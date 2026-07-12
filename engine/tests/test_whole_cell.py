from __future__ import annotations

import unittest
from dataclasses import replace

from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.cytoplasm_inventory import protein_inventory_counts
from cell_engine.stochastic.cell_cycle import divide
from cell_engine.stochastic.whole_cell import (
    PROLIFERATING_HEPATOCYTE_CYCLE,
    REAL_TIME_PROLIFERATING_HEPATOCYTE_CYCLE,
    WHOLE_CELL_CYCLE,
    build_whole_cell_network,
    run_whole_cell_population,
    run_whole_cell,
    seed_whole_cell_population,
    seed_whole_cell,
    whole_cell_snapshot,
    whole_cell_population_snapshot,
)
from cell_engine.stochastic.hepatocyte_regeneration import (
    CYTOKINESIS_FAILURE_UNCALIBRATED_NOTE,
    HepatocyteRegenerationInput,
    POLYPLOID_PROGRAM_UNKNOWN_NOTE,
    REPORT_CYTOKINESIS_FAILURE_QUALITATIVE,
    REPORT_CYTOKINESIS_FAILURE_UNCALIBRATED,
    REPORT_DIRECT_MITOGEN_QUALITATIVE,
    REPORT_ECM_BLOCK_QUALITATIVE,
    REPORT_HIPPO_BLOCK_QUALITATIVE,
    REPORT_POLYPLOID_PROGRAM_QUALITATIVE,
    REPORT_POLYPLOID_PROGRAM_UNKNOWN,
    REPORT_PRIMING_QUALITATIVE,
    REPORT_TGFB_BRAKE_QUALITATIVE,
    REPORT_WNT_REDUCED_DELAY,
    REPORT_WNT_SUPPORT_QUALITATIVE,
    apply_regeneration_decision,
    evaluate_hepatocyte_regeneration,
    regeneration_timing_profile,
)


class WholeCellStructureTests(unittest.TestCase):
    def test_all_subsystems_composed(self):
        network = build_whole_cell_network(1.0e-12)
        ids = {r.id for r in network.reactions}
        for required in ("glucokinase", "cps1", "glutathione_reductase", "atp_regeneration"):
            self.assertIn(required, ids)
        # Shared pools are unified (ATP appears once in the species list).
        self.assertEqual(network.species.count("ATP"), 1)
        self.assertNotIn("gene", network.species)
        self.assertNotIn("transcription", ids)

    def test_synthetic_expression_benchmark_is_explicitly_opt_in(self):
        network = build_whole_cell_network(1.0e-12, include_synthetic_expression_benchmark=True)
        self.assertIn("gene", network.species)
        self.assertIn("transcription", {reaction.id for reaction in network.reactions})

    def test_glut2_capacity_uses_protein_inventory_effect_layer(self):
        inventory = protein_inventory_counts()
        inventory["protein:SLC2A2"] *= 0.25
        reference = build_whole_cell_network(1.0e-12)
        depleted = seed_whole_cell(build_hepatocyte_definition(), protein_inventory=inventory).network
        counts = {"glucose_blood": 1.0e6, "glucose": 0.0, "ATP": 1.0e6, "ADP": 0.0}
        baseline_flux = next(r for r in reference.reactions if r.id == "glut2_uptake").propensity(counts, 1.0e-12)
        depleted_flux = next(r for r in depleted.reactions if r.id == "glut2_uptake").propensity(counts, 1.0e-12)
        self.assertAlmostEqual(depleted_flux / baseline_flux, 0.25)


class WholeCellRunTests(unittest.TestCase):
    def setUp(self):
        self.definition = build_hepatocyte_definition()

    def test_default_fed_hepatocyte_stays_quiescent_without_growth_signal(self):
        cell, divisions = run_whole_cell(
            seed_whole_cell(self.definition, fed=True), 160.0, 0.05, EngineRng(7)
        )
        self.assertEqual(divisions, 0)                         # nutrients alone are not a mitogen
        self.assertEqual(cell.cycle.phase, "G0")
        self.assertGreater(cell.energy_charge(), 0.0)
        self.assertLessEqual(cell.energy_charge(), 1.0)        # exploratory network; not PHH energy validation
        snapshot = whole_cell_snapshot(cell, "cell-0", params=WHOLE_CELL_CYCLE)
        self.assertEqual(snapshot["phase"], "G0")
        self.assertEqual(snapshot["checkpoint_control"]["blocked_by"], ())
        self.assertIn(
            "quiescent G0 maintained",
            snapshot["checkpoint_control"]["supported_by"][0],
        )

    def test_regeneration_signal_allows_fed_cell_to_divide(self):
        cell, divisions = run_whole_cell(
            seed_whole_cell(self.definition, fed=True, include_synthetic_expression_benchmark=True), 160.0, 0.05, EngineRng(7),
            params=PROLIFERATING_HEPATOCYTE_CYCLE,
        )
        self.assertGreater(divisions, 0)                         # grew and divided
        self.assertGreater(cell.counts["protein"], 0.0)          # gene expression ran
        self.assertGreater(cell.counts["urea"], 0.0)             # urea cycle ran
        self.assertGreater(cell.energy_charge(), 0.0)
        self.assertLessEqual(cell.energy_charge(), 1.0)          # placeholder pathway loads block quantitative claim
        for value in cell.counts.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLess(value, 1.0e12)

    def test_real_hepatocyte_timing_prevents_demo_speed_division(self):
        cell, divisions = run_whole_cell(
            seed_whole_cell(self.definition, fed=True), 160.0, 0.05, EngineRng(7),
            params=REAL_TIME_PROLIFERATING_HEPATOCYTE_CYCLE,
        )
        self.assertEqual(divisions, 0)
        self.assertEqual(cell.cycle.phase, "G1")
        self.assertEqual(REAL_TIME_PROLIFERATING_HEPATOCYTE_CYCLE.timing_profile.id, "rat_hepatocyte_phx_reference")
        self.assertFalse(REAL_TIME_PROLIFERATING_HEPATOCYTE_CYCLE.timing_profile.time_compressed)

    def test_starved_cell_arrests(self):
        cell, divisions = run_whole_cell(
            seed_whole_cell(self.definition, fed=False), 160.0, 0.05, EngineRng(7)
        )
        self.assertEqual(divisions, 0)  # no glucose, no growth, no division

    def test_division_partitions_unified_counts(self):
        cell = seed_whole_cell(self.definition, fed=True, include_synthetic_expression_benchmark=True)
        ready = replace(cell.cycle, ready_to_divide=True, counts=cell.counts)
        a, b = divide(ready, WHOLE_CELL_CYCLE, EngineRng(3))
        for species, n in cell.counts.items():
            self.assertAlmostEqual(a.counts[species] + b.counts[species], n, delta=1e-6)
        # Genome segregates exactly.
        self.assertEqual(a.counts["gene"] + b.counts["gene"], cell.counts["gene"])

    def test_population_keeps_both_real_daughters(self):
        population = run_whole_cell_population(
            seed_whole_cell_population(self.definition, fed=True, include_synthetic_expression_benchmark=True),
            80.0,
            0.05,
            EngineRng(9),
            params=replace(PROLIFERATING_HEPATOCYTE_CYCLE, cytokinesis_failure_probability=0.0),
        )
        self.assertGreaterEqual(len(population.cells), 2)
        self.assertGreaterEqual(len(population.events), 1)
        event = population.events[0]
        self.assertEqual(event.outcome, "abscission_success")
        self.assertEqual(len(event.daughters), 2)
        self.assertEqual(len(event.resulting_cells), 2)
        self.assertEqual(event.daughters[0].cycle.generation, 1)
        self.assertEqual(event.daughters[1].cycle.generation, 1)
        self.assertTrue(all(cell.cycle.generation >= 1 for cell in population.cells))
        for species, n in event.parent.counts.items():
            inherited = event.daughters[0].counts[species] + event.daughters[1].counts[species]
            self.assertAlmostEqual(inherited, n, delta=max(1e-6, n * 1.0e-12))
        self.assertEqual(
            event.daughters[0].cycle.organelles.mitochondria + event.daughters[1].cycle.organelles.mitochondria,
            event.parent.cycle.organelles.mitochondria,
        )
        self.assertEqual(event.daughters[0].cycle.organelles.centrosomes, 1)
        self.assertEqual(event.daughters[1].cycle.organelles.centrosomes, 1)

    def test_population_cytokinesis_failure_keeps_one_binucleated_cell(self):
        population = run_whole_cell_population(
            seed_whole_cell_population(self.definition, fed=True, include_synthetic_expression_benchmark=True),
            80.0,
            0.05,
            EngineRng(9),
            params=replace(PROLIFERATING_HEPATOCYTE_CYCLE, cytokinesis_failure_probability=1.0, cytokinesis_failure_calibrated=True),
        )
        self.assertGreaterEqual(len(population.events), 1)
        event = population.events[0]
        self.assertEqual(event.outcome, "cytokinesis_failure")
        self.assertEqual(event.daughters, ())
        self.assertEqual(len(event.resulting_cells), 1)
        failed_cell = event.resulting_cells[0]
        self.assertEqual(failed_cell.cycle.ploidy.nuclei, 2)
        self.assertEqual(failed_cell.cycle.cytokinesis.stage, "regressed")
        self.assertEqual(failed_cell.cycle.organelles.mitochondria, event.parent.cycle.organelles.mitochondria)
        self.assertEqual(failed_cell.cycle.organelles.centrosomes, 2)
        for species, n in event.parent.counts.items():
            self.assertAlmostEqual(failed_cell.counts[species], n, delta=max(1e-6, n * 1.0e-12))

    def test_population_snapshot_serializes_division_events(self):
        population = run_whole_cell_population(
            seed_whole_cell_population(self.definition, fed=True, include_synthetic_expression_benchmark=True),
            80.0,
            0.05,
            EngineRng(9),
            params=replace(PROLIFERATING_HEPATOCYTE_CYCLE, cytokinesis_failure_probability=0.0),
        )
        snapshot = whole_cell_population_snapshot(
            population,
            params=replace(PROLIFERATING_HEPATOCYTE_CYCLE, cytokinesis_failure_probability=0.0),
        )
        self.assertEqual(snapshot["engine"], "whole_cell_population")
        self.assertEqual(snapshot["timing_profile"]["id"], "compressed_demo")
        self.assertTrue(snapshot["timing_profile"]["time_compressed"])
        self.assertEqual(snapshot["cell_count"], len(population.cells))
        self.assertGreaterEqual(snapshot["event_count"], 1)
        latest = snapshot["latest_event"]
        self.assertIsNotNone(latest)
        assert isinstance(latest, dict)
        self.assertEqual(latest["outcome"], "abscission_success")
        self.assertEqual(latest["daughter_count"], 2)
        self.assertEqual(len(latest["resulting_cells"]), 2)
        first_child = latest["resulting_cells"][0]
        self.assertIn("organelles", first_child)
        self.assertEqual(first_child["organelles"]["centrosomes"], 1)
        self.assertIn("checkpoint_control", first_child)
        self.assertIn("nodes", first_child["checkpoint_control"])
        self.assertIn("cytokinesis", latest["parent"])

    def test_regeneration_gate_requires_context_and_direct_mitogen(self):
        no_context = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="none",
                hgf_met="elevated",
                egfr_ligand="elevated",
                liver_mass_restored=True,
            )
        )
        self.assertFalse(no_context.cell_cycle_entry_permitted)
        self.assertIn("no injury", no_context.blocked_by[0])

        regeneration = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_met="elevated",
                il6_stat3="elevated",
                tnf_nfkb="elevated",
                wnt_beta_catenin="elevated",
            )
        )
        self.assertTrue(regeneration.cell_cycle_entry_permitted)
        self.assertIn(REPORT_DIRECT_MITOGEN_QUALITATIVE, regeneration.reporting_labels)
        self.assertIn(REPORT_PRIMING_QUALITATIVE, regeneration.reporting_labels)
        self.assertIn(REPORT_WNT_SUPPORT_QUALITATIVE, regeneration.reporting_labels)
        params = apply_regeneration_decision(WHOLE_CELL_CYCLE, regeneration)
        self.assertTrue(params.regeneration_signal_active)

    def test_hgf_met_axis_requires_ecm_permissive_receptor_signalling(self):
        permitted = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="elevated",
                met_receptor="baseline",
                ecm_integrin_attachment="baseline",
            )
        )
        self.assertTrue(permitted.cell_cycle_entry_permitted)
        hgf_axis = next(axis for axis in permitted.direct_mitogen_axes if axis.axis == "HGF/MET")
        self.assertTrue(hgf_axis.active)
        self.assertIn("HGF/MET receptor phosphorylation not explicitly measured", hgf_axis.uncalibrated)

        ecm_blocked = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="elevated",
                met_receptor="baseline",
                ecm_integrin_attachment="reduced",
            )
        )
        self.assertFalse(ecm_blocked.cell_cycle_entry_permitted)
        self.assertTrue(any("ECM/beta1-integrin" in reason for reason in ecm_blocked.blocked_by))

    def test_egfr_axis_can_supply_direct_mitogen_when_hgf_axis_absent(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="absent",
                egfr_ligand="elevated",
                egfr_receptor="baseline",
            )
        )
        self.assertTrue(decision.cell_cycle_entry_permitted)
        egfr_axis = next(axis for axis in decision.direct_mitogen_axes if axis.axis == "EGFR")
        self.assertTrue(egfr_axis.active)
        self.assertIn("egfr_g1s", egfr_axis.sources)

    def test_explicit_baseline_phosphorylation_blocks_axis_activation(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="elevated",
                met_receptor="baseline",
                met_phosphorylation="baseline",
            )
        )
        self.assertFalse(decision.cell_cycle_entry_permitted)
        self.assertTrue(any("phosphorylation not elevated" in reason for reason in decision.blocked_by))

    def test_tgfb_context_blocks_proliferation_and_supports_binucleation(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="development",
                liver_mass_restored=False,
                hgf_met="elevated",
                tgfb_smad="elevated",
                e2f7_e2f8_polyploid_program="elevated",
            )
        )
        self.assertFalse(decision.cell_cycle_entry_permitted)
        self.assertTrue(decision.cytokinesis_failure_supported)
        self.assertTrue(decision.polyploid_binucleation_supported)
        self.assertIn("tgfb_binucleation", decision.sources)
        self.assertIn("human_hepatocyte_binucleation", decision.sources)
        self.assertIn(CYTOKINESIS_FAILURE_UNCALIBRATED_NOTE, decision.uncalibrated)
        self.assertIn(REPORT_TGFB_BRAKE_QUALITATIVE, decision.reporting_labels)
        self.assertIn(REPORT_CYTOKINESIS_FAILURE_QUALITATIVE, decision.reporting_labels)
        self.assertIn(REPORT_CYTOKINESIS_FAILURE_UNCALIBRATED, decision.reporting_labels)
        self.assertIn(REPORT_POLYPLOID_PROGRAM_QUALITATIVE, decision.reporting_labels)
        params = apply_regeneration_decision(WHOLE_CELL_CYCLE, decision)
        self.assertEqual(
            params.cytokinesis_failure_probability,
            WHOLE_CELL_CYCLE.cytokinesis_failure_probability,
        )

    def test_unknown_polyploid_program_is_reported_not_used_as_support(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="elevated",
                met_receptor="baseline",
                wnt_beta_catenin="elevated",
            )
        )
        self.assertTrue(decision.cell_cycle_entry_permitted)
        self.assertFalse(decision.cytokinesis_failure_supported)
        self.assertFalse(decision.polyploid_binucleation_supported)
        self.assertIn(POLYPLOID_PROGRAM_UNKNOWN_NOTE, decision.uncalibrated)
        self.assertIn(REPORT_POLYPLOID_PROGRAM_UNKNOWN, decision.reporting_labels)
        self.assertNotIn(REPORT_CYTOKINESIS_FAILURE_UNCALIBRATED, decision.reporting_labels)
        self.assertNotIn("human_hepatocyte_binucleation", decision.sources)

    def test_e2f_polyploid_support_remains_qualitative_not_probability_calibration(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="elevated",
                met_receptor="baseline",
                wnt_beta_catenin="elevated",
                e2f7_e2f8_polyploid_program="elevated",
            )
        )
        self.assertTrue(decision.cell_cycle_entry_permitted)
        self.assertFalse(decision.cytokinesis_failure_supported)
        self.assertTrue(decision.polyploid_binucleation_supported)
        self.assertIn("human_hepatocyte_binucleation", decision.sources)
        self.assertIn(CYTOKINESIS_FAILURE_UNCALIBRATED_NOTE, decision.uncalibrated)
        self.assertIn(REPORT_POLYPLOID_PROGRAM_QUALITATIVE, decision.reporting_labels)
        self.assertIn(REPORT_CYTOKINESIS_FAILURE_UNCALIBRATED, decision.reporting_labels)
        self.assertNotIn(REPORT_CYTOKINESIS_FAILURE_QUALITATIVE, decision.reporting_labels)
        self.assertTrue(
            any("E2F7/E2F8" in item for item in decision.supported_by)
        )
        params = apply_regeneration_decision(WHOLE_CELL_CYCLE, decision)
        self.assertEqual(
            params.cytokinesis_failure_probability,
            WHOLE_CELL_CYCLE.cytokinesis_failure_probability,
        )

    def test_cytokine_priming_does_not_replace_direct_mitogen(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                il6_ligand="elevated",
                stat3_activation="elevated",
                tnf_alpha="elevated",
                nfkb_activation="elevated",
            )
        )
        self.assertTrue(decision.priming_supported)
        self.assertFalse(decision.cell_cycle_entry_permitted)
        self.assertTrue(any(reason.startswith("no active direct mitogenic axis") for reason in decision.blocked_by))

    def test_wnt_support_is_modelled_as_delay_not_absolute_gate(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="elevated",
                met_receptor="baseline",
                beta_catenin_nuclear="reduced",
            )
        )
        self.assertTrue(decision.cell_cycle_entry_permitted)
        self.assertFalse(decision.support_signaling_supported)
        self.assertTrue(any("Wnt/beta-catenin support reduced" in reason for reason in decision.uncalibrated))
        self.assertIn(REPORT_WNT_REDUCED_DELAY, decision.reporting_labels)
        self.assertNotIn(REPORT_CYTOKINESIS_FAILURE_QUALITATIVE, decision.reporting_labels)

    def test_tgfb_smad_brake_blocks_even_with_direct_mitogen(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="elevated",
                met_receptor="baseline",
                tgfb_ligand="elevated",
                smad2_3_activation="elevated",
            )
        )
        self.assertFalse(decision.cell_cycle_entry_permitted)
        self.assertTrue(decision.anti_proliferative_brake_active)
        self.assertIn("TGF-beta/SMAD anti-proliferative brake active", decision.blocked_by)
        self.assertIn(REPORT_TGFB_BRAKE_QUALITATIVE, decision.reporting_labels)
        self.assertIn(REPORT_CYTOKINESIS_FAILURE_QUALITATIVE, decision.reporting_labels)

    def test_ecm_and_hippo_blocks_are_reported_as_qualitative_labels(self):
        decision = evaluate_hepatocyte_regeneration(
            HepatocyteRegenerationInput(
                trigger="major_partial_hepatectomy",
                liver_mass_restored=False,
                hgf_ligand="elevated",
                met_receptor="baseline",
                ecm_integrin_attachment="reduced",
                hippo_contact_inhibition="elevated",
            )
        )
        self.assertFalse(decision.cell_cycle_entry_permitted)
        self.assertIn(REPORT_ECM_BLOCK_QUALITATIVE, decision.reporting_labels)
        self.assertIn(REPORT_HIPPO_BLOCK_QUALITATIVE, decision.reporting_labels)
        self.assertNotIn(REPORT_DIRECT_MITOGEN_QUALITATIVE, decision.reporting_labels)

    def test_regeneration_timing_profiles_are_source_anchored(self):
        rat = regeneration_timing_profile(species="rat", trigger="major_partial_hepatectomy")
        mouse = regeneration_timing_profile(species="mouse", trigger="major_partial_hepatectomy")
        human = regeneration_timing_profile(species="human", trigger="major_partial_hepatectomy")
        self.assertEqual(rat.dna_synthesis_onset_h, (12.0, 16.0))
        self.assertEqual(mouse.dna_synthesis_peak_h, (36.0, 48.0))
        self.assertEqual(human.dna_synthesis_peak_h, (168.0, 240.0))
        self.assertIn("hepatectomy_timing", human.source_ids)


if __name__ == "__main__":
    unittest.main()
