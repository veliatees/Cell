from __future__ import annotations

from dataclasses import replace
import unittest

from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation.experiments import (
    BSEP_LOSS_SCENARIO,
    CANALICULAR_EXPORT_LOSS_SCENARIO,
    MRP2_LOSS_SCENARIO,
    apply_scenario,
)


class CellularResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)

    def test_exact_bsep_loss_blocks_only_bile_acid_export(self) -> None:
        baseline = step_cell(self.definition, self.state, 1800.0, rng=EngineRng(51))
        bsep_loss = step_cell(
            self.definition,
            apply_scenario(self.state, BSEP_LOSS_SCENARIO),
            1800.0,
            rng=EngineRng(51),
        )
        baseline_fluxes = {flux.id: flux.value for flux in baseline.metabolic_fluxes}
        loss_fluxes = {flux.id: flux.value for flux in bsep_loss.metabolic_fluxes}
        self.assertGreater(baseline_fluxes["bsep-bile-acid-export"], 0.0)
        self.assertEqual(loss_fluxes["bsep-bile-acid-export"], 0.0)
        self.assertEqual(loss_fluxes["mrp2-bilirubin-export"], baseline_fluxes["mrp2-bilirubin-export"])
        self.assertGreater(bsep_loss.pools["bile_acids"].value, baseline.pools["bile_acids"].value)
        self.assertGreater(baseline.pools["canalicular_bile_acids"].value, 0.0)
        self.assertEqual(bsep_loss.pools["canalicular_bile_acids"].value, 0.0)
        self.assertAlmostEqual(
            baseline.pools["bile_acids"].value + baseline.pools["canalicular_bile_acids"].value,
            self.state.pools["bile_acids"].value,
        )
        assert baseline.cellular_response is not None
        self.assertEqual(baseline.cellular_response.intervention_type, "unclassified")
        self.assertEqual(
            baseline.cellular_response.cyp7a1_feedback_status,
            "expression_present_function_unknown_no_synthesis_rate",
        )

    def test_exact_mrp2_loss_blocks_only_bilirubin_export(self) -> None:
        baseline = step_cell(self.definition, self.state, 1800.0, rng=EngineRng(52))
        mrp2_loss = step_cell(
            self.definition,
            apply_scenario(self.state, MRP2_LOSS_SCENARIO),
            1800.0,
            rng=EngineRng(52),
        )
        baseline_fluxes = {flux.id: flux.value for flux in baseline.metabolic_fluxes}
        loss_fluxes = {flux.id: flux.value for flux in mrp2_loss.metabolic_fluxes}
        self.assertGreater(baseline_fluxes["mrp2-bilirubin-export"], 0.0)
        self.assertEqual(loss_fluxes["mrp2-bilirubin-export"], 0.0)
        self.assertEqual(loss_fluxes["bsep-bile-acid-export"], baseline_fluxes["bsep-bile-acid-export"])
        self.assertGreater(mrp2_loss.pools["bilirubin_conjugates"].value, baseline.pools["bilirubin_conjugates"].value)
        self.assertGreater(baseline.pools["canalicular_bilirubin_conjugates"].value, 0.0)
        self.assertEqual(mrp2_loss.pools["canalicular_bilirubin_conjugates"].value, 0.0)
        self.assertAlmostEqual(
            baseline.pools["bilirubin_conjugates"].value
            + baseline.pools["canalicular_bilirubin_conjugates"].value,
            self.state.pools["bilirubin_conjugates"].value,
        )

    def test_response_tracks_proteostasis_damage_exposure_and_fate_evidence(self) -> None:
        stressed = replace(
            apply_scenario(self.state, CANALICULAR_EXPORT_LOSS_SCENARIO),
            pools={
                **self.state.pools,
                "misfolded_protein": replace(self.state.pools["misfolded_protein"], value=0.70),
                "ROS": replace(self.state.pools["ROS"], value=0.60),
            },
            stress={**self.state.stress, "proteotoxic": 0.8, "oxidative": 0.7, "cholestatic": 0.8},
        )
        first = step_cell(self.definition, stressed, 120.0, rng=EngineRng(53))
        second = step_cell(self.definition, first, 120.0, rng=EngineRng(53))
        response = second.cellular_response
        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.cholestasis_state, "canalicular_export_loss")
        self.assertEqual(response.intervention_type, "combined_genetic_abcb11_abcc2_loss")
        self.assertEqual(response.bile_acid_system_total, response.intracellular_bile_acids + response.canalicular_bile_acids)
        self.assertGreater(response.upr_signal or 0.0, 0.0)
        self.assertGreater(response.damage_exposure_s["proteotoxic"], 0.0)
        self.assertGreater(
            response.damage_exposure_s["proteotoxic"],
            first.cellular_response.damage_exposure_s["proteotoxic"],  # type: ignore[union-attr]
        )
        self.assertIn(response.fate_evidence, {"homeostatic", "proteostasis_adaptation", "senescence_pressure", "apoptotic_pressure"})


if __name__ == "__main__":
    unittest.main()
