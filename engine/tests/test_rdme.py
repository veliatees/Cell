from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.rdme import (
    RdmeState,
    VoxelLattice,
    rdme_stable_tau,
    rdme_tau_leap_step,
    simulate_rdme,
)
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action


def empty_network() -> ReactionNetwork:
    """No reactions: pure diffusion."""
    return ReactionNetwork(species=("A",), reactions=(), volume_l=1e-15)


class RdmeStateTest(unittest.TestCase):
    def test_sparse_storage_prunes_zeros(self) -> None:
        state = RdmeState()
        state.add(5, "A", 3)
        state.add(5, "A", -3)  # back to zero -> voxel must be dropped
        self.assertEqual(state.n_occupied(), 0)
        self.assertEqual(state.total("A"), 0)

    def test_add_and_total(self) -> None:
        state = RdmeState()
        state.add(0, "A", 10)
        state.add(4, "A", 7)
        self.assertEqual(state.total("A"), 17)
        self.assertEqual(state.get(0, "A"), 10)
        self.assertEqual(state.n_occupied(), 2)


class RdmeDiffusionTest(unittest.TestCase):
    def test_diffusion_conserves_total_and_spreads(self) -> None:
        lattice = VoxelLattice.build(9, 1, 1, dx_um=1.0)
        diffusion = {"A": 1.0}  # um^2/s
        tau = rdme_stable_tau(diffusion, lattice.dx_um)
        state = RdmeState()
        center = lattice.index(4, 0, 0)
        state.add(center, "A", 5000)

        rng = EngineRng(seed=21)
        out = simulate_rdme(lattice, empty_network(), diffusion, state, t_end=2.0, tau=tau, rng=rng)

        # Population is conserved exactly by construction.
        self.assertEqual(out.total("A"), 5000)
        # And it has spread away from the seed voxel.
        self.assertLess(out.get(center, "A"), 5000)
        self.assertGreater(out.get(lattice.index(0, 0, 0), "A") + out.get(lattice.index(8, 0, 0), "A"), 0)

    def test_no_diffusion_constant_is_static(self) -> None:
        lattice = VoxelLattice.build(5, 1, 1, dx_um=1.0)
        state = RdmeState()
        state.add(lattice.index(2, 0, 0), "A", 100)
        rng = EngineRng(seed=5)
        out = rdme_tau_leap_step(lattice, empty_network(), {}, state, tau=0.1, rng=rng)
        self.assertEqual(out.get(lattice.index(2, 0, 0), "A"), 100)
        self.assertEqual(out.n_occupied(), 1)


class RdmeConfinementTest(unittest.TestCase):
    def test_species_confined_to_its_compartment(self) -> None:
        # x == 0 plane is "membrane", everything else "cytosol".
        def label(x, y, z):
            return "membrane" if x == 0 else "cytosol"

        lattice = VoxelLattice.build(6, 3, 1, dx_um=1.0, compartment_of=label)
        diffusion = {"A": 2.0}
        allowed = {"A": {"membrane"}}
        tau = rdme_stable_tau(diffusion, lattice.dx_um)

        state = RdmeState()
        state.add(lattice.index(0, 1, 0), "A", 3000)
        rng = EngineRng(seed=33)
        out = simulate_rdme(
            lattice, empty_network(), diffusion, state, t_end=3.0, tau=tau, rng=rng,
            allowed_compartments=allowed,
        )

        self.assertEqual(out.total("A"), 3000)  # conserved
        # Never leaked into cytosol: every occupied voxel is a membrane voxel.
        for voxel in out.occupied_voxels():
            self.assertEqual(lattice.compartment_of(voxel), "membrane")
        # It did move along the membrane (off the seed row).
        moved = sum(
            out.get(lattice.index(0, y, 0), "A") for y in (0, 2)
        )
        self.assertGreater(moved, 0)


class RdmeReactionTest(unittest.TestCase):
    def test_local_decay_reduces_population(self) -> None:
        lattice = VoxelLattice.build(4, 1, 1, dx_um=1.0)
        decay = mass_action("decay", {"A": 1}, {}, 1.0)  # A -> 0, 1/s
        network = ReactionNetwork(species=("A",), reactions=(decay,), volume_l=lattice.voxel_volume_l)
        state = RdmeState()
        for x in range(4):
            state.add(lattice.index(x, 0, 0), "A", 4000)
        rng = EngineRng(seed=9)
        out = simulate_rdme(lattice, network, {"A": 0.0}, state, t_end=1.0, tau=0.01, rng=rng)
        # ~exp(-1) of 16000 remains; well below the start, well above zero.
        self.assertLess(out.total("A"), 16000)
        self.assertGreater(out.total("A"), 3000)


if __name__ == "__main__":
    unittest.main()
