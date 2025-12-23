import uuid
from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

class Asset(SQLAlchemyBase):
    __tablename__ = 'assets'
    
    asset_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    
    asset_name = Column(String, nullable=False)
    asset_type = Column(String(50), nullable=False)
    asset_size = Column(Integer, nullable=False)
    asset_config = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    asset_project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    project = relationship("Project", back_populates="assets")
    chunks = relationship("DataChunk", back_populates="asset")
    
    __table_args__ = (
        Index('ix_asset_project_id', asset_project_id),
    )
