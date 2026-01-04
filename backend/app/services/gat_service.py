import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from torch_geometric.data import Data
import numpy as np
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.models import Agent, ExecutionLog, MappingHint, GATModel
from app.services.vector_store import VectorStore
from app.core.logging import logger

class GraphAttentionNetwork(torch.nn.Module):
    """Graph Attention Network for agent recommendations and mapping suggestions"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 128, output_dim: int = 64, num_heads: int = 4):
        super(GraphAttentionNetwork, self).__init__()
        
        self.conv1 = GATConv(input_dim, hidden_dim, heads=num_heads, dropout=0.1)
        self.conv2 = GATConv(hidden_dim * num_heads, hidden_dim, heads=num_heads, dropout=0.1)
        self.conv3 = GATConv(hidden_dim * num_heads, output_dim, heads=1, concat=False, dropout=0.1)
        
        self.dropout = torch.nn.Dropout(0.2)

    def forward(self, x, edge_index, return_attention=False):
        # First GAT layer
        x, attention1 = self.conv1(x, edge_index, return_attention_weights=True)
        x = F.elu(x)
        x = self.dropout(x)
        
        # Second GAT layer
        x, attention2 = self.conv2(x, edge_index, return_attention_weights=True)
        x = F.elu(x)
        x = self.dropout(x)
        
        # Third GAT layer
        x, attention3 = self.conv3(x, edge_index, return_attention_weights=True)
        
        if return_attention:
            return x, (attention1, attention2, attention3)
        return x

class GATService:
    """GAT service for agent recommendations and mapping suggestions"""
    
    def __init__(self, db: AsyncSession, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store
        self.model = None
        self.node_embeddings = {}
        self.agent_index_map = {}
        self.embedding_dim = 384
        
    async def initialize(self):
        """Initialize or load GAT model"""
        
        # Check for existing model
        result = await self.db.execute(
            select(GATModel).where(
                GATModel.status == "ready"
            ).order_by(GATModel.created_at.desc())
        )
        existing_model = result.scalar_one_or_none()
        
        if existing_model:
            await self._load_model(existing_model)
        else:
            await self.train_model()

    async def train_model(self):
        """Train GAT model on agent collaboration graph"""
        
        logger.info("Training GAT model...")
        
        # Build graph from execution history
        graph_data = await self._build_graph()
        
        if not graph_data:
            logger.warning("Insufficient data for GAT training")
            return
        
        # Initialize model
        input_dim = graph_data.x.shape[1]
        self.model = GraphAttentionNetwork(input_dim=input_dim)
        
        # Training loop
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.model.train()
        
        for epoch in range(200):
            optimizer.zero_grad()
            
            # Forward pass
            embeddings = self.model(graph_data.x, graph_data.edge_index)
            
            # Self-supervised loss (node similarity)
            pos_loss = self._compute_positive_loss(embeddings, graph_data.edge_index)
            neg_loss = self._compute_negative_loss(embeddings, graph_data.edge_index)
            loss = pos_loss + neg_loss
            
            loss.backward()
            optimizer.step()
            
            if epoch % 20 == 0:
                logger.info(f"GAT Training - Epoch {epoch}, Loss: {loss.item():.4f}")
        
        # Save model and embeddings
        await self._save_model(embeddings.detach())
        
        logger.info("GAT model training completed")

    async def suggest_mappings(
        self,
        source_fp: str,
        target_fp: str,
        input_data: dict = None
    ) -> List[Dict]:
        """Suggest mapping recipes using GAT attention"""
        
        if not self.model:
            return []
        
        suggestions = []
        
        # Find agents with similar schema fingerprints
        similar_pairs = await self._find_similar_transformations(source_fp, target_fp)
        
        for pair in similar_pairs[:5]:
            # Get attention weights between agents
            attention_weights = await self._get_attention_between_agents(
                pair['source_agent_id'],
                pair['target_agent_id']
            )
            
            # Generate mapping recipe based on historical patterns
            recipe = await self._generate_mapping_recipe(
                pair['source_schema'],
                pair['target_schema'],
                attention_weights
            )
            
            suggestions.append({
                'recipe': recipe,
                'confidence': pair['similarity_score'] * attention_weights.get('weight', 0.5),
                'attention_trace': attention_weights
            })
        
        return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)

    async def recommend_collaborators(
        self,
        agent_id: str,
        top_k: int = 5
    ) -> List[Dict]:
        """Recommend collaborator agents using GAT embeddings and attention"""
        
        if not self.model or agent_id not in self.agent_index_map:
            return []
        
        recommendations = []
        
        # Get agent embedding
        agent_idx = self.agent_index_map[agent_id]
        agent_embedding = self.node_embeddings.get(agent_idx)
        
        if agent_embedding is None:
            return []
        
        # Find similar agents using cosine similarity
        similarities = []
        for other_id, other_idx in self.agent_index_map.items():
            if other_id == agent_id:
                continue
            
            other_embedding = self.node_embeddings.get(other_idx)
            if other_embedding is not None:
                similarity = F.cosine_similarity(
                    agent_embedding.unsqueeze(0),
                    other_embedding.unsqueeze(0)
                ).item()
                
                similarities.append({
                    'agent_id': other_id,
                    'similarity': similarity
                })
        
        # Sort and get top-k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        for item in similarities[:top_k]:
            # Get additional context
            agent_data = await self._get_agent_data(item['agent_id'])
            attention_trace = await self._get_attention_trace(agent_id, item['agent_id'])
            
            # Check for existing mapping hints
            mapping_hint = await self._find_mapping_hint_between_agents(
                agent_id,
                item['agent_id']
            )
            
            recommendations.append({
                'agent_id': item['agent_id'],
                'score': item['similarity'],
                'name': agent_data.get('name'),
                'verification_level': agent_data.get('verification_level'),
                'price_cents': agent_data.get('price_cents'),
                'mapping_hint_id': mapping_hint.id if mapping_hint else None,
                'attention_trace': attention_trace,
                'explanation': self._generate_explanation(
                    item['similarity'],
                    attention_trace,
                    agent_data
                )
            })
        
        return recommendations

    async def _build_graph(self) -> Optional[Data]:
        """Build graph from agent execution history"""
        
        # Get all agents
        result = await self.db.execute(select(Agent))
        agents = result.scalars().all()
        
        if len(agents) < 2:
            return None
        
        # Create node features
        node_features = []
        for i, agent in enumerate(agents):
            self.agent_index_map[str(agent.id)] = i
            
            # Get agent embedding from vector store
            embedding = await self.vector_store.get_embedding(
                self._create_agent_text(agent)
            )
            
            # Add additional features
            features = embedding.tolist()
            features.extend([
                agent.price_cents / 100.0,  # Normalized price
                agent.metrics_cache.get('success_rate', 0.5) if agent.metrics_cache else 0.5,
                agent.metrics_cache.get('avg_latency_ms', 1000) / 1000.0 if agent.metrics_cache else 1.0,
                self._encode_verification_level(agent.verification_level),
                agent.metrics_cache.get('call_volume', 0) / 100.0 if agent.metrics_cache else 0.0
            ])
            
            node_features.append(features)
        
        # Create edges from co-execution history
        edges = []
        edge_weights = []
        
        # Query execution logs for co-executions
        result = await self.db.execute(select(ExecutionLog))
        logs = result.scalars().all()
        
        # Group by run to find co-executions
        run_agents = {}
        for log in logs:
            run_id = str(log.run_id)
            if run_id not in run_agents:
                run_agents[run_id] = []
            run_agents[run_id].append(str(log.agent_id))
        
        # Create edges for agents that appear in same runs
        co_execution_counts = {}
        for agents_in_run in run_agents.values():
            for i in range(len(agents_in_run)):
                for j in range(i + 1, len(agents_in_run)):
                    agent1, agent2 = agents_in_run[i], agents_in_run[j]
                    if agent1 in self.agent_index_map and agent2 in self.agent_index_map:
                        key = tuple(sorted([agent1, agent2]))
                        co_execution_counts[key] = co_execution_counts.get(key, 0) + 1
        
        # Convert to edge list
        for (agent1, agent2), count in co_execution_counts.items():
            idx1 = self.agent_index_map[agent1]
            idx2 = self.agent_index_map[agent2]
            
            edges.append([idx1, idx2])
            edges.append([idx2, idx1])  # Bidirectional
            
            weight = min(count / 10.0, 1.0)  # Normalize weight
            edge_weights.extend([weight, weight])
        
        if not edges:
            # Create minimal connectivity if no co-executions
            for i in range(len(agents) - 1):
                edges.append([i, i + 1])
                edges.append([i + 1, i])
                edge_weights.extend([0.1, 0.1])
        
        # Create PyTorch geometric data
        x = torch.tensor(node_features, dtype=torch.float)
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
        
        return Data(x=x, edge_index=edge_index)

    async def _get_attention_between_agents(
        self,
        source_agent_id: str,
        target_agent_id: str
    ) -> Dict:
        """Get attention weights between two agents"""
        
        if not self.model or not all([
            source_agent_id in self.agent_index_map,
            target_agent_id in self.agent_index_map
        ]):
            return {'weight': 0.5, 'layers': []}
        
        source_idx = self.agent_index_map[source_agent_id]
        target_idx = self.agent_index_map[target_agent_id]
        
        # Get attention weights from model
        # This is simplified - in production, would need to properly extract attention
        weight = 0.7  # Placeholder
        
        return {
            'weight': weight,
            'source_agent': source_agent_id,
            'target_agent': target_agent_id,
            'layers': [
                {'layer': 1, 'weight': weight * 0.8},
                {'layer': 2, 'weight': weight * 1.0},
                {'layer': 3, 'weight': weight * 0.9}
            ]
        }

    async def _generate_mapping_recipe(
        self,
        source_schema: dict,
        target_schema: dict,
        attention_weights: dict
    ) -> List[Dict]:
        """Generate mapping recipe based on schemas and attention"""
        
        recipe = []
        
        source_props = source_schema.get('properties', {})
        target_props = target_schema.get('properties', {})
        
        # Use attention weights to prioritize field mappings
        confidence = attention_weights.get('weight', 0.5)
        
        for target_field, target_spec in target_props.items():
            # Find best matching source field
            best_match = None
            best_score = 0
            
            for source_field, source_spec in source_props.items():
                # Calculate similarity
                score = self._calculate_field_similarity(
                    source_field, source_spec,
                    target_field, target_spec
                ) * confidence
                
                if score > best_score:
                    best_score = score
                    best_match = source_field
            
            if best_match and best_score > 0.3:
                if best_match != target_field:
                    recipe.append({
                        'op': 'rename',
                        'from': best_match,
                        'to': target_field
                    })
                
                # Add type coercion if needed
                if source_props[best_match].get('type') != target_spec.get('type'):
                    recipe.append({
                        'op': 'coerce',
                        'field': target_field,
                        'to': target_spec.get('type')
                    })
        
        return recipe

    def _calculate_field_similarity(
        self,
        source_field: str,
        source_spec: dict,
        target_field: str,
        target_spec: dict
    ) -> float:
        """Calculate similarity between two schema fields"""
        
        score = 0.0
        
        # Name similarity
        if source_field.lower() == target_field.lower():
            score += 0.5
        elif source_field.lower() in target_field.lower() or target_field.lower() in source_field.lower():
            score += 0.3
        
        # Type compatibility
        if source_spec.get('type') == target_spec.get('type'):
            score += 0.3
        elif self._are_types_compatible(source_spec.get('type'), target_spec.get('type')):
            score += 0.2
        
        return score

    def _are_types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if two types are compatible for coercion"""
        
        compatible_types = {
            ('string', 'number'),
            ('string', 'integer'),
            ('number', 'integer'),
            ('integer', 'number')
        }
        
        return (source_type, target_type) in compatible_types or \
               (target_type, source_type) in compatible_types

    async def _find_similar_transformations(
        self,
        source_fp: str,
        target_fp: str
    ) -> List[Dict]:
        """Find similar schema transformations from history"""
        
        # Query mapping hints with similar fingerprints
        result = await self.db.execute(
            select(MappingHint).where(
                MappingHint.success_count > 0
            )
        )
        hints = result.scalars().all()
        
        similar = []
        for hint in hints:
            # Calculate similarity (simplified)
            similarity = 0.0
            if hint.source_schema_fp == source_fp:
                similarity += 0.5
            if hint.target_schema_fp == target_fp:
                similarity += 0.5
            
            if similarity > 0:
                similar.append({
                    'source_agent_id': None,  # Would need to track this
                    'target_agent_id': None,
                    'source_schema': {},
                    'target_schema': {},
                    'similarity_score': similarity,
                    'mapping_hint': hint
                })
        
        return similar

    def _create_agent_text(self, agent: Agent) -> str:
        """Create text representation of agent for embedding"""
        
        text_parts = [
            agent.name,
            agent.description or "",
            json.dumps(agent.input_schema) if agent.input_schema else "",
            json.dumps(agent.output_schema) if agent.output_schema else "",
            json.dumps(agent.sample_response) if agent.sample_response else ""
        ]
        
        return " ".join(text_parts)

    def _encode_verification_level(self, level) -> float:
        """Encode verification level as numeric feature"""
        
        levels = {
            "unverified": 0.0,
            "L1": 0.33,
            "L2": 0.66,
            "L3": 1.0
        }
        return levels.get(str(level), 0.0)

    async def _get_agent_data(self, agent_id: str) -> Dict:
        """Get agent data by ID"""
        
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if agent:
            return {
                'name': agent.name,
                'verification_level': str(agent.verification_level),
                'price_cents': agent.price_cents,
                'success_rate': agent.metrics_cache.get('success_rate', 0) if agent.metrics_cache else 0
            }
        
        return {}

    async def _find_mapping_hint_between_agents(
        self,
        agent1_id: str,
        agent2_id: str
    ) -> Optional[MappingHint]:
        """Find mapping hint between two agents"""
        
        # This would need to track agent associations with mapping hints
        # For now, return None
        return None

    async def _get_attention_trace(
        self,
        source_agent_id: str,
        target_agent_id: str
    ) -> Dict:
        """Get attention trace between agents"""
        
        return await self._get_attention_between_agents(source_agent_id, target_agent_id)

    def _generate_explanation(
        self,
        similarity: float,
        attention_trace: dict,
        agent_data: dict
    ) -> str:
        """Generate human-readable explanation for recommendation"""
        
        reasons = []
        
        if similarity > 0.8:
            reasons.append(f"high similarity score ({similarity:.2f})")
        
        if agent_data.get('success_rate', 0) > 0.9:
            reasons.append(f"{agent_data['success_rate']*100:.0f}% success rate")
        
        if attention_trace.get('weight', 0) > 0.7:
            reasons.append("strong attention weight in graph")
        
        if not reasons:
            reasons.append("potential compatibility")
        
        return f"Recommended because: {', '.join(reasons)}"

    def _compute_positive_loss(self, embeddings, edge_index):
        """Compute loss for positive (connected) pairs"""
        
        source = embeddings[edge_index[0]]
        target = embeddings[edge_index[1]]
        
        pos_loss = -F.logsigmoid((source * target).sum(dim=1)).mean()
        return pos_loss

    def _compute_negative_loss(self, embeddings, edge_index, num_neg_samples=5):
        """Compute loss for negative (unconnected) pairs"""
        
        num_nodes = embeddings.size(0)
        
        # Random negative sampling
        neg_edge_index = torch.randint(
            0, num_nodes,
            (2, edge_index.size(1) * num_neg_samples),
            dtype=torch.long
        )
        
        source = embeddings[neg_edge_index[0]]
        target = embeddings[neg_edge_index[1]]
        
        neg_loss = -F.logsigmoid(-(source * target).sum(dim=1)).mean()
        return neg_loss

    async def _save_model(self, embeddings):
        """Save trained model and embeddings"""
        
        # Save to database
        gat_model = GATModel(
            model_version=f"v_{datetime.utcnow().timestamp()}",
            status="ready",
            embedding_dim=self.embedding_dim,
            num_layers=3,
            training_started_at=datetime.utcnow(),
            training_completed_at=datetime.utcnow(),
            training_metrics={
                "final_loss": 0.1,  # Placeholder
                "num_nodes": len(self.agent_index_map),
                "num_edges": 0  # Placeholder
            }
        )
        self.db.add(gat_model)
        await self.db.commit()
        
        # Store embeddings
        for agent_id, idx in self.agent_index_map.items():
            self.node_embeddings[idx] = embeddings[idx]

    async def _load_model(self, gat_model: GATModel):
        """Load existing model"""
        
        # In production, load from file system or S3
        logger.info(f"Loading GAT model version {gat_model.model_version}")
        
        # Initialize model architecture
        self.model = GraphAttentionNetwork(
            input_dim=gat_model.embedding_dim + 5,  # Base embedding + features
            hidden_dim=128,
            output_dim=64
        )
