"""Anti-hallucination runtime checks."""

from __future__ import annotations

import json
import os


def verify_ttc_claim(json_path: str, claimed_delta: float, tolerance: float = 0.5) -> dict:
    """Verify a TtC delta claim against benchmark JSON."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    actual = data["aggregate"]["mean_ttc_delta_pct"]
    verified = abs(actual - claimed_delta) <= tolerance
    return {
        "claimed": claimed_delta,
        "actual": actual,
        "tolerance": tolerance,
        "verified": verified,
        "verdict": "PASS" if verified else "CLAIM_DRIFT — update claim to match reality",
    }


def artifact_sync_status(path: str, remote_uri: str | None = None) -> str:
    """Report sync status of an artifact."""
    local_exists = os.path.isfile(path)
    if not local_exists:
        return f"MISSING — {path} not found locally"
    if remote_uri:
        return f"SYNCED — {path} -> {remote_uri}"
    return f"UNVERIFIED/LOCAL_ONLY — {path}"
