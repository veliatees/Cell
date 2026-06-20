from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.transport import (
    TRANSPORT_SOURCES,
    build_transport_network,
    run_transport,
)


class TransportTests(unittest.TestCase):
    def test_network_has_real_transporters(self):
        ids = {r.id for r in build_transport_network(1.0).reactions}
        for t in ("glut2_uptake", "ntcp_uptake", "oatp_uptake", "na_k_atpase", "bsep_export", "mrp2_export"):
            self.assertIn(t, ids)
        self.assertIn("bile_formation", TRANSPORT_SOURCES)

    def test_vectorial_bile_flux(self):
        # Bile salts move blood -> cytosol -> canaliculus (vectorial secretion).
        out = run_transport(40.0, EngineRng(1))
        self.assertLess(out["bile_blood"], 5000.0)          # taken up from blood
        self.assertGreater(out["bile_canaliculus"], 0.0)    # exported to bile
        self.assertGreater(out["bilirubin_canaliculus"], 0.0)
        for v in out.values():
            self.assertGreaterEqual(v, 0.0)

    def test_bsep_defect_causes_intracellular_retention(self):
        # Without BSEP, bile salts are taken up but cannot be exported -> they
        # accumulate inside the cell (cholestasis), reaching the canaliculus far less.
        healthy = run_transport(40.0, EngineRng(2), bsep_active=True)
        defect = run_transport(40.0, EngineRng(2), bsep_active=False)
        self.assertGreater(defect["bile_cyto"], healthy["bile_cyto"])
        self.assertLess(defect["bile_canaliculus"], healthy["bile_canaliculus"])


if __name__ == "__main__":
    unittest.main()
