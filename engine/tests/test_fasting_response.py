from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.signaling import FED, FASTED
from cell_engine.stochastic.fasting_response import (
    blood_glucose,
    build_fasting_fuel_response,
    ketone_output,
    run_fasting_response,
)


class FastingResponseTests(unittest.TestCase):
    def test_fasted_raises_both_glucose_and_ketones(self):
        """The integrated fasting program: a fasted liver dumps glucose AND ketones;
        a fed liver does neither."""
        fed = run_fasting_response(FED, 150.0, EngineRng(31))
        fasted = run_fasting_response(FASTED, 150.0, EngineRng(31))
        self.assertLess(blood_glucose(fed), 50.0)
        self.assertLess(ketone_output(fed), 50.0)
        self.assertGreater(blood_glucose(fasted), 1000.0)
        self.assertGreater(ketone_output(fasted), 500.0)

    def test_fed_stores_glucose_as_glycogen(self):
        """Fed (insulin) is anabolic: cytosolic glucose is stored as glycogen, not
        exported."""
        out = run_fasting_response(FED, 150.0, EngineRng(32), glycogen=4000.0, glucose_cyto=1000.0)
        self.assertGreater(out["glycogen"], 4000.0)   # glucose stored
        self.assertLess(blood_glucose(out), 50.0)      # not exported

    def test_blood_glucose_stacks_glycogenolysis_and_gluconeogenesis(self):
        """Shared glucose_blood means both sources add to output: fasted blood
        glucose exceeds the glycogen+free-glucose store alone, so gluconeogenesis
        contributed on top."""
        glycogen, glucose_cyto = 4000.0, 1000.0
        out = run_fasting_response(FASTED, 150.0, EngineRng(33),
                                   glycogen=glycogen, glucose_cyto=glucose_cyto, lactate=5000.0)
        self.assertGreater(blood_glucose(out), 1.2 * (glycogen + glucose_cyto))

    def test_composition_is_the_union_of_three_pathways(self):
        net = build_fasting_fuel_response(FASTED)
        # glucose_blood shared by glycogen export + gluconeogenesis export; redox shared.
        self.assertIn("glucose_blood", net.species)
        self.assertIn("beta_hydroxybutyrate", net.species)
        self.assertIn("glycogen", net.species)
        ids = {r.id for r in net.reactions}
        self.assertIn("hepatic_glucose_output", ids)  # gluconeogenesis/GLUT2
        self.assertIn("glucose_export", ids)          # glycogenolysis glucose_cyto->blood
        self.assertIn("glycogen_breakdown", ids)      # glycogenolysis
        self.assertIn("hmgcs2", ids)                  # ketogenesis


if __name__ == "__main__":
    unittest.main()
