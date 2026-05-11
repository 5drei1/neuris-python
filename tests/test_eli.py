"""Unit tests for ELI helpers."""

from __future__ import annotations

import pytest

from neuris.eli import ELI, build_eli, eli_to_url_path, parse_eli

# ── parse_eli ─────────────────────────────────────────────────────────────────

def test_parse_eli_full_expression() -> None:
    eli = parse_eli("eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1")
    assert eli.jurisdiction == "bgbl-1"
    assert eli.agent == "1949"
    assert eli.year == "grundgesetz"
    assert eli.natural_number == "2023-12-19"
    assert eli.point_in_time == "1"
    assert eli.version == "deu"
    assert eli.language == "regelungstext-1"
    assert eli.subtype is None


def test_parse_eli_work_level() -> None:
    eli = parse_eli("eli/bgbl-1/1949/grundgesetz")
    assert eli.jurisdiction == "bgbl-1"
    assert eli.point_in_time is None
    assert eli.version is None
    assert eli.language is None
    assert not eli.is_expression


def test_parse_eli_with_leading_eli_prefix() -> None:
    eli = parse_eli("eli/de/bgbl-1/2023/s1234")
    assert eli.jurisdiction == "de"


def test_parse_eli_without_prefix() -> None:
    eli = parse_eli("de/bgbl-1/2023/s1234")
    assert eli.jurisdiction == "de"
    assert eli.agent == "bgbl-1"


def test_parse_eli_too_short_raises() -> None:
    with pytest.raises(ValueError, match="at least 3"):
        parse_eli("eli/bgbl-1")


def test_parse_eli_minimal_three_parts() -> None:
    eli = parse_eli("eli/a/b/c")
    assert eli.jurisdiction == "a"
    assert eli.year == "c"
    assert eli.natural_number == ""


# ── ELI.is_expression ─────────────────────────────────────────────────────────

def test_is_expression_true() -> None:
    eli = ELI("bgbl-1", "1949", "gg", "s1", point_in_time="2023-01-01", version=None, language=None, subtype=None)
    assert eli.is_expression is True


def test_is_expression_false() -> None:
    eli = ELI("bgbl-1", "1949", "gg", "s1", point_in_time=None, version=None, language=None, subtype=None)
    assert eli.is_expression is False


# ── ELI.to_work ───────────────────────────────────────────────────────────────

def test_to_work_strips_expression() -> None:
    eli = parse_eli("eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1")
    work = eli.to_work()
    assert work.point_in_time is None
    assert work.version is None
    assert work.language is None
    assert work.subtype is None
    assert not work.is_expression


# ── ELI.build ─────────────────────────────────────────────────────────────────

def test_build_work_eli() -> None:
    eli = ELI("bgbl-1", "1949", "grundgesetz", "2023-12-19", point_in_time=None, version=None, language=None, subtype=None)
    assert eli.build() == "eli/bgbl-1/1949/grundgesetz/2023-12-19"


def test_build_expression_eli() -> None:
    eli = parse_eli("eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1")
    rebuilt = eli.build()
    assert rebuilt == "eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1"


def test_str_equals_build() -> None:
    eli = parse_eli("eli/bgbl-1/1949/gg/2023-01-01")
    assert str(eli) == eli.build()


# ── build_eli ─────────────────────────────────────────────────────────────────

def test_build_eli_function_minimal() -> None:
    result = build_eli("bgbl-1", "2023", 2023, "s1234")
    assert result == "eli/bgbl-1/2023/2023/s1234"


def test_build_eli_function_full() -> None:
    result = build_eli(
        "bgbl-1", "2023", 2023, "s1234",
        point_in_time="2023-06-07",
        version="1",
        language="deu",
        subtype="regelungstext-1",
    )
    assert "eli/" in result
    assert "2023" in result
    assert "deu" in result


# ── eli_to_url_path ────────────────────────────────────────────────────────────

def test_eli_to_url_path_basic() -> None:
    path = eli_to_url_path("eli/bgbl-1/1949/grundgesetz")
    assert path.startswith("eli/")
    assert "bgbl-1" in path


def test_eli_roundtrip() -> None:
    original = "eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1"
    parsed = parse_eli(original)
    rebuilt = parsed.build()
    assert rebuilt == original
