# prompt_processor/schemas/__init__.py
import json
import os
from typing import Dict, Any

def load_istvon_schema() -> Dict[str, Any]:
    """
    Load the ISTVON schema from the JSON file
    """
    schema_path = os.path.join(os.path.dirname(__file__), 'istvon_schema.json')
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            schema = json.load(file)
        return schema
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema file: {e}")

def get_schema_properties() -> Dict[str, Any]:
    """
    Get the properties section from the schema for form generation
    """
    schema = load_istvon_schema()
    return schema.get('properties', {})

def get_required_fields() -> list:
    """
    Get list of required fields from schema
    """
    schema = load_istvon_schema()
    return schema.get('required', [])

def get_field_enums() -> Dict[str, list]:
    """
    Extract all enum values from the schema for dropdown generation
    """
    properties = get_schema_properties()
    enums = {}
    
    def extract_enums(obj, prefix=""):
        if isinstance(obj, dict):
            if 'enum' in obj:
                enums[prefix] = obj['enum']
            for key, value in obj.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                extract_enums(value, new_prefix)
        elif isinstance(obj, list):
            for item in obj:
                extract_enums(item, prefix)
    
    extract_enums(properties)
    return enums

# Cache the schema to avoid repeated file reads
_cached_schema = None

def get_cached_schema() -> Dict[str, Any]:
    """
    Get cached schema or load it if not cached
    """
    global _cached_schema
    if _cached_schema is None:
        _cached_schema = load_istvon_schema()
    return _cached_schema