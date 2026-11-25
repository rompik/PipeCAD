import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "python" / "PipeCAD" / "Design" / "General"
spec = importlib.util.spec_from_file_location("cii_exporter", DIRECTORY / "CiiExporter.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def point(x, y, z):
    return SimpleNamespace(X=x, Y=y, Z=z)


def tubing(start, end, bore=50, spec_name="TEST-SPEC"):
    return SimpleNamespace(
        Type="TUBI", Aposition=point(*start), Lposition=point(*end), Lbore=bore,
        Spref=SimpleNamespace(IsValid=True, Name=spec_name),
    )


def branch(*members):
    return SimpleNamespace(Members=members)


def fields(line):
    return [line[i:i + 13] for i in range(2, len(line), 13)]


class CiiExporterTests(unittest.TestCase):
    def setUp(self):
        self.settings = json.loads((DIRECTORY / "cii_settings.example.json").read_text(encoding="utf-8"))
        self.exporter = module.CiiExporter(self.settings, allow_test_settings=True)

    def test_connected_tubing_serializes_geometry_and_properties(self):
        components = [
            tubing((100, 200, 300), (1100, 200, 300)),
            tubing((1100, 200, 300), (1100, 700, 300)),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pipe.cii"
            self.exporter.export([branch(*components)], path)
            data = path.read_bytes()
        self.assertIn(b"\r\n", data)
        lines = data.decode("cp1252").splitlines()
        self.assertEqual(lines[0], "#$ VERSION")
        control = lines.index("#$ CONTROL")
        self.assertEqual(int(fields(lines[control + 1])[0]), 2)
        self.assertEqual(int(fields(lines[control + 3])[5]), 1)
        first = lines.index("#$ ELEMENTS") + 1
        real_values = [float(field) for line in lines[first:first + 9] for field in fields(line)]
        self.assertEqual(len(real_values), 53)
        self.assertEqual(real_values[:9], [10, 20, 1000, 0, 0, 60.3, 3.91, 0, 1])
        self.assertEqual(real_values[9], 80)
        self.assertEqual(real_values[18], 1000)
        self.assertAlmostEqual(real_values[29], 0.00785)
        self.assertAlmostEqual(real_values[31], 0.001)
        self.assertEqual(real_values[36], 195000000)
        auxiliary = lines.index("#$ AUX_DATA")
        material = lines.index("#$ MISCEL_1")
        self.assertLess(auxiliary, lines.index("#$ BEND"))
        self.assertLess(lines.index("#$ RESTRANT"), material)
        self.assertEqual([float(field) for field in fields(lines[material + 1])], [1, 1])
        units = lines.index("#$ UNITS")
        self.assertEqual(sum(len(fields(line)) for line in lines[units + 1:units + 5]), 22)
        second = first + 13
        self.assertEqual([float(field) for field in fields(lines[second])][:5],
                         [20, 30, 0, 500, 0])
        coords = lines.index("#$ COORDS")
        self.assertEqual(int(fields(lines[coords + 1])[0]), 1)
        self.assertEqual([float(field) for field in fields(lines[coords + 2])],
                         [10, 100, 200, 300])

    def test_illustrative_settings_require_opt_in(self):
        with self.assertRaisesRegex(ValueError, "test-mode"):
            module.CiiExporter(self.settings)

    def test_unknown_components_and_mapping_do_not_replace_output(self):
        cases = [
            branch(tubing((0, 0, 0), (1, 0, 0)), SimpleNamespace(Type="ELBO")),
            branch(tubing((0, 0, 0), (1, 0, 0), bore=80)),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pipe.cii"
            for case in cases:
                path.write_bytes(b"existing")
                with self.assertRaises(ValueError):
                    self.exporter.export([case], path)
                self.assertEqual(path.read_bytes(), b"existing")

    def test_disconnected_duplicate_and_zero_length_rejected(self):
        first = tubing((0, 0, 0), (100, 0, 0))
        cases = [
            branch(first, tubing((200, 0, 0), (300, 0, 0))),
            branch(first, tubing((100, 0, 0), (0, 0, 0))),
            branch(tubing((0, 0, 0), (0, 0, 0))),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for case in cases:
                with self.assertRaises(ValueError):
                    self.exporter.export([case], Path(directory) / "pipe.cii")

    def test_invalid_engineering_settings_rejected(self):
        self.settings["specs"]["TEST-SPEC"][0]["wall_thickness_mm"] = 100
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(ValueError, "thickness"):
            self.exporter.export([branch(tubing((0, 0, 0), (100, 0, 0)))],
                                 Path(directory) / "pipe.cii")

    def test_non_finite_and_lossy_coordinates_are_rejected(self):
        cases = [
            tubing((0, 0, 0), (float("nan"), 0, 0)),
            tubing((0, 0, 0), (12345678, 0, 0)),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for case in cases:
                with self.assertRaises(ValueError):
                    self.exporter.export([branch(case)], Path(directory) / "pipe.cii")


if __name__ == "__main__":
    unittest.main()
