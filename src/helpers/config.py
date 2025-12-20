from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    
    FILE_MAX_SIZE_MB: int
    FILE_ALLOWED_TYPES: List[str]
    FILE_STORAGE_PATH: str
    FILE_DEFAULT_CHUNK_SIZE: int
    
    MONGO_URI: str
    MONGODB_NAME: str
    
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str
    
    OPENAI_API_KEY: str=None
    COHERE_API_KEY: str=None
    GROQ_API_KEY: str=None
    BASE_API_URL: str=None
    
    GENERATION_MODEL_ID: str=None
    EMBEDDING_MODEL_ID: str=None
    EMBEDDING_MODEL_SIZE: int=None
    
    DEFAULT_GENERATION_TEMPERATURE: float
    DEFAULT_GENERATION_OUTPUT_MAX_TOKENS: int
    DEFAULT_GENERATION_INPUT_MAX_CHARACTERS: int
    
    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DB_PATH_NAME: str
    VECTOR_DB_DISTANCE_METRIC: str = None
    
    PRIMARY_LANGUAGE: str = "en"
    DEFAULT_LANGUAGE: str = "en"
    
    class Config:
        env_file = ".env" 
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()
