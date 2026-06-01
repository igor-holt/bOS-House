"""Phase 4 Chimera benchmark. Generates auditable JSON artifact."""

from __future__ import annotations

import json
import time

import numpy as np

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

SEED_LIST = list(range(10))
L = 4
M = 4
BETA = 1.0
STEPS = 2000
TTC_THRESHOLD = 0.9


def run_benchmark() -> dict:
    results = {
        "meta": {
            "L": L,
            "M": M,
            "beta": BETA,
            "steps": STEPS,
            "ttc_threshold_ratio": TTC_THRESHOLD,
            "seed_list": SEED_LIST,
            "constants": {
                "J_ij_mean": CONST.J_IJ_MEAN,
                "entropy_seed_eV": CONST.ENTROPY_SEED_EV,
                "flip_bias": CONST.FLIP_BIAS,
                "tau_sw_ps": CONST.TAU_SW_PS,
            },
            "ttc_definition": "TtC = min{t : E(t) <= threshold_ratio * min(E)}. If never reached, TtC = len(trace).",
            "actual_n_reconciliation": "actual_N == 2 * M * L^2",
        },
        "per_seed": [],
        "aggregate": {},
    }

    A_pure = build_chimera_adjacency(L, M)
    pure_gap = spectral_gap(A_pure)

    ttc_pure_list = []
    ttc_hybrid_list = []

    for seed in SEED_LIST:
        J_pure = compute_coupling_matrix(A_pure, seed=seed)
        sim_pure = simulate_pbit_dynamics(J_pure, beta=BETA, steps=STEPS, seed=seed)
        ttc_p = time_to_cut(sim_pure["energy_trace"], TTC_THRESHOLD)
        pr_p = parisi_ratio(sim_pure["energy_trace"])

        A_hyb, hyb_meta = hybrid_chimera_er_bridge(L, M, p_bridge=0.05, seed=seed)
        hyb_gap = spectral_gap(A_hyb)
        J_hyb = compute_coupling_matrix(A_hyb, seed=seed)
        sim_hyb = simulate_pbit_dynamics(J_hyb, beta=BETA, steps=STEPS, seed=seed)
        ttc_h = time_to_cut(sim_hyb["energy_trace"], TTC_THRESHOLD)
        pr_h = parisi_ratio(sim_hyb["energy_trace"])

        ttc_pure_list.append(ttc_p)
        ttc_hybrid_list.append(ttc_h)

        results["per_seed"].append(
            {
                "seed": seed,
                "pure": {
                    "ttc": ttc_p,
                    "parisi_ratio": round(pr_p, 6),
                    "final_energy": round(sim_pure["energy_trace"][-1], 6),
                    "spectral_gap": round(pure_gap, 6),
                },
                "hybrid": {
                    "ttc": ttc_h,
                    "parisi_ratio": round(pr_h, 6),
                    "final_energy": round(sim_hyb["energy_trace"][-1], 6),
                    "spectral_gap": round(hyb_gap, 6),
                    "bridge_edges": hyb_meta["bridge_edge_count"],
                },
                "ttc_delta_pct": round(((ttc_p - ttc_h) / ttc_p * 100) if ttc_p > 0 else 0.0, 4),
            }
        )

    deltas = [r["ttc_delta_pct"] for r in results["per_seed"]]
    results["aggregate"] = {
        "mean_ttc_pure": round(float(np.mean(ttc_pure_list)), 2),
        "mean_ttc_hybrid": round(float(np.mean(ttc_hybrid_list)), 2),
        "mean_ttc_delta_pct": round(float(np.mean(deltas)), 4),
        "std_ttc_delta_pct": round(float(np.std(deltas)), 4),
        "min_ttc_delta_pct": round(float(min(deltas)), 4),
        "max_ttc_delta_pct": round(float(max(deltas)), 4),
    }

    return results


if __name__ == "__main__":
    print("[BENCHMARK] Phase 4 Chimera — executing...")
    t0 = time.time()
    data = run_benchmark()
    data["meta"]["runtime_seconds"] = round(time.time() - t0, 3)

    outfile = "phase4_chimera_benchmark_results.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[BENCHMARK] Complete. {len(SEED_LIST)} seeds. Written to {outfile}")
    print(f"[BENCHMARK] Mean TtC delta: {data['aggregate']['mean_ttc_delta_pct']}%")
    print(f"[BENCHMARK] Artifact: LOCAL_ONLY — {outfile}")
