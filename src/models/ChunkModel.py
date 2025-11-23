from bson import ObjectId
from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from pymongo import InsertOne
from typing import List

class ChunkModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
    
    async def insert_chunk(self, chunk: DataChunk) -> DataChunk:
        result = self.collection.insert_one(chunk.model_dump(by_alias=True, exclude_unset=True))
        chunk._id = result.inserted_id
        return chunk

    async def get_chunk(self, chunk_id: str) -> DataChunk:
        chunk = await self.collection.find_one({
            "_id": ObjectId(chunk_id)
        })
        
        if chunk:
            return DataChunk(**chunk)
        
        return None
    
    async def insert_many_chunks(self, chunks: List[DataChunk], batch_size: int = 100) -> List[DataChunk]:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i: i + batch_size]
            
            ops = [
                InsertOne(chunk.model_dump(by_alias=True, exclude_unset=True)) for chunk in batch
            ]
            self.collection.bulk_write(ops)
        
        return len(chunks)
    
    async def delete_chunks_by_id(self, project_id: ObjectId):
        result = await self.collection.delete_many({'chunk_project_id': project_id})
        
        return result.deleted_count
