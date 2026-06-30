from __future__ import annotations

import random
from dataclasses import dataclass, field
from math import exp, sqrt


@dataclass
class EngineRng:
    seed: int
    _random: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

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

