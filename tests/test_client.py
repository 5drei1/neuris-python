"""Unit tests for NeuRIS client (all offline via MockTransport)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from neuris.client import AsyncNeuRISClient, NeuRISClient
from neuris.exceptions import NeuRISTransportError
from neuris.models import (
    AdministrativeDirective,
    CollectionPage,
    Court,
    Decision,
    Legislation,
    Literature,
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


def test_search_legislation_sends_temporal_and_sort_params(
    mock_transport: MockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/legislation", legislation_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.search_legislation(
        temporal_coverage_from="2020-01-01",
        temporal_coverage_to="2023-12-31",
        sort="name",
    )
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("temporalCoverageFrom") == "2020-01-01"
    assert params.get("temporalCoverageTo") == "2023-12-31"
    assert params.get("sort") == "name"


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


def test_list_courts_empty_member_key_does_not_fall_through(
    mock_transport: MockTransport,
) -> None:
    """Regression: empty 'member' list must not fall through to 'hydra:member'."""
    mock_transport.register("/case-law/courts", {
        "member": [],
        "hydra:member": [{"label": "ShouldNotAppear", "location": "X", "type": "X"}],
    })
    client = NeuRISClient(transport=mock_transport)
    courts = client.list_courts()
    assert courts == []


def test_list_courts_falls_back_to_hydra_member_when_member_absent(
    mock_transport: MockTransport,
) -> None:
    mock_transport.register("/case-law/courts", {
        "hydra:member": [{"label": "Amtsgericht Berlin", "location": "Berlin", "type": "AG"}],
    })
    client = NeuRISClient(transport=mock_transport)
    courts = client.list_courts()
    assert len(courts) == 1
    assert courts[0].label == "Amtsgericht Berlin"


def test_search_case_law_sends_camel_case_params(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/case-law", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.search_case_law(
        type_group="Urteil",
        legal_effect="bindend",
        sort="decisionDate",
    )
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("typeGroup") == "Urteil"
    assert params.get("legalEffect") == "bindend"
    assert params.get("sort") == "decisionDate"


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
            {"item": {"@type": "Decision", "documentNumber": "D1", "type": "BGH", "documentType": "Urteil", "fileNumbers": []}, "textMatches": []},
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
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params["query"] == "Bundesrecht AND Verwaltung"
    assert "q" not in params


def test_lucene_search_with_scope(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/document/lucene-search/case-law", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.lucene_search("Bundesrecht", scope="case-law")
    assert page.total_items >= 0
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params["query"] == "Bundesrecht"
    assert "q" not in params


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
async def test_async_search_case_law_sends_camel_case_params(
    async_mock_transport: AsyncMockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/case-law", case_law_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.search_case_law(
        type_group="Urteil",
        legal_effect="bindend",
        sort="decisionDate",
    )
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params.get("typeGroup") == "Urteil"
    assert params.get("legalEffect") == "bindend"
    assert params.get("sort") == "decisionDate"


@pytest.mark.asyncio
async def test_async_search_legislation_sends_temporal_and_sort_params(
    async_mock_transport: AsyncMockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/legislation", legislation_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.search_legislation(
        temporal_coverage_from="2020-01-01",
        temporal_coverage_to="2023-12-31",
        sort="name",
    )
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params.get("temporalCoverageFrom") == "2020-01-01"
    assert params.get("temporalCoverageTo") == "2023-12-31"
    assert params.get("sort") == "name"


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
async def test_async_list_courts_empty_member_key_does_not_fall_through(
    async_mock_transport: AsyncMockTransport,
) -> None:
    """Regression: empty 'member' list must not fall through to 'hydra:member'."""
    async_mock_transport.register("/case-law/courts", {
        "member": [],
        "hydra:member": [{"label": "ShouldNotAppear", "location": "X", "type": "X"}],
    })
    client = AsyncNeuRISClient(transport=async_mock_transport)
    courts = await client.list_courts()
    assert courts == []


@pytest.mark.asyncio
async def test_async_list_courts_falls_back_to_hydra_member_when_member_absent(
    async_mock_transport: AsyncMockTransport,
) -> None:
    async_mock_transport.register("/case-law/courts", {
        "hydra:member": [{"label": "Amtsgericht Berlin", "location": "Berlin", "type": "AG"}],
    })
    client = AsyncNeuRISClient(transport=async_mock_transport)
    courts = await client.list_courts()
    assert len(courts) == 1
    assert courts[0].label == "Amtsgericht Berlin"


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


@pytest.mark.asyncio
async def test_async_get_legislation_by_eli(
    async_mock_transport: AsyncMockTransport,
    legislation_list_fixture: dict[str, Any],
) -> None:
    eli_raw = legislation_list_fixture["member"][0]["item"]
    async_mock_transport.register(
        "/legislation/eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1",
        eli_raw,
    )
    client = AsyncNeuRISClient(transport=async_mock_transport)
    law = await client.get_legislation_by_eli(
        "eli/bgbl-1/1949/grundgesetz/2023-12-19/1/deu/regelungstext-1"
    )
    assert isinstance(law, Legislation)
    assert law.abbreviation == "GG"


@pytest.mark.asyncio
async def test_async_search_administrative_directives(
    async_mock_transport: AsyncMockTransport,
) -> None:
    async_mock_transport.register("/administrative-directive", {
        "totalItems": 0,
        "member": [],
        "view": {"first": None, "last": None, "next": None, "previous": None},
    })
    client = AsyncNeuRISClient(transport=async_mock_transport)
    page = await client.search_administrative_directives()
    assert page.total_items == 0
    assert len(page.members) == 0


@pytest.mark.asyncio
async def test_async_search_documents_dispatches_types(
    async_mock_transport: AsyncMockTransport,
) -> None:
    data = {
        "totalItems": 2,
        "member": [
            {"item": {"@type": "Decision", "documentNumber": "D1", "type": "BGH", "documentType": "Urteil", "fileNumbers": []}, "textMatches": []},
            {"item": {"@type": "Legislation", "legislationIdentifier": "eli/x", "name": "X", "abbreviation": "X", "hasPart": []}, "textMatches": []},
        ],
        "view": {"first": None, "last": None, "next": None, "previous": None},
    }
    async_mock_transport.register("/document", data)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    page = await client.search_documents(search_term="test")
    assert isinstance(page.members[0].item, Decision)
    assert isinstance(page.members[1].item, Legislation)


@pytest.mark.asyncio
async def test_async_lucene_search(
    async_mock_transport: AsyncMockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/document/lucene-search", case_law_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    page = await client.lucene_search("Bundesrecht AND Verwaltung")
    assert page.total_items >= 0
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params["query"] == "Bundesrecht AND Verwaltung"
    assert "q" not in params


@pytest.mark.asyncio
async def test_async_lucene_search_with_scope(
    async_mock_transport: AsyncMockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/document/lucene-search/case-law", case_law_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    page = await client.lucene_search("Bundesrecht", scope="case-law")
    assert page.total_items >= 0
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params["query"] == "Bundesrecht"
    assert "q" not in params


@pytest.mark.asyncio
async def test_async_aclose(
    async_mock_transport: AsyncMockTransport,
) -> None:
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.aclose()


# ── NeuRISClient — Literature ─────────────────────────────────────────────────

def test_search_literature_returns_collection(
    mock_transport: MockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/literature", literature_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_literature()
    assert isinstance(page, CollectionPage)
    assert page.total_items == 2
    assert len(page.members) == 2


def test_search_literature_maps_item_to_literature(
    mock_transport: MockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/literature", literature_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_literature()
    item = page.members[0].item
    assert isinstance(item, Literature)
    assert item.document_number == "LIT-2023-001"
    assert item.year_of_publication == "2023"
    assert item.document_type == "Aufsatz"
    assert item.author == "Müller, Hans"
    assert item.collaborator == "Schmidt, Klaus"


def test_search_literature_no_next_page(
    mock_transport: MockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/literature", literature_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_literature()
    assert not page.has_next


def test_search_literature_text_matches(
    mock_transport: MockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/literature", literature_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_literature()
    result = page.members[0]
    assert len(result.text_matches) == 1
    assert result.text_matches[0].property == "author"


def test_search_literature_sends_camel_case_params(
    mock_transport: MockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/literature", literature_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.search_literature(
        author="Müller",
        year_of_publication="2023",
        document_type="Aufsatz",
        collaborator="Schmidt",
        search_term="test",
        size=5,
        page_index=1,
        sort="yearOfPublication",
    )
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("author") == "Müller"
    assert params.get("yearOfPublication") == "2023"
    assert params.get("documentType") == "Aufsatz"
    assert params.get("collaborator") == "Schmidt"
    assert params.get("searchTerm") == "test"
    assert params.get("size") == 5
    assert params.get("pageIndex") == 1
    assert params.get("sort") == "yearOfPublication"


def test_search_literature_document_number_param(
    mock_transport: MockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/literature", literature_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.search_literature(document_number="LIT-2023-001")
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("documentNumber") == "LIT-2023-001"


def test_get_literature_by_document_number(
    mock_transport: MockTransport,
    literature_detail_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/literature/LIT-2023-001", literature_detail_fixture)
    client = NeuRISClient(transport=mock_transport)
    lit = client.get_literature("LIT-2023-001")
    assert isinstance(lit, Literature)
    assert lit.document_number == "LIT-2023-001"
    assert lit.author == "Müller, Hans"


def test_search_literature_iter(
    mock_transport: MockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/literature", literature_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    results = list(client.search_literature_iter(search_term="Müller"))
    assert len(results) == 2
    assert all(isinstance(r.item, Literature) for r in results)


def test_search_literature_optional_fields_none(
    mock_transport: MockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    """Second fixture entry has collaborator=null — verify it maps to None."""
    mock_transport.register("/literature", literature_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    page = client.search_literature()
    item = page.members[1].item
    assert isinstance(item, Literature)
    assert item.collaborator is None


# ── AsyncNeuRISClient — Literature ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_async_search_literature(
    async_mock_transport: AsyncMockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/literature", literature_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    page = await client.search_literature()
    assert isinstance(page, CollectionPage)
    assert page.total_items == 2
    assert isinstance(page.members[0].item, Literature)


@pytest.mark.asyncio
async def test_async_search_literature_sends_camel_case_params(
    async_mock_transport: AsyncMockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/literature", literature_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.search_literature(
        author="Müller",
        year_of_publication="2023",
        document_type="Aufsatz",
        collaborator="Schmidt",
    )
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params.get("author") == "Müller"
    assert params.get("yearOfPublication") == "2023"
    assert params.get("documentType") == "Aufsatz"
    assert params.get("collaborator") == "Schmidt"


@pytest.mark.asyncio
async def test_async_get_literature(
    async_mock_transport: AsyncMockTransport,
    literature_detail_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/literature/LIT-2023-001", literature_detail_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    lit = await client.get_literature("LIT-2023-001")
    assert isinstance(lit, Literature)
    assert lit.document_number == "LIT-2023-001"
    assert lit.author == "Müller, Hans"


@pytest.mark.asyncio
async def test_async_search_literature_iter(
    async_mock_transport: AsyncMockTransport,
    literature_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/literature", literature_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    results = [r async for r in client.search_literature_iter()]
    assert len(results) == 2
    assert all(isinstance(r.item, Literature) for r in results)


# ── AIG-169: Missing API parameters ──────────────────────────────────────────

def test_list_courts_sends_prefix_param(
    mock_transport: MockTransport,
    courts_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/case-law/courts", courts_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.list_courts(prefix="BVerwG")
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("prefix") == "BVerwG"


def test_list_courts_no_prefix_sends_no_prefix_param(
    mock_transport: MockTransport,
    courts_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/case-law/courts", courts_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.list_courts()
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert "prefix" not in params


def test_search_administrative_directives_sends_date_and_document_number_params(
    mock_transport: MockTransport,
) -> None:
    mock_transport.register("/administrative-directive", {
        "totalItems": 0,
        "member": [],
        "view": {"first": None, "last": None, "next": None, "previous": None},
    })
    client = NeuRISClient(transport=mock_transport)
    client.search_administrative_directives(
        document_number="VwV-2023-001",
        date_from="2023-01-01",
        date_to="2023-12-31",
    )
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("documentNumber") == "VwV-2023-001"
    assert params.get("dateFrom") == "2023-01-01"
    assert params.get("dateTo") == "2023-12-31"


def test_search_documents_sends_sort_param(
    mock_transport: MockTransport,
) -> None:
    data = {
        "totalItems": 0,
        "member": [],
        "view": {"first": None, "last": None, "next": None, "previous": None},
    }
    mock_transport.register("/document", data)
    client = NeuRISClient(transport=mock_transport)
    client.search_documents(sort="publicationDate")
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("sort") == "publicationDate"


def test_lucene_search_sends_sort_param(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/document/lucene-search", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.lucene_search("Bundesrecht AND Verwaltung", sort="decisionDate")
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert params.get("sort") == "decisionDate"


def test_lucene_search_no_sort_omits_sort_param(
    mock_transport: MockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    mock_transport.register("/document/lucene-search", case_law_list_fixture)
    client = NeuRISClient(transport=mock_transport)
    client.lucene_search("Bundesrecht")
    _, params = mock_transport._calls[-1]
    assert params is not None
    assert "sort" not in params


@pytest.mark.asyncio
async def test_async_list_courts_sends_prefix_param(
    async_mock_transport: AsyncMockTransport,
    courts_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/case-law/courts", courts_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.list_courts(prefix="BGH")
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params.get("prefix") == "BGH"


@pytest.mark.asyncio
async def test_async_search_administrative_directives_sends_date_and_document_number_params(
    async_mock_transport: AsyncMockTransport,
) -> None:
    async_mock_transport.register("/administrative-directive", {
        "totalItems": 0,
        "member": [],
        "view": {"first": None, "last": None, "next": None, "previous": None},
    })
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.search_administrative_directives(
        document_number="VwV-2023-001",
        date_from="2023-01-01",
        date_to="2023-12-31",
    )
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params.get("documentNumber") == "VwV-2023-001"
    assert params.get("dateFrom") == "2023-01-01"
    assert params.get("dateTo") == "2023-12-31"


@pytest.mark.asyncio
async def test_async_search_documents_sends_sort_param(
    async_mock_transport: AsyncMockTransport,
) -> None:
    data = {
        "totalItems": 0,
        "member": [],
        "view": {"first": None, "last": None, "next": None, "previous": None},
    }
    async_mock_transport.register("/document", data)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.search_documents(sort="publicationDate")
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params.get("sort") == "publicationDate"


@pytest.mark.asyncio
async def test_async_lucene_search_sends_sort_param(
    async_mock_transport: AsyncMockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/document/lucene-search", case_law_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.lucene_search("Bundesrecht AND Verwaltung", sort="decisionDate")
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert params.get("sort") == "decisionDate"


@pytest.mark.asyncio
async def test_async_lucene_search_no_sort_omits_sort_param(
    async_mock_transport: AsyncMockTransport,
    case_law_list_fixture: dict[str, Any],
) -> None:
    async_mock_transport.register("/document/lucene-search", case_law_list_fixture)
    client = AsyncNeuRISClient(transport=async_mock_transport)
    await client.lucene_search("Bundesrecht")
    _, params = async_mock_transport._calls[-1]
    assert params is not None
    assert "sort" not in params
