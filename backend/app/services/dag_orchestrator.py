import asyncio
import hashlib
import json
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, deque
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import ChainRun, ExecutionLog, Agent, TransformRecord
from app.models.chain import RunStatus, NodeStatus
from app.models.transform import TransformMethod
from app.services.transform_pipeline import TransformPipeline
from app.services.agent_caller import AgentCaller
from app.services.wallet_service import WalletService
from app.services.provenance_tracker import ProvenanceTracker
from app.core.logging import logger

class DAGNode:
    def __init__(self, node_id: str, agent_id: str, metadata: dict = None):
        self.node_id = node_id
        self.agent_id = agent_id
        self.metadata = metadata or {}
        self.inputs: Set[str] = set()
        self.outputs: Set[str] = set()
        self.status = "pending"
        self.result = None
        self.error = None

class DAGEdge:
    def __init__(self, from_node: str, to_node: str, mapping_hint_id: Optional[str] = None):
        self.from_node = from_node
        self.to_node = to_node
        self.mapping_hint_id = mapping_hint_id
        self.compatibility_score = 0.0
        self.transform_method = None

class DAGOrchestrator:
    def __init__(
        self,
        db: AsyncSession,
        transform_pipeline: TransformPipeline,
        agent_caller: AgentCaller,
        wallet_service: WalletService,
        provenance_tracker: ProvenanceTracker
    ):
        self.db = db
        self.transform_pipeline = transform_pipeline
        self.agent_caller = agent_caller
        self.wallet_service = wallet_service
        self.provenance_tracker = provenance_tracker
        self.worker_pool_size = 5

    async def execute_chain(
        self,
        chain_run: ChainRun,
        chain_descriptor: dict
    ) -> dict:
        """Execute a DAG chain with proper ordering and transformations"""
        
        try:
            # Update status to running
            chain_run.status = RunStatus.RUNNING
            chain_run.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Parse DAG structure
            dag_nodes, dag_edges = self._parse_dag(chain_descriptor)
            
            # Validate and reserve budget
            estimated_cost = await self._estimate_cost(dag_nodes)
            hold_id = await self.wallet_service.create_hold(
                chain_run.owner_user_id,
                estimated_cost,
                f"chain_run_{chain_run.id}"
            )
            chain_run.reserved_cents = estimated_cost
            
            # Topological sort for execution order
            execution_order = self._topological_sort(dag_nodes, dag_edges)
            
            # Initialize execution state
            node_results = {}
            ready_queue = deque()
            completed_nodes = set()
            
            # Find initial nodes (no dependencies)
            for node_id in execution_order:
                if not self._get_dependencies(node_id, dag_edges):
                    ready_queue.append(node_id)
            
            # Execute nodes
            while ready_queue:
                # Get nodes that can run in parallel
                batch = []
                batch_size = min(len(ready_queue), self.worker_pool_size)
                for _ in range(batch_size):
                    if ready_queue:
                        batch.append(ready_queue.popleft())
                
                # Execute batch in parallel
                batch_tasks = []
                for node_id in batch:
                    node = dag_nodes[node_id]
                    input_data = await self._build_node_input(
                        node, dag_edges, node_results, chain_run
                    )
                    
                    task = self._execute_node(
                        node, input_data, chain_run
                    )
                    batch_tasks.append((node_id, task))
                
                # Wait for batch completion
                for node_id, task in batch_tasks:
                    try:
                        result = await task
                        node_results[node_id] = result
                        completed_nodes.add(node_id)
                        
                        # Settle payment for successful node
                        agent = await self._get_agent(dag_nodes[node_id].agent_id)
                        await self.wallet_service.settle_node_payment(
                            chain_run.id,
                            node_id,
                            agent.price_cents
                        )
                        
                        # Add newly ready nodes to queue
                        for edge in dag_edges:
                            if edge.from_node == node_id:
                                to_node = edge.to_node
                                deps = self._get_dependencies(to_node, dag_edges)
                                if deps.issubset(completed_nodes):
                                    ready_queue.append(to_node)
                                    
                    except Exception as e:
                        logger.error(f"Node {node_id} failed: {str(e)}")
                        dag_nodes[node_id].status = "failed"
                        dag_nodes[node_id].error = str(e)
                        
                        # Refund for failed node
                        await self.wallet_service.refund_node_payment(
                            chain_run.id,
                            node_id
                        )
            
            # Merge final outputs
            final_output = await self._merge_outputs(
                node_results,
                chain_descriptor.get("merge_strategy", "authoritative"),
                chain_run
            )
            
            # Generate provenance map
            provenance_map = self.provenance_tracker.generate_provenance_map(
                final_output,
                node_results,
                chain_run.id
            )
            
            # Update chain run
            chain_run.status = RunStatus.SUCCEEDED
            chain_run.finished_at = datetime.utcnow()
            chain_run.final_output = final_output
            chain_run.provenance_map = provenance_map
            chain_run.spent_cents = await self._calculate_spent(chain_run.id)
            
            # Release unused budget
            unused = chain_run.reserved_cents - chain_run.spent_cents
            if unused > 0:
                await self.wallet_service.refund_unused(chain_run.id, unused)
            
            await self.db.commit()
            
            return {
                "status": "success",
                "output": final_output,
                "provenance": provenance_map,
                "cost_cents": chain_run.spent_cents
            }
            
        except Exception as e:
            logger.error(f"Chain execution failed: {str(e)}")
            chain_run.status = RunStatus.FAILED
            chain_run.finished_at = datetime.utcnow()
            
            # Refund all reserved funds
            await self.wallet_service.refund_all(chain_run.id)
            
            await self.db.commit()
            raise

    async def _execute_node(
        self,
        node: DAGNode,
        input_data: dict,
        chain_run: ChainRun
    ) -> dict:
        """Execute a single node with retries and error handling"""
        
        # Generate idempotency key
        idempotency_key = self._generate_idempotency_key(
            chain_run.id,
            node.node_id,
            input_data
        )
        
        # Check if already executed
        existing_log = await self.db.execute(
            select(ExecutionLog).where(
                ExecutionLog.idempotency_key == idempotency_key
            )
        )
        if existing_log.scalar_one_or_none():
            return existing_log.scalar_one().response_payload
        
        # Get agent
        agent = await self._get_agent(node.agent_id)
        
        # Validate input against schema
        is_valid, validation_error = await self._validate_schema(
            input_data,
            agent.input_schema
        )
        
        if not is_valid:
            # Attempt transformation if schema doesn't match
            transformed_input = await self.transform_pipeline.transform(
                input_data,
                agent.input_schema,
                chain_run
            )
            input_data = transformed_input
        
        # Call agent
        start_time = datetime.utcnow()
        response = await self.agent_caller.call_agent(
            agent,
            input_data,
            idempotency_key
        )
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Validate output
        is_valid, _ = await self._validate_schema(
            response,
            agent.output_schema
        )
        
        # Log execution
        execution_log = ExecutionLog(
            run_id=chain_run.id,
            step_index=node.metadata.get("step_index", 0),
            node_id=node.node_id,
            agent_id=agent.id,
            request_payload=input_data,
            response_payload=response,
            status=NodeStatus.SUCCESS if is_valid else NodeStatus.FAILED,
            duration_ms=duration_ms,
            idempotency_key=idempotency_key
        )
        self.db.add(execution_log)
        await self.db.commit()
        
        return response

    async def _build_node_input(
        self,
        node: DAGNode,
        edges: List[DAGEdge],
        node_results: dict,
        chain_run: ChainRun
    ) -> dict:
        """Build input for a node by merging predecessor outputs"""
        
        # Get predecessor outputs
        predecessor_outputs = []
        for edge in edges:
            if edge.to_node == node.node_id and edge.from_node in node_results:
                predecessor_outputs.append(node_results[edge.from_node])
        
        if not predecessor_outputs:
            # No predecessors, use sample input or empty
            agent = await self._get_agent(node.agent_id)
            return agent.sample_request or {}
        
        if len(predecessor_outputs) == 1:
            return predecessor_outputs[0]
        
        # Merge multiple inputs
        return await self._merge_inputs(predecessor_outputs, chain_run)

    async def _merge_inputs(self, inputs: List[dict], chain_run: ChainRun) -> dict:
        """Merge multiple inputs using deterministic rules"""
        
        merged = {}
        
        for input_data in inputs:
            for key, value in input_data.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, list) and isinstance(merged[key], list):
                    merged[key].extend(value)
                elif value is not None:
                    # Prefer non-null values
                    merged[key] = value
        
        return merged

    async def _merge_outputs(
        self,
        node_results: dict,
        strategy: str,
        chain_run: ChainRun
    ) -> dict:
        """Merge final outputs based on strategy"""
        
        # Find terminal nodes (no outgoing edges)
        terminal_outputs = []
        for node_id, result in node_results.items():
            # Check if terminal node logic
            terminal_outputs.append(result)
        
        if not terminal_outputs:
            return {}
        
        if len(terminal_outputs) == 1:
            return terminal_outputs[0]
        
        if strategy == "concatenate":
            return await self._merge_concatenate(terminal_outputs)
        elif strategy == "synthesize":
            return await self._merge_synthesize(terminal_outputs, chain_run)
        else:  # authoritative
            return await self._merge_authoritative(terminal_outputs)

    async def _merge_authoritative(self, outputs: List[dict]) -> dict:
        """Choose fields from most authoritative source"""
        
        # For now, take the last output as most authoritative
        # In production, use provenance confidence scores
        return outputs[-1] if outputs else {}

    async def _merge_concatenate(self, outputs: List[dict]) -> dict:
        """Concatenate string/array fields"""
        
        merged = {}
        for output in outputs:
            for key, value in output.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, str) and isinstance(merged[key], str):
                    merged[key] += "\n" + value
                elif isinstance(value, list) and isinstance(merged[key], list):
                    merged[key].extend(value)
        return merged

    async def _merge_synthesize(self, outputs: List[dict], chain_run: ChainRun) -> dict:
        """Use LLM to synthesize final output"""
        
        # This would call the LLM gateway if enabled
        # For now, fallback to authoritative
        return await self._merge_authoritative(outputs)

    def _parse_dag(self, descriptor: dict) -> Tuple[Dict[str, DAGNode], List[DAGEdge]]:
        """Parse chain descriptor into DAG structure"""
        
        nodes = {}
        for node_data in descriptor.get("nodes", []):
            node = DAGNode(
                node_data["node_id"],
                node_data["agent_id"],
                node_data.get("node_metadata", {})
            )
            nodes[node.node_id] = node
        
        edges = []
        for edge_data in descriptor.get("edges", []):
            edge = DAGEdge(
                edge_data["from_node"],
                edge_data["to_node"],
                edge_data.get("mapping_hint_id")
            )
            edges.append(edge)
        
        return nodes, edges

    def _topological_sort(self, nodes: Dict[str, DAGNode], edges: List[DAGEdge]) -> List[str]:
        """Topologically sort DAG nodes"""
        
        # Build adjacency list
        adj_list = defaultdict(list)
        in_degree = defaultdict(int)
        
        for node_id in nodes:
            in_degree[node_id] = 0
        
        for edge in edges:
            adj_list[edge.from_node].append(edge.to_node)
            in_degree[edge.to_node] += 1
        
        # Kahn's algorithm
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(nodes):
            raise ValueError("DAG contains cycles")
        
        return result

    def _get_dependencies(self, node_id: str, edges: List[DAGEdge]) -> Set[str]:
        """Get dependencies for a node"""
        
        deps = set()
        for edge in edges:
            if edge.to_node == node_id:
                deps.add(edge.from_node)
        return deps

    def _generate_idempotency_key(self, run_id: str, node_id: str, input_data: dict) -> str:
        """Generate idempotency key for node execution"""
        
        key_data = f"{run_id}_{node_id}_{json.dumps(input_data, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def _get_agent(self, agent_id: str) -> Agent:
        """Get agent by ID"""
        
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        return agent

    async def _validate_schema(self, data: dict, schema: dict) -> Tuple[bool, Optional[str]]:
        """Validate data against JSON schema"""
        
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, str(e)

    async def _estimate_cost(self, nodes: Dict[str, DAGNode]) -> int:
        """Estimate total cost for chain execution"""
        
        total = 0
        for node in nodes.values():
            agent = await self._get_agent(node.agent_id)
            total += agent.price_cents
        
        # Add buffer for potential LLM usage
        total = int(total * 1.2)
        return total

    async def _calculate_spent(self, run_id: str) -> int:
        """Calculate actual spent amount for a run"""
        
        result = await self.db.execute(
            select(TransformRecord).where(TransformRecord.run_id == run_id)
        )
        transforms = result.scalars().all()
        
        total = 0
        for transform in transforms:
            total += transform.cost_cents or 0
        
        # Add agent costs
        result = await self.db.execute(
            select(ExecutionLog).where(ExecutionLog.run_id == run_id)
        )
        logs = result.scalars().all()
        
        for log in logs:
            agent = await self._get_agent(log.agent_id)
            total += agent.price_cents
        
        return total
