from typing import List
from qdrant_client import QdrantClient, models
from ..VectorDBInterface import VectorDBInterface
import logging
from ..utils import get_distance_metrics

class Qdrant(VectorDBInterface):
    def __init__(self, db_path: str, distance_metric: str):
        self.client = None
        self.db_path = db_path
        self.distance_metric = None
        
        metrics_map = get_distance_metrics(special_map={"euclidean": "EUCLID"})
        
        if distance_metric in metrics_map:
            self.distance_metric = metrics_map[distance_metric]
        
        else:
            return ValueError(f"Invalid distance metric: {distance_metric}")
        
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        self.client = QdrantClient(path=self.db_path)
    
    def disconnect(self):
        self.client = None
    
    def is_collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    def list_collections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name).model_dump()
    
    def delete_collection(self, collection_name: str):
        if self.is_collenction_exists(collection_name):
            return self.client.delete_collection(collection_name=collection_name)
    
    def create_collection(self, 
                          collection_name: str, 
                          embedding_size: int, 
                          do_reset: bool=False):
        if do_reset: 
            _ = self.delete_collection(collection_name=collection_name)
        
        if not self.is_collenction_exists(collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=embedding_size,
                                                   distance=self.distance_metric))
            return True
        
        return False
    
    def insert_one(self, 
                   collection_name: str, 
                   text: str,
                   vector: list, 
                   metadata: dict=None, 
                   record_id: str=None):
        
        if not self.is_collenction_exists(collection_name):
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
    
    def insert_many(self, 
                    collection_name: str, 
                    texts: list,
                    vectors: list, 
                    metadatas: list=None, 
                    record_ids: list=None,
                    batch_size: int=50):
        
        if not self.is_collection_exists(collection_name):
            self.logger.error(f"Cannot insert into Collection: {collection_name} does not exist.")
            return False
        
        if metadatas is None:
            metadatas = [None] * len(texts)
        
        if record_ids is None:
            record_ids = [None] * len(texts)
        
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
            
    
    def search_by_vector(self, 
                         collection_name: str, 
                         query_vector: list,
                         top_k: int=5) -> list:
        
        if not self.is_collection_exists(collection_name):
            self.logger.error(f"Cannot search Collection: {collection_name} does not exist.")
            return []
        
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k
            )
    