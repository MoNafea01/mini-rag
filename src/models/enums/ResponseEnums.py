from enum import Enum

class ResponseStatus(Enum):
    SUCCESS = True
    FAILURE = False
    
class FileValidationMessage(Enum):
    TYPE_NOT_ALLOWED = "File type '{file_extension}' is not allowed. Allowed types: {allowed_types}"
    SIZE_EXCEEDED = "File size exceeds the maximum limit of {max_size} MB."
    VALID_FILE = "File is valid."
    FILE_UPLOADED = "File '{filename}' uploaded successfully."
    FILE_UPLOADED_ERROR = "Error uploading file '{filename}'."
