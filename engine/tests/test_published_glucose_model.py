from __future__ import annotations

import unittest

from cell_engine.io.sbml import RoadRunnerAdapter
from cell_engine.quantitative.published_glucose_model import (
    EXECUTABLE_MODEL_SHA256,
    OFFICIAL_MODEL_SHA256,
    audited_model_manifests,
    build_published_hepatic_glucose_context,
    generate_runtime_validation,
    project_published_hormone_response,
    validate_published_hepatic_glucose_context,
)


class PublishedHepaticGlucoseModelTests(unittest.TestCase):
    def test_official_and_executable_sbml_artifacts_are_not_conflated(self) -> None:
        official, executable = audited_model_manifests()
        self.assertEqual(official.sha256, OFFICIAL_MODEL_SHA256)
        self.assertEqual(executable.sha256, EXECUTABLE_MODEL_SHA256)
        self.assertEqual(len(official.reaction_ids), 36)
        self.assertEqual(len(official.reactions_with_kinetic_law), 0)
        self.assertEqual(official.element_counts["species"], 52)
        self.assertEqual(len(executable.reaction_ids), 36)
        self.assertEqual(len(executable.reactions_with_kinetic_law), 36)
        self.assertEqual(executable.element_counts["species"], 49)
        self.assertEqual(executable.element_counts["parameter"], 258)

    def test_published_hormone_equations_reproduce_reported_endpoints(self) -> None:
        low = project_published_hormone_response(2.0)
        high = project_published_hormone_response(14.0)
        self.assertAlmostEqual(low.phosphorylated_fraction, 0.940877644659)
        self.assertAlmostEqual(high.phosphorylated_fraction, 0.050997010304)
        self.assertEqual(low.regulated_enzymes, ("GS", "GP", "PFK2", "FBP2", "PK", "PDH"))
        self.assertIn("not_measured", low.evidence)

    def test_only_profile_with_sourced_glucose_boundary_gets_a_prediction(self) -> None:
        postabsorptive = build_published_hepatic_glucose_context("postabsorptive")
        validate_published_hepatic_glucose_context(postabsorptive)
        self.assertIsNotNone(postabsorptive.profile_projection)
        self.assertIsNotNone(postabsorptive.shadow_flux_prediction)
        self.assertEqual(postabsorptive.shadow_flux_prediction["glucose_mM"], 4.75)
        self.assertEqual(postabsorptive.shadow_flux_prediction["glycogen_mM"], 229.0)
        for profile_id in ("fed_peak", "prolonged_fasted"):
            context = build_published_hepatic_glucose_context(profile_id)
            validate_published_hepatic_glucose_context(context)
            self.assertIsNone(context.profile_projection)
            self.assertIsNone(context.shadow_flux_prediction)

    def test_incomplete_publication_reproduction_fails_closed(self) -> None:
        context = build_published_hepatic_glucose_context("postabsorptive")
        validation = context.runtime_validation
        self.assertEqual(validation["benchmark_pass_count"], 2)
        self.assertEqual(validation["benchmark_total_count"], 5)
        self.assertFalse(validation["publication_reproduction_passed"])
        self.assertTrue(validation["technical_equation_parity"]["passed"])
        self.assertFalse(context.gate.authoritative_rate_coupling_enabled)
        self.assertFalse(context.gate.predictive_ready)
        self.assertEqual(context.model_role, "non_authoritative_shadow_prediction")

    @unittest.skipUnless(RoadRunnerAdapter.detect().available, "libRoadRunner optional dependency not installed")
    def test_pinned_runtime_regeneration_matches_committed_benchmarks(self) -> None:
        regenerated = generate_runtime_validation()
        self.assertEqual(regenerated["benchmark_pass_count"], 2)
        predicted = {item["id"]: item["predicted"] for item in regenerated["benchmarks"]}
        self.assertAlmostEqual(predicted["hgp_hgu_switch"], 7.143741299282, places=7)
        self.assertAlmostEqual(predicted["gng_glycolysis_switch"], 8.304155655787, places=7)
        self.assertAlmostEqual(predicted["glycogenolysis_glycogenesis_switch"], 5.433978295769, places=7)


if __name__ == "__main__":
    unittest.main()
