# Milestone 164 - Organelle instance evidence firewall v1

## Problem

The per-instance organelle layer had begun to assign synthetic vitality, age,
recovery, stress-sensitivity and clearance values. The browser then used a
second set of synthetic constants to change motion, size, opacity and colour.
Those values were labelled schematic, but they still altered the simulated
cell and therefore violated the project's no-invented-parameters rule.

The size coupling also created three different bodies for one organelle:

- a vitality-scaled rendered mesh;
- a static membrane-contact sphere;
- a static sphere or capsule in the cytosol obstacle field.

## Evidence audit

Primary studies support the biological existence of within-cell organelle
heterogeneity and selective quality control. They do not provide a matched,
longitudinal healthy-adult primary-human-hepatocyte data set from which the
removed numerical laws can be identified.

- Collins et al. imaged mitochondrial functional heterogeneity in primary rat
  hepatocytes. This supports heterogeneity, not healthy-human vitality values or
  turnover kinetics: <https://pmc.ncbi.nlm.nih.gov/articles/PMC125942/>.
- McWilliams et al. used the mito-QC reporter in mice to resolve mitophagy and
  mitochondrial architecture in vivo. It does not provide a PHH per-organelle
  clearance threshold: <https://pubmed.ncbi.nlm.nih.gov/27458135/>.
- Dutta et al. studied stress-responsive pexophagy in catalase-knockout mouse
  liver during prolonged fasting. It is not a healthy-human baseline:
  <https://pubmed.ncbi.nlm.nih.gov/33496364/>.

Cross-species and perturbation studies may establish pathway existence. They
cannot silently authorize healthy-PHH numerical parameters.

## Implemented contract

`organelle_instance_vitality_v2` retains 1,901 stable discrete-body identities
from the authoritative placement contract. Every unmeasured quantitative field
is now `null`:

- vitality and health;
- organelle age and turnover time;
- recovery time constant and stress sensitivity;
- clearance threshold and size-response law.

The field reports zero quantitative model parameters and zero quantified
instances. Reaction, transport and geometry authority are all disabled. The
browser fails closed if a future snapshot attempts to enable either quantitative
runtime or geometry coupling before a calibrated implementation exists.

## Geometry correction

The renderer no longer changes an organelle's scale from an unsupported vitality
state. Rendered scale, cytosol obstacle scale and conservative membrane-contact
radius now derive from the same placement geometry. Capsules retain their
analytic cytosol shape; the membrane kernel uses the corresponding conservative
bounding radius.

Aggregate organelle-type activity may still modulate a shared display material.
Stable per-instance colour variation remains an optical readability aid. Neither
is presented as a measurement of an individual organelle's vitality or age.

## Activation requirements

Quantitative per-organelle dynamics must remain disabled until a delivery has:

1. adult primary human hepatocytes with donor and culture context;
2. longitudinal single-organelle identities and calibrated raw image artifacts;
3. simultaneous position, geometry and a reporter with a defined measurement
   operator;
4. perturbation, recovery and clearance trajectories at reported timestamps;
5. units, uncertainty, censoring, segmentation and tracking methods;
6. a fitted law separated from donor- or study-disjoint held-out validation.

Until then, identity is represented and numerical biology remains explicitly
unknown.
