from .providers import OpenAI, Cohere, Groq
from .LLMEnums import LLMEnums
from .LLMInterface import LLMInterface
from typing import Dict, Type

PROVIDER_REGISTRY: Dict[str, Type[LLMInterface]] = {
    LLMEnums.OPENAI.value: OpenAI,
    LLMEnums.COHERE.value: Cohere,
    LLMEnums.GROQ.value: Groq,
}
