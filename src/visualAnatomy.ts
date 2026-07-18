export type VisualAnatomyDomain = "apical" | "basolateral" | "lateral";
export type VisualAnatomyLod = "overview" | "cellular" | "ultrastructure";

export type VisualAnatomyRequirement = {
  id: string;
  label: string;
  weight: number;
  completion: number;
  evidenceScope: "human" | "mammalian_topology" | "renderer_contract";
};

export const VISUAL_ANATOMY_SOURCES = {
  humanLiverCellularArchitecture: {
    id: "fabyan2026_human_liver_3d",
    url: "https://doi.org/10.1126/sciadv.adz2299",
    supports: ["human 3D liver cellular architecture", "tissue-scale spatial context; not single-cell mechanics"]
  },
  humanHepatocyte3dMorphometry: {
    id: "segovia_miranda2019_human_liver_3d_morphometry",
    url: "https://doi.org/10.1038/s41591-019-0660-7",
    supports: ["normal-control human 3D hepatocyte aggregate volume", "normal-control aggregate lipid-droplet volume fraction"]
  },
  humanSinusoidUltrastructure: {
    id: "wisse2010_human_liver_em",
    url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC2887580/",
    supports: ["human LSEC fenestra mean diameter", "Space of Disse", "sinusoidal hepatocyte microvilli"]
  },
  hepaticErTopology: {
    id: "jiang2021_hepatic_er_3d",
    url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC8648385/",
    supports: ["contiguous hepatic ER network", "ER-organelle contacts"]
  },
  hepaticArchitecture: {
    id: "parlakgul2022_liver_fibsem",
    url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC9014868/",
    supports: ["3D hepatocyte organelle architecture", "ER and mitochondria spatial organization"]
  },
  bileCanaliculusMicroarchitecture: {
    id: "meyer2017_bile_canaliculus_3d_em",
    url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC8063490/",
    supports: ["convoluted canalicular lumen", "dense canalicular microvilli"]
  },
  canalicularActomyosin: {
    id: "belicova2023_apical_bulkheads",
    url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC9930133/",
    supports: ["canalicular F-actin cortex", "tight-junction boundary", "contractile apical structures"]
  },
  hepatocytePolarityFormation: {
    id: "wang2014_hepatocyte_polarization",
    url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC4038943/",
    supports: ["apical lumen landmark", "microtubule and exocyst organization near canalicular membrane"]
  },
  humanIntermediateFilaments: {
    id: "ishii1985_human_hepatocyte_intermediate_filaments",
    url: "https://pubmed.ncbi.nlm.nih.gov/3914103/",
    supports: ["human hepatocyte intermediate-filament meshwork", "junctional, pericanalicular and nuclear attachment topology"]
  },
  humanCanalicularActin: {
    id: "bachour_el_azzi2015_human_hepatocyte_canalicular_actin",
    url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC4833040/",
    supports: ["primary human hepatocyte canalicular F-actin", "polarized canalicular transporter localization"]
  },
  primaryHepatocyteGolgiPolarity: {
    id: "porcine_primary_hepatocyte_ultrastructure_2020",
    url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC7259665/",
    supports: ["Golgi stacks near canalicular domain", "canalicular microvilli in primary hepatocytes"]
  }
} as const;

// Mean diameter reported from tangentially sectioned human liver sinusoidal
// endothelium. This is the only numeric ultrastructural dimension transferred
// into the renderer by this visual-anatomy contract.
export const HUMAN_LSEC_FENESTRA_MEAN_DIAMETER_NM = 105;
export const ISOLATED_PHH_MEDIAN_DIAMETER_UM = 18.4;
export const HISTORICAL_IN_SITU_PHH_MEAN_VOLUME_UM3 = 2850;
// Aggregate normal-control 3D median and MAD from Segovia-Miranda et al.
// Supplementary Table 3, Figure 3c. The equivalent diameter is derived.
export const HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3 = 5657.07116;
export const HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3 = 744.875484;
export const HEPATOCYTE_REFERENCE_EQUIVALENT_DIAMETER_UM = 22.107060841416555;
// Figure 3i normal-control median. This constrains aggregate display volume,
// not droplet count, size distribution or a nutrition-dependent response law.
export const HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION = 0.00507807;
export const HEPATOCYTE_CANONICAL_POLARITY_AXIS = [1, 0, 0] as const;
export const HEPATOCYTE_RENDER_RADIUS_WORLD = 14;
export const HEPATOCYTE_RENDER_UM_PER_WORLD_UNIT =
  (HEPATOCYTE_REFERENCE_EQUIVALENT_DIAMETER_UM / 2) / HEPATOCYTE_RENDER_RADIUS_WORLD;

// This is a project-defined coverage rubric, not a percentage of hepatocyte
// biology and not a validation score. Completion can only describe whether a
// named visual layer is represented with the evidence boundary shown here.
export const VISUAL_ANATOMY_REQUIREMENTS: readonly VisualAnatomyRequirement[] = [
  { id: "cell-boundary", label: "Cell form and deformable boundary", weight: 8, completion: 0.9, evidenceScope: "renderer_contract" },
  { id: "membrane-polarity", label: "Apical, lateral and basolateral membrane domains", weight: 12, completion: 1, evidenceScope: "mammalian_topology" },
  { id: "canalicular-interface", label: "Canalicular lumen, microvilli, junctions and actin", weight: 12, completion: 1, evidenceScope: "mammalian_topology" },
  { id: "sinusoidal-interface", label: "LSEC, fenestrae, Disse space and microvilli", weight: 12, completion: 1, evidenceScope: "human" },
  { id: "nuclear-system", label: "Nucleus, envelope, pores and chromatin", weight: 7, completion: 1, evidenceScope: "mammalian_topology" },
  { id: "endomembrane-system", label: "Continuous rough/smooth ER and polarized Golgi", weight: 12, completion: 1, evidenceScope: "mammalian_topology" },
  { id: "metabolic-organelles", label: "Mitochondria, peroxisomes, lysosomes and lipid droplets", weight: 10, completion: 0.8, evidenceScope: "mammalian_topology" },
  { id: "cytoskeleton", label: "Actin cortex, microtubules and intermediate filaments", weight: 10, completion: 1, evidenceScope: "mammalian_topology" },
  { id: "trafficking", label: "Compartment-connected directional traffic", weight: 7, completion: 1, evidenceScope: "renderer_contract" },
  { id: "scale-lod", label: "True-scale disclosure and level of detail", weight: 5, completion: 1, evidenceScope: "renderer_contract" },
  { id: "image-validation", label: "Quantitative registration against reference EM volumes", weight: 5, completion: 0.2, evidenceScope: "renderer_contract" }
] as const;

export function visualAnatomyCoverage(requirements: readonly VisualAnatomyRequirement[] = VISUAL_ANATOMY_REQUIREMENTS): number {
  const total = requirements.reduce((sum, requirement) => sum + requirement.weight, 0);
  if (total <= 0) return 0;
  const completed = requirements.reduce(
    (sum, requirement) => sum + requirement.weight * Math.min(1, Math.max(0, requirement.completion)),
    0
  );
  return (completed / total) * 100;
}

export function normalizeDisplaySphereScalesToVolumeFraction(
  rawScales: readonly number[],
  baseRadius: number,
  cellEquivalentRadius: number,
  targetFraction: number
): number[] {
  if (
    rawScales.length === 0 ||
    !rawScales.every((value) => Number.isFinite(value) && value > 0) ||
    !Number.isFinite(baseRadius) || baseRadius <= 0 ||
    !Number.isFinite(cellEquivalentRadius) || cellEquivalentRadius <= 0 ||
    !Number.isFinite(targetFraction) || targetFraction <= 0 || targetFraction >= 1
  ) throw new Error("Display-volume normalization requires positive finite geometry.");
  const rawRadiusCubeSum = rawScales.reduce(
    (sum, scale) => sum + (baseRadius * scale) ** 3,
    0
  );
  const targetRadiusCubeSum = targetFraction * cellEquivalentRadius ** 3;
  const factor = Math.cbrt(targetRadiusCubeSum / rawRadiusCubeSum);
  return rawScales.map((scale) => scale * factor);
}

export function visualAnatomyLod(cameraDistance: number, viewportWidth: number): VisualAnatomyLod {
  if (cameraDistance > 48 || (viewportWidth < 700 && cameraDistance > 44)) return "overview";
  if (cameraDistance > 24) return "cellular";
  return "ultrastructure";
}

// Ray/face classification for the canonical truncated-octahedron collision
// proxy: |x|,|y|,|z| <= 2s and |x|+|y|+|z| <= 3s. This keeps renderer domains
// identical to engine faces; it is not donor-specific membrane morphometry.
export function membraneDomainForDirection(x: number, y: number, z: number): VisualAnatomyDomain {
  const magnitude = Math.hypot(x, y, z) || 1;
  const nx = x / magnitude, ny = y / magnitude, nz = z / magnitude;
  const tx = Math.abs(nx) > Number.EPSILON ? 2 / Math.abs(nx) : Number.POSITIVE_INFINITY;
  const ty = Math.abs(ny) > Number.EPSILON ? 2 / Math.abs(ny) : Number.POSITIVE_INFINITY;
  const tz = Math.abs(nz) > Number.EPSILON ? 2 / Math.abs(nz) : Number.POSITIVE_INFINITY;
  const tsum = 3 / (Math.abs(nx) + Math.abs(ny) + Math.abs(nz));
  const firstHit = Math.min(tx, ty, tz, tsum);
  const tolerance = 1e-10;
  const xFaceIsUnique = Math.abs(tx - firstHit) <= tolerance
    && ty - firstHit > tolerance
    && tz - firstHit > tolerance
    && tsum - firstHit > tolerance;
  if (xFaceIsUnique && nx > 0) return "apical";
  if (xFaceIsUnique && nx < 0) return "basolateral";
  return "lateral";
}
