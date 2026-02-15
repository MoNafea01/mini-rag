import uuid
from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, String, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

class CeleryTaskExecution(SQLAlchemyBase):
    __tablename__ = "celery_task_executions"
    
    execution_id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(255), nullable=False)
    task_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    status = Column(String(50), nullable=False, default="PENDING")
    
    task_args = Column(JSONB, nullable=True)
    task_args_hash = Column(String(64), nullable=False)
    result = Column(JSONB, nullable=True)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    __table_args__ = (
        Index('ixz_task_name_args_celery_hash', task_name, task_args_hash, task_id, unique=True),
        Index('ixz_task_execution_status', status),
        Index('ixz_task_execution_created_at', created_at),
        Index('ixz_task_id', task_id),
    )
