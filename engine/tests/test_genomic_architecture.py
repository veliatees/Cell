from __future__ import annotations

import unittest
from dataclasses import replace

from cell_engine.core.genome import SomaticVariantRecord, record_somatic_variant
from cell_engine.core.genomic_architecture import (
    EpigeneticLocusState,
    OmicsDatasetRecord,
    VariantFunctionalLink,
    link_variant_to_function,
    record_epigenetic_observation,
    register_omics_dataset,
)
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation.invariants import validate_state


class GenomicArchitectureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)
        assert self.state.genomic_architecture is not None
        assert self.state.genome is not None

    def test_all_six_milestones_have_software_contracts_without_claiming_validation(self) -> None:
        architecture = self.state.genomic_architecture
        assert architecture is not None
        self.assertEqual([item.milestone for item in architecture.milestones], list(range(1, 7)))
        self.assertTrue(all(item.software_complete for item in architecture.milestones))
        self.assertTrue(all(item.scientific_status == "implemented_data_required" for item in architecture.milestones))
        self.assertEqual(len(architecture.gene_modules), 6)
        self.assertEqual(set(architecture.epigenetic_loci), {locus.symbol for locus in self.state.genome.functional_loci})
        validate_state(self.definition, self.state)

    def test_donor_identity_and_epigenome_are_unknown_by_default(self) -> None:
        architecture = self.state.genomic_architecture
        assert architecture is not None
        self.assertEqual(architecture.identity.donor_id, "not_provided")
        self.assertTrue(all(item.observation_status == "not_measured" for item in architecture.epigenetic_loci.values()))
        self.assertTrue(all(item.dna_methylation_fraction is None for item in architecture.epigenetic_loci.values()))

    def test_measured_epigenetic_observation_preserves_assay_context(self) -> None:
        architecture = self.state.genomic_architecture
        assert architecture is not None
        observed = record_epigenetic_observation(
            architecture,
            EpigeneticLocusState(
                gene_symbol="HNF4A",
                chromatin_accessibility="open",
                dna_methylation_fraction=0.18,
                histone_marks={"H3K27ac_normalized": 0.72},
                observation_status="measured",
                biological_system="donor-matched primary human hepatocyte",
                assay="single-nucleus ATAC plus targeted bisulfite sequencing",
                source_ids=("donor-assay-1",),
                notes="Test record exercises provenance; values are not part of the baseline simulation.",
            ),
        )
        self.assertEqual(observed.epigenetic_loci["HNF4A"].assay, "single-nucleus ATAC plus targeted bisulfite sequencing")

    def test_omics_dataset_declares_calibration_or_validation_role(self) -> None:
        architecture = self.state.genomic_architecture
        assert architecture is not None
        registered = register_omics_dataset(
            architecture,
            OmicsDatasetRecord(
                id="held-out-phh-1",
                assay_type="single-cell RNA-seq",
                biological_system="primary human hepatocyte",
                donor_or_cohort="held-out donor cohort",
                genome_assembly="GRCh38.p14",
                normalization="raw UMI plus documented library-size normalization",
                observed_genes=("HNF4A", "ABCB11"),
                source_ids=("held-out-study",),
                evidence="Dataset registration test",
                use="validation",
            ),
        )
        self.assertEqual(registered.omics_datasets[0].use, "validation")

    def test_variant_function_link_requires_an_observed_variant(self) -> None:
        genome = record_somatic_variant(
            self.state.genome,
            SomaticVariantRecord(
                id="observed-tp53-variant",
                chromosome="17",
                position_bp=7_675_000,
                variant_type="snv",
                reference="C",
                alternate="T",
                observed_time_s=10.0,
                source_id="matched-sequencing",
                evidence="Donor-matched sequencing observation",
                affected_gene="TP53",
            ),
        )
        architecture = link_variant_to_function(
            self.state.genomic_architecture,
            genome,
            VariantFunctionalLink(
                id="tp53-functional-assay-link",
                variant_id="observed-tp53-variant",
                target_gene_or_module="TP53",
                effect_layer="functional_protein",
                observed_effect="reduced transcriptional response in matched assay",
                evidence_status="measured",
                experimental_system="donor-derived hepatocyte assay",
                source_ids=("matched-functional-assay",),
            ),
        )
        linked_state = replace(self.state, genome=genome, genomic_architecture=architecture)
        validate_state(self.definition, linked_state)
        self.assertEqual(architecture.variant_functional_links[0].variant_id, "observed-tp53-variant")


if __name__ == "__main__":
    unittest.main()

