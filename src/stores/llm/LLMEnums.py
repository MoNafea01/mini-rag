from enum import Enum

class LLMEnums(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    GEMINI = "gemini"
    OLLAMA = "ollama"

class OPENAIRolesEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
