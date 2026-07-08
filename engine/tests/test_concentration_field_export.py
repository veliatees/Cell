"""Guard the per-voxel concentration field the renderer consumes.

Validates both the exporter's physics (on a small lattice) and the committed
``public/cell_concentration_field.json`` artifact, mirroring the
``test_hepatocyte_counts`` convention of asserting the shipped JSON agrees with
the engine.
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from cell_engine.stochastic.hepatocyte_rdme import (
    MEMBRANE_BASOLATERAL,
    MITOCHONDRIA,
    build_hepatocyte_lattice,
)

_ROOT = Path(__file__).resolve().parents[2]
_PUBLIC_JSON = _ROOT / "public" / "cell_concentration_field.json"
_SCRIPT = _ROOT / "scripts" / "export_concentration_field.py"


def _load_exporter():
    spec = importlib.util.spec_from_file_location("export_concentration_field", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConcentrationFieldPhysics(unittest.TestCase):
    def setUp(self) -> None:
        self.exp = _load_exporter()

    def test_glucose_decreases_from_sinusoid_to_canaliculus(self) -> None:
        lattice = build_hepatocyte_lattice(n=12)
        field = self.exp.glucose_field(lattice, iterations=2000)
        center = (lattice.nx - 1) / 2.0
        sinusoid, canaliculus = [], []
        for idx, value in field.items():
            x = lattice.coords(idx)[0]
            if (x - center) < -1.5:
                sinusoid.append(value)
            elif (x - center) > 1.5:
                canaliculus.append(value)
        self.assertTrue(sinusoid and canaliculus)
        # Blood-facing side is glucose-rich; the bile pole is depleted.
        self.assertGreater(sum(sinusoid) / len(sinusoid), sum(canaliculus) / len(canaliculus))
        self.assertLessEqual(max(field.values()), self.exp.GLUCOSE_BLOOD_MM + 1e-6)

    def test_atp_peaks_at_mitochondria(self) -> None:
        lattice = build_hepatocyte_lattice(n=12)
        field = self.exp.atp_field(lattice, iterations=2000)
        mito, other = [], []
        for idx, value in field.items():
            if lattice.compartment_of(idx) == MITOCHONDRIA:
                mito.append(value)
            else:
                other.append(value)
        self.assertTrue(mito and other)
        # Micro-domains: ATP is far higher in mitochondrial voxels than elsewhere.
        self.assertGreater(sum(mito) / len(mito), 2.0 * (sum(other) / len(other)))
        self.assertLessEqual(max(field.values()), self.exp.ATP_MITO_MM + 1e-6)


class CommittedArtifact(unittest.TestCase):
    def test_public_json_structure_and_gradient(self) -> None:
        data = json.loads(_PUBLIC_JSON.read_text())
        self.assertIn("voxels", data)
        self.assertEqual(set(data["species"]), {"g", "a"})
        voxels = data["voxels"]
        self.assertGreater(len(voxels), 0)
        for v in voxels:
            self.assertEqual(len(v["p"]), 3)
            self.assertIn("g", v)
            self.assertIn("a", v)

        # The shipped glucose field still runs high (sinusoid, -x) to low (+x).
        low_x = [v["g"] for v in voxels if v["p"][0] < -0.4]
        high_x = [v["g"] for v in voxels if v["p"][0] > 0.4]
        self.assertTrue(low_x and high_x)
        self.assertGreater(sum(low_x) / len(low_x), sum(high_x) / len(high_x))

        # ATP still peaks in mitochondrial voxels.
        mito = [v["a"] for v in voxels if v["c"] == MITOCHONDRIA]
        cyt = [v["a"] for v in voxels if v["c"] == "cytosol"]
        self.assertTrue(mito and cyt)
        self.assertGreater(sum(mito) / len(mito), sum(cyt) / len(cyt))

    def test_basolateral_is_the_glucose_source(self) -> None:
        data = json.loads(_PUBLIC_JSON.read_text())
        baso = [v["g"] for v in data["voxels"] if v["c"] == MEMBRANE_BASOLATERAL]
        self.assertTrue(baso)
        # Dirichlet source held at blood glucose.
        self.assertAlmostEqual(max(baso), data["params"]["glucose"]["bloodMM"], places=3)


if __name__ == "__main__":
    unittest.main()
