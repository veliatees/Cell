from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.apoptosis import (
    APOPTOSIS,
    NECROSIS,
    DeathState,
    StressSignals,
    run_death,
    signals_from_detox,
    signals_from_infection,
    step_death,
)
from cell_engine.stochastic.detox import run_detox
from cell_engine.stochastic.virus import run_infection


class DeathBasicsTests(unittest.TestCase):
    def test_healthy_cell_survives(self):
        healthy = StressSignals(ros01=0.0, energy_charge=0.85, gsh_fraction=1.0)
        final = run_death(healthy, 200.0)
        self.assertTrue(final.alive)

    def test_stress_with_atp_intact_is_apoptosis(self):
        # Strong death drive but ATP preserved -> regulated apoptosis.
        stressed = StressSignals(ros01=0.9, energy_charge=0.7, gsh_fraction=0.0, damage01=0.4)
        final = run_death(stressed, 300.0)
        self.assertEqual(final.mode, APOPTOSIS)

    def test_atp_collapse_is_necrosis(self):
        # Same kind of insult but with ATP collapsed -> necrosis, per the ATP switch.
        collapsed = StressSignals(ros01=0.9, energy_charge=0.15, gsh_fraction=0.0, damage01=0.8)
        final = run_death(collapsed, 300.0)
        self.assertEqual(final.mode, NECROSIS)

    def test_commitment_is_irreversible(self):
        stressed = StressSignals(ros01=0.9, energy_charge=0.7, gsh_fraction=0.0, damage01=0.5)
        committed = run_death(stressed, 300.0)
        self.assertTrue(committed.committed)
        recovered = step_death(committed, StressSignals(), 100.0)
        self.assertEqual(recovered.mode, committed.mode)  # cannot revive or switch mode


class IntegratedDeathTests(unittest.TestCase):
    def test_paracetamol_overdose_is_necrosis(self):
        # Overdose collapses ATP (adduct-driven mitochondrial failure) -> necrosis,
        # which is what paracetamol overdose actually causes.
        therapeutic = run_detox(2000, 60.0, EngineRng(1), gsh=10000.0)
        overdose = run_detox(60000, 60.0, EngineRng(1), gsh=10000.0)

        alive = run_death(signals_from_detox(therapeutic, 10000.0), 300.0)
        dead = run_death(signals_from_detox(overdose, 10000.0), 300.0)

        self.assertTrue(alive.alive, "therapeutic dose should not kill the cell")
        self.assertEqual(dead.mode, NECROSIS, "overdose should die by necrosis, not apoptosis")

    def test_high_viral_load_is_apoptosis(self):
        # Heavy infection with ATP only moderately reduced -> apoptosis.
        infected = run_infection(30, 100.0, EngineRng(4))
        uninfected = run_infection(0, 100.0, EngineRng(4))

        dead = run_death(signals_from_infection(infected), 300.0)
        alive = run_death(signals_from_infection(uninfected), 300.0)

        self.assertEqual(dead.mode, APOPTOSIS, "heavy infection should trigger apoptosis")
        self.assertTrue(alive.alive, "uninfected cell should survive")


if __name__ == "__main__":
    unittest.main()
