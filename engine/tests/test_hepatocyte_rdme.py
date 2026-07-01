from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.hepatocyte_counts import PROTEIN_BY_ID
from cell_engine.stochastic.hepatocyte_rdme import (
    CYTOSOL,
    MEMBRANE_BASOLATERAL,
    MEMBRANE_CANALICULAR,
    MITOCHONDRIA,
    build_hepatocyte_lattice,
    seed_proteins,
    voxel_field,
)


class HepatocyteLatticeTest(unittest.TestCase):
    def test_has_all_compartments(self) -> None:
        lattice = build_hepatocyte_lattice(n=20)
        comps = {lattice.compartment_of(i) for i in range(lattice.size)}
        self.assertIn(MEMBRANE_BASOLATERAL, comps)
        self.assertIn(MEMBRANE_CANALICULAR, comps)
        self.assertIn(CYTOSOL, comps)
        self.assertIn(MITOCHONDRIA, comps)

    def test_membrane_split_by_side(self) -> None:
        lattice = build_hepatocyte_lattice(n=20)
        center = (lattice.nx - 1) / 2.0
        for i in range(lattice.size):
            comp = lattice.compartment_of(i)
            x, _, _ = lattice.coords(i)
            if comp == MEMBRANE_CANALICULAR:
                self.assertGreater(x - center, 0)
            elif comp == MEMBRANE_BASOLATERAL:
                self.assertLessEqual(x - center, 0)


class SeedingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lattice = build_hepatocyte_lattice(n=20)
        self.rng = EngineRng(seed=42)
        # Thin the absolute numbers but keep structure (full CPS1 is 5e7).
        self.state = seed_proteins(self.lattice, self.rng, scale=1e-3)

    def test_copy_numbers_conserved_at_scale(self) -> None:
        for pid, p in PROTEIN_BY_ID.items():
            expected = int(round(p.copies_typical * 1e-3))
            self.assertEqual(self.state.total(pid), expected, pid)

    def test_proteins_only_in_their_compartment(self) -> None:
        want = {
            "naka": {MEMBRANE_BASOLATERAL},
            "bsep": {MEMBRANE_CANALICULAR},
            "glucokinase": {CYTOSOL},
            "cps1": {MITOCHONDRIA},
        }
        for voxel in self.state.occupied_voxels():
            comp = self.lattice.compartment_of(voxel)
            for pid in self.state.voxel_counts(voxel):
                if pid in want:
                    self.assertIn(comp, want[pid], f"{pid} leaked into {comp}")

    def test_relative_abundance_preserved(self) -> None:
        # CPS1 still dominates after spatial seeding.
        self.assertGreater(self.state.total("cps1"), self.state.total("ntcp"))
        self.assertGreater(self.state.total("ntcp"), self.state.total("naka"))

    def test_voxel_field_is_sparse_and_normalised(self) -> None:
        field = voxel_field(self.lattice, self.state)
        self.assertGreater(len(field), 0)
        self.assertLess(len(field), self.lattice.size)  # sparse
        for rec in field:
            for coord in rec["p"]:
                self.assertGreaterEqual(coord, -1.0001)
                self.assertLessEqual(coord, 1.0001)
            self.assertTrue(rec["n"])  # no empty voxels emitted


if __name__ == "__main__":
    unittest.main()
