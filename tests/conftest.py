from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pytest

from radar.scorer import LLMResponse

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "samples"
LABELS_CSV = SAMPLES_DIR / "labels.csv"


@dataclass
class Label:
    file: str
    expected_min: int
    expected_max: int
    note: str


def read_labels(path: Path = LABELS_CSV) -> list[Label]:
    with path.open(encoding="utf-8", newline="") as fh:
        return [
            Label(r["file"].strip(), int(r["expected_min"]), int(r["expected_max"]), r.get("note") or "")
            for r in csv.DictReader(fh)
            if (r.get("file") or "").strip()
        ]


class FakeLLM:
    """Returns canned answers in order; records the prompts it received."""

    model = "fake-llm"

    def __init__(self, *answers: str, tokens: int = 10):
        self.answers = list(answers)
        self.tokens = tokens
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> LLMResponse:
        self.prompts.append(prompt)
        return LLMResponse(self.answers.pop(0), self.tokens)


@pytest.fixture
def fake_llm():
    return FakeLLM
