from typing import Type, Dict
from .VectorDBEnums import DistanceMetricEnums
from qdrant_client import models

def get_distance_metrics(special_map: dict = {}) -> Dict[str, Type[models.Distance]]:

    mapping = {}

    for enum_item in DistanceMetricEnums:
        enum_value = enum_item.value

        # Step 1: Resolve Qdrant attribute name
        qdrant_name = special_map.get(enum_value, enum_value.upper())

        # Step 2: Lookup in Qdrant
        qdrant_attr = getattr(models.Distance, qdrant_name, None)

        if qdrant_attr is None:
            raise ValueError(
                f"Qdrant does not support distance metric '{qdrant_name}' "
                f"(derived from '{enum_value}')"
            )

        # Step 3: Save mapping
        mapping[enum_value] = qdrant_attr

    return mapping
