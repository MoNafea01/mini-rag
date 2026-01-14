from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes import base, data, nlp, settings
from helpers.config import get_settings
from stores import LLMFactory, VectorDBFactory
from stores.llm.templates.template_parser import TemplateParser
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from models.enums import DatabaseType

logger = logging.getLogger('uvicorn.error')


async def initialize_database_connection(app: FastAPI, settings):
    """Initialize or reinitialize database connection based on DB_TYPE"""
    # Close existing connections if they exist
    if hasattr(app, 'db_engine') and app.db_engine:
        await app.db_engine.dispose()
        logger.info("🛑 Previous database engine disposed")
    
    # Initialize MongoDB connection (always available)
    if not hasattr(app, 'mongo_conn') or app.mongo_conn is None:
        app.mongo_conn = AsyncIOMotorClient(settings.MONGO_URI)
    
    # Initialize PostgreSQL connection (always available)
    pg_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DB}"
    app.db_engine = create_async_engine(pg_conn)
    
    # Create PostgreSQL session factory (needed for PgVector)
    app.pg_session_factory = async_sessionmaker(
        app.db_engine, 
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Set active db_client based on DB_TYPE
    if settings.DB_TYPE == DatabaseType.MONGODB.value:
        app.db_client = app.mongo_conn[settings.MONGODB_NAME]
        logger.info("✅ Using MongoDB as active database")
    else:
        app.db_client = app.pg_session_factory
        logger.info("✅ Using PostgreSQL as active database")


async def initialize_llm_clients(app: FastAPI, settings):
    """Initialize or reinitialize LLM clients"""
    llm_factory = LLMFactory(settings)
    
    # generation client
    app.generation_client = llm_factory.create(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    logger.info(f"✅ Generation client initialized: {settings.GENERATION_BACKEND}")
    
    # embedding client
    app.embedding_client = llm_factory.create(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(
        settings.EMBEDDING_MODEL_ID, 
        settings.EMBEDDING_MODEL_SIZE)
    logger.info(f"✅ Embedding client initialized: {settings.EMBEDDING_BACKEND}")


async def initialize_vector_db(app: FastAPI, settings):
    """Initialize or reinitialize vector database"""
    # Disconnect existing connection if it exists
    if hasattr(app, 'vectordb_client') and app.vectordb_client:
        try:
            app.vectordb_client.disconnect()
            logger.info("🛑 Previous VectorDB connection closed")
        except:
            pass
    
    # PgVector always needs PostgreSQL session factory, regardless of main DB_TYPE
    # Qdrant doesn't use db_client, so it doesn't matter what we pass
    db_client_for_vector = app.pg_session_factory
    
    vectordb_factory = VectorDBFactory(settings, db_client=db_client_for_vector)
    app.vectordb_client = vectordb_factory.create(settings.VECTOR_DB_BACKEND)
    await app.vectordb_client.connect()
    logger.info(f"✅ VectorDB connected: {settings.VECTOR_DB_BACKEND}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # Initialize all connections
    await initialize_database_connection(app, settings)
    await initialize_llm_clients(app, settings)
    await initialize_vector_db(app, settings)
    
    # template parser
    app.template_parser = TemplateParser(language=settings.PRIMARY_LANGUAGE, 
                                         default_language=settings.DEFAULT_LANGUAGE)
    logger.info("✅ Template parser initialized")
    
    yield
    
    # Shutdown
    await app.db_engine.dispose()
    logger.info("🛑 Database connection closed")
    await app.vectordb_client.disconnect()
    logger.info("🛑 VectorDB connection closed")

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
app.include_router(settings.settings_router)
