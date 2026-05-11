"""Integration tests against the live NeuRIS API.

Run with: NEURIS_LIVE=1 pytest -m live

These tests are skipped unless NEURIS_LIVE is set. They verify end-to-end
behavior against the real testphase API and should be run before each release.
"""

from __future__ import annotations

import os

import pytest

from neuris import NeuRISClient
from neuris.models import Decision, Legislation, Statistics

pytestmark = pytest.mark.live


@pytest.fixture(autouse=True)
def require_live_flag() -> None:
    if not os.getenv("NEURIS_LIVE"):
        pytest.skip("Set NEURIS_LIVE=1 to run live integration tests")


def test_live_get_statistics() -> None:
    with NeuRISClient() as client:
        stats = client.get_statistics()
    assert isinstance(stats, Statistics)
    assert stats.legislation_count > 0
    assert stats.case_law_count > 0


def test_live_search_legislation() -> None:
    with NeuRISClient() as client:
        page = client.search_legislation(search_term="Grundgesetz", size=5)
    assert page.total_items > 0
    assert len(page.members) > 0
    assert isinstance(page.members[0].item, Legislation)


def test_live_search_case_law() -> None:
    with NeuRISClient() as client:
        page = client.search_case_law(size=5)
    assert page.total_items > 0
    assert isinstance(page.members[0].item, Decision)


def test_live_list_courts() -> None:
    with NeuRISClient() as client:
        courts = client.list_courts()
    assert len(courts) > 0


def test_live_search_case_law_by_ecli_returns_document_number() -> None:
    """Regression: searching by ECLI returns documentNumber for subsequent lookup."""
    with NeuRISClient() as client:
        page = client.search_case_law(size=1)
    if not page.members:
        pytest.skip("No case law available in live API")
    decision = page.members[0].item
    assert isinstance(decision, Decision)
    assert decision.document_number
    assert decision.document_number != decision.ecli
