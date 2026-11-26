"""Export straight PipeCAD tubing as a CAESAR II neutral-file candidate."""

import json
import math
from pathlib import Path


_AUXILIARY_SECTIONS = (
    "NODENAME", "BEND", "RIGID", "EXPJT", "RESTRANT", "DISPLMNT",
    "FORCMNT", "UNIFORM", "WIND", "OFFSETS", "ALLOWBLS", "SIF&TEES",
    "REDUCERS", "FLANGES", "EQUIPMNT",
)

# CAESAR's SI (mm) conversion factors and labels, in neutral-file order.
_UNIT_FACTORS = (
    25.4, 4.44822, 0.453592, 0.112985, 0.112985, 6.89476,
    0.555556, -17.7778, 6.89476, 6.89476, 0.02768, 0.02768,
    0.02768, 1.75127, 0.112985, 1.75127, 1.0, 6.89476,
    0.0254, 25.4, 25.4, 25.4,
)
_UNIT_LABELS = (
    "SI (mm)", "on", "mm.", "N.", "Kg.", "N.m.", "N.m..", "KPa",
    "C", "C", "KPa", "KPa", "kg.cu.cm.", "kg.cu.cm.", "kg.cu.cm.",
    "N./cm.", "N.m./deg", "N./cm.", "g's", "Kpa", "m.", "mm.", "mm.",
    "mm.",
)

DEFAULT_MAPPING_FILE = Path(__file__).resolve().parents[4] / "data" / "cii_attribute_mapping.json"
_POSITION_MAPPINGS = {
    "ELEMENTS.REL[1] FROM node": ["Aposition"],
    "ELEMENTS.REL[2] TO node": ["Lposition"],
    "ELEMENTS.REL[3] delta X": ["Aposition.X", "Lposition.X"],
    "ELEMENTS.REL[4] delta Y": ["Aposition.Y", "Lposition.Y"],
    "ELEMENTS.REL[5] delta Z": ["Aposition.Z", "Lposition.Z"],
    "COORDS node and global X, Y, Z": ["Aposition"],
}
_PROPERTY_MAPPINGS = {
    "outside_diameter_mm": "ELEMENTS.REL[6] actual outside diameter",
    "wall_thickness_mm": "ELEMENTS.REL[7] wall thickness",
    "insulation_thickness_mm": "ELEMENTS.REL[8] insulation thickness",
    "corrosion_allowance_mm": "ELEMENTS.REL[9] corrosion allowance",
    "temperature_c": "ELEMENTS.REL[10] temperature 1",
    "pressure_kpa": "ELEMENTS.REL[19] pressure 1",
    "cold_modulus_kpa": "ELEMENTS.REL[28] cold elastic modulus",
    "poisson_ratio": "ELEMENTS.REL[29] Poisson ratio",
    "pipe_density_kg_m3": "ELEMENTS.REL[30] pipe density",
    "insulation_density_kg_m3": "ELEMENTS.REL[31] insulation density",
    "fluid_density_kg_m3": "ELEMENTS.REL[32] fluid density",
    "hot_modulus_kpa": "ELEMENTS.REL[37] hot elastic modulus 1",
    "material_id": "MISCEL_1.RRMAT material ID",
    "ambient_temperature_c": "MISCEL_1 execution options: ambient temperature",
}


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("{} must be a number".format(name))
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("{} must be finite".format(name))
    return value


def _integer(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError("{} must be an integer between {} and {}".format(name, minimum, maximum))
    return value


def _real_field(value):
    field = "{:.6E}".format(value)
    if len(field) > 13:
        raise ValueError("Value {} does not fit a CII numeric field".format(value))
    return field.rjust(13)


def _real_lines(values):
    fields = [_real_field(value) for value in values]
    return ["  " + "".join(fields[i:i + 6]) for i in range(0, len(fields), 6)]


def _integer_lines(values):
    fields = []
    for value in values:
        field = str(value)
        if len(field) > 13:
            raise ValueError("Integer {} does not fit a CII field".format(value))
        fields.append(field.rjust(13))
    return ["  " + "".join(fields[i:i + 6]) for i in range(0, len(fields), 6)]


def _position(value):
    return tuple(_number(getattr(value, axis), "position." + axis) for axis in ("X", "Y", "Z"))


class CiiExporter:
    """Write an unqualified CII candidate; engineering inputs must be reviewed."""

    def __init__(self, settings, allow_test_settings=False, cii_version=10, mapping_file=None):
        if not isinstance(settings, dict):
            raise ValueError("CII settings must be a JSON object")
        if isinstance(cii_version, bool) or not isinstance(cii_version, int) or cii_version not in (10, 11):
            raise ValueError("CII writer layout must be 10 or 11")
        self.cii_version = cii_version
        illustrative = settings.get("illustrative")
        if not isinstance(illustrative, bool):
            raise ValueError("illustrative must be true or false")
        if illustrative and not allow_test_settings:
            raise ValueError("Illustrative settings require explicit test-mode consent")
        with open(mapping_file if mapping_file is not None else DEFAULT_MAPPING_FILE, encoding="utf-8") as source:
            mapping = json.load(source)
        self.mapping = self._load_mapping(mapping)
        self.settings = settings
        self.start = _integer(settings.get("node_start"), "node_start", 1, 999999)
        self.step = _integer(settings.get("node_step"), "node_step", 1, 999999)
        self.ambient = _number(settings.get(self.mapping["ambient_temperature_c"]), "ambient_temperature_c")
        specs = settings.get("specs")
        if not isinstance(specs, dict) or not specs:
            raise ValueError("specs must be a non-empty object")
        self.specs = specs

    @classmethod
    def from_file(cls, filename, allow_test_settings=False, cii_version=10, mapping_file=None):
        with open(filename, encoding="utf-8") as source:
            return cls(json.load(source), allow_test_settings, cii_version, mapping_file)

    def _load_mapping(self, mapping):
        if not isinstance(mapping, dict) or not isinstance(mapping.get("mappings"), list):
            raise ValueError("CII mapping must contain a mappings list")
        lookup = mapping.get("lookup")
        if (not isinstance(lookup, dict) or lookup.get("component_type") != "TUBI"
                or lookup.get("source") != ["Spref.Name", "Lbore"]
                or lookup.get("settings") != ["specs[Spref.Name]", "nominal_bore_mm"]):
            raise ValueError("Unsupported CII specification lookup mapping")
        by_target = {}
        supported = set(_POSITION_MAPPINGS) | set(_PROPERTY_MAPPINGS.values())
        for item in mapping["mappings"]:
            if not isinstance(item, dict):
                raise ValueError("Each CII mapping must be an object")
            target = item.get("target")
            if not isinstance(target, str):
                raise ValueError("Each CII mapping requires a target")
            if target in by_target:
                raise ValueError("Duplicate CII mapping target {!r}".format(target))
            by_target[target] = item
            if item.get("status") == "implemented_unverified" and target not in supported:
                raise ValueError("CII mapping target {!r} is not implemented".format(target))
        for target in supported:
            item = by_target.get(target)
            if item is None or item.get("status") != "implemented_unverified":
                raise ValueError("Required CII mapping {!r} is not implemented".format(target))
            version = item.get("version")
            if isinstance(version, bool) or not isinstance(version, int) or version < 1:
                raise ValueError("Required CII mapping {!r} has no known version".format(target))
            if version > self.cii_version:
                raise ValueError("CII mapping {!r} requires writer layout {}".format(target, version))
            if item.get("component_types") != ["TUBI"]:
                raise ValueError("CII mapping {!r} must apply to TUBI".format(target))
        for target, sources in _POSITION_MAPPINGS.items():
            if by_target[target].get("source") != sources:
                raise ValueError("Unsupported geometry source for CII mapping {!r}".format(target))
        properties = {}
        for name, target in _PROPERTY_MAPPINGS.items():
            source = by_target[target].get("source")
            if not isinstance(source, list) or len(source) != 1 or not isinstance(source[0], str):
                raise ValueError("CII mapping {!r} requires one settings source".format(target))
            prefix = "settings."
            key = source[0][len(prefix):]
            suffix = next((unit for unit in ("_kg_m3", "_mm", "_kpa", "_c", "_ratio", "_id")
                           if name.endswith(unit)), None)
            if (not source[0].startswith(prefix) or not key.isidentifier()
                    or suffix is None or not key.endswith(suffix)):
                raise ValueError("Invalid or incompatible settings source for CII mapping {!r}".format(target))
            properties[name] = key
        return properties

    def _properties(self, component):
        spec = component.Spref
        if not spec.IsValid:
            raise ValueError("Tubing has no valid specification")
        name = str(spec.Name)
        bore = _number(component.Lbore, "Lbore")
        if bore <= 0:
            raise ValueError("Lbore must be positive")
        options = self.specs.get(name)
        if not isinstance(options, list):
            raise ValueError("No CII settings for specification {!r}".format(name))
        matches = [
            item for item in options
            if isinstance(item, dict)
            and math.isclose(_number(item.get("nominal_bore_mm"), "nominal_bore_mm"),
                             bore, rel_tol=0.0, abs_tol=0.000001)
        ]
        if len(matches) != 1:
            raise ValueError("Expected one mapping for specification {!r}, bore {}".format(name, bore))
        item = matches[0]
        fields = (
            "outside_diameter_mm", "wall_thickness_mm", "insulation_thickness_mm",
            "corrosion_allowance_mm", "temperature_c", "pressure_kpa",
            "cold_modulus_kpa", "poisson_ratio", "pipe_density_kg_m3",
            "insulation_density_kg_m3", "fluid_density_kg_m3", "hot_modulus_kpa",
        )
        values = {field: _number(item.get(self.mapping[field]), field) for field in fields}
        values["material_id"] = _integer(item.get(self.mapping["material_id"]), "material_id", 1, 699)
        if values["outside_diameter_mm"] <= 0 or values["wall_thickness_mm"] <= 0:
            raise ValueError("Outside diameter and wall thickness must be positive")
        if 2 * values["wall_thickness_mm"] >= values["outside_diameter_mm"]:
            raise ValueError("Wall thickness must be less than half the outside diameter")
        for field in ("insulation_thickness_mm", "corrosion_allowance_mm",
                      "insulation_density_kg_m3", "fluid_density_kg_m3"):
            if values[field] < 0:
                raise ValueError("{} must not be negative".format(field))
        if values["corrosion_allowance_mm"] >= values["wall_thickness_mm"]:
            raise ValueError("Corrosion allowance must be less than wall thickness")
        for field in ("cold_modulus_kpa", "hot_modulus_kpa", "pipe_density_kg_m3"):
            if values[field] <= 0:
                raise ValueError("{} must be positive".format(field))
        if not 0 < values["poisson_ratio"] < 0.5:
            raise ValueError("poisson_ratio must be between 0 and 0.5")
        if values["insulation_thickness_mm"] > 0 and values["insulation_density_kg_m3"] <= 0:
            raise ValueError("Insulated pipe requires a positive insulation density")
        return values

    def export(self, branches, filename):
        branches = list(branches)
        if not branches:
            raise ValueError("Select at least one branch")

        nodes = {}
        edges = set()
        adjacency = {}
        elements = []
        for branch in branches:
            for component in branch.Members:
                if component.Type != "TUBI":
                    raise ValueError("Unsupported component type {!r}; only TUBI is supported".format(
                        component.Type))
                start, end = _position(component.Aposition), _position(component.Lposition)
                if start == end:
                    raise ValueError("Zero-length tubing cannot be exported")
                edge = frozenset((start, end))
                if edge in edges:
                    raise ValueError("Duplicate tubing endpoints cannot be exported")
                edges.add(edge)
                properties = self._properties(component)
                for position in (start, end):
                    if position not in nodes:
                        node = self.start + len(nodes) * self.step
                        nodes[position] = _integer(node, "node number", 1, 999999)
                        adjacency[position] = set()
                adjacency[start].add(end)
                adjacency[end].add(start)
                delta = tuple(b - a for a, b in zip(start, end))
                for value in delta:
                    if abs(float(_real_field(value)) - value) > 0.01:
                        raise ValueError("CII precision would change a pipe length by more than 0.01 mm")
                elements.append((start, end, delta, properties))
        if not elements:
            raise ValueError("Selected branches contain no tubing")

        origins = []
        visited = set()
        for start, _, _, _ in elements:
            if start in visited:
                continue
            origins.append(start)
            pending = [start]
            visited.add(start)
            while pending:
                position = pending.pop()
                for neighbor in adjacency[position] - visited:
                    visited.add(neighbor)
                    pending.append(neighbor)

        lines = ["#$ VERSION", "  {:13.6f}{:13.6f}{:8d}".format(5.0, self.cii_version, 1252)]
        lines.extend(["  PipeCAD CII export candidate"] + ["  "] * 59)
        lines.append("#$ CONTROL")
        lines.extend(_integer_lines([len(elements), 0, 0, 0, 0, 0] + [0] * 11 + [1, 0]))
        lines.append("#$ ELEMENTS")
        for start, end, delta, p in elements:
            values = [0.0] * 53
            values[0:9] = [nodes[start], nodes[end], *delta, p["outside_diameter_mm"],
                           p["wall_thickness_mm"], p["insulation_thickness_mm"],
                           p["corrosion_allowance_mm"]]
            values[9] = p["temperature_c"]
            values[18] = p["pressure_kpa"]
            values[27:32] = [p["cold_modulus_kpa"], p["poisson_ratio"],
                             p["pipe_density_kg_m3"] / 1000000,
                             p["insulation_density_kg_m3"] / 1000000,
                             p["fluid_density_kg_m3"] / 1000000]
            values[36] = p["hot_modulus_kpa"]
            lines.extend(_real_lines(values))
            lines.append("       {:5d} ".format(0))
            if self.cii_version == 11:
                lines.append("       {:5d} ".format(0))
                lines.extend(_integer_lines([-1, -1]))
            lines.extend(_integer_lines([0] * 15))

        lines.append("#$ AUX_DATA")
        lines.extend("#$ " + section for section in _AUXILIARY_SECTIONS)
        lines.append("#$ MISCEL_1")
        lines.extend(_real_lines([p["material_id"] for _, _, _, p in elements]))
        lines.extend([
            "  " + "".join(str(v).rjust(13) for v in (0, 0, 0, 0)) + _real_field(0) + str(0).rjust(13),
            "  " + str(0).rjust(13) + _real_field(0) + _real_field(self.ambient)
            + "".join(str(v).rjust(13) for v in (0, 0, 0)),
            "  " + "".join(str(v).rjust(13) for v in (0, 0, 0, 0)) + _real_field(0) + str(0).rjust(13),
        ])
        lines.extend(_integer_lines([3]))
        lines.append("#$ UNITS")
        lines.extend(_real_lines(_UNIT_FACTORS))
        lines.extend("  " + label for label in _UNIT_LABELS)
        lines.append("#$ COORDS")
        lines.extend(_integer_lines([len(origins)]))
        for origin in origins:
            coords = ["{:13.4f}".format(value) for value in origin]
            if any(len(value) > 13 for value in coords):
                raise ValueError("Origin coordinate does not fit a CII field")
            lines.append("  " + str(nodes[origin]).rjust(13) + "".join(coords))

        output = "\r\n".join(lines) + "\r\n"
        Path(filename).write_bytes(output.encode("cp1252"))
