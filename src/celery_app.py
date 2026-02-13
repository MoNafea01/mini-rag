from celery import Celery
from helpers.config import get_settings
from stores import LLMFactory, VectorDBFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from models.enums import DatabaseType

logger = logging.getLogger("celery.worker")

settings = get_settings()

class CeleryContext:
    def __init__(self):
        self.db_engine = None
        self.db_client = None
        self.generation_client = None
        self.embedding_client = None
        self.vectordb_client = None
        self.template_parser = None

async def get_setup_utils():
    settings = get_settings()
    ctx = CeleryContext()
    
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DB}"
    db_engine = create_async_engine(postgres_conn)
    ctx.db_engine = db_engine
    
    pg_session_factory = async_sessionmaker(
        db_engine, 
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Set active db_client based on DB_TYPE
    if settings.DB_TYPE == DatabaseType.MONGODB.value:
        db_client = AsyncIOMotorClient(settings.MONGO_URI)
        logger.info("✅ Using MongoDB as active database")
    else:
        db_client = pg_session_factory
        logger.info("✅ Using PostgreSQL as active database")
    
    ctx.db_client = db_client

    llm_provider_factory = LLMFactory(settings)
    vectordb_provider_factory = VectorDBFactory(settings=settings, db_client=db_client)

    # generation client
    generation_client = llm_provider_factory.create(provider_cls=settings.GENERATION_BACKEND)
    generation_client.set_generation_model(model_id = settings.GENERATION_MODEL_ID)
    
    ctx.generation_client = generation_client

    # embedding client
    embedding_client = llm_provider_factory.create(provider_cls=settings.EMBEDDING_BACKEND)
    embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                             embedding_size=settings.EMBEDDING_MODEL_SIZE)
    ctx.embedding_client = embedding_client
    
    # vector db client
    vectordb_client = vectordb_provider_factory.create(
        provider_cls=settings.VECTOR_DB_BACKEND
    )
    await vectordb_client.connect()
    
    ctx.vectordb_client = vectordb_client

    template_parser = TemplateParser(
        language=settings.PRIMARY_LANGUAGE,
        default_language=settings.PRIMARY_LANGUAGE,
    )

    ctx.template_parser = template_parser
    
    return ctx

# Create Celery application instance
celery_app = Celery(
    "minirag",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.mail_service",
        "tasks.file_processing"
    ]
)

# Configure Celery with essential settings
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    
    # Task safety - Late acknowledgment prevents task loss on worker crash
    task_acks_late=settings.CELERY_ACKS_LATE,
    
    # Time limits - Prevent hanging tasks
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    
    # Result backend - Store results for status tracking
    task_ignore_result=False,
    result_expires=3600,  
    
    # Worker settings
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    
    # Connection settings for better reliability
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    
    task_routes={
        "tasks.mail_service.send_email_reports": {"queue": "mail_server_queue"}, 
        "tasks.file_processing.process_data": {"queue": "data_processing_queue"}
    },
)

celery_app.conf.default_queue = "default"
