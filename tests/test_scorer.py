import json

import pytest

from radar import PROMPT_VERSION
from radar.scorer import (
    build_prompt,
    client_from_env,
    load_prompt_template,
    main,
    score_job,
)

OK = json.dumps({"score": 8, "reasons": "Combina com o perfil.", "work_model": "remoto"})


def test_template_has_placeholders_and_no_json_comments():
    template = load_prompt_template()
    assert "{{criteria_yaml}}" in template and "{{job_text}}" in template
    assert "//" not in template  # the model tends to copy comments into the JSON


def test_build_prompt_fills_placeholders_and_keeps_braces():
    template = load_prompt_template()
    prompt = build_prompt("Vaga {com chaves} em Python", "profile: x", template)
    assert "{{" not in prompt
    assert "Vaga {com chaves} em Python" in prompt and "profile: x" in prompt


def test_score_ok_first_try(fake_llm):
    llm = fake_llm(OK)
    result = score_job("vaga", llm, criteria_yaml="c: 1")
    assert (result.status, result.score, result.attempts, result.tokens) == ("ok", 8, 1, 10)
    assert result.prompt_version == PROMPT_VERSION and result.model == "fake-llm"
    assert "vaga" in llm.prompts[0]


def test_score_retries_once_after_invalid_json(fake_llm):
    llm = fake_llm("não é json", OK)
    result = score_job("vaga", llm, criteria_yaml="c: 1")
    assert (result.status, result.attempts, result.tokens) == ("ok", 2, 20)


def test_score_llm_error_after_two_invalid_answers(fake_llm):
    llm = fake_llm("x", '{"score": 99, "reasons": "r"}')
    result = score_job("vaga", llm, criteria_yaml="c: 1")
    assert result.status == "llm_error" and result.job is None and result.score is None
    assert result.attempts == 2 and len(llm.prompts) == 2 and result.error


def test_score_uses_real_criteria_by_default(fake_llm):
    llm = fake_llm(OK)
    score_job("vaga", llm)
    assert "strengths" in llm.prompts[0]


def test_client_from_env_requires_api_key(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        client_from_env()


def test_client_from_env_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        client_from_env()


def test_cli_print_prompt(tmp_path, capsys):
    job = tmp_path / "vaga.txt"
    job.write_text("Engenheiro de IA, remoto", encoding="utf-8")
    assert main(["--print-prompt", str(job)]) == 0
    assert "Engenheiro de IA, remoto" in capsys.readouterr().out


def test_cli_print_criteria(capsys):
    assert main(["--print-criteria"]) == 0
    assert "profile:" in capsys.readouterr().out


@pytest.mark.parametrize(
    "provider, key_var, client_name, model",
    [
        ("", "DEEPSEEK_API_KEY", "DeepSeekClient", "deepseek-flash"),
        ("deepseek", "DEEPSEEK_API_KEY", "DeepSeekClient", "deepseek-flash"),
        ("gemini", "GEMINI_API_KEY", "GeminiClient", "gemini-2.5-flash"),
        ("anthropic", "ANTHROPIC_API_KEY", "AnthropicClient", "claude-haiku-5-5"),
    ],
)
def test_client_from_env_picks_provider(monkeypatch, provider, key_var, client_name, model):
    import radar.scorer as scorer

    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv(key_var, "test-key")

    class Recorder:
        def __init__(self, model, api_key):
            self.model, self.api_key = model, api_key

    monkeypatch.setitem(scorer.CLIENTS, provider or scorer.DEFAULT_PROVIDER, Recorder)
    client = client_from_env()
    assert (client.model, client.api_key) == (model, "test-key")
    assert getattr(scorer, client_name)  # real client class exists


def test_deepseek_request_disables_thinking_and_asks_json(monkeypatch):
    import radar.scorer as scorer

    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            msg = type("M", (), {"content": OK})
            choice = type("C", (), {"message": msg})
            usage = type("U", (), {"total_tokens": 42})
            return type("R", (), {"choices": [choice], "usage": usage})

    class FakeOpenAI:
        def __init__(self, api_key, base_url):
            captured["base_url"] = base_url
            self.chat = type("Chat", (), {"completions": FakeCompletions()})

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    response = scorer.DeepSeekClient("deepseek-flash", "k").complete("prompt com JSON")
    assert response.tokens == 42 and json.loads(response.text)["score"] == 8
    assert captured["base_url"] == "https://api.deepseek.com"
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}
    assert captured["model"] == "deepseek-flash" and captured["temperature"] == 0
