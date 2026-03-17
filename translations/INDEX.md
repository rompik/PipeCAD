# PipeCAD Automated Translation System

## Overview

This is a comprehensive automated translation structure for PipeCAD that supports:

- ✅ Automated translation via Google Translate, DeepL, Azure Translator, or custom systems
- ✅ Source string extraction from Python code
- ✅ Translation status tracking with metadata
- ✅ Quality validation (placeholders, HTML tags, glossary compliance)
- ✅ Technical terminology glossary
- ✅ Translation memory for consistency
- ✅ Support for UI strings (Qt .ts) and documentation (Markdown)
- ✅ Multi-language support with easy addition of new languages
- ✅ CI/CD integration ready

## Quick Links

- **[Quick Start Guide](QUICKSTART.md)** - Get started in 5 minutes
- **[Full Documentation](README.md)** - Complete translation workflow guide
- **[Configuration Files](config/)** - Automation settings and glossary
- **[Automation Scripts](scripts/)** - Python tools for translation workflow

## Current Status

| Language | Code | UI Strings | Documentation | Status |
|----------|------|------------|---------------|---------|
| English (Source) | en | ✓ Source | ✓ Source | Active |
| Russian | ru | 🔄 Ready | 🔄 Ready | Ready |
| Chinese (Simplified) | zh | 🔄 Ready | 🔄 Ready | Ready |
| German | de | 📋 Planned | 📋 Planned | Planned |
| French | fr | 📋 Planned | 📋 Planned | Planned |
| Japanese | ja | 📋 Planned | 📋 Planned | Planned |
| Spanish | es | 📋 Planned | 📋 Planned | Planned |

## Directory Structure

```
translations/
├── INDEX.md                 # This file
├── README.md               # Full documentation
├── QUICKSTART.md           # Quick start guide
│
├── source/                 # Source language (English)
│   ├── ui/                # Source UI strings (.ts files)
│   └── docs/              # Source documentation
│
├── targets/               # Target languages
│   ├── ru/               # Russian
│   │   ├── ui/          # Translated UI strings
│   │   ├── docs/        # Translated documentation
│   │   └── status.json  # Translation status
│   └── zh/              # Chinese
│       ├── ui/
│       ├── docs/
│       └── status.json
│
├── config/               # Configuration files
│   ├── automation.json  # Automation settings
│   ├── glossary.json    # Technical terms
│   └── language-mapping.json  # Language metadata
│
├── scripts/             # Automation tools
│   ├── extract_source.py    # Extract strings from code
│   ├── translate_auto.py    # Automated translation
│   ├── validate.py          # Quality validation
│   └── sync_status.py       # Status tracking
│
├── phrase_books/        # Qt phrase books (legacy)
└── qt_messages/         # Compiled messages (legacy)
```

## Workflows

### 1. Extract Source Strings (Devs)

When source code changes, extract new translatable strings:

```bash
cd scripts
python extract_source.py --source ../../lib/pipecad --output ../source/ui/pipecad_en.ts
```

### 2. Automated Translation (Translators)

Translate to target language with ONE command:

```bash
python translate_auto.py --source ../source/ui/pipecad_en.ts --target ru --type ui
```

### 3. Quality Check (QA)

Validate translations for common issues:

```bash
python validate.py --file ../targets/ru/ui/pipecad_ru.ts --type ui
```

### 4. Manual Review (Optional but Recommended)

Open `.ts` file in Qt Linguist, review automated translations, mark as finished.

### 5. Status Update (Automated)

Track translation progress:

```bash
python sync_status.py --all
```

### 6. Compile for Runtime (Build)

Generate binary `.qm` files:

```bash
lrelease pipecad_ru.ts -qm pipecad_ru.qm
```

## Key Features

### 🤖 Fully Automated
- One command to translate entire applications
- Automatic string extraction from source code
- Batch processing for multiple languages

### 📊 Status Tracking
- Real-time translation completeness metrics
- Quality scores and review status
- Per-language status reports

### 🔍 Quality Assurance
- Placeholder validation (e.g., %1, {0})
- HTML tag preservation
- Glossary enforcement
- Format validation

### 📚 Glossary Management
- Technical term consistency
- Do-not-translate terms (product names)
- Multi-language term database

### 🌍 Multi-Language Support
- Easy addition of new languages
- Supports 50+ languages via translation APIs
- Locale and format support

### 🔗 CI/CD Integration
- Validation hooks for pull requests
- Automated status reports
- Translation completeness gates

## Getting Started

1. **Read the Quick Start**: [QUICKSTART.md](QUICKSTART.md)
2. **Configure your API**: Edit [config/automation.json](config/automation.json)
3. **Run your first translation**: Follow the workflow above
4. **Review and improvise**: Manual review in Qt Linguist

## Translation Service Options

| Service | API | Cost | Quality | Speed |
|---------|-----|------|---------|-------|
| Google Cloud Translation | ✅ | Pay per char | Good | Fast |
| DeepL | ✅ | Subscription | Excellent | Medium |
| Azure Translator | ✅ | Pay per char | Good | Fast |
| Custom MT | ✅ | Self-hosted | Variable | Variable |

Configure in [config/automation.json](config/automation.json).

## Best Practices

1. ✅ Always update English source first
2. ✅ Use automated translation as a draft
3. ✅ Always review automated output
4. ✅ Run validation before committing
5. ✅ Keep glossary updated with new terms
6. ✅ Track status regularly

## Support

For questions or issues:
- Check [README.md](README.md) for detailed docs
- Review [QUICKSTART.md](QUICKSTART.md) for common tasks
- Check script help: `python script_name.py --help`

## Migration from Old Structure

The old translation files are preserved in:
- `phrase_books/` - Qt phrase books
- `qt_messages/` - Compiled messages

To migrate:
1. Run extract to create new source file
2. Copy old translations to new structure
3. Run validation to check quality
4. Update and approve

---

**Version**: 1.0  
**Last Updated**: 2026-03-10  
**Status**: Production Ready
