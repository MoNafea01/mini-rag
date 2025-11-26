from enum import Enum


class ResponseMessage(Enum):
    TYPE_NOT_ALLOWED = "File type '{file_extension}' is not allowed. Allowed types: {allowed_types}"
    SIZE_EXCEEDED = "File size exceeds the maximum limit of {max_size} MB."
    VALID_FILE = "File is valid."
    FILE_UPLOADED = "File '{filename}' uploaded successfully."
    FILE_UPLOADED_ERROR = "Error uploading file '{filename}'."
    FILE_PROCESSING_SUCCESS = "Files processed successfully."
    FILE_PROCESSING_ERROR = "Error processing file with name '{asset_name}'."
    NO_FILES_FOUND_FOR_PROCESSING = "No files found for processing in project '{project_id}'."
    FILE_NOT_FOUND_FOR_PROCESSING = "File '{asset_name}' not found in project '{project_id}' for processing."