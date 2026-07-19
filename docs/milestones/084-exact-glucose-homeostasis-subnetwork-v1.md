# Milestone 084: Exact Glucose Homeostasis Subnetwork v1

## Outcome

The project now has a source-exact, non-executable structural contract for the
published human hepatic glucose model. The contract reads the official PLOS
SBML supplement directly and checksum-locks its:

- 52 species;
- five source compartments;
- 36 reaction equations; and
- zero kinetic laws.

This is intentionally not a numerical model. The source supports reaction
topology and stoichiometry, but it does not authorize an active healthy-PHH
single-cell rate law.

## Canonical pools

The contract introduces canonical identities for extracellular glucose,
cytosolic glucose, glucose-6-phosphate, glycogen glucosyl residues, lactate,
pyruvate, ATP and NADH. Cytosolic and mitochondrial pools remain distinct.

The older exploratory runtime is not silently rewritten. It is automatically
blocked from promotion because it currently contains:

1. separate `glucose` and `glucose_cyto` pools for one physical cytosolic pool;
2. two non-equivalent glucose-export reactions;
3. a lumped lower-gluconeogenesis callable; and
4. one numerical volume for cytosolic and mitochondrial chemistry.

## Scientific boundary

No parameter was added or activated. Structural source authority is separate
from numerical authority. Runtime replacement requires exact equations,
per-cell units, a matched healthy-PHH context and independent validation for
every active reaction.

## Verification

- SBML species metadata preserves amount versus concentration semantics.
- Source checksum, inventory counts and reaction uniqueness are tested.
- All four runtime structural conflicts are regression tested.
- Snapshot summary reports zero executable reactions and zero activated
  parameters.
