"""Checks on samples/ that run without the LLM: labels are consistent and data is anonymized."""

import re

import pytest

from tests.conftest import LABELS_CSV, SAMPLES_DIR, read_labels

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}")


def sample_files():
    return sorted(p for p in SAMPLES_DIR.iterdir() if p.is_file() and p.suffix in {".txt", ".md", ".eml"}
                  and p.name != "README.md")


def test_labels_header():
    assert LABELS_CSV.read_text(encoding="utf-8").splitlines()[0] == "file,expected_min,expected_max,note"


@pytest.mark.parametrize("label", read_labels(), ids=lambda l: l.file)
def test_label_is_consistent(label):
    assert (SAMPLES_DIR / label.file).is_file(), f"{label.file} listed in labels.csv but missing"
    assert 0 <= label.expected_min <= label.expected_max <= 10


@pytest.mark.parametrize("path", sample_files(), ids=lambda p: p.name)
def test_sample_is_anonymized(path):
    text = path.read_text(encoding="utf-8")
    assert not EMAIL.search(text), f"{path.name}: e-mail address, use <EMAIL>"
    assert not PHONE.search(text), f"{path.name}: phone number, use <TELEFONE>"


@pytest.mark.parametrize("path", sample_files(), ids=lambda p: p.name)
def test_every_sample_is_labeled(path):
    assert path.name in {l.file for l in read_labels()}, f"{path.name} has no row in labels.csv"


@pytest.mark.parametrize("path", sample_files(), ids=lambda p: p.name)
def test_sample_name_has_group_prefix(path):
    # ADR-009: synthetic_* (rules) or real_* (anonymized alerts)
    assert path.name.startswith(("synthetic_", "real_")), f"{path.name}: use synthetic_ or real_ prefix"
