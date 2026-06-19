from dataclasses import replace
import unittest

from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation.invariants import validate_state


class HepatocyteMetabolismTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)

    def test_metabolism_emits_distinct_process_fluxes(self) -> None:
        next_state = step_cell(self.definition, self.state, 600.0, rng=EngineRng(3))
        validate_state(self.definition, next_state)
        fluxes = {flux.id: flux for flux in next_state.metabolic_fluxes}
        for id in [
            "glycolysis",
            "mitochondrial-oxidation",
            "beta-oxidation",
            "urea-cycle",
            "detox",
            "bile-export",
            "maintenance",
        ]:
            self.assertIn(id, fluxes)
            self.assertGreaterEqual(fluxes[id].value, 0.0)
        self.assertEqual(fluxes["mitochondrial-oxidation"].produced_by, "mitochondria")
        self.assertEqual(fluxes["detox"].produced_by, "smooth_er")
        self.assertEqual(fluxes["bile-export"].produced_by, "plasma_membrane_golgi")

    def test_adenylate_pool_is_conserved(self) -> None:
        next_state = step_cell(self.definition, self.state, 1200.0, rng=EngineRng(4))
        total = sum(next_state.pools[id].value for id in ("ATP", "ADP", "AMP"))
        self.assertAlmostEqual(total, 1.0, places=8)

    def test_low_energy_mobilizes_glycogen(self) -> None:
        low_energy = replace(
            self.state,
            pools={
                **self.state.pools,
                "ATP": replace(self.state.pools["ATP"], value=0.18),
                "ADP": replace(self.state.pools["ADP"], value=0.72),
                "AMP": replace(self.state.pools["AMP"], value=0.10),
            },
        )
        next_state = step_cell(self.definition, low_energy, 900.0, rng=EngineRng(5))
        fluxes = {flux.id: flux for flux in next_state.metabolic_fluxes}
        self.assertGreater(fluxes["glycogen-breakdown"].value, fluxes["glycogen-storage"].value)
        self.assertLess(next_state.pools["glycogen"].value, low_energy.pools["glycogen"].value)

    def test_high_detox_load_consumes_redox_and_adds_ros_cost(self) -> None:
        loaded = replace(
            self.state,
            pools={**self.state.pools, "xenobiotic": replace(self.state.pools["xenobiotic"], value=0.9)},
        )
        next_state = step_cell(self.definition, loaded, 1800.0, rng=EngineRng(6))
        self.assertLess(next_state.pools["NADPH"].value, loaded.pools["NADPH"].value)
        self.assertLess(next_state.pools["GSH"].value, loaded.pools["GSH"].value)
        self.assertGreater(next_state.pools["GSSG"].value, loaded.pools["GSSG"].value)
        self.assertGreater(next_state.pools["ROS"].value, loaded.pools["ROS"].value)
        self.assertGreater(next_state.pools["detoxified_xenobiotic"].value, loaded.pools["detoxified_xenobiotic"].value)

    def test_local_atp_lags_global_pool_by_transport_delay(self) -> None:
        low_global_atp = replace(
            self.state,
            pools={
                **self.state.pools,
                "ATP": replace(self.state.pools["ATP"], value=0.20),
                "ADP": replace(self.state.pools["ADP"], value=0.70),
                "AMP": replace(self.state.pools["AMP"], value=0.10),
            },
        )
        next_state = step_cell(self.definition, low_global_atp, 1.0, rng=EngineRng(7))
        self.assertGreater(next_state.organelles["plasma_membrane"].transport_delay_s, next_state.organelles["mitochondria"].transport_delay_s)
        self.assertGreater(next_state.organelles["plasma_membrane"].local_atp, next_state.pools["ATP"].value)
        self.assertGreater(next_state.organelles["ribosome"].local_atp, next_state.organelles["mitochondria"].local_atp)


if __name__ == "__main__":
    unittest.main()

