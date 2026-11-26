## PipeCAD - Plant Piping Design Software.

| PipeCAD | **Free Edition** | **Professional Edition** |
| :--- | :--- | :--- |
| Import Catalogue from Excel | :heavy_check_mark: | :heavy_check_mark:   |
| Design Modeling | :heavy_check_mark: | :heavy_check_mark:   |
| Export Piping PCF | :heavy_check_mark: | :heavy_check_mark:   |
| Export Review RVM | :x: | :heavy_check_mark:   |
| Export MTO | :warning: BASIC | :heavy_check_mark: |
| Piping Isometrics Drawing | :warning: BASIC | :heavy_check_mark: |
| Piping Arrangement Drawing | :warning: BASIC | :heavy_check_mark: |
| Nozzle Orientation Drawing | :warning: BASIC | :heavy_check_mark: |

PipeCAD Free Edition is **FREE** to personal, commercial or enterprise use.

PipeCAD Professional Edition is **NOT FREE**, you can send email consult to buy it.

### Python Plugins
PipeCAD provide customization by Python. The python plugins locate in the python/PipeCAD folder.
The Python plugins are open source with **MIT** license.

### Translations

After Python files in `python/PipeCAD` are pushed, the translation workflow updates
`translations/*.ts` and compiles `i18n/*.qm`. If there are changes, it opens or
updates a pull request targeting the source branch. New strings still need to be
translated manually; the workflow extracts strings but does not translate them.
After editing a `.ts` file, compile it with the same Qt version as the workflow,
for example `pyside6-lrelease translations\ru_RU.ts -qm i18n\ru_RU.qm`, and
include the updated `.qm` file before merging.
For the workflow to open pull requests, enable **Allow GitHub Actions to create
and approve pull requests** in the repository's Actions settings. Branch
protection rules may also require the generated pull request to be reviewed.

CII export documentation: [feature_dev/CII.md](feature_dev/CII.md).

## PipeCAD Sample

Spooler project:

![PipeCAD Spooler](docs/images/PipeCAD_Spooler.png)

Stabilizer project:

![PipeCAD Spooler](docs/images/PipeCAD_Stabilizer.png)

## Piping Isometrics

PipeCAD generate piping isometric drawing by IsoAlgo:

![PipeCAD ISO](docs/images/PipeCAD-ISO-03.png)
![PipeCAD ISO](docs/images/PipeCAD-ISO-04.png)

## PipeCAD User Guide

How to use PipeCAD? Please refer to the [PipeCAD User Guide](docs/user_guide_en.md). [中文版](docs/user_guide_zh.md)

## PipeCAD Dev Guide

If you want to develop plugins for PipeCAD, or want to use AI to develop PipeCAD plugins, please refer to AI agent skill  `pipecad-dev-python`. [中文版](skills/pipecad-dev-python/SKILL.md)
