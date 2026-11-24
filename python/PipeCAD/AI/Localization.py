# -*- coding: utf-8 -*-
"""
PipeCAD AI Assistant - Multilingual Localization System

Система многоязычной поддержки для Assistant.py.
Автоматически определяет язык пользователя и предоставляет переводы всех строк.

Использование:
    l10n = Localization()  # Auto-detect языка ОС
    message = l10n._("error_metadata_not_found", count=10)
"""

import json
import locale
import os


class Localization:
    """Система многоязычной локализации для PipeCAD AI Assistant."""

    _instance = None
    _loaded_languages = {}

    def __init__(self, language=None, auto_detect=True):
        """Инициализация локализации.
        
        Args:
            language: Код языка ('en', 'zh', 'ru', 'de', etc.)
                     или полное имя локали ('en_US', 'zh_CN', etc.)
            auto_detect: Если True и language не указан, определить язык ОС
        """
        if language is None and auto_detect:
            language = self._detect_system_language()
        
        self.language = language or 'en'
        self.strings = self._load_strings(self.language)
    
    @staticmethod
    def _detect_system_language():
        """Определить язык операционной системы.
        
        Returns:
            Код языка (e.g., 'en', 'zh', 'ru', 'de')
        """
        try:
            lang, _ = locale.getdefaultlocale()
            if lang:
                # Преобразовать 'zh_CN' -> 'zh', 'en_US' -> 'en'
                return lang.split('_')[0].lower()
        except Exception:
            pass
        return 'en'  # Fallback на английский
    
    @staticmethod
    def _get_locales_dir():
        """Получить путь к директории с локализациями.
        
        Returns:
            Абсолютный путь к папке locales/ рядом с этим модулем
        """
        module_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(module_dir, 'locales')
    
    @staticmethod
    def _load_strings(language):
        """Загрузить строки локализации для указанного языка.
        
        Args:
            language: Код языка ('en', 'zh', 'ru', etc.)
        
        Returns:
            Dict с переводами
        """
        # Кэширование: не загружать дважды
        if language in Localization._loaded_languages:
            return Localization._loaded_languages[language]
        
        locales_dir = Localization._get_locales_dir()
        lang_file = os.path.join(locales_dir, f'{language}.json')
        
        # Fallback: если файл не найден, попробовать английский
        if not os.path.isfile(lang_file):
            if language != 'en':
                return Localization._load_strings('en')
            lang_file = os.path.join(locales_dir, 'en.json')
        
        # Fallback: если нет ни одного файла, вернуть пустой словарь
        if not os.path.isfile(lang_file):
            return {}
        
        try:
            with open(lang_file, 'r', encoding='utf-8-sig') as f:
                strings = json.load(f)
            Localization._loaded_languages[language] = strings
            return strings
        except (IOError, json.JSONDecodeError):
            # Если не смогли загрузить, вернуть пустой словарь
            return {}
    
    def _(self, key, **kwargs):
        """Получить переведённую строку.
        
        Args:
            key: Ключ строки в локализационном файле
            **kwargs: Параметры для форматирования строки
        
        Returns:
            Переведённая строка, или ключ если перевод не найден
        """
        # Получить строку из словаря, или вернуть ключ как fallback
        text = self.strings.get(key, key)
        
        # Форматирование с параметрами (если есть)
        try:
            if kwargs:
                return text.format(**kwargs)
        except (KeyError, ValueError):
            # Если форматирование не удалось, вернуть оригинальную строку
            pass
        
        return text
    
    def set_language(self, language):
        """Изменить язык на лету.
        
        Args:
            language: Новый код языка
        """
        self.language = language
        self.strings = self._load_strings(language)
    
    def get_language(self):
        """Получить текущий код языка.
        
        Returns:
            Код языка (e.g., 'en', 'zh', 'ru')
        """
        return self.language
    
    @staticmethod
    def get_instance(language=None):
        """Получить или создать глобальный экземпляр локализации (singleton).
        
        Args:
            language: Код языка (опционально)
        
        Returns:
            Экземпляр Localization
        """
        if Localization._instance is None:
            Localization._instance = Localization(language)
        return Localization._instance
    
    @staticmethod
    def reset_instance():
        """Сбросить глобальный экземпляр (для тестирования)."""
        Localization._instance = None
        Localization._loaded_languages.clear()


# Быстрые функции для использования в коде
def _(key, **kwargs):
    """Глобальная функция локализации (использует singleton).
    
    Usage:
        from PipeCAD.AI.Localization import _
        message = _("error_metadata_not_found", count=10)
    """
    return Localization.get_instance()._(key, **kwargs)


def set_language(language):
    """Установить язык для всего приложения.
    
    Usage:
        from PipeCAD.AI.Localization import set_language
        set_language('ru')
    """
    Localization.get_instance().set_language(language)


def get_language():
    """Получить текущий язык приложения."""
    return Localization.get_instance().get_language()
