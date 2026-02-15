from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from bson.objectid import ObjectId
from datetime import datetime


class CeleryTaskExecution(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    task_name: str = Field(..., min_length=1, max_length=255)
    task_id: str = Field(...)  # UUID as string in MongoDB
    
    status: str = Field(default="PENDING", max_length=50)
    
    task_args: Optional[Dict[str, Any]] = Field(default=None)
    task_args_hash: str = Field(..., max_length=64)
    result: Optional[Dict[str, Any]] = Field(default=None)
    
    started_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def get_indexes(cls):
        return [
            {
                "name": "ixz_task_name_args_celery_hash",
                "keys": [("task_name", 1), ("task_args_hash", 1), ("task_id", 1)],
                "unique": True
            },
            {
                "name": "ixz_task_execution_status",
                "keys": [("status", 1)],
                "unique": False
            },
            {
                "name": "ixz_task_execution_created_at",
                "keys": [("created_at", 1)],
                "unique": False
            },
            {
                "name": "ixz_task_id",
                "keys": [("task_id", 1)],
                "unique": False
            },
        ]
