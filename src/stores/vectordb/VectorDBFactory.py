from helpers.config import Settings
from . import VECTOR_DB_REGISTRY
from controllers.BaseController import BaseController
from typing import Type
from .VectorDBInterface import VectorDBInterface

class VectorDBFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_controller = BaseController()
    
    def create(self, provider_cls: str):
        Provider: Type[VectorDBInterface] = VECTOR_DB_REGISTRY.get(provider_cls)
        
        if not Provider:
            return None
        
        db_path = self.base_controller.get_database_path(db_name=self.settings.VECTOR_DB_PATH_NAME)
        
        return Provider(
            db_path=db_path,
            distance_metric=self.settings.VECTOR_DB_DISTANCE_METRIC
        )
