from __future__ import annotations

from cell_engine.core.cell_definition import (
    CellDefinition,
    CompartmentDefinition,
    GeometryDefinition,
    OrganelleDefinition,
    PoolDefinition,
    StochasticPolicy,
    ValidationTarget,
)
from cell_engine.core.provenance import ParameterProvenance, SourceReference
from cell_engine.core.genome import build_reference_hepatocyte_genome
from cell_engine.core.expression import build_initial_hepatocyte_expression
from cell_engine.core.genomic_architecture import build_genomic_architecture
from cell_engine.core.history import initial_cell_history
from cell_engine.core.state import CargoPacket, CellEvent, CellState, OrganelleState, PoolState
from cell_engine.quantitative.geometry import (
    HEPATOCYTE_CANONICAL_POLARITY_AXIS,
    HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
    HEPATOCYTE_REFERENCE_VOLUME_UM3,
)

DATE_VERIFIED = "2026-06-19"
HEPATOCYTE_EQUIVALENT_SPHERE_RADIUS_UM = HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM / 2.0


def build_hepatocyte_definition(zone: str = "midlobular") -> CellDefinition:
    sources = {
        "alberts_mbc": SourceReference(
            id="alberts_mbc",
            title="Molecular Biology of the Cell, NCBI Bookshelf",
            url="https://www.ncbi.nlm.nih.gov/books/NBK21054/",
            source_type="textbook",
            date_verified=DATE_VERIFIED,
            notes="Broad cell biology reference for organelle function and cross-organelle stress responses.",
        ),
        "cell_biology_by_numbers": SourceReference(
            id="cell_biology_by_numbers",
            title="Cell Biology by the Numbers",
            url="https://book.bionumbers.org/",
            source_type="database",
            date_verified=DATE_VERIFIED,
            notes="Quantitative reference for sizes, concentrations, copy numbers, and order-of-magnitude checks.",
        ),
        "olander2021_human_hepatocyte_size": SourceReference(
            id="olander2021_human_hepatocyte_size",
            title="Hepatocyte size fractionation allows dissection of human liver zonation",
            url="https://doi.org/10.1002/jcp.30273",
            source_type="primary_paper",
            date_verified="2026-07-15",
            notes="Median diameter 18.4 um across 54 isolated cryopreserved primary-human-hepatocyte batches; 88% were 12-26 um.",
        ),
        "duarte1989_human_hepatocyte_volume": SourceReference(
            id="duarte1989_human_hepatocyte_volume",
            title="Baseline volume data of human liver parenchymal cell",
            url="https://pubmed.ncbi.nlm.nih.gov/2752360/",
            source_type="primary_paper",
            date_verified="2026-07-17",
            notes="Normal-human in-situ intermediate-zone mean hepatocyte volume 2850 +/- 99.9 um3 in five selected cases; uncertainty statistic not identified in the abstract.",
        ),
        "segovia_miranda2019_human_liver_3d_morphometry": SourceReference(
            id="segovia_miranda2019_human_liver_3d_morphometry",
            title="Three-dimensional spatially resolved geometrical and functional models of human liver tissue reveal new aspects of NAFLD progression",
            url="https://doi.org/10.1038/s41591-019-0660-7",
            source_type="primary_paper",
            date_verified="2026-07-17",
            notes="Normal-control human liver 3D reconstructions report median hepatocyte volume 5657.07116 um3 with MAD 744.875484 um3 across five reconstructions at 0.3 um isotropic voxels.",
        ),
        "project_roadmap_07": SourceReference(
            id="project_roadmap_07",
            title="Integrated Cell Engine Roadmap",
            url="docs/07-integrated-cell-engine-roadmap.md",
            source_type="project_assumption",
            date_verified=DATE_VERIFIED,
            notes="Project-specific hepatocyte-first engine boundary and stochastic modeling contract.",
        ),
    }

    parameters = {
        "hepatocyte_radius_um": ParameterProvenance(
            name="hepatocyte_radius_um",
            value=HEPATOCYTE_EQUIVALENT_SPHERE_RADIUS_UM,
            unit="um",
            source_id="segovia_miranda2019_human_liver_3d_morphometry",
            assumption_level="literature_derived",
            confidence=0.85,
            notes="Radius of a volume-equivalent sphere derived from the measured normal-control 3D hepatocyte-volume median; not a claim that the cell is spherical.",
        ),
        "initial_pool_unit": ParameterProvenance(
            name="initial_pool_unit",
            value="relative_pool_0_1",
            unit="dimensionless",
            source_id="project_roadmap_07",
            assumption_level="placeholder",
            confidence=0.25,
            notes="M015 uses normalized pools until quantitative hepatocyte concentrations are curated.",
        ),
    }

    compartments = (
        _compartment("cytosol", "Cytosol", None, 0.52, "Shared soluble phase and metabolic field."),
        _compartment("nucleus", "Nucleus", "cytosol", 0.09, "Genome, transcription, repair decisions."),
        _compartment("rough_er", "Rough ER", "cytosol", 0.08, "ER-bound translation and folding."),
        _compartment("smooth_er", "Smooth ER", "cytosol", 0.07, "Lipid metabolism, Ca storage, CYP detox."),
        _compartment("golgi", "Golgi", "cytosol", 0.03, "Cargo processing, sorting, vesicle dispatch."),
        _compartment("mitochondria_pool", "Mitochondria pool", "cytosol", 0.12, "Distributed mitochondrial population."),
        _compartment("lysosome_pool", "Lysosome/endosome pool", "cytosol", 0.03, "Endocytic and autophagy degradation."),
        _compartment("peroxisome_pool", "Peroxisome pool", "cytosol", 0.02, "Fatty-acid and peroxide handling."),
        _compartment("proteasome_pool", "Proteasome pool", "cytosol", None, "Cytosolic and ERAD degradation capacity."),
        _compartment("cytoskeleton", "Cytoskeleton", "cytosol", None, "Track/motor/polarity scaffold."),
        _compartment("plasma_membrane", "Plasma membrane", None, None, "Selective barrier and receptor/transport surface."),
        _compartment("sinusoidal_face", "Sinusoidal membrane face", "plasma_membrane", None, "Blood-facing uptake/secretion side."),
        _compartment("canalicular_face", "Canalicular membrane face", "plasma_membrane", None, "Bile-facing export side."),
        _compartment("extracellular_sinusoid", "Extracellular sinusoid", None, None, "External nutrient, oxygen, xenobiotic input."),
        _compartment("bile_canaliculus", "Bile canaliculus", None, None, "External bile export sink."),
    )

    pools = (
        _pool("ATP", "ATP", "cytosol", 0.78, "Energy currency available to ATP-costly processes."),
        _pool("ADP", "ADP", "cytosol", 0.18, "Energy charge partner pool."),
        _pool("AMP", "AMP", "cytosol", 0.04, "Low-energy alarm pool."),
        _pool("NADH", "NADH", "cytosol", 0.35, "Redox carrier feeding mitochondrial metabolism."),
        _pool("NAD+", "NAD+", "cytosol", 0.65, "Oxidized redox carrier."),
        _pool("NADPH", "NADPH", "cytosol", 0.72, "Detox and antioxidant reducing power."),
        _pool("GSH", "Reduced glutathione", "cytosol", 0.82, "Antioxidant reserve."),
        _pool("GSSG", "Oxidized glutathione", "cytosol", 0.08, "Oxidative load marker."),
        _pool("glucose", "Glucose", "cytosol", 0.30, "Cytosolic glucose pool."),
        _pool("glycogen", "Glycogen", "cytosol", 0.62, "Hepatocyte carbohydrate storage."),
        _pool("lactate", "Lactate", "cytosol", 0.08, "Gluconeogenesis and redox-linked substrate."),
        _pool("pyruvate", "Pyruvate", "cytosol", 0.14, "Glycolysis/TCA bridge."),
        _pool("fatty_acids", "Fatty acids", "cytosol", 0.28, "Lipid fuel and storage substrate."),
        _pool("acetyl_CoA", "Acetyl-CoA", "mitochondria_pool", 0.20, "TCA and lipid metabolism junction."),
        _pool("amino_acids", "Amino acids", "cytosol", 0.40, "Translation and nitrogen metabolism input."),
        _pool("cytosolic_protein", "Cytosolic protein", "cytosol", 0.35, "Bulk translated cytosolic protein pool."),
        _pool("ammonia", "Ammonia", "cytosol", 0.05, "Urea-cycle detox substrate."),
        _pool("urea", "Urea", "cytosol", 0.08, "Ammonia detox output."),
        _pool("bile_acids", "Intracellular bile acids", "cytosol", 0.14, "Intracellular hepatocyte bile-acid pool; retained legacy id for snapshot compatibility."),
        _pool("canalicular_bile_acids", "Canalicular bile acids", "bile_canaliculus", 0.00, "Mass-conserving destination for BSEP export; zero is an empty model sink at initialization, not a measured concentration."),
        _pool("bilirubin_conjugates", "Intracellular bilirubin conjugates", "cytosol", 0.05, "Intracellular conjugated-bilirubin pool; retained legacy id for snapshot compatibility."),
        _pool("canalicular_bilirubin_conjugates", "Canalicular bilirubin conjugates", "bile_canaliculus", 0.00, "Mass-conserving destination for MRP2 export; zero is an empty model sink at initialization, not a measured concentration."),
        _pool("cholesterol", "Cholesterol", "smooth_er", 0.22, "Bile/lipid metabolism pool."),
        _pool("lipids", "Lipids", "smooth_er", 0.28, "Membrane and secretion lipid pool."),
        _pool("xenobiotic", "Xenobiotic", "smooth_er", 0.04, "Detox load."),
        _pool("detoxified_xenobiotic", "Detoxified xenobiotic", "cytosol", 0.00, "Export-ready detox product."),
        _pool("ROS", "Reactive oxygen species", "cytosol", 0.02, "Oxidative stress pool."),
        _pool("Ca2+", "Calcium", "cytosol", 0.10, "Cytosolic calcium signal pool."),
        _pool("K+", "Potassium", "cytosol", 0.90, "Dominant intracellular cation (~140 mM); sets resting potential."),
        _pool("Na+", "Sodium", "cytosol", 0.10, "Low inside (~12 mM); its gradient powers secondary transport."),
        _pool("Cl-", "Chloride", "cytosol", 0.20, "Intracellular chloride (~10-40 mM)."),
        _pool("Mg2+", "Magnesium", "cytosol", 0.50, "Free Mg2+ (~0.5 mM); cofactor for ATP-dependent enzymes."),
        _pool("GTP", "GTP", "cytosol", 0.40, "Guanine nucleotide pool for GTPases and biosynthesis."),
        _pool("NADP+", "NADP+", "cytosol", 0.10, "Oxidised NADP pool; kept small so NADPH/NADP+ stays high."),
        _pool("oxygen", "Oxygen", "cytosol", 0.70, "Cytosolic oxygen availability for mitochondrial and peroxisomal oxidation."),
        _pool("mRNA", "mRNA", "cytosol", 0.10, "Exported transcript pool."),
        _pool("secretory_protein_cargo", "Secretory protein cargo", "rough_er", 0.08, "ER-bound nascent protein cargo."),
        _pool("folded_cargo", "Folded secretory cargo", "rough_er", 0.02, "ER quality-control-passed cargo ready for Golgi processing."),
        _pool("misfolded_protein", "Misfolded protein", "rough_er", 0.03, "Protein quality-control burden."),
        _pool("ubiquitinated_cargo", "Ubiquitinated cargo", "proteasome_pool", 0.02, "ERAD/proteasome-bound degradation substrate."),
        _pool("albumin", "Albumin", "golgi", 0.18, "Hepatocyte secretory cargo."),
        _pool("membrane_cargo", "Membrane cargo", "golgi", 0.04, "Golgi-sorted membrane protein/lipid cargo."),
        _pool("lysosome_enzyme_cargo", "Lysosome enzyme cargo", "golgi", 0.03, "Golgi-sorted lysosomal enzyme cargo."),
        _pool("canalicular_cargo", "Canalicular cargo", "golgi", 0.03, "Golgi-sorted canalicular membrane/bile export cargo."),
        _pool("endocytosed_cargo", "Endocytosed cargo", "lysosome_pool", 0.02, "Plasma-membrane/endosome cargo awaiting lysosomal processing."),
        _pool("autophagy_cargo", "Autophagy cargo", "lysosome_pool", 0.02, "Damaged protein/organelle material committed to autophagy."),
        _pool("very_long_chain_fatty_acids", "Very-long-chain fatty acids", "peroxisome_pool", 0.10, "Peroxisomal beta-oxidation substrate."),
        _pool("damaged_organelle_mass", "Damaged organelle mass", "cytosol", 0.02, "Autophagy/mitophagy substrate."),
    )

    organelles = (
        _organelle(
            "plasma_membrane",
            "Plasma membrane",
            "plasma_membrane",
            ("python", "brian2", "pysb", "typescript_visual"),
            ("selective_transport", "receptor_signaling", "ion_homeostasis", "endocytosis", "exocytosis", "polarity_boundary"),
            ("extracellular_nutrients", "ATP", "signals"),
            ("imported_substrate", "exported_waste", "signaling_state"),
            ("leak", "transporter_saturation", "wrong_side_localization", "pump_ATP_shortage"),
            ("channel_open_close", "transporter_mislocalization", "membrane_repair_failure"),
            ("cytoskeleton", "rough_er", "golgi", "lysosome_endosome"),
        ),
        _organelle(
            "nucleus",
            "Nucleus",
            "nucleus",
            ("python", "pysb", "sbml"),
            ("genome_state", "transcription", "splicing", "mRNA_export", "DNA_damage_response", "cell_fate_decisions"),
            ("ATP", "signals", "nucleotides"),
            ("mRNA", "repair_state", "apoptosis_senescence_signals"),
            ("DNA_damage", "repair_failure", "transcription_error", "splicing_defect", "nuclear_envelope_stress"),
            ("transcription_burst", "repair_success_failure", "mRNA_export_failure"),
            ("rough_er", "cytosol"),
        ),
        _organelle(
            "ribosome",
            "Ribosomes",
            "cytosol",
            ("python",),
            ("translation", "elongation", "termination", "ribosome_quality_control", "ER_targeting"),
            ("mRNA", "amino_acids", "ATP"),
            ("cytosolic_protein", "secretory_protein_cargo", "translation_stress"),
            ("mistranslation", "ribosome_stall", "amino_acid_shortage", "mRNA_degradation"),
            ("translation_burst", "stall_event", "ER_mistargeting"),
            ("rough_er", "proteasome"),
        ),
        _organelle(
            "rough_er",
            "Rough ER",
            "rough_er",
            ("python", "pysb", "sbml", "brian2"),
            ("protein_folding", "glycosylation_start", "ER_quality_control", "ERAD", "calcium_storage"),
            ("secretory_protein_cargo", "ATP", "Ca2+"),
            ("folded_cargo", "misfolded_protein", "ER_stress_signal"),
            ("misfolding", "ER_retention", "UPR_overload", "calcium_leak", "ERAD_bottleneck"),
            ("folding_success_failure", "UPR_activation", "calcium_release"),
            ("nucleus", "golgi", "mitochondria", "proteasome"),
        ),
        _organelle(
            "smooth_er",
            "Smooth ER",
            "smooth_er",
            ("python", "sbml"),
            ("lipid_synthesis", "CYP_detox", "calcium_storage", "cholesterol_bile_coupling"),
            ("fatty_acids", "xenobiotic", "NADPH", "GSH"),
            ("lipids", "detoxified_xenobiotic", "ROS"),
            ("CYP_ROS_leak", "detox_saturation", "NADPH_shortage", "calcium_leak"),
            ("detox_burst", "ROS_side_effect", "lipid_synthesis_pulse"),
            ("peroxisome", "mitochondria", "golgi"),
        ),
        _organelle(
            "golgi",
            "Golgi apparatus",
            "golgi",
            ("python",),
            ("cargo_modification", "glycosylation_maturation", "sorting", "vesicle_budding", "lysosome_tagging", "polarized_delivery"),
            ("folded_cargo", "ATP", "cytoskeleton_state"),
            ("albumin", "membrane_cargo", "lysosome_enzyme_cargo", "canalicular_cargo"),
            ("glycosylation_error", "misrouting", "vesicle_loss", "stack_fragmentation", "wrong_membrane_face_delivery"),
            ("vesicle_batch_release", "sorting_success_failure", "misroute_event"),
            ("rough_er", "plasma_membrane", "lysosome_endosome", "cytoskeleton"),
        ),
        _organelle(
            "mitochondria",
            "Mitochondria",
            "mitochondria_pool",
            ("python", "sbml"),
            ("TCA", "OXPHOS", "ATP_production", "ROS_balance", "apoptosis_gate", "urea_cycle_entry"),
            ("pyruvate", "fatty_acids", "oxygen", "ADP", "ammonia"),
            ("ATP", "ROS", "urea_cycle_intermediates", "apoptosis_signal"),
            ("membrane_potential_loss", "ATP_collapse", "ROS_leak", "mtDNA_damage", "mitophagy_trigger"),
            ("fission_fusion_abstraction", "mitophagy_commit", "permeability_transition"),
            ("rough_er", "smooth_er", "peroxisome", "cytoskeleton"),
        ),
        _organelle(
            "lysosome_endosome",
            "Lysosome/endosome system",
            "lysosome_pool",
            ("python",),
            ("endocytosed_cargo_degradation", "autophagy_completion", "organelle_turnover", "receptor_recycling", "pathogen_cargo_processing"),
            ("autophagy_cargo", "endocytosed_cargo", "ATP"),
            ("recycled_amino_acids", "recycled_lipids", "degradation_signal"),
            ("pH_loss", "enzyme_deficiency", "overload", "incomplete_degradation", "membrane_permeabilization"),
            ("degradation_success_failure", "autophagy_backlog", "receptor_recycling_failure"),
            ("plasma_membrane", "golgi", "mitochondria", "peroxisome"),
        ),
        _organelle(
            "peroxisome",
            "Peroxisomes",
            "peroxisome_pool",
            ("python", "sbml"),
            ("very_long_chain_fatty_acid_oxidation", "H2O2_catalase_balance", "lipid_metabolism", "ROS_buffering"),
            ("fatty_acids", "ROS"),
            ("shortened_lipids", "detoxified_H2O2"),
            ("catalase_saturation", "H2O2_leak", "fatty_acid_processing_bottleneck", "biogenesis_failure"),
            ("peroxide_detox_failure", "peroxisome_turnover", "lipid_load_spike"),
            ("smooth_er", "mitochondria", "lysosome_endosome"),
        ),
        _organelle(
            "proteasome",
            "Proteasome system",
            "proteasome_pool",
            ("python",),
            ("misfolded_protein_degradation", "ERAD_degradation", "regulatory_protein_turnover"),
            ("misfolded_protein", "ubiquitinated_cargo", "ATP"),
            ("amino_acids", "proteotoxic_stress_reduction"),
            ("saturation", "ATP_shortage", "misfolded_protein_accumulation"),
            ("degradation_success_failure", "capacity_saturation"),
            ("rough_er", "ribosome", "cytosol"),
        ),
        _organelle(
            "cytoskeleton",
            "Cytoskeleton and motor system",
            "cytoskeleton",
            ("python", "rust_or_cpp_optional"),
            ("organelle_positioning", "vesicle_transport", "cell_polarity", "mechanical_integrity"),
            ("ATP", "cargo_packets", "polarity_signals"),
            ("delivered_cargo", "positioned_organelles", "traffic_state"),
            ("motor_stall", "track_disruption", "polarity_loss", "vesicle_congestion"),
            ("motor_stall_event", "track_repair", "cargo_delay"),
            ("golgi", "mitochondria", "rough_er", "plasma_membrane"),
        ),
        _organelle(
            "cytosol_metabolism",
            "Cytosolic metabolism field",
            "cytosol",
            ("python", "sbml"),
            ("glycolysis", "gluconeogenesis_bridge", "pH_buffering", "metabolite_diffusion", "molecular_crowding"),
            ("glucose", "glycogen", "lactate", "ADP"),
            ("pyruvate", "ATP", "pH_state", "local_availability"),
            ("local_ATP_shortage", "pH_shift", "ion_imbalance", "crowding_slowdown"),
            ("diffusion_delay", "glycolytic_flux_noise", "local_depletion"),
            ("mitochondria", "plasma_membrane", "cytoskeleton"),
        ),
    )

    processes = (
        "transcription",
        "splicing",
        "mRNA_export",
        "translation",
        "protein_folding",
        "ERAD",
        "glycosylation",
        "vesicle_trafficking",
        "membrane_transport",
        "glycolysis",
        "glycogen_storage_breakdown",
        "gluconeogenesis",
        "fatty_acid_oxidation",
        "TCA_OXPHOS",
        "urea_cycle",
        "CYP_detox",
        "bile_export",
        "albumin_secretion",
        "autophagy",
        "mitophagy",
        "apoptosis",
        "senescence",
        "calcium_homeostasis",
        "oxidative_stress_response",
    )

    validation_targets = (
        ValidationTarget(
            id="hepatocyte_has_polarity",
            description="Definition includes sinusoidal and canalicular membrane regions.",
            expected="both membrane faces present",
            unit="boolean",
            source_id="project_roadmap_07",
            confidence=0.95,
        ),
        ValidationTarget(
            id="probability_is_state_conditioned",
            description="Every stochastic event must be described as a hazard tied to cell/organelle state.",
            expected="hazard_model=state_conditioned",
            unit="contract",
            source_id="project_roadmap_07",
            confidence=0.9,
        ),
    )

    return CellDefinition(
        id=f"human_hepatocyte_{zone}_v1",
        species="human",
        cell_type="hepatocyte",
        zone=zone,
        geometry=GeometryDefinition(
            radius_um=HEPATOCYTE_EQUIVALENT_SPHERE_RADIUS_UM,
            polarity_axis=HEPATOCYTE_CANONICAL_POLARITY_AXIS,
            membrane_regions={
                "sinusoidal": "blood-facing uptake/secretion face",
                "canalicular": "bile-facing export face",
            },
        ),
        compartments=compartments,
        pools=pools,
        organelles=organelles,
        processes=processes,
        stochastic_policy=StochasticPolicy(
            seed=1357924680,
            event_mode="hybrid_hazard_and_flux",
            packet_mode="flux_now_packet_ready",
            hazard_model="state_conditioned",
            uncertainty_model="assumption_level_per_parameter",
            notes="M015 defines the contract; event kinetics are implemented in later process modules.",
        ),
        validation_targets=validation_targets,
        sources=sources,
        parameters=parameters,
        notes="Mixed-authority hepatocyte definition: structural contracts are source-backed where stated; relative 0-1 pools and organelle cycles are schematic and cannot drive quantitative validation.",
    )


def initial_hepatocyte_state(definition: CellDefinition) -> CellState:
    pools = {
        pool.id: PoolState(
            id=pool.id,
            value=pool.initial_value,
            unit=pool.unit,
            compartment_id=pool.compartment_id,
        )
        for pool in definition.pools
    }

    organelles = {
        organelle.id: OrganelleState(
            id=organelle.id,
            health=1.0,
            activity=0.0,
            age_h=0.0,
            damage=0.0,
            capacity=1.0,
            location_um=_default_location_um(organelle.id),
            risk_per_hour=0.0,
            local_atp=pools["ATP"].value,
            transport_delay_s=0.0,
            active_processes=organelle.functions[:3],
        )
        for organelle in definition.organelles
    }

    stress = {
        "energy": 0.0,
        "oxidative": 0.0,
        "detox": 0.0,
        "cholestatic": 0.0,
        "proteotoxic": 0.0,
        "genotoxic": 0.0,
        "membrane": 0.0,
        "trafficking": 0.0,
        "autophagy": 0.0,
        "ionic": 0.0,
        "senescence": 0.0,
    }

    genome = build_reference_hepatocyte_genome()
    return CellState(
        definition_id=definition.id,
        elapsed_s=0.0,
        status="healthy",
        pools=pools,
        organelles=organelles,
        stress=stress,
        genome=genome,
        gene_expression=build_initial_hepatocyte_expression(genome),
        genomic_architecture=build_genomic_architecture(genome, zonation=definition.zone),
        history=initial_cell_history(),
        cargo_packets=_initial_cargo_packets(),
        events=(
            CellEvent(
                id="m015_initialized",
                t_s=0.0,
                severity="info",
                text="Initialized mixed-authority hepatocyte snapshot; relative pools and organelle cycles are schematic.",
            ),
        ),
    )


def _initial_cargo_packets() -> tuple[CargoPacket, ...]:
    return (
        CargoPacket(
            id="cargo_albumin_001",
            species="albumin",
            origin_compartment="rough_er",
            target_compartment="sinusoidal_face",
            current_location="rough_er",
            route_plan=("rough_er", "er_quality_control", "golgi", "sinusoidal_face"),
            route_index=0,
            quality_score=0.94,
            folding_state="nascent",
            glycosylation_state="early",
            age_s=0.0,
            energy_cost_atp=0.035,
            motor_dependency=True,
            membrane_side_target="sinusoidal",
            state="in_transit",
        ),
        CargoPacket(
            id="cargo_canalicular_transporter_001",
            species="canalicular_bile_transporter",
            origin_compartment="rough_er",
            target_compartment="canalicular_face",
            current_location="rough_er",
            route_plan=("rough_er", "er_quality_control", "golgi", "canalicular_face"),
            route_index=0,
            quality_score=0.90,
            folding_state="nascent",
            glycosylation_state="early",
            age_s=0.0,
            energy_cost_atp=0.045,
            motor_dependency=True,
            membrane_side_target="canalicular",
            state="in_transit",
        ),
        CargoPacket(
            id="cargo_lysosomal_hydrolase_001",
            species="lysosomal_hydrolase",
            origin_compartment="rough_er",
            target_compartment="lysosome_endosome",
            current_location="rough_er",
            route_plan=("rough_er", "er_quality_control", "golgi", "lysosome_endosome"),
            route_index=0,
            quality_score=0.88,
            folding_state="nascent",
            glycosylation_state="mannose_phosphate_candidate",
            age_s=0.0,
            energy_cost_atp=0.040,
            motor_dependency=True,
            membrane_side_target=None,
            state="in_transit",
        ),
        CargoPacket(
            id="cargo_er_misfolded_001",
            species="misfolded_secretory_protein",
            origin_compartment="rough_er",
            target_compartment="proteasome",
            current_location="er_quality_control",
            route_plan=("er_quality_control", "proteasome"),
            route_index=0,
            quality_score=0.24,
            folding_state="misfolded",
            glycosylation_state="failed_qc",
            age_s=20.0,
            energy_cost_atp=0.025,
            motor_dependency=False,
            membrane_side_target=None,
            state="in_transit",
        ),
    )


def _compartment(
    id: str,
    label: str,
    parent_id: str | None,
    volume_fraction: float | None,
    notes: str,
) -> CompartmentDefinition:
    return CompartmentDefinition(
        id=id,
        label=label,
        parent_id=parent_id,
        volume_fraction=volume_fraction,
        notes=notes,
    )


def _pool(
    id: str,
    label: str,
    compartment_id: str,
    initial_value: float,
    notes: str,
) -> PoolDefinition:
    return PoolDefinition(
        id=id,
        label=label,
        compartment_id=compartment_id,
        initial_value=initial_value,
        unit="relative_pool_0_1",
        normal_range=(0.0, 1.0),
        source_id="project_roadmap_07",
        assumption_level="placeholder",
        notes=notes,
    )


def _organelle(
    id: str,
    label: str,
    compartment_id: str,
    model_layers: tuple[str, ...],
    functions: tuple[str, ...],
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    failure_modes: tuple[str, ...],
    stochastic_events: tuple[str, ...],
    contacts: tuple[str, ...],
) -> OrganelleDefinition:
    return OrganelleDefinition(
        id=id,
        label=label,
        compartment_id=compartment_id,
        model_layers=model_layers,
        functions=functions,
        inputs=inputs,
        outputs=outputs,
        failure_modes=failure_modes,
        stochastic_events=stochastic_events,
        contacts=contacts,
        source_ids=("alberts_mbc", "project_roadmap_07"),
    )


def _default_location_um(organelle_id: str) -> tuple[float, float, float]:
    locations = {
        "plasma_membrane": (0.0, 11.5, 0.0),
        "nucleus": (0.0, 0.0, 0.0),
        "ribosome": (-3.5, 1.5, 1.2),
        "rough_er": (-2.2, 0.8, 0.5),
        "smooth_er": (2.5, -1.0, 0.7),
        "golgi": (1.3, 2.3, 0.2),
        "mitochondria": (-4.0, -2.0, 1.1),
        "lysosome_endosome": (3.7, 1.2, -1.4),
        "peroxisome": (-1.5, -3.2, -1.2),
        "proteasome": (0.9, -0.8, 2.4),
        "cytoskeleton": (0.0, 0.0, 0.0),
        "cytosol_metabolism": (0.0, -1.0, 0.0),
    }
    return locations.get(organelle_id, (0.0, 0.0, 0.0))
