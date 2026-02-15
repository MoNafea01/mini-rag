import os
import aiofiles as aio
import logging
from typing import List, Union
from fastapi import APIRouter, UploadFile, status, Request, File, Depends
from fastapi.responses import JSONResponse
from controllers import DataController, ProjectController
from helpers.config import get_settings, Settings
from helpers.utils import generate_unique_filepath, message_handler
from models.enums import ResponseMessage, AssetTypeEnum
from models import ModelFactory, DatabaseType

from models.db_schemas import SchemaFactory
from .schemas import ProcessRequest

from tasks.file_processing import process_data as process_data_task
from tasks.process_workflow import process_and_push_workflow

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, 
                      project_id: Union[int, str], 
                      files: List[UploadFile] = File(...),
                      app_settings: Settings = Depends(get_settings)):
    
    if app_settings.DB_TYPE == DatabaseType.POSTGRES.value:
        try:
            project_id = int(project_id)
        except ValueError:
            return JSONResponse(
                content={"message": "Project ID must be a number"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    project_model = await ModelFactory.create_project_model(
        db_type=app_settings.DB_TYPE,
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    if not files:
        return JSONResponse(content={"message": "No files provided"}, status_code=status.HTTP_400_BAD_REQUEST)
    
    errors = []
    uploaded_files = []
    
    # Validate file extension
    data_controller = DataController()
    project_dir_path = ProjectController().get_project_path(project_id)
    
    for file in files:
        is_valid, message = data_controller.validate_file(file)
        if not is_valid:
            errors.append({"filename": file.filename, "error": message["message"]})
            continue

        file_info = generate_unique_filepath(file.filename, project_dir_path)
        file_path = file_info.get("path")

        try:
            async with aio.open(file_path, 'wb') as out_file:
                while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                    await out_file.write(chunk)
            uploaded_files.append(file_info)

        except Exception as e:
            errors.append({"filename": file.filename, "error": ResponseMessage.FILE_UPLOADED_ERROR.value.format(filename=file_info.get("filename"))})
            if os.path.exists(file_path):
                os.remove(file_path)
            continue
        
    if not uploaded_files:
        return JSONResponse(content={"errors": errors}, status_code=status.HTTP_400_BAD_REQUEST)
    
    # Storing the asset info in DB
    asset_model = await ModelFactory.create_asset_model(
        db_type=app_settings.DB_TYPE,
        db_client=request.app.db_client
    )
    
    messages = []
    
    for i, file_info in enumerate(uploaded_files):
        asset_full_name = f"{file_info.get('prefix')}_{file_info.get('filename')}"
        file_path = file_info.get("path")
        
        asset_schema = SchemaFactory.get_asset_schema(app_settings.DB_TYPE)

        asset_resource = asset_schema(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value,
            asset_name=asset_full_name,
            asset_size=os.path.getsize(file_path),
        )
        
        asset = await asset_model.create_asset(asset_resource)
        
        message = message_handler(
            ResponseMessage.FILE_UPLOADED.value.format(filename=file_info.get("filename")),
            file_id=asset.asset_id,
            file_name=asset.asset_name,
        )
        messages.append(message)
    response_content = {"files": messages}
    if errors:
        response_content["errors"] = errors
        
    status_code = status.HTTP_201_CREATED if not errors else status.HTTP_200_OK
    return JSONResponse(content=response_content, status_code=status_code)


@data_router.post("/process/{project_id}")
async def process_data(request: Request, 
                       project_id: Union[int, str], 
                       process_request: ProcessRequest,
                       app_settings: Settings = Depends(get_settings)):
    
    if app_settings.DB_TYPE == DatabaseType.POSTGRES.value:
        try:
            project_id = int(project_id)
        except ValueError:
            return JSONResponse(
                content={"message": "Project ID must be a number"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    asset_name = process_request.asset_name
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    
    task = process_data_task.delay(
        project_id=project_id,
        asset_name=asset_name, 
        chunk_size=chunk_size, 
        overlap_size=overlap_size, 
        do_reset=do_reset
    )
    
    return JSONResponse(
        content={ "message": "Data processing task has been initiated.", "task_id": task.id, "task_status": task.status }, 
        status_code=status.HTTP_202_ACCEPTED 
    )


@data_router.post("/process-and-push/{project_id}")
async def process_and_push(request: Request, 
                       project_id: Union[int, str], 
                       process_request: ProcessRequest,
                       app_settings: Settings = Depends(get_settings)):
    
    if app_settings.DB_TYPE == DatabaseType.POSTGRES.value:
        try:
            project_id = int(project_id)
        except ValueError:
            return JSONResponse(
                content={"message": "Project ID must be a number"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    asset_name = process_request.asset_name
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    
    task = process_and_push_workflow.delay(
        project_id=project_id,
        asset_name=asset_name, 
        chunk_size=chunk_size, 
        overlap_size=overlap_size, 
        do_reset=do_reset
    )
    
    return JSONResponse(
        content={ "message": "Data processing then pushing workflow has been initiated.", "task_id": task.id, "task_status": task.status }, 
        status_code=status.HTTP_202_ACCEPTED 
    )
