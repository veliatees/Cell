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

