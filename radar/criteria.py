"""Load the scoring criteria: public config merged with the private local file (ADR-007)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_CRITERIA = ROOT / "config" / "criteria.yaml"
LOCAL_CRITERIA = ROOT / "config" / "criteria.local.yaml"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge dicts recursively; lists and scalars in `override` replace `base`."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_criteria(
    public_path: Path = PUBLIC_CRITERIA,
    local_path: Path | None = LOCAL_CRITERIA,
) -> dict[str, Any]:
    """Return the public criteria, overlaid with the local file when it exists."""
    criteria = _read_yaml(public_path)
    if local_path is not None and local_path.exists():
        criteria = deep_merge(criteria, _read_yaml(local_path))
    return criteria


def criteria_to_yaml(criteria: dict[str, Any]) -> str:
    """Serialize criteria for the prompt, keeping key order and accents."""
    return yaml.safe_dump(criteria, allow_unicode=True, sort_keys=False, width=100)
