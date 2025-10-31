from .BaseController import BaseController
from fastapi import UploadFile
from models import FileValidationMessage, ResponseStatus
import os, re

class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 2**20  # 1 MB in bytes
    
    def validate_file(self, file:UploadFile) -> bool:
        file_extension = file.content_type
        allowed_types = self.app_settings.FILE_ALLOWED_TYPES
        max_size = self.app_settings.FILE_MAX_SIZE_MB
        
        if file_extension not in allowed_types:
            return ResponseStatus.FAILURE.value, {
                "message": FileValidationMessage.TYPE_NOT_ALLOWED.value.format(
                    file_extension=file_extension,allowed_types=", ".join(allowed_types)
                    )
                }
            
        if file.size > max_size * self.size_scale:
            return ResponseStatus.FAILURE.value, {
                "message": FileValidationMessage.SIZE_EXCEEDED.value.format(max_size=max_size)
                }

        return ResponseStatus.SUCCESS.value, {"message": FileValidationMessage.VALID_FILE.value}

    def generate_unique_filename(self, original_filename: str, project_path: str) -> str:
        random_str = self.generate_random_string()
        original_filename = self.get_clean_file_name(original_filename)
        is_new = False
        while not is_new:
            file_path = os.path.join(project_path, f"{random_str}_{original_filename}")
            if not os.path.exists(file_path):
                is_new = True
            else:
                random_str = self.generate_random_string()
        
        return {
            "filename": f"{random_str}_{original_filename}",
            "path": file_path
        }

    def get_clean_file_name(self, filename: str) -> str:
        # Remove any unwanted characters from the filename
        cleaned_file_name = re.sub(r'[^\w.]', '', filename.strip())
        cleaned_file_name = cleaned_file_name.replace(" ", "_")
        return cleaned_file_name
