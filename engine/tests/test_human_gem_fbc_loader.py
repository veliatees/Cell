from __future__ import annotations

import json
from pathlib import Path

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import (
    DEFAULT_CACHE_PATH,
    DEFAULT_LOADER_AUDIT_PATH,
    HumanGemFbcError,
    build_fbc_loader_audit,
    load_committed_fbc_loader_audit,
    load_pinned_human_gem,
    load_sbml_fbc,
    validate_fbc_loader_audit,
)


def _write_fixture(path: Path, *, lower_bound_id: str = "lb") -> None:
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version2"
      level="3" version="1" fbc:required="false">
  <model id="sparse_fixture" name="Sparse fixture" fbc:strict="true">
    <listOfCompartments>
      <compartment id="c" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="a" compartment="c" boundaryCondition="false"/>
      <species id="b" compartment="c" boundaryCondition="false"/>
    </listOfSpecies>
    <listOfParameters>
      <parameter id="lb" value="0" constant="true"/>
      <parameter id="ub" value="10" constant="true"/>
    </listOfParameters>
    <listOfReactions>
      <reaction id="R_IN" reversible="false"
                fbc:lowerFluxBound="{lower_bound_id}" fbc:upperFluxBound="ub">
        <listOfProducts>
          <speciesReference species="a" stoichiometry="1" constant="true"/>
        </listOfProducts>
      </reaction>
      <reaction id="R_AB" reversible="false"
                fbc:lowerFluxBound="lb" fbc:upperFluxBound="ub">
        <listOfReactants>
          <speciesReference species="a" stoichiometry="2" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="b" stoichiometry="1" constant="true"/>
        </listOfProducts>
        <fbc:geneProductAssociation>
          <fbc:and>
            <fbc:geneProductRef fbc:geneProduct="g1"/>
            <fbc:or>
              <fbc:geneProductRef fbc:geneProduct="g2"/>
              <fbc:geneProductRef fbc:geneProduct="g3"/>
            </fbc:or>
          </fbc:and>
        </fbc:geneProductAssociation>
      </reaction>
      <reaction id="R_OUT" reversible="false"
                fbc:lowerFluxBound="lb" fbc:upperFluxBound="ub">
        <listOfReactants>
          <speciesReference species="b" stoichiometry="1" constant="true"/>
        </listOfReactants>
      </reaction>
    </listOfReactions>
    <fbc:listOfObjectives fbc:activeObjective="obj">
      <fbc:objective fbc:id="obj" fbc:type="maximize">
        <fbc:listOfFluxObjectives>
          <fbc:fluxObjective fbc:reaction="R_OUT" fbc:coefficient="1"/>
        </fbc:listOfFluxObjectives>
      </fbc:objective>
    </fbc:listOfObjectives>
    <fbc:listOfGeneProducts>
      <fbc:geneProduct fbc:id="g1" fbc:label="G1"/>
      <fbc:geneProduct fbc:id="g2" fbc:label="G2"/>
      <fbc:geneProduct fbc:id="g3" fbc:label="G3"/>
    </fbc:listOfGeneProducts>
  </model>
</sbml>
""",
        encoding="utf-8",
    )


def test_sparse_loader_preserves_bounds_stoichiometry_objective_and_gene_rule(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "fixture.xml"
    _write_fixture(artifact)

    model = load_sbml_fbc(artifact)

    assert model.model_id == "sparse_fixture"
    assert model.fbc_strict is True
    assert model.compartment_ids == ("c",)
    assert tuple(record.identifier for record in model.species) == ("a", "b")
    assert tuple(record.identifier for record in model.reactions) == (
        "R_IN",
        "R_AB",
        "R_OUT",
    )
    assert model.stoichiometry.shape == (2, 3)
    assert model.stoichiometry.row_indices == (0, 0, 1, 1)
    assert model.stoichiometry.column_indices == (0, 1, 1, 2)
    assert model.stoichiometry.values == (1.0, -2.0, 1.0, -1.0)
    assert model.stoichiometry.to_scipy_csc().toarray().tolist() == [
        [1.0, -2.0, 0.0],
        [0.0, 1.0, -1.0],
    ]
    assert model.reactions[1].gene_product_ids == ("g1", "g2", "g3")
    assert model.reactions[1].gene_rule == "(g1 and (g2 or g3))"
    assert model.active_objective_id == "obj"
    assert model.objectives[0].objective_type == "maximize"
    assert model.objectives[0].flux_objectives[0].reaction_id == "R_OUT"


def test_sparse_loader_rejects_unknown_bound_parameter(tmp_path: Path) -> None:
    artifact = tmp_path / "fixture.xml"
    _write_fixture(artifact, lower_bound_id="missing")

    with pytest.raises(HumanGemFbcError, match="unknown flux-bound"):
        load_sbml_fbc(artifact)


def test_sparse_loader_rejects_dtd_or_entity_input(tmp_path: Path) -> None:
    artifact = tmp_path / "unsafe.xml"
    artifact.write_text(
        """<?xml version="1.0"?><!DOCTYPE sbml [<!ENTITY x "unsafe">]>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
level="3" version="1"><model id="&x;"/></sbml>""",
        encoding="utf-8",
    )

    with pytest.raises(HumanGemFbcError, match="DTD and entity"):
        load_sbml_fbc(artifact)


def test_committed_loader_audit_is_checksum_and_scope_gated() -> None:
    report = load_committed_fbc_loader_audit()
    validate_fbc_loader_audit(report)

    assert report["loaded_structure"]["stoichiometric_shape"] == [8461, 12931]
    assert report["loaded_structure"]["stoichiometric_nonzero_count"] > 0
    assert report["integrity"]["artifact_identity_verified_before_parse"] is True
    assert report["scientific_boundary"]["generic_human_reconstruction_loaded"] is True
    assert report["scientific_boundary"]["healthy_phh_context_extracted"] is False
    assert report["scientific_boundary"]["fba_execution_allowed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_pinned_human_gem_matches_committed_loader_audit() -> None:
    model = load_pinned_human_gem()
    generated = build_fbc_loader_audit(model)
    committed = json.loads(DEFAULT_LOADER_AUDIT_PATH.read_text(encoding="utf-8"))

    assert generated == committed
