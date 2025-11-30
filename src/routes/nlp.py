import logging
from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from .schemas import PushRequest, SearchRequest
from models import ProjectModel, ChunkModel
from controllers import NLPController
from models.enums import ResponseMessage
from helpers.utils import message_handler

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: str,
                        push_request: PushRequest):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    if not project:
        return JSONResponse(
            content=message_handler(ResponseMessage.PROJECT_NOT_FOUND.value.format(project_id=project_id)),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client
    )
    
    pg_num = 1
    pg_size = 50
    inserted_count = 0
    idx  = 0
    
    while True:
        chunks = await chunk_model.get_project_chunks(project_id=project.project_id, page=pg_num, page_size=pg_size)
        
        paged_chunks = chunks[(pg_num - 1) * pg_size : pg_num * pg_size]
        if not paged_chunks:
            break
        
        chunks_ids = list(range(idx, idx + len(paged_chunks)))
        idx += len(paged_chunks)
        
        pg_num += 1
        is_inserted = nlp_controller.index_into_vector_db(project=project, chunks=paged_chunks, chunks_ids=chunks_ids, do_reset=push_request.do_reset)
        
        if not is_inserted:
            return JSONResponse(
                content=message_handler(ResponseMessage.VECTOR_DB_INDEXING_FAILED.value.format(project_id=project_id)),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        inserted_count += len(paged_chunks)
    
    return JSONResponse(
        content=message_handler(ResponseMessage.VECTOR_DB_INDEXING_SUCCESS.value.format(project_id=project_id), inserted_count=inserted_count),
        status_code=status.HTTP_200_OK
    )


@nlp_router.get("/index/info/{project_id}")
async def get_index_info(request: Request, project_id: str):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    if not project:
        return JSONResponse(
            content=message_handler(ResponseMessage.PROJECT_NOT_FOUND.value.format(project_id=project_id)),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client
    )
    
    collection_info = nlp_controller.get_vector_collection_info(project=project)
    
    return JSONResponse(
        content=message_handler(ResponseMessage.VECTOR_DB_COLLECTION_INFO_RETRIEVED.value.format(project_id=project_id), collection_info=collection_info),
        status_code=status.HTTP_200_OK
    )

@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    if not project:
        return JSONResponse(
            content=message_handler(ResponseMessage.PROJECT_NOT_FOUND.value.format(project_id=project_id)),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client
    )
    
    result = nlp_controller.search_vector_db(project=project, query_text=search_request.query, top_k=search_request.top_k)
    
    if not result:
        return JSONResponse(
            content=message_handler(ResponseMessage.VECTOR_DB_SEARCH_FAILED.value.format(project_id=project_id)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return JSONResponse(
        content=message_handler(ResponseMessage.VECTOR_DB_SEARCH_COMPLETED.value.format(project_id=project_id), search_results=result),
        status_code=status.HTTP_200_OK
    )
