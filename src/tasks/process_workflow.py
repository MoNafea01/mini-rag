from celery import chain
from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import logging
import asyncio

from tasks.file_processing import process_data as process_data_task
from tasks.data_indexing import _index_data

logger = logging.getLogger("celery.task")

@celery_app.task(bind=True, 
                name="tasks.process_workflow.push_task",
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60}
            )
def push_task(self, prev_task_result):
    project_id = prev_task_result.get("project_id")
    do_reset = prev_task_result.get("do_reset")
    
    task_result = asyncio.run(
        _index_data(self, project_id, do_reset)
    )
    
    return {
        "status": "Indexing task initiated",
        "indexing_task_id": task_result.id,
        "project_id": project_id,
        "do_reset": do_reset
    }
    

@celery_app.task(bind=True, 
                name="tasks.process_workflow.process_and_push_workflow",
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60}
            )
def process_and_push_workflow(self, project_id, asset_name, chunk_size, overlap_size, do_reset):
    workflow = chain(
        process_data_task.s(project_id, asset_name, chunk_size, overlap_size, do_reset),
        push_task.s()
    )

    result = workflow.apply_async()
    
    return {
        "status": "Workflow initiated",
        "workflow_id": result.id,
        "tasks": [
            {
                "task_name": "process_data",
                "task_id": result.parent.id
            },
            {
                "task_name": "index_data",
                "task_id": result.id
            }
        ]
    }
