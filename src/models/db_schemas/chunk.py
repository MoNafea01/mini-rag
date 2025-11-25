from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

class DataChunk(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., ge=0)
    chunk_project_id: str = Field(..., min_length=1, max_length=100)
    
    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def get_indexes(cls):
        return [
            {
                "name": "chunk_project_id_index_1",     # Index name
                "keys": [("chunk_project_id", 1)],       # 1 for ascending order, -1 for descending order
                "unique": False                         # False because each project can have multiple chunks
            }
        ]
