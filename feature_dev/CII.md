# CAESAR II neutral-file export

`PipeCAD.Design.General.CiiExportDialog.Show()` opens the CII export dialog in
PipeCAD. Select PIPE or BRAN elements and add their branches, then specify the
output file, JSON settings file, attribute mapping file and writer-layout version
(10 or 11). The exporter currently accepts straight
`TUBI` elements only. It stops on elbows, fittings, duplicate tubing, missing
mappings, and invalid settings rather than silently omitting them. Exact
matching endpoints share a node; intersections inside a segment are not split
automatically. Disconnected groups are given separate coordinate anchors.

Copy [cii_settings.example.json](../python/PipeCAD/Design/General/cii_settings.example.json)
and replace its illustrative values with reviewed values for each `Spref.Name`
and `Lbore` pair. The test file is disabled unless the dialog's test-settings
checkbox is selected. The settings specify actual outside diameter and wall
thickness, not nominal bore; temperatures are in Celsius, pressures and
moduli in kPa, dimensions in mm, and densities in kg/m³. Every element matching
the same specification and bore receives the same material and operating
values. Set `illustrative` to `false` only after review.

The default layout 10 is based on an example confirmed to import in CAESAR II 13
or later. Layout 11 uses the additional line-number and colour/visibility
records observed in the supplied version 11 examples. The choice controls the
generating-version field and element record layout; it does not select a CAESAR II
application version. Generated files for either layout have not been verified by
an application round trip: they are import candidates, not calculation-ready
models. No supports, load cases or piping-code-specific allowables are exported.
Verify coordinates, connectivity, dimensions, material and operating data,
restraints and analysis settings in CAESAR II before engineering use.

## Format references and limitations

- [PipeCAD-to-CII attribute mapping](../data/cii_attribute_mapping.json): implemented
  fields and unverified candidates. This file must be available to the exporter;
  select another path in the dialog if it is installed separately.
- [CAESAR II 13 neutral-file documentation](https://docs.hexagonppm.com/r/en-US/CAESAR-II-Users-Guide/Version-13/337037)
- [CAESAR II 15 neutral-file documentation](https://docs.hexagonppm.com/r/en-US/CAESAR-II-Users-Guide/15/337037)
- [CAESAR II 15.1 basic element data](https://docs.hexagonppm.com/r/en-US/CAESAR-II-Users-Guide/15.1/337040)
- [CAESAR II 15.1 input export options](https://docs.hexagonppm.com/r/en-US/CAESAR-II-Users-Guide/15.1/425497)

The version 13 specification describes element name, line number and line
colour/visibility records that are not emitted by this version 10-layout
exporter. Its BEND section says 13 values are used but lists 14. A version 13
reference export and an import check are needed before implementing and
validating that layout or bend data.

The mapping's `version` is the earliest writer layout in the supplied examples
where the supported field was observed, not a proven historical minimum. A null
version denotes an unknown layout. `documented_caesar_ii_version` identifies the
manual describing the CII target, not a verified PipeCAD mapping. The exporter
checks required mappings and their versions and uses each implemented property's
`settings.*` source to select a value; specification-level values come from the
matched entry, while ambient temperature comes from the settings root. Source
keys must have the expected unit suffix. Geometry mappings and conversion rules
are fixed in code; changing their descriptions does not change conversions.
Candidate mappings cannot enable additional component types.

## Additional reference check

The supplied `50-B-321_PSI.cii` declares neutral interface 5.0 and generating
version 11.0. Its 16 elements reference five bends, five rigid elements, two
restraint blocks and one reducer. Each bend record contains 14 values; the
reducer record contains five values, whereas the version 13 documentation
describes ten. These observations alone do not establish the version 13 layout.

For the five elements without auxiliary references, synthetic isolated tubing
reproduced the reference node numbers, deltas and four dimensions. The 22 unit
factors and 24 labels also matched. Other engineering settings were illustrative;
the original PipeCAD model, full connectivity and import into CAESAR II were not
validated. The current exporter cannot reproduce the complete reference file.
