from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.secretion import (
    SECRETION_SOURCES,
    AlbuminPulseChaseParameters,
    build_albumin_pulse_chase_network,
    run_albumin_pulse_chase,
)


SOFTWARE_FIXTURE = AlbuminPulseChaseParameters(
    er_to_golgi_half_time_s=60.0,
    golgi_to_medium_half_time_s=120.0,
    source_id="software_fixture",
    experimental_system="software_test_only",
    evidence_role="software_fixture",
)


class SecretionTests(unittest.TestCase):
    def test_network_contains_transport_only(self):
        network = build_albumin_pulse_chase_network(SOFTWARE_FIXTURE)
        self.assertEqual(len(network.reactions), 2)
        self.assertNotIn("amino_acids", network.species)
        self.assertNotIn("albumin_translation", {reaction.id for reaction in network.reactions})
        self.assertEqual(
            network.species,
            (
                "pulse_labeled_proalbumin_er",
                "pulse_labeled_albumin_golgi",
                "pulse_labeled_albumin_medium",
            ),
        )

    def test_software_fixture_is_mass_conserving_and_reaches_medium(self):
        initial = 10_000.0
        counts = run_albumin_pulse_chase(
            1_800.0,
            EngineRng(1),
            parameters=SOFTWARE_FIXTURE,
            initial_labeled_proalbumin=initial,
        )
        self.assertAlmostEqual(sum(counts.values()), initial, delta=0.1)
        self.assertGreater(counts["pulse_labeled_albumin_medium"], 0.0)

    def test_parameters_are_mandatory_and_provenance_gated(self):
        with self.assertRaises(ValueError):
            build_albumin_pulse_chase_network(
                AlbuminPulseChaseParameters(
                    er_to_golgi_half_time_s=0.0,
                    golgi_to_medium_half_time_s=1.0,
                    source_id="software_fixture",
                    experimental_system="software_test_only",
                    evidence_role="software_fixture",
                )
            )
        with self.assertRaises(ValueError):
            build_albumin_pulse_chase_network(
                AlbuminPulseChaseParameters(
                    er_to_golgi_half_time_s=1.0,
                    golgi_to_medium_half_time_s=1.0,
                    source_id="unregistered",
                    experimental_system="human_hepatoma",
                    evidence_role="measured_external_system",
                )
            )
        self.assertIn("lodish1983_hepg2_secretory_transit", SECRETION_SOURCES)


if __name__ == "__main__":
    unittest.main()
