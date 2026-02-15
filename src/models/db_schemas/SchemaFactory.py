from enum import Enum
from typing import Type, Union
from models.enums import DatabaseType


class SchemaFactory:
    """
    Factory class for retrieving database schema classes.
    Supports MongoDB (Pydantic) and PostgreSQL (SQLAlchemy) database schemas.
    """
    
    @staticmethod
    def get_project_schema(db_type: Union[DatabaseType, str]) -> Type:
        """
        Get the Project schema class for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            
        Returns:
            Project schema class (Pydantic BaseModel for MongoDB, SQLAlchemy model for Postgres)
            
        Raises:
            ValueError: If database type is not supported
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.MONGODB:
            from .minirag_mongo.schemas import Project
            return Project
        elif db_type == DatabaseType.POSTGRES:
            from .minirag.schemas import Project
            return Project
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    
    @staticmethod
    def get_asset_schema(db_type: Union[DatabaseType, str]) -> Type:
        """
        Get the Asset schema class for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            
        Returns:
            Asset schema class (Pydantic BaseModel for MongoDB, SQLAlchemy model for Postgres)
            
        Raises:
            ValueError: If database type is not supported
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.MONGODB:
            from .minirag_mongo.schemas import Asset
            return Asset
        elif db_type == DatabaseType.POSTGRES:
            from .minirag.schemas import Asset
            return Asset
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    
    @staticmethod
    def get_chunk_schema(db_type: Union[DatabaseType, str]) -> Type:
        """
        Get the DataChunk schema class for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            
        Returns:
            DataChunk schema class (Pydantic BaseModel for MongoDB, SQLAlchemy model for Postgres)
            
        Raises:
            ValueError: If database type is not supported
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.MONGODB:
            from .minirag_mongo.schemas import DataChunk
            return DataChunk
        elif db_type == DatabaseType.POSTGRES:
            from .minirag.schemas import DataChunk
            return DataChunk
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    
    @staticmethod
    def get_retrieved_document_schema(db_type: Union[DatabaseType, str]) -> Type:
        """
        Get the RetrievedDocument schema class for the specified database type.
        Note: This schema is only available for certain database types.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            
        Returns:
            RetrievedDocument schema class
            
        Raises:
            ValueError: If database type is not supported or schema is not available
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.MONGODB:
            from .minirag_mongo.schemas import RetrievedDocument
            return RetrievedDocument
        elif db_type == DatabaseType.POSTGRES:
            from .minirag.schemas import RetrievedDocument
            return RetrievedDocument
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def get_celery_task_execution_schema(db_type: Union[DatabaseType, str]) -> Type:
        """
        Get the CeleryTaskExecution schema class for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            
        Returns:
            CeleryTaskExecution schema class
            
        Raises:
            ValueError: If database type is not supported
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.MONGODB:
            from .minirag_mongo.schemas import CeleryTaskExecution
            return CeleryTaskExecution
        elif db_type == DatabaseType.POSTGRES:
            from .minirag.schemas import CeleryTaskExecution
            return CeleryTaskExecution
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @staticmethod
    def get_all_schemas(db_type: Union[DatabaseType, str]) -> dict:
        """
        Get all schema classes for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            
        Returns:
            Dictionary containing all schema classes:
            {
                'Project': Project schema class,
                'Asset': Asset schema class,
                'DataChunk': DataChunk schema class,
                'RetrievedDocument': RetrievedDocument schema class (if available),
                'CeleryTaskExecution': CeleryTaskExecution schema class
            }
            
        Raises:
            ValueError: If database type is not supported
        """
        schemas = {
            'Project': SchemaFactory.get_project_schema(db_type),
            'Asset': SchemaFactory.get_asset_schema(db_type),
            'DataChunk': SchemaFactory.get_chunk_schema(db_type),
            'CeleryTaskExecution': SchemaFactory.get_celery_task_execution_schema(db_type),
        }
        
        # Add RetrievedDocument if available
        try:
            schemas['RetrievedDocument'] = SchemaFactory.get_retrieved_document_schema(db_type)
        except (ValueError, ImportError):
            pass
        
        return schemas
    
    
    @staticmethod
    def get_sqlalchemy_base(db_type: Union[DatabaseType, str]) -> Type:
        """
        Get the SQLAlchemy Base class for PostgreSQL database.
        Only applicable for PostgreSQL databases.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'postgres')
            
        Returns:
            SQLAlchemy Base class
            
        Raises:
            ValueError: If database type is not PostgreSQL
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.POSTGRES:
            from .minirag.schemas import SQLAlchemyBase
            return SQLAlchemyBase
        else:
            raise ValueError(f"SQLAlchemy Base is only available for PostgreSQL, not {db_type}")
