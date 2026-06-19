# Milestone 028 - Visual time-scale disclosure

Status: implemented

M028 makes the browser cell scene explicit about time. The visualization is not
a real-time microscope movie. It is an accelerated, normalized view of the cell
engine and visual model.

## What Was Added

- The organelle scene now advances with a frame-rate independent visual clock.
- The UI shows a time-scale note in the hepatocyte activity panel.
- The note distinguishes:
  - accelerated TypeScript visual clock;
  - static Python engine snapshot time;
  - normalized pool/flux values.

## Current Visual Clock

The TypeScript visual cell advances at approximately:

```text
5 simulated cell seconds / 1 real browser second
```

The default Python snapshot is a separate engine state exported at:

```text
t = 1200 simulated seconds
```

## Biological Reality

Real cells do not run on one clock:

- molecular diffusion and ion-channel events can be microseconds to
  milliseconds;
- enzyme turnovers and local binding can be milliseconds to seconds;
- vesicle transport is commonly seconds to minutes;
- transcription, folding, secretion and autophagy are often minutes-scale;
- organelle turnover and cell fate decisions are hours to days.

The current scene compresses those scales so humans can inspect the system. It
should not be interpreted as "everything in the cell happens that fast."

## Boundaries

- The UI note is a disclosure, not a calibrated kinetic model.
- Python and TypeScript clocks are still bridged by snapshots, not live
  streaming.
- M029 will address the next visual realism issue: generated products should not
  always follow the same fixed visible path.

## Verification

```bash
npm test -- --maxWorkers=1
npm run build
python -m unittest discover -s engine/tests -t engine
```
