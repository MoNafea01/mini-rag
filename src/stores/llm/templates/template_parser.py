import os
from string import Template

class TemplateParser:
    current_path = os.path.dirname(os.path.abspath(__file__))
    
    def __init__(self, language: str, default_language: str="en"):
        self.default_language = default_language
        self.language = None
        self.set_language(language)
        
    def set_language(self, language: str):
        if not language:
            self.language = self.default_language
            return
        
        language_path = os.path.join(TemplateParser.current_path, 'locales', language)
        if os.path.exists(language_path):
            self.language = language
            return

        self.language = self.default_language
    
    
    def get_text(self, group: str, key: str, vars: dict=None) -> str:
        if not (group and key):
            return None
        
        # Sanitize group to prevent path traversal
        if not group.replace('_', '').isalnum():
            return None
        
        vars = vars or {}
        
        language = self.language
        
        group_path = os.path.join(TemplateParser.current_path, 'locales', self.language, f"{group}.py")
        if not os.path.exists(group_path):
            group_path = os.path.join(TemplateParser.current_path, 'locales', self.default_language, f"{group}.py")
            language = self.default_language
            
        if not os.path.exists(group_path):
            return None
        
        grp_module = __import__(f"stores.llm.templates.locales.{language}.{group}", fromlist=[group])
        
        k_attr: Template = getattr(grp_module, key, None)
        if not k_attr:
            return None
        
        return k_attr.substitute(vars)
