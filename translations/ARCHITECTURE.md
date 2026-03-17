# Automated Translation System Architecture

```mermaid
graph TB
    subgraph "Source Code"
        A[Python Files<br/>lib/pipecad/*.py] --> B[extract_source.py]
        B --> C[source/ui/pipecad_en.ts<br/>English Source Strings]
    end
    
    subgraph "Configuration"
        D[config/automation.json<br/>API Settings]
        E[config/glossary.json<br/>Technical Terms]
        F[config/language-mapping.json<br/>Language Metadata]
    end
    
    subgraph "Translation Process"
        C --> G[translate_auto.py]
        D --> G
        E --> G
        G --> H{Translation<br/>Service}
        H -->|Google| I[targets/ru/ui/pipecad_ru.ts]
        H -->|DeepL| J[targets/zh/ui/pipecad_zh.ts]
        H -->|Azure| K[targets/de/ui/pipecad_de.ts]
    end
    
    subgraph "Quality Assurance"
        I --> L[validate.py]
        J --> L
        K --> L
        L -->|Check| M[Placeholders %1, {0}]
        L -->|Check| N[HTML Tags]
        L -->|Check| O[Glossary Terms]
        L -->|Check| P[Format Integrity]
    end
    
    subgraph "Review & Status"
        L --> Q[sync_status.py]
        Q --> R[targets/ru/status.json<br/>Progress Metrics]
        I --> S[Qt Linguist<br/>Manual Review]
        S --> T[lrelease<br/>Compile .qm]
        T --> U[Runtime .qm Files]
    end
    
    subgraph "CI/CD Integration"
        L --> V[Pull Request<br/>Validation]
        Q --> W[Status Reports]
        V --> X{Pass?}
        X -->|Yes| Y[Merge]
        X -->|No| Z[Fix Issues]
    end
    
    style C fill:#90EE90
    style G fill:#87CEEB
    style L fill:#FFD700
    style U fill:#FF6B6B
```

## Workflow Steps

### 1️⃣ Extract Source Strings
```bash
python extract_source.py --source ../../lib/pipecad --output ../source/ui/pipecad_en.ts
```
**Output**: `source/ui/pipecad_en.ts` (English source)

### 2️⃣ Automated Translation
```bash
python translate_auto.py --source ../source/ui/pipecad_en.ts --target ru --type ui
```
**Output**: `targets/ru/ui/pipecad_ru.ts` (Russian translation)

### 3️⃣ Validate Quality
```bash
python validate.py --file ../targets/ru/ui/pipecad_ru.ts --type ui
```
**Output**: Validation report with issues/warnings

### 4️⃣ Update Status
```bash
python sync_status.py --all
```
**Output**: `targets/*/status.json` (Translation metrics)

### 5️⃣ Manual Review (Optional)
Open `.ts` file in Qt Linguist, review automated translations

### 6️⃣ Compile for Runtime
```bash
lrelease pipecad_ru.ts -qm pipecad_ru.qm
```
**Output**: `pipecad_ru.qm` (Binary file for runtime)

## Data Flow

```
Source Code → Extract → English .ts → Translate API → Target .ts → Validate → Review → Compile → Runtime
```

## Quality Gates

| Stage | Check | Tool | Result |
|-------|-------|------|--------|
| Extraction | Code parsing | extract_source.py | Source .ts |
| Translation | API call + glossary | translate_auto.py | Target .ts |
| Validation | Format + placeholders | validate.py | Pass/Fail |
| Review | Human check | Qt Linguist | Approved |
| Compilation | Binary generation | lrelease | .qm file |

## File Extensions

- `.ts` - Translation Source (XML, human-readable)
- `.qm` - Qt Message (binary, optimized for runtime)
- `.json` - Configuration and status files
- `.py` - Automation scripts

## Integration Points

### For Developers
- Extract strings after code changes
- Update glossary with new technical terms

### For Translators
- Run automated translation
- Review in Qt Linguist
- Approve translations

### For CI/CD
- Validate on pull requests
- Generate status reports
- Block merge if validation fails

### For Build Pipeline
- Compile .ts to .qm
- Package localized resources
- Deploy language packs
```
