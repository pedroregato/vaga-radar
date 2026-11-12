"""Pydantic model of the JSON returned by the LLM (RF-03) and a tolerant parser (RF-04)."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

WorkModel = Literal["remoto", "hibrido", "presencial"]


class LLMOutputError(ValueError):
    """The LLM answer is not a valid JobScore JSON."""


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


class JobScore(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[WorkModel] = None
    seniority: Optional[str] = None
    english_required: Optional[bool] = None
    location_ok: Optional[bool] = None
    score: int = Field(ge=0, le=10)
    reasons: str = Field(min_length=1)
    red_flags: Optional[str] = None

    @field_validator("work_model", mode="before")
    @classmethod
    def normalize_work_model(cls, value: object) -> object:
        # "Híbrido", "REMOTO" -> values accepted by the table check constraint
        if isinstance(value, str):
            value = _strip_accents(value).strip().lower() or None
        return value

    @field_validator("score", mode="before")
    @classmethod
    def reject_fractional_score(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("score must be an integer, not a boolean")
        if isinstance(value, float) and not value.is_integer():
            raise ValueError("score must be an integer")
        return value

    @field_validator("red_flags", mode="before")
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value if v)
        return value or None


_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def extract_json_object(text: str) -> dict:
    """Return the JSON object in `text`, accepting ```json fences or stray text around it."""
    cleaned = text.strip()
    fenced = _FENCE.match(cleaned)
    if fenced:
        cleaned = fenced.group(1)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise LLMOutputError("no JSON object found in LLM output") from None
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMOutputError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMOutputError("LLM output is JSON but not an object")
    return data


def parse_llm_output(text: str) -> JobScore:
    """Parse and validate the LLM answer; raise LLMOutputError on any problem."""
    data = extract_json_object(text)
    try:
        return JobScore.model_validate(data)
    except ValidationError as exc:
        raise LLMOutputError(str(exc)) from exc
