import os
import aiofiles as aio
from fastapi import APIRouter, UploadFile, status, Depends
from fastapi.responses import JSONResponse

from controllers import DataController, ProjectController
from helpers.config import get_settings, Settings
from models import FileValidationMessage

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, 
                      file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    
    
    # Validate file extension
    data_controller = DataController()
    is_valid, message = data_controller.validate_file(file)

    if is_valid == False:
        return JSONResponse(content=message, status_code=status.HTTP_400_BAD_REQUEST)

    project_dir_path = ProjectController().get_project_path(project_id)
    generated_file_info = data_controller.generate_unique_filename(file.filename, project_dir_path)
    file_path = generated_file_info.get("path")

    try:
        async with aio.open(file_path, 'wb') as out_file:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await out_file.write(chunk)

            return JSONResponse(content=FileValidationMessage.FILE_UPLOADED.value.format(filename=generated_file_info.get("filename")), 
                                status_code=status.HTTP_201_CREATED)
    except Exception as e:
        return JSONResponse(content=FileValidationMessage.FILE_UPLOADED_ERROR.value.format(filename=generated_file_info.get("filename")), status_code=status.HTTP_400_BAD_REQUEST)
    
    return JSONResponse(content=message, status_code=status.HTTP_200_OK)
