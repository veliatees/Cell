from __future__ import annotations

import unittest
from math import exp

from cell_engine.stochastic.spatial import (
    SpatialField,
    cfl_limit_dt,
    decay_length_um,
    react_diffuse,
    uniform_field,
)


class DiffusionTests(unittest.TestCase):
    def test_pure_diffusion_conserves_mass(self):
        # A spike in the middle; reflecting boundaries -> total amount is invariant.
        n = 40
        conc = [0.0] * n
        conc[20] = 100.0
        field = SpatialField(("X",), dx_um=1.0, conc={"X": tuple(conc)})
        diffusion = {"X": 10.0}
        dt = 0.5 * cfl_limit_dt(diffusion, 1.0)
        before = field.total("X")
        out = react_diffuse(field, diffusion=diffusion, dt_s=dt, steps=2000)
        self.assertAlmostEqual(out.total("X"), before, delta=1e-6)

    def test_diffusion_relaxes_toward_uniform(self):
        n = 30
        conc = [10.0 if i < n // 2 else 0.0 for i in range(n)]
        field = SpatialField(("X",), dx_um=1.0, conc={"X": tuple(conc)})
        diffusion = {"X": 5.0}
        dt = 0.5 * cfl_limit_dt(diffusion, 1.0)
        out = react_diffuse(field, diffusion=diffusion, dt_s=dt, steps=20000)
        prof = out.profile("X")
        # Should have flattened toward the mean (5.0).
        self.assertLess(max(prof) - min(prof), 0.5)
        self.assertAlmostEqual(sum(prof) / n, 5.0, delta=1e-6)

    def test_cfl_limit_rejects_unstable_dt(self):
        field = uniform_field(("X",), 10, 1.0, 1.0)
        with self.assertRaises(ValueError):
            react_diffuse(field, diffusion={"X": 10.0}, dt_s=1.0, steps=1)


class ReactionDiffusionGradientTests(unittest.TestCase):
    def test_morphogen_exponential_gradient(self):
        # Production at voxel 0, first-order degradation everywhere -> steady-state
        # exponential gradient with decay length lambda = sqrt(D/k).
        n = 60
        D, k = 10.0, 0.4
        lam = decay_length_um(D, k)  # = 5 um
        self.assertAlmostEqual(lam, 5.0, places=6)

        field = uniform_field(("M",), n, dx_um=1.0, value=0.0)
        production = 5.0  # mM/s injected at voxel 0

        def reaction(i: int, voxel: dict[str, float]) -> dict[str, float]:
            src = production if i == 0 else 0.0
            return {"M": src - k * voxel["M"]}

        dt = 0.5 * cfl_limit_dt({"M": D}, 1.0)
        out = react_diffuse(field, diffusion={"M": D}, dt_s=dt, steps=40000, reaction=reaction)
        prof = out.profile("M")

        # Monotonic decay away from the source.
        self.assertGreater(prof[2], prof[6])
        self.assertGreater(prof[6], prof[12])
        # Ratio between voxels dx apart matches exp(-dx/lambda) in the clean region.
        expected_ratio = exp(-1.0 / lam)  # ~0.8187
        for i in (8, 10, 12, 14):
            self.assertAlmostEqual(prof[i + 1] / prof[i], expected_ratio, delta=0.03)


class MicrodomainTests(unittest.TestCase):
    def test_atp_microdomain_gradient(self):
        # ATP produced at a "mitochondria" voxel and consumed everywhere forms a
        # local high-ATP microdomain that falls off with distance — the spatial
        # version of the coarse microdomain delay the well-mixed engine assumed.
        n = 40
        mito = 5
        D, k = 150.0, 2.0  # ATP diffuses fast
        field = uniform_field(("ATP",), n, dx_um=1.0, value=0.0)

        def reaction(i: int, voxel: dict[str, float]) -> dict[str, float]:
            src = 50.0 if i == mito else 0.0
            return {"ATP": src - k * voxel["ATP"]}

        dt = 0.5 * cfl_limit_dt({"ATP": D}, 1.0)
        out = react_diffuse(field, diffusion={"ATP": D}, dt_s=dt, steps=20000, reaction=reaction)
        prof = out.profile("ATP")
        self.assertEqual(max(range(n), key=lambda i: prof[i]), mito)  # peak at the source
        self.assertGreater(prof[mito], prof[mito + 8])                 # falls with distance


if __name__ == "__main__":
    unittest.main()
