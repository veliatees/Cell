from dataclasses import replace
import unittest

from cell_engine.cargo.routing import build_hepatocyte_route_graph, route_cargo_packets, success_probability
from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.core.state import CargoPacket
from cell_engine.io.snapshots import build_snapshot
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation.invariants import validate_state


class CargoRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)
        self.graph = build_hepatocyte_route_graph()

    def test_initial_state_contains_named_cargo_packets(self) -> None:
        species = {packet.species for packet in self.state.cargo_packets}
        self.assertIn("albumin", species)
        self.assertIn("canalicular_bile_transporter", species)
        self.assertIn("lysosomal_hydrolase", species)
        self.assertIn("misfolded_secretory_protein", species)
        self.assertTrue(all(packet.state == "in_transit" for packet in self.state.cargo_packets))

    def test_success_probability_depends_on_energy_stress_quality_and_cytoskeleton(self) -> None:
        albumin = next(packet for packet in self.state.cargo_packets if packet.species == "albumin")
        edge = self.graph.edge("golgi", "sinusoidal_face")
        albumin_at_golgi = replace(albumin, current_location="golgi", route_index=2)
        healthy_p = success_probability(albumin_at_golgi, edge, self.state)

        stressed_pools = {
            **self.state.pools,
            "ATP": replace(self.state.pools["ATP"], value=0.12),
        }
        stressed_organelles = {
            **self.state.organelles,
            "cytoskeleton": replace(self.state.organelles["cytoskeleton"], health=0.25),
        }
        stressed_state = replace(
            self.state,
            pools=stressed_pools,
            organelles=stressed_organelles,
            stress={**self.state.stress, "energy": 1.0, "trafficking": 1.0, "membrane": 0.8},
        )
        damaged_packet = replace(albumin_at_golgi, quality_score=0.30)
        stressed_p = success_probability(damaged_packet, edge, stressed_state)

        self.assertGreater(healthy_p, stressed_p)
        self.assertGreater(healthy_p, 0.45)
        self.assertLess(stressed_p, 0.12)

    def test_step_cell_routes_packets_without_guaranteed_delivery(self) -> None:
        next_state = step_cell(self.definition, self.state, 240.0, rng=EngineRng(4))
        validate_state(self.definition, next_state)
        before = {packet.id: packet for packet in self.state.cargo_packets}
        changed_count = sum(
            1
            for packet in next_state.cargo_packets
            if packet.current_location != before[packet.id].current_location or packet.state != before[packet.id].state
        )
        self.assertGreaterEqual(changed_count, 1)
        self.assertTrue(any(packet.state != "delivered" for packet in next_state.cargo_packets))

    def test_stressed_low_quality_packet_can_be_retained_degraded_misrouted_or_lost(self) -> None:
        low_quality = CargoPacket(
            id="cargo_bad_albumin_test",
            species="albumin",
            origin_compartment="rough_er",
            target_compartment="sinusoidal_face",
            current_location="golgi",
            route_plan=("rough_er", "er_quality_control", "golgi", "sinusoidal_face"),
            route_index=2,
            quality_score=0.05,
            folding_state="unstable",
            glycosylation_state="poor",
            age_s=1200.0,
            energy_cost_atp=0.08,
            motor_dependency=True,
            membrane_side_target="sinusoidal",
            state="in_transit",
        )
        stressed_state = replace(
            self.state,
            cargo_packets=(low_quality,),
            pools={**self.state.pools, "ATP": replace(self.state.pools["ATP"], value=0.05)},
            organelles={**self.state.organelles, "cytoskeleton": replace(self.state.organelles["cytoskeleton"], health=0.1)},
            stress={**self.state.stress, "energy": 1.0, "trafficking": 1.0, "proteotoxic": 1.0, "membrane": 1.0},
        )
        routed = route_cargo_packets(stressed_state, route_graph=self.graph, dt_s=1800.0, rng=EngineRng(1))
        packet = routed.packets[0]
        self.assertIn(packet.state, {"retained", "degraded", "misrouted", "lost"})
        self.assertTrue(packet.fate_reason)
        self.assertEqual(len(routed.events), 1)

    def test_snapshot_exposes_cargo_packets_for_the_ui(self) -> None:
        next_state = step_cell(self.definition, self.state, 60.0, rng=EngineRng(9))
        snapshot = build_snapshot(self.definition, next_state)
        packets = snapshot["state"]["cargo_packets"]
        self.assertIsInstance(packets, list)
        self.assertGreaterEqual(len(packets), 4)
        self.assertIn("route_plan", packets[0])
        self.assertIn("fate_reason", packets[0])


if __name__ == "__main__":
    unittest.main()
