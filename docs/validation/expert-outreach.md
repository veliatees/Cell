# External Reviewer Outreach

This file identifies review routes, not project endorsers. Contacting a person or
community does not imply that they reviewed, approved, or validated Cell Engine.

## First Review Targets

### Primary-human-hepatocyte biology

- **Volker Lauschke / Lauschke Lab, Karolinska Institutet**
  - Fit: primary human hepatocyte 3D systems, donor variation, drug metabolism,
    metabolic disease, and the Kemas glucose-assay evidence already used by the project.
  - Requested claim IDs: `cell_identity_scale_and_zonation`,
    `glucose_measurement_and_model_bridge`,
    `protein_abundance_localization_and_transport`, and
    `compartmental_energy_and_redox_topology`.
  - Official profile: <https://ki.se/en/people/volker-lauschke>
  - Lab: <https://ki.se/en/research/research-areas-centres-and-networks/research-groups/personalized-medicine-and-drug-development-lauschke-lab>

### Computational liver modeling

- **Matthias Koenig / Systems Medicine of the Liver, Humboldt-Universitaet zu Berlin**
  - Fit: kinetic liver metabolism, PBPK/PD, digital twins, multiscale modeling,
    and authorship of the Koenig 2012 glucose model audited by Cell Engine.
  - Requested claim IDs: `nutritional_endocrine_and_zonation_context`,
    `glucose_measurement_and_model_bridge`,
    `compartmental_energy_and_redox_topology`, and
    `whole_cell_predictive_hepatocyte`.
  - Official profile: <https://fis.hu-berlin.de/converis/portal/detail/Person/400248407?lang=en_GB>

### Membrane and cell-surface biophysics

- **Patricia Bassereau / Membranes and Cellular Functions, Institut Curie**
  - Fit: quantitative membrane mechanics, curvature, tension, membrane-protein
    organization, endo/exocytosis and adhesion.
  - Requested claim IDs: `membrane_and_contact_geometry` and
    `communication_and_receptor_chain` only. This is not a request to validate
    hepatocyte metabolism.
  - Official profile: <https://curie.fr/personne/patricia-bassereau>
  - Team: <https://curie.fr/equipe/bassereau>

- **Alba Diz-Munoz / Mechanobiology at the Cell Surface, EMBL**
  - Fit: plasma-membrane/cortex coupling, cell-surface mechanics and force
    transduction across molecular and cellular scales.
  - Requested claim IDs: `membrane_and_contact_geometry` and
    `communication_and_receptor_chain` only.
  - Official group page: <https://www.embl.org/groups/diz-munoz/>

## Network Routes

- **Human Cell Atlas Liver Biological Network**
  - Use for spatial, structural, genomic and cell-atlas review routes.
  - Public network contact: `liver@humancellatlas.org`
  - <https://www.humancellatlas.org/biological-networks/liver-biological-network/>

- **EASL Basic Science Task Force**
  - Use to identify an independent hepatologist, liver pathologist or basic
    liver scientist for disease-scope and clinical-overinterpretation review.
  - <https://easl.eu/easl/leadership-and-governance/basic-science-task-force/>

- **BioModels curation**
  - Use after a preprint or manuscript exists for model-format, annotation and
    reproducibility curation. BioModels curation does not certify hepatocyte biology.
  - <https://www.ebi.ac.uk/biomodels/model/submission-guidelines-and-agreement>

## Package To Send

Send one frozen archive or permanent commit link containing:

1. `docs/validation/external-review-dossier.md`
2. `data/validation/external_validation_program.v1.json`
3. `public/engine-snapshot.json`
4. `docs/sources.md`
5. The exact command used to regenerate snapshots, tests and figures
6. A short screen recording showing the research-preview interface
7. Only the claim IDs assigned to that reviewer

Do not ask one reviewer to approve the complete project. Ask them to falsify a
small set of explicit claims within their expertise.

## Email: PHH Biology Review

**Subject:** Scoped external review request: source-traceable human hepatocyte simulation

Dear Professor [Name],

I am developing Cell Engine, open research software that represents a single
human hepatocyte using source-traceable anatomical, metabolic and assay-specific
evidence. The current release is explicitly a research preview; it does not claim
to be a predictive digital twin or assign a biological-accuracy percentage.

Your work is directly relevant to the PHH evidence used in the project. I would
be grateful for a scoped review of the following claims: [CLAIM IDS]. The review
packet lists the exact source transfers, missing measurements, prohibited uses,
and questions that could falsify each claim.

Would you or a member of your group be available for a short review, or advise
whether a formal consultancy or research collaboration would be more appropriate?
Negative findings and rejected assumptions will be recorded in the repository.

Repository: <https://github.com/veliatees/Cell>

Thank you for considering it,

Veli Ates

## Email: Computational Model Review

**Subject:** Review request: liver-model equations, scale bridges and validation gates

Dear Dr. [Name],

I am developing Cell Engine, a source-audited single-hepatocyte research
simulation. The project includes an explicit audit of published liver models,
including equation, compartment, unit, biological-context and held-out-validation
gates. No published kinetic parameter enters the active quantitative model unless
all gates pass.

I am seeking a scoped external review of [CLAIM IDS], especially the separation
of organ-scale observations from per-cell quantities, the glucose measurement
operator, compartmental energy/redox topology, and the current reasons predictive
execution remains blocked.

The packet contains machine-readable contexts of use, source manifests,
falsification questions and reproducible commands. Would you be available to
review this scope, or suggest a suitable member of your group?

Repository: <https://github.com/veliatees/Cell>

Kind regards,

Veli Ates

## Email: Membrane Biophysics Review

**Subject:** Scoped review request: membrane/contact mechanics in a hepatocyte simulation

Dear Dr. [Name],

I am developing a single-hepatocyte research simulation with an explicit
membrane and contact-geometry engine. It currently implements a closed surface,
contact-patch detection, membrane-domain ambiguity and volume-preserving
kinematic deformation. Healthy-PHH tension, cortex coupling, bending modulus,
viscosity, adhesion force and mechanotransduction remain unparameterized.

I am asking for a narrow review of two claims only:
`membrane_and_contact_geometry` and `communication_and_receptor_chain`. In
particular, I would value criticism of how the model separates bending/reservoir
shape change from direct area stretch, and which measurements would be required
before mechanical or biochemical coupling could be activated.

This request is not for endorsement of the hepatocyte metabolism model. The
review packet records limitations and negative findings explicitly.

Repository: <https://github.com/veliatees/Cell>

Kind regards,

Veli Ates
