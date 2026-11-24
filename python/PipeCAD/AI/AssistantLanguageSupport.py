# -*- coding: utf-8 -*-
"""
Example of integrating language selection into Assistant.py

Shows how to add support for explicit language selection for user requests.
"""

from PipeCAD.AI.Localization import Localization, set_language


class AssistantLanguageSupport:
    """Multilingual support for PipeCAD Assistant"""
    
    def __init__(self):
        """Initialize with auto-detection of OS language"""
        self.l10n = Localization()  # Auto-detect OS language
        self.request_language = self.l10n.get_language()
        
        # Available languages
        self.available_languages = [
            {'code': 'en', 'name': 'English', 'native': 'English'},
            {'code': 'ru', 'name': 'Russian', 'native': 'Русский'},
            {'code': 'zh', 'name': 'Chinese', 'native': '中文'},
        ]
    
    def set_request_language(self, lang_code):
        """
        Set language for user request.
        
        Called from UI when user selects language in dropdown.
        
        Args:
            lang_code: Language code ('en', 'ru', 'zh')
        
        Raises:
            ValueError: If language is not supported
        
        Example:
            assistant.set_request_language('ru')
            # Now all strings will be in Russian
        """
        valid_codes = {lang['code'] for lang in self.available_languages}
        
        if lang_code not in valid_codes:
            raise ValueError(
                f"Unsupported language: {lang_code}. "
                f"Available: {', '.join(valid_codes)}"
            )
        
        self.request_language = lang_code
        self.l10n.set_language(lang_code)
        print(f"Request language set to: {lang_code}")
    
    def get_available_languages(self):
        """
        Get list of available languages for UI.
        
        Returns:
            List[dict]: List with language information
        
        Example:
            languages = assistant.get_available_languages()
            # [
            #   {'code': 'en', 'name': 'English', 'native': 'English'},
            #   {'code': 'ru', 'name': 'Russian', 'native': 'Русский'},
            #   {'code': 'zh', 'name': 'Chinese', 'native': '中文'},
            # ]
        """
        return self.available_languages
    
    def get_current_request_language(self):
        """Get current language for requests"""
        return self.request_language
    
    def process_request(self, user_text):
        """
        Process user request.
        
        Uses language selected by user in UI.
        
        Args:
            user_text: User text
        
        Returns:
            tuple: (system_prompt, user_input) in the same language
        """
        # Language already set from UI via set_request_language()
        
        # System prompt in user language
        system_prompt = self.l10n._("system_prompt")
        
        # User input remains in the same language
        # (user writes in the language they need)
        
        return system_prompt, user_text
    
    def get_localized_string(self, key, **kwargs):
        """
        Get translated string.
        
        Args:
            key: Translation key from localization file
            **kwargs: Parameters for formatting
        
        Returns:
            str: Translated string
        """
        return self.l10n._(key, **kwargs)


# ============================================================================
# Example usage
# ============================================================================

if __name__ == "__main__":
    # Initialization
    assistant = AssistantLanguageSupport()
    
    print(f"Current system language: {assistant.l10n.get_language()}")
    print(f"Available languages: {assistant.get_available_languages()}\n")
    
    # Scenario 1: English OS, user writes in Russian
    print("=== Scenario 1: English OS, Russian input ===")
    assistant.set_request_language('ru')
    system_prompt, user_text = assistant.process_request("Создай трубопровод")
    print(f"Language: {assistant.get_current_request_language()}")
    print(f"System prompt starts with: {system_prompt[:100]}...\n")
    
    # Scenario 2: Switch to Chinese
    print("=== Scenario 2: Chinese input ===")
    assistant.set_request_language('zh')
    system_prompt, user_text = assistant.process_request("创建管道")
    print(f"Language: {assistant.get_current_request_language()}")
    print(f"System prompt starts with: {system_prompt[:100]}...\n")
    
    # Scenario 3: Back to English
    print("=== Scenario 3: English input ===")
    assistant.set_request_language('en')
    system_prompt, user_text = assistant.process_request("Create a pipeline")
    print(f"Language: {assistant.get_current_request_language()}")
    print(f"System prompt starts with: {system_prompt[:100]}...\n")
    
    # Get localized strings
    print("=== Localized strings ===")
    error_msg = assistant.get_localized_string("error_metadata_not_found", count=5)
    print(f"Error message (ru): {error_msg}\n")
