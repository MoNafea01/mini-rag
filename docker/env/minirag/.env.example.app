APP_NAME="mini-RAG"
APP_VERSION="0.1.0"
OPENAPI_API_KEY="your_openapi_api_key"

FILE_MAX_SIZE_MB=20
FILE_ALLOWED_TYPES=["text/plain", "application/pdf"]
FILE_STORAGE_PATH="assets/files"
FILE_DEFAULT_CHUNK_SIZE=524288 # 512 KB

DB_TYPE_OPTIONS=["mongodb", "postgres"]
DB_TYPE="postgres"

# ============================= MongoDB Settings ============================= #
MONGO_HOST="mongodb"

MONGO_USERNAME=""
MONGO_PASSWORD=""

MONGO_URI="mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@${MONGO_HOST}:27017"
MONGODB_NAME=""

# ============================= PostgreSQL Settings ============================= #
POSTGRES_HOST="pgvector"
POSTGRES_PORT=5432
POSTGRES_MAIN_DB=""
POSTGRES_USERNAME=""
POSTGRES_PASSWORD=""

# ============================= LLM Settings ============================= #
GENERATION_BACKEND_OPTIONS=["OPENAI", "GROQ", "COHERE", "OLLAMA"]
EMBEDDING_BACKEND_OPTIONS=["OPENAI", "COHERE", "OLLAMA"]

GENERATION_BACKEND=GROQ
EMBEDDING_BACKEND=COHERE

OPENAI_API_KEY=""
COHERE_API_KEY=""
GROQ_API_KEY=""
BASE_API_URL=""

GENERATION_MODEL_ID="openai/gpt-oss-120b"
EMBEDDING_MODEL_ID="embed-multilingual-light-v3.0"
EMBEDDING_MODEL_SIZE=384

DEFAULT_GENERATION_TEMPERATURE=0.7
DEFAULT_GENERATION_OUTPUT_MAX_TOKENS=512
DEFAULT_GENERATION_INPUT_MAX_CHARACTERS=4096

# ============================= Vector DB Settings ============================= #
VECTOR_DB_BACKEND_OPTIONS=["QDRANT", "PGVECTOR"]
VECTOR_DB_DISTANCE_METRIC_OPTIONS=["cosine", "dot", "euclidean", "manhattan"]

VECTOR_DB_BACKEND="QDRANT"
VECTOR_DB_PATH = "assets/database"
VECTOR_DB_PATH_NAME=""
VECTOR_DB_DISTANCE_METRIC="cosine"
VECTOR_DB_PGVEC_INDEX_THRESHOLD=250

# ============================= Template Settings ============================= #
LANGUAGE_OPTIONS=["en", "ar"]

PRIMARY_LANGUAGE="ar"
DEFAULT_LANGUAGE="en"