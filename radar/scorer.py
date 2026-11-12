"""Build the triage prompt and score a job posting with an LLM (RF-03, RF-04)."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Protocol

from radar import PROMPT_VERSION
from radar.criteria import ROOT, criteria_to_yaml, load_criteria
from radar.schema import JobScore, LLMOutputError, parse_llm_output

PROMPTS_DIR = ROOT / "prompts"
_CODE_BLOCK = re.compile(r"```[a-zA-Z]*\n(.*?)\n```", re.DOTALL)
PLACEHOLDERS = ("{{criteria_yaml}}", "{{job_text}}")


# --- prompt -----------------------------------------------------------------

def load_prompt_template(version: str = PROMPT_VERSION, prompts_dir: Path = PROMPTS_DIR) -> str:
    """Return the first fenced code block of prompts/<version>.md."""
    path = prompts_dir / f"{version}.md"
    match = _CODE_BLOCK.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{path} has no fenced code block with the prompt")
    template = match.group(1)
    missing = [p for p in PLACEHOLDERS if p not in template]
    if missing:
        raise ValueError(f"{path} is missing placeholders: {missing}")
    return template


def build_prompt(job_text: str, criteria_yaml: str, template: str) -> str:
    # str.replace (not str.format) so braces in the JSON example and in job text are safe
    return template.replace("{{criteria_yaml}}", criteria_yaml.strip()).replace(
        "{{job_text}}", job_text.strip()
    )


# --- LLM clients ------------------------------------------------------------

@dataclass
class LLMResponse:
    text: str
    tokens: Optional[int] = None


class LLMClient(Protocol):
    model: str

    def complete(self, prompt: str) -> LLMResponse: ...


class GeminiClient:
    def __init__(self, model: str, api_key: str):
        from google import genai  # lazy: tests never import the SDK

        self.model = model
        self._client = genai.Client(api_key=api_key)

    def complete(self, prompt: str) -> LLMResponse:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0, response_mime_type="application/json"
            ),
        )
        usage = getattr(response, "usage_metadata", None)
        return LLMResponse(text=response.text or "", tokens=getattr(usage, "total_token_count", None))


class AnthropicClient:
    def __init__(self, model: str, api_key: str):
        import anthropic  # lazy

        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(self, prompt: str) -> LLMResponse:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        usage = message.usage
        return LLMResponse(text=text, tokens=usage.input_tokens + usage.output_tokens)


class DeepSeekClient:
    """DeepSeek through its OpenAI-compatible API (ADR-010)."""

    BASE_URL = "https://api.deepseek.com"

    def __init__(self, model: str, api_key: str):
        from openai import OpenAI  # lazy

        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL)

    def complete(self, prompt: str) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=1024,
            response_format={"type": "json_object"},
            # thinking is on by default; a scoring task does not need it (ADR-010)
            extra_body={"thinking": {"type": "disabled"}},
        )
        usage = response.usage
        return LLMResponse(
            text=response.choices[0].message.content or "",
            tokens=usage.total_tokens if usage else None,
        )


DEFAULT_PROVIDER = "deepseek"
DEFAULT_MODELS = {
    "deepseek": "deepseek-flash",
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-haiku-5-5",
}
API_KEY_VARS = {
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
CLIENTS = {"deepseek": DeepSeekClient, "gemini": GeminiClient, "anthropic": AnthropicClient}


def client_from_env() -> LLMClient:
    """Build the client from LLM_PROVIDER / LLM_MODEL / *_API_KEY (see .env.example)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:  # pragma: no cover
        pass
    provider = os.environ.get("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower() or DEFAULT_PROVIDER
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"LLM_PROVIDER must be one of {sorted(DEFAULT_MODELS)}, got {provider!r}")
    model = os.environ.get("LLM_MODEL", "").strip() or DEFAULT_MODELS[provider]
    key_var = API_KEY_VARS[provider]
    api_key = os.environ.get(key_var, "").strip()
    if not api_key:
        raise RuntimeError(f"{key_var} is not set (see .env.example)")
    return CLIENTS[provider](model, api_key)


# --- scoring ----------------------------------------------------------------

@dataclass
class ScoreResult:
    status: Literal["ok", "llm_error"]
    job: Optional[JobScore]
    attempts: int
    tokens: Optional[int]
    model: str
    prompt_version: str
    error: Optional[str] = None

    @property
    def score(self) -> Optional[int]:
        return self.job.score if self.job else None


def score_job(
    job_text: str,
    client: LLMClient,
    criteria_yaml: Optional[str] = None,
    template: Optional[str] = None,
    max_attempts: int = 2,
) -> ScoreResult:
    """Score one job. Invalid JSON is retried once; then status is llm_error (RF-04)."""
    if criteria_yaml is None:
        criteria_yaml = criteria_to_yaml(load_criteria())
    if template is None:
        template = load_prompt_template()
    prompt = build_prompt(job_text, criteria_yaml, template)

    tokens: Optional[int] = None
    error: Optional[str] = None
    for attempt in range(1, max_attempts + 1):
        response = client.complete(prompt)
        if response.tokens is not None:
            tokens = (tokens or 0) + response.tokens
        try:
            job = parse_llm_output(response.text)
        except LLMOutputError as exc:
            error = str(exc)
            continue
        return ScoreResult("ok", job, attempt, tokens, client.model, PROMPT_VERSION)
    return ScoreResult("llm_error", None, max_attempts, tokens, client.model, PROMPT_VERSION, error)


# --- CLI --------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m radar.scorer", description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--print-criteria", action="store_true",
                       help="print merged criteria (to paste into the N8N node)")
    group.add_argument("--print-prompt", metavar="FILE", type=Path,
                       help="print the full prompt for a job text file, without calling the LLM")
    group.add_argument("--score", metavar="FILE", type=Path,
                       help="score a job text file with the configured LLM")
    args = parser.parse_args(argv)

    criteria_yaml = criteria_to_yaml(load_criteria())
    if args.print_criteria:
        print(criteria_yaml, end="")
        return 0
    path = args.print_prompt or args.score
    job_text = path.read_text(encoding="utf-8")
    if args.print_prompt:
        print(build_prompt(job_text, criteria_yaml, load_prompt_template()))
        return 0
    result = score_job(job_text, client_from_env(), criteria_yaml=criteria_yaml)
    if result.job:
        print(result.job.model_dump_json(indent=2))
    print(f"status={result.status} attempts={result.attempts} tokens={result.tokens} "
          f"model={result.model} prompt={result.prompt_version}", file=sys.stderr)
    if result.error:
        print(f"error: {result.error}", file=sys.stderr)
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
