"""Declared hepatocyte capability scope with fail-closed quantitative slots.

The atlas is a coverage map, not a claim that every listed capability is already
simulated.  Each entry records the state, dependencies, measurements and history
substrates that a future executable module must expose.  Numerical slots remain
``None`` until matched evidence is curated and validated.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-07-21"
VERSION = "hepatocyte_capability_atlas_v1"

CAPABILITY_ATLAS_SOURCES: dict[str, SourceReference] = {
    "human1_metabolic_atlas": SourceReference(
        id="human1_metabolic_atlas",
        title="An atlas of human metabolism",
        url="https://doi.org/10.1126/scisignal.aaz1482",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Human1 supplies a curated stoichiometric reaction scaffold. It is not a "
            "kinetic, donor-specific hepatocyte trajectory."
        ),
    ),
    "thul2017_subcellular_proteome": SourceReference(
        id="thul2017_subcellular_proteome",
        title="A subcellular map of the human proteome",
        url="https://doi.org/10.1126/science.aal3321",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Image-based human-protein localization atlas across cell lines. It supports "
            "subcellular topology, not healthy-PHH copy numbers or kinetics."
        ),
    ),
    "macparland2018_human_liver_atlas": SourceReference(
        id="macparland2018_human_liver_atlas",
        title="A Human Liver Cell Atlas reveals heterogeneity and epithelial progenitors",
        url="https://doi.org/10.1038/s41467-018-06318-7",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Normal human liver single-cell transcriptomics across nine donors; supports "
            "cell identity and heterogeneity, not protein activity or reaction rates."
        ),
    ),
    "alberts_mbc_capability_scope": SourceReference(
        id="alberts_mbc_capability_scope",
        title="Molecular Biology of the Cell",
        url="https://www.ncbi.nlm.nih.gov/books/NBK21054/",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="General eukaryotic cell-process topology used only to define template scope.",
    ),
}


@dataclass(frozen=True)
class CapabilityParameterSlot:
    id: str
    quantity: str
    unit: str
    value: None
    required_evidence: str


@dataclass(frozen=True)
class HepatocyteCapabilityTemplate:
    id: str
    domain: str
    biological_role: str
    compartments: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    state_variables: tuple[str, ...]
    dependencies: tuple[str, ...]
    parameter_slots: tuple[CapabilityParameterSlot, ...]
    validation_observables: tuple[str, ...]
    history_substrates: tuple[str, ...]
    visual_representation: str
    implementation_refs: tuple[str, ...]
    topology_source_ids: tuple[str, ...]
    template_status: str = "template_non_executable"
    quantitative_activation_allowed: bool = False


def _slot(id: str, quantity: str, unit: str, evidence: str) -> CapabilityParameterSlot:
    return CapabilityParameterSlot(id, quantity, unit, None, evidence)


def _feature(
    id: str,
    domain: str,
    role: str,
    compartments: tuple[str, ...],
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    states: tuple[str, ...],
    dependencies: tuple[str, ...],
    slots: tuple[CapabilityParameterSlot, ...],
    observables: tuple[str, ...],
    history: tuple[str, ...],
    visual: str,
    refs: tuple[str, ...],
    sources: tuple[str, ...],
) -> HepatocyteCapabilityTemplate:
    return HepatocyteCapabilityTemplate(
        id=id,
        domain=domain,
        biological_role=role,
        compartments=compartments,
        inputs=inputs,
        outputs=outputs,
        state_variables=states,
        dependencies=dependencies,
        parameter_slots=slots,
        validation_observables=observables,
        history_substrates=history,
        visual_representation=visual,
        implementation_refs=refs,
        topology_source_ids=sources,
    )


_PHH_RATE = "matched donor-resolved healthy-PHH time course with assay conditions and uncertainty"
_PHH_STATE = "matched healthy-PHH absolute state measurement with compartment and uncertainty"
_HUMAN_FLUX = "human hepatocyte-resolved flux with boundary conditions, units and uncertainty"


HEPATOCYTE_CAPABILITIES: tuple[HepatocyteCapabilityTemplate, ...] = (
    _feature(
        "cell_geometry_and_polarity", "structure",
        "Maintain a polarized hepatocyte boundary with sinusoidal, lateral and canalicular domains.",
        ("plasma_membrane", "sinusoidal_face", "lateral_face", "canalicular_face"),
        ("tissue_geometry", "junction_context"), ("domain_areas", "contact_interfaces"),
        ("cell_boundary", "polarity_axis", "domain_identity"), ("cytoskeleton_and_trafficking",),
        (_slot("domain_surface_area", "surface area by membrane domain", "um2", _PHH_STATE),),
        ("3D boundary mesh", "domain-resolved surface area", "canalicular connectivity"),
        ("cytoskeletal_or_polarity_state",), "Engine geometry and domain-coloured membrane surface.",
        ("human_hepatocyte_3d_morphometry", "spatial_world"),
        ("macparland2018_human_liver_atlas",),
    ),
    _feature(
        "fluid_plasma_membrane", "structure",
        "Provide a laterally fluid, bendable lipid-protein barrier without treating area dilation as shape change.",
        ("plasma_membrane",), ("lipids", "membrane_proteins", "mechanical_load"),
        ("curvature", "surface_transport", "vesicles"),
        ("surface_composition", "curvature", "tension", "area_reservoir"), ("cell_geometry_and_polarity",),
        (_slot("bending_rigidity", "healthy-PHH bending rigidity", "J", _PHH_STATE),
         _slot("surface_viscosity", "healthy-PHH membrane surface viscosity", "Pa s m", _PHH_STATE)),
        ("shape relaxation", "lateral FRAP", "area-volume response"),
        ("lipid_or_membrane_composition", "stable_post_translational_state"),
        "Deforming Eulerian surface with separate membrane-bound tracers.",
        ("membrane_material", "membrane_mechanics"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "cytosol_transport_and_rheology", "structure",
        "Redistribute intracellular water and dissolved species through a crowded porous cytoplasmic scaffold.",
        ("cytosol", "cytoskeleton", "organelle_excluded_volume"),
        ("water", "solutes", "membrane_motion", "active_cytoskeletal_forcing"),
        ("local_velocity", "local_concentration", "pressure_relaxation"),
        ("fluid_velocity", "pressure", "species_concentration", "crowding_state"),
        ("cell_geometry_and_polarity", "cytoskeleton_and_trafficking"),
        (_slot("poroelastic_diffusivity", "healthy-PHH poroelastic diffusivity", "um2/s", _PHH_STATE),
         _slot("species_apparent_diffusivity", "species- and state-specific apparent diffusivity", "um2/s", _PHH_RATE)),
        ("FRAP/FCS diffusion", "microrheology", "volume-relaxation trajectory"),
        ("metabolic_store", "protein_or_aggregate", "cytoskeletal_or_polarity_state"),
        "Subtle advected tracers reading the same volume-preserving membrane deformation.",
        ("cytosol_transport", "intracellular_fluid_visual"),
        ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "cytoskeleton_and_trafficking", "structure",
        "Organize cortex, polarity, organelle positions and directed vesicle transport.",
        ("cytosol", "cell_cortex"), ("ATP", "motor_cargo", "mechanical_signals"),
        ("cargo_delivery", "shape_support", "junction_remodelling"),
        ("actin_state", "microtubule_state", "keratin_state", "motor_occupancy"),
        ("atp_and_redox_homeostasis",),
        (_slot("motor_velocity", "cargo-specific motor velocity", "um/s", _PHH_RATE),),
        ("single-cargo trajectories", "cytoskeletal organization", "delivery-time distributions"),
        ("cytoskeletal_or_polarity_state", "organelle_age_or_quality"),
        "Actin cortex, microtubule tracks and keratin topology.", ("cargo_routing", "visual_cytoskeleton"),
        ("thul2017_subcellular_proteome",),
    ),
    _feature(
        "membrane_receptor_signaling", "communication",
        "Sense soluble ligands and contact-bound partners through domain-local receptors.",
        ("plasma_membrane", "cytosol", "nucleus"), ("ligands", "contact_geometry", "receptors"),
        ("second_messengers", "phosphorylation_state", "gene_regulation"),
        ("surface_receptor_density", "occupancy", "active_complexes"),
        ("fluid_plasma_membrane", "cytosol_transport_and_rheology"),
        (_slot("surface_receptor_density", "active receptor density by domain", "molecules/um2", _PHH_STATE),
         _slot("two_dimensional_binding_rates", "contact-bound association and dissociation", "um2/(molecule s);1/s", _PHH_RATE)),
        ("dose-time signaling", "receptor occupancy", "contact-duration response"),
        ("receptor_desensitization", "stable_post_translational_state"),
        "Local contact patch and receptor-state overlay; no deterministic patch without an external body.",
        ("signaling", "intercellular_communication"), ("macparland2018_human_liver_atlas",),
    ),
    _feature(
        "membrane_transport", "communication",
        "Move ions, nutrients, bile constituents and xenobiotics across the correct membrane domain.",
        ("sinusoidal_face", "canalicular_face", "cytosol"),
        ("substrates", "ion_gradients", "ATP", "transporters"), ("imported_substrates", "exported_products"),
        ("surface_transporter_count", "transport_flux", "electrochemical_gradient"),
        ("cell_geometry_and_polarity", "atp_and_redox_homeostasis"),
        (_slot("active_surface_copy_count", "active transporter copies by domain", "molecules", _PHH_STATE),
         _slot("transporter_turnover", "substrate-specific turnover", "1/s", _PHH_RATE)),
        ("uptake clearance", "canalicular export", "surface localization"),
        ("protein_turnover", "lipid_or_membrane_composition"),
        "Subpixel domain-local protein symbols and geometry-routed cargo.",
        ("transporter_inventory", "geometry_transport_gates"), ("human_hepatocyte_proteome_2016",),
    ),
    _feature(
        "endocytosis_exocytosis", "communication",
        "Internalize membrane/cargo and export secretory or membrane cargo through vesicles.",
        ("plasma_membrane", "endosome", "golgi", "lysosome", "extracellular"),
        ("bound_cargo", "coats", "ATP_GTP"), ("endosomes", "secreted_cargo", "recycled_membrane"),
        ("vesicle_count", "cargo_identity", "route_state"),
        ("fluid_plasma_membrane", "cytoskeleton_and_trafficking"),
        (_slot("vesicle_budding_rate", "cargo- and domain-specific budding rate", "events/s", _PHH_RATE),),
        ("single-vesicle trajectories", "cargo recovery", "surface-area balance"),
        ("protein_turnover", "lipid_or_membrane_composition"),
        "Membrane-connected vesicle trajectories.", ("cargo_routing",),
        ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "genome_architecture", "information",
        "Store the diploid/polyploid genome in chromosome and nuclear spatial context.",
        ("nucleus",), ("DNA", "nuclear_lamina"), ("accessible_loci", "replication_templates"),
        ("ploidy", "chromosome_copy_state", "locus_coordinates", "chromatin_domains"), (),
        (_slot("donor_ploidy_state", "single-cell donor ploidy", "chromosome sets", _PHH_STATE),),
        ("single-cell DNA sequencing", "karyotype", "3D genome contacts"),
        ("genetic", "histone_or_chromatin"), "Chromosome territories and locus markers.",
        ("genome", "genomic_architecture"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "epigenetic_regulation", "information",
        "Regulate persistent locus accessibility through DNA methylation and chromatin state.",
        ("nucleus",), ("chromatin_modifiers", "metabolic_cofactors", "signals"),
        ("accessibility", "transcriptional_competence"),
        ("DNA_methylation", "histone_marks", "enhancer_promoter_state"), ("genome_architecture",),
        (_slot("mark_write_erase_rates", "locus-specific chromatin transition rates", "1/s", _PHH_RATE),),
        ("matched ATAC-seq", "methylome", "histone ChIP-seq with washout/rechallenge"),
        ("dna_methylation", "histone_or_chromatin"), "Locus-state overlays only when measured.",
        ("cellular_memory", "genomic_architecture"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "transcription_rna_processing", "information",
        "Produce, splice, export and degrade gene-specific RNA.",
        ("nucleus", "nuclear_pore", "cytosol"), ("DNA_template", "nucleotides", "ATP", "transcription_factors"),
        ("pre_mRNA", "mature_mRNA"),
        ("promoter_state", "nascent_RNA", "mature_RNA", "RNA_half_life"),
        ("genome_architecture", "epigenetic_regulation"),
        (_slot("transcription_burst_kinetics", "gene- and state-specific burst kinetics", "1/s", _PHH_RATE),
         _slot("mrna_decay_rate", "gene-specific cytosolic mRNA decay", "1/s", _PHH_RATE)),
        ("nascent RNA", "absolute RNA copies", "pulse-chase decay"),
        ("transcriptional_network", "rna_or_ribonucleoprotein_state"),
        "Engine-event-driven transcripts from loci through nuclear pores.",
        ("gene_expression",), ("macparland2018_human_liver_atlas",),
    ),
    _feature(
        "translation_and_proteome", "information",
        "Translate mRNA into cytosolic, organellar and secretory proteins.",
        ("cytosol", "rough_er"), ("mRNA", "ribosomes", "amino_acids", "ATP_GTP"),
        ("nascent_protein", "protein_copy_number"),
        ("ribosome_occupancy", "protein_synthesis", "protein_abundance"),
        ("transcription_rna_processing", "atp_and_redox_homeostasis"),
        (_slot("translation_rate", "gene-specific translation rate", "proteins/(mRNA s)", _PHH_RATE),),
        ("ribosome profiling", "dynamic proteomics", "pulse SILAC"),
        ("protein_turnover", "protein_or_aggregate"),
        "Subpixel ribosome/protein density and selected deposited structures.",
        ("central_dogma", "phh_proteome_atlas"),
        ("human_hepatocyte_proteome_2016", "thul2017_subcellular_proteome"),
    ),
    _feature(
        "proteostasis_er_upr", "maintenance",
        "Fold, modify, retain, degrade and signal from secretory-pathway proteins.",
        ("rough_er", "cytosol", "proteasome", "nucleus"),
        ("nascent_secretory_protein", "chaperones", "ATP", "ER_calcium"),
        ("folded_cargo", "ERAD_cargo", "UPR_signal"),
        ("folding_load", "misfolded_load", "UPR_branches", "proteasome_capacity"),
        ("translation_and_proteome", "calcium_ph_ion_homeostasis"),
        (_slot("protein_turnover_rates", "protein-class synthesis and degradation", "1/s", _PHH_RATE),),
        ("pulse-chase proteomics", "UPR dose-time markers", "ERAD flux"),
        ("protein_or_aggregate", "stable_post_translational_state"),
        "Connected ER, ribosomes, proteasome and burden overlay.",
        ("proteostasis", "cellular_response"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "golgi_sorting_and_secretion", "maintenance",
        "Modify and route proteins/lipids to sinusoidal, canalicular, lysosomal or membrane destinations.",
        ("er", "golgi", "vesicles", "plasma_membrane"), ("folded_cargo", "ATP_GTP"),
        ("albumin", "membrane_cargo", "lysosomal_cargo", "canalicular_cargo"),
        ("cargo_occupancy", "glycoform", "destination", "delivery_state"),
        ("proteostasis_er_upr", "cytoskeleton_and_trafficking"),
        (_slot("cargo_transit_time", "cargo-specific ER-to-surface transit distribution", "s", _PHH_RATE),),
        ("secretome time course", "glycoform profiling", "live cargo tracking"),
        ("protein_turnover", "organelle_composition"), "Connected ER-Golgi-vesicle paths.",
        ("cargo_routing", "albumin_secretion"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "autophagy_lysosome", "maintenance",
        "Remove and recycle damaged proteins, organelles and endocytic cargo.",
        ("cytosol", "autophagosome", "lysosome"), ("damaged_cargo", "ATP", "lysosomal_enzymes"),
        ("recycled_monomers", "residual_bodies"),
        ("autophagic_flux", "lysosomal_pH", "cargo_damage"),
        ("proteostasis_er_upr", "atp_and_redox_homeostasis"),
        (_slot("autophagic_flux", "cargo-class autophagic flux", "fraction/s", _PHH_RATE),),
        ("LC3 flux", "lysosomal pH", "cargo clearance"),
        ("protein_or_aggregate", "organelle_age_or_quality"), "Autophagosome-to-lysosome cargo routes.",
        ("autophagy", "lysosome_module"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "mitochondrial_energy_and_dynamics", "organelle",
        "Generate ATP, couple TCA/respiration, buffer calcium and maintain mitochondrial quality.",
        ("mitochondrial_matrix", "inner_membrane", "intermembrane_space", "cytosol"),
        ("carbon_substrates", "oxygen", "ADP", "phosphate"), ("ATP", "CO2", "ROS", "heat"),
        ("membrane_potential", "adenylates", "redox_pairs", "mitochondrial_quality"),
        ("cytosol_transport_and_rheology", "autophagy_lysosome"),
        (_slot("oxygen_consumption", "donor- and state-specific mitochondrial oxygen consumption", "mol/(cell s)", _PHH_RATE),
         _slot("proton_leak", "mitochondrial proton leak", "mol/(cell s)", _PHH_RATE)),
        ("OCR/ECAR", "ATP production", "membrane potential", "mitophagy flux"),
        ("mitochondrial", "organelle_age_or_quality", "damage_response"),
        "Cristae-bearing distributed mitochondria whose activity reads engine state.",
        ("compartmental_energy_redox", "oxphos", "mitophagy"),
        ("human_hepatocyte_proteome_2016",),
    ),
    _feature(
        "peroxisomal_metabolism", "organelle",
        "Oxidize very-long-chain lipids and control peroxide through catalase-linked pathways.",
        ("peroxisome", "cytosol"), ("very_long_chain_fatty_acids", "oxygen"),
        ("shortened_acyl_products", "H2O2", "water"),
        ("substrate_load", "catalase_state", "organelle_quality"),
        ("fatty_acid_oxidation_ketogenesis", "redox_and_glutathione"),
        (_slot("peroxisomal_flux", "substrate-specific peroxisomal oxidation flux", "mol/(cell s)", _PHH_RATE),),
        ("isotope flux", "H2O2 handling", "peroxisome abundance"),
        ("organelle_age_or_quality", "damage_response"), "Distributed peroxisome population.",
        ("peroxisome_module",), ("human_hepatocyte_proteome_2016",),
    ),
    _feature(
        "glucose_exchange_and_glycolysis", "metabolism",
        "Exchange glucose with blood and interconvert glucose, lactate and pyruvate.",
        ("sinusoid", "cytosol"), ("glucose", "lactate", "ADP", "NAD"),
        ("pyruvate", "ATP", "NADH", "glucose_output"),
        ("metabolite_concentrations", "reaction_fluxes", "transporter_state"),
        ("membrane_transport", "atp_and_redox_homeostasis"),
        (_slot("reaction_fluxes", "reaction-resolved glucose pathway fluxes", "mol/(cell s)", _HUMAN_FLUX),),
        ("exact-protocol PHH glucose exchange", "13C flux", "intracellular metabolites"),
        ("metabolic_store", "stable_post_translational_state"), "Local concentration and routed glucose flux overlays.",
        ("exact_glucose_homeostasis", "glucose_open_system"), ("human1_metabolic_atlas",),
    ),
    _feature(
        "glycogen_homeostasis", "metabolism",
        "Store or mobilize glucose as glycogen in response to nutritional and hormonal state.",
        ("cytosol",), ("glucose_6_phosphate", "UTP", "hormonal_signals"),
        ("glycogen", "glucose_6_phosphate"),
        ("glycogen_amount", "branch_structure", "synthase_phosphorylation", "phosphorylase_phosphorylation"),
        ("glucose_exchange_and_glycolysis", "membrane_receptor_signaling"),
        (_slot("glycogen_turnover", "synthesis and breakdown flux", "mol_glucosyl/(cell s)", _HUMAN_FLUX),),
        ("absolute glycogen time course", "hormone perturbation", "isotopic turnover"),
        ("metabolic_store", "stable_post_translational_state"), "Glycogen rosettes proportional only to authorized state.",
        ("glycogen_control", "nutritional_homeostasis"), ("human1_metabolic_atlas",),
    ),
    _feature(
        "gluconeogenesis", "metabolism",
        "Produce glucose from lactate, glycerol and glucogenic amino-acid carbon.",
        ("mitochondria", "cytosol", "er", "sinusoid"),
        ("lactate", "glycerol", "alanine", "ATP_GTP", "redox"), ("glucose", "urea"),
        ("reaction_fluxes", "substrate_state", "hormonal_control"),
        ("glucose_exchange_and_glycolysis", "amino_acid_and_urea_cycle"),
        (_slot("gluconeogenic_flux", "substrate-resolved gluconeogenic flux", "mol/(cell s)", _HUMAN_FLUX),),
        ("13C flux", "substrate balance", "glucose output"),
        ("metabolic_store", "transcriptional_network"), "Cross-compartment pathway overlay.",
        ("integrated_metabolism",), ("human1_metabolic_atlas",),
    ),
    _feature(
        "tca_cycle", "metabolism",
        "Oxidize acetyl-CoA and supply biosynthetic intermediates and reducing equivalents.",
        ("mitochondrial_matrix",), ("acetyl_CoA", "NAD", "FAD", "ADP_GDP"),
        ("CO2", "NADH", "FADH2", "ATP_GTP"), ("metabolite_concentrations", "reaction_fluxes"),
        ("mitochondrial_energy_and_dynamics",),
        (_slot("tca_fluxes", "reaction-resolved TCA flux", "mol/(cell s)", _HUMAN_FLUX),),
        ("13C isotopologues", "oxygen consumption", "compartment metabolites"),
        ("metabolic_store", "mitochondrial"), "Mitochondrial pathway overlay.",
        ("compartmental_energy_redox",), ("human1_metabolic_atlas",),
    ),
    _feature(
        "fatty_acid_oxidation_ketogenesis", "metabolism",
        "Oxidize fatty acids and produce ketone bodies during fasting.",
        ("cytosol", "mitochondria", "peroxisome", "sinusoid"),
        ("fatty_acids", "carnitine", "CoA", "NAD_FAD"),
        ("acetyl_CoA", "ATP", "beta_hydroxybutyrate", "acetoacetate"),
        ("acyl_pool", "malonyl_CoA", "reaction_fluxes", "redox_ratio"),
        ("mitochondrial_energy_and_dynamics", "peroxisomal_metabolism"),
        (_slot("beta_oxidation_flux", "chain-length-resolved oxidation flux", "mol/(cell s)", _HUMAN_FLUX),),
        ("acylcarnitines", "ketone output", "isotope flux"),
        ("metabolic_store", "transcriptional_network"), "Mitochondria/peroxisome and ketone-flow overlay.",
        ("ketogenesis", "malonyl_coa_node"), ("human1_metabolic_atlas",),
    ),
    _feature(
        "lipogenesis_lipid_droplets", "metabolism",
        "Synthesize, store and mobilize neutral and membrane lipids.",
        ("cytosol", "smooth_er", "lipid_droplet", "golgi"),
        ("acetyl_CoA", "NADPH", "fatty_acids", "glycerol"),
        ("triacylglycerol", "phospholipids", "VLDL_cargo"),
        ("lipid_species", "droplet_volume", "synthesis_lipolysis_flux"),
        ("fatty_acid_oxidation_ketogenesis", "golgi_sorting_and_secretion"),
        (_slot("lipid_fluxes", "species-resolved lipid synthesis and turnover", "mol/(cell s)", _HUMAN_FLUX),),
        ("lipidomics", "droplet-volume trajectory", "VLDL secretion"),
        ("metabolic_store", "lipid_or_membrane_composition"), "Aggregate lipid-droplet fraction only; no invented dynamics.",
        ("lipid_metabolism", "human_hepatocyte_3d_morphometry"), ("human1_metabolic_atlas",),
    ),
    _feature(
        "amino_acid_and_urea_cycle", "metabolism",
        "Handle amino-acid carbon/nitrogen and detoxify ammonia as urea.",
        ("cytosol", "mitochondria", "sinusoid"),
        ("amino_acids", "ammonia", "bicarbonate", "ATP"),
        ("urea", "carbon_skeletons", "fumarate"),
        ("amino_acid_pools", "ammonia", "urea_cycle_intermediates", "reaction_fluxes"),
        ("mitochondrial_energy_and_dynamics",),
        (_slot("ureagenesis_flux", "ammonia-to-urea flux", "mol/(cell s)", _HUMAN_FLUX),),
        ("nitrogen balance", "urea output", "isotope flux"),
        ("metabolic_store", "mitochondrial"), "Mitochondria-cytosol urea-cycle overlay.",
        ("urea_cycle", "amino_acid_catabolism"), ("human1_metabolic_atlas",),
    ),
    _feature(
        "bile_acid_synthesis_and_export", "specialized_function",
        "Synthesize, conjugate and export bile acids into the canaliculus.",
        ("smooth_er", "cytosol", "canalicular_membrane", "bile_canaliculus"),
        ("cholesterol", "ATP", "CoA", "transporters"), ("conjugated_bile_acids", "canalicular_bile"),
        ("bile_acid_species", "canalicular_export", "transporter_state"),
        ("membrane_transport", "atp_and_redox_homeostasis"),
        (_slot("species_resolved_bile_flux", "bile-acid species synthesis/export", "mol/(cell s)", _HUMAN_FLUX),),
        ("SCH bile compartments", "species-resolved efflux", "canalicular concentration"),
        ("metabolic_store", "protein_turnover", "damage_response"), "Canalicular domain and export trajectories.",
        ("human_sch_bile_acids", "transporter_inventory"), ("human1_metabolic_atlas",),
    ),
    _feature(
        "bilirubin_handling", "specialized_function",
        "Take up, conjugate and excrete bilirubin-derived cargo.",
        ("sinusoidal_membrane", "cytosol", "er", "canalicular_membrane"),
        ("bilirubin", "UDP_glucuronate", "ATP"), ("bilirubin_conjugates", "canalicular_output"),
        ("bilirubin_species", "UGT_state", "MRP2_state"),
        ("membrane_transport", "xenobiotic_metabolism"),
        (_slot("bilirubin_clearance", "substrate-resolved bilirubin handling", "mol/(cell s)", _HUMAN_FLUX),),
        ("uptake/conjugation/export balance", "canalicular output"),
        ("metabolic_store", "protein_turnover"), "Sinusoid-to-ER-to-canaliculus cargo path.",
        ("cargo_routing", "transporter_inventory"), ("human1_metabolic_atlas",),
    ),
    _feature(
        "xenobiotic_metabolism", "specialized_function",
        "Transform and export xenobiotics through phase I, II and III processes.",
        ("sinusoidal_membrane", "smooth_er", "cytosol", "canalicular_membrane"),
        ("xenobiotics", "oxygen", "NADPH", "conjugating_cofactors"),
        ("metabolites", "conjugates", "ROS"),
        ("compound_concentration", "enzyme_activity", "metabolite_flux", "toxicity_state"),
        ("membrane_transport", "redox_and_glutathione"),
        (_slot("compound_specific_clearance", "enzyme/transporter-resolved intrinsic clearance", "volume/(cell s)", _PHH_RATE),),
        ("compound-specific metabolite time course", "CYP activity", "mass balance"),
        ("protein_turnover", "damage_response", "transcriptional_network"), "Compound-specific routes only when an experiment is selected.",
        ("detox", "phh_cyp_function"), ("human_hepatocyte_proteome_2016",),
    ),
    _feature(
        "redox_and_glutathione", "homeostasis",
        "Maintain compartment-resolved redox couples and detoxify reactive species.",
        ("cytosol", "mitochondria", "er", "peroxisome"),
        ("NADPH", "GSH", "ROS", "oxygen"), ("GSSG", "water", "oxidized_targets"),
        ("NADH_NAD", "NADPH_NADP", "GSH_GSSG", "ROS_species"),
        ("mitochondrial_energy_and_dynamics", "peroxisomal_metabolism"),
        (_slot("redox_fluxes", "compartment- and reaction-resolved redox flux", "mol/(cell s)", _HUMAN_FLUX),),
        ("compartment redox sensors", "GSH/GSSG", "ROS time course"),
        ("damage_response", "stable_post_translational_state"), "Compartment-specific redox overlays.",
        ("compartmental_energy_redox",), ("human1_metabolic_atlas",),
    ),
    _feature(
        "atp_and_redox_homeostasis", "homeostasis",
        "Balance ATP production, transport and consumption across compartments.",
        ("cytosol", "mitochondria", "er", "nucleus", "membranes"),
        ("ADP", "phosphate", "fuels", "oxygen"), ("ATP", "AMP", "heat"),
        ("adenylates", "energy_charge", "local_ATP", "maintenance_demand"),
        ("mitochondrial_energy_and_dynamics", "glucose_exchange_and_glycolysis"),
        (_slot("compartment_atp_turnover", "production and demand by compartment", "mol/(cell s)", _HUMAN_FLUX),),
        ("ATP/ADP/AMP by compartment", "oxygen consumption", "maintenance demand"),
        ("metabolic_store", "mitochondrial"), "Local ATP field only when diffusion and demand are identified.",
        ("compartmental_energy_redox",), ("human1_metabolic_atlas",),
    ),
    _feature(
        "calcium_ph_ion_homeostasis", "homeostasis",
        "Maintain membrane potential, osmotic balance, pH and compartmental calcium signals.",
        ("cytosol", "er", "mitochondria", "lysosome", "plasma_membrane"),
        ("Na", "K", "Cl", "Ca", "protons", "ATP"), ("electrochemical_gradients", "calcium_signals"),
        ("ion_concentrations", "membrane_potential", "pH", "channel_pump_state"),
        ("membrane_transport", "atp_and_redox_homeostasis"),
        (_slot("ion_transport_kinetics", "channel/pump-specific conductance and turnover", "context_specific", _PHH_RATE),),
        ("patch clamp", "ion imaging", "compartment pH time course"),
        ("receptor_desensitization", "stable_post_translational_state"), "Membrane/calcium fields with explicit source status.",
        ("membrane_ca", "brian2_boundary"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "secreted_plasma_proteins", "specialized_function",
        "Synthesize and secrete albumin and other hepatocyte-derived plasma proteins.",
        ("nucleus", "rough_er", "golgi", "sinusoidal_membrane"),
        ("amino_acids", "ATP_GTP", "gene_program"), ("albumin", "coagulation_and_carrier_proteins"),
        ("mRNA", "protein_cargo", "secretion_flux"),
        ("translation_and_proteome", "golgi_sorting_and_secretion"),
        (_slot("protein_secretion_rates", "protein-specific secretion rate", "molecules/(cell s)", _PHH_RATE),),
        ("absolute secretome time course", "intracellular cargo", "cell viability"),
        ("transcriptional_network", "protein_turnover"), "ER-Golgi-sinusoid secretory routes.",
        ("phh_albumin_secretion", "cargo_routing"), ("human_hepatocyte_proteome_2016",),
    ),
    _feature(
        "zonation_and_sinusoid_coupling", "tissue_context",
        "Respond to spatial oxygen, nutrient, hormone and paracrine gradients across the liver lobule.",
        ("sinusoid", "space_of_disse", "hepatocyte"),
        ("oxygen_gradient", "nutrients", "hormones", "neighbour_signals"),
        ("zone_specific_expression", "zone_specific_flux"),
        ("lobular_position", "boundary_conditions", "zone_identity"),
        ("membrane_receptor_signaling", "membrane_transport"),
        (_slot("human_boundary_gradients", "matched human sinusoid-to-hepatocyte boundary conditions", "analyte_specific", _PHH_STATE),),
        ("spatial transcriptomics/proteomics", "oxygen/nutrient gradients", "zone-resolved flux"),
        ("external_niche", "transcriptional_network"), "Sinusoid/Disse/canalicular spatial context.",
        ("zonation_state", "sinusoid_homeostasis"), ("macparland2018_human_liver_atlas",),
    ),
    _feature(
        "cell_contact_and_junctions", "tissue_context",
        "Form geometry-dependent hepatocyte and non-parenchymal contacts, junctions and exchange surfaces.",
        ("plasma_membrane", "junctions", "extracellular_space"),
        ("surface_geometry", "adhesion_pairs", "mechanical_load"),
        ("contact_domains", "junction_state", "local_signals"),
        ("contact_patch", "adhesion_bonds", "junction_permeability"),
        ("fluid_plasma_membrane", "membrane_receptor_signaling"),
        (_slot("adhesion_kinetics", "pair-specific two-dimensional adhesion kinetics", "context_specific", _PHH_RATE),),
        ("contact-area trajectories", "junction permeability", "mechanotransduction"),
        ("external_niche", "cytoskeletal_or_polarity_state"), "Random external-body-dependent contact patches.",
        ("spatial_world", "intercellular_communication"), ("macparland2018_human_liver_atlas",),
    ),
    _feature(
        "innate_inflammatory_response", "tissue_context",
        "Integrate cytokine, pattern-recognition and acute-phase programs without pretending the hepatocyte is an immune cell.",
        ("plasma_membrane", "cytosol", "nucleus", "secretory_pathway"),
        ("cytokines", "PAMP_DAMP_signals"), ("acute_phase_proteins", "chemokines", "stress_programs"),
        ("receptor_state", "NFkB_STAT_state", "acute_phase_expression"),
        ("membrane_receptor_signaling", "transcription_rna_processing"),
        (_slot("cytokine_response_kinetics", "ligand-dose and time-dependent response", "context_specific", _PHH_RATE),),
        ("dose-time phosphoproteomics", "transcriptomics", "secretome"),
        ("external_niche", "transcriptional_network", "damage_response"), "Signal-chain overlays only for explicit exposures.",
        ("cellular_response",), ("macparland2018_human_liver_atlas",),
    ),
    _feature(
        "dna_damage_and_repair", "cell_fate",
        "Detect and repair DNA lesions while retaining verified somatic sequence changes as stable history.",
        ("nucleus",), ("DNA_lesions", "repair_factors", "ATP"), ("repaired_DNA", "mutations", "checkpoint_signals"),
        ("lesion_burden", "repair_pathway_state", "somatic_variants"),
        ("genome_architecture", "atp_and_redox_homeostasis"),
        (_slot("lesion_repair_kinetics", "lesion-class repair kinetics", "events/(cell s)", _PHH_RATE),),
        ("lesion-specific repair time course", "single-cell somatic variants", "checkpoint markers"),
        ("genetic", "dna_damage_or_repair_scar", "damage_response"), "Damage foci only when driven by explicit state.",
        ("dna_repair", "cellular_memory"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "cell_cycle_and_regeneration", "cell_fate",
        "Remain quiescent at baseline and re-enter a checkpoint-controlled cycle under validated regenerative context.",
        ("whole_cell", "nucleus", "centrosome", "membrane"),
        ("mitogens", "nutrients", "damage_checkpoints"), ("DNA_replication", "daughter_cells"),
        ("cycle_phase", "biomass", "DNA_content", "checkpoint_state"),
        ("dna_damage_and_repair", "atp_and_redox_homeostasis"),
        (_slot("human_regeneration_timing", "human hepatocyte phase and division timing", "s", _PHH_RATE),),
        ("human lineage tracing", "phase-resolved time course", "division outcomes"),
        ("lineage_state", "genetic", "replication_coupled_epigenetic"), "No daughter rendering without an engine division event.",
        ("whole_cell_cycle", "hepatocyte_regeneration"), ("macparland2018_human_liver_atlas",),
    ),
    _feature(
        "senescence_apoptosis_and_necrosis", "cell_fate",
        "Resolve reversible stress, stable arrest and distinct death programs from measured commitment markers.",
        ("whole_cell", "mitochondria", "nucleus", "plasma_membrane"),
        ("damage", "ATP_state", "death_receptor_signals"),
        ("recovery", "senescence", "apoptosis", "necrosis"),
        ("commitment_markers", "caspase_state", "membrane_integrity", "senescence_program"),
        ("dna_damage_and_repair", "mitochondrial_energy_and_dynamics"),
        (_slot("fate_hazards", "cause- and state-specific human-PHH fate hazards", "1/s", _PHH_RATE),),
        ("single-cell fate trajectories", "commitment markers", "washout recovery"),
        ("damage_response", "histone_or_chromatin", "protein_or_aggregate"), "Evidence-state halo, never an inferred irreversible fate.",
        ("apoptosis", "cellular_response"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "cellular_history_and_memory", "history",
        "Retain causal history only in physical molecular or structural substrates whose persistence is observed.",
        ("genome", "chromatin", "proteome", "organelles", "metabolic_stores", "membranes", "external_niche"),
        ("experience_events", "writer_processes"), ("persistent_traces", "altered_future_response"),
        ("event_log", "memory_traces", "lineage", "substrate_age"),
        ("all_capabilities",),
        (_slot("memory_write_read_decay", "substrate-specific write/read/decay or dilution law", "context_specific", _PHH_RATE),),
        ("washout persistence", "rechallenge", "lineage inheritance", "direct substrate assay"),
        ("all_declared_memory_substrates",), "History inspector separates events from persistent traces.",
        ("cellular_memory", "history"), ("alberts_mbc_capability_scope",),
    ),
    _feature(
        "host_pathogen_interaction", "future_interaction",
        "Represent receptor-, geometry- and cargo-dependent viral or bacterial interaction with the hepatocyte.",
        ("extracellular", "plasma_membrane", "endosome", "cytosol", "nucleus"),
        ("pathogen_body", "contact_geometry", "receptor_pairs"),
        ("entry", "innate_response", "replication_effects", "clearance"),
        ("bound_complexes", "internalized_cargo", "pathogen_state", "host_response"),
        ("cell_contact_and_junctions", "endocytosis_exocytosis", "innate_inflammatory_response"),
        (_slot("entry_and_replication_kinetics", "pathogen- and receptor-specific kinetics", "context_specific", _PHH_RATE),),
        ("binding/entry time course", "single-cell infection outcome", "perturbation rescue"),
        ("external_niche", "transcriptional_network", "damage_response"), "External bodies appear only in selected scenarios.",
        ("virus", "spatial_world"), ("alberts_mbc_capability_scope",),
    ),
)


_REQUIRED_DOMAINS = frozenset(
    {
        "structure", "communication", "information", "maintenance", "organelle",
        "metabolism", "specialized_function", "homeostasis", "tissue_context",
        "cell_fate", "history", "future_interaction",
    }
)


def validate_hepatocyte_capability_atlas(
    features: tuple[HepatocyteCapabilityTemplate, ...] = HEPATOCYTE_CAPABILITIES,
) -> None:
    if not features:
        raise ValueError("capability atlas cannot be empty")
    ids = tuple(feature.id for feature in features)
    if len(set(ids)) != len(ids):
        raise ValueError("capability atlas contains duplicate feature ids")
    domains = frozenset(feature.domain for feature in features)
    if not _REQUIRED_DOMAINS.issubset(domains):
        raise ValueError(f"capability atlas is missing domains: {sorted(_REQUIRED_DOMAINS - domains)}")
    known_sources = set(CAPABILITY_ATLAS_SOURCES) | {
        "human_hepatocyte_proteome_2016",
    }
    for feature in features:
        if feature.template_status != "template_non_executable":
            raise ValueError(f"{feature.id} template unexpectedly became executable")
        if feature.quantitative_activation_allowed:
            raise ValueError(f"{feature.id} template may not activate quantitative behavior")
        if not feature.biological_role or not feature.compartments or not feature.state_variables:
            raise ValueError(f"{feature.id} is missing its structural contract")
        if not feature.validation_observables or not feature.topology_source_ids:
            raise ValueError(f"{feature.id} is missing validation or source requirements")
        unknown = set(feature.topology_source_ids) - known_sources
        if unknown:
            raise ValueError(f"{feature.id} references unknown capability source ids: {sorted(unknown)}")
        for slot in feature.parameter_slots:
            if slot.value is not None:
                raise ValueError(f"{feature.id}.{slot.id} must remain null until evidence intake")
            if not slot.required_evidence:
                raise ValueError(f"{feature.id}.{slot.id} lacks an evidence requirement")


def hepatocyte_capability_atlas_snapshot() -> dict[str, object]:
    validate_hepatocyte_capability_atlas()
    domains = tuple(sorted({feature.domain for feature in HEPATOCYTE_CAPABILITIES}))
    parameter_slots = sum(len(feature.parameter_slots) for feature in HEPATOCYTE_CAPABILITIES)
    return {
        "version": VERSION,
        "status": "coverage_scope_declared_quantitative_activation_blocked",
        "scope": (
            "Canonical healthy-adult human hepatocyte capabilities plus explicitly future "
            "interaction surfaces. Completeness applies to this declared engineering scope, "
            "not to all discoverable human biology."
        ),
        "policy": (
            "A feature template may define topology, state names, dependencies and required "
            "measurements. It may not contribute a numerical state transition, rate, hazard "
            "or prediction until its parameter slots are source-qualified and independently "
            "validated for the stated context."
        ),
        "domains": domains,
        "features": to_plain(HEPATOCYTE_CAPABILITIES),
        "source_ids": tuple(CAPABILITY_ATLAS_SOURCES),
        "summary": {
            "declared_domain_count": len(domains),
            "feature_template_count": len(HEPATOCYTE_CAPABILITIES),
            "parameter_slot_count": parameter_slots,
            "filled_parameter_slot_count": 0,
            "quantitatively_activated_template_count": 0,
            "template_non_executable_count": len(HEPATOCYTE_CAPABILITIES),
            "biological_accuracy_pct": None,
        },
        "limitations": (
            "The atlas is a bounded capability checklist, not an exhaustive ontology of every hepatocyte molecule or reaction.",
            "Implementation references may point to exploratory or source-backed project surfaces; the template itself never upgrades their authority.",
            "A topology source cannot fill a kinetic parameter slot.",
        ),
    }
