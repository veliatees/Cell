from __future__ import annotations

import unittest

from cell_engine.stochastic.reactions import ReactionNetwork, mass_action
from cell_engine.stochastic.spatial import (
    CYTOPLASMIC_DIFFUSION_UM2_PER_S,
    cfl_limit_dt,
    network_voxel_reaction,
    react_diffuse,
    tag_reaction_quantity,
    uniform_field,
)


class NetworkVoxelReactionTests(unittest.TestCase):
    def test_callback_matches_network_rate(self):
        # A first-order maintenance reaction ATP -> ADP gives ddt[ATP] = -k*ATP.
        net = ReactionNetwork(("ATP", "ADP"), (mass_action("maint", {"ATP": 1}, {"ADP": 1}, 0.1),), 1.0e-15)
        reaction = network_voxel_reaction(net, 1.0e-15)
        self.assertEqual(getattr(reaction, "quantity"), "molecule_count")
        ddt = reaction(0, {"ATP": 1000.0, "ADP": 0.0})
        self.assertAlmostEqual(ddt["ATP"], -100.0)   # -k*ATP
        self.assertAlmostEqual(ddt["ADP"], +100.0)

    def test_count_reaction_rejects_concentration_field(self):
        # Network propensities consume molecule counts, not mM concentrations.
        # The default uniform field is concentration_mM, so this is a contract
        # error rather than a silent unit mix.
        net = ReactionNetwork(("ATP", "ADP"), (mass_action("maint", {"ATP": 1}, {"ADP": 1}, 0.1),), 1.0e-15)
        field = uniform_field(("ATP", "ADP"), n=2, dx_um=1.0, value=100.0)
        with self.assertRaisesRegex(ValueError, "molecule_count"):
            react_diffuse(
                field,
                diffusion={"ATP": 0.0, "ADP": 0.0},
                dt_s=0.1,
                steps=1,
                reaction=network_voxel_reaction(net, 1.0e-15),
            )

    def test_count_reaction_runs_on_molecule_count_field(self):
        # Method-only values: verifies ReactionNetwork count semantics are allowed
        # on a molecule_count field without adding biological assumptions.
        net = ReactionNetwork(("ATP", "ADP"), (mass_action("maint", {"ATP": 1}, {"ADP": 1}, 0.1),), 1.0e-15)
        field = uniform_field(("ATP", "ADP"), n=1, dx_um=1.0, value=0.0, quantity="molecule_count")
        field = field.__class__(
            field.species,
            field.dx_um,
            {"ATP": (100.0,), "ADP": (0.0,)},
            quantity="molecule_count",
        )
        out = react_diffuse(
            field,
            diffusion={"ATP": 0.0, "ADP": 0.0},
            dt_s=1.0,
            steps=1,
            reaction=network_voxel_reaction(net, 1.0e-15),
        )
        self.assertEqual(out.quantity, "molecule_count")
        self.assertAlmostEqual(out.profile("ATP")[0], 90.0)
        self.assertAlmostEqual(out.profile("ADP")[0], 10.0)

    def test_spatial_atp_microdomain_from_real_network(self):
        # The real engine network drives the spatial field: ATP is produced at the
        # mitochondria voxel and consumed everywhere. This field is explicitly in
        # molecule counts so ReactionNetwork propensities receive their native
        # count units; dx_um is a numerical-method grid spacing in this test.
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

        reaction = tag_reaction_quantity(reaction, "molecule_count")
        field = uniform_field(("ATP", "ADP"), n, dx_um=1.0, value=0.0, quantity="molecule_count")
        field = field.__class__(field.species, field.dx_um,
                                {"ATP": tuple(0.0 for _ in range(n)),
                                 "ADP": tuple(100.0 for _ in range(n))},
                                quantity="molecule_count")
        d = CYTOPLASMIC_DIFFUSION_UM2_PER_S["ATP"]   # 150 um^2/s, grounded
        dt = 0.5 * cfl_limit_dt({"ATP": d, "ADP": d}, 1.0)
        out = react_diffuse(field, diffusion={"ATP": d, "ADP": d}, dt_s=dt, steps=20000, reaction=reaction)
        self.assertEqual(out.quantity, "molecule_count")
        atp = out.profile("ATP")
        self.assertEqual(max(range(n), key=lambda i: atp[i]), mito)   # peak at the source
        self.assertGreater(atp[mito], atp[mito + 10])                  # falls with distance
        self.assertGreater(atp[mito], 0.0)


if __name__ == "__main__":
    unittest.main()
