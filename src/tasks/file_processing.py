from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import logging
import asyncio

from fastapi import status
from controllers import ProcessController, NLPController
from helpers.utils import message_handler
from models.db_schemas.SchemaFactory import SchemaFactory
from models.enums import ResponseMessage, AssetTypeEnum
from models import ModelFactory

logger = logging.getLogger("celery.task")

@celery_app.task(bind=True, 
                 name="tasks.file_processing.process_data",
                 autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60}
            )
def process_data(self, project_id, asset_name, chunk_size, overlap_size, do_reset):
    return asyncio.run(_process_data(self, project_id, asset_name, chunk_size, overlap_size, do_reset))

async def _process_data(task_instance, project_id, asset_name, chunk_size, overlap_size, do_reset):
    # Access Celery context for connections
    ctx = await get_setup_utils()
    
    try:
        settings = get_settings()
        project_model = await ModelFactory.create_project_model(
            db_type=settings.DB_TYPE,
            db_client=ctx.db_client
        )
        
        asset_model = await ModelFactory.create_asset_model(
            db_type=settings.DB_TYPE,
            db_client=ctx.db_client
        )
        
        project = await project_model.get_project_or_create_one(project_id=project_id)
        process_controller = ProcessController(project_id)
        
        nlp_controller = NLPController(
            vectordb_client=ctx.vectordb_client,
            generation_client=ctx.generation_client,
            embedding_client=ctx.embedding_client,
            template_parser=ctx.template_parser
        )
        
        if asset_name:
            asset_record = await asset_model.get_asset_by_name(asset_name=asset_name, asset_project_id=project.project_id)
            if asset_record is None:
                
                task_instance.update_state(
                    state="FAILURE", 
                    meta=message_handler(
                        ResponseMessage.FILE_NOT_FOUND_FOR_PROCESSING.value.format(
                            asset_name=asset_name,
                            project_id=project.project_id
                        )
                    ),
                    status_code=status.HTTP_404_NOT_FOUND
                )
                
                raise Exception("File not found for processing")

                
            project_files = [asset_record]
        
        else:
            project_files = await asset_model.get_all_assets(
                asset_project_id=project.project_id,
                asset_type=AssetTypeEnum.FILE.value
            )
        
        if len(project_files) == 0:
            
            task_instance.update_state(
                state="FAILURE", 
                meta=message_handler(
                    ResponseMessage.NO_FILES_FOUND_FOR_PROCESSING.value.format(project_id=project.project_id)
                )
            )
            
            raise Exception("No files found for processing")

        # project_files_names = list(map(lambda x: x.asset_name, project_files))

        chunk_model = await ModelFactory.create_chunk_model(
                db_type=settings.DB_TYPE,
                db_client=ctx.db_client
            )
            
        if do_reset == 1:
            collection_name = nlp_controller.generate_collection_name(project.project_id)
            await ctx.vectordb_client.delete_collection(collection_name=collection_name)
            
            await chunk_model.delete_chunks_by_id(project_id=project.project_id)
        
        no_files = 0
        no_records = 0
        files_names = []
        all_file_chunks = []
        warnings = {'content': []}
        for idx, asset in enumerate(project_files):
            asset_name = asset.asset_name
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
                
                logger.warning(f"No chunks created for file: {asset_name}, skipping...")
                pass

            data_chunk_schema = SchemaFactory.get_chunk_schema(settings.DB_TYPE)
            file_chunks_records = [data_chunk_schema(
                chunk_text=chunk.page_content.replace("\x00", ""),
                chunk_metadata= {
                        k: (v.replace("\x00", "") if isinstance(v, str) else v)
                        for k, v in chunk.metadata.items()
                    },
                chunk_order=i+1,
                chunk_project_id=project.project_id,
                chunk_asset_id=asset.asset_id,
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
            records_count=no_records,
            processed_files=no_files,
            warnings=warnings
        )
        
        task_instance.update_state(
            state="SUCCESS",
            meta=message
        )
        
        return message
    except Exception as e:
        logger.error(f"Error in processing data: {str(e)}")
        task_instance.update_state(
            state="FAILURE",
            meta=message_handler(
                ResponseMessage.FILE_PROCESSING_ERROR.value.format(
                    asset_name=asset_name
                )
            )
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

