from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    
    FILE_MAX_SIZE_MB: int
    FILE_ALLOWED_TYPES: List[str]
    FILE_STORAGE_PATH: str
    FILE_DEFAULT_CHUNK_SIZE: int
    
    DB_TYPE_OPTIONS: List[str] = None
    DB_TYPE: str
    
    MONGO_URI: str
    MONGODB_NAME: str
    
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DB: str
    
    GENERATION_BACKEND_OPTIONS: List[str] = None
    EMBEDDING_BACKEND_OPTIONS: List[str] = None
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
    
    VECTOR_DB_BACKEND_OPTIONS: List[str] = None
    VECTOR_DB_DISTANCE_METRIC_OPTIONS: List[str] = None
    
    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    QDRANT_URL: str = None
    VECTOR_DB_PATH_NAME: str
    VECTOR_DB_DISTANCE_METRIC: str = None
    VECTOR_DB_PGVEC_INDEX_THRESHOLD: int=100
    
    LANGUAGE_OPTIONS: List[str] = None
    PRIMARY_LANGUAGE: str = "en"
    DEFAULT_LANGUAGE: str = "en"
    
    CELERY_BROKER_URL: str = None
    CELERY_RESULT_BACKEND: str = None
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TASK_TIME_LIMIT: int = 600
    CELERY_ACKS_LATE: bool = True
    CELERY_WORKER_CONCURRENCY: int = 2
    CELERY_FLOWER_PASSWORD: str = None
    
    class Config:
        env_file = ".env" 
        extra = "ignore"


# Singleton instance for settings
_settings_instance = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """Force reload settings from .env file"""
    global _settings_instance
    _settings_instance = Settings()
    return _settings_instance


def get_env_file_path():
    """Get the path to the .env file"""
    from pathlib import Path
    current_dir = Path(__file__).parent.parent
    return current_dir / ".env"


def read_env_file() -> dict:
    """Read the .env file and return as dictionary"""
    env_path = get_env_file_path()
    env_vars = {}
    
    if not env_path.exists():
        return env_vars
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Remove inline comments
                if '#' in value:
                    value = value.split('#')[0].strip()
                
                env_vars[key] = value
    
    return env_vars


def update_env_file(updates: dict) -> bool:
    """
    Update specific values in the .env file
    
    Args:
        updates: Dictionary of key-value pairs to update
        
    Returns:
        True if successful, False otherwise
    """
    env_path = get_env_file_path()
    
    if not env_path.exists():
        return False
    
    # Read the entire file content
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update the lines
    updated_lines = []
    updated_keys = set()
    
    for line in lines:
        stripped = line.strip()
        
        # Keep comments and empty lines as is
        if not stripped or stripped.startswith('#'):
            updated_lines.append(line)
            continue
        
        # Check if this line has a key we want to update
        if '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            
            if key in updates:
                # Update this line
                new_value = updates[key]
                
                # Add quotes if value contains spaces or special characters
                if isinstance(new_value, str) and (' ' in new_value or any(c in new_value for c in ['$', '#'])):
                    new_value = f'"{new_value}"'
                
                updated_lines.append(f'{key}={new_value}\n')
                updated_keys.add(key)
            else:
                # Keep original line
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Write back to file
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    return True

    return Settings()
