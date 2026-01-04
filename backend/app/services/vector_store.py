import os
from typing import List, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
import uuid

from app.core.logging import logger

class VectorStore:
    """Vector database service using Qdrant for semantic search"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333")
        )
        
        # Initialize sentence transformer model
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        
        # Collection names
        self.agents_collection = "agents"
        self.schemas_collection = "schemas"
        
        # Initialize collections
        self._init_collections()

    def _init_collections(self):
        """Initialize Qdrant collections"""
        
        try:
            # Create agents collection
            self.client.recreate_collection(
                collection_name=self.agents_collection,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            
            # Create schemas collection
            self.client.recreate_collection(
                collection_name=self.schemas_collection,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            
            logger.info("Vector store collections initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {str(e)}")

    async def index_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        input_schema: dict,
        output_schema: dict,
        sample_response: dict,
        metadata: dict
    ):
        """Index an agent for semantic search"""
        
        # Create text representation
        text = self._create_agent_text(
            name, description, input_schema, output_schema, sample_response
        )
        
        # Generate embedding
        embedding = await self.get_embedding(text)
        
        # Store in Qdrant
        point = PointStruct(
            id=agent_id,
            vector=embedding.tolist(),
            payload={
                "agent_id": agent_id,
                "name": name,
                "description": description,
                "verification_level": metadata.get("verification_level", "unverified"),
                "price_cents": metadata.get("price_cents", 0),
                "success_rate": metadata.get("success_rate", 0),
                "avg_latency_ms": metadata.get("avg_latency_ms", 1000)
            }
        )
        
        self.client.upsert(
            collection_name=self.agents_collection,
            points=[point]
        )
        
        logger.info(f"Indexed agent {agent_id} in vector store")

    async def search_agents(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict] = None
    ) -> List[Dict]:
        """Search for agents using semantic similarity"""
        
        # Generate query embedding
        query_embedding = await self.get_embedding(query)
        
        # Build filter if provided
        qdrant_filter = None
        if filters:
            conditions = []
            
            if "min_verification_level" in filters:
                # Note: This would need custom encoding for verification levels
                pass
            
            if "max_price_cents" in filters:
                conditions.append(
                    FieldCondition(
                        key="price_cents",
                        range=Range(lte=filters["max_price_cents"])
                    )
                )
            
            if "min_success_rate" in filters:
                conditions.append(
                    FieldCondition(
                        key="success_rate",
                        range=Range(gte=filters["min_success_rate"])
                    )
                )
            
            if conditions:
                qdrant_filter = Filter(must=conditions)
        
        # Search
        results = self.client.search(
            collection_name=self.agents_collection,
            query_vector=query_embedding.tolist(),
            filter=qdrant_filter,
            limit=top_k
        )
        
        # Format results
        agents = []
        for result in results:
            agent_data = result.payload
            agent_data["similarity_score"] = result.score
            agents.append(agent_data)
        
        return agents

    async def find_similar_schemas(
        self,
        schema: dict,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find similar schemas for mapping suggestions"""
        
        # Create text representation of schema
        schema_text = self._create_schema_text(schema)
        
        # Generate embedding
        embedding = await self.get_embedding(schema_text)
        
        # Search for similar schemas
        results = self.client.search(
            collection_name=self.schemas_collection,
            query_vector=embedding.tolist(),
            limit=top_k
        )
        
        similar_schemas = []
        for result in results:
            similar_schemas.append((
                result.payload.get("schema_fp"),
                result.score
            ))
        
        return similar_schemas

    async def index_schema(
        self,
        schema_fp: str,
        schema: dict,
        agent_id: Optional[str] = None
    ):
        """Index a schema for similarity search"""
        
        # Create text representation
        schema_text = self._create_schema_text(schema)
        
        # Generate embedding
        embedding = await self.get_embedding(schema_text)
        
        # Store in Qdrant
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload={
                "schema_fp": schema_fp,
                "agent_id": agent_id,
                "field_count": len(schema.get("properties", {})),
                "required_fields": schema.get("required", [])
            }
        )
        
        self.client.upsert(
            collection_name=self.schemas_collection,
            points=[point]
        )

    async def calculate_compatibility_score(
        self,
        source_schema: dict,
        target_schema: dict,
        source_data: Optional[dict] = None,
        target_data: Optional[dict] = None
    ) -> float:
        """Calculate compatibility score between schemas"""
        
        score = 0.0
        weights = {
            "field_overlap": 0.35,
            "type_compatibility": 0.15,
            "embedding_similarity": 0.20,
            "required_fields": 0.15,
            "data_similarity": 0.15
        }
        
        # Field overlap
        source_fields = set(source_schema.get("properties", {}).keys())
        target_fields = set(target_schema.get("properties", {}).keys())
        
        if source_fields and target_fields:
            overlap = len(source_fields.intersection(target_fields))
            field_overlap_score = overlap / max(len(source_fields), len(target_fields))
            score += field_overlap_score * weights["field_overlap"]
        
        # Type compatibility
        type_matches = 0
        type_total = 0
        
        for field in source_fields.intersection(target_fields):
            type_total += 1
            source_type = source_schema["properties"][field].get("type")
            target_type = target_schema["properties"][field].get("type")
            
            if source_type == target_type:
                type_matches += 1
            elif self._are_types_compatible(source_type, target_type):
                type_matches += 0.5
        
        if type_total > 0:
            score += (type_matches / type_total) * weights["type_compatibility"]
        
        # Embedding similarity
        source_text = self._create_schema_text(source_schema)
        target_text = self._create_schema_text(target_schema)
        
        source_embedding = await self.get_embedding(source_text)
        target_embedding = await self.get_embedding(target_text)
        
        cosine_sim = np.dot(source_embedding, target_embedding) / (
            np.linalg.norm(source_embedding) * np.linalg.norm(target_embedding)
        )
        score += max(0, cosine_sim) * weights["embedding_similarity"]
        
        # Required fields coverage
        source_required = set(source_schema.get("required", []))
        if source_required:
            covered = len(source_required.intersection(target_fields))
            score += (covered / len(source_required)) * weights["required_fields"]
        else:
            score += weights["required_fields"]  # No required fields is compatible
        
        # Data similarity if provided
        if source_data and target_data:
            data_sim = self._calculate_data_similarity(source_data, target_data)
            score += data_sim * weights["data_similarity"]
        else:
            # Skip data similarity if not provided
            score += 0.5 * weights["data_similarity"]
        
        return min(1.0, score)

    async def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        
        return self.encoder.encode(text)

    def _create_agent_text(
        self,
        name: str,
        description: str,
        input_schema: dict,
        output_schema: dict,
        sample_response: dict
    ) -> str:
        """Create text representation of agent for embedding"""
        
        parts = [name]
        
        if description:
            parts.append(description)
        
        # Add schema field names
        if input_schema and "properties" in input_schema:
            parts.append("input: " + " ".join(input_schema["properties"].keys()))
        
        if output_schema and "properties" in output_schema:
            parts.append("output: " + " ".join(output_schema["properties"].keys()))
        
        # Add sample response keys
        if sample_response:
            parts.append("sample: " + " ".join(str(sample_response)[:200]))
        
        return " ".join(parts)

    def _create_schema_text(self, schema: dict) -> str:
        """Create text representation of schema for embedding"""
        
        parts = []
        
        if "properties" in schema:
            for field, spec in schema["properties"].items():
                parts.append(f"{field}:{spec.get('type', 'unknown')}")
        
        if "required" in schema:
            parts.append("required:" + ",".join(schema["required"]))
        
        return " ".join(parts)

    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two JSON schema types are compatible"""
        
        compatible = {
            ("string", "number"),
            ("string", "integer"),
            ("number", "integer"),
            ("integer", "number"),
            ("string", "boolean")
        }
        
        return (type1, type2) in compatible or (type2, type1) in compatible

    def _calculate_data_similarity(self, data1: dict, data2: dict) -> float:
        """Calculate similarity between two data objects"""
        
        if not data1 or not data2:
            return 0.5
        
        # Simple key overlap
        keys1 = set(data1.keys())
        keys2 = set(data2.keys())
        
        if not keys1 or not keys2:
            return 0.5
        
        overlap = len(keys1.intersection(keys2))
        return overlap / max(len(keys1), len(keys2))
