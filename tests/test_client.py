"""Unit tests for NeuRIS client (all offline via MockTransport)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from neuris.client import AsyncNeuRISClient, NeuRISClient
from neuris.exceptions import NeuRISTransportError
from neuris.models import (
    CollectionPage,
    Court,
    Decision,
    Legislation,
    Statistics,
)
from neuris.transport import ProductionTransport

from .conftest import AsyncMockTransport, MockTransport

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ── NeuRISClient — Legislation ────────────────────────────────────────────────

def test_search_legislation_returns_collection(
    mock_transport: MockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/legislation", legislation_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_legislation(search_term="Grundgesetz")
    assert isinstance(page, CollectionPage)
    assert page.total_items == 2
    assert len(page.members) == 2


def test_search_legislation_maps_item_to_legislation(
    mock_transport: MockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/legislation", legislation_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_legislation()
    item = page.members[0].item
    assert isinstance(item, Legislation)
    assert item.name == "Grundgesetz"
    assert item.abbreviation == "GG"
    assert item.publication_date == date(1949, 5, 23)


def test_search_legislation_text_matches(
    mock_transport: MockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/legislation", legislation_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_legislation()
    result = page.members[0]
    assert len(result.text_matches) == 1
    assert result.text_matches[0].property == "name"


def test_search_legislation_sends_camel_case_params(
    mock_transport: MockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/legislation", legislation_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.search_legislation(search_term="test", size=5, page_index=1)
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("searchTerm") == "test"
    assert params.get("size") == 5
    assert params.get("pageIndex") == 1


def test_search_legislation_no_next_page(
    mock_transport: MockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/legislation", legislation_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_legislation()
    assert not page.has_next


def test_get_legislation_by_eli(
    mock_transport: MockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    eli_raw = legislation_list_fixture["member"][0]["item"]
    mock_transport.register(
        "/legislation/eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1",
        eli_raw,
    )
    client = NeuRISClient(transport=mock_transport)
    law = client.get_legislation_by_eli(
        "eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1"
    )
    assert isinstance(law, Legislation)
    assert law.abbreviation == "GG"


def test_search_legislation_iter_single_page(
    mock_transport: MockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/legislation", legislation_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    results = list(client.search_legislation_iter(search_term="GG"))
    assert len(results) == 2


def test_search_legislation_iter_multi_page() -> None:
    """Iterator must follow next-page links until exhausted."""
    page1 = {
        "totalItems": 2,
        "member": [
            {"item": {"@type": "Legislation", "legislationIdentifier": "eli/a", "name": "A", "abbreviation": "A", "hasPart": []}, "textMatches": []}
        ],
        "view": {
            "first": "?pageIndex=0",
            "last": "?pageIndex=1",
            "next": "https://testphase.rechtsinformationen.bund.de/v1/legislation?pageIndex=1&size=1",
            "previous": None,
        },
    }
    page2 = {
        "totalItems": 2,
        "member": [
            {"item": {"@type": "Legislation", "legislationIdentifier": "eli/b", "name": "B", "abbreviation": "B", "hasPart": []}, "textMatches": []}
        ],
        "view": {
            "first": "?pageIndex=0",
            "last": "?pageIndex=1",
            "next": None,
            "previous": "?pageIndex=0",
        },
    }
    transport = MockTransport()
    # Register both pages - second call will use pageIndex=1
    call_count = 0
    pages = [page1, page2]

    def patched_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        nonlocal call_count
        result = pages[call_count]
        call_count += 1
        return result

    transport.get = patched_get  # type: ignore[method-assign]
    client = NeuRISClient(transport=transport)
    results = list(client.search_legislation_iter(size=1))
    assert len(results) == 2
    assert call_count == 2


# ── NeuRISClient — Case Law ───────────────────────────────────────────────────

def test_search_case_law_returns_collection(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/case-law", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_case_law()
    assert isinstance(page, CollectionPage)
    assert page.total_items == 1


def test_search_case_law_maps_decision(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/case-law", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_case_law()
    decision = page.members[0].item
    assert isinstance(decision, Decision)
    assert decision.document_number == "BVERWG-123-456-2023"
    assert decision.ecli is not None
    assert decision.decision_date == date(2023, 6, 15)
    assert "1 BvR 123/23" in decision.file_numbers


def test_search_case_law_ecli_is_metadata_not_path(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    """Regression: search_case_law(ecli=...) returns documentNumber, not ECLI as path."""
    mock_transport.register("/case-law", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_case_law(ecli="ECLI:DE:BVerwG:2023:123456.U1BvR123.23.0")
    decision = page.members[0].item
    assert isinstance(decision, Decision)
    assert decision.document_number == "BVERWG-123-456-2023"
    # ECLI is metadata only
    assert decision.ecli == "ECLI:DE:BVerwG:2023:123456.U1BvR123.23.0"
    # Verify the API call used ecli param, NOT as URL path
    path, params = mock_transport._calls[-1]
    assert path == "/case-law"
    assert params is not None
    assert "ecli" in params


def test_get_case_law_by_document_number(
    mock_transport: MockTransport,
    case_law_detail_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/case-law/BVERWG-123-456-2023", case_law_detail_fixture)
    client = NeuRISClient(transport=mock_transport)
    decision = client.get_case_law("BVERWG-123-456-2023")
    assert isinstance(decision, Decision)
    assert decision.document_number == "BVERWG-123-456-2023"
    assert decision.court_label == "Bundesverwaltungsgericht"


def test_list_courts(
    mock_transport: MockTransport,
    courts_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/case-law/courts", courts_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    courts = client.list_courts()
    assert isinstance(courts, list)
    assert len(courts) == 3
    assert all(isinstance(c, Court) for c in courts)
    assert courts[0].label == "Bundesverwaltungsgericht"
    assert courts[0].location == "Leipzig"


def test_search_case_law_iter(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/case-law", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    results = list(client.search_case_law_iter())
    assert len(results) == 1


# ── NeuRISClient — Statistics ─────────────────────────────────────────────────

def test_get_statistics(
    mock_transport: MockTransport,
    statistics_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/statistics", statistics_fixture)
    client = NeuRISClient(transport=mock_transport)
    stats = client.get_statistics()
    assert isinstance(stats, Statistics)
    assert stats.legislation_count > 0
    assert stats.administrative_directive_count == 0


# ── NeuRISClient — Administrative Directives ──────────────────────────────────

def test_search_administrative_directives_empty(
    mock_transport: MockTransport,
) -> None:
    """VwV endpoint currently returns empty collection."""
    mock_transport.register("/administrative-directive", {
        "totalItems": 0,
        "member": [],
        "view": {"first": None, "last": None, "next": None, "previous": None},
    })
    client = NeuRISClient(transport=mock_transport)
    page = client.search_administrative_directives()
    assert page.total_items == 0
    assert len(page.members) == 0


# ── NeuRISClient — Document search ───────────────────────────────────────────

def test_search_documents_dispatches_types(
    mock_transport: MockTransport,
) -> None:
    data = {
        "totalItems": 2,
        "member": [
            {"item": {"@type": "Decision", "documentNumber": "D1", "courtType": "BGH", "documentType": "Urteil", "fileNumbers": []}, "textMatches": []},
            {"item": {"@type": "Legislation", "legislationIdentifier": "eli/x", "name": "X", "abbreviation": "X", "hasPart": []}, "textMatches": []},
        ],
        "view": {"first": None, "last": None, "next": None, "previous": None},
    }
    mock_transport.register("/document", data)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_documents(search_term="test")
    assert isinstance(page.members[0].item, Decision)
    assert isinstance(page.members[1].item, Legislation)


def test_lucene_search(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/document/lucene-search", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.lucene_search("Bundesrecht AND Verwaltung")
    assert page.total_items >= 0


def test_lucene_search_with_scope(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/document/lucene-search/case-law", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.lucene_search("Bundesrecht", scope="case-law")
    assert page.total_items >= 0


# ── NeuRISClient — Context manager ───────────────────────────────────────────

def test_client_context_manager(mock_transport: MockTransport) -> None:
    with NeuRISClient(transport=mock_transport) as client:
        assert client is not None


# ── ProductionTransport regression ───────────────────────────────────────────

def test_production_transport_regression() -> None:
    """ProductionTransport.get() must always raise NeuRISTransportError."""
    client = NeuRISClient(transport=ProductionTransport())
    with pytest.raises(NeuRISTransportError):
        client.get_statistics()


# ── AsyncNeuRISClient ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_async_search_legislation(
    async_mock_transport: AsyncMockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/legislation", legislation_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    page = await client.search_legislation(search_term="test")
    assert page.total_items == 2


@pytest.mark.asyncio
async def test_async_search_case_law(
    async_mock_transport: AsyncMockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/case-law", case_law_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    page = await client.search_case_law()
    assert len(page.members) == 1
    assert isinstance(page.members[0].item, Decision)


@pytest.mark.asyncio
async def test_async_get_case_law(
    async_mock_transport: AsyncMockTransport,
    case_law_detail_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/case-law/BVERWG-123-456-2023", case_law_detail_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    decision = await client.get_case_law("BVERWG-123-456-2023")
    assert decision.document_number == "BVERWG-123-456-2023"


@pytest.mark.asyncio
async def test_async_list_courts(
    async_mock_transport: AsyncMockTransport,
    courts_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/case-law/courts", courts_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    courts = await client.list_courts()
    assert len(courts) == 3


@pytest.mark.asyncio
async def test_async_get_statistics(
    async_mock_transport: AsyncMockTransport,
    statistics_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/statistics", statistics_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    stats = await client.get_statistics()
    assert isinstance(stats, Statistics)


@pytest.mark.asyncio
async def test_async_client_context_manager(
    async_mock_transport: AsyncMockTransport,
) -> None:
    async with AsyncNeuRISClient(transport=async_mock_transport) as client:
        assert client is not None


@pytest.mark.asyncio
async def test_async_search_legislation_iter(
    async_mock_transport: AsyncMockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/legislation", legislation_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    results = [r async for r in client.search_legislation_iter()]
    assert len(results) == 2


@pytest.mark.asyncio
async def test_async_search_case_law_iter(
    async_mock_transport: AsyncMockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/case-law", case_law_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    results = [r async for r in client.search_case_law_iter()]
    assert len(results) == 1
