from __future__ import annotations

import unittest

from cell_engine.stochastic.reactions import ReactionNetwork, mass_action
from cell_engine.stochastic.spatial import (
    CYTOPLASMIC_DIFFUSION_UM2_PER_S,
    cfl_limit_dt,
    network_voxel_reaction,
    react_diffuse,
    uniform_field,
)


class NetworkVoxelReactionTests(unittest.TestCase):
    def test_callback_matches_network_rate(self):
        # A first-order maintenance reaction ATP -> ADP gives ddt[ATP] = -k*ATP.
        net = ReactionNetwork(("ATP", "ADP"), (mass_action("maint", {"ATP": 1}, {"ADP": 1}, 0.1),), 1.0e-15)
        reaction = network_voxel_reaction(net, 1.0e-15)
        ddt = reaction(0, {"ATP": 1000.0, "ADP": 0.0})
        self.assertAlmostEqual(ddt["ATP"], -100.0)   # -k*ATP
        self.assertAlmostEqual(ddt["ADP"], +100.0)

    def test_spatial_atp_microdomain_from_real_network(self):
        # The real engine network drives the spatial field: ATP is produced at the
        # mitochondria voxel and consumed everywhere, diffusing at its grounded
        # cytoplasmic coefficient -> a high-ATP microdomain around the source.
        n = 40
        mito = 8
        volume = 1.0e-15
        consume = ReactionNetwork(("ATP", "ADP"), (mass_action("maint", {"ATP": 1}, {"ADP": 1}, 2.0),), volume)
        base = network_voxel_reaction(consume, volume)

        def reaction(i: int, voxel: dict[str, float]) -> dict[str, float]:
            ddt = dict(base(i, voxel))
            if i == mito:  # OXPHOS localized to mitochondria: ADP -> ATP
                prod = 50.0 * voxel.get("ADP", 0.0)
                ddt["ATP"] = ddt.get("ATP", 0.0) + prod
                ddt["ADP"] = ddt.get("ADP", 0.0) - prod
            return ddt

        field = uniform_field(("ATP", "ADP"), n, dx_um=1.0, value=0.0)
        field = field.__class__(field.species, field.dx_um,
                                {"ATP": tuple(0.0 for _ in range(n)),
                                 "ADP": tuple(100.0 for _ in range(n))})
        d = CYTOPLASMIC_DIFFUSION_UM2_PER_S["ATP"]   # 150 um^2/s, grounded
        dt = 0.5 * cfl_limit_dt({"ATP": d, "ADP": d}, 1.0)
        out = react_diffuse(field, diffusion={"ATP": d, "ADP": d}, dt_s=dt, steps=20000, reaction=reaction)
        atp = out.profile("ATP")
        self.assertEqual(max(range(n), key=lambda i: atp[i]), mito)   # peak at the source
        self.assertGreater(atp[mito], atp[mito + 10])                  # falls with distance
        self.assertGreater(atp[mito], 0.0)


if __name__ == "__main__":
    unittest.main()
