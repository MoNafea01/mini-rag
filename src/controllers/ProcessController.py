import os
from models.enums import ProcessingEnum
from .BaseController import BaseController
from .ProjectController import ProjectController
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ProcessController(BaseController):
    def __init__(self, project_id: int):
        super().__init__()
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id)
    
    
    def get_file_extension(self, file_id: str) -> str:
        return os.path.splitext(file_id)[-1]

    
    def resolve_file_id(self, prefix: str) -> str:
        for filename in os.listdir(self.project_path):
            if filename.startswith(prefix):
                return filename
        return None
    
    
    def get_file_loader(self, file_id: str):
        
        file_name = self.resolve_file_id(file_id)
        if file_name is None:
            return None
        
        file_ext = self.get_file_extension(file_name)
        file_path = os.path.join(self.project_path, file_name)
        
        if not os.path.exists(file_path):
            return None
        
        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path=file_path, encoding='utf-8')
            
        elif file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path=file_path)

        return None

    
    def get_file_content(self, file_id: str):
        
        loader = self.get_file_loader(file_id)
        if loader is None:
            return None
        
        return loader.load()
    
    
    def process_file_content(self, 
                             file_content: list, 
                             chunk_size: int = 100, 
                             overlap_size: int = 20):
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        docs = text_splitter.split_documents(file_content)
        return docs
