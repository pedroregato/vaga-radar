"""Prompt accuracy against labeled samples (PRD, section 6). Calls the real LLM: `pytest -m llm`."""

import pytest

from radar.criteria import criteria_to_yaml, load_criteria
from radar.scorer import client_from_env, load_prompt_template, score_job
from tests.conftest import SAMPLES_DIR, read_labels

TARGET = 0.90

pytestmark = pytest.mark.llm


def test_accuracy_on_samples():
    labels = read_labels()
    if not labels:
        pytest.skip("samples/labels.csv has no labeled samples yet")
    client = client_from_env()
    criteria_yaml, template = criteria_to_yaml(load_criteria()), load_prompt_template()

    hits, report, total_tokens = 0, [], 0
    groups: dict[str, list[bool]] = {}
    for label in labels:
        text = (SAMPLES_DIR / label.file).read_text(encoding="utf-8")
        result = score_job(text, client, criteria_yaml=criteria_yaml, template=template)
        total_tokens += result.tokens or 0
        ok = result.score is not None and label.expected_min <= result.score <= label.expected_max
        hits += ok
        groups.setdefault(label.file.split("_", 1)[0], []).append(ok)
        report.append(f"{'OK ' if ok else 'ERR'} {label.file}: got {result.score} "
                      f"expected {label.expected_min}-{label.expected_max} ({result.status})")

    accuracy = hits / len(labels)
    print("\n" + "\n".join(report))
    for group, oks in sorted(groups.items()):  # ADR-009: synthetic and real reported apart
        print(f"{group}: {sum(oks)}/{len(oks)} ({sum(oks) / len(oks):.0%})")
    print(f"accuracy={accuracy:.0%} ({hits}/{len(labels)}) tokens={total_tokens} model={client.model}")
    assert accuracy >= TARGET, f"accuracy {accuracy:.0%} below {TARGET:.0%}"
