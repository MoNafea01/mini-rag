from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMFactory import LLMFactory

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # Startup
    app.mongo_conn = AsyncIOMotorClient(settings.MONGO_URI)
    app.db_client = app.mongo_conn[settings.MONGODB_NAME]
    print("✅ Connected to MongoDB")
    
    llm_factory = LLMFactory(settings)
    
    # generation client
    app.generation_client = llm_factory.create(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    
    # embedding client
    app.embedding_client = llm_factory.create(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(
        settings.EMBEDDING_MODEL_ID, 
        settings.EMBEDDING_MODEL_SIZE)
    
    yield
    
    # Shutdown
    app.mongo_conn.close()
    print("🛑 MongoDB connection closed")

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
