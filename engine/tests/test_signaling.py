from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.signaling import (
    FASTED,
    FED,
    HormoneState,
    SIGNALING_SOURCES,
    run_glycogen_control,
)


class SignalingTests(unittest.TestCase):
    def test_fed_state_stores_glycogen(self):
        out = run_glycogen_control(FED, 30.0, EngineRng(1), glycogen=5000.0, glucose_cyto=5000.0)
        self.assertGreater(out["glycogen"], 5000.0)          # insulin -> storage
        self.assertLess(out["glucose_cyto"], 5000.0)
        self.assertIn("hepatic_glucose_control", SIGNALING_SOURCES)

    def test_fasted_state_mobilizes_and_exports_glucose(self):
        out = run_glycogen_control(FASTED, 30.0, EngineRng(1), glycogen=5000.0, glucose_cyto=5000.0)
        self.assertLess(out["glycogen"], 5000.0)             # glucagon -> breakdown
        self.assertGreater(out["glucose_blood"], 0.0)        # glucose exported to blood

    def test_ampk_drives_catabolism_without_glucagon(self):
        # Energy stress (AMPK) mobilizes glycogen even with no glucagon and no insulin.
        stressed = HormoneState(insulin=0.0, glucagon=0.0, ampk=0.8)
        out = run_glycogen_control(stressed, 30.0, EngineRng(1), glycogen=5000.0, glucose_cyto=1000.0)
        self.assertLess(out["glycogen"], 5000.0)


if __name__ == "__main__":
    unittest.main()
