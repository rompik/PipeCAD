"""
Пример интеграции многоязычности в PipeCAD AI Assistant

Этот файл показывает как модифицировать Assistant.py для поддержки локализации.
"""

# =====================================================================
# ШАГИ ИНТЕГРАЦИИ
# =====================================================================

"""
ШАГ 1: Импорт локализации в начало Assistant.py
"""
# Добавить после других импортов:
# from PipeCAD.AI.Localization import Localization, _


"""
ШАГ 2: Инициализировать локализацию при создании AIAssistantCore
"""
# В методе __init__ класса AIAssistantCore:
class AIAssistantCore:
    def __init__(self, config=None, language=None):
        self.config = config or self._load_config()
        self.l10n = Localization(language)  # <-- Добавить эту строку
        # ... остальной код ...


"""
ШАГ 3: Заменить жесткие строки на вызовы локализации
"""

# БЫЛО (жесткокодировано):
# raise IOError('未找到 MetaData.json（试过 %d 个位置），'
#               '请设置 PIPECAD_HOME 指向含 data/MetaData.json 的目录' % len(probes))

# СТАЛО (локализовано):
# raise IOError(self.l10n._("error_metadata_not_found", count=len(probes)))


"""
ШАГ 4: Обновить build_system_prompt() для использования локализации
"""
def build_system_prompt(schema_text, l10n, skill_text=''):
    """Построить системный промпт на языке пользователя."""
    prompt = l10n._("system_prompt") + '\n# Schema for this request\n' + (
        schema_text or l10n._("schema_missing"))
    if skill_text:
        prompt += ('\n\n# Official skills excerpt\n' + skill_text)
    return prompt


"""
ШАГ 5: Обновить build_user_prompt()
"""
def build_user_prompt(user_text, model_context, l10n, extra=''):
    """Построить пользовательский промпт с локализацией."""
    parts = [l10n._("user_request") + ':\n%s' % user_text.strip()]
    if model_context:
        parts.append(l10n._("current_model_state") + ':\n%s' % model_context)
    if extra:
        parts.append(extra)
    return '\n\n'.join(parts)


"""
ШАГ 6: Обновить сообщения об ошибках
"""
# Во всем коде заменить:
#   raise IOError('...')          →  raise IOError(self.l10n._("key"))
#   raise LLMError('...')         →  raise LLMError(self.l10n._("key"))
#   print('...')                  →  print(self.l10n._("key"))
#   raise RuntimeError('...')     →  raise RuntimeError(self.l10n._("key"))


"""
ШАГ 7: Поддержка для Qt диалогов (EquipmentDialog)
"""
class EquipmentDialog(QDialog):
    def __init__(self, parent=None, language=None):
        QDialog.__init__(self, parent)
        self.l10n = Localization(language)  # <-- Добавить
        self.setupUi()
    
    def setupUi(self):
        self.setWindowTitle(self.l10n._("ui_create_equipment"))  # <-- Вместо "Create Equipment"
        
        # ... остальной код ...
        
        self.labelName = QLabel(self.l10n._("ui_name"))  # <-- Вместо "Name"
        self.labelPx = QLabel(self.l10n._("ui_east"))    # <-- Вместо "East"
        self.labelPy = QLabel(self.l10n._("ui_north"))   # <-- Вместо "North"
        self.labelPz = QLabel(self.l10n._("ui_up"))      # <-- Вместо "Up"


"""
ШАГ 8: Добавить метод для смены языка в runtime
"""
# В класс AIAssistantCore добавить:
def set_language(self, language_code):
    """Изменить язык на лету."""
    self.l10n.set_language(language_code)


"""
ШАГ 9: Поддержка в главном окне (если есть UI)
"""
# В главном окне добавить:
# def on_language_changed(self, new_language):
#     """Обработчик смены языка."""
#     core.set_language(new_language)
#     # Пересоздать диалоги с новым языком
#     dialog.close()
#     dialog = EquipmentDialog(self, language=new_language)
#     dialog.show()


# =====================================================================
# ПОЛНЫЙ ПРИМЕР: Как использовать
# =====================================================================

"""
# Инициализация с автоопределением языка:
from PipeCAD.AI import Assistant
from PipeCAD.AI.Localization import Localization

# Создать помощника с автоопределением языка ОС
core = Assistant.create_core()

# Или явно указать язык:
l10n = Localization('ru')  # Русский
core = Assistant.create_core(language='ru')

# Выполнить команду (модель ответит на языке пользователя):
turn = core.plan('Создать трубопровод DN200 P-101')
if turn.ok:
    result = core.execute(turn.script)
    print(result.summary())  # Сообщения могут быть на русском

# Смена языка в runtime:
core.set_language('en')
turn2 = core.plan('Create a DN100 pipe named P-102')

# Получить текущий язык:
current_lang = core.l10n.get_language()
print(f"Current language: {current_lang}")
"""


# =====================================================================
# ПОДДЕРЖИВАЕМЫЕ ЯЗЫКИ И КОДЫ
# =====================================================================

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'zh': '中文 (Chinese)',
    'ru': 'Русский (Russian)',
    'de': 'Deutsch (German)',
    'fr': 'Français (French)',
    'es': 'Español (Spanish)',
    'ja': '日本語 (Japanese)',
}

# Добавить комбобокс в UI для выбора языка:
# self.languageCombo = QComboBox()
# for code, name in SUPPORTED_LANGUAGES.items():
#     self.languageCombo.addItem(name, code)
# self.languageCombo.currentIndexChanged.connect(self.on_language_changed)


# =====================================================================
# ЭКСПОРТ ВСЕХ СТРОК В CSV (для переводчиков)
# =====================================================================

"""
import json
import csv

def export_strings_to_csv(language_file, output_csv):
    '''Экспортировать строки в CSV для переводов.'''
    with open(language_file, 'r', encoding='utf-8') as f:
        strings = json.load(f)
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Key', 'Value', 'Context'])
        
        for key, value in strings.items():
            if key != 'meta':
                # Определить контекст по префиксу ключа
                if key.startswith('error_'):
                    context = 'Error message'
                elif key.startswith('ui_'):
                    context = 'UI text'
                elif key.startswith('log_'):
                    context = 'Log message'
                elif key.startswith('help_'):
                    context = 'Help text'
                elif key.startswith('hint_'):
                    context = 'Type hint'
                else:
                    context = 'General'
                
                writer.writerow([key, value, context])

# Использование:
# export_strings_to_csv('locales/en.json', 'translations_for_review.csv')
"""


# =====================================================================
# ПРОВЕРКА: Какие строки нужно добавить в локализацию
# =====================================================================

"""
grep_strings_in_code = r'''
Места в Assistant.py которые нужно локализировать:

1. Строки вроде "未找到 MetaData.json"
   → Поискать: grep -n "raise IOError\|raise LLMError\|raise RuntimeError"
   
2. Строки в QMessageBox и диалогах
   → Поискать: grep -n "QMessageBox.warning\|QMessageBox.information\|QMessageBox.critical"
   
3. Комментарии и docstring
   → Поискать: grep -n "^\\s*#.*[^a-z]" (комментарии не на английском)
   
4. Строки в SYSTEM_PROMPT и PROMPT
   → Поискать: grep -n "PROMPT = " или "'''你是"
   
5. CN_HINTS и языковые словари
   → Поискать: grep -n "CN_HINTS\|'罐'\|'管'"
'''
"""
