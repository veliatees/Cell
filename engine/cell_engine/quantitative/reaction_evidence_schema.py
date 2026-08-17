"""Dependency-free schema constants for reaction-evidence intake and audit."""

from __future__ import annotations


REACTION_EVIDENCE_SLOT_SPECS: tuple[tuple[str, str, str, str], ...] = (
    (
        "biochemical_identity",
        "exact enzyme/reaction identity including isoform and direction",
        "identifier",
        "same biochemical event",
    ),
    (
        "biological_compartment",
        "subcellular compartment and membrane side",
        "identifier",
        "healthy human hepatocyte",
    ),
    (
        "symbolic_rate_law",
        "complete symbolic rate equation",
        "equation",
        "same substrates, products, effectors and direction",
    ),
    (
        "km",
        "substrate-specific Michaelis or half-saturation constants",
        "M",
        "same isoform and assay conditions",
    ),
    (
        "kcat",
        "enzyme turnover number",
        "1/s",
        "same isoform, temperature, pH and cofactors",
    ),
    (
        "ki_or_allostery",
        "inhibition and allosteric constants",
        "context_specific",
        "same inhibitor/effector and assay conditions",
    ),
    (
        "vmax",
        "maximum reaction capacity",
        "mol/(cell s)",
        "same healthy-PHH context and active enzyme state",
    ),
    (
        "active_enzyme_abundance",
        "active localized enzyme abundance",
        "molecules/cell",
        "matched donor, compartment, PTM and complex state",
    ),
    (
        "assay_temperature",
        "assay temperature",
        "degC",
        "reported by the kinetic source",
    ),
    (
        "assay_ph",
        "assay pH",
        "pH",
        "reported by the kinetic source",
    ),
    (
        "intracellular_flux",
        "reaction-resolved intracellular flux",
        "mol/(cell s)",
        "matched human hepatocyte isotope/flux experiment",
    ),
    (
        "heldout_validation",
        "independent same-format held-out result",
        "validation_result",
        "donor-disjoint frozen-model evaluation",
    ),
)


__all__ = ["REACTION_EVIDENCE_SLOT_SPECS"]
