from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cell_engine.validation.evidence_intake import (
    EvidenceIntakeError,
    evidence_intake_snapshot,
    validate_evidence_bundle,
)


CSV_FILES = (
    "human_phh_scale_bridge.csv",
    "human_phh_glucose_fluxes.csv",
    "human_endocrine_signal_chain.csv",
    "human_oxygen_redox_zonation.csv",
    "heldout_validation_trajectories.csv",
)
MARKDOWN_FILES = (
    "koenig_model_provenance_audit.md",
    "source_audit.md",
    "unidentifiable_parameters.md",
)
HEADER = (
    "record_id,parameter,value,lower,upper,uncertainty_value,unit,biological_system,"
    "species,model_system,record_type,directness,source_title,source_kind,doi,source_locator,applicability,limitations\n"
)
VALID_ROW = (
    "record_1,glucose_flux,1.0,0.5,1.5,0.1,umol/min,healthy_adult_human_in_vivo,"
    "Homo sapiens,in_vivo_human,measured,direct_measurement,Primary human study,primary_research,10.1234/example.1,Table 1,"
    "organ_scale_validation_only,Requires scale matching\n"
)


def write_bundle(root: Path, row: str = VALID_ROW, integration_contract: dict[str, object] | None = None) -> None:
    for file_name in CSV_FILES:
        (root / file_name).write_text(HEADER + row, encoding="utf-8")
    for file_name in MARKDOWN_FILES:
        (root / file_name).write_text(f"# {file_name}\n\nPrimary-source audit.\n", encoding="utf-8")
    (root / "integration_contract.json").write_text(
        json.dumps(integration_contract or {"automatic_parameter_activation": False}),
        encoding="utf-8",
    )


class EvidenceIntakeTests(unittest.TestCase):
    def test_pending_snapshot_exposes_nine_file_gate_without_values(self) -> None:
        with TemporaryDirectory() as tmp:
            snapshot = evidence_intake_snapshot(Path(tmp) / "not-delivered")
        self.assertEqual(snapshot["status"], "awaiting_external_evidence_bundle")
        self.assertEqual(snapshot["required_file_count"], 9)
        self.assertEqual(snapshot["present_file_count"], 0)
        self.assertFalse(snapshot["automatic_parameter_activation"])
        self.assertFalse(snapshot["authoritative_coupling_enabled"])

    def test_structurally_valid_bundle_remains_manual_review_only(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_bundle(root)
            audit = validate_evidence_bundle(root)
        self.assertEqual(audit.status, "structurally_valid_manual_review_required")
        self.assertEqual(audit.present_file_count, 9)
        self.assertEqual(len(audit.sha256_by_file), 9)
        self.assertEqual(audit.curation_candidate_count, 5)
        self.assertTrue(audit.manual_primary_source_review_required)
        self.assertFalse(audit.automatic_parameter_activation)
        self.assertFalse(audit.authoritative_coupling_enabled)

    def test_fake_missing_token_is_rejected(self) -> None:
        invalid_row = VALID_ROW.replace("1.0,0.5", "N/A,0.5")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_bundle(root, invalid_row)
            with self.assertRaisesRegex(EvidenceIntakeError, "forbidden missing token"):
                validate_evidence_bundle(root)

    def test_model_output_cannot_be_labelled_as_measurement(self) -> None:
        invalid_row = VALID_ROW.replace("measured,direct_measurement", "measured,model_output")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_bundle(root, invalid_row)
            with self.assertRaisesRegex(EvidenceIntakeError, "labels model output as measured"):
                validate_evidence_bundle(root)

    def test_review_record_is_retained_but_not_a_curation_candidate(self) -> None:
        review_row = VALID_ROW.replace("primary_research", "review")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_bundle(root, review_row)
            audit = validate_evidence_bundle(root)
        self.assertEqual(audit.curation_candidate_count, 0)
        self.assertEqual(sum(table.numeric_record_count for table in audit.tables), 5)

    def test_external_contract_cannot_enable_coupling(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_bundle(root, integration_contract={"authoritative_coupling_enabled": True})
            with self.assertRaisesRegex(EvidenceIntakeError, "attempts to activate"):
                validate_evidence_bundle(root)


if __name__ == "__main__":
    unittest.main()
