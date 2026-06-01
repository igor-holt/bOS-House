"""Deterministic p-bit array solver. No placeholders. No drift."""

from __future__ import annotations

import numpy as np
from numpy.random import Generator, default_rng
from scipy.linalg import eigvalsh
from scipy.sparse.csgraph import laplacian

from constants import CONST


def build_chimera_adjacency(L: int, M: int = 4) -> np.ndarray:
    """Build true Chimera C(L, M) adjacency matrix."""
    N = 2 * M * L * L
    A = np.zeros((N, N), dtype=np.float64)

    def qubit_index(row: int, col: int, partition: int, idx: int) -> int:
        cell = row * L + col
        return cell * (2 * M) + partition * M + idx

    for r in range(L):
        for c in range(L):
            for i in range(M):
                for j in range(M):
                    u = qubit_index(r, c, 0, i)
                    v = qubit_index(r, c, 1, j)
                    A[u, v] = 1.0
                    A[v, u] = 1.0

            if c < L - 1:
                for j in range(M):
                    u = qubit_index(r, c, 1, j)
                    v = qubit_index(r, c + 1, 1, j)
                    A[u, v] = 1.0
                    A[v, u] = 1.0

            if r < L - 1:
                for i in range(M):
                    u = qubit_index(r, c, 0, i)
                    v = qubit_index(r + 1, c, 0, i)
                    A[u, v] = 1.0
                    A[v, u] = 1.0

    np.fill_diagonal(A, 0.0)
    assert np.allclose(A, A.T), "SYMMETRY VIOLATION"
    return A


def hybrid_chimera_er_bridge(
    L: int,
    M: int = 4,
    p_bridge: float = 0.05,
    seed: int = 42,
) -> tuple[np.ndarray, dict]:
    """Chimera base + deterministic Erdos-Renyi bridge edges."""
    rng: Generator = default_rng(seed)
    A = build_chimera_adjacency(L, M)
    N = A.shape[0]
    bridge_count = 0

    for i in range(N):
        for j in range(i + 1, N):
            if A[i, j] == 0.0 and rng.random() < p_bridge:
                A[i, j] = 1.0
                A[j, i] = 1.0
                bridge_count += 1

    np.fill_diagonal(A, 0.0)
    meta = {
        "grid_L": L,
        "partition_M": M,
        "actual_N": N,
        "expected_N": 2 * M * L * L,
        "bridge_edge_count": bridge_count,
        "p_bridge": p_bridge,
        "seed": seed,
        "reconciliation": "actual_N == 2 * M * L^2",
    }
    assert meta["actual_N"] == meta["expected_N"], "N RECONCILIATION FAILURE"
    return A, meta


def spectral_gap(A: np.ndarray) -> float:
    """Return algebraic connectivity λ₂ of combinatorial Laplacian."""
    L_mat = laplacian(A, normed=False)
    eigenvalues = eigvalsh(L_mat)
    eigenvalues.sort()
    if len(eigenvalues) < 2:
        return 0.0
    return float(max(eigenvalues[1], 0.0))


def compute_coupling_matrix(
    A: np.ndarray,
    J_mean: float = CONST.J_IJ_MEAN,
    seed: int = 42,
) -> np.ndarray:
    """Generate symmetric coupling matrix J_ij from adjacency with deterministic noise."""
    rng = default_rng(seed)
    N = A.shape[0]
    noise = rng.normal(0, J_mean * 0.1, size=(N, N))
    noise = (noise + noise.T) / 2
    J = A * (J_mean + noise)
    np.fill_diagonal(J, 0.0)
    return J


def simulate_pbit_dynamics(
    J: np.ndarray,
    beta: float = 1.0,
    steps: int = 1000,
    flip_bias: float = CONST.FLIP_BIAS,
    seed: int = 42,
) -> dict:
    """Run deterministic p-bit Glauber dynamics."""
    rng = default_rng(seed)
    N = J.shape[0]
    spins = rng.choice([-1, 1], size=N).astype(np.float64)
    mag_trace: list[float] = []
    energy_trace: list[float] = []

    for step in range(steps):
        i = step % N
        h_i = float(J[i] @ spins + flip_bias)
        p_up = 1.0 / (1.0 + np.exp(-2.0 * beta * h_i))
        spins[i] = 1.0 if rng.random() < p_up else -1.0
        mag_trace.append(float(np.mean(spins)))
        energy_trace.append(float(-0.5 * spins @ J @ spins))

    return {
        "final_state": spins.tolist(),
        "magnetization_trace": mag_trace,
        "energy_trace": energy_trace,
    }


def time_to_cut(energy_trace: list[float], threshold_ratio: float = 0.9) -> int:
    """First step where energy drops below threshold_ratio * E_min."""
    e_min = min(energy_trace)
    target = threshold_ratio * e_min
    for t, e in enumerate(energy_trace):
        if e <= target:
            return t
    return len(energy_trace)


def parisi_ratio(energy_trace: list[float]) -> float:
    """Variance(second half) / variance(first half)."""
    mid = len(energy_trace) // 2
    if mid == 0:
        return 0.0
    var_first = float(np.var(energy_trace[:mid]))
    var_second = float(np.var(energy_trace[mid:]))
    if var_first == 0.0 and var_second == 0.0:
        return 1.0
    if var_first == 0.0:
        return float("inf")
    return var_second / var_first
