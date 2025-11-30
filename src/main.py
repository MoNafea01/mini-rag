from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes import base, data, nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores import LLMFactory, VectorDBFactory
from stores.llm.templates.template_parser import TemplateParser
import logging

logger = logging.getLogger('uvicorn.error')

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # Startup
    app.mongo_conn = AsyncIOMotorClient(settings.MONGO_URI)
    app.db_client = app.mongo_conn[settings.MONGODB_NAME]
    logger.info("✅ Connected to MongoDB")
    
    llm_factory = LLMFactory(settings)
    vectordb_factory = VectorDBFactory(settings)
    
    # generation client
    app.generation_client = llm_factory.create(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    
    # embedding client
    app.embedding_client = llm_factory.create(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(
        settings.EMBEDDING_MODEL_ID, 
        settings.EMBEDDING_MODEL_SIZE)
    
    # vector db client
    app.vector_db_client = vectordb_factory.create(settings.VECTOR_DB_BACKEND)
    
    app.vector_db_client.connect()
    logger.info("✅ Connected to VectorDB")
    
    # template parser
    app.template_parser = TemplateParser(language=settings.PRIMARY_LANGUAGE, 
                                         default_language=settings.DEFAULT_LANGUAGE)
    logger.info("✅ Template parser initialized")
    
    yield
    
    # Shutdown
    app.mongo_conn.close()
    logger.info("🛑 MongoDB connection closed")
    app.vector_db_client.disconnect()
    logger.info("🛑 VectorDB connection closed")

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
