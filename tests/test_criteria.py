from pathlib import Path

import yaml

from radar.criteria import PUBLIC_CRITERIA, criteria_to_yaml, deep_merge, load_criteria


def test_public_criteria_has_required_sections():
    data = yaml.safe_load(PUBLIC_CRITERIA.read_text(encoding="utf-8"))
    for key in ("profile", "location", "language", "seniority", "domains_bonus"):
        assert key in data, key


def test_public_criteria_keeps_weak_spots_private():
    # ADR-007: weak_spots never goes to the public file
    data = yaml.safe_load(PUBLIC_CRITERIA.read_text(encoding="utf-8"))
    assert "weak_spots" not in data["profile"]


def test_deep_merge_merges_dicts_and_replaces_lists():
    base = {"profile": {"summary": "s", "strengths": ["a"]}, "x": 1}
    override = {"profile": {"weak_spots": ["w"], "strengths": ["b"]}}
    assert deep_merge(base, override) == {
        "profile": {"summary": "s", "strengths": ["b"], "weak_spots": ["w"]},
        "x": 1,
    }
    assert base["profile"] == {"summary": "s", "strengths": ["a"]}  # not mutated


def test_load_criteria_overlays_local_file(tmp_path: Path):
    public = tmp_path / "criteria.yaml"
    local = tmp_path / "criteria.local.yaml"
    public.write_text("profile:\n  summary: público\n", encoding="utf-8")
    local.write_text("profile:\n  weak_spots: [X]\n", encoding="utf-8")
    assert load_criteria(public, local)["profile"] == {"summary": "público", "weak_spots": ["X"]}


def test_load_criteria_without_local_file(tmp_path: Path):
    public = tmp_path / "criteria.yaml"
    public.write_text("profile:\n  summary: s\n", encoding="utf-8")
    assert load_criteria(public, tmp_path / "missing.yaml") == {"profile": {"summary": "s"}}


def test_criteria_to_yaml_keeps_accents():
    assert "sênior" in criteria_to_yaml({"seniority": ["sênior"]})
