import os
from helpers.config import get_settings, Settings


class BaseController:
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    
    def __init__(self):
        self.app_settings: Settings = get_settings()

        self.file_dir = os.path.join(BaseController.BASE_DIR, self.app_settings.FILE_STORAGE_PATH)
        self.db_dir = os.path.join(BaseController.BASE_DIR, self.app_settings.VECTOR_DB_PATH)
        os.makedirs(self.file_dir, exist_ok=True)

    def get_database_path(
        self, 
        db_name) -> str:
        
        db_path = os.path.join(self.db_dir, db_name)
        
        if not os.path.exists(db_path):
            os.makedirs(db_path)
            
        return db_path
