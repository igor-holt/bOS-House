"""Aggressive structural tests. No placeholders. Every test can fail."""

import numpy as np
import pytest

from constants import CONST
from pbit_array_solver import (
    build_chimera_adjacency,
    compute_coupling_matrix,
    hybrid_chimera_er_bridge,
    parisi_ratio,
    simulate_pbit_dynamics,
    spectral_gap,
    time_to_cut,
)


class TestChimeraAdjacency:
    @pytest.fixture
    def chimera_4x4(self):
        return build_chimera_adjacency(L=4, M=4)

    def test_symmetry(self, chimera_4x4):
        assert np.allclose(chimera_4x4, chimera_4x4.T)

    def test_no_self_loops(self, chimera_4x4):
        assert np.all(np.diag(chimera_4x4) == 0)

    def test_correct_dimensions(self, chimera_4x4):
        assert chimera_4x4.shape == (128, 128)

    def test_intra_cell_K44_completeness(self):
        L, M = 3, 4
        A = build_chimera_adjacency(L, M)
        for r in range(L):
            for c in range(L):
                cell = r * L + c
                left_idx = [cell * 2 * M + i for i in range(M)]
                right_idx = [cell * 2 * M + M + j for j in range(M)]
                for i in left_idx:
                    for j in right_idx:
                        assert A[i, j] == 1.0
                for i in left_idx:
                    for i2 in left_idx:
                        if i != i2:
                            assert A[i, i2] == 0.0

    def test_inter_cell_horizontal(self):
        L, M = 3, 4
        A = build_chimera_adjacency(L, M)
        for r in range(L):
            for c in range(L - 1):
                cell_a = r * L + c
                cell_b = r * L + (c + 1)
                for j in range(M):
                    u = cell_a * 2 * M + M + j
                    v = cell_b * 2 * M + M + j
                    assert A[u, v] == 1.0

    def test_inter_cell_vertical(self):
        L, M = 3, 4
        A = build_chimera_adjacency(L, M)
        for r in range(L - 1):
            for c in range(L):
                cell_a = r * L + c
                cell_b = (r + 1) * L + c
                for i in range(M):
                    u = cell_a * 2 * M + i
                    v = cell_b * 2 * M + i
                    assert A[u, v] == 1.0

    def test_boundary_no_phantom_edges(self):
        L, M = 3, 4
        A = build_chimera_adjacency(L, M)
        expected_edges = L * L * M * M + L * (L - 1) * M + (L - 1) * L * M
        actual_edges = int(np.sum(A)) // 2
        assert actual_edges == expected_edges

    def test_connectivity_via_spectral_gap(self, chimera_4x4):
        assert spectral_gap(chimera_4x4) > 0


class TestHybridBridge:
    def test_determinism(self):
        A1, m1 = hybrid_chimera_er_bridge(L=3, seed=99)
        A2, m2 = hybrid_chimera_er_bridge(L=3, seed=99)
        assert np.array_equal(A1, A2)
        assert m1 == m2

    def test_different_seeds_differ(self):
        A1, _ = hybrid_chimera_er_bridge(L=3, seed=1)
        A2, _ = hybrid_chimera_er_bridge(L=3, seed=2)
        assert not np.array_equal(A1, A2)

    def test_symmetry_preserved(self):
        A, _ = hybrid_chimera_er_bridge(L=4, seed=42)
        assert np.allclose(A, A.T)

    def test_no_self_loops(self):
        A, _ = hybrid_chimera_er_bridge(L=4, seed=42)
        assert np.all(np.diag(A) == 0)

    def test_metadata_reconciliation(self):
        A, meta = hybrid_chimera_er_bridge(L=4, M=4, seed=42)
        assert meta["actual_N"] == meta["expected_N"]
        assert meta["actual_N"] == A.shape[0]
        assert meta["bridge_edge_count"] >= 0


class TestSolver:
    def test_coupling_symmetry(self):
        A = build_chimera_adjacency(L=2)
        J = compute_coupling_matrix(A, seed=7)
        assert np.allclose(J, J.T)
        assert np.all(np.diag(J) == 0)

    def test_simulation_determinism(self):
        A = build_chimera_adjacency(L=2)
        J = compute_coupling_matrix(A, seed=7)
        r1 = simulate_pbit_dynamics(J, steps=500, seed=13)
        r2 = simulate_pbit_dynamics(J, steps=500, seed=13)
        assert r1["final_state"] == r2["final_state"]
        assert r1["energy_trace"] == r2["energy_trace"]

    def test_ttc_monotonic_definition(self):
        trace = [0.0, -1.0, -2.0, -3.0, -2.5, -3.5]
        ttc = time_to_cut(trace, threshold_ratio=0.9)
        assert isinstance(ttc, int)
        assert 0 <= ttc <= len(trace)

    def test_parisi_ratio_equilibrium(self):
        flat = [1.0] * 100
        assert abs(parisi_ratio(flat) - 1.0) < 1e-6

    def test_parisi_ratio_nonzero(self):
        trace = list(range(100))
        assert parisi_ratio(trace) > 0

    def test_locked_constants_used(self):
        A = build_chimera_adjacency(L=2)
        J = compute_coupling_matrix(A)
        nonzero = J[J != 0]
        assert abs(np.mean(nonzero) - CONST.J_IJ_MEAN) < 0.01
