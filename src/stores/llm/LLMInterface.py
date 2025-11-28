from abc import ABC, abstractmethod

class LLMInterface(ABC):
    
    @abstractmethod
    def __init__(self, 
                 api_key: str, 
                 base_url: str=None, 
                 default_input_max_characters: int=None,
                 default_generation_output_max_tokens: int=None, 
                 default_generation_temperature: float=None):
        pass
    
    @abstractmethod
    def generate_text(self, prompt: str, chat_history: list=None, max_output_tokens: int=None, temperature: float=None):
        pass
    
    @abstractmethod
    def embed_text(self, text: str, document_type: str=None):
        pass
    
    @abstractmethod
    def construct_prompt(self, prompt: str, role: str):
        pass
