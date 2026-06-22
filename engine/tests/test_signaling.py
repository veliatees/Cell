from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import molecules_from_concentration_mM
from cell_engine.stochastic.signaling import (
    FASTED,
    FED,
    TRANSPORT_VOLUME_L,
    HormoneState,
    SIGNALING_SOURCES,
    run_glycogen_control,
)

# Seed pools on the real molar scale (see run_glycogen_control). Hepatic
# glycogen is a large reserve expressed in glucosyl units (~75 mM); free
# cytosolic glucose is ~5 mM. The seeded molecule counts are the thresholds the
# relational assertions compare against (replacing the old 5000 / 1000 counts).
GLYCOGEN_mM = 75.0
GLUCOSE_CYTO_mM = 5.0


def _molecules(mM: float) -> float:
    return molecules_from_concentration_mM(mM, TRANSPORT_VOLUME_L)


class SignalingTests(unittest.TestCase):
    def test_fed_state_stores_glycogen(self):
        out = run_glycogen_control(FED, 30.0, EngineRng(1),
                                   glycogen_mM=GLYCOGEN_mM, glucose_cyto_mM=GLUCOSE_CYTO_mM)
        self.assertGreater(out["glycogen"], _molecules(GLYCOGEN_mM))      # insulin -> storage
        self.assertLess(out["glucose_cyto"], _molecules(GLUCOSE_CYTO_mM))
        self.assertIn("hepatic_glucose_control", SIGNALING_SOURCES)

    def test_fasted_state_mobilizes_and_exports_glucose(self):
        out = run_glycogen_control(FASTED, 30.0, EngineRng(1),
                                   glycogen_mM=GLYCOGEN_mM, glucose_cyto_mM=GLUCOSE_CYTO_mM)
        self.assertLess(out["glycogen"], _molecules(GLYCOGEN_mM))         # glucagon -> breakdown
        self.assertGreater(out["glucose_blood"], 0.0)                     # glucose exported to blood

    def test_ampk_drives_catabolism_without_glucagon(self):
        # Energy stress (AMPK) mobilizes glycogen even with no glucagon and no insulin.
        stressed = HormoneState(insulin=0.0, glucagon=0.0, ampk=0.8)
        out = run_glycogen_control(stressed, 30.0, EngineRng(1),
                                   glycogen_mM=GLYCOGEN_mM, glucose_cyto_mM=1.0)
        self.assertLess(out["glycogen"], _molecules(GLYCOGEN_mM))


if __name__ == "__main__":
    unittest.main()
