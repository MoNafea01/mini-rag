from ..LLMInterface import LLMInterface
from ..LLMEnums import CohereDocumentTypeEnums, DocumentTypeEnums, CohereRolesEnums
import cohere as CohereClient
import logging
from ..utils import ModelUtils

class Cohere(LLMInterface, ModelUtils):
    
    def __init__(self, 
                 api_key: str, 
                 base_url: str=None,
                 default_input_max_characters: int = 1024,
                 default_generation_output_max_tokens: int = 1024,
                 default_generation_temperature: float = 0.1):
        
        ModelUtils.__init__(self)
        
        self.api_key = api_key
        
        self.enums = CohereRolesEnums
        
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_output_max_tokens = default_generation_output_max_tokens
        self.default_generation_temperature = default_generation_temperature
        
        self.generation_model_id = None
        
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.client = CohereClient.Client(api_key=self.api_key)
        
        self.logger = logging.getLogger(__name__)
    
    
    def generate_text(self, 
                      prompt: str, 
                      chat_history: list=None, 
                      max_output_tokens: int=None, 
                      temperature: float=None):
        
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model ID is not set.")
            return None
        
        max_output_tokens = max_output_tokens or self.default_generation_output_max_tokens
        temperature = temperature or self.default_generation_temperature
        
        response = self.client.chat(
            model=self.generation_model_id,
            chat_history=chat_history,
            message=self.process_text(prompt),
            temperature=temperature,
            max_tokens=max_output_tokens
        )
        
        if not response or not response.text:
            self.logger.error("No response received from Cohere API.")
            return None
        
        return response.text
    
    
    def embed_text(self, 
                   text: str, 
                   document_type: str=None):
        
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model ID is not set.")
            return None
        
        (document, query) = (CohereDocumentTypeEnums.DOCUMENT.value, CohereDocumentTypeEnums.QUERY.value)
        
        input_type = query if document_type == DocumentTypeEnums.QUERY.value else document
        
        response = self.client.embed(
            model=self.embedding_model_id,
            texts=[self.process_text(text)],
            input_type=input_type,
            embedding_types=['float']
        )
        
        if (
            response is None
            or response.embeddings is None
            or response.embeddings.float is None
            or len(response.embeddings.float) == 0
            ):
            self.logger.error("Failed to get embedding from Cohere response.")
            return None
        
        return response.embeddings.float[0]
    
    
    def process_text(self, text: str):
        text = text.strip()
        if len(text) > self.default_input_max_characters:
            self.logger.warning("Input text exceeds the maximum allowed characters. It will be truncated.")
            
        return text[:self.default_input_max_characters]

    
    def construct_prompt(self, 
                         prompt: str, 
                         role: str):
        
        return {"role": role, "text": self.process_text(prompt)}
