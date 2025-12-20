from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime as dt, timezone


class Asset(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    asset_id: str = Field(..., min_length=1, max_length=100)
    asset_project_id: str = Field(..., min_length=1, max_length=100)
    
    asset_name: str = Field(..., min_length=1)
    asset_type: str = Field(..., min_length=1)
    asset_size: int = Field(None, ge=0)
    asset_config: Optional[dict] = Field(default_factory=dict)
    asset_pushed_at: dt = Field(default_factory=lambda: dt.now(timezone.utc))

    @field_validator("asset_id")
    def validate_project_id(cls, v):
        if not v.isalnum():
            raise ValueError("asset_id must be alphanumeric")
        return v
    
    class Config:
        arbitrary_types_allowed = True

    
    @classmethod
    def get_indexes(cls):
        return [
            {
                "name": "asset_project_id_index_1",
                "keys": [("asset_project_id", 1)],
                "unique": False
            },
            {
                "name": "asset_id_name_index_1",
                "keys": [("asset_id", 1), ("asset_name", 1)],
                "unique": True
            },
        ]
