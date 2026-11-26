# -*- coding: utf-8 -*-
"""
PipeCAD AI Assistant - Multilingual Localization System

Loads translations for the explicitly selected language. The assistant uses the
language selected in its request-language dropdown; optional OS-language
detection is available when no language is passed.

Usage:
    l10n = Localization('ru', auto_detect=False)
    message = l10n._("error_metadata_not_found", count=10)
"""

import json
import locale
import os


class Localization:
    """Load and retrieve translations for a selected language."""

    _instance = None
    _loaded_languages = {}
    _available_languages = None

    def __init__(self, language=None, auto_detect=True):
        """Initialize localization system.
        
        Args:
            language: Locale code matching a JSON file in locales/.
                      Full locale names are not normalized.
            auto_detect: If True and language is omitted, use the OS base language.
                         If its translation file is unavailable, English is loaded.
        """
        if language is None and auto_detect:
            language = self._detect_system_language()
        
        self.language = language or 'en'
        self.strings = self._load_strings(self.language)
    
    @staticmethod
    def _detect_system_language():
        """Detect operating system language.
        
        Returns:
            Lowercase base language code (for example, 'zh_CN' becomes 'zh').
            This code is not checked against available translation files here.
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

    @classmethod
    def get_available_languages(cls):
        """Returns locale codes mapped to display names from their JSON metadata."""
        if cls._available_languages is not None:
            return dict(cls._available_languages)

        locales_dir = cls._get_locales_dir()
        languages = {}
        for filename in sorted(os.listdir(locales_dir)):
            if not filename.lower().endswith('.json'):
                continue
            path = os.path.join(locales_dir, filename)
            with open(path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            meta = data.get('meta') or {}
            code = meta.get('locale')
            name = meta.get('language')
            if not code or not name:
                raise ValueError('Locale file is missing meta.locale or meta.language: %s'
                                 % path)
            if code != os.path.splitext(filename)[0]:
                raise ValueError('Locale code does not match filename: %s' % path)
            languages[code] = name
        if not languages:
            raise IOError('No locale JSON files found in %s' % locales_dir)

        cls._available_languages = dict(
            sorted(languages.items(), key=lambda item: (item[0] != 'en', item[0])))
        return dict(cls._available_languages)

    @staticmethod
    def _load_strings(language):
        """Load localization strings for a given language.
        
        Args:
            language: Locale code matching a JSON file in locales/.
        
        Returns:
            Dictionary with translations
        """
        # Reuse translations already loaded for this language.
        if language in Localization._loaded_languages:
            return Localization._loaded_languages[language]
        
        locales_dir = Localization._get_locales_dir()
        lang_file = os.path.join(locales_dir, f'{language}.json')
        
        # Use English when there is no translation file for the requested code.
        if not os.path.isfile(lang_file):
            if language != 'en':
                return Localization._load_strings('en')
            lang_file = os.path.join(locales_dir, 'en.json')
        
        # If even the English file is missing, there are no translations to load.
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
        text = self.get_data(key, key)
        if not isinstance(text, str):
            return text
        
        # Format with parameters (if any)
        try:
            if kwargs:
                return text.format(**kwargs)
        except (KeyError, ValueError):
            # If formatting failed, return original string
            pass
        
        return text

    def get_data(self, key, default=None):
        """Returns a raw locale resource, including non-string structured data."""
        value = self.strings
        for part in key.split('.'):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value
    
    def set_language(self, language):
        """Change language on the fly.
        
        Args:
            language: New language code. If its file is unavailable, English
                      translations are loaded; self.language keeps the requested code.
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
        """Get or create the process-wide localization singleton.
        
        Args:
            language: Language code used only when creating the singleton.
        
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
        Localization._available_languages = None


# Quick functions for use in code
def _(key, **kwargs):
    """Global localization function (uses singleton).
    
    Usage:
        from PipeCAD.AI.Localization import _
        message = _("error_metadata_not_found", count=10)
    """
    return Localization.get_instance()._(key, **kwargs)


def set_language(language):
    """Set the language on the process-wide localization singleton.
    
    Usage:
        from PipeCAD.AI.Localization import set_language
        set_language('ru')

    This does not change separately constructed Localization instances.
    """
    Localization.get_instance().set_language(language)


def get_language():
    """Get current language of the application."""
    return Localization.get_instance().get_language()
