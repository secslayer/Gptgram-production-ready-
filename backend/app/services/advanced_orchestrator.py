"""
Advanced DAG Orchestrator with Deterministic → GAT → LLM fallback hierarchy
Implements the 14-point testing methodology with @agent replacement
"""

import json
import hmac
import hashlib
import uuid
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
from jsonschema import validate, ValidationError
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ChainRun, ExecutionLog, TransformRecord, MappingHint, Agent
from app.services.agent_caller import AgentCaller
from app.services.gat_service import GATService
from app.services.llm_gateway import LLMGateway
from app.services.provenance_tracker import ProvenanceTracker
from app.services.orchestrator_methods import OrchestratorMethods
from app.core.config import settings
from app.core.logging import logger

class AdvancedOrchestrator(OrchestratorMethods):
    """Production-ready DAG orchestrator with deterministic-first approach"""
    
    def __init__(
        self,
        db: AsyncSession,
        agent_caller: AgentCaller,
        gat_service: GATService,
        llm_gateway: LLMGateway,
        provenance_tracker: ProvenanceTracker
    ):
        self.db = db
        self.agent_caller = agent_caller
        self.gat_service = gat_service
        self.llm_gateway = llm_gateway
        self.provenance_tracker = provenance_tracker
        
        # Deterministic mapping rules
        self.field_aliases = {
            'summary': ['summary_text', 'text_summary', 'summarized', 'abstract'],
            'text': ['content', 'body', 'message', 'input_text', 'text_input'],
            'sentiment': ['emotion', 'feeling', 'mood', 'tone'],
            'target': ['target_language', 'lang', 'to_lang', 'destination'],
            'translated': ['translation', 'translated_text', 'output_text'],
            'score': ['confidence', 'probability', 'certainty']
        }
        
        # Merge policies
        self.merge_policies = {
            'concat_text': self._merge_concat_text,
            'json_merge_by_key': self._merge_json_by_key,
            'prefer_high_confidence': self._merge_prefer_high_confidence,
            'authoritative': self._merge_authoritative
        }

    def canonical_json(self, obj: dict) -> str:
        """Create canonical JSON for HMAC signing"""
        return json.dumps(obj, separators=(',', ':'), sort_keys=True)

    def compute_signature(self, payload: str) -> str:
        """Compute HMAC-SHA256 signature"""
        return hmac.new(
            settings.N8N_HMAC_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def execute_dag(
        self,
        dag: Dict,
        root_input: Dict,
        options: Dict
    ) -> Dict:
        """
        Execute DAG with deterministic → GAT → LLM fallback hierarchy
        """
        
        # 1. Topological sort
        ordered_nodes = self._topological_sort(dag)
        
        # 2. Storage for outputs and validation
        outputs = {}
        validation_reports = {}
        telemetry = []
        
        # 3. Execute nodes in order
        for node in ordered_nodes:
            start_time = datetime.utcnow()
            
            try:
                # Gather parent outputs and merge
                if node.get('parents'):
                    parent_payloads = [outputs.get(p, {}) for p in node['parents']]
                    merge_policy = node.get('merge_policy', 'json_merge_by_key')
                    merged = self.merge_policies[merge_policy](parent_payloads)
                else:
                    merged = root_input
                
                # 4. Replace @agent tokens
                node_input = self._replace_at_tokens(node.get('input_template', {}), outputs)
                
                # If no template, use merged data
                if not node_input:
                    node_input = merged
                
                # 5. Validate against schema
                input_schema = node.get('input_schema', {})
                score, is_valid, errors = self._compute_compatibility_score(
                    node_input, 
                    input_schema
                )
                
                if is_valid and score >= options.get('compatibility_threshold', 0.85):
                    # Direct execution - no transform needed
                    result = await self._call_agent(node, node_input)
                    outputs[node['id']] = result
                    validation_reports[node['id']] = {
                        'compatibility': score,
                        'transform_used': None,
                        'method': 'direct',
                        'success': True
                    }
                    
                    telemetry.append({
                        'node_id': node['id'],
                        'method': 'direct',
                        'score': score,
                        'latency_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
                    })
                    continue
                
                # 6. Try deterministic mappings
                mapping_result = await self._try_deterministic_mappings(
                    node, merged, input_schema
                )
                
                if mapping_result['success']:
                    result = await self._call_agent(node, mapping_result['transformed'])
                    outputs[node['id']] = result
                    validation_reports[node['id']] = {
                        'compatibility': mapping_result['score'],
                        'transform_used': mapping_result['mapping'],
                        'method': 'deterministic',
                        'success': True
                    }
                    
                    telemetry.append({
                        'node_id': node['id'],
                        'method': 'deterministic',
                        'score': mapping_result['score'],
                        'mapping': mapping_result['mapping'],
                        'latency_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
                    })
                    continue
                
                # 7. Try GAT suggestions if enabled
                if options.get('allow_gat', True):
                    gat_result = await self._try_gat_mappings(
                        node, merged, input_schema
                    )
                    
                    if gat_result['success']:
                        result = await self._call_agent(node, gat_result['transformed'])
                        outputs[node['id']] = result
                        validation_reports[node['id']] = {
                            'compatibility': gat_result['score'],
                            'transform_used': gat_result['mapping'],
                            'method': 'gat',
                            'success': True
                        }
                        
                        telemetry.append({
                            'node_id': node['id'],
                            'method': 'gat',
                            'score': gat_result['score'],
                            'mapping': gat_result['mapping'],
                            'latency_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
                        })
                        continue
                
                # 8. LLM fallback if enabled
                if options.get('allow_llm', False):
                    llm_result = await self._try_llm_synthesis(
                        node, merged, input_schema
                    )
                    
                    if llm_result['success']:
                        result = await self._call_agent(node, llm_result['transformed'])
                        outputs[node['id']] = result
                        validation_reports[node['id']] = {
                            'compatibility': llm_result['score'],
                            'transform_used': 'llm_synthesis',
                            'method': 'llm',
                            'success': True,
                            'llm_tokens_used': llm_result.get('tokens_used', 0)
                        }
                        
                        telemetry.append({
                            'node_id': node['id'],
                            'method': 'llm',
                            'score': llm_result['score'],
                            'tokens': llm_result.get('tokens_used', 0),
                            'latency_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
                        })
                        continue
                
                # 9. Handle failure based on policy
                failure_policy = node.get('failure_policy', 'abort')
                
                if failure_policy == 'abort':
                    return {
                        'status': 'failed',
                        'failed_node': node['id'],
                        'outputs': outputs,
                        'reports': validation_reports,
                        'telemetry': telemetry,
                        'error': f"Node {node['id']} failed - no valid transform found"
                    }
                elif failure_policy == 'continue_partial':
                    outputs[node['id']] = None
                    validation_reports[node['id']] = {
                        'compatibility': score,
                        'transform_used': None,
                        'method': 'failed',
                        'success': False,
                        'errors': errors
                    }
                elif failure_policy == 'skip':
                    logger.warning(f"Skipping node {node['id']} due to compatibility failure")
                    continue
                    
            except Exception as e:
                logger.error(f"Node {node['id']} execution failed: {str(e)}")
                
                if node.get('failure_policy') == 'abort':
                    return {
                        'status': 'failed',
                        'failed_node': node['id'],
                        'outputs': outputs,
                        'reports': validation_reports,
                        'telemetry': telemetry,
                        'error': str(e)
                    }
                else:
                    outputs[node['id']] = None
                    validation_reports[node['id']] = {
                        'success': False,
                        'error': str(e)
                    }
        
        # 10. Success - analyze telemetry for auto-adaptation
        await self._analyze_and_adapt(telemetry, validation_reports)
        
        return {
            'status': 'success',
            'outputs': outputs,
            'reports': validation_reports,
            'telemetry': telemetry
        }

    def _topological_sort(self, dag: Dict) -> List[Dict]:
        """Topological sort of DAG nodes"""
        nodes = dag.get('nodes', [])
        edges = dag.get('edges', [])
        
        # Build adjacency list
        graph = {node['id']: [] for node in nodes}
        in_degree = {node['id']: 0 for node in nodes}
        
        for edge in edges:
            graph[edge['from']].append(edge['to'])
            in_degree[edge['to']] += 1
        
        # Find nodes with no dependencies
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        sorted_nodes = []
        
        while queue:
            node_id = queue.pop(0)
            node = next(n for n in nodes if n['id'] == node_id)
            sorted_nodes.append(node)
            
            # Add parents info for merging
            node['parents'] = [
                e['from'] for e in edges if e['to'] == node_id
            ]
            
            # Reduce in-degree of neighbors
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(sorted_nodes) != len(nodes):
            raise ValueError("DAG contains cycles")
        
        return sorted_nodes

    def _replace_at_tokens(self, template: Any, outputs: Dict) -> Any:
        """Replace @agent.field tokens with actual values"""
        
        def resolve_token(token: str) -> Any:
            if not token.startswith('@'):
                return token
            
            # Remove @ and split
            token = token[1:]
            parts = token.split('.')
            
            if len(parts) < 2:
                return None
            
            agent_name = parts[0]
            field_path = parts[1:]
            
            # Get agent output
            if agent_name not in outputs:
                logger.warning(f"Agent {agent_name} not found in outputs")
                return None
            
            # Traverse path
            value = outputs[agent_name]
            for part in field_path:
                # Handle array indices like field[0]
                if '[' in part and part.endswith(']'):
                    field, idx_str = part.rstrip(']').split('[')
                    idx = int(idx_str)
                    
                    if isinstance(value, dict) and field in value:
                        value = value[field]
                        if isinstance(value, list) and idx < len(value):
                            value = value[idx]
                        else:
                            return None
                    else:
                        return None
                else:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return None
                
                if value is None:
                    return None
            
            return value
        
        # Recursive replacement
        if isinstance(template, str):
            # Find all @tokens
            pattern = r'@[\w\-\_]+(?:\.[\w\-\_\[\]0-9]+)+'
            
            result = template
            for match in re.findall(pattern, template):
                resolved = resolve_token(match)
                if resolved is not None:
                    if isinstance(resolved, str):
                        result = result.replace(match, resolved)
                    else:
                        result = result.replace(match, json.dumps(resolved))
                else:
                    # Try to find fallback or leave empty
                    result = result.replace(match, '')
            
            return result
        
        elif isinstance(template, dict):
            return {
                key: self._replace_at_tokens(value, outputs)
                for key, value in template.items()
            }
        
        elif isinstance(template, list):
            return [
                self._replace_at_tokens(item, outputs)
                for item in template
            ]
        
        else:
            return template
