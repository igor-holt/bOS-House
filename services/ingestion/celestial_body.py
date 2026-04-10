from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import hashlib
import json


@dataclass(slots=True)
class SeismicRecord:
    """Evidence attached to each inferred claim for stress testing."""

    claim: str
    source: str
    confidence: float


@dataclass(slots=True)
class CelestialBody:
    """Canonical A2A schema representing an agent/repo as a celestial object."""

    id: str
    name: str
    kind: str
    mass: float
    atmosphere: dict[str, Any]
    gravity: float
    orbits: list[str] = field(default_factory=list)
    seismic_test: list[SeismicRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["seismic_test"] = [asdict(record) for record in self.seismic_test]
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


_LANGUAGE_WEIGHTS = {
    ".py": 1.2,
    ".rs": 1.4,
    ".js": 1.0,
    ".ts": 1.1,
    ".tsx": 1.15,
    ".jsx": 1.05,
    ".go": 1.25,
    ".java": 1.15,
    ".cpp": 1.3,
    ".c": 1.25,
    ".md": 0.2,
    ".json": 0.3,
    ".yaml": 0.25,
    ".yml": 0.25,
}


class IngestionError(RuntimeError):
    """Raised when repository ingestion cannot proceed safely."""


def _stable_id(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"body_{digest[:16]}"


def _scan_repo(repo_path: Path) -> tuple[list[Path], dict[str, int]]:
    if not repo_path.exists() or not repo_path.is_dir():
        raise IngestionError(f"Repository path does not exist or is not a directory: {repo_path}")

    files: list[Path] = []
    suffix_counts: dict[str, int] = {}
    for file in repo_path.rglob("*"):
        if not file.is_file():
            continue
        if ".git" in file.parts:
            continue
        files.append(file)
        suffix = file.suffix.lower()
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1

    if not files:
        raise IngestionError(f"Repository has no ingestible files: {repo_path}")

    return files, suffix_counts


def _infer_primary_language(suffix_counts: dict[str, int]) -> str:
    if not suffix_counts:
        return "unknown"

    non_source = {".md", ".txt", ".json", ".yaml", ".yml"}
    candidates = {k: v for k, v in suffix_counts.items() if k not in non_source}
    if not candidates:
        candidates = suffix_counts

    suffix = max(candidates.items(), key=lambda item: item[1])[0]
    return suffix.lstrip(".") or "unknown"


def _infer_mass(files: list[Path]) -> float:
    weighted_units = 0.0
    for file in files:
        weight = _LANGUAGE_WEIGHTS.get(file.suffix.lower(), 0.5)
        try:
            size = file.stat().st_size
        except OSError:
            size = 0
        weighted_units += (size / 1024.0) * weight
    return round(max(weighted_units, 0.1), 3)


def _infer_atmosphere(repo_name: str, suffix_counts: dict[str, int]) -> dict[str, Any]:
    return {
        "intent": "exploration",
        "temperament": "adaptive",
        "primary_language": _infer_primary_language(suffix_counts),
        "signature": f"{repo_name}:{len(suffix_counts)}-ecosystems",
    }


def _infer_gravity(mass: float, file_count: int) -> float:
    gravity = (mass ** 0.5) + min(file_count / 50.0, 10.0)
    return round(gravity, 3)


def convert_repo_to_celestial_body(repo_path: str | Path, *, kind: str = "code_repo") -> CelestialBody:
    path = Path(repo_path).resolve()
    files, suffix_counts = _scan_repo(path)
    repo_name = path.name
    mass = _infer_mass(files)

    seismic = [
        SeismicRecord(
            claim="Primary language inferred from file extension frequency.",
            source=str(path),
            confidence=0.72,
        ),
        SeismicRecord(
            claim="Mass estimated from weighted file size by language.",
            source=str(path),
            confidence=0.68,
        ),
    ]

    return CelestialBody(
        id=_stable_id(str(path)),
        name=repo_name,
        kind=kind,
        mass=mass,
        atmosphere=_infer_atmosphere(repo_name, suffix_counts),
        gravity=_infer_gravity(mass, len(files)),
        seismic_test=seismic,
    )
