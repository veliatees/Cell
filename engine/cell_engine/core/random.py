from __future__ import annotations

import random
from dataclasses import dataclass, field


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

