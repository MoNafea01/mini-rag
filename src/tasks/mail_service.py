from celery_app import celery_app
from helpers.config import get_settings
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger("celery.task")


@celery_app.task(bind=True, name="tasks.mail_service.send_email_reports")
def send_email_reports(self, mail_wait_seconds: int):
    return asyncio.run(_send_email_reports(self, mail_wait_seconds))

async def _send_email_reports(task_instance, mail_wait_seconds: int):
    started_at = str(datetime.now())
    task_instance.update_state(
        state="PROGRESS",
        meta={
            "started_at": started_at,
        }
    )
    
    for i in range(15):
        logger.info(f"Report {i+1} sent successfully.")
        await asyncio.sleep(mail_wait_seconds)
    
    
    return {
        "no. emails_sent": 15,
        "started_at": started_at,
        "completed_at": str(datetime.now())
    }