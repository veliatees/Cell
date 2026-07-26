# Milestone 118 - PHH receptor/signaling trajectory intake v1

## Problem

The communication atlas identifies eight plausible hepatocyte communication
pathways, but pathway identity does not provide receptor density, occupancy,
binding kinetics, trafficking, delay, or response magnitude.

## Implemented

`phh_receptor_signaling_trajectory_contract.v1.json` defines a strict
48-column, donor-resolved delivery format for eight evidence stages across all
eight pathways:

1. ligand or contact-partner exposure;
2. receptor/channel surface density;
3. active fraction or occupancy;
4. association and dissociation;
5. internalization, recycling, or gate turnover;
6. proximal signal;
7. downstream functional response;
8. independent held-out validation.

The loader enforces exact pathway IDs, raw source units, measured area
denominators, soluble 3D versus contact 2D geometry, strictly ordered dynamic
series, one matched healthy-PHH calibration donor, donor/study split isolation,
manual primary-source review, and a checksum-frozen held-out artifact.

## Authority Boundary

A structurally complete delivery still cannot:

- convert units automatically;
- fit kinetics automatically;
- activate a receptor;
- execute a signal;
- alter cell state.

Those actions require manual cross-stage adjudication and promotion of an
immutable, independently validated model artifact. The current delivery count
and runtime authority are both zero.
