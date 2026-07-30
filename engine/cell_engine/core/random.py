from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import exp, sqrt


# Bumped whenever the on-disk shape of a captured RNG state changes, so a resume
# can fail closed instead of silently reinterpreting an incompatible payload.
RNG_STATE_VERSION = "engine_rng_state_v1"


@dataclass
class EngineRng:
    seed: int
    _random: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

    def get_state(self) -> dict[str, object]:
        """JSON-serialisable capture of the *full* generator state.

        This is the load-bearing primitive for checkpoint/resume/fork: it
        records the Mersenne-Twister internal vector (and the cached Box-Muller
        value used by :meth:`gauss`), which the bare ``seed`` cannot, so a run
        can be continued bit-identically from mid-stream rather than only
        replayed from the start.
        """
        mt_version, internal, gauss_next = self._random.getstate()
        return {
            "state_version": RNG_STATE_VERSION,
            "seed": self.seed,
            "mt_version": mt_version,
            "internal": list(internal),
            "gauss_next": gauss_next,
        }

    def set_state(self, captured: Mapping[str, object]) -> None:
        """Restore a state previously produced by :meth:`get_state`.

        Fails closed on an unrecognised payload shape rather than resuming from
        a silently wrong stream position.
        """
        state_version = captured.get("state_version")
        if state_version != RNG_STATE_VERSION:
            raise ValueError(
                "cannot restore EngineRng: expected state_version "
                f"{RNG_STATE_VERSION!r}, got {state_version!r}"
            )
        gauss_next = captured["gauss_next"]
        self._random.setstate(
            (
                int(captured["mt_version"]),
                tuple(int(word) for word in captured["internal"]),  # type: ignore[arg-type]
                None if gauss_next is None else float(gauss_next),
            )
        )
        self.seed = int(captured["seed"])

    @classmethod
    def from_state(cls, captured: Mapping[str, object]) -> "EngineRng":
        """Build a new, independent generator positioned at a captured state.

        Used to *fork* a run: the parent keeps drawing from its own generator
        while the child continues from the same point in an isolated one. The
        two reproduce identically until their inputs diverge, which is exactly
        what a counterfactual re-run from a checkpoint needs.
        """
        rng = cls(seed=int(captured["seed"]))
        rng.set_state(captured)
        return rng

    def random(self) -> float:
        return self._random.random()

    def expovariate(self, rate: float) -> float:
        """Exponential waiting time with the given total rate (for Gillespie SSA)."""
        return self._random.expovariate(rate)

    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """Normal draw for the chemical Langevin (Euler-Maruyama) integrator."""
        return self._random.gauss(mu, sigma)

    def poisson(self, lam: float) -> int:
        """Poisson draw with mean ``lam`` (number of events in a tau-leap /
        RDME diffusion-hop interval). Knuth's exact product method for small
        means; a rounded, clamped normal approximation for large means where
        Knuth's loop would be slow. Stdlib only."""
        if lam <= 0.0:
            return 0
        if lam < 30.0:
            # Knuth: count unit-rate exponential arrivals within one interval.
            target = exp(-lam)
            k = 0
            product = self._random.random()
            while product > target:
                k += 1
                product *= self._random.random()
            return k
        # Large mean: Poisson -> Normal(lam, lam); round and clamp at zero.
        value = self._random.gauss(lam, sqrt(lam))
        return max(0, int(value + 0.5))

