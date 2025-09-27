# prompt_processor/validators.py
import json
from typing import Dict, Any, List, Optional, Tuple
from jsonschema import validate, ValidationError
from .schemas import load_istvon_schema, get_cached_schema

class ISTVONValidator:
    """
    Validates ISTVON JSON structures against the schema
    """
    
    def __init__(self):
        self.schema = get_cached_schema()
    
    def validate_istvon(self, istvon_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate an ISTVON JSON structure
        
        Args:
            istvon_data: The ISTVON JSON to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            validate(instance=istvon_data, schema=self.schema)
            return True, None
        except ValidationError as e:
            return False, f"Validation error at {'.'.join(str(x) for x in e.path)}: {e.message}"
        except Exception as e:
            return False, f"Unexpected validation error: {str(e)}"
    
    def create_minimal_istvon(self, instructions: str) -> Dict[str, Any]:
        """
        Create a minimal valid ISTVON structure
        
        Args:
            instructions: The basic instruction text
            
        Returns:
            Minimal valid ISTVON structure
        """
        return {
            "instructions": instructions,
            "source_data": [{"type": "none", "source": "general_knowledge"}],
            "tools": [{"name": "text_generation"}],
            "variables": {
                "tone": "professional",
                "priority": "medium"
            },
            "outcome": {
                "format": "plain_text",
                "delivery": "display"
            },
            "notification": {
                "method": "none",
                "trigger": "on_completion"
            }
        }
    
    def validate_partial(self, partial_data: Dict[str, Any], 
                        required_only: bool = False) -> Tuple[bool, List[str]]:
        """
        Validate a partial ISTVON structure (useful during form building)
        
        Args:
            partial_data: Incomplete ISTVON data
            required_only: Only validate required fields
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        schema_props = self.schema.get('properties', {})
        required_fields = self.schema.get('required', [])
        
        # Check required fields
        if required_only:
            for field in required_fields:
                if field not in partial_data:
                    errors.append(f"Missing required field: {field}")
        
        # Validate existing fields
        for field, value in partial_data.items():
            if field in schema_props:
                field_schema = schema_props[field]
                try:
                    validate(instance=value, schema=field_schema)
                except ValidationError as e:
                    errors.append(f"Field '{field}': {e.message}")
        
        return len(errors) == 0, errors
    
    def get_validation_suggestions(self, istvon_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get suggestions for improving the ISTVON structure
        
        Args:
            istvon_data: ISTVON data to analyze
            
        Returns:
            Dictionary of component suggestions
        """
        suggestions = {}
        
        # Check instructions quality
        instructions = istvon_data.get('instructions', '')
        if instructions:
            inst_suggestions = []
            if len(instructions.split()) < 5:
                inst_suggestions.append("Consider making instructions more detailed")
            if not any(word in instructions.lower() for word in ['create', 'write', 'analyze', 'generate']):
                inst_suggestions.append("Start with a clear action verb (create, write, analyze, etc.)")
            if inst_suggestions:
                suggestions['instructions'] = inst_suggestions
        
        # Check source_data completeness
        source_data = istvon_data.get('source_data', [])
        if not source_data:
            suggestions['source_data'] = ["Consider specifying data sources for better context"]
        
        # Check variables completeness
        variables = istvon_data.get('variables', {})
        var_suggestions = []
        if 'topic' not in variables:
            var_suggestions.append("Adding a topic would improve clarity")
        if 'target_audience' not in variables:
            var_suggestions.append("Specifying target audience helps tailor content")
        if var_suggestions:
            suggestions['variables'] = var_suggestions
        
        return suggestions


class ISTVONBuilder:
    """
    Helper class to build ISTVON structures step by step
    """
    
    def __init__(self):
        self.validator = ISTVONValidator()
        self.istvon = self.validator.create_minimal_istvon("")
    
    def set_instructions(self, instructions: str) -> 'ISTVONBuilder':
        """Set the instructions component"""
        self.istvon["instructions"] = instructions
        return self
    
    def add_source_data(self, source_type: str, source: str, 
                       description: str = "", required: bool = False) -> 'ISTVONBuilder':
        """Add a data source"""
        # Remove default "none" source if adding real sources
        if (self.istvon["source_data"] and 
            len(self.istvon["source_data"]) == 1 and 
            self.istvon["source_data"][0].get("type") == "none"):
            self.istvon["source_data"] = []
        
        source_item = {
            "type": source_type,
            "source": source,
            "required": required
        }
        if description:
            source_item["description"] = description
        
        self.istvon["source_data"].append(source_item)
        return self
    
    def clear_tools(self) -> 'ISTVONBuilder':
        """Clear default tools to add custom ones"""
        self.istvon["tools"] = []
        return self
    
    def add_tool(self, tool_name: str, version: str = None, 
                 parameters: Optional[Dict] = None) -> 'ISTVONBuilder':
        """Add a tool requirement"""
        tool_item = {"name": tool_name}
        if version:
            tool_item["version"] = version
        if parameters:
            tool_item["parameters"] = parameters
        
        self.istvon["tools"].append(tool_item)
        return self
    
    def set_variables(self, **variables) -> 'ISTVONBuilder':
        """Set variable values"""
        self.istvon["variables"].update(variables)
        return self
    
    def set_outcome(self, format_type: str, delivery: str, 
                   filename: str = None, destination: str = None,
                   **other_options) -> 'ISTVONBuilder':
        """Set outcome specifications"""
        self.istvon["outcome"] = {
            "format": format_type,
            "delivery": delivery
        }
        
        if filename:
            self.istvon["outcome"]["filename"] = filename
        if destination:
            self.istvon["outcome"]["destination"] = destination
        
        # Add any other options
        self.istvon["outcome"].update(other_options)
        return self
    
    def set_notification(self, method: str, recipient: str = None, 
                        trigger: str = "on_completion", 
                        message_template: str = None) -> 'ISTVONBuilder':
        """Set notification preferences"""
        self.istvon["notification"] = {
            "method": method,
            "trigger": trigger
        }
        
        if recipient:
            self.istvon["notification"]["recipient"] = recipient
        if message_template:
            self.istvon["notification"]["message_template"] = message_template
        
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and validate the final ISTVON structure"""
        is_valid, error = self.validator.validate_istvon(self.istvon)
        if not is_valid:
            raise ValueError(f"Invalid ISTVON structure: {error}")
        
        return self.istvon.copy()
    
    def build_partial(self) -> Tuple[Dict[str, Any], bool, List[str]]:
        """Build partial ISTVON and return validation status"""
        is_valid, errors = self.validator.validate_partial(self.istvon)
        return self.istvon.copy(), is_valid, errors