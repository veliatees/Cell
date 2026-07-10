from __future__ import annotations

import unittest

from cell_engine.stochastic.transport import build_transport_network, seed_transport
from cell_engine.stochastic.transporter_lifecycle import (
    ObservedTraffickingTransfer,
    TransporterLifecycleState,
    activity_from_lifecycle_states,
    apply_observed_transfers,
)


class TransporterLifecycleTests(unittest.TestCase):
    def test_functional_pool_depends_on_polarized_surface_domain(self):
        bsep = TransporterLifecycleState(
            protein_id="bsep",
            evidence_source_id="unit_test_measurement",
            experimental_system="primary human hepatocytes",
            canalicular_surface_copies=5_000.0,
            basolateral_surface_copies=4_000.0,
            unlocalized_intracellular_copies=11_000.0,
        )
        self.assertEqual(bsep.live_copies, 20_000.0)
        self.assertEqual(bsep.functional_surface_copies, 5_000.0)
        self.assertEqual(bsep.surface_measurement().surface_fraction, 0.25)

    def test_observed_transfers_conserve_total_synthesis(self):
        state = TransporterLifecycleState(
            protein_id="mrp2",
            evidence_source_id="unit_test_measurement",
            experimental_system="primary human hepatocytes",
            golgi_copies=8_000.0,
            subapical_endosome_copies=2_000.0,
        )
        moved = apply_observed_transfers(
            state,
            (
                ObservedTraffickingTransfer("golgi_copies", "canalicular_surface_copies", 3_000.0, "unit_test_transfer"),
                ObservedTraffickingTransfer("subapical_endosome_copies", "degraded_copies", 500.0, "unit_test_transfer"),
            ),
        )
        self.assertEqual(moved.canalicular_surface_copies, 3_000.0)
        self.assertEqual(moved.degraded_copies, 500.0)
        self.assertEqual(moved.total_synthesized_copies, state.total_synthesized_copies)

    def test_lifecycle_surface_activity_scales_canalicular_exports(self):
        reference = {"bsep": 10_000.0, "mrp2": 8_000.0}
        lifecycle = {
            "bsep": TransporterLifecycleState(
                protein_id="bsep",
                evidence_source_id="unit_test_measurement",
                experimental_system="primary human hepatocytes",
                canalicular_surface_copies=2_500.0,
                unlocalized_intracellular_copies=17_500.0,
            ),
            "mrp2": TransporterLifecycleState(
                protein_id="mrp2",
                evidence_source_id="unit_test_measurement",
                experimental_system="primary human hepatocytes",
                canalicular_surface_copies=4_000.0,
                subapical_endosome_copies=12_000.0,
            ),
        }
        activity = activity_from_lifecycle_states(lifecycle, reference)
        self.assertAlmostEqual(activity["bsep"], 0.25)
        self.assertAlmostEqual(activity["mrp2"], 0.5)

        baseline = build_transport_network(1.0)
        localized = build_transport_network(
            1.0,
            transporter_lifecycle=lifecycle,
            reference_surface_copies=reference,
        )
        counts = seed_transport()
        counts["bile_cyto"] = 1_000.0
        counts["bilirubin_cyto"] = 1_000.0
        baseline_rate = next(r for r in baseline.reactions if r.id == "bsep_export").propensity(counts, 1.0)
        localized_rate = next(r for r in localized.reactions if r.id == "bsep_export").propensity(counts, 1.0)
        baseline_mrp2_rate = next(r for r in baseline.reactions if r.id == "mrp2_export").propensity(counts, 1.0)
        localized_mrp2_rate = next(r for r in localized.reactions if r.id == "mrp2_export").propensity(counts, 1.0)
        self.assertAlmostEqual(localized_rate / baseline_rate, 0.25)
        self.assertAlmostEqual(localized_mrp2_rate / baseline_mrp2_rate, 0.5)

    def test_missing_surface_reference_or_overdraw_is_rejected(self):
        state = TransporterLifecycleState(
            protein_id="bsep",
            evidence_source_id="unit_test_measurement",
            experimental_system="primary human hepatocytes",
            golgi_copies=100.0,
        )
        with self.assertRaises(ValueError):
            activity_from_lifecycle_states({"bsep": state}, {})
        with self.assertRaises(ValueError):
            apply_observed_transfers(
                state,
                (ObservedTraffickingTransfer("golgi_copies", "canalicular_surface_copies", 101.0, "unit_test_transfer"),),
            )
        with self.assertRaises(ValueError):
            build_transport_network(1.0, transporter_lifecycle={"bsep": state})


if __name__ == "__main__":
    unittest.main()
