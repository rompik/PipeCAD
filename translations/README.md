# PipeCAD Translation Structure

## Overview
This directory contains all translation resources for PipeCAD, organized to support automated translation workflows.

## Directory Structure

```
translations/
├── source/                      # Source language (English)
│   ├── ui/                     # UI strings (Qt .ts files)
│   │   └── pipecad_en.ts      # Source UI strings
│   ├── docs/                   # Documentation source
│   │   └── *.md               # Markdown documentation files
│   └── metadata.json           # Source string metadata
├── targets/                     # Target languages
│   ├── ru/                     # Russian
│   │   ├── ui/
│   │   │   └── pipecad_ru.ts
│   │   ├── docs/
│   │   └── status.json         # Translation status tracking
│   ├── zh/                     # Chinese
│   │   ├── ui/
│   │   │   └── pipecad_zh.ts
│   │   ├── docs/
│   │   └── status.json
│   ├── de/                     # German (example)
│   │   ├── ui/
│   │   ├── docs/
│   │   └── status.json
│   └── fr/                     # French (example)
│       ├── ui/
│       ├── docs/
│       └── status.json
├── config/                      # Translation configuration
│   ├── automation.json         # Automation settings
│   ├── glossary.json          # Technical terms glossary
│   └── language-mapping.json   # Source to target mappings
├── scripts/                     # Automation scripts
│   ├── extract_source.py      # Extract strings from source code
│   ├── translate_auto.py      # Run automated translation
│   ├── validate.py            # Validate translations
│   └── sync_status.py         # Update translation status
├── phrase_books/               # Qt phrase books (legacy)
└── qt_messages/                # Compiled Qt messages (legacy)
```

## Automated Translation Workflow

### 1. Extract Source Strings
```bash
python scripts/extract_source.py --source ../lib/pipecad --output source/ui/pipecad_en.ts
```

### 2. Translate Automatically
```bash
python scripts/translate_auto.py --source source/ui/pipecad_en.ts --target ru --output targets/ru/ui/pipecad_ru.ts
```

### 3. Validate Translations
```bash
python scripts/validate.py --target targets/ru/ui/pipecad_ru.ts
```

### 4. Update Status
```bash
python scripts/sync_status.py --language ru
```

## Translation Status Tracking

Each target language has a `status.json` file that tracks:
- Total strings count
- Translated strings count
- Unfinished/fuzzy strings count
- Last update timestamp
- Translation quality score
- Review status

## Supported Translation Services

The automation system supports:
- Google Cloud Translation API
- DeepL API
- Microsoft Azure Translator
- Custom MT systems

Configure in `config/automation.json`.

## Glossary Management

Technical terms are maintained in `config/glossary.json` to ensure consistency:
- Product names (e.g., "PipeCAD")
- Technical terms (e.g., "piping", "isometric")
- UI elements (e.g., "toolbar", "ribbon")

## Quality Assurance

Automated checks include:
- String format validation (placeholders, HTML tags)
- Length limits (UI space constraints)
- Glossary consistency
- Encoding validation
- Qt .ts format validation

## Manual Review Process

1. Automated translation generates draft translations
2. Translator reviews and edits in Qt Linguist
3. Quality checker validates technical accuracy
4. Status updated to "reviewed"
5. Compiled .qm file generated for runtime

## Adding a New Language

1. Create target language folder: `targets/<lang_code>/`
2. Add language entry in `config/language-mapping.json`
3. Initialize status: `python scripts/sync_status.py --language <lang_code> --init`
4. Run automated translation
5. Review and validate

## File Formats

- **UI Strings**: Qt .ts (XML) format
- **Documentation**: Markdown (.md) format
- **Metadata**: JSON format
- **Compiled UI**: Qt .qm (binary) format

## Translation Memory

Translation memory is maintained in `config/translation-memory.json` to:
- Reuse previous translations
- Maintain consistency across versions
- Speed up incremental updates

## Best Practices

1. **Always update source first** - Modify English strings, then propagate to targets
2. **Use glossary** - Technical terms should be consistent
3. **Validate before commit** - Run validation scripts
4. **Review automated output** - Machine translation is a starting point
5. **Update status metadata** - Keep status.json current

## Integration with CI/CD

Automated checks run on pull requests:
- Source string extraction
- Translation completeness check
- Format validation
- Status report generation

## Contact

For translation issues or questions, contact the localization team.
