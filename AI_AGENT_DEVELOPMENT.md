# 🤖 PipeCAD AI Agent Development Branch

## 📌 Обзор

Это отдельная ветка разработки для **AI Agent Development** в проекте PipeCAD. 
Здесь собраны все улучшения и нововведения для PipeCAD AI Assistant, включая:

- ✅ Система многоязычной поддержки (i18n)
- 🧪 Инфраструктура для тестирования AI агентов
- 📚 Расширенная документация и примеры
- 🔧 Утилиты для разработки и отладки

---

## 🌳 Информация о ветке

```
Ветка:     feature/ai-agent-development
Базовая:   docs/python-documentation
Статус:    ✅ Активная разработка
Версия:    1.0.0 (Multilingual Support)
```

### Git информация

```bash
# Переключиться на ветку
git checkout feature/ai-agent-development

# Посмотреть всю историю ветки
git log --oneline feature/ai-agent-development

# Сравнить с главной веткой
git diff main feature/ai-agent-development

# Увидеть только изменения этой ветки
git log --oneline main..feature/ai-agent-development
```

---

## 📂 Структура проекта

```
PipeCAD/
├── 📄 AI_AGENT_DEVELOPMENT.md          ← Вы находитесь здесь
├── 📄 MULTILINGUAL_GUIDE.md            Архитектура i18n системы
├── 📄 INTEGRATION_GUIDE.md             Как интегрировать в код
├── 📄 QUICK_REFERENCE.md              Быстрая справка и примеры
│
└── python/PipeCAD/AI/
    ├── 📄 Assistant.py                (3,325 строк) - Основной AI ассистент
    ├── 🆕 Localization.py             (200+ строк) - Система локализации
    │
    └── locales/                       Директория переводов
        ├── 📄 en.json                 English
        ├── 📄 ru.json                 Русский  
        └── 📄 zh.json                 中文 (Chinese)
```

---

## 🚀 Быстрый старт

### 1️⃣ Инициализировать систему локализации

```python
from PipeCAD.AI.Localization import Localization

# Автоматически определит язык ОС
l10n = Localization()
print(f"Язык: {l10n.get_language()}")  # 'ru' или 'en' или 'zh'
```

### 2️⃣ Использовать переводы в коде

```python
# Получить переведённую строку
message = l10n._("error_metadata_not_found", count=10)

# На русском: "MetaData.json не найден в 10 местах"
# На английском: "MetaData.json not found in 10 locations"
```

### 3️⃣ Обновить Assistant.py

```python
# В AIAssistantCore.__init__():
self.l10n = Localization(language)  # Auto-detect если None

# Использовать в коде:
raise IOError(self.l10n._("error_metadata_not_found", count=len(probes)))
```

---

## 📚 Документация

### 🔵 MULTILINGUAL_GUIDE.md
**Архитектура и дизайн системы локализации**

Содержит:
- 3-уровневая архитектура решения
- Почему JSON вместо gettext/Babel
- Интеграция с LLM моделями
- Преимущества и недостатки подхода
- Поддерживаемые и рекомендуемые языки
- Дальнейшие улучшения

**Читайте если:** Нужно понять как работает система

---

### 🟢 INTEGRATION_GUIDE.md
**Пошаговая инструкция по интеграции**

Содержит:
- 9 шагов для полной интеграции
- Примеры "БЫЛО vs СТАЛО"
- Как использовать в своем коде
- Поддержка Qt диалогов
- Утилиты для разработчиков
- Экспорт CSV для переводчиков

**Читайте если:** Нужно интегрировать в Assistant.py

---

### 🟡 QUICK_REFERENCE.md
**Быстрая справка и примеры использования**

Содержит:
- TL;DR в 3 шага
- Структура файлов проекта
- Таблица поддерживаемых языков
- Примеры использования
- Полный API справочник
- Как добавить новый язык
- Как редактировать переводы
- Тестирование и troubleshooting
- FAQ (часто задаваемые вопросы)
- Контрольный список интеграции

**Читайте если:** Нужна быстрая информация или примеры

---

## 🌍 Поддерживаемые языки

### ✅ Реализованные (готовы к использованию)

| Код | Язык | Файл | Статус |
|-----|------|------|--------|
| `en` | 🇬🇧 English | en.json | ✅ Готово (103 ключа) |
| `zh` | 🇨🇳 中文 | zh.json | ✅ Готово (103 ключа) |
| `ru` | 🇷🇺 Русский | ru.json | ✅ Готово (103 ключа) |

### 📝 Готовы к добавлению (шаблоны есть)

| Код | Язык | Шаблон |
|-----|------|--------|
| `de` | 🇩🇪 Deutsch | Копировать en.json |
| `fr` | 🇫🇷 Français | Копировать en.json |
| `es` | 🇪🇸 Español | Копировать en.json |
| `ja` | 🇯🇵 日本語 | Копировать en.json |

---

## 🎯 Категории переводов (103 ключа)

```
├─ Системные строки (3):
│  ├─ system_prompt
│  ├─ user_request
│  └─ current_model_state
│
├─ Ошибки - error_* (9):
│  ├─ error_metadata_not_found
│  ├─ error_requires_pythonqt
│  ├─ error_import_failed
│  ├─ error_invalid_response
│  ├─ error_execution_failed
│  ├─ error_validation_failed
│  ├─ error_timeout
│  ├─ error_connection
│  └─ error_invalid_language
│
├─ UI элементы - ui_* (21):
│  ├─ ui_create_equipment
│  ├─ ui_name, ui_position
│  ├─ ui_east, ui_north, ui_up
│  ├─ ui_description, ui_function, ui_purpose
│  ├─ ui_ok, ui_cancel, ui_close, ui_apply
│  └─ ... и другие
│
├─ Логирование - log_* (9):
│  ├─ log_start
│  ├─ log_config_loaded
│  ├─ log_metadata_loaded
│  ├─ log_model_initialized
│  └─ ... и другие
│
├─ Справка - help_* (3):
│  ├─ help_title
│  ├─ help_intro
│  └─ help_examples
│
├─ О программе - about_* (3):
│  ├─ about_title
│  ├─ about_version
│  └─ about_description
│
├─ Статусы - status_* (4):
│  ├─ status_ready
│  ├─ status_processing
│  ├─ status_error
│  └─ status_success
│
└─ Подсказки типов - hint_* (42):
   ├─ hint_tank, hint_pipe, hint_elbow, hint_tee
   ├─ hint_reducer, hint_flange, hint_valve, hint_gasket
   ├─ hint_cap, hint_nozzle, hint_support, hint_structure
   └─ hint_zone
```

---

## 🔄 Процесс разработки

### 1. Создание новой фичи

```bash
# Убедиться что вы на feature/ai-agent-development
git branch -v

# Создать подветку для конкретной фичи
git checkout -b feature/ai-agent-development/feature-name

# Работать с кодом...

# Коммитить изменения
git commit -m "feat: описание изменения"
```

### 2. Запуск тестов

```bash
# Протестировать автоопределение языка
python -c "from PipeCAD.AI.Localization import Localization; l10n = Localization(); print(f'Язык: {l10n.get_language()}')"

# Протестировать получение строк
python -c "from PipeCAD.AI.Localization import Localization; l10n = Localization('ru'); print(l10n._('error_timeout', timeout=30))"
```

### 3. Создание Pull Request

```bash
# Запушить ветку в репозиторий
git push origin feature/ai-agent-development/feature-name

# На GitHub создать Pull Request
# - Target: feature/ai-agent-development
# - Source: feature/ai-agent-development/feature-name
```

### 4. Слияние в основную ветку

```bash
# Когда готово к релизу
git checkout main
git merge --no-ff feature/ai-agent-development

# Пометить релиз тегом
git tag -a v1.0.0-ai-agent -m "AI Agent Development v1.0.0"
```

---

## 📊 Статистика ветки

```
Файлы добавлены:    8
Файлы изменены:     1 (Assistant.py)
Строк добавлено:    ~1,330
Размер артефактов:  ~58 KB

Компоненты:
├─ Модуль Localization.py        6.9 KB
├─ Переводы (3 языка)            21.3 KB
├─ Документация (3 файла)        23.6 KB
└─ .gitignore обновлен
```

---

## 🎯 TODO (Планы на будущее)

### ✅ Выполнено в этом коммите

- [x] Создать модуль Localization.py
- [x] Реализовать автоопределение языка ОС
- [x] Добавить переводы для 3 языков (en, ru, zh)
- [x] Написать документацию (3 гайда)
- [x] Создать примеры использования
- [x] Оптимизировать производительность

### ⏳ Планы на следующие версии

- [ ] Добавить поддержку еще 4 языков (de, fr, es, ja)
- [ ] Создать UI для выбора языка
- [ ] Реализовать плюрализацию (1 file vs 2 files)
- [ ] Добавить поддержку региональных вариантов (en_US vs en_GB)
- [ ] Создать экспорт/импорт переводов (CSV)
- [ ] Реализовать контекстные переводы
- [ ] Добавить тесты для всех языков
- [ ] Написать документацию для переводчиков
- [ ] Интегрировать в CI/CD pipeline
- [ ] Создать dashboard для управления переводами

---

## 💡 Как участвовать в разработке

### Добавить новый язык

1. Копировать `python/PipeCAD/AI/locales/en.json`
2. Переименовать в `{language_code}.json` (например, `de.json`)
3. Перевести все значения на нужный язык
4. Обновить таблицу в этом файле
5. Запушить в ветку

### Улучшить существующий перевод

1. Отредактировать нужный JSON файл
2. Протестировать: `python -c "from PipeCAD.AI.Localization import Localization; l10n = Localization('{lang}'); print(l10n._('key'))"`
3. Сделать коммит
4. Запушить

### Добавить новую строку для локализации

1. Определить ключ (например, `feature_new_button`)
2. Добавить во все JSON файлы (en.json, ru.json, zh.json и др.)
3. Обновить код для использования: `l10n._("feature_new_button")`
4. Добавить в документацию (QUICK_REFERENCE.md)

---

## 🐛 Решение проблем

### Проблема: Перевод не загружается

```python
# Проверить что файл существует
import os
path = 'python/PipeCAD/AI/locales/en.json'
print(os.path.isfile(path))

# Проверить что JSON валиден
import json
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"Загружено {len(data)} ключей")
```

### Проблема: Язык не определяется правильно

```python
import locale
print(locale.getdefaultlocale())  # ('ru_RU', 'cp1251') на Windows

# Явно указать язык
from PipeCAD.AI.Localization import Localization
l10n = Localization('ru')  # Вместо auto-detect
```

### Проблема: Ключ не найден

```python
# Fallback - вернётся сам ключ
l10n._("nonexistent_key")  # → "nonexistent_key"

# Проверить наличие ключа
if 'key_name' in l10n.strings:
    print("Ключ найден")
else:
    print("Ключ не найден, нужно добавить в JSON")
```

---

## 📞 Контакты и поддержка

### Документация

- 📚 MULTILINGUAL_GUIDE.md - Архитектура
- 🔧 INTEGRATION_GUIDE.md - Как интегрировать
- 🚀 QUICK_REFERENCE.md - Быстрая справка

### Git информация

```bash
# История ветки
git log --graph --oneline feature/ai-agent-development

# Показать всех авторов
git log --oneline feature/ai-agent-development | wc -l

# Показать последний коммит
git log -1 --format="%H %s %an" feature/ai-agent-development
```

---

## 📄 Лицензия

Этот проект и все его компоненты защищены лицензией PipeCAD.

**Copyright (C) 2026 Wuhan TUHE Tech Co., Ltd.**

---

## 🏆 Версия и статус

```
Версия:      1.0.0-ai-agent (Multilingual Support)
Статус:      ✅ Активная разработка
Дата:        2026-11-24
Коммит:      08b5a7e
```

---

**Последнее обновление:** 2026-11-24  
**Статус:** ✅ Готово к использованию и дальнейшей разработке
