import unittest

from cell_engine.ml import (
    BASELINE_HEPATOCYTE_TARGETS,
    CalibrationCandidate,
    CellPolicyEnvironment,
    apply_policy_action,
    evaluate_calibration,
    rank_calibration_candidates,
)
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation import BASELINE_SCENARIO, ENERGY_STARVATION_SCENARIO


class MlEnvironmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)

    def test_policy_environment_observation_contains_engine_state_summary(self) -> None:
        env = CellPolicyEnvironment(self.definition, self.state, dt_s=120.0, episode_steps=4, seed=19)
        observation = env.reset()
        self.assertIn("ATP", observation.pools)
        self.assertIn("energy", observation.stress)
        self.assertIn("mitochondria", observation.organelle_health)

        step = env.step({"glucose_influx": 0.02, "amino_acid_influx": 0.01})
        self.assertIn(step.observation.status, {"healthy", "stressed", "dying"})
        self.assertIn("reward_terms", step.info)
        self.assertIn("membrane_potential_mv", step.observation.membrane)
        self.assertGreater(step.observation.elapsed_s, observation.elapsed_s)

    def test_policy_action_does_not_mutate_cell_definition_or_rules(self) -> None:
        before_definition = self.definition.to_dict()
        env = CellPolicyEnvironment(self.definition, self.state, dt_s=180.0, episode_steps=2, seed=20)
        step = env.step({"glucose_influx": 0.03, "xenobiotic_exposure": 0.04})
        self.assertEqual(self.definition.to_dict(), before_definition)
        self.assertFalse(step.info["rules_mutated"])
        self.assertGreaterEqual(step.state.pools["glucose"].value, 0.0)
        self.assertIn("detox", step.state.stress)

    def test_unrealistic_action_is_clipped_and_penalized(self) -> None:
        application = apply_policy_action(self.state, {"glucose_influx": 0.40, "unknown_magic": 2.0})
        self.assertIn("glucose_influx", application.clipped)
        self.assertIn("unknown_magic", application.unknown)
        self.assertGreater(application.unrealistic_penalty, 1.0)
        self.assertLessEqual(application.applied["glucose_influx"], 0.08)

        safe_env = CellPolicyEnvironment(self.definition, self.state, dt_s=120.0, episode_steps=2, seed=21)
        unsafe_env = CellPolicyEnvironment(self.definition, self.state, dt_s=120.0, episode_steps=2, seed=21)
        safe_reward = safe_env.step({"glucose_influx": 0.02}).reward
        unsafe_reward = unsafe_env.step({"glucose_influx": 0.40, "unknown_magic": 2.0}).reward
        self.assertLess(unsafe_reward, safe_reward)

    def test_calibration_runner_scores_targets_without_using_policy_env(self) -> None:
        run = evaluate_calibration(
            self.definition,
            self.state,
            BASELINE_SCENARIO,
            BASELINE_HEPATOCYTE_TARGETS,
            dt_s=120.0,
            steps=2,
            seed=22,
        )
        self.assertEqual(run.scenario_id, BASELINE_SCENARIO.id)
        self.assertGreater(run.fit_score, 0.0)
        self.assertLessEqual(run.fit_score, 1.0)
        self.assertIn("does_not_mutate_cell_rules", run.provenance)
        self.assertGreaterEqual(len(run.residuals), 3)

    def test_calibration_candidate_ranking_is_separate_from_rl_actions(self) -> None:
        candidates = (
            CalibrationCandidate(id="starved", interventions={"ATP": 0.12, "ADP": 0.78, "AMP": 0.10}),
            CalibrationCandidate(id="supported", interventions={"ATP": 0.72, "ADP": 0.22, "AMP": 0.06}),
        )
        runs = rank_calibration_candidates(
            self.definition,
            self.state,
            ENERGY_STARVATION_SCENARIO,
            BASELINE_HEPATOCYTE_TARGETS,
            candidates,
            dt_s=120.0,
            steps=2,
            seed=23,
        )
        self.assertEqual(len(runs), 2)
        self.assertLessEqual(runs[0].normalized_error, runs[1].normalized_error)
        self.assertEqual({run.candidate_id for run in runs}, {"starved", "supported"})


if __name__ == "__main__":
    unittest.main()
