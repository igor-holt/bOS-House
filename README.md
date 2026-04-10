# Deterministic Topology Invariance + A2A Ingestion

This repository now contains two aligned layers:

1. **A2A ingestion layer** that converts repos into `CelestialBody` JSON objects.
2. **Deterministic p-bit solver/benchmark layer** that enforces topology invariance between implementation, tests, and benchmark artifacts.

## A2A Ingestion

- Schema + converter: `services/ingestion/celestial_body.py`
- CLI: `services/ingestion/a2a_ingestion.py`
- Unit tests: `tests/test_celestial_body.py`

Run:

```bash
python -m services.ingestion.a2a_ingestion . --output artifacts/celestial_bodies.jsonl
```

## Deterministic Solver Stack

- Locked constants: `constants.py`
- Solver: `pbit_array_solver.py`
- Structural test suite: `test_pbit_array.py`
- Benchmark artifact generator: `benchmark_phase4_chimera.py`
- Claim/sync guardrails: `guardrails.py`
- Runtime state template: `conductor_state.yaml`

Run tests:

```bash
python -m pytest -q
```

Run benchmark:

```bash
python benchmark_phase4_chimera.py
```
