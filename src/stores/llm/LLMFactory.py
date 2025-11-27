from .LLMEnums import LLMEnums
from .providers import OpenAI, Cohere, Groq
from helpers.config import Settings

class LLMFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
        
    def create(self, provider: str):
        params = dict(
            base_url=self.settings.OPENAI_API_URL,
            default_input_max_characters=self.settings.DEFAULT_GENERATION_INPUT_MAX_CHARACTERS,
            default_generation_output_max_tokens=self.settings.DEFAULT_GENERATION_OUTPUT_MAX_TOKENS,
            default_generation_temperature=self.settings.DEFAULT_GENERATION_TEMPERATURE
            )
        
        if provider == LLMEnums.OPENAI.value:
            return OpenAI(
                api_key=self.settings.OPENAI_API_KEY,
                **params
                )
        
        if provider == LLMEnums.COHERE.value:
            return Cohere(api_key=self.settings.COHERE_API_KEY,
                          **params)
        
        if provider == LLMEnums.GROQ.value:
            return Groq(api_key=self.settings.GROQ_API_KEY, **params)
        
        return None
