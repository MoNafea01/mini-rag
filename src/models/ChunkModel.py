from bson import ObjectId
from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from pymongo import InsertOne
from typing import List


class ChunkModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
    
    
    @classmethod
    async def create_instance(cls, db_client):
        isinstance = cls(db_client)
        await isinstance.init_collection()
        return isinstance
    
    
    async def init_collection(self):
        collection_name = DataBaseEnum.COLLECTION_CHUNK_NAME.value
        all_collections = await self.db_client.list_collection_names()
        self.collection = self.db_client[collection_name]
        
        if collection_name not in all_collections:
            print(f"⏳ Initializing collection: '{collection_name}'")
            indexes = DataChunk.get_indexes()
            for index in indexes:
                await self.collection.create_index(**index)
    
    
    async def insert_chunk(self, chunk: DataChunk) -> DataChunk:
        result = await self.collection.insert_one(chunk.model_dump(by_alias=True, exclude_unset=True))
        chunk.id = result.inserted_id
        return chunk

    
    async def get_chunk(self, chunk_id: str) -> DataChunk:
        chunk = await self.collection.find_one({
            "_id": ObjectId(chunk_id)
        })
        
        if chunk:
            return DataChunk(**chunk)
        
        return None
    
    
    async def insert_many_chunks(self, 
                                 chunks: List[DataChunk], 
                                 batch_size: int = 100) -> List[DataChunk]:
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i: i + batch_size]
            
            ops = [
                InsertOne(chunk.model_dump(by_alias=True, exclude_unset=True)) for chunk in batch
            ]
            await self.collection.bulk_write(ops)
        
        return len(chunks)
    
    async def get_project_chunks(self, 
                                 project_id: str, 
                                 page: int=1, 
                                 page_size: int = 50) -> List[DataChunk]:
        
        cursor = self.collection.find({'chunk_project_id': project_id}).skip((page-1) * page_size).limit(page_size)
        
        chunks = []
        async for chunk in cursor:
            chunks.append(DataChunk(**chunk))
        
        return chunks
    
    async def delete_chunks_by_id(self, project_id: str):
        result = await self.collection.delete_many({'chunk_project_id': project_id})
        
        return result.deleted_count
