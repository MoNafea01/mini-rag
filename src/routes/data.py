import os
import aiofiles as aio
import logging
from typing import List
from fastapi import APIRouter, UploadFile, status, Request, File, Depends
from fastapi.responses import JSONResponse
from controllers import DataController, ProjectController, ProcessController
from helpers.config import get_settings, Settings
from helpers.utils import generate_unique_filepath, message_handler
from models.enums import ResponseMessage, AssetTypeEnum
from models import ProjectModel, ChunkModel, AssetModel

from models.db_schemas import DataChunk, Asset
from .schemas import ProcessRequest

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, 
                      files: List[UploadFile] = File(...),
                      app_settings: Settings = Depends(get_settings)):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    # print(project)
    
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
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )
    
    assets_count = await asset_model.count_assets(
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value
    )
    
    messages = []
    
    for i, file_info in enumerate(uploaded_files):
        asset_full_name = f"{file_info.get('prefix')}_{file_info.get('filename')}"
        file_path = file_info.get("path")
        
        asset_resource = Asset(
            asset_id=f"{assets_count + 1 + i}",
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
async def process_data(request: Request, project_id: str, 
                       process_request: ProcessRequest):
    
    asset_name = process_request.asset_name
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    process_controller = ProcessController(project_id)

    if asset_name:
        asset_record = await asset_model.get_asset_by_name(asset_name=asset_name, asset_project_id=project.project_id)
        if asset_record is None:
            return JSONResponse(
                content=message_handler(
                    ResponseMessage.FILE_NOT_FOUND_FOR_PROCESSING.value.format(
                        asset_name=asset_name,
                        project_id=project.project_id
                    )
                ),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        project_files = [asset_record]
    
    else:
        project_files = await asset_model.get_all_assets(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value
        )
    
    if len(project_files) == 0:
        return JSONResponse(
            content=message_handler(
                ResponseMessage.NO_FILES_FOUND_FOR_PROCESSING.value.format(project_id=project.project_id)
            ),
            status_code=status.HTTP_404_NOT_FOUND
        )
    project_files_names = list(map(lambda x: x.asset_name, project_files))

    chunk_model = await ChunkModel.create_instance(
            db_client=request.app.db_client
        )
        
    if do_reset == 1:
        await chunk_model.delete_chunks_by_id(project_id=project.project_id)
    
    no_files = 0
    no_records = 0
    files_names = []
    all_file_chunks = []
    warnings = {'content': []}
    for idx, asset_name in enumerate(project_files_names):
        file_content = process_controller.get_file_content(asset_name)
        
        if file_content is None:
            warning = f"File content is None or file not found: {asset_name}, skipping..."
            logger.warning(warning)
            
            warnings['content'].append({'id': idx+1, 
                             'name': asset_name, 
                             'message': warning})
            continue
        
        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )
        
        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                content=message_handler(
                    ResponseMessage.FILE_PROCESSING_ERROR.value.format(asset_name=asset_name)
                ),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        file_chunks_records = [DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i+1,
            chunk_project_id=project.project_id,
            chunk_asset_id=str(idx+1),
            ) for i, chunk in enumerate(file_chunks)
        ]
        
        no_records += await chunk_model.insert_many_chunks(file_chunks_records)
        
        no_files += 1
        files_names.append(asset_name)
        all_file_chunks.append(file_chunks)
    
    if len(warnings['content']) > 0:
        warnings['count'] = len(warnings['content'])
    
    message = message_handler(
        ResponseMessage.FILE_PROCESSING_SUCCESS.value,
        names=files_names,
        chunks=all_file_chunks,
        records_count=no_records,
        processed_files=no_files,
        warnings=warnings
    )
    
    return message
