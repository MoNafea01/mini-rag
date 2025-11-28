from .VectorDBEnums import VectorDBEnums
from .VectorDBInterface import VectorDBInterface
from .providers import Qdrant
from typing import Dict, Type

VECTOR_DB_REGISTRY: Dict[str, Type[VectorDBInterface]] = {
    VectorDBEnums.QDRANT.value: Qdrant,
}
