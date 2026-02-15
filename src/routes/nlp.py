from typing import List, Union
import logging
from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse

from helpers.config import Settings, get_settings
from models.enums.DatabaseTypeEnum import DatabaseType
from .schemas import PushRequest, SearchRequest, AnswerRequest
from models import ModelFactory
from controllers import NLPController
from models.enums import ResponseMessage
from helpers.utils import message_handler
from models.db_schemas import RetrievedDocument 
from tasks.data_indexing import index_data as index_data_task


logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, 
                        project_id: Union[int, str],
                        push_request: PushRequest,
                        app_settings: Settings = Depends(get_settings)):
    
    if app_settings.DB_TYPE == DatabaseType.POSTGRES.value:
        try:
            project_id = int(project_id)
        except ValueError:
            return JSONResponse(
                content={"message": "Project ID must be a number"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
    task = index_data_task.delay(
        project_id=project_id, 
        do_reset=push_request.do_reset
    )
    
    return JSONResponse(
        content={"message": "Data indexing task has been initiated", "task_id": task.id, "task_status": task.status},
        status_code=status.HTTP_202_ACCEPTED
    )
    


@nlp_router.get("/index/info/{project_id}")
async def get_index_info(request: Request, project_id: Union[int, str], app_settings: Settings = Depends(get_settings)):
    
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
    
    if not project:
        return JSONResponse(
            content=message_handler(ResponseMessage.PROJECT_NOT_FOUND.value.format(project_id=project_id)),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )
    try:
        collection_info = await nlp_controller.get_vector_collection_info(project=project)
    except Exception as e:
        logger.error(f"Failed to retrieve collection info for project {project_id}: {str(e)}")
        return JSONResponse(
            content=message_handler(ResponseMessage.VECTOR_DB_COLLECTION_INFO_RETRIEVAL_FAILED.value.format(project_id=project_id)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    return JSONResponse(
        content=message_handler(ResponseMessage.VECTOR_DB_COLLECTION_INFO_RETRIEVED.value.format(project_id=project_id), collection_info=collection_info),
        status_code=status.HTTP_200_OK
    )

@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, 
                       project_id: Union[int, str], 
                       search_request: SearchRequest,
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
    
    if not project:
        return JSONResponse(
            content=message_handler(ResponseMessage.PROJECT_NOT_FOUND.value.format(project_id=project_id)),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )
    
    result: List[RetrievedDocument] = await nlp_controller.search_vector_db(project=project, query_text=search_request.query, top_k=search_request.top_k)
    
    if not result:
        return JSONResponse(
            content=message_handler(ResponseMessage.VECTOR_DB_SEARCH_FAILED.value.format(project_id=project_id)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    result = [r.model_dump() for r in result]
    
    return JSONResponse(
        content=message_handler(ResponseMessage.VECTOR_DB_SEARCH_COMPLETED.value.format(project_id=project_id), search_results=result),
        status_code=status.HTTP_200_OK
    )


@nlp_router.post("/index/answer/{project_id}")
@nlp_router.post("/index/answer")
async def answer_query(request: Request, 
                       answer_request: AnswerRequest,
                       project_id: Union[int, str, None] = None,
                       app_settings: Settings = Depends(get_settings)):
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )
    
    # If no project_id provided, use simple chatbot mode (no RAG)
    if project_id is None:
        try:
            answer, full_prompt, chat_history = await nlp_controller.simple_chat(
                query_text=answer_request.query,
                max_output_tokens=answer_request.max_tokens,
                temperature=answer_request.temperature
            )
            
            if answer is None:
                return JSONResponse(
                    content=message_handler(ResponseMessage.ANSWER_GENERATION_FAILED.value.format(project_id="chatbot")),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return JSONResponse(
                content={
                    "message": "Chatbot response generated successfully",
                    "mode": "chatbot",
                    "answer": answer,
                    "full_prompt": full_prompt,
                    "chat_history": chat_history
                },
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Chatbot answer generation failed: {str(e)}")
            return JSONResponse(
                content={"message": f"Chatbot answer generation failed: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # RAG mode with project_id
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
    
    if not project:
        return JSONResponse(
            content=message_handler(ResponseMessage.PROJECT_NOT_FOUND.value.format(project_id=project_id)),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    try:
        answer, full_prompt, chat_history = await nlp_controller.answer_query(project=project, 
                                                                        query_text=answer_request.query, 
                                                                        top_k=answer_request.top_k, 
                                                                        max_output_tokens=answer_request.max_tokens, 
                                                                        temperature=answer_request.temperature)
    except Exception as e:
        logger.error(f"Answer generation failed for project {project_id}: {str(e)}")
        return JSONResponse(
            content=message_handler(ResponseMessage.ANSWER_GENERATION_FAILED.value.format(project_id=project_id)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    if answer is None:
        return JSONResponse(
            content=message_handler(ResponseMessage.ANSWER_GENERATION_FAILED.value.format(project_id=project_id)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return JSONResponse(
        content=message_handler(ResponseMessage.ANSWER_GENERATION_SUCCESS.value.format(project_id=project_id), answer=answer, full_prompt=full_prompt, chat_history=chat_history),
        status_code=status.HTTP_200_OK
    )

