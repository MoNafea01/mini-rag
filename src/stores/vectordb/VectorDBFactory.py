from helpers.config import Settings
from . import VECTOR_DB_REGISTRY
from controllers.BaseController import BaseController
from typing import Type
from .VectorDBInterface import VectorDBInterface
from sqlalchemy.ext.asyncio import async_sessionmaker

class VectorDBFactory:
    def __init__(self, settings: Settings, db_client: async_sessionmaker=None):
        self.settings = settings
        self.base_controller = BaseController()
        self.db_client = db_client
    
    def create(self, provider_cls: str):
        Provider: Type[VectorDBInterface] = VECTOR_DB_REGISTRY.get(provider_cls)
        
        if not Provider:
            return None
        
        db_path = self.base_controller.get_database_path(db_name=self.settings.VECTOR_DB_PATH_NAME)
        db_url = self.settings.QDRANT_URL if self.settings.VECTOR_DB_BACKEND == "QDRANT" else None
        
        return Provider(
            db_path=db_path,
            db_url=db_url,
            db_client=self.db_client,
            distance_metric=self.settings.VECTOR_DB_DISTANCE_METRIC,
            index_threshold=self.settings.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            default_vector_size=self.settings.EMBEDDING_MODEL_SIZE
        )
