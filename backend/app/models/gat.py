from sqlalchemy import Column, String, Integer, JSON, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel

class GATModel(BaseModel):
    __tablename__ = "gat_models"
    
    model_version = Column(String, unique=True, nullable=False)
    status = Column(String, default="training")  # training, ready, deprecated
    
    # Model artifacts
    model_path = Column(String)  # Path to saved model
    embedding_dim = Column(Integer, default=384)
    num_layers = Column(Integer, default=3)
    
    # Training metadata
    training_started_at = Column(DateTime(timezone=True))
    training_completed_at = Column(DateTime(timezone=True))
    training_metrics = Column(JSON)  # Loss, accuracy, etc.
    
    # Node embeddings cache
    node_embeddings_version = Column(String)
    
    # Performance metrics
    avg_inference_time_ms = Column(Float)
    successful_recommendations = Column(Integer, default=0)
    total_recommendations = Column(Integer, default=0)
