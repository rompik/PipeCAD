import importlib.util
import io
import math
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = (
    ROOT / "python" / "PipeCAD" / "Design" / "General" / "PcfExporterCore.py"
)
spec = importlib.util.spec_from_file_location("pcf_exporter_core", CORE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Position:
    def __init__(self, x, y, z=0):
        self.X = x
        self.Y = y
        self.Z = z

    def Distance(self, other):
        return math.sqrt(
            (self.X - other.X) ** 2
            + (self.Y - other.Y) ** 2
            + (self.Z - other.Z) ** 2
        )


def reference(name, **attributes):
    return SimpleNamespace(IsValid=True, Name=name, **attributes)


class Component:
    def __init__(
        self,
        component_type="ELBO",
        arrive=1,
        leave=2,
        points=None,
        skey="ELBW",
        item_code="ELBOW-50",
        description="ELBOW 50",
        component_position=None,
        full_type=None,
    ):
        self.Type = component_type
        self.FullType = full_type or component_type
        self.Arrive = arrive
        self.Leave = leave
        self.points = points or {
            1: Position(100, 0),
            2: Position(200, 0),
            3: Position(100, 100),
        }
        self.Pbores = {index: 50 for index in self.points}
        self.Position = component_position or Position(150, 0)
        self.Directions = {
            3: SimpleNamespace(X=1, Y=0, Z=0),
        }
        detref = reference(
            item_code, Skey=skey, Rtext=description, Description=description
        )
        self.Spref = reference("PIPE-SPEC", Detref=detref)
        self.Aconnect = "BW"
        self.Lconnect = "FL"
        self.IsValid = True
        self.calls = []

    def GetPosition(self, attribute, index, world):
        self.calls.append(("position", attribute, index, world))
        return self.points[int(index)]

    def GetDirection(self, attribute, index, world):
        self.calls.append(("direction", attribute, index, world))
        return self.Directions[int(index)]


def pipeline():
    return SimpleNamespace(
        IsValid=True,
        Name="P-101",
        Pspec=reference("A1"),
        Ispec=reference("I1"),
        Tspec=reference("T1"),
    )


def branch(components, head=Position(0, 0), tail=Position(300, 0)):
    result = SimpleNamespace(
        Type="BRAN",
        Name="B-101",
        Owner=pipeline(),
        Hposition=head,
        Tposition=tail,
        Hbore=50,
        Tbore=50,
        Members=components,
    )
    for component in components:
        component.Owner = result
    return result


class PcfExporterCoreTests(unittest.TestCase):
    def test_non_tube_component_uses_arrive_leave_points_and_catalogue_detail(self):
        component = Component(full_type="ELBOW")
        stream = io.StringIO()
        world = object()

        module.write_pcf([branch([component])], stream, world)

        output = stream.getvalue()
        self.assertIn("END-POINT  100 0 0 50 BW", output)
        self.assertIn("END-POINT  200 0 0 50 FL", output)
        self.assertIn("CENTRE-POINT  150 0 0", output)
        self.assertIn("SKEY  ELBW", output)
        self.assertIn("ITEM-CODE  ELBOW-50", output)
        self.assertIn("ITEM-DESCRIPTION  ELBOW 50", output)
        self.assertIn(("position", "Pposition", 1, world), component.calls)
        self.assertIn(("position", "Pposition", 2, world), component.calls)

    def test_gap_pipes_and_component_records_have_unique_identifiers(self):
        component = Component(
            full_type="VALVE", component_position=Position(150, 0)
        )
        stream = io.StringIO()

        module.write_pcf([branch([component])], stream, object())

        output = stream.getvalue()
        identifiers = [
            int(line.rsplit(" ", 1)[1])
            for line in output.splitlines()
            if "COMPONENT-IDENTIFIER" in line
        ]
        self.assertEqual(identifiers, list(range(1, 4)))
        self.assertEqual(sum(line == "PIPE" for line in output.splitlines()), 2)
        self.assertIn("SPINDLE-DIRECTION  EAST", output)

    def test_tee_and_reducer_records_are_exported(self):
        tee = Component(full_type="TEE", arrive=1, leave=2)
        reducer = Component(
            full_type="REDUCER",
            skey="RCBW",
            item_code="RED-50-25",
            description="REDUCER",
            points={
                1: Position(400, 0),
                2: Position(500, 0),
                3: Position(400, 100),
            },
        )
        stream = io.StringIO()
        branch_item = branch([tee, reducer], tail=Position(500, 0))

        module.write_pcf([branch_item], stream, object())

        output = stream.getvalue()
        self.assertIn("TEE", output)
        self.assertIn("BRANCH1-POINT  100 100 0 50", output)
        self.assertIn("REDUCER-CONCENTRIC", output)

    def test_component_type_falls_back_to_catalogue_gtype(self):
        component = Component(component_type="UNKN")
        component.FullType = ""
        component.Spref.Catref = SimpleNamespace(
            IsValid=True, Gtype="VALV"
        )
        stream = io.StringIO()

        module.write_pcf([branch([component])], stream, object())

        self.assertIn("\nVALVE\n", stream.getvalue())

    def test_materials_contains_only_real_item_codes(self):
        detref_less = Component(full_type="ELBOW")
        detref_less.Spref = SimpleNamespace(
            IsValid=True, Name="PIPE-SPEC", Detref=SimpleNamespace(IsValid=False)
        )
        stream = io.StringIO()

        module.write_pcf([branch([detref_less])], stream, object())

        output = stream.getvalue()
        materials = output.split("MATERIALS", 1)[1]
        self.assertNotIn("PA100", output)
        self.assertNotIn("PIPE SCH80", output)
        self.assertNotIn("ITEM-CODE", materials)


if __name__ == "__main__":
    unittest.main()
