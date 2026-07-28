# Milestone 105 - Automated browser render integrity v1

## Scope

This milestone closes the narrow engineering question: can the primary
hepatocyte view repeatedly render a populated, moving canvas without layout or
runtime failures on representative desktop and mobile viewports?

## Implemented

- Playwright starts an isolated Vite server and runs Chromium at `1280x720` and
  `390x844`.
- Each viewport checks canvas visibility and stable dimensions.
- PNG diagnostics measure luminance mean/variance, non-dark pixels, chromatic
  pixels and quantized color diversity.
- Two frames separated by 650 ms must differ enough to prove motion without
  allowing a full-frame random flicker.
- DOM checks reject horizontal overflow, unintended desktop vertical overflow,
  clipped controls and canvas escape from its viewport.
- Console errors and uncaught page errors fail the suite.

## Claim boundary

The thresholds are renderer-integrity tests, not biological measurements or
visual-anatomy accuracy scores. Exact pixel equality is deliberately not claimed
across GPU drivers. A future approved design-baseline system remains a separate
possible scope.

## Run

```bash
npm run test:visual
```
