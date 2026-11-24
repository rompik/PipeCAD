# -*- coding: utf-8 -*-
"""
PipeCAD AI Assistant - Multilingual Localization System

Provides automatic language detection and translation support for all UI strings.

Usage:
    l10n = Localization()  # Auto-detect OS language
    message = l10n._("error_metadata_not_found", count=10)
"""

import json
import locale
import os


class Localization:
    """Multilingual localization system for PipeCAD AI Assistant."""

    _instance = None
    _loaded_languages = {}

    def __init__(self, language=None, auto_detect=True):
        """Initialize localization system.
        
        Args:
            language: Language code ('en', 'zh', 'ru', 'de', etc.)
                     or full locale name ('en_US', 'zh_CN', etc.)
            auto_detect: If True and language is not specified, auto-detect OS language
        """
        if language is None and auto_detect:
            language = self._detect_system_language()
        
        self.language = language or 'en'
        self.strings = self._load_strings(self.language)
    
    @staticmethod
    def _detect_system_language():
        """Detect operating system language.
        
        Returns:
            Language code (e.g., 'en', 'zh', 'ru', 'de')
        """
        try:
            lang, _ = locale.getdefaultlocale()
            if lang:
                # Convert 'zh_CN' -> 'zh', 'en_US' -> 'en'
                return lang.split('_')[0].lower()
        except Exception:
            pass
        return 'en'  # Fallback to English
    
    @staticmethod
    def _get_locales_dir():
        """Get the path to the localization directory.
        
        Returns:
            Absolute path to locales/ folder next to this module
        """
        module_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(module_dir, 'locales')
    
    @staticmethod
    def _load_strings(language):
        """Load localization strings for a given language.
        
        Args:
            language: Language code ('en', 'zh', 'ru', etc.)
        
        Returns:
            Dictionary with translations
        """
        # Cache: don't load twice
        if language in Localization._loaded_languages:
            return Localization._loaded_languages[language]
        
        locales_dir = Localization._get_locales_dir()
        lang_file = os.path.join(locales_dir, f'{language}.json')
        
        # Fallback: if file not found, try English
        if not os.path.isfile(lang_file):
            if language != 'en':
                return Localization._load_strings('en')
            lang_file = os.path.join(locales_dir, 'en.json')
        
        # Fallback: if no files exist, return empty dictionary
        if not os.path.isfile(lang_file):
            return {}
        
        try:
            with open(lang_file, 'r', encoding='utf-8-sig') as f:
                strings = json.load(f)
            Localization._loaded_languages[language] = strings
            return strings
        except (IOError, json.JSONDecodeError):
            # If loading failed, return empty dictionary
            return {}
    
    def _(self, key, **kwargs):
        """Get translated string.
        
        Args:
            key: Translation key from localization file
            **kwargs: Parameters for string formatting
        
        Returns:
            Translated string, or key if translation not found
        """
        # Get string from dictionary, or return key as fallback
        text = self.strings.get(key, key)
        
        # Format with parameters (if any)
        try:
            if kwargs:
                return text.format(**kwargs)
        except (KeyError, ValueError):
            # If formatting failed, return original string
            pass
        
        return text
    
    def set_language(self, language):
        """Change language on the fly.
        
        Args:
            language: New language code
        """
        self.language = language
        self.strings = self._load_strings(language)
    
    def get_language(self):
        """Get current language code.
        
        Returns:
            Language code (e.g., 'en', 'zh', 'ru')
        """
        return self.language
    
    @staticmethod
    def get_instance(language=None):
        """Get or create global localization instance (singleton).
        
        Args:
            language: Language code (optional)
        
        Returns:
            Localization instance
        """
        if Localization._instance is None:
            Localization._instance = Localization(language)
        return Localization._instance
    
    @staticmethod
    def reset_instance():
        """Reset global instance (for testing)."""
        Localization._instance = None
        Localization._loaded_languages.clear()


# Quick functions for use in code
def _(key, **kwargs):
    """Global localization function (uses singleton).
    
    Usage:
        from PipeCAD.AI.Localization import _
        message = _("error_metadata_not_found", count=10)
    """
    return Localization.get_instance()._(key, **kwargs)


def set_language(language):
    """Set language for the entire application.
    
    Usage:
        from PipeCAD.AI.Localization import set_language
        set_language('ru')
    """
    Localization.get_instance().set_language(language)


def get_language():
    """Get current language of the application."""
    return Localization.get_instance().get_language()
