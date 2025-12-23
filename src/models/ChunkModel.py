from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from typing import List
from sqlalchemy.future import select
from sqlalchemy import func, delete


class ChunkModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
    
    
    @classmethod
    async def create_instance(cls, db_client):
        isinstance = cls(db_client)
        return isinstance
    
    
    async def insert_chunk(self, chunk: DataChunk) -> DataChunk:
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)
        
        return chunk

    
    async def get_chunk(self, chunk_id: int) -> DataChunk:
        async with self.db_client() as session:
            async with session.begin():
                query = select(DataChunk).where(DataChunk.chunk_id == chunk_id)
                chunk = await session.execute(query).scalar_one_or_none()
                
        return chunk
    
    
    async def insert_many_chunks(self, chunks: List[DataChunk], batch_size: int = 100) -> List[DataChunk]:
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i: i + batch_size]
                    session.add_all(batch)
                await session.commit()
        
        return len(chunks)
    
    
    async def get_project_chunks(self, project_id: int, page: int=1, page_size: int = 50) -> List[DataChunk]:
        async with self.db_client() as session:
            async with session.begin():
                query = select(DataChunk).where(DataChunk.chunk_project_id == project_id).offset((page-1) * page_size).limit(page_size)
                result = await session.execute(query)
                chunks = result.scalars().all()
                
        return chunks

    
    async def delete_chunks_by_id(self, project_id: int):
        async with self.db_client() as session:
            async with session.begin():
                query = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(query)
                await session.commit()
        
        return result.rowcount
