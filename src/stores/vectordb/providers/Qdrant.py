from typing import List
from qdrant_client import QdrantClient, models
from ..VectorDBInterface import VectorDBInterface
import logging
from ..utils import get_distance_metrics
from ..VectorDBEnums import VectorDBEnums
from models.db_schemas import RetrievedDocument

class Qdrant(VectorDBInterface):
    def __init__(self, 
                 db_path: str, 
                 db_url: str,
                 distance_metric: str,
                 default_vector_size: int,
                 *args, **kwargs):
        
        self.client = None
        self.db_path = db_path
        self.db_url = db_url
        self.distance_metric = None
        self.default_vector_size = default_vector_size
        
        metrics_map = get_distance_metrics(vectordb_type=VectorDBEnums.QDRANT.value)
        
        if distance_metric in metrics_map:
            self.distance_metric = metrics_map[distance_metric]
        
        else:
            raise ValueError(f"Invalid distance metric: {distance_metric}")
        
        self.logger = logging.getLogger('uvicorn')
        
    async def connect(self):
        if self.db_url:
            self.client = QdrantClient(url=self.db_url)
            return
        
        self.client = QdrantClient(path=self.db_path)
    
    async def disconnect(self):
        self.client = None
    
    async def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    async def list_collections(self) -> List:
        return self.client.get_collections()
    
    async def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name).model_dump()
    
    async def delete_collection(self, collection_name: str):
        if await self.is_collection_existed(collection_name):
            self.logger.info(f"Deleting collection: {collection_name}")
            return self.client.delete_collection(collection_name=collection_name)
    
    async def create_collection(self, 
                          collection_name: str, 
                          embedding_size: int, 
                          do_reset: bool=False):
        if do_reset: 
            _ = await self.delete_collection(collection_name=collection_name)
        
        if not await self.is_collection_existed(collection_name):
            self.logger.info(f"Creating Qdrant Collection: {collection_name}.")
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=embedding_size,
                                                   distance=self.distance_metric))
            return True
        
        return False
    
    async def insert_one(self, 
                   collection_name: str, 
                   text: str,
                   vector: list, 
                   metadata: dict=None, 
                   record_id: str=None):
        
        if not await self.is_collection_existed(collection_name):
            self.logger.error(f"Cannot insert into Collection: {collection_name} does not exist.")
            return False
        
        try:
            self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=record_id, 
                        vector=vector, 
                        payload={
                            'text':text,'metadata':metadata
                            }
                        )
                    ]
                )
        except Exception as e:
            self.logger.error(f"Error inserting record into {collection_name}: {e}")
        
        return True
    
    async def insert_many(self, 
                    collection_name: str, 
                    texts: list,
                    vectors: list, 
                    metadatas: list=None, 
                    record_ids: list=None,
                    batch_size: int=50):
        
        if not await self.is_collection_existed(collection_name):
            self.logger.error(f"Cannot insert into Collection: {collection_name} does not exist.")
            return False
        
        if metadatas is None:
            metadatas = [None] * len(texts)
        
        if record_ids is None:
            record_ids = list(range(len(texts)))
        
        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]
            
            batch_records = [models.Record(
                id=batch_record_ids[j],
                vector=batch_vectors[j],
                payload={
                    'text':batch_texts[j],
                    'metadata':batch_metadatas[j]
                    }
                ) for j in range(len(batch_texts))]
            try:
                _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records
                    )
            except Exception as e:
                self.logger.error(f"Error inserting batch starting at index {i}: {e}")
                return False
            
        return True
            
    
    async def search_by_vector(self, 
                         collection_name: str, 
                         query_vector: list,
                         top_k: int=5) -> List[RetrievedDocument]:
        
        if not await self.is_collection_existed(collection_name):
            self.logger.error(f"Cannot search Collection: {collection_name} does not exist.")
            return []
        
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k
            )
        
        if not results or len(results) == 0:
            return None
        
        return [
            RetrievedDocument(
                text=res.payload.get('text', ''),
                score=res.score,
            ) for res in results
        ]
