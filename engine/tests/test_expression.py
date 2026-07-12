from __future__ import annotations

import unittest
from dataclasses import replace

from cell_engine.core.expression import (
    CHOLESTASIS_GENE_PROGRAM,
    EXPRESSION_SOURCES,
    GeneExpressionKineticProfile,
    ObservedExpressionUpdate,
    apply_regulatory_observation,
    apply_observed_expression_update,
    build_initial_hepatocyte_expression,
    register_kinetic_profile,
)
from cell_engine.core.random import EngineRng
from cell_engine.processes.gene_expression import step_gene_expression_program
from cell_engine.core.genome import build_reference_hepatocyte_genome
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.processes.metabolism import step_hepatocyte_metabolism
from cell_engine.validation.experiments import BSEP_LOSS_SCENARIO, apply_scenario
from cell_engine.validation.invariants import validate_state


class HepatocyteExpressionTests(unittest.TestCase):
    def test_seven_gene_program_uses_real_genome_loci_and_ploidy(self) -> None:
        genome = build_reference_hepatocyte_genome((2.0, 2.0))
        program = build_initial_hepatocyte_expression(genome)
        self.assertEqual(len(program.genes), 7)
        self.assertEqual(set(program.genes), {definition.symbol for definition in CHOLESTASIS_GENE_PROGRAM})
        self.assertTrue(all(gene.allele_copies == 4.0 for gene in program.genes.values()))
        self.assertEqual(program.engine_mode, "calibration_gated_exact_ssa")
        self.assertEqual(len(program.regulatory_edges), 6)

    def test_missing_gene_specific_kinetics_remain_unknown(self) -> None:
        program = build_initial_hepatocyte_expression(build_reference_hepatocyte_genome())
        cyp7a1 = program.genes["CYP7A1"]
        self.assertEqual(cyp7a1.promoter_state, "unknown")
        self.assertIsNone(cyp7a1.cytoplasmic_mrna_count)
        self.assertIsNone(cyp7a1.total_protein_count)
        self.assertIsNone(cyp7a1.functional_protein_scale)
        self.assertIn("expression_unknown_policy", EXPRESSION_SOURCES)

    def test_transporter_abundance_is_not_claimed_as_surface_count(self) -> None:
        program = build_initial_hepatocyte_expression(build_reference_hepatocyte_genome())
        bsep = program.genes["ABCB11"]
        self.assertGreater(bsep.total_protein_count or 0.0, 0.0)
        self.assertEqual(bsep.functional_protein_scale, 1.0)
        self.assertIn("not a measured surface fraction", bsep.notes)

    def test_observed_updates_can_follow_dna_rna_protein_stages(self) -> None:
        program = build_initial_hepatocyte_expression(build_reference_hepatocyte_genome())
        updates = (
            ObservedExpressionUpdate("evt-1", 1.0, "CYP7A1", "promoter_observed_active", "assay-1", "live locus assay", promoter_state="active", chromatin_state="open", evidence_status="measured"),
            ObservedExpressionUpdate("evt-2", 2.0, "CYP7A1", "pre_mrna_measured", "assay-1", "nascent RNA assay", nuclear_pre_mrna_count=2.0, evidence_status="measured"),
            ObservedExpressionUpdate("evt-3", 3.0, "CYP7A1", "rna_spliced", "assay-1", "nuclear RNA assay", nuclear_mature_mrna_count=2.0, evidence_status="measured"),
            ObservedExpressionUpdate("evt-4", 4.0, "CYP7A1", "rna_exported", "assay-1", "cytoplasmic RNA assay", cytoplasmic_mrna_count=2.0, evidence_status="measured"),
            ObservedExpressionUpdate("evt-5", 5.0, "CYP7A1", "protein_measured", "assay-1", "targeted proteomics", total_protein_count=100.0, evidence_status="measured"),
        )
        for update in updates:
            program = apply_observed_expression_update(program, update)
        gene = program.genes["CYP7A1"]
        self.assertEqual(gene.promoter_state, "active")
        self.assertEqual(gene.nuclear_pre_mrna_count, 2.0)
        self.assertEqual(gene.nuclear_mature_mrna_count, 2.0)
        self.assertEqual(gene.cytoplasmic_mrna_count, 2.0)
        self.assertEqual(gene.total_protein_count, 100.0)
        self.assertEqual([event.event_type for event in program.events], [update.event_type for update in updates])

    def test_updates_require_source_and_do_not_accept_negative_counts(self) -> None:
        program = build_initial_hepatocyte_expression(build_reference_hepatocyte_genome())
        with self.assertRaises(ValueError):
            apply_observed_expression_update(
                program,
                ObservedExpressionUpdate("bad-source", 0.0, "ABCB11", "rna_measured", "", "", cytoplasmic_mrna_count=1.0),
            )
        with self.assertRaises(ValueError):
            apply_observed_expression_update(
                program,
                ObservedExpressionUpdate("bad-count", 0.0, "ABCB11", "rna_measured", "assay", "measurement", cytoplasmic_mrna_count=-1.0),
            )

    def test_bsep_loss_updates_function_without_inventing_variant_or_rna(self) -> None:
        definition = build_hepatocyte_definition()
        state = initial_hepatocyte_state(definition)
        perturbed = apply_scenario(state, BSEP_LOSS_SCENARIO)
        validate_state(definition, perturbed)
        assert perturbed.gene_expression is not None
        bsep = perturbed.gene_expression.genes["ABCB11"]
        self.assertEqual(bsep.functional_protein_scale, 0.0)
        self.assertIsNone(bsep.cytoplasmic_mrna_count)
        self.assertEqual(perturbed.genome.somatic_variants, ())  # type: ignore[union-attr]
        self.assertEqual(perturbed.gene_expression.events[-1].event_type, "functional_perturbation")

    def test_cyp7a1_synthesis_requires_expression_and_explicit_rate(self) -> None:
        definition = build_hepatocyte_definition()
        state = initial_hepatocyte_state(definition)
        uncalibrated = step_hepatocyte_metabolism(state, 3600.0)
        fluxes = {flux.id: flux.value for flux in uncalibrated.fluxes}
        self.assertEqual(fluxes["cyp7a1-bile-acid-synthesis"], 0.0)

        assert state.gene_expression is not None
        expression = apply_observed_expression_update(
            state.gene_expression,
            ObservedExpressionUpdate(
                "cyp7a1-functional-assay",
                0.0,
                "CYP7A1",
                "functional_protein_calibrated",
                "assay-cyp7a1",
                "matched CYP7A1 functional assay",
                functional_protein_scale=1.0,
                evidence_status="calibrated",
            ),
        )
        calibrated = replace(
            state,
            gene_expression=expression,
            model_controls={"cyp7a1_bile_synthesis_rate_per_h": 0.01},
        )
        result = step_hepatocyte_metabolism(calibrated, 3600.0)
        fluxes = {flux.id: flux.value for flux in result.fluxes}
        self.assertGreater(fluxes["cyp7a1-bile-acid-synthesis"], 0.0)
        self.assertLess(result.pools["cholesterol"].value, state.pools["cholesterol"].value)

    def test_regulatory_observation_changes_only_the_observed_layer(self) -> None:
        program = build_initial_hepatocyte_expression(build_reference_hepatocyte_genome())
        observed = apply_regulatory_observation(
            program,
            edge_id="fxr-shp-induction",
            promoter_state="active",
            event_id="phh-fxr-shp-1",
            t_s=48 * 3600.0,
            source_id="phh_bile_acid_gene_regulation",
            evidence="Primary human hepatocyte treatment observation",
        )
        self.assertEqual(observed.genes["NR0B2"].promoter_state, "active")
        self.assertIsNone(observed.genes["NR0B2"].cytoplasmic_mrna_count)
        self.assertEqual(observed.events[-1].event_type, "regulatory_observation")

    def test_exact_ssa_runs_only_for_an_explicitly_allowed_profile(self) -> None:
        program = build_initial_hepatocyte_expression(build_reference_hepatocyte_genome())
        program = apply_observed_expression_update(
            program,
            ObservedExpressionUpdate(
                "fixture-initial-state", 0.0, "CYP7A1", "initial_counts", "synthetic-test",
                "Unit-test initial condition; not a biological parameter set",
                active_allele_count=1.0,
                nuclear_pre_mrna_count=0.0,
                nuclear_mature_mrna_count=0.0,
                cytoplasmic_mrna_count=0.0,
                total_protein_count=0.0,
                evidence_status="unknown",
            ),
        )
        profile = GeneExpressionKineticProfile(
            gene_symbol="CYP7A1",
            promoter_on_rate_per_s=0.2,
            promoter_off_rate_per_s=0.1,
            transcription_rate_per_active_allele_per_s=0.5,
            splicing_rate_per_s=0.3,
            nuclear_export_rate_per_s=0.2,
            cytoplasmic_mrna_decay_rate_per_s=0.01,
            translation_rate_per_mrna_per_s=0.4,
            protein_decay_rate_per_s=0.005,
            calibration_status="synthetic_test_fixture",
            biological_system="software unit test",
            assay="deterministic seeded SSA fixture",
            evidence="Synthetic values test the reaction topology only",
            source_ids=("synthetic-test",),
        )
        program = register_kinetic_profile(program, profile)
        blocked = step_gene_expression_program(program, dt_s=60.0, t_s=0.0, rng=EngineRng(11))
        self.assertEqual(blocked.genes["CYP7A1"].total_protein_count, 0.0)
        self.assertIn("blocked_external_1", blocked.kinetics_status)

        advanced = step_gene_expression_program(
            program,
            dt_s=60.0,
            t_s=0.0,
            rng=EngineRng(11),
            allow_test_profiles=True,
        )
        self.assertGreater(advanced.genes["CYP7A1"].total_protein_count or 0.0, 0.0)
        self.assertTrue(any(event.event_type == "transcription_fired" for event in advanced.events))
        self.assertLessEqual(advanced.genes["CYP7A1"].active_allele_count or 0.0, 2.0)


if __name__ == "__main__":
    unittest.main()
