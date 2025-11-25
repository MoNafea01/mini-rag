from typing import Tuple
from .BaseDataModel import BaseDataModel
from .db_schemas import Project
from .enums.DataBaseEnum import DataBaseEnum

class ProjectModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
    
    @classmethod
    async def create_instance(cls, db_client):
        isinstance = cls(db_client)
        await isinstance.init_collection()
        return isinstance
    
    async def init_collection(self):
        collection_name = DataBaseEnum.COLLECTION_PROJECT_NAME.value
        all_collections = await self.db_client.list_collection_names()
        self.collection = self.db_client[collection_name]
        
        if collection_name not in all_collections:
            print(f"⏳ Initializing collection: '{collection_name}'")
            indexes = Project.get_indexes()
            for index in indexes:
                await self.collection.create_index(**index)
            
    async def create_project(self, project: Project) -> Project:
        result = await self.collection.insert_one(project.model_dump(by_alias=True, exclude_unset=True))
        project.id = result.inserted_id
        return project

    async def get_project_or_create_one(self, project_id: str) -> Project:
        project = await self.collection.find_one({
            "project_id": project_id
        })
        
        if project:
            return Project(**project)
        
        # create a new Project
        project = Project(project_id=project_id)
        project = await self.create_project(project=project)
        
        return project
    
    async def get_all_projects(self, page: int = 1, page_size: int = 10) -> Tuple[list, int]:
        """
        Returns:\n
            - Projects (List[Porject])      
            - total_Pages (int)
        """
        # count total number of docs
        total_docs = await self.collection.count_documents({})
        
        # calculate total number of pages
        total_pages = total_docs // page_size
        if total_docs % page_size > 0:
            total_pages += 1
        
        cursor = self.collection.find().skip((page-1) * page_size).limit(page_size)
        
        projects = []
        async for doc in cursor:
            projects.append(
                Project(**doc)
            )
        
        return projects, total_pages
