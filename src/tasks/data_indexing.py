from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import logging
import asyncio

from tqdm.auto import tqdm
from models import ModelFactory
from controllers import NLPController
from models.enums import ResponseMessage
from helpers.utils import message_handler
from utils.idempotency_manager import IdempotencyManager

logger = logging.getLogger("celery.task")

@celery_app.task(bind=True, 
                name="tasks.data_indexing.index_data",
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60}
            )
def index_data(self, project_id, do_reset):
    return asyncio.run(_index_data(self, project_id, do_reset))

async def _index_data(task_instance, project_id, do_reset):
    
    ctx = await get_setup_utils()
    settings = get_settings()
    
    try:
        # Idempotency check
        idempotency_manager = IdempotencyManager(db_client=ctx.db_client, db_engine=ctx.db_engine, db_type=ctx.DB_TYPE)
        task_args = {
            "project_id": project_id,
            "do_reset": do_reset
        }
        task_name = "tasks.data_indexing.index_data"
        
        should_execute, existing_task = await idempotency_manager.should_execute_task(
            task_name=task_name,
            task_args=task_args,
            task_id=task_instance.request.id,
            task_time_limit=settings.CELERY_TASK_TIME_LIMIT
        )
        
        if not should_execute:
            logger.warning(f"Can not handle the task | status: {existing_task.status}")
            return existing_task.result
        
        task_record = None
        if existing_task:
            # Update existing task with new celery task ID
            await idempotency_manager.update_task_status(
                execution_id=idempotency_manager.get_task_record_id(existing_task),
                status='PENDING'
            )
            task_record = existing_task
        else:
            # Create new task record
            task_record = await idempotency_manager.create_task_record(
                task_name=task_name,
                task_args=task_args,
                task_id=task_instance.request.id
            )
        
        task_record_id = idempotency_manager.get_task_record_id(task_record)
        
        # Update status to STARTED
        await idempotency_manager.update_task_status(
            execution_id=task_record_id,
            status='STARTED'
        )
        
        project_model = await ModelFactory.create_project_model(
            db_type=ctx.DB_TYPE,
            db_client=ctx.db_client
        )
    
        project = await project_model.get_project_or_create_one(project_id=project_id)
        
        if not project:
            task_instance.update_state(
                state="FAILURE",
                meta=message_handler(ResponseMessage.PROJECT_NOT_FOUND.value.format(project_id=project_id))
            )
            await idempotency_manager.update_task_status(
                execution_id=task_record_id,
                status='FAILURE',
                result=message_handler(ResponseMessage.PROJECT_NOT_FOUND.value.format(project_id=project_id))
            )
            raise Exception(f"Project with ID {project_id} not found for indexing.")
        
        chunk_model = await ModelFactory.create_chunk_model(
            db_type=ctx.DB_TYPE,
            db_client=ctx.db_client
        )
        
        nlp_controller = NLPController(
            vectordb_client=ctx.vectordb_client,
            generation_client=ctx.generation_client,
            embedding_client=ctx.embedding_client,
            template_parser=ctx.template_parser
        )
        
        collection_name = nlp_controller.generate_collection_name(project_id=project.project_id)
        
        await ctx.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=nlp_controller.embedding_client.embedding_size,
            do_reset=do_reset
        )
        
        pg_num = 1
        pg_size = 50
        inserted_count = 0
        idx  = 0
        is_first_batch = True
        
        total_chunks_count = await chunk_model.count_chunks_by_project(project_id=project.project_id)
        pbar = tqdm(
            total=total_chunks_count, 
            desc=f"Indexing Project {project_id} into VectorDB", 
            unit="chunk",
            position=0,
        )
        
        while True:
            paged_chunks = await chunk_model.get_project_chunks(project_id=project.project_id, page=pg_num, page_size=pg_size)
            
            if not paged_chunks or len(paged_chunks) == 0:
                break
            
            chunks_ids = [c.chunk_id for c in paged_chunks]
            
            # Only reset on first batch
            do_reset_batch = do_reset if is_first_batch else False
            
            is_inserted = await nlp_controller.index_into_vector_db(
                project=project, 
                chunks=paged_chunks, 
                chunks_ids=chunks_ids
            )
            
            if not is_inserted:
                task_instance.update_state(
                    state="FAILURE",
                    meta=message_handler(ResponseMessage.VECTOR_DB_INDEXING_FAILED.value.format(project_id=project_id))
                )
                await idempotency_manager.update_task_status(
                    execution_id=task_record_id,
                    status='FAILURE',
                    result=message_handler(ResponseMessage.VECTOR_DB_INDEXING_FAILED.value.format(project_id=project_id))
                )
                raise Exception(f"VectorDB indexing failed for project_id {project_id}")
            
            pbar.update(len(paged_chunks))
            inserted_count += len(paged_chunks)
            idx += len(paged_chunks)
            pg_num += 1
            is_first_batch = False
        
        message = message_handler(
            ResponseMessage.VECTOR_DB_INDEXING_SUCCESS.value.format(project_id=project_id), 
            inserted_count=inserted_count
        )
        
        task_instance.update_state(
            state="SUCCESS", 
            meta=message
        )
        
        await idempotency_manager.update_task_status(
            execution_id=task_record_id,
            status='SUCCESS',
            result=message
        )
        
        return message

    
    except Exception as e:
        logger.error(f"Error in index_data task for project_id {project_id}: {str(e)}")
        task_instance.update_state(
            state="FAILURE", 
            meta={"error": str(e)}
        )
        raise e
    
    finally:
            try:
                if ctx.db_engine:
                    await ctx.db_engine.dispose()
                if ctx.vectordb_client:
                    await ctx.vectordb_client.disconnect()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")
