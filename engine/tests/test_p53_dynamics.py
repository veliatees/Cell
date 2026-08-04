from __future__ import annotations

import json
import unittest

from cell_engine.quantitative.p53_dynamics import (
    MEASURED_PULSE_PERIOD_H,
    P53_DYNAMICS_SOURCES,
    atm_signal,
    build_p53_dynamics,
    p53_dynamics_snapshot,
    simulate_p53_response,
)


class QuiescenceTest(unittest.TestCase):
    def test_undamaged_cell_does_not_pulse(self) -> None:
        r = simulate_p53_response(0.0)
        self.assertEqual(r.n_pulses, 0)
        self.assertLess(r.peak_p53, 0.4)
        self.assertEqual(r.fate, "homeostatic_recovery")

    def test_atm_gate_is_monotone_and_bounded(self) -> None:
        self.assertEqual(atm_signal(0.0), 0.0)
        self.assertGreater(atm_signal(1.0), atm_signal(0.2))
        self.assertLess(atm_signal(100.0), 1.0 + 1e-9)


class DigitalDoseEncodingTest(unittest.TestCase):
    def test_pulse_count_increases_with_dose(self) -> None:
        # Lahav 2004: dose is encoded in the NUMBER of pulses, not their size.
        low = simulate_p53_response(0.4)
        mid = simulate_p53_response(1.5)
        high = simulate_p53_response(3.0)
        self.assertLessEqual(low.n_pulses, mid.n_pulses)
        self.assertLess(mid.n_pulses, high.n_pulses)

    def test_amplitude_is_roughly_fixed_across_dose(self) -> None:
        # Amplitude (peak) is the conserved digital feature once pulsing engages.
        mid = simulate_p53_response(1.5)
        high = simulate_p53_response(3.0)
        self.assertGreater(mid.peak_p53, 1.0)
        self.assertLess(abs(mid.peak_p53 - high.peak_p53), 0.3)

    def test_model_period_matches_measured_5_5h(self) -> None:
        r = simulate_p53_response(5.0)
        self.assertIsNotNone(r.mean_pulse_period_h)
        assert r.mean_pulse_period_h is not None
        self.assertAlmostEqual(r.mean_pulse_period_h, MEASURED_PULSE_PERIOD_H, delta=1.0)


class FateSplitTest(unittest.TestCase):
    def test_pulsed_response_recovers(self) -> None:
        r = simulate_p53_response(1.5)
        self.assertGreater(r.n_pulses, 0)
        self.assertEqual(r.fate, "recovery_after_pulsed_arrest")
        self.assertLess(r.retained_damage, 0.01)

    def test_sustained_p53_drives_senescence(self) -> None:
        # Purvis 2012: sustained p53 (Mdm2 inhibited) -> senescence, not recovery.
        r = simulate_p53_response(0.8, mdm2_inhibited=True)
        self.assertEqual(r.fate, "senescence")

    def test_irreparable_damage_drives_apoptosis(self) -> None:
        r = simulate_p53_response(8.0)
        self.assertEqual(r.fate, "apoptosis")
        self.assertGreater(r.retained_damage, 0.5)


class KnockoutValidationTest(unittest.TestCase):
    def test_p53_knockout_never_pulses(self) -> None:
        r = simulate_p53_response(1.5, p53_functional=False)
        self.assertEqual(r.n_pulses, 0)
        self.assertEqual(r.fate, "proliferation_with_unresolved_damage")

    def test_knockout_retains_more_cumulative_damage_than_wildtype(self) -> None:
        # Free known-biology check: losing p53 leaves the cell with a higher
        # cumulative damage exposure (the substrate for later transformation).
        wt = simulate_p53_response(1.5, p53_functional=True)
        ko = simulate_p53_response(1.5, p53_functional=False)
        self.assertGreater(
            ko.cumulative_damage_exposure, wt.cumulative_damage_exposure
        )


class ContractTest(unittest.TestCase):
    def test_determinism(self) -> None:
        a = simulate_p53_response(1.5)
        b = simulate_p53_response(1.5)
        self.assertEqual(a.cumulative_p53, b.cumulative_p53)
        self.assertEqual(a.n_pulses, b.n_pulses)

    def test_not_a_reaction_transport_authority(self) -> None:
        dyn = build_p53_dynamics()
        self.assertFalse(dyn.is_reaction_transport_authority)

    def test_snapshot_is_json_serialisable_and_populated(self) -> None:
        snap = p53_dynamics_snapshot()
        text = json.dumps(snap)  # must not raise
        self.assertIn("responses", snap)
        self.assertEqual(len(snap["responses"]), 7)
        self.assertGreater(len(snap["source_ids"]), 0)
        for sid in snap["source_ids"]:
            self.assertIn(sid, P53_DYNAMICS_SOURCES)

    def test_honesty_fields_present(self) -> None:
        snap = p53_dynamics_snapshot()
        self.assertTrue(snap["grounded"])
        self.assertTrue(snap["not_grounded"])
        self.assertTrue(snap["blockers"])


if __name__ == "__main__":
    unittest.main()
