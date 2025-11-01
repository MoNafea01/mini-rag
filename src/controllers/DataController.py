from .BaseController import BaseController
from fastapi import UploadFile
from models import FileValidationMessage, ResponseStatus

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
