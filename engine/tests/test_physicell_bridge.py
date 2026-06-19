from dataclasses import replace
import unittest

from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.multicell import build_microenvironment_fields, build_population_from_state, cell_state_to_agent
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state


class PhysiCellBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = step_cell(self.definition, initial_hepatocyte_state(self.definition), 120.0, rng=EngineRng(3))

    def test_microenvironment_fields_have_units_and_transport_parameters(self) -> None:
        fields = build_microenvironment_fields()
        ids = {field.id for field in fields}
        self.assertIn("oxygen", ids)
        self.assertIn("glucose", ids)
        self.assertIn("xenobiotic", ids)
        self.assertTrue(all(field.unit for field in fields))
        self.assertTrue(all(field.diffusion_coefficient > 0 for field in fields))

    def test_single_cell_state_maps_to_agent_phenotype(self) -> None:
        agent = cell_state_to_agent(self.state, id="h0", position_um=(0.0, 0.0, 0.0))
        self.assertEqual(agent.cell_type, "hepatocyte")
        self.assertEqual(agent.intracellular_state_ref, self.state.definition_id)
        self.assertGreaterEqual(agent.viability, 0.0)
        self.assertLessEqual(agent.viability, 1.0)
        self.assertIn("oxygen", agent.uptake)
        self.assertIn("waste", agent.secretion)

    def test_low_energy_agent_has_lower_viability_and_higher_glucose_uptake(self) -> None:
        low = replace(
            self.state,
            pools={
                **self.state.pools,
                "ATP": replace(self.state.pools["ATP"], value=0.08),
                "ADP": replace(self.state.pools["ADP"], value=0.82),
                "AMP": replace(self.state.pools["AMP"], value=0.10),
            },
            stress={**self.state.stress, "energy": 1.0},
        )
        healthy_agent = cell_state_to_agent(self.state, id="healthy", position_um=(0.0, 0.0, 0.0))
        low_agent = cell_state_to_agent(low, id="low", position_um=(0.0, 0.0, 0.0))
        self.assertLess(low_agent.viability, healthy_agent.viability)
        self.assertGreater(low_agent.uptake["glucose"], healthy_agent.uptake["glucose"])

    def test_builds_100_cell_population_export(self) -> None:
        population = build_population_from_state(self.state, count=100)
        data = population.to_dict()
        self.assertEqual(len(population.agents), 100)
        self.assertEqual(len({agent.id for agent in population.agents}), 100)
        self.assertEqual(data["agents"][0]["cell_type"], "hepatocyte")
        self.assertGreaterEqual(len(data["microenvironment"]), 5)


if __name__ == "__main__":
    unittest.main()

