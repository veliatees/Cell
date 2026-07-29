from __future__ import annotations

import json
import unittest

from cell_engine.quantitative.cytoplasm_dynamics import (
    ACTIVE_TRANSPORT_SPEED_UM_S,
    CYTOPLASM_DYNAMICS_SOURCES,
    build_cytoplasm_dynamics,
    cytoplasm_dynamics_snapshot,
    relative_effective_viscosity,
    thermal_diffusion_um2_s,
)


class ViscosityLawTest(unittest.TestCase):
    def test_gfp_small_probe_anchor_is_recovered(self) -> None:
        # The prefactor is fixed so a ~2.5 nm probe returns the measured 3.2x.
        self.assertAlmostEqual(relative_effective_viscosity(2.5), 3.2, places=6)

    def test_viscosity_grows_with_probe_size_but_stays_bounded(self) -> None:
        small = relative_effective_viscosity(2.5)
        organelle = relative_effective_viscosity(1000.0)
        huge = relative_effective_viscosity(1_000_000.0)
        self.assertGreater(organelle, small)
        # Saturating law: micrometre and metre probes see nearly the same
        # (bounded) macroviscosity, never an exponential blow-up.
        self.assertLess(huge, organelle * 1.2)
        self.assertLess(organelle, 200.0)


class ThermalDiffusionTest(unittest.TestCase):
    def test_smaller_organelles_diffuse_faster(self) -> None:
        # Stokes-Einstein: D ~ 1/(r * eta(r)); a small vesicle out-diffuses a mito.
        d_small = thermal_diffusion_um2_s(0.34)
        d_mito = thermal_diffusion_um2_s(0.65)
        d_nucleus = thermal_diffusion_um2_s(4.4)
        self.assertGreater(d_small, d_mito)
        self.assertGreater(d_mito, d_nucleus)

    def test_organelle_thermal_diffusion_is_physically_small(self) -> None:
        # Micrometre organelles barely thermally diffuse; active transport
        # dominates the visible motion.
        self.assertLess(thermal_diffusion_um2_s(0.65), 0.1)


class ContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dynamics = build_cytoplasm_dynamics()

    def test_per_organelle_motility_matches_placement_types(self) -> None:
        ids = {m.organelle_id for m in self.dynamics.organelle_motility}
        self.assertEqual(ids, {"nucleus", "mitochondria", "lysosomes", "peroxisomes"})
        # Each carries a size-dependent thermal coefficient.
        for m in self.dynamics.organelle_motility:
            self.assertGreater(m.thermal_diffusion_um2_s, 0.0)
            self.assertGreater(m.relative_effective_viscosity, 1.0)

    def test_active_transport_speed_is_the_grounded_hepatocyte_value(self) -> None:
        self.assertEqual(self.dynamics.active_transport_speed_um_s, ACTIVE_TRANSPORT_SPEED_UM_S)

    def test_is_not_a_reaction_transport_authority(self) -> None:
        self.assertFalse(self.dynamics.is_reaction_transport_authority)
        self.assertTrue(
            any("reaction-transport authority" in b for b in self.dynamics.blockers)
        )

    def test_extrapolation_and_visual_model_are_flagged(self) -> None:
        self.assertTrue(any("extrapolated" in n for n in self.dynamics.not_grounded))
        self.assertTrue(any("stirring" in n for n in self.dynamics.not_grounded))
        self.assertTrue(set(self.dynamics.source_ids) <= set(CYTOPLASM_DYNAMICS_SOURCES))

    def test_snapshot_is_json_ready(self) -> None:
        payload = cytoplasm_dynamics_snapshot()
        restored = json.loads(json.dumps(payload))
        self.assertEqual(restored["version"], "cytoplasm_dynamics_visual_v1")
        self.assertFalse(restored["is_reaction_transport_authority"])
        self.assertEqual(len(restored["organelle_motility"]), 4)


if __name__ == "__main__":
    unittest.main()
