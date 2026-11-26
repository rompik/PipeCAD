import importlib.util
import io
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
EXPORTER_PATH = (
    ROOT / "python" / "PipeCAD" / "Design" / "General" / "PmlExporter.py"
)
spec = importlib.util.spec_from_file_location("pml_exporter", EXPORTER_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def direction(x, y, z):
    return SimpleNamespace(X=x, Y=y, Z=z)


def position(x, y, z):
    return SimpleNamespace(X=x, Y=y, Z=z)


def orientation(x, y):
    return SimpleNamespace(
        XDirection=lambda: direction(*x),
        YDirection=lambda: direction(*y),
    )


class PmlExporterTests(unittest.TestCase):
    def test_equipment_uses_current_member_geometry_api(self):
        box = SimpleNamespace(
            Type="BOX",
            Name="BOX-1",
            Xlength=10.0,
            Ylength=20.0,
            Zlength=30.0,
            Position=position(1, 2, 3),
            Orientation=orientation((1, 0, 0), (0, 1, 0)),
            IsValid=True,
        )
        equipment = SimpleNamespace(
            Type="EQUI",
            Name="P-101",
            Position=position(100, 200, 300),
            Members=[box],
            IsValid=True,
        )
        stream = io.StringIO()

        module.write_macro(equipment, stream, timestamp="TEST-DATE")

        output = stream.getvalue()
        self.assertIn("NEW EQUIPMENT/P-101", output)
        self.assertIn("POS E100.000000 N200.000000 U300.000000", output)
        self.assertIn("NEW BOX XLEN 10.000000 YLEN 20.000000 ZLEN 30.000000", output)
        self.assertIn("ORI X is $!aDx and Y is $!aDy", output)
        self.assertNotIn("aDy.north = 0.000000", output)
        self.assertIn("INPUT END EQUI", output)

    def test_catalogue_exports_ptset_scom_and_parameter_array(self):
        ptcar = SimpleNamespace(
            Type="PTCA", Name="", Number=1, Connection="FLAN", Bore="DD1",
            Direction="", Px="DD1 / 2", Py="0", Pz="0",
        )
        ptset = SimpleNamespace(Type="PTSE", Name="POINTS", Members=[ptcar])
        scom = SimpleNamespace(
            Type="SCOM", Name="BEND", Gtype="BEND", Param=[50.0, 150.0],
        )
        category = SimpleNamespace(
            Type="CATE", Name="CAT", Purpose="PIPE", Description="Test category",
            Gtype="BEND", Members=[ptset, scom],
        )
        section = SimpleNamespace(
            Type="SECT", Name="SEC", Purpose="PIPE", Members=[category]
        )
        catalogue = SimpleNamespace(
            Type="CATA", Name="CATA-1", Purpose="PIPE", Members=[section]
        )
        stream = io.StringIO()

        module.write_macro(catalogue, stream, timestamp="TEST-DATE")

        output = stream.getvalue()
        self.assertIn("NEW CATALOGUE/CATA-1", output)
        self.assertIn("NEW PTCAR", output)
        self.assertIn("PX DD1 / 2", output)
        self.assertIn("PARA 50.0 150.0", output)
        self.assertIn("!!ce.Ptref = !aPtref", output)

    def test_unsupported_type_is_rejected_without_writing_partial_macro_content(self):
        stream = io.StringIO()
        with self.assertRaisesRegex(ValueError, "Unsupported PML export element"):
            module.write_macro(SimpleNamespace(Type="ZONE"), stream)
        self.assertIn("INPUT BEGIN", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
