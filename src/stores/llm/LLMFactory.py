from helpers.config import Settings
from .utils import ModelUtils
from . import PROVIDER_REGISTRY
from .LLMInterface import LLMInterface
from typing import Type


class LLMFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
       
    def create(self, provider_cls: str):
        Provider: Type[LLMInterface] = PROVIDER_REGISTRY.get(provider_cls)
        
        if not Provider:
            return None
        
        api_key = ModelUtils.get_api_key(settings=self.settings, Provider=Provider)
        
        return Provider(
            api_key=api_key,
            base_url=self.settings.BASE_API_URL,
            default_input_max_characters=self.settings.DEFAULT_GENERATION_INPUT_MAX_CHARACTERS,
            default_generation_output_max_tokens=self.settings.DEFAULT_GENERATION_OUTPUT_MAX_TOKENS,
            default_generation_temperature=self.settings.DEFAULT_GENERATION_TEMPERATURE
        )
