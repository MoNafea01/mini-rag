from ..LLMInterface import LLMInterface
from ..LLMEnums import GroqRolesEnums
from groq import Groq as GroqClient
import logging
from ..utils import ModelUtils

class Groq(LLMInterface, ModelUtils):
    
    def __init__(self, 
                 api_key: str, 
                 base_url: str = None, 
                 default_input_max_characters: int = 1024,
                 default_generation_output_max_tokens: int = 1024,
                 default_generation_temperature: float = 0.1):
        
        ModelUtils.__init__(self)
        self.api_key = api_key
        
        self.enums = GroqRolesEnums
        
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_output_max_tokens = default_generation_output_max_tokens
        self.default_generation_temperature = default_generation_temperature
        
        self.generation_model_id = None
        
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.client = GroqClient(api_key=self.api_key)
        
        self.logger = logging.getLogger(__name__)
    
    
    def generate_text(self, 
                      prompt: str, 
                      chat_history: list=None, 
                      max_output_tokens: int=None, 
                      temperature: float=None):
        
        if not self.client:
            self.logger.error("Groq client is not initialized.")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model ID is not set.")
            return None
        
        chat_history = chat_history or []
        max_output_tokens = max_output_tokens or self.default_generation_output_max_tokens
        temperature = temperature or self.default_generation_temperature
        history = chat_history + [self.construct_prompt(prompt, role=GroqRolesEnums.USER.value)]
        
        response = self.client.chat.completions.create(
            model=self.generation_model_id,
            messages=history,
            max_tokens=max_output_tokens,
            temperature=temperature,
            include_reasoning=False,
        )
        
        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            self.logger.error("Failed to get completion from Groq response.")
            return None
        
        return response.choices[0].message.content
    
    
    def embed_text(self, 
                   text: str, 
                   document_type: str=None):
        
        raise NotImplementedError
    
    
    def construct_prompt(self, 
                         prompt: str, 
                         role: str):
        
        return {"role": role, "content": prompt}


    def process_text(self, text: str):
        text = text.strip()
        if len(text) > self.default_input_max_characters:
            self.logger.warning("Input text exceeds the maximum allowed characters. It will be truncated.")
            
        return text[:self.default_input_max_characters]
