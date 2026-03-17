# Migration Guide: Old → New Translation Structure

## Overview

This guide helps you migrate from the current simple translation structure to the new automated translation system.

## Current Structure (Before)

```
translations/
├── pipecad_ru.ts          # Russian UI strings
├── pipecad_zh.ts          # Chinese UI strings
├── phrase_books/
│   └── pipecad_ru.qph
└── qt_messages/
    └── pipecad_ru.qm
```

## New Structure (After)

```
translations/
├── source/                 # Source strings
│   └── ui/
│       └── pipecad_en.ts  # NEW: English source
├── targets/               # Target languages
│   ├── ru/
│   │   ├── ui/
│   │   │   └── pipecad_ru.ts  # Migrated
│   │   └── status.json        # NEW: Metrics
│   └── zh/
│       ├── ui/
│       │   └── pipecad_zh.ts  # Migrated
│       └── status.json
├── config/                # NEW: Configuration
│   ├── automation.json
│   ├── glossary.json
│   └── language-mapping.json
└── scripts/               # NEW: Automation tools
    ├── extract_source.py
    ├── translate_auto.py
    ├── validate.py
    └── sync_status.py
```

## Migration Steps

### Step 1: Backup Current Files

```powershell
# Windows
cd C:\PipeCAD_Devs
mkdir translations_backup
Copy-Item -Path translations\*.ts -Destination translations_backup\
Copy-Item -Path translations\phrase_books\* -Destination translations_backup\phrase_books\ -Recurse
Copy-Item -Path translations\qt_messages\* -Destination translations_backup\qt_messages\ -Recurse
```

```bash
# Linux/Mac
cd /path/to/PipeCAD_Devs
mkdir translations_backup
cp translations/*.ts translations_backup/
cp -r translations/phrase_books translations_backup/
cp -r translations/qt_messages translations_backup/
```

### Step 2: Extract Source Strings

Create the English source file from your Python code:

```bash
cd translations/scripts
python extract_source.py --source ../../lib/pipecad --output ../source/ui/pipecad_en.ts
```

This generates: `translations/source/ui/pipecad_en.ts`

### Step 3: Move Existing Translations

Move Russian translations:

```powershell
# Windows
Move-Item translations\pipecad_ru.ts translations\targets\ru\ui\pipecad_ru.ts
```

```bash
# Linux/Mac
mv translations/pipecad_ru.ts translations/targets/ru/ui/pipecad_ru.ts
```

Move Chinese translations:

```powershell
# Windows
Move-Item translations\pipecad_zh.ts translations\targets\zh\ui\pipecad_zh.ts
```

```bash
# Linux/Mac
mv translations/pipecad_zh.ts translations/targets/zh/ui/pipecad_zh.ts
```

### Step 4: Validate Migrated Files

Check if moved files are valid:

```bash
cd translations/scripts
python validate.py --file ../targets/ru/ui/pipecad_ru.ts --type ui
python validate.py --file ../targets/zh/ui/pipecad_zh.ts --type ui
```

Fix any validation errors reported.

### Step 5: Update Status Metadata

Generate status files for all languages:

```bash
python sync_status.py --all
```

This creates:
- `translations/targets/ru/status.json`
- `translations/targets/zh/status.json`

### Step 6: Configure Translation Service

Edit `translations/config/automation.json`:

1. Set your translation service provider (google, deepl, azure)
2. Configure API credentials
3. Enable/disable target languages

Example:
```json
{
  "translation_service": {
    "provider": "google",
    "api_key_env": "TRANSLATION_API_KEY"
  }
}
```

Set environment variable:
```bash
export TRANSLATION_API_KEY="your-api-key-here"
```

### Step 7: Update Build Scripts

Update your build/packaging scripts to use new paths:

**Before:**
```python
ts_files = ["translations/pipecad_ru.ts", "translations/pipecad_zh.ts"]
```

**After:**
```python
ts_files = [
    "translations/targets/ru/ui/pipecad_ru.ts",
    "translations/targets/zh/ui/pipecad_zh.ts"
]
```

### Step 8: Compile .qm Files

Compile translations to binary format:

```bash
cd translations/targets/ru/ui
lrelease pipecad_ru.ts -qm pipecad_ru.qm

cd ../../../targets/zh/ui
lrelease pipecad_zh.ts -qm pipecad_zh.qm
```

### Step 9: Test Runtime Loading

Update your application to load .qm files from new locations:

**Before:**
```python
translator = QTranslator()
translator.load("translations/qt_messages/pipecad_ru.qm")
```

**After:**
```python
translator = QTranslator()
translator.load("translations/targets/ru/ui/pipecad_ru.qm")
```

### Step 10: Update .gitignore

Add to `.gitignore`:

```gitignore
# Translation binaries (generated)
translations/targets/**/ui/*.qm

# Translation working files
translations/source/metadata.json
translations/config/translation-memory.json

# Optional: Keep compiled messages out of version control
translations/qt_messages/*.qm
```

## Post-Migration Verification

### Check 1: All Files Migrated

```bash
# Should list all .ts files in new locations
find translations/targets -name "*.ts"
```

Expected output:
```
translations/targets/ru/ui/pipecad_ru.ts
translations/targets/zh/ui/pipecad_zh.ts
```

### Check 2: Status Updated

```bash
cat translations/targets/ru/status.json
cat translations/targets/zh/status.json
```

Should show translation statistics.

### Check 3: Validation Passes

```bash
cd translations/scripts
python validate.py --file ../targets/ru/ui/pipecad_ru.ts --type ui
python validate.py --file ../targets/zh/ui/pipecad_zh.ts --type ui
```

Should report no critical errors.

### Check 4: Application Loads Translations

Run PipeCAD and switch language to verify translations load correctly.

## Rollback Procedure

If migration fails, restore from backup:

```powershell
# Windows
Copy-Item -Path translations_backup\* -Destination translations\ -Recurse -Force
```

```bash
# Linux/Mac
cp -r translations_backup/* translations/
```

## Benefits After Migration

✅ **Automated translation** - Add new languages with one command  
✅ **Quality validation** - Catch errors before deployment  
✅ **Status tracking** - Know translation progress at a glance  
✅ **Glossary enforcement** - Consistent technical terms  
✅ **CI/CD ready** - Integrate with build pipeline  
✅ **Scalable** - Easy to add 10+ languages  

## Backward Compatibility

To maintain backward compatibility during transition:

1. **Keep old files** in `phrase_books/` and `qt_messages/` temporarily
2. **Update loading code** to try new paths first, fall back to old
3. **Remove old structure** after thorough testing

Example fallback code:
```python
translator = QTranslator()
# Try new location first
if not translator.load("translations/targets/ru/ui/pipecad_ru.qm"):
    # Fall back to old location
    translator.load("translations/qt_messages/pipecad_ru.qm")
```

## Timeline Recommendation

| Week | Activities |
|------|-----------|
| 1 | Backup, extract source, validate current files |
| 2 | Move files, configure automation, test locally |
| 3 | Update build scripts, test CI/CD integration |
| 4 | Deploy to staging, verify all languages work |
| 5 | Production deployment |
| 6 | Remove old structure, update documentation |

## Troubleshooting

### Issue: "Source file has new strings, target is missing them"
**Solution**: Run translation update:
```bash
python translate_auto.py --source ../source/ui/pipecad_en.ts --target ru --type ui
```

### Issue: "Validation fails with placeholder errors"
**Solution**: Review translations in Qt Linguist, fix placeholder mismatches manually

### Issue: "API key not working"
**Solution**: 
1. Verify API key is correct
2. Check environment variable is set
3. Verify API has required permissions

### Issue: "Compiled .qm file not loading"
**Solution**: 
1. Check file path in code
2. Verify .qm file was compiled successfully
3. Check file permissions

## Next Steps

After successful migration:

1. **Add new languages**: Use `translate_auto.py` to add German, French, etc.
2. **Set up CI/CD**: Add validation to pull request pipeline
3. **Train team**: Share [QUICKSTART.md](QUICKSTART.md) with translators
4. **Monitor status**: Run `sync_status.py` regularly

## Support

For migration issues:
- Check [README.md](README.md) for detailed documentation
- Review [QUICKSTART.md](QUICKSTART.md) for workflows
- Run `python script_name.py --help` for script usage
