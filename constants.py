"""Axiomatic locked parameters. Import-only. Never mutate."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Phase2Constants:
    """Invariant physics substrate. Hash-locked at build time."""

    J_IJ_MEAN: Final[float] = 0.021
    ENTROPY_SEED_EV: Final[float] = 0.037
    FLIP_BIAS: Final[float] = 0.14
    TAU_SW_PS: Final[float] = 6.8  # picoseconds

    QUARANTINE_FILES: Final[tuple[str, ...]] = (
        "er_epr_hypersphere.py",
        "device_pbit_cell.py",
        "test_phase3.py",
    )


CONST = Phase2Constants()
