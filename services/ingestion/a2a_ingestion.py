from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json

from services.ingestion.celestial_body import IngestionError, convert_repo_to_celestial_body


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Convert raw repos into CelestialBody JSON objects.")
    parser.add_argument("repos", nargs="+", help="Repository paths to ingest")
    parser.add_argument("--output", default="celestial_bodies.jsonl", help="Output JSONL file")
    parser.add_argument("--kind", default="code_repo", help="Celestial body kind label")
    return parser


def run() -> int:
    args = build_parser().parse_args()
    output = Path(args.output)
    bodies = []

    for repo in args.repos:
        try:
            body = convert_repo_to_celestial_body(repo, kind=args.kind)
            bodies.append(body.to_dict())
        except IngestionError as error:
            print(f"[stability-warning] {error}")

    if not bodies:
        print("No repositories ingested.")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for body in bodies:
            handle.write(json.dumps(body, ensure_ascii=False) + "\n")

    print(f"Ingested {len(bodies)} repositories into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
