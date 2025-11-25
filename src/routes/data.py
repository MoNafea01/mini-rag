import os
import aiofiles as aio
from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from controllers import DataController, ProjectController, ProcessController
from helpers.config import get_settings, Settings
from helpers.utils import generate_unique_filepath, message_handler
from models.enums import ResponseMessage, AssetTypeEnum
from models import ProjectModel, ChunkModel, AssetModel

from models.db_schemas import DataChunk, Asset
from .schemas import ProcessRequest

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, 
                      file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    # print(project)
    
    # Validate file extension
    data_controller = DataController()
    is_valid, message = data_controller.validate_file(file)

    if is_valid == False:
        return JSONResponse(content=message, status_code=status.HTTP_400_BAD_REQUEST)

    project_dir_path = ProjectController().get_project_path(project_id)
    file_info = generate_unique_filepath(file.filename, project_dir_path)
    file_path = file_info.get("path")

    try:
        async with aio.open(file_path, 'wb') as out_file:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await out_file.write(chunk)

    except Exception as e:
        return JSONResponse(content=ResponseMessage.FILE_UPLOADED_ERROR.value.format(filename=file_info.get("filename")), status_code=status.HTTP_400_BAD_REQUEST)

    # Storing the asset info in DB
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )
    asset_resource = Asset(
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_info.get("filename"),
        asset_size=os.path.getsize(file_path),
    )
    
    asset = await asset_model.create_asset(asset_resource)
    
    message = message_handler(
        ResponseMessage.FILE_UPLOADED.value.format(filename=file_info.get("filename")),
        file_id=str(asset.id),
        file_name=asset.asset_name,
    )
    return JSONResponse(content=message, status_code=status.HTTP_201_CREATED)

@data_router.post("/process/{project_id}")
async def process_data(request: Request, project_id: str, 
                       process_request: ProcessRequest):
    
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    process_controller = ProcessController(project_id)

    file_content = process_controller.get_file_content(file_id)
    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )
    
    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            content=message_handler(
                ResponseMessage.FILE_PROCESSING_ERROR.value.format(file_id=file_id)
            ),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    file_chunks_records = [DataChunk(
        chunk_text=chunk.page_content,
        chunk_metadata=chunk.metadata,
        chunk_order=i+1,
        chunk_project_id=project.project_id
        ) for i, chunk in enumerate(file_chunks)
    ]
    
    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )
    
    if do_reset == 1:
        await chunk_model.delete_chunks_by_id(project_id=project.project_id)
        
    no_records = await chunk_model.insert_many_chunks(file_chunks_records)
    
    message = message_handler(
        ResponseMessage.FILE_PROCESSING_SUCCESS.value,
        file_id=file_id,
        file_chunks=file_chunks,
        no_records=no_records
    )
    return message
