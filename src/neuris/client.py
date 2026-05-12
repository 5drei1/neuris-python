from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

from .models import (
    AdministrativeDirective,
    CollectionPage,
    Court,
    Decision,
    Legislation,
    SearchResult,
    Statistics,
    _dispatch_item,
    _parse_collection_page,
)
from .pagination import async_iter_pages, iter_pages
from .transport import (
    AsyncNeuRISTransport,
    AsyncTestphaseTransport,
    NeuRISTransport,
    TestphaseTransport,
)


def _to_api_params(**kwargs: Any) -> dict[str, Any]:
    """Convert snake_case keyword args to camelCase API params."""
    mapping: dict[str, str] = {
        "search_term": "searchTerm",
        "eli": "eli",
        "temporal_coverage_from": "temporalCoverageFrom",
        "temporal_coverage_to": "temporalCoverageTo",
        "most_relevant_on": "mostRelevantOn",
        "date_from": "dateFrom",
        "date_to": "dateTo",
        "size": "size",
        "page_index": "pageIndex",
        "sort": "sort",
        "file_number": "fileNumber",
        "ecli": "ecli",
        "court": "court",
        "legal_effect": "legalEffect",
        "type": "type",
        "type_group": "typeGroup",
    }
    result: dict[str, Any] = {}
    for py_key, api_key in mapping.items():
        if py_key in kwargs and kwargs[py_key] is not None:
            result[api_key] = kwargs[py_key]
    return result


class NeuRISClient:
    """Synchronous NeuRIS API client."""

    def __init__(self, transport: NeuRISTransport | None = None) -> None:
        self._t = transport or TestphaseTransport()

    def __enter__(self) -> NeuRISClient:
        return self

    def __exit__(self, *_: object) -> None:
        self._t.close()

    def close(self) -> None:
        self._t.close()

    # ── Legislation ──────────────────────────────────────────────────────────

    def search_legislation(
        self,
        *,
        search_term: str | None = None,
        eli: str | None = None,
        temporal_coverage_from: str | None = None,
        temporal_coverage_to: str | None = None,
        most_relevant_on: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        size: int = 10,
        page_index: int = 0,
        sort: str | None = None,
    ) -> CollectionPage[SearchResult[Legislation]]:
        params = _to_api_params(
            search_term=search_term,
            eli=eli,
            temporal_coverage_from=temporal_coverage_from,
            temporal_coverage_to=temporal_coverage_to,
            most_relevant_on=most_relevant_on,
            date_from=date_from,
            date_to=date_to,
            size=size,
            page_index=page_index,
            sort=sort,
        )
        data = self._t.get("/legislation", params=params)
        return _parse_collection_page(data, Legislation.from_api)
    def search_legislation_iter(self, **kw: Any) -> Iterator[SearchResult[Legislation]]:
        """Auto-paginating iterator over all legislation search results."""
        return iter_pages(self.search_legislation, kw)

    def get_legislation_by_eli(self, eli: str) -> Legislation:
        path_part = eli.lstrip("/")
        if path_part.startswith("eli/"):
            path_part = path_part[4:]
        data = self._t.get(f"/legislation/eli/{path_part}")
        return Legislation.from_api(data)

    # ── Case Law ─────────────────────────────────────────────────────────────

    def search_case_law(
        self,
        *,
        search_term: str | None = None,
        file_number: str | None = None,
        ecli: str | None = None,
        court: str | None = None,
        legal_effect: str | None = None,
        type: str | None = None,
        type_group: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        size: int = 10,
        page_index: int = 0,
        sort: str | None = None,
    ) -> CollectionPage[SearchResult[Decision]]:
        params = _to_api_params(
            search_term=search_term,
            file_number=file_number,
            ecli=ecli,
            court=court,
            legal_effect=legal_effect,
            type=type,
            type_group=type_group,
            date_from=date_from,
            date_to=date_to,
            size=size,
            page_index=page_index,
            sort=sort,
        )
        data = self._t.get("/case-law", params=params)
        return _parse_collection_page(data, Decision.from_api)
    def search_case_law_iter(self, **kw: Any) -> Iterator[SearchResult[Decision]]:
        """Auto-paginating iterator over all case law search results."""
        return iter_pages(self.search_case_law, kw)

    def get_case_law(self, document_number: str) -> Decision:
        """Fetch a single decision by documentNumber (NOT ECLI)."""
        data = self._t.get(f"/case-law/{document_number}")
        return Decision.from_api(data)

    def list_courts(self) -> list[Court]:
        data = self._t.get("/case-law/courts")
        members: list[Any] = data["member"] if "member" in data else data.get("hydra:member", [])
        return [Court.from_api(c) for c in members]

    # ── Administrative Directives ─────────────────────────────────────────────

    def search_administrative_directives(
        self,
        *,
        search_term: str | None = None,
        size: int = 10,
        page_index: int = 0,
    ) -> CollectionPage[SearchResult[AdministrativeDirective]]:
        """Search administrative directives (currently returns empty collection)."""
        params = _to_api_params(
            search_term=search_term,
            size=size,
            page_index=page_index,
        )
        data = self._t.get("/administrative-directive", params=params)
        return _parse_collection_page(data, AdministrativeDirective.from_api)
    # ── Combined / Lucene ─────────────────────────────────────────────────────

    def search_documents(
        self,
        *,
        search_term: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        most_relevant_on: str | None = None,
        size: int = 10,
        page_index: int = 0,
    ) -> CollectionPage[Any]:
        """Search across all document types."""
        params = _to_api_params(
            search_term=search_term,
            date_from=date_from,
            date_to=date_to,
            most_relevant_on=most_relevant_on,
            size=size,
            page_index=page_index,
        )
        data = self._t.get("/document", params=params)
        return _parse_collection_page(data, _dispatch_item)

    def lucene_search(
        self,
        query: str,
        *,
        scope: str = "all",
        size: int = 10,
        page_index: int = 0,
    ) -> CollectionPage[Any]:
        """Lucene query search across documents."""
        path = "/document/lucene-search" if scope == "all" else f"/document/lucene-search/{scope}"
        params: dict[str, Any] = {"q": query, "size": size, "pageIndex": page_index}
        data = self._t.get(path, params=params)
        return _parse_collection_page(data, _dispatch_item)

    # ── Meta ──────────────────────────────────────────────────────────────────

    def get_statistics(self) -> Statistics:
        data = self._t.get("/statistics")
        return Statistics.from_api(data)


class AsyncNeuRISClient:
    """Asynchronous NeuRIS API client."""

    def __init__(self, transport: AsyncNeuRISTransport | None = None) -> None:
        self._t = transport or AsyncTestphaseTransport()

    async def __aenter__(self) -> AsyncNeuRISClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._t.aclose()

    async def aclose(self) -> None:
        await self._t.aclose()

    # ── Legislation ──────────────────────────────────────────────────────────

    async def search_legislation(
        self,
        *,
        search_term: str | None = None,
        eli: str | None = None,
        temporal_coverage_from: str | None = None,
        temporal_coverage_to: str | None = None,
        most_relevant_on: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        size: int = 10,
        page_index: int = 0,
        sort: str | None = None,
    ) -> CollectionPage[SearchResult[Legislation]]:
        params = _to_api_params(
            search_term=search_term,
            eli=eli,
            temporal_coverage_from=temporal_coverage_from,
            temporal_coverage_to=temporal_coverage_to,
            most_relevant_on=most_relevant_on,
            date_from=date_from,
            date_to=date_to,
            size=size,
            page_index=page_index,
            sort=sort,
        )
        data = await self._t.get("/legislation", params=params)
        return _parse_collection_page(data, Legislation.from_api)
    async def search_legislation_iter(self, **kw: Any) -> AsyncIterator[SearchResult[Legislation]]:
        """Async auto-paginating iterator over legislation search results."""
        async for item in async_iter_pages(self.search_legislation, kw):
            yield item

    async def get_legislation_by_eli(self, eli: str) -> Legislation:
        path_part = eli.lstrip("/")
        if path_part.startswith("eli/"):
            path_part = path_part[4:]
        data = await self._t.get(f"/legislation/eli/{path_part}")
        return Legislation.from_api(data)

    # ── Case Law ─────────────────────────────────────────────────────────────

    async def search_case_law(
        self,
        *,
        search_term: str | None = None,
        file_number: str | None = None,
        ecli: str | None = None,
        court: str | None = None,
        legal_effect: str | None = None,
        type: str | None = None,
        type_group: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        size: int = 10,
        page_index: int = 0,
        sort: str | None = None,
    ) -> CollectionPage[SearchResult[Decision]]:
        params = _to_api_params(
            search_term=search_term,
            file_number=file_number,
            ecli=ecli,
            court=court,
            legal_effect=legal_effect,
            type=type,
            type_group=type_group,
            date_from=date_from,
            date_to=date_to,
            size=size,
            page_index=page_index,
            sort=sort,
        )
        data = await self._t.get("/case-law", params=params)
        return _parse_collection_page(data, Decision.from_api)
    async def search_case_law_iter(self, **kw: Any) -> AsyncIterator[SearchResult[Decision]]:
        """Async auto-paginating iterator over case law search results."""
        async for item in async_iter_pages(self.search_case_law, kw):
            yield item

    async def get_case_law(self, document_number: str) -> Decision:
        """Fetch a single decision by documentNumber (NOT ECLI)."""
        data = await self._t.get(f"/case-law/{document_number}")
        return Decision.from_api(data)

    async def list_courts(self) -> list[Court]:
        data = await self._t.get("/case-law/courts")
        members: list[Any] = data["member"] if "member" in data else data.get("hydra:member", [])
        return [Court.from_api(c) for c in members]

    # ── Administrative Directives ─────────────────────────────────────────────

    async def search_administrative_directives(
        self,
        *,
        search_term: str | None = None,
        size: int = 10,
        page_index: int = 0,
    ) -> CollectionPage[SearchResult[AdministrativeDirective]]:
        """Search administrative directives (currently returns empty collection)."""
        params = _to_api_params(
            search_term=search_term,
            size=size,
            page_index=page_index,
        )
        data = await self._t.get("/administrative-directive", params=params)
        return _parse_collection_page(data, AdministrativeDirective.from_api)
    # ── Combined / Lucene ─────────────────────────────────────────────────────

    async def search_documents(
        self,
        *,
        search_term: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        most_relevant_on: str | None = None,
        size: int = 10,
        page_index: int = 0,
    ) -> CollectionPage[Any]:
        params = _to_api_params(
            search_term=search_term,
            date_from=date_from,
            date_to=date_to,
            most_relevant_on=most_relevant_on,
            size=size,
            page_index=page_index,
        )
        data = await self._t.get("/document", params=params)
        return _parse_collection_page(data, _dispatch_item)

    async def lucene_search(
        self,
        query: str,
        *,
        scope: str = "all",
        size: int = 10,
        page_index: int = 0,
    ) -> CollectionPage[Any]:
        path = "/document/lucene-search" if scope == "all" else f"/document/lucene-search/{scope}"
        params: dict[str, Any] = {"q": query, "size": size, "pageIndex": page_index}
        data = await self._t.get(path, params=params)
        return _parse_collection_page(data, _dispatch_item)

    # ── Meta ──────────────────────────────────────────────────────────────────

    async def get_statistics(self) -> Statistics:
        data = await self._t.get("/statistics")
        return Statistics.from_api(data)
