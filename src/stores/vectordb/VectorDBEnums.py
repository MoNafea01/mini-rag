from enum import Enum

class VectorDBEnums(Enum):
    QDRANT = "QDRANT"
    
    # Upcoming
    # FAISS = "FAISS"
    # CHROMA = "CHROMA"

class DistanceMetricEnums(Enum):
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT = "dot"
    MANHATTAN = "manhattan"
    