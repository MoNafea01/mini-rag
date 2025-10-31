from helpers.config import get_settings, Settings
import os, random, string

class BaseController:
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    
    def __init__(self):
        self.app_settings: Settings = get_settings()

        self.file_dir = os.path.join(BaseController.BASE_DIR, self.app_settings.FILE_STORAGE_PATH)
        os.makedirs(self.file_dir, exist_ok=True)
        
    def generate_random_string(self, length: int = 12) -> str:
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join(random.choice(letters_and_digits) for i in range(length))
