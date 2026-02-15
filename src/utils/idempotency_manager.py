import hashlib
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from models.enums import DatabaseType
from models.db_schemas import (
    CeleryTaskExecutionMongo, 
    CeleryTaskExecution as CeleryTaskExecutionPG
)

class IdempotencyManager:

    def __init__(self, db_client, db_engine, db_type: str = "postgres"):
        self.db_client = db_client
        self.db_engine = db_engine
        self.db_type = db_type
        self.collection = None
        self.counters_collection = None

    def get_task_record_id(self, task_record):
        """Get the primary key ID from a task record, handling both DB types."""
        if task_record is None:
            return None
        if self.db_type == DatabaseType.MONGODB.value:
            return task_record.id
        return task_record.execution_id

    async def init_mongo_collection(self):
        """Initialize MongoDB collection and indexes."""
        if self.db_type != DatabaseType.MONGODB.value:
            return
            
        collection_name = "celery_task_executions"
        all_collections = await self.db_client.list_collection_names()
        self.collection = self.db_client[collection_name]
        self.counters_collection = self.db_client["counters"]
        
        if collection_name not in all_collections:
            indexes = CeleryTaskExecutionMongo.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["keys"],
                    name=index["name"],
                    unique=index.get("unique", False)
                )

    def create_args_hash(self, task_name: str, task_args: dict):
        combined_data = {
            **task_args,
            "task_name": task_name
        }
        json_string = json.dumps(combined_data, sort_keys=True, default=str)
        return hashlib.sha256(json_string.encode()).hexdigest()
    
    async def create_task_record(self, task_name: str, task_args: dict, task_id: str = None):
        """Create new task execution record."""
        if self.db_type == DatabaseType.MONGODB.value:
            return await self._create_task_record_mongo(task_name, task_args, task_id)
        return await self._create_task_record_postgres(task_name, task_args, task_id)
    
    async def update_task_status(self, execution_id, status: str, result: dict = None):
        """Update task status and result."""
        if self.db_type == DatabaseType.MONGODB.value:
            return await self._update_task_status_mongo(execution_id, status, result)
        return await self._update_task_status_postgres(execution_id, status, result)
    
    async def get_existing_task(self, task_name: str, task_args: dict, task_id: str):
        """Check if task with same name and args already exists."""
        if self.db_type == DatabaseType.MONGODB.value:
            return await self._get_existing_task_mongo(task_name, task_args, task_id)
        return await self._get_existing_task_postgres(task_name, task_args, task_id)
    
    async def should_execute_task(self, task_name: str, task_args: dict,
                                  task_id: str, 
                                  task_time_limit: int = 600) -> tuple[bool, any]:
        """
        Check if task should be executed or return existing result.
        Args:
            task_time_limit: Time limit in seconds after which a stuck task can be re-executed
        Returns (should_execute, existing_task_or_none)
        """
        existing_task = await self.get_existing_task(task_name, task_args, task_id)
        
        if not existing_task:
            return True, None
            
        # Don't execute if task is already completed successfully
        if existing_task.status == 'SUCCESS':
            return False, existing_task
            
        # Check if task is stuck (running longer than time limit + 60 seconds)
        if existing_task.status in ['PENDING', 'STARTED', 'RETRY']:
            if existing_task.started_at:
                started_at = existing_task.started_at
                # Handle both timezone-aware and naive datetimes
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                time_elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
                time_gap = 60  # 60 seconds grace period
                if time_elapsed > (task_time_limit + time_gap):
                    return True, existing_task  # Task is stuck, allow re-execution
            return False, existing_task  # Task is still running within time limit
            
        # Re-execute if previous task failed
        return True, existing_task
    
    async def cleanup_old_tasks(self, time_retention: int = 86400) -> int:
        """
        Delete old task records older than time_retention seconds.
        Args:
            time_retention: Time in seconds to retain tasks (default: 86400 = 24 hours)
        Returns:
            Number of deleted records
        """
        if self.db_type == DatabaseType.MONGODB.value:
            return await self._cleanup_old_tasks_mongo(time_retention)
        return await self._cleanup_old_tasks_postgres(time_retention)


    async def _create_task_record_postgres(self, task_name: str, task_args: dict, task_id: str = None) -> CeleryTaskExecutionPG:
        """Create new task execution record in PostgreSQL."""
        args_hash = self.create_args_hash(task_name, task_args)
        
        task_record = CeleryTaskExecutionPG(
            task_name=task_name,
            task_args_hash=args_hash,
            task_args=task_args,
            task_id=task_id,
            status='PENDING',
            started_at=datetime.now(timezone.utc)
        )
        
        session = self.db_client()
        try:
            session.add(task_record)
            await session.commit()
            await session.refresh(task_record)
            return task_record
        finally:
            await session.close()

    async def _create_task_record_mongo(self, task_name: str, task_args: dict, task_id: str = None) -> CeleryTaskExecutionMongo:
        """Create new task execution record in MongoDB."""
        await self.init_mongo_collection()
        args_hash = self.create_args_hash(task_name, task_args)
        
        task_record = CeleryTaskExecutionMongo(
            task_name=task_name,
            task_args_hash=args_hash,
            task_args=task_args,
            task_id=task_id,
            status='PENDING',
            started_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        
        result = await self.collection.insert_one(task_record.model_dump(by_alias=True, exclude_unset=True))
        task_record.id = result.inserted_id
        return task_record

    async def _update_task_status_postgres(self, execution_id: int, status: str, result: dict = None):
        """Update task status and result in PostgreSQL."""
        session = self.db_client()
        try:
            task_record = await session.get(CeleryTaskExecutionPG, execution_id)
            if task_record:
                task_record.status = status
                if result:
                    task_record.result = result
                if status in ['SUCCESS', 'FAILURE']:
                    task_record.completed_at = datetime.now(timezone.utc)
                await session.commit()
        finally:
            await session.close()

    async def _update_task_status_mongo(self, execution_id, status: str, result: dict = None):
        """Update task status and result in MongoDB."""
        await self.init_mongo_collection()
        
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }
        if result:
            update_data["result"] = result
        if status in ['SUCCESS', 'FAILURE']:
            update_data["completed_at"] = datetime.now(timezone.utc)
        
        await self.collection.update_one(
            {"_id": execution_id},
            {"$set": update_data}
        )

    async def _get_existing_task_postgres(self, task_name: str, task_args: dict, task_id: str) -> CeleryTaskExecutionPG:
        """Check if task exists in PostgreSQL."""
        args_hash = self.create_args_hash(task_name, task_args)
        
        session = self.db_client()
        try:
            stmt = select(CeleryTaskExecutionPG).where(
                CeleryTaskExecutionPG.task_id == task_id,
                CeleryTaskExecutionPG.task_name == task_name,
                CeleryTaskExecutionPG.task_args_hash == args_hash
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            await session.close()

    async def _get_existing_task_mongo(self, task_name: str, task_args: dict, task_id: str) -> CeleryTaskExecutionMongo:
        """Check if task exists in MongoDB."""
        await self.init_mongo_collection()
        args_hash = self.create_args_hash(task_name, task_args)
        
        record = await self.collection.find_one({
            "task_id": task_id,
            "task_name": task_name,
            "task_args_hash": args_hash
        })
        
        if record:
            return CeleryTaskExecutionMongo(**record)
        return None

    async def _cleanup_old_tasks_postgres(self, time_retention: int = 86400) -> int:
        """Delete old task records from PostgreSQL."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=time_retention)
        
        session = self.db_client()
        try:
            stmt = delete(CeleryTaskExecutionPG).where(
                CeleryTaskExecutionPG.created_at < cutoff_time
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount
        finally:
            await session.close()

    async def _cleanup_old_tasks_mongo(self, time_retention: int = 86400) -> int:
        """Delete old task records from MongoDB."""
        await self.init_mongo_collection()
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=time_retention)
        
        result = await self.collection.delete_many({
            "created_at": {"$lt": cutoff_time}
        })
        return result.deleted_count
