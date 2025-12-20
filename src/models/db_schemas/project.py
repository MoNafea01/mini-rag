from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson.objectid import ObjectId


class Project(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    project_id: str = Field(..., min_length=1, max_length=100)
    
    @field_validator("project_id")
    def validate_project_id(cls, v):
        if not v.isalnum():
            raise ValueError("project_id must be alphanumeric")
        return v
    
    
    class Config:
        arbitrary_types_allowed = True

    
    @classmethod
    def get_indexes(cls):
        return [
            {
                "name": "project_id_index_1",   # Index name
                "keys": [("project_id", 1)],     # 1 for ascending order, -1 for descending order
                "unique": True
            }
        ]
