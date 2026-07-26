# Milestone 136: Seven-donor PHH proteome-to-GPR core evidence v1

## Purpose

Use measured primary-human-hepatocyte total proteomes to create a conservative
Boolean Human-GEM reaction-support core without inventing an abundance cutoff.

## Sources And Cohort

The input is the curated official supplement to Wisniewski et al.:

- primary paper: <https://doi.org/10.1016/j.jprot.2016.01.016>;
- seven primary hepatocyte donors, A-G;
- cells isolated from histologically normal areas of surgical liver
  resections;
- the cohort is explicitly not a healthy-volunteer cohort;
- source values are proteomic-ruler copies per nucleus, not active copies per
  cell.

The supplementary workbook identities, sizes and SHA-256 checksums are already
frozen in the PHH proteome atlas.

## Conservative Mapping

- Only protein groups with exactly one source gene symbol are eligible.
- A donor supports a group only when source `copies_per_nucleus` is non-null.
- Gene symbols must match an FBC label exactly and case-sensitively.
- No synonym expansion, imputation or abundance threshold is used.
- Quantitative values from distinct MaxQuant groups are never summed.
- Each donor's complete Boolean GPR is evaluated independently.

The independent donor evaluation matters for `or` rules: different donors can
support the same reaction through different exact isoenzymes.

## Pinned Result

- quantified source groups: `8,689`;
- eligible single-gene groups: `8,110`;
- excluded groups: `579` (`241` multi-gene, `338` without a source symbol);
- exact model gene products detected per donor: `1,364-1,615`;
- GPR-supported reactions per donor: `5,373-5,879`;
- reactions supported in every donor: `5,082`;
- reactions supported by one identical all-donor gene intersection: `5,064`;
- donor-specific isoenzyme difference: `18`;
- all-donor reactions blocked by generic FASTCC: `527`;
- flux-consistent Boolean core candidate: `4,555`.

## Scientific Boundary

Total-protein detection is not enzyme activity, membrane localization, complex
assembly, catalytic capacity or flux. The result is a reaction-support
candidate, not an accepted healthy-PHH context model.
