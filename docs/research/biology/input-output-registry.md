# Input / Output Registry

This file is the starting table for anything that enters, leaves, modifies, or
is produced by a cell. Each row should eventually point to source-backed values,
transport mechanisms, equations, and implementation state variables.

## Registry Fields

- entity
- category
- direction
- route
- source compartment
- target compartment
- energy coupling
- primary equations or rules
- visual representation
- hidden state
- sources
- confidence

## Starting Entries

| Entity | Category | Direction | Route | Notes |
| --- | --- | --- | --- | --- |
| O2 | gas/metabolite | input | diffusion | Used by mitochondria for oxidative metabolism. |
| CO2 | gas/metabolite | output | diffusion | Produced by metabolism. |
| H2O | solvent | input/output | osmosis, channels, diffusion | Drives volume and osmotic balance. |
| Na+ | ion | input/output | channels, pumps, cotransporters | Major extracellular cation; gradient couples transport. |
| K+ | ion | input/output | channels, pumps | Major intracellular cation; important for membrane potential. |
| Ca2+ | ion/signal | input/output/storage | channels, pumps, organelle stores | Low cytosolic concentration makes it a strong signal. |
| Cl- | ion | input/output | channels, transporters | Important for charge and fluid movement. |
| H+ | ion/pH | input/output | pumps, buffers, metabolism | Determines pH and affects protein behavior. |
| HCO3- | ion/buffer | input/output | transporters | Important buffer and epithelial secretion/absorption species. |
| glucose | nutrient | input | transporters | Carbon and energy source. |
| amino acids | nutrient/building blocks | input/output | transporters | Protein synthesis and metabolism. |
| fatty acids | nutrient/building blocks | input/output | transporters, diffusion-like handling | Membrane and energy metabolism. |
| ATP | energy currency | internal output/input | metabolism, reactions | Couples chemical energy to work. |
| ADP/AMP | energy state | internal output/input | metabolism | Tracks energy use and stress. |
| lactate | metabolite | output/input | transporters | Depends on glycolytic state and tissue context. |
| proteins | macromolecules | output/internal | secretion, trafficking | Secreted, membrane, cytosolic, and organelle proteins. |
| cytokines/growth factors | signals | input/output | receptors, secretion | Context-specific epithelial communication. |
| mechanical force | physical | input/output | junctions, cytoskeleton, ECM | Affects shape, signaling, and tissue integrity. |
| heat | energy | output | physical dissipation | Comes from non-perfect energy conversion. |

## Transport Mechanism Types

- simple diffusion
- facilitated diffusion
- primary active transport
- secondary active transport
- channels
- pumps
- symporters/antiporters
- vesicular transport
- endocytosis
- exocytosis
- paracellular transport

## Modeling Notes

The registry should become machine-readable later, likely as JSON or YAML
generated from source-backed Markdown. For now Markdown keeps it easy to discuss
and revise.

Each entry should eventually include:

- concentration ranges
- compartment location
- transporter names
- rate equations
- source citations
- visualization behavior
- simulation cost
- confidence level

## Sources

- NCBI transport of small molecules: https://www.ncbi.nlm.nih.gov/books/NBK9847/
- NCBI active transport overview: https://www.ncbi.nlm.nih.gov/books/NBK547718/
- Cell Biology by the Numbers: https://book.bionumbers.org/
