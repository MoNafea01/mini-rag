from ..LLMInterface import LLMInterface
from ..LLMEnums import OPENAIRolesEnums
from ..utils import ModelUtils
from openai import OpenAI as OpenAIClient
import logging

class OpenAI(LLMInterface, ModelUtils):
    
    def __init__(self, 
                 api_key: str, 
                 base_url: str = None, 
                 default_input_max_characters: int = 1024,
                 default_generation_output_max_tokens: int = 1024,
                 default_generation_temperature: float = 0.1):
        
        ModelUtils.__init__(self)
        self.api_key = api_key
        self.base_url = base_url
        
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_output_max_tokens = default_generation_output_max_tokens
        self.default_generation_temperature = default_generation_temperature
        
        self.generation_model_id = None
        
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.client = OpenAIClient(api_key=self.api_key,
                             base_url=self.base_url)
        
        self.logger = logging.getLogger(__name__)
    
    
    def generate_text(self, prompt: str, chat_history: list=None, max_output_tokens: int=None, temperature: float=None):
        if not self.client:
            self.logger.error("OpenAI client is not initialized.")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model ID is not set.")
            return None
        
        chat_history = chat_history or []
        max_output_tokens = max_output_tokens or self.default_generation_output_max_tokens
        temperature = temperature or self.default_generation_temperature
        history = chat_history + [self.construct_prompt(prompt, role=OPENAIRolesEnums.USER.value)]
        
        response = self.client.chat.completions.create(
            model=self.generation_model_id,
            messages=history,
            max_tokens=max_output_tokens,
            temperature=temperature
        )
        
        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            self.logger.error("Failed to get completion from OpenAI response.")
            return None
        
        return response.choices[0].message["content"]
    
    
    def embed_text(self, text: str, document_type: str=None):
        if not self.client:
            self.logger.error("OpenAI client is not initialized.")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model ID is not set.")
            return None

        response = self.client.embeddings.create(
            model=self.embedding_model_id,
            input=text,
        )
        
        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Failed to get embedding from OpenAI response.")
            return None
        return response.data[0].embedding
    
    
    def construct_prompt(self, prompt: str, role: str):
        return {"role": role, "content": self.process_text(prompt)}


    def process_text(self, text: str):
        text = text.strip()
        if len(text) > self.default_input_max_characters:
            self.logger.warning("Input text exceeds the maximum allowed characters. It will be truncated.")
            
        return text[:self.default_input_max_characters]
