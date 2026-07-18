"""Source-traceable healthy primary-human-hepatocyte baseline profiles.

The measurements available for intact healthy human liver are mostly reported per
wet tissue volume or mass, not per isolated-cell cytosolic volume.  These profiles
therefore expose *effective whole-tissue-equivalent* concentrations for the lumped
single-volume model and keep that applicability boundary explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PhhNutritionalState = Literal["fed_peak", "postabsorptive", "prolonged_fasted"]
HUMAN_LIVER_DENSITY_KG_PER_L = 1.054


@dataclass(frozen=True)
class PhhPoolValue:
    value_mM: float
    low_mM: float | None
    high_mM: float | None
    source_ids: tuple[str, ...]
    evidence: Literal["measured", "derived"]
    basis: str
    notes: str = ""


@dataclass(frozen=True)
class PhhNutritionalProfile:
    id: PhhNutritionalState
    label: str
    pools: dict[str, PhhPoolValue]

    def concentrations_mM(self) -> dict[str, float]:
        return {species: pool.value_mM for species, pool in self.pools.items()}

    def energy_charge(self) -> float:
        atp = self.pools["ATP"].value_mM
        adp = self.pools["ADP"].value_mM
        amp = self.pools["AMP"].value_mM
        return (atp + 0.5 * adp) / (atp + adp + amp)


def _wet_tissue_mM(umol_per_g: float) -> float:
    """Convert umol/g wet liver to mmol/L wet liver using measured liver density."""
    return umol_per_g * HUMAN_LIVER_DENSITY_KG_PER_L


_ADENYLATES = {
    "ATP": PhhPoolValue(
        _wet_tissue_mM(2.080), None, None, ("human_liver_adenylates_1992", "human_liver_phosphorus_mrs_2017"), "derived",
        "whole_tissue_equivalent_mM",
        "Control human-liver HPLC mean converted with 1.054 kg/L liver density.",
    ),
    "ADP": PhhPoolValue(
        _wet_tissue_mM(1.170), None, None, ("human_liver_adenylates_1992", "human_liver_phosphorus_mrs_2017"), "derived",
        "whole_tissue_equivalent_mM",
        "Control human-liver HPLC mean converted with 1.054 kg/L liver density.",
    ),
    "AMP": PhhPoolValue(
        _wet_tissue_mM(0.445), None, None, ("human_liver_adenylates_1992", "human_liver_phosphorus_mrs_2017"), "derived",
        "whole_tissue_equivalent_mM",
        "Control human-liver HPLC mean converted with 1.054 kg/L liver density.",
    ),
    "NAD_plus": PhhPoolValue(
        _wet_tissue_mM(0.632), None, None, ("human_liver_adenylates_1992", "human_liver_phosphorus_mrs_2017"), "derived",
        "whole_tissue_equivalent_mM",
        "Total tissue NAD+; no cytosol/matrix split is inferred.",
    ),
}


def _profile(
    profile_id: PhhNutritionalState,
    label: str,
    glycogen: PhhPoolValue,
    extra_pools: dict[str, PhhPoolValue] | None = None,
) -> PhhNutritionalProfile:
    return PhhNutritionalProfile(profile_id, label, {**_ADENYLATES, "glycogen": glycogen, **(extra_pools or {})})


PHH_NUTRITIONAL_PROFILES: dict[PhhNutritionalState, PhhNutritionalProfile] = {
    "fed_peak": _profile(
        "fed_peak", "Fed peak",
        PhhPoolValue(316.0, 297.0, 335.0, ("human_liver_glycogen_mixed_meal_2000",), "measured", "in_vivo_liver_mM", "Peak after a mixed meal; bounds are mean +/- SEM."),
    ),
    "postabsorptive": _profile(
        "postabsorptive", "Postabsorptive / overnight fast",
        PhhPoolValue(229.0, 195.0, 263.0, ("human_liver_glycogen_overnight_1996",), "measured", "in_vivo_liver_mM", "Healthy volunteers without carbohydrate preparation; bounds are mean +/- SEM."),
        {"glucose_blood": PhhPoolValue(4.75, 3.9, 5.6, ("hmdb_2022",), "derived", "human_plasma_mM", "Midpoint of the curated fasting plasma range; used only at the sinusoidal boundary.")},
    ),
    "prolonged_fasted": _profile(
        "prolonged_fasted", "Prolonged fast",
        PhhPoolValue(39.5, 24.0, 55.0, ("human_liver_glycogen_starvation_1973",), "derived", "mmol_glucosyl_per_kg_wet_liver", "Midpoint of the reported biopsy range; tissue-mass denominator retained as an effective lumped-model value."),
    ),
}


DEFAULT_PHH_PROFILE_ID: PhhNutritionalState = "postabsorptive"


def phh_profile(profile_id: PhhNutritionalState = DEFAULT_PHH_PROFILE_ID) -> PhhNutritionalProfile:
    return PHH_NUTRITIONAL_PROFILES[profile_id]


def phh_profiles_snapshot(
    selected_profile_id: PhhNutritionalState = DEFAULT_PHH_PROFILE_ID,
) -> dict[str, object]:
    selected = phh_profile(selected_profile_id)
    return {
        "selected_profile": selected.id,
        "profiles": {
            profile.id: {
                "label": profile.label,
                "energy_charge": profile.energy_charge(),
                "pools": profile.pools,
            }
            for profile in PHH_NUTRITIONAL_PROFILES.values()
        },
        "applicability": "Healthy human liver tissue-equivalent baseline for a lumped hepatocyte model; not donor-matched isolated PHH cytosol.",
    }
