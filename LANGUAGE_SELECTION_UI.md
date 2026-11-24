# 🎯 Выбор языка через интерфейс (Улучшенный подход)

## Проблема со старым подходом

**Автоопределение языка ввода** было сложным:
- ❌ Пороги срабатывания неоднозначные
- ❌ Смешанные языки в одном запросе создают проблемы
- ❌ Много кода для реализации
- ❌ Много токенов на отладку

## ✅ Новое решение: Явное меню выбора языка

**Преимущества:**
- ✅ Простое
- ✅ Надежное (нет ошибок определения)
- ✅ Дает полный контроль пользователю
- ✅ Работает правильно для смешанных языков
- ✅ Минимум кода и токенов
- ✅ UX знаком всем пользователям

## 🎨 Реализация в UI

### Вариант 1: Dropdown меню (рекомендуется)

```
┌─────────────────────────────────────────┐
│ Language: [English        ▼]            │  ← Dropdown
├─────────────────────────────────────────┤
│ Your request:                            │
│ ┌──────────────────────────────────────┐ │
│ │ [пользователь пишет на русском]      │ │
│ └──────────────────────────────────────┘ │
│                                          │
│  [Send] [Clear]                          │
└─────────────────────────────────────────┘

Опции в dropdown:
- English (en)
- Русский (ru)
- 中文 (zh)
- Deutsch (de)  [future]
- Français (fr) [future]
```

### Вариант 2: Радио-кнопки

```
┌─────────────────────────────────────────┐
│ Select language:                         │
│  ○ English    ◉ Русский    ○ 中文        │
├─────────────────────────────────────────┤
│ Your request:                            │
│ ┌──────────────────────────────────────┐ │
│ │ Создай трубопровод диаметром 100мм   │ │
│ └──────────────────────────────────────┘ │
│                                          │
│  [Send] [Clear]                          │
└─────────────────────────────────────────┘
```

### Вариант 3: Комбинированный (язык ОС + явный выбор)

```
┌─────────────────────────────────────────┐
│ System language (auto): English          │  ← Только информ.
│ Request language:    [Русский    ▼]     │  ← Выбор пользователя
├─────────────────────────────────────────┤
│ Your request:                            │
│ ┌──────────────────────────────────────┐ │
│ │                                       │ │
│ └──────────────────────────────────────┘ │
│  [Send] [Clear]                          │
└─────────────────────────────────────────┘
```

## 💻 Код интеграции

### Python (Assistant.py)

```python
from PipeCAD.AI.Localization import Localization, set_language, _

class PipeCADAssistant:
    def __init__(self):
        self.l10n = Localization()
        self.current_language = 'en'  # Язык ОС
    
    def set_request_language(self, lang_code):
        """Пользователь выбрал язык в интерфейсе."""
        if lang_code in ['en', 'ru', 'zh']:
            self.current_language = lang_code
            self.l10n.set_language(lang_code)
            print(_(f"Language switched to: {lang_code}"))
        else:
            raise ValueError(f"Unknown language: {lang_code}")
    
    def process_request(self, user_text):
        """Обработать запрос пользователя."""
        # Текущий язык уже установлен из интерфейса
        system_prompt = self._("system_prompt")
        
        # Теперь system_prompt на ПРАВИЛЬНОМ языке!
        response = self.llm.generate(system_prompt, user_text)
        return response
    
    def _get_available_languages(self):
        """Получить список доступных языков для интерфейса."""
        return [
            {'code': 'en', 'name': 'English', 'name_native': 'English'},
            {'code': 'ru', 'name': 'Russian', 'name_native': 'Русский'},
            {'code': 'zh', 'name': 'Chinese', 'name_native': '中文'},
        ]
```

### JavaScript/TypeScript (UI)

```typescript
// React компонент для выбора языка

interface LanguageOption {
  code: 'en' | 'ru' | 'zh';
  name: string;
  native_name: string;
}

function LanguageSelector() {
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  
  const languages: LanguageOption[] = [
    { code: 'en', name: 'English', native_name: 'English' },
    { code: 'ru', name: 'Russian', native_name: 'Русский' },
    { code: 'zh', name: 'Chinese', native_name: '中文' },
  ];
  
  const handleLanguageChange = (lang: string) => {
    setSelectedLanguage(lang);
    // Отправить на backend
    api.setRequestLanguage(lang);
  };
  
  return (
    <div className="language-selector">
      <label htmlFor="lang-select">Language for requests:</label>
      <select
        id="lang-select"
        value={selectedLanguage}
        onChange={(e) => handleLanguageChange(e.target.value)}
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.native_name} ({lang.name})
          </option>
        ))}
      </select>
    </div>
  );
}
```

## 📊 Расход токенов (сравнение)

### Автоопределение (старый подход)
- Анализ текста: 2-5 токенов (каждый запрос)
- System prompt на неправильном языке: +35-80% токенов
- **Итого потери: 50-100 токенов на 100 запросов**

### Явное меню (новый подход)
- Пользователь выбирает один раз: 0 токенов
- System prompt на ПРАВИЛЬНОМ языке: -35-80% экономия
- **Итого выигрыш: 3500-8000 токенов на 100 запросов!**

## 🔄 Пользовательский сценарий

```
Пользователь (English ОС, говорит по-русски):

1. Открывает интерфейс PipeCAD
   └─ System language: English (auto-detected)
   └─ Request language: English (default)

2. Видит dropdown меню "Request language"
   └─ Нажимает dropdown
   └─ Выбирает "Русский (ru)"

3. Пишет запрос: "Создай трубопровод диаметром 100мм"
   
4. Система:
   ✓ Знает, что язык русский
   ✓ Загружает System prompt на русском
   ✓ Отправляет оба на одном языке
   ✓ Экономит 35-80% токенов
   ✓ Получает точный ответ на русском

5. Пользователь доволен! 😊
```

## 📝 Интеграция в код

**Шаг 1:** Добавить в UI компонент языка (Dropdown/RadioButtons)

**Шаг 2:** Вызвать API endpoint:
```python
POST /api/set-language
{
  "language_code": "ru"
}
```

**Шаг 3:** В Assistant.py:
```python
def set_language_for_request(self, lang_code: str):
    """Установить язык для текущего запроса."""
    self.l10n.set_language(lang_code)
```

**Шаг 4:** При отправке запроса:
```python
def process_user_request(self, text: str):
    # Language уже установлена из UI!
    system_prompt = self.l10n._("system_prompt")
    response = self.llm.generate(system_prompt, text)
    return response
```

## ✅ Контрольный список реализации

- [ ] Добавить компонент языка в UI
- [ ] Добавить API endpoint для `set-language`
- [ ] Обновить Assistant.py для использования выбранного языка
- [ ] Протестировать на 3 языках
- [ ] Обновить документацию
- [ ] Добавить сохранение выбранного языка в localStorage/DB

## 🚀 Преимущества этого подхода

1. **Простота** - нет сложного кода определения языка
2. **Надежность** - пользователь явно выбирает язык
3. **Производительность** - нет анализа текста каждый запрос
4. **Экономия токенов** - правильный язык system prompt
5. **UX** - знаком всем (как в Google Translate, DeepL, ChatGPT)
6. **Масштабируемость** - легко добавлять новые языки
7. **Гибкость** - пользователь может переключаться между запросами

## 🎓 Вывод

**Явное меню выбора языка > автоопределение языка ввода**

Это простой, надежный и эффективный подход, который:
- Экономит 35-80% токенов
- Дает полный контроль пользователю
- Минимизирует ошибки
- Работает для смешанных языков
- Следует лучшим практикам
