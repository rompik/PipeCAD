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

### CAESAR II neutral-file export

`PipeCAD.Design.General.CiiExportDialog.Show()` opens the CII export dialog in
PipeCAD. Select PIPE or BRAN elements and add their branches, then specify the
output file and a JSON settings file. The exporter currently accepts connected
straight `TUBI` elements only. It stops on elbows, fittings, disconnected
segments, duplicate tubing, missing mappings, and invalid settings rather than
silently omitting them. Exact matching endpoints share a node; intersections
inside a segment are not split automatically.

Copy `python/PipeCAD/Design/General/cii_settings.example.json` and replace its
illustrative values with reviewed values for each `Spref.Name` and `Lbore` pair.
The test file is disabled unless the dialog's test-settings checkbox is selected.
The settings specify actual outside diameter and wall thickness, not nominal
bore; temperatures are in Celsius, pressures and moduli in kPa, dimensions in
mm, and densities in kg/m³. Every element matching the same specification and
bore receives the same material and operating values. Set `illustrative` to
`false` only after review.
The output uses the version 10 neutral layout of an example confirmed to import
in CAESAR II 13 or later. Generated files have not yet been verified by an
application round trip: they are import candidates, not calculation-ready
models. No supports, load cases or piping-code-specific allowables are exported.
Verify coordinates, connectivity, dimensions, material and operating data,
restraints and analysis settings in CAESAR II before engineering use.

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
