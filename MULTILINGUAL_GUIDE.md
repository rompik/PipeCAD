# 🌍 PipeCAD AI Assistant - Система многоязычной поддержки

## 📋 Обзор

Текущий код Assistant.py жестко закодирован на **китайском языке** (中文). Для поддержки **любого нативного языка пользователя**, необходимо реализовать систему локализации.

## 🎯 Решение: 3-уровневая архитектура

### Уровень 1: Детектирование языка пользователя
```python
# Автоматическое определение языка ОС
import locale

def get_user_language():
    """Получить язык пользователя"""
    lang, _ = locale.getdefaultlocale()
    return lang  # 'zh_CN', 'en_US', 'ru_RU', 'de_DE', etc.
```

### Уровень 2: Система локализации (i18n)
Создать структуру переводов для всех строк:
```
locales/
├── en.json          # English
├── zh_CN.json       # Chinese Simplified
├── zh_TW.json       # Chinese Traditional
├── ru.json          # Russian
├── de.json          # German
├── fr.json          # French
├── ja.json          # Japanese
└── es.json          # Spanish
```

### Уровень 3: Кэширование и производительность
- Загружать нужный файл локализации при инициализации
- Кэшировать переводы в памяти
- Переключение языка в runtime

## 📝 Ключевые компоненты для локализации

### 1. SYSTEM_PROMPT (главный системный промпт)
**Текущее состояние:** Жестко закодирован на китайском
**Решение:** Параметризировать по языку

### 2. Сообщения об ошибках
- `'未找到 MetaData.json'` → `'MetaData.json not found'`
- `'窗口层需要 PythonQt'` → `'Window layer requires PythonQt'`

### 3. Справочный текст (Help, Docs)
- Описания функций (docstring)
- Комментарии в коде

### 4. UI текст (для Qt)
- Заголовки окон (`"Create Equipment"`)
- Метки полей (labels)
- Кнопки

### 5. Вспомогательные данные
- `CN_HINTS` → Словари синонимов для каждого языка
- Комментарии в коде

## 🔧 Реализация

### Шаг 1: Создать класс локализации
```python
class Localization:
    def __init__(self, language='auto'):
        self.language = language or self.detect_language()
        self.strings = self._load_strings()
    
    def _(self, key, **kwargs):
        """Получить переведённую строку"""
        text = self.strings.get(key, key)
        return text.format(**kwargs) if kwargs else text
    
    def detect_language(self):
        """Определить язык ОС"""
        lang = locale.getdefaultlocale()[0]
        return lang.split('_')[0]  # 'en', 'zh', 'ru'
```

### Шаг 2: Структура JSON локализации
```json
{
  "system_prompt": "You are a PipeCAD modeling assistant...",
  "user_request": "User request:",
  "current_model_state": "Current model state:",
  "error_metadata_not_found": "MetaData.json not found in {count} locations",
  "error_requires_pythonqt": "Window layer requires PythonQt",
  "ui_create_equipment": "Create Equipment",
  "ui_name": "Name",
  "ui_position": "Position",
  "ui_east": "East",
  "ui_north": "North",
  "ui_up": "Up"
}
```

### Шаг 3: Языковые словари синонимов
```python
# Вместо одного CN_HINTS
LANGUAGE_HINTS = {
    'en': {
        'tank': ['EQUI', 'CYLI', 'NOZZ'],
        'pipe': ['PIPE', 'BRAN', 'TUBE'],
        'elbow': ['ELBO'],
        'tee': ['TEE'],
    },
    'zh': {
        '罐': ['EQUI', 'CYLI', 'NOZZ'],
        '管': ['PIPE', 'BRAN', 'TUBE'],
        '弯头': ['ELBO'],
        '三通': ['TEE'],
    },
    'ru': {
        'бак': ['EQUI', 'CYLI', 'NOZZ'],
        'труба': ['PIPE', 'BRAN', 'TUBE'],
        'отвод': ['ELBO'],
        'тройник': ['TEE'],
    },
}
```

## 🚀 Преимущества подхода

| Аспект | Преимущество |
|--------|-------------|
| **Скорость** | O(1) поиск в JSON, кэширование в памяти |
| **Масштабируемость** | Просто добавить новый язык (новый JSON файл) |
| **Поддержка** | Нетехнический персонал может обновлять переводы |
| **Fallback** | Если перевод отсутствует, использовать ключ как текст |
| **Dynamic** | Смена языка без перезагрузки (если нужно) |
| **Асинхронность** | LLM ответит на языке пользователя (multilingual модели) |

## 📊 Пример использования

```python
# Инициализация
l10n = Localization()  # Auto-detect

# В коде
raise IOError(l10n._("error_metadata_not_found", count=len(probes)))

# Для системного промпта
system_prompt = l10n._("system_prompt")

# Для UI
dialog = EquipmentDialog(MainWindow, language=l10n.language)
dialog.setWindowTitle(l10n._("ui_create_equipment"))
```

## ⚙️ Интеграция с LLM

**Важно:** LLM-модели (ChatGPT, DeepSeek, etc.) уже **многоязычны** по умолчанию!

```python
def build_system_prompt(schema_text, l10n, skill_text=''):
    prompt = l10n._("system_prompt") + '\n# Schema for this request\n' + (...)
    return prompt

def build_user_prompt(user_text, model_context, l10n, extra=''):
    parts = [l10n._("user_request") + ':\n%s' % user_text.strip()]
    if model_context:
        parts.append(l10n._("current_model_state") + ':\n%s' % model_context)
    return '\n\n'.join(parts)
```

**Результат:** Если пользователь пишет на русском → LLM ответит на русском. Если на английском → ответит на английском. Если на смешанном → ответит на смешанном.

## 🎓 Лучшие практики

1. **Не переводить:**
   - Имена переменных (camelCase остаётся)
   - Технические термины (Position, Direction, PIPE)
   - API имена функций

2. **Переводить:**
   - Сообщения об ошибках
   - Справку и комментарии
   - UI текст
   - Слова в системном промпте

3. **Документирование:**
   - Каждая строка i18n должна иметь контекст (комментарий в JSON)
   - Версия локализации в файле

4. **Тестирование:**
   - Проверить все языки на корректность
   - Убедиться, что ключи совпадают между локалями

## 📝 Поддерживаемые языки (рекомендация)

- ✅ **Chinese (中文)** - исходный язык
- ✅ **English (English)** - основной язык разработки  
- ✅ **Russian (Русский)** - пользователь (вы)
- ✅ **Japanese (日本語)** - технический рынок
- ✅ **German (Deutsch)** - инженеры
- ✅ **Spanish (Español)** - латинская америка
- ✅ **French (Français)** - французские проекты

## 🔄 Дальнейшие улучшения

1. **Context-aware**: Запомнить предпочитаемый язык пользователя
2. **Dynamic loading**: Загружать локали по требованию (не все сразу)
3. **Pluralization**: Правила для множественных форм (en/ru различаются)
4. **Regional variants**: en_US vs en_GB vs en_AU
5. **RTL support**: Арабский, иврит (если потребуется)

---

**Итог:** Добавить многоязычность можно за 1-2 дня работы, просто параметризировав существующий код и создав JSON файлы локализации.
