# Milestone 165 - p53 and population authority firewall v1

## Problem

Two recent modules crossed the project's evidence boundary:

- a reduced p53/MDM2 oscillator used 34 project-tuned or schematic constants but
  described the result as grounded;
- a cell-population demonstration embedded project-selected stress, repair,
  noise, carrying-capacity and fate thresholds, then exported a canonical
  `transformation_emerged` claim.

The qualitative mechanisms are biologically plausible. That does not make the
numbers primary-human-hepatocyte parameters or the resulting trajectories PHH
predictions.

## Evidence audit

Lahav et al., Geva-Zatorsky et al., Batchelor et al., Purvis et al. and Ciliberto
et al. support p53/MDM2 pulse structure, feedback mechanisms and
dynamics-dependent fate in studied mammalian systems. The key pulse studies are
cross-context cell-line evidence, including MCF7 breast-cancer cells. Their
approximately 5.5 h period cannot be relabelled as a healthy-PHH measurement.

Heldring et al. (2022) is the closest directly relevant PHH study identified:

- 54 cryopreserved PHH donors entered the experiment;
- four non-confluent donors were excluded, leaving 50;
- TempO-Seq transcripts were measured after cisplatin at 8 h and 24 h;
- time-resolved p53, MDM2, p21 and BTG2 protein measurements came from HepG2
  reporters, not PHHs;
- the HepG2-derived model did not reproduce the negative PHH TP53-MDM2
  relationship, exposing a stated translation knowledge gap.

The article and its code/data release are pinned in
`data/published_models/heldring2022_p53_phh_translation.v1.json`. The Zenodo
v1.1 archive identity is recorded as 17,340,023 bytes with MD5
`10be64daac7e3e3a59b0d4184b31a2f0`; the archive is not vendored or automatically
executed.

Human liver studies confirm that clonal expansion is real and spatially
structured. A direct PHH transformation study used defined combinations of
oncogenic factors in an in-vivo host context. These sources do not authorize a
p53-null-only transformation law or a dimensionless stress threshold.

## Implemented boundary

`p53_dynamics_authority_v2` now:

- requires an explicit `software_fixture` or `exploratory_candidate` purpose to
  execute the reduced ODE;
- rejects quantitative validation, prediction and authoritative state coupling;
- labels every candidate output and its parameter authority;
- publishes zero simulated scenarios and zero healthy-PHH kinetic parameters;
- records the 50-donor, two-timepoint PHH transcript evidence separately from
  time-resolved protein evidence, whose count remains zero.

`cell_population_authority_v2` now:

- contains no bundled numerical parameter set;
- requires every candidate parameter and execution purpose from the caller;
- publishes no canonical scenario and no transformation result;
- calls majority status only a candidate bookkeeping readout;
- blocks scientific execution until matched lineage, spatial niche, fate and
  independent validation data exist.

The TypeScript snapshot contract and the completion matrix enforce the same
boundary. The matrix now tracks PHH p53 dynamics and PHH clonal dynamics as two
separate `blocked_missing_evidence` capabilities. This is not a loss of software
functionality; it is removal of unsupported biological authority.

## Activation requirements

The p53 module needs time-resolved PHH p53, phosphorylated-p53 and MDM2 protein
trajectories under a defined damage protocol, matched repair and fate outcomes,
measurement uncertainty, donor-conditioned calibration and donor-disjoint
held-out validation.

The population module additionally needs clone-resolved genotype and ploidy,
injury and zonation context, proliferation/arrest/senescence/death/clearance
trajectories, spatial neighbour geometry, measurement operators and independent
review. Until those records pass intake, neither module can alter the
authoritative hepatocyte state.

## Sources

1. Lahav et al. (2004), <https://doi.org/10.1038/ng1293>
2. Geva-Zatorsky et al. (2006), <https://doi.org/10.1038/msb4100068>
3. Batchelor et al. (2008), <https://doi.org/10.1016/j.molcel.2008.03.016>
4. Purvis et al. (2012), <https://doi.org/10.1126/science.1218351>
5. Ciliberto et al. (2005), <https://doi.org/10.4161/cc.4.3.1548>
6. Heldring et al. (2022), <https://doi.org/10.1371/journal.pcbi.1010264>
7. Heldring code/data v1.1, <https://doi.org/10.5281/zenodo.6458438>
8. Brunner et al. (2019), <https://doi.org/10.1038/s41586-019-1670-9>
9. Braun et al. (2023), <https://pubmed.ncbi.nlm.nih.gov/37088309/>
10. Jiang et al. (2022), <https://doi.org/10.15252/embr.202154275>
