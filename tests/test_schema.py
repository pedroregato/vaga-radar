import json

import pytest

from radar.schema import JobScore, LLMOutputError, parse_llm_output

VALID = {
    "title": "Engenheiro de IA",
    "company": "Empresa X",
    "location": "Rio de Janeiro, RJ",
    "work_model": "hibrido",
    "seniority": "sênior",
    "english_required": False,
    "location_ok": True,
    "score": 8,
    "reasons": "Stack combina.",
    "red_flags": None,
}


def test_valid_json():
    job = parse_llm_output(json.dumps(VALID))
    assert job.score == 8 and job.work_model == "hibrido"


def test_json_inside_markdown_fence():
    assert parse_llm_output("```json\n" + json.dumps(VALID) + "\n```").score == 8


def test_json_with_text_around_it():
    assert parse_llm_output("Aqui está:\n" + json.dumps(VALID) + "\nFim.").score == 8


def test_missing_fields_default_to_null():
    job = parse_llm_output('{"score": 3, "reasons": "Fora do Rio."}')
    assert job.title is None and job.location_ok is None


@pytest.mark.parametrize("raw, expected", [("Híbrido", "hibrido"), ("REMOTO", "remoto"), ("", None)])
def test_work_model_is_normalized(raw, expected):
    assert JobScore(score=5, reasons="r", work_model=raw).work_model == expected


def test_red_flags_list_becomes_text():
    assert JobScore(score=5, reasons="r", red_flags=["a", "b"]).red_flags == "a; b"


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID, "score": 11},
        {**VALID, "score": -1},
        {**VALID, "score": 7.5},
        {**VALID, "score": True},
        {**VALID, "work_model": "home office"},
        {**VALID, "reasons": ""},
        {k: v for k, v in VALID.items() if k != "score"},
    ],
)
def test_invalid_payloads(payload):
    with pytest.raises(LLMOutputError):
        parse_llm_output(json.dumps(payload))


@pytest.mark.parametrize("text", ["", "sem json", "[1, 2]", '{"score": 5, "reasons": "a" // x}'])
def test_not_a_json_object(text):
    with pytest.raises(LLMOutputError):
        parse_llm_output(text)
