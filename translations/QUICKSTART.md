# PipeCAD Translation Quick Start Guide

## Prerequisites

1. Python 3.7 or higher
2. Translation API access (Google Cloud Translation, DeepL, or Azure Translator)
3. Qt Linguist (optional, for manual review)

## Setup

### 1. Configure Translation Service

Edit `config/automation.json` and set your translation service credentials:

```json
{
  "translation_service": {
    "provider": "google",
    "api_key_env": "TRANSLATION_API_KEY"
  }
}
```

Set the API key as environment variable:
```bash
export TRANSLATION_API_KEY="your-api-key-here"
```

### 2. Update Glossary

Edit `config/glossary.json` to add product-specific terms:

```json
{
  "terms": [
    {
      "source": "MyProduct",
      "do_not_translate": true,
      "category": "product_name"
    }
  ]
}
```

## Workflows

### Extract Source Strings from Code

Extract translatable strings from Python source:

```bash
cd translations/scripts
python extract_source.py --source ../../lib/pipecad --output ../source/ui/pipecad_en.ts
```

### Translate to New Language

Translate UI strings to Russian:

```bash
python translate_auto.py --source ../source/ui/pipecad_en.ts --target ru --type ui
```

Translate documentation:

```bash
python translate_auto.py --source ../../docs/en/index.md --target ru --type docs
```

### Validate Translations

Check for formatting and quality issues:

```bash
python validate.py --file ../targets/ru/ui/pipecad_ru.ts --type ui
```

### Update Status

Sync translation status for all languages:

```bash
python sync_status.py --all
```

Check status for specific language:

```bash
python sync_status.py --language ru
```

## Manual Review Workflow

1. **Automated Translation**: Run `translate_auto.py` to generate draft translations
2. **Open in Qt Linguist**: Open the `.ts` file in Qt Linguist for review
3. **Edit Translations**: Review and edit automated translations
4. **Mark as Complete**: Mark strings as finished in Qt Linguist
5. **Compile**: Generate `.qm` file: `lrelease pipecad_ru.ts`
6. **Update Status**: Run `sync_status.py` to update metrics

## Adding a New Language

1. **Create Target Directory**:
   ```bash
   mkdir -p targets/de/ui
   mkdir -p targets/de/docs
   ```

2. **Initialize Status**:
   ```bash
   python sync_status.py --language de
   ```

3. **Add to Configuration**:
   Edit `config/automation.json` and add language to `target_languages`:
   ```json
   {
     "code": "de",
     "name": "German",
     "locale": "de_DE",
     "enabled": true,
     "auto_translate": true,
     "requires_review": true
   }
   ```

4. **Run Translation**:
   ```bash
   python translate_auto.py --source ../source/ui/pipecad_en.ts --target de --type ui
   ```

## Directory Overview

```
translations/
├── source/          # English source strings (single source of truth)
├── targets/         # Translated strings for each language
├── config/          # Configuration and glossary
└── scripts/         # Automation scripts
```

## Common Issues

### Issue: "No lupdate tool found"
**Solution**: Install PySide2 or PySide6:
```bash
pip install PySide6
```

### Issue: "Translation API key not set"
**Solution**: Set environment variable:
```bash
export TRANSLATION_API_KEY="your-key"
```

### Issue: "Placeholder mismatch"
**Solution**: Review and fix placeholders in manual review. Automated translation sometimes reorders them.

## Best Practices

1. **Always update English source first**, then propagate to other languages
2. **Run validation** before committing translations
3. **Review automated translations** - they are a starting point, not final
4. **Use glossary** for technical terms
5. **Keep status updated** - run sync_status.py regularly

## Integration with CI/CD

Add to your CI pipeline:

```yaml
translation-check:
  script:
    - cd translations/scripts
    - python sync_status.py --all
    - python validate.py --file ../targets/ru/ui/pipecad_ru.ts --type ui
```

## Next Steps

- Review [README.md](../README.md) for detailed documentation
- Configure your preferred translation service
- Update glossary with product-specific terms
- Set up CI/CD integration for automatic validation
