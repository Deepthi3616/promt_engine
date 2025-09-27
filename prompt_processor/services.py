# prompt_processor/services.py
import re
from typing import Dict, List, Any

class ISTVONMapper:
    """
    Converts natural language prompts to ISTVON JSON structure
    """
    
    def __init__(self):
        # Common patterns for mapping
        self.action_keywords = {
            'write': 'text_generation',
            'create': 'text_generation',
            'generate': 'text_generation',
            'analyze': 'data_analysis',
            'search': 'web_search',
            'summarize': 'summarization',
            'translate': 'translation',
            'code': 'code_generation',
        }
        
        self.output_formats = {
            'blog post': 'markdown',
            'blog': 'markdown',
            'report': 'pdf',
            'email': 'plain_text',
            'presentation': 'html',
            'document': 'docx',
            'analysis': 'pdf',
            'summary': 'plain_text',
        }
        
        self.tone_indicators = {
            'professional': 'professional',
            'casual': 'casual',
            'formal': 'formal',
            'friendly': 'friendly',
            'technical': 'technical',
        }

    def convert_to_istvon(self, original_prompt: str) -> Dict[str, Any]:
        """
        Convert natural language prompt to ISTVON JSON structure
        """
        prompt_lower = original_prompt.lower()
        
        # Extract components using rule-based approach
        instructions = self._extract_instructions(original_prompt)
        source_data = self._extract_source_data(prompt_lower)
        tools = self._extract_tools(prompt_lower)
        variables = self._extract_variables(original_prompt)
        outcome = self._extract_outcome(prompt_lower)
        notification = self._extract_notification(prompt_lower)
        
        return {
            "instructions": instructions,
            "source_data": source_data,
            "tools": tools,
            "variables": variables,
            "outcome": outcome,
            "notification": notification
        }
    
    def _extract_instructions(self, prompt: str) -> str:
        """Extract and enhance the core instruction"""
        # Remove common prefixes and clean up
        cleaned = re.sub(r'^(please|can you|could you|i want you to|i need you to)\s*', '', prompt, flags=re.IGNORECASE)
        
        # Capitalize first letter
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned if cleaned else prompt
    
    def _extract_source_data(self, prompt: str) -> List[Dict[str, Any]]:
        """Identify potential data sources"""
        sources = []
        
        # Look for explicit mentions
        if any(word in prompt for word in ['research', 'data', 'file', 'document']):
            sources.append({
                "type": "knowledge_base",
                "source": "research_data",
                "description": "Referenced research or data sources"
            })
        elif any(word in prompt for word in ['company', 'organization', 'internal']):
            sources.append({
                "type": "knowledge_base",
                "source": "company_guidelines",
                "description": "Company or organizational information"
            })
        else:
            sources.append({
                "type": "none",
                "source": "general_knowledge",
                "description": "General knowledge base"
            })
            
        return sources
    
    def _extract_tools(self, prompt: str) -> List[Dict[str, str]]:
        """Identify required tools based on keywords"""
        tools = []
        found_tools = set()
        
        # Check for tool keywords
        for keyword, tool in self.action_keywords.items():
            if keyword in prompt:
                found_tools.add(tool)
        
        # Convert to list of dicts
        for tool in found_tools:
            tools.append({"name": tool})
        
        # Default tool if none identified
        if not tools:
            tools.append({"name": "text_generation"})
            
        return tools
    
    def _extract_variables(self, prompt: str) -> Dict[str, Any]:
        """Extract dynamic variables"""
        variables = {}
        
        # Extract topic (often the main subject after 'about')
        topic_match = re.search(r'about\s+([^,.\n!?]+)', prompt, re.IGNORECASE)
        if topic_match:
            variables['topic'] = topic_match.group(1).strip()
        else:
            # Try to extract from context
            words = prompt.split()
            if len(words) > 3:
                # Take a reasonable guess at the topic
                variables['topic'] = ' '.join(words[1:4])
        
        # Extract tone indicators
        for indicator, tone in self.tone_indicators.items():
            if indicator in prompt.lower():
                variables['tone'] = tone
                break
        else:
            variables['tone'] = 'professional'  # default
        
        # Extract length if mentioned
        length_match = re.search(r'(\d+)\s*(words?|pages?|paragraphs?)', prompt.lower())
        if length_match:
            variables['length'] = f"{length_match.group(1)} {length_match.group(2)}"
        
        # Extract audience if mentioned
        audience_match = re.search(r'for\s+([^,.\n!?]+)', prompt, re.IGNORECASE)
        if audience_match:
            variables['target_audience'] = audience_match.group(1).strip()
            
        variables['priority'] = 'medium'  # default
        variables['language'] = 'en'      # default
        
        return variables
    
    def _extract_outcome(self, prompt: str) -> Dict[str, Any]:
        """Determine output format and delivery"""
        outcome = {
            "format": "plain_text",
            "delivery": "display"
        }
        
        # Determine format based on content type
        for content_type, format_type in self.output_formats.items():
            if content_type in prompt:
                outcome["format"] = format_type
                break
        
        # Check for save/export instructions
        if any(word in prompt for word in ['save', 'export', 'download', 'file']):
            outcome["delivery"] = "save_to_file"
        
        return outcome
    
    def _extract_notification(self, prompt: str) -> Dict[str, str]:
        """Determine notification preferences"""
        notification = {
            "method": "none",
            "trigger": "on_completion"
        }
        
        if 'email' in prompt or 'notify' in prompt:
            notification["method"] = "email"
        elif 'alert' in prompt or 'ping' in prompt:
            notification["method"] = "in_app"
            
        return notification