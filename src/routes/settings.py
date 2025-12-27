import logging
from fastapi import APIRouter, status, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from helpers.config import get_settings, reload_settings, read_env_file, update_env_file, Settings

logger = logging.getLogger('uvicorn.error')

settings_router = APIRouter(
    prefix="/api/v1/settings",
    tags=["api_v1", "settings"],
)


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "settings": {
                    "GENERATION_BACKEND": "OPENAI",
                    "EMBEDDING_BACKEND": "COHERE",
                    "DEFAULT_GENERATION_TEMPERATURE": "0.7",
                    "DB_TYPE": "mongodb"
                }
            }
        }


@settings_router.get("/")
async def get_app_settings():
    """
    Get current application settings from .env file
    
    Returns:
        All environment variables (sensitive keys are masked)
    """
    try:
        env_vars = read_env_file()
        
        # Mask sensitive keys
        sensitive_keys = ['API_KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'URI']
        masked_vars = {}
        
        for key, value in env_vars.items():
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                # Show only first 4 and last 4 characters
                if len(value) > 8:
                    masked_vars[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    masked_vars[key] = "***"
            else:
                masked_vars[key] = value
        
        return JSONResponse(
            content={
                "settings": masked_vars
            },
            status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error reading settings: {str(e)}")
        return JSONResponse(
            content={"message": f"Failed to read settings: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@settings_router.get("/active")
async def get_active_settings(app_settings: Settings = Depends(get_settings)):
    """
    Get currently active settings in the application
    
    Returns:
        Current settings loaded in memory (sensitive keys are masked)
    """
    try:
        settings_dict = app_settings.model_dump()
        
        # Mask sensitive keys
        sensitive_keys = ['api_key', 'password', 'secret', 'token', 'uri']
        masked_settings = {}
        
        for key, value in settings_dict.items():
            if value is None:
                masked_settings[key] = None
            elif any(sensitive in key.lower() for sensitive in sensitive_keys):
                # Show only first 4 and last 4 characters
                if isinstance(value, str) and len(value) > 8:
                    masked_settings[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    masked_settings[key] = "***"
            else:
                masked_settings[key] = value
        
        return JSONResponse(
            content={
                "settings": masked_settings
            },
            status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error reading active settings: {str(e)}")
        return JSONResponse(
            content={"message": f"Failed to read active settings: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@settings_router.put("/")
async def update_app_settings(request: Request, settings_request: SettingsUpdateRequest):
    """
    Update application settings in .env file and reload connections
    
    Args:
        request: FastAPI request object
        settings_request: Dictionary of settings to update
        
    Returns:
        Success message with updated settings
    """
    try:
        updates = settings_request.settings
        
        if not updates:
            return JSONResponse(
                content={"message": "No settings provided to update"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert all values to strings for .env file
        string_updates = {k: str(v) for k, v in updates.items()}
        
        # Update the .env file
        success = update_env_file(string_updates)
        
        if not success:
            return JSONResponse(
                content={"message": "Failed to update .env file"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Reload settings to apply changes
        new_settings = reload_settings()
        
        # Import here to avoid circular dependency
        from main import initialize_database_connection, initialize_llm_clients, initialize_vector_db
        
        # Get the app instance
        app = request.app
        
        # Reinitialize connections if critical settings changed
        critical_keys = ['DB_TYPE', 'GENERATION_BACKEND', 'EMBEDDING_BACKEND', 
                        'VECTOR_DB_BACKEND', 'MONGO_URI', 'POSTGRES_HOST', 
                        'POSTGRES_PORT', 'POSTGRES_MAIN_DB', 'GENERATION_MODEL_ID',
                        'EMBEDDING_MODEL_ID', 'EMBEDDING_MODEL_SIZE']
        
        needs_reconnect = any(key in updates for key in critical_keys)
        
        if needs_reconnect:
            logger.info("🔄 Critical settings changed, reinitializing connections...")
            
            if any(key in updates for key in ['DB_TYPE', 'MONGO_URI', 'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_MAIN_DB', 'POSTGRES_USERNAME', 'POSTGRES_PASSWORD']):
                await initialize_database_connection(app, new_settings)
            
            if any(key in updates for key in ['GENERATION_BACKEND', 'EMBEDDING_BACKEND', 'GENERATION_MODEL_ID', 'EMBEDDING_MODEL_ID', 'EMBEDDING_MODEL_SIZE']):
                await initialize_llm_clients(app, new_settings)
            
            if any(key in updates for key in ['VECTOR_DB_BACKEND', 'VECTOR_DB_PATH', 'VECTOR_DB_PATH_NAME']):
                await initialize_vector_db(app, new_settings)
        
        return JSONResponse(
            content={
                "message": "Settings updated successfully",
                "updated_keys": list(updates.keys()),
                "reconnected": needs_reconnect,
                "active_db": new_settings.DB_TYPE,
                "info": "Connections have been reinitialized." if needs_reconnect else "Settings updated without reconnection."
            },
            status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return JSONResponse(
            content={"message": f"Failed to update settings: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@settings_router.post("/reload")
async def reload_app_settings(request: Request):
    """
    Reload settings from .env file and reinitialize connections
    
    Useful after manually editing the .env file.
    This will reinitialize database, LLM, and vector DB connections.
    """
    try:
        # Reload settings from .env
        new_settings = reload_settings()
        
        # Import here to avoid circular dependency
        from main import initialize_database_connection, initialize_llm_clients, initialize_vector_db
        
        # Get the app instance
        app = request.app
        print(app)
        # Reinitialize all connections with new settings
        await initialize_database_connection(app, new_settings)
        await initialize_llm_clients(app, new_settings)
        await initialize_vector_db(app, new_settings)
        
        # Update template parser
        from stores.llm.templates.template_parser import TemplateParser
        app.template_parser = TemplateParser(
            language=new_settings.PRIMARY_LANGUAGE, 
            default_language=new_settings.DEFAULT_LANGUAGE
        )
        
        logger.info("✅ All settings and connections reloaded successfully")
        
        return JSONResponse(
            content={
                "message": "Settings and connections reloaded successfully",
                "active_db": new_settings.DB_TYPE,
                "generation_backend": new_settings.GENERATION_BACKEND,
                "embedding_backend": new_settings.EMBEDDING_BACKEND,
                "vector_db_backend": new_settings.VECTOR_DB_BACKEND
            },
            status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error reloading settings: {str(e)}")
        return JSONResponse(
            content={"message": f"Failed to reload settings: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
