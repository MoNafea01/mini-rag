import os
from helpers.config import get_settings, Settings

class BaseController:
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    
    def __init__(self):
        self.app_settings: Settings = get_settings()

        self.file_dir = os.path.join(BaseController.BASE_DIR, self.app_settings.FILE_STORAGE_PATH)
        os.makedirs(self.file_dir, exist_ok=True)
