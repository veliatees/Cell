from __future__ import annotations

import unittest
from dataclasses import replace
from math import sqrt

from cell_engine.quantitative.hepatocyte_counts import CELL_VOLUME_UM3, ORGANELLE_BY_ID
from cell_engine.quantitative.organelle_placement import (
    PLACEMENT_SOURCES,
    _fits_in_cell,
    build_organelle_placement,
    organelle_placement_snapshot,
    truncated_octahedron_scale_um,
    validate_organelle_placement,
)


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sqrt(sum((a[k] - b[k]) ** 2 for k in range(3)))


class OrganelleCountTest(unittest.TestCase):
    def test_discrete_bodies_match_declared_cross_species_proxy_counts(self) -> None:
        placement = build_organelle_placement(seed=3)
        # nucleus (1), mitochondria (1000), lysosomes (400), peroxisomes (500).
        self.assertEqual(placement.body_count_by_organelle["nucleus"], 1)
        for organelle_id in ("mitochondria", "lysosomes", "peroxisomes"):
            expected = int(round(ORGANELLE_BY_ID[organelle_id].count_typical))
            self.assertEqual(
                placement.body_count_by_organelle[organelle_id],
                expected,
                f"{organelle_id} population must equal its declared proxy count",
            )

    def test_all_bodies_were_packed(self) -> None:
        placement = build_organelle_placement(seed=3)
        shortfall = [b for b in placement.blockers if "could not be packed" in b]
        self.assertEqual(shortfall, [], "every declared proxy body must fit without overlap")


class SolidBodyTest(unittest.TestCase):
    """The load-bearing physical guarantee: nothing interpenetrates."""

    def setUp(self) -> None:
        self.placement = build_organelle_placement(seed=7)

    def test_no_body_overlaps_another(self) -> None:
        bodies = self.placement.bodies
        for i in range(len(bodies)):
            a = bodies[i]
            for j in range(i + 1, len(bodies)):
                b = bodies[j]
                self.assertGreaterEqual(
                    _distance(a.center_um, b.center_um) + 1e-9,
                    a.radius_um + b.radius_um,
                    f"{a.organelle_id}#{a.index} overlaps {b.organelle_id}#{b.index}",
                )

    def test_every_body_is_inside_the_cell_polyhedron(self) -> None:
        # Bodies fill the volume-matched truncated-octahedron cell shape (the
        # rendered membrane) and stay fully inside it in every direction.
        scale = truncated_octahedron_scale_um(self.placement.cell_volume_um3)
        for b in self.placement.bodies:
            self.assertTrue(
                _fits_in_cell(b.center_um, scale, b.radius_um),
                f"{b.organelle_id}#{b.index} pokes outside the membrane polyhedron",
            )

    def test_bodies_fill_the_polyhedral_corners(self) -> None:
        # Organelles must reach beyond the inscribed equivalent sphere toward the
        # polyhedron vertices, i.e. they touch the membrane, not just a ball.
        sphere_r = self.placement.cell_envelope_radius_um
        reach = max(_distance(b.center_um, (0.0, 0.0, 0.0)) for b in self.placement.bodies)
        self.assertGreater(reach, sphere_r)

    def test_no_body_enters_the_nucleus(self) -> None:
        rn = self.placement.nucleus_radius_um
        for b in self.placement.bodies:
            if b.organelle_id == "nucleus":
                continue
            self.assertGreaterEqual(
                _distance(b.center_um, (0.0, 0.0, 0.0)) + 1e-9,
                rn + b.radius_um,
                f"{b.organelle_id}#{b.index} intrudes into the nucleus",
            )


class VolumeConsistencyTest(unittest.TestCase):
    def test_body_volume_matches_declared_cross_species_proxy_fraction(self) -> None:
        placement = build_organelle_placement(seed=1)
        for organelle_id in ("mitochondria", "lysosomes", "peroxisomes"):
            organelle = ORGANELLE_BY_ID[organelle_id]
            proxy_total = (organelle.volume_fraction_pct / 100.0) * CELL_VOLUME_UM3
            placed_total = sum(
                b.volume_um3 for b in placement.bodies if b.organelle_id == organelle_id
            )
            self.assertAlmostEqual(placed_total, proxy_total, places=6)

    def test_total_discrete_volume_fits_in_the_cell(self) -> None:
        placement = build_organelle_placement(seed=1)
        self.assertLess(placement.placed_body_volume_um3, placement.cell_volume_um3)
        self.assertGreater(placement.discrete_volume_fraction_pct, 0.0)


class DeterminismTest(unittest.TestCase):
    def test_same_seed_reproduces_placement(self) -> None:
        self.assertEqual(
            build_organelle_placement(seed=42).to_dict(),
            build_organelle_placement(seed=42).to_dict(),
        )

    def test_different_seed_changes_placement(self) -> None:
        a = build_organelle_placement(seed=1)
        b = build_organelle_placement(seed=2)
        self.assertNotEqual(
            [body.center_um for body in a.bodies],
            [body.center_um for body in b.bodies],
        )


class FailClosedHonestyTest(unittest.TestCase):
    def test_mixed_species_proxy_has_zero_healthy_phh_authority(self) -> None:
        placement = build_organelle_placement(seed=0)
        self.assertEqual(placement.version, "organelle_placement_v2")
        self.assertEqual(
            placement.status,
            "mixed_species_seeded_organelle_geometry_proxy",
        )
        self.assertEqual(
            placement.runtime_geometry_role,
            "engine_collision_and_renderer_proxy_only",
        )
        self.assertTrue(placement.uses_cross_species_organelle_parameters)
        self.assertFalse(placement.healthy_phh_biological_authority)
        self.assertFalse(placement.quantitative_contact_force_authority)
        self.assertEqual(placement.healthy_phh_discrete_count_parameter_count, 0)
        self.assertEqual(
            placement.healthy_phh_discrete_volume_fraction_parameter_count,
            0,
        )
        self.assertEqual(placement.cross_species_proxy_body_count, 1901)
        self.assertEqual(placement.human_aggregate_region_count, 1)
        self.assertEqual(placement.measured_per_organelle_coordinate_count, 0)
        self.assertEqual(placement.donor_resolved_mesh_count, 0)
        validate_organelle_placement(placement)

    def test_network_organelles_are_regions_not_spheres(self) -> None:
        placement = build_organelle_placement(seed=0)
        region_ids = {r.organelle_id for r in placement.regions}
        for organelle_id in ("rough_er", "smooth_er", "golgi", "glycogen", "lipid_droplets"):
            self.assertIn(organelle_id, region_ids)
            self.assertNotIn(
                organelle_id,
                placement.body_count_by_organelle,
                f"{organelle_id} has no discrete count and must not be faked as spheres",
            )
        for region in placement.regions:
            self.assertFalse(region.discrete)

    def test_ribosomes_are_reported_unplaced(self) -> None:
        placement = build_organelle_placement(seed=0)
        self.assertIn("ribosomes", {u.organelle_id for u in placement.unplaced})

    def test_positions_are_not_claimed_as_measured(self) -> None:
        placement = build_organelle_placement(seed=0)
        self.assertIn(
            "exact per-organelle coordinates",
            placement.not_biologically_identified,
        )
        self.assertTrue(placement.blockers)
        self.assertEqual(set(placement.source_ids), set(PLACEMENT_SOURCES))
        self.assertEqual(len(placement.source_ids), len(PLACEMENT_SOURCES))

    def test_validator_rejects_promotion_to_healthy_phh_authority(self) -> None:
        placement = build_organelle_placement(seed=0)
        with self.assertRaisesRegex(ValueError, "gained healthy-PHH authority"):
            validate_organelle_placement(
                replace(placement, healthy_phh_biological_authority=True)
            )

    def test_validator_rejects_an_incomplete_source_ledger(self) -> None:
        placement = build_organelle_placement(seed=0)
        with self.assertRaisesRegex(ValueError, "source ledger is incomplete"):
            validate_organelle_placement(
                replace(placement, source_ids=placement.source_ids[:-1])
            )


class SnapshotTest(unittest.TestCase):
    def test_snapshot_is_json_ready_and_round_trips(self) -> None:
        import json

        payload = organelle_placement_snapshot(seed=5)
        restored = json.loads(json.dumps(payload))
        self.assertEqual(restored["version"], "organelle_placement_v2")
        self.assertEqual(len(restored["bodies"]), len(payload["bodies"]))
        self.assertFalse(restored["healthy_phh_biological_authority"])


if __name__ == "__main__":
    unittest.main()
