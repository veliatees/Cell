from __future__ import annotations

import json
from pathlib import Path

from cell_engine.quantitative.human_gem_structural_audit import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_REPORT_PATH,
    audit_sbml_structure,
    load_human_gem_manifest,
    validate_committed_human_gem_audit,
)


def _write_synthetic_sbml(path: Path) -> None:
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version2"
      level="3" version="1" fbc:required="false">
  <model id="audit_fixture" fbc:activeObjective="obj">
    <listOfCompartments><compartment id="c" constant="true"/></listOfCompartments>
    <listOfSpecies>
      <species id="a" compartment="c" fbc:chemicalFormula="C2H4" fbc:charge="0"/>
      <species id="b" compartment="c" fbc:chemicalFormula="C2H4" fbc:charge="0"/>
      <species id="c1" compartment="c" fbc:chemicalFormula="CH2" fbc:charge="0"/>
      <species id="hp" compartment="c" fbc:chemicalFormula="H" fbc:charge="1"/>
      <species id="h0" compartment="c" fbc:chemicalFormula="H" fbc:charge="0"/>
      <species id="generic" compartment="c" fbc:chemicalFormula="X" fbc:charge="0"/>
      <species id="generic2" compartment="c" fbc:chemicalFormula="X" fbc:charge="0"/>
    </listOfSpecies>
    <listOfReactions>
      <reaction id="balanced" reversible="false"><listOfReactants><speciesReference species="a"/></listOfReactants><listOfProducts><speciesReference species="b"/></listOfProducts></reaction>
      <reaction id="element_imbalanced" reversible="false"><listOfReactants><speciesReference species="a"/></listOfReactants><listOfProducts><speciesReference species="c1"/></listOfProducts></reaction>
      <reaction id="charge_imbalanced" reversible="false"><listOfReactants><speciesReference species="hp"/></listOfReactants><listOfProducts><speciesReference species="h0"/></listOfProducts></reaction>
      <reaction id="generic_unassessable" reversible="false"><listOfReactants><speciesReference species="generic"/></listOfReactants><listOfProducts><speciesReference species="generic2"/></listOfProducts></reaction>
      <reaction id="exchange" reversible="false"><listOfReactants><speciesReference species="a"/></listOfReactants></reaction>
    </listOfReactions>
    <fbc:listOfObjectives><fbc:objective fbc:id="obj" fbc:type="maximize"/></fbc:listOfObjectives>
    <fbc:listOfGeneProducts><fbc:geneProduct fbc:id="g1" fbc:label="G1"/></fbc:listOfGeneProducts>
  </model>
</sbml>
""",
        encoding="utf-8",
    )


def test_streaming_audit_separates_exchange_unassessable_and_imbalanced_reactions(tmp_path: Path) -> None:
    artifact = tmp_path / "fixture.xml"
    _write_synthetic_sbml(artifact)
    report = audit_sbml_structure(artifact)

    assert report["structure"]["reaction_count"] == 5
    assert report["structure"]["one_sided_reaction_count"] == 1
    assert report["structure"]["two_sided_reaction_count"] == 4
    assert report["elemental_balance"]["assessable_reaction_count"] == 3
    assert report["elemental_balance"]["balanced_reaction_count"] == 2
    assert report["elemental_balance"]["imbalanced_reaction_count"] == 1
    assert report["elemental_balance"]["unassessable_reaction_count"] == 1
    assert report["charge_balance"]["assessable_reaction_count"] == 4
    assert report["charge_balance"]["imbalanced_reaction_count"] == 1
    assert report["joint_balance"]["balanced_reaction_count"] == 1
    assert report["joint_balance"]["imbalanced_reaction_count"] == 2
    assert report["scientific_boundary"]["fba_execution_allowed"] is False


def test_committed_human_gem_audit_matches_the_pinned_manifest() -> None:
    manifest = load_human_gem_manifest(DEFAULT_MANIFEST_PATH)
    report = json.loads(DEFAULT_REPORT_PATH.read_text(encoding="utf-8"))
    validate_committed_human_gem_audit(report, manifest)

    assert report["artifact"]["sha256"] == manifest["artifact_sha256"]
    assert report["structure"]["species_count"] == 8461
    assert report["structure"]["reaction_count"] == 12931
    assert report["structure"]["one_sided_reaction_count"] > 0
    assert report["joint_balance"]["assessable_reaction_count"] > 0
    assert report["scientific_boundary"]["healthy_phh_context_extracted"] is False
