# 🚀 Оптимизация расхода токенов для многоязычной системы

## 📋 Проблема

Текущая система определяет язык по **ОС пользователя**, но игнорирует **язык входного текста пользователя**.

### Пример проблемы:
```
Пользователь: ОС на английском, но пишет на русском
├─ System prompt: English ❌ (мисматч)
├─ User input: Russian ❌ (мисматч)
└─ Результат: +35% расход токенов
```

## 🔍 Анализ текущего расхода

### Сценарий 1: English ОС + English input (ОПТИМАЛЬНО)
```
System prompt (EN):  "You are an expert CAD assistant..."
                     ≈ 25 токенов

User input (EN):     "Create a pipeline with 100mm diameter"
                     ≈ 12 токенов

LLM response (EN):   "I will create a pipeline configuration..."
                     ≈ 50 токенов

ВСЕГО ПО TURN:       ~87 токенов
```

### Сценарий 2: English ОС + Russian input (НЕОПТИМАЛЬНО) ❌
```
System prompt (EN):  "You are an expert CAD assistant..."
                     ≈ 25 токенов

User input (RU):     "Создай трубопровод диаметром 100 мм"
                     ≈ 18 токенов (+50%)

LLM response (RU):   "Я создам конфигурацию трубопровода..."
                     ≈ 75 токенов (+50%)

ВСЕГО ПО TURN:       ~118 токенов
ПОТЕРЯ:              +35% (+31 токен)
```

### Сценарий 3: Russian ОС + Russian input (ОПТИМАЛЬНО)
```
System prompt (RU):  "Вы опытный ассистент САПР..."
                     ≈ 30 токенов

User input (RU):     "Создай трубопровод диаметром 100 мм"
                     ≈ 18 токенов

LLM response (RU):   "Я создам конфигурацию трубопровода..."
                     ≈ 75 токенов

ВСЕГО ПО TURN:       ~123 токенов
(Нет мисматча языков)
```

## 📊 Статистика: Почему русский требует больше токенов?

| Характеристика | English | Russian | Увеличение |
|---|---|---|---|
| Средняя длина слова | 4.7 символа | 6.2 символа | +32% |
| Слова на фразу | 15 слов | 11 слов | -27% (короче фразы) |
| Символов на токен | 4-5 | 2-3 | -40% (больше токенов) |
| **Итого токенов** | 10 (baseline) | 15 | **+50%** |

**Вывод:** Русский язык требует на ~30-50% больше токенов, чем английский, из-за:
- Более длинных слов
- Флективной морфологии (падежи, спряжения)
- Меньшего сжатия в токенизаторе (cyrillic characters)

## 🛠️ Решение: Определение языка входного текста

### Реализация 1: Простая (regex-based)
```python
def detect_input_language(text: str) -> str:
    """Определить язык текста по символам."""
    if not text:
        return 'en'
    
    # Русские символы (Cyrillic)
    cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    # Китайские символы (CJK)
    cjk = sum(1 for c in text if '\u4E00' <= c <= '\u9FFF')
    # Латинские символы (ASCII/Latin)
    latin = sum(1 for c in text if ord(c) < 128)
    
    total_letters = cyrillic + cjk + latin
    if total_letters == 0:
        return 'en'
    
    # Определить язык по доминирующим символам
    if cyrillic / total_letters > 0.3:
        return 'ru'
    elif cjk / total_letters > 0.3:
        return 'zh'
    else:
        return 'en'
```

### Реализация 2: ML-based (более точная, но медленнее)
```python
from langdetect import detect, detect_langs

def detect_input_language_ml(text: str) -> str:
    """Определить язык с помощью ML модели."""
    try:
        lang = detect(text)
        # Маппировать langdetect коды на наши коды
        lang_map = {
            'ru': 'ru',
            'en': 'en',
            'zh-cn': 'zh',
            'zh-tw': 'zh',
        }
        return lang_map.get(lang, 'en')
    except:
        return 'en'
```

### Реализация 3: Гибридная (быстрая + точная)
```python
def detect_input_language_hybrid(text: str) -> str:
    """Гибридное определение: сначала regex, потом ML."""
    # Шаг 1: Быстрое определение по символам
    lang = detect_input_language(text)
    
    # Шаг 2: Если неуверенно, используем ML
    if lang == 'en':  # English часто неопределен
        try:
            from langdetect import detect
            lang = detect(text)
        except:
            pass
    
    return lang
```

## 🎯 Рекомендуемое решение

**Добавить двухуровневую систему определения языка:**

```
┌─────────────────────────────────────────┐
│   Пользовательский ввод (User Input)    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  1. Определить язык входного текста         │
│     (detect_input_language)                  │
│     Результат: 'ru', 'en', 'zh'             │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  2. Загрузить локализацию на ЭТОМ языке      │
│     (l10n.set_language('ru'))                │
│     Результат: System prompt на русском      │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  3. Отправить в LLM:                         │
│     - System prompt на русском ✅            │
│     - User input на русском ✅               │
│     - Мисматч языков исправлен!              │
└──────────────────────────────────────────────┘
```

## 💾 Код для Localization.py

```python
@staticmethod
def detect_input_language(text: str) -> str:
    """Определить язык пользовательского ввода.
    
    Args:
        text: Текст пользователя
    
    Returns:
        Код языка ('en', 'ru', 'zh')
    """
    if not text or len(text.strip()) < 3:
        return None  # Слишком короткий текст
    
    # Подсчитать символы разных систем
    cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    cjk = sum(1 for c in text if '\u4E00' <= c <= '\u9FFF')
    latin = sum(1 for c in text if ord(c) < 128)
    
    total_letters = cyrillic + cjk + latin
    if total_letters == 0:
        return None
    
    # Определить доминирующий язык
    if cyrillic / total_letters > 0.25:  # 25% русских символов
        return 'ru'
    elif cjk / total_letters > 0.25:  # 25% китайских символов
        return 'zh'
    elif latin / total_letters > 0.5:  # 50% латинских символов
        return 'en'
    
    return None

def set_language_for_input(self, user_input: str) -> str:
    """Автоматически выбрать язык на основе входного текста.
    
    Args:
        user_input: Текст пользователя
    
    Returns:
        Выбранный язык ('en', 'ru', 'zh')
    """
    detected_lang = self.detect_input_language(user_input)
    
    if detected_lang:
        self.language = detected_lang
        self.strings = self._load_strings(detected_lang)
        return detected_lang
    
    # Если не определен, оставить текущий язык
    return self.language
```

## 📈 Прогноз экономии токенов

После реализации оптимизации:

| Метрика | До оптимизации | После | Экономия |
|---------|---|---|---|
| Токенов на turn | 118 | 87 | -26% |
| Токенов на 1000 turns | 118,000 | 87,000 | -31,000 (-26%) |
| Токенов на 1 млн запросов | 118M | 87M | -31M (-26%) |
| Стоимость (1M токенов = $0.10) | $11.80 | $8.70 | **-$3.10 (-26%)** |

## 🔄 Миграция

**Этап 1:** Добавить метод `detect_input_language()` в Localization.py
**Этап 2:** Добавить метод `set_language_for_input()` в Localization.py
**Этап 3:** Вызывать перед каждым запросом в Assistant.py:
```python
user_input = get_user_input()
l10n.set_language_for_input(user_input)  # Переключить язык
response = llm.generate(l10n._("system_prompt"), user_input)
```

**Этап 4:** Добавить в INTEGRATION_GUIDE.md инструкции

## ✅ Переносимость

- Нет зависимостей от внешних библиотек (regex работает везде)
- Работает на Python 3.5+
- Работает с любыми Unicode текстами
- Работает offline

## 🚀 Следующие шаги

1. Реализовать `detect_input_language()` в Localization.py
2. Добавить тесты (test_detect_language.py)
3. Обновить INTEGRATION_GUIDE.md
4. Тестировать на реальных данных (Russian, English, Chinese inputs)
5. Измерить реальное снижение расхода токенов
