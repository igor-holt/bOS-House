from pathlib import Path

from services.ingestion.celestial_body import convert_repo_to_celestial_body


def test_convert_repo_to_celestial_body_returns_expected_shape(tmp_path: Path) -> None:
    repo = tmp_path / "demo-repo"
    repo.mkdir()
    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / "README.md").write_text("demo\n", encoding="utf-8")

    body = convert_repo_to_celestial_body(repo)

    assert body.name == "demo-repo"
    assert body.kind == "code_repo"
    assert body.mass > 0
    assert body.gravity > 0
    assert body.atmosphere["primary_language"] == "py"
    assert len(body.seismic_test) >= 2
