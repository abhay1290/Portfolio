import math


def replace_nan_with_none(d):
    for k, v in d.items():
        if isinstance(v, float) and math.isnan(v):
            d[k] = None
        elif isinstance(v, dict):
            replace_nan_with_none(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    replace_nan_with_none(item)
    return d


import json
from datetime import date, datetime
from typing import Dict, Any
import logging


def to_string(data: Dict[str, Any]) -> str:
    """
    Convert a dictionary containing potential date objects to a JSON string.
    Handles:
    - Python date/datetime objects
    - QuantLib Date objects (if present)
    - Nested dictionaries and lists
    - NaN/None values
    - Regular numeric/string values

    Args:
        data: Dictionary to serialize (like your summary dict)

    Returns:
        JSON string with all dates converted to ISO format strings
    """

    def convert_value(obj):
        # Handle date types
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif hasattr(obj, 'year') and hasattr(obj, 'month') and hasattr(obj, 'dayOfMonth'):
            # QuantLib Date object
            return f"{obj.year()}-{obj.month():02d}-{obj.dayOfMonth():02d}"
        elif isinstance(obj, (dict, list, tuple)):
            return convert_structure(obj)
        elif obj != obj:  # Check for NaN
            return None
        return obj

    def convert_structure(structure):
        if isinstance(structure, dict):
            return {k: convert_value(v) for k, v in structure.items()}
        elif isinstance(structure, (list, tuple)):
            return [convert_value(x) for x in structure]
        return structure

    try:
        processed_data = convert_structure(data)
        return json.dumps(processed_data, indent=2)
    except Exception as e:
        logging.error(f"Failed to serialize summary data: {str(e)}")
        return json.dumps({"error": "Could not serialize summary data"})
