from enum import Enum

class VectorDBEnums(Enum):
    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"
    
    # Upcoming
    # FAISS = "FAISS"
    # CHROMA = "CHROMA"

class DistanceMetricEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"

class QdrantDistanceMetricEnums(Enum):
    COSINE = "Cosine"
    DOT = "Dot"
    EUCLID = "Euclid"
    MANHATTAN = "Manhattan"

class PgVectorDistanceMetricEnums(Enum):
    COSINE = "vector_cosine_ops"
    DOT = "vector_ip_ops"
    EUCLIDEAN = "vector_l2_ops"
    MANHATTAN = "vector_l1_ops"

class PgVectorTableSchemaEnums(Enum):
    ID = "id"
    TEXT = "text"
    VECTOR = "vector"
    CHUNK_ID = "chunk_id"
    METADATA = "metadata"
    _PREFIX = "pgvector"

class PgVectorIndexTypeEnums(Enum):
    IVFFLAT = "ivfflat"
    HNSW = "hnsw"
