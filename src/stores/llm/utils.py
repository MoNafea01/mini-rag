from helpers.config import Settings
from .LLMEnums import LLMEnums
from .LLMInterface import LLMInterface
from .providers import OpenAI, Cohere, Groq
from typing import Dict, Type

def get_all_models() -> Dict[str, Type[LLMInterface]]:
    providers_map = {
        LLMEnums.OPENAI.value: OpenAI,
        LLMEnums.COHERE.value: Cohere,
        LLMEnums.GROQ.value: Groq,
    }
    
    return providers_map
    
def get_api_key(settings: Settings, Provider: Type[LLMInterface]) -> str:
    return {
        OpenAI: settings.OPENAI_API_KEY,
        Cohere: settings.COHERE_API_KEY,
        Groq: settings.GROQ_API_KEY,
    }.get(Provider)


class ModelUtils:
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
