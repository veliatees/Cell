# Milestone 085: Glucose Open System and Exact Assay v1

## Outcome

The engine now represents two non-interchangeable glucose environments:

1. a healthy-adult human liver blood-boundary reference; and
2. the finite-batch Kemas primary-human-hepatocyte 3D-spheroid assay.

The liver reference retains the sourced postabsorptive glucose interval and
whole-liver transit observation. It does not infer one-sinusoid volume, flow
geometry or hepatocyte GLUT2 exchange.

The PHH assay retains its exact four exposure bundles and 0, 6, 24 and 72 hour
time points. It is explicitly not represented as a sinusoid or a concentration
clamp.

## Missing values preserved

The primary PHH source does not report the challenge-medium initial volume,
remaining-volume schedule, volumetric factor or viable-cell count at every
window. All four remain null. High-insulin conditions also retain unmeasured
glucagon rather than assuming zero.

## Model-output bridge

A model may submit exactly 12 non-overlapping signed window fluxes in
`fmol/cell/h`, with matching species, cell format, exposure matrix, denominator,
protocol version and artifact SHA-256. The bridge integrates those rates into
16 cumulative points and passes them through the existing exact PHH measurement
operator, which derives all 16 reported assay windows.

Negative rates are preserved as net glucose production. Overlap rows, missing
windows, non-finite values and unprovenanced artifacts are rejected.

## Scientific boundary

This milestone adds no transport law and no biological rate. It enables an
honest same-format comparison when a qualified model produces output; it does
not make the current model predictive or permit automatic cell-state coupling.
