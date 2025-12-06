from enum import Enum

class LLMEnums(Enum):
    OPENAI = "OPENAI"
    GROQ = "GROQ"
    COHERE = "COHERE"
    OLLAMA = "OLLAMA"
    
    # Upcoming
    # ANTHROPIC = "ANTHROPIC"
    # GEMINI = "GEMINI"
    
class OPENAIRolesEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class OLLAMARolesEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class CohereRolesEnums(Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"


class GroqRolesEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class CohereDocumentTypeEnums(Enum):
    QUERY = "search_query"
    DOCUMENT = "search_document"


class DocumentTypeEnums(Enum):
    QUERY = "query"
    DOCUMENT = "document"
