from helpers.config import Settings
from .LLMInterface import LLMInterface
from typing import Type


class ModelUtils:
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
    def set_embedding_model(self, 
                            model_id: str, 
                            embedding_size: int):
        
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
    
    @staticmethod
    def get_api_key(settings: Settings, Provider: Type[LLMInterface]) -> str:
        return {
            "OpenAI": settings.OPENAI_API_KEY,
            "Cohere": settings.COHERE_API_KEY,
            "Groq": settings.GROQ_API_KEY,
        }.get(Provider.__name__)
