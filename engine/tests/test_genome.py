from __future__ import annotations

import unittest

from cell_engine.core.genome import (
    GRCH38_P14_CHROMOSOMES,
    HEPATOCYTE_FUNCTIONAL_LOCI,
    SomaticVariantRecord,
    build_reference_hepatocyte_genome,
    record_somatic_variant,
)


class HepatocyteGenomeTests(unittest.TestCase):
    def test_reference_assembly_is_compact_but_coordinate_complete(self) -> None:
        genome = build_reference_hepatocyte_genome()
        self.assertEqual(genome.assembly_accession, "GCF_000001405.40")
        self.assertEqual(len(GRCH38_P14_CHROMOSOMES), 24)
        self.assertEqual(sum(item.length_bp for item in GRCH38_P14_CHROMOSOMES), 3_088_269_832)
        self.assertEqual(genome.primary_assembly_length_bp, 3_088_269_832)
        self.assertEqual(genome.mitochondrial.reference_length_bp, 16_569)

    def test_functional_loci_use_ncbi_grch38_coordinates(self) -> None:
        loci = {locus.symbol: locus for locus in HEPATOCYTE_FUNCTIONAL_LOCI}
        self.assertEqual(loci["ABCB11"].ncbi_gene_id, "8647")
        self.assertEqual((loci["ABCB11"].chromosome, loci["ABCB11"].start_bp, loci["ABCB11"].end_bp), ("2", 168_915_391, 169_031_325))
        self.assertEqual((loci["ABCC2"].chromosome, loci["ABCC2"].start_bp, loci["ABCC2"].end_bp), ("10", 99_782_641, 99_852_595))
        self.assertEqual((loci["NR1H4"].chromosome, loci["NR1H4"].start_bp, loci["NR1H4"].end_bp), ("12", 100_473_866, 100_564_414))
        self.assertEqual((loci["NR0B2"].chromosome, loci["NR0B2"].start_bp, loci["NR0B2"].end_bp), ("1", 26_911_489, 26_913_975))
        self.assertEqual(len(loci), len(HEPATOCYTE_FUNCTIONAL_LOCI))

    def test_reference_state_does_not_invent_an_individual_genotype(self) -> None:
        genome = build_reference_hepatocyte_genome()
        self.assertEqual(genome.individual_genotype_status, "not_provided_reference_coordinates_only")
        self.assertEqual(genome.sex_chromosome_complement, "not_provided")
        self.assertEqual(genome.somatic_variants, ())
        self.assertEqual(genome.mitochondrial.copy_number, None)
        self.assertEqual(genome.mitochondrial.heteroplasmy_status, "not_measured")

    def test_only_observed_source_linked_variants_can_be_recorded(self) -> None:
        genome = build_reference_hepatocyte_genome()
        variant = SomaticVariantRecord(
            id="observed-1",
            chromosome="2",
            position_bp=168_915_391,
            variant_type="snv",
            reference="A",
            alternate="G",
            observed_time_s=120.0,
            source_id="assay-1",
            evidence="VCF call passing the selected assay quality policy",
            allele_fraction=0.25,
            affected_gene="ABCB11",
        )
        updated = record_somatic_variant(genome, variant)
        self.assertEqual(updated.somatic_variants, (variant,))
        with self.assertRaises(ValueError):
            record_somatic_variant(genome, SomaticVariantRecord(
                **{**variant.__dict__, "id": "outside", "position_bp": 300_000_000}
            ))
        with self.assertRaises(ValueError):
            record_somatic_variant(genome, SomaticVariantRecord(
                **{**variant.__dict__, "id": "no-source", "source_id": ""}
            ))


if __name__ == "__main__":
    unittest.main()
