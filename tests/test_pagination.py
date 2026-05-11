"""Unit tests for pagination helpers."""

from __future__ import annotations

from typing import Any

import pytest

from neuris.models import CollectionPage, PartialCollectionView, SearchResult
from neuris.pagination import _extract_page_index, async_iter_pages, iter_pages

# ── _extract_page_index ───────────────────────────────────────────────────────

def test_extract_page_index_present() -> None:
    url = "https://testphase.rechtsinformationen.bund.de/v1/legislation?pageIndex=3&size=10"
    assert _extract_page_index(url) == 3


def test_extract_page_index_page_param() -> None:
    url = "https://example.com/api?page=5&size=10"
    assert _extract_page_index(url) == 5


def test_extract_page_index_missing() -> None:
    assert _extract_page_index("https://example.com/api?size=10") is None


def test_extract_page_index_invalid() -> None:
    assert _extract_page_index("not-a-url") is None


# ── iter_pages ────────────────────────────────────────────────────────────────

def _make_page(
    items: list[str],
    next_url: str | None = None,
    total: int | None = None,
) -> CollectionPage[str]:
    view = PartialCollectionView(first=None, last=None, next=next_url, previous=None)
    members = tuple(SearchResult(item=i, text_matches=()) for i in items)
    return CollectionPage(
        total_items=total if total is not None else len(items),
        members=members,
        view=view,
    )


def test_iter_pages_single_page() -> None:
    calls = 0

    def fetch(**kw: Any) -> CollectionPage[str]:
        nonlocal calls
        calls += 1
        return _make_page(["a", "b", "c"])

    results = list(iter_pages(fetch, {}))
    assert results == [SearchResult(item="a", text_matches=()), SearchResult(item="b", text_matches=()), SearchResult(item="c", text_matches=())]
    assert calls == 1


def test_iter_pages_two_pages() -> None:
    call_count = 0
    pages = [
        _make_page(["a", "b"], next_url="?pageIndex=1"),
        _make_page(["c"], next_url=None),
    ]

    def fetch(**kw: Any) -> CollectionPage[str]:
        nonlocal call_count
        page = pages[call_count]
        call_count += 1
        return page

    results = list(iter_pages(fetch, {}))
    assert len(results) == 3
    assert call_count == 2


def test_iter_pages_respects_page_index_in_next_url() -> None:
    call_kwargs: list[dict[str, Any]] = []
    pages = [
        _make_page(["a"], next_url="?pageIndex=2"),
        _make_page(["b"]),
    ]
    call_count = 0

    def fetch(**kw: Any) -> CollectionPage[str]:
        nonlocal call_count
        call_kwargs.append(dict(kw))
        page = pages[call_count]
        call_count += 1
        return page

    list(iter_pages(fetch, {"size": 1}))
    assert call_kwargs[1].get("page_index") == 2


def test_iter_pages_increments_page_index_when_no_url_hint() -> None:
    call_kwargs: list[dict[str, Any]] = []
    call_count = 0

    def fetch(**kw: Any) -> CollectionPage[str]:
        nonlocal call_count
        call_kwargs.append(dict(kw))
        # Second call gets no next
        if call_count == 0:
            call_count += 1
            return _make_page(["a"], next_url="relative-no-index")
        return _make_page(["b"])

    list(iter_pages(fetch, {"page_index": 0}))
    assert call_kwargs[1]["page_index"] == 1


# ── async_iter_pages ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_async_iter_pages_single_page() -> None:
    async def fetch(**kw: Any) -> CollectionPage[str]:
        return _make_page(["x", "y"])

    results = [r async for r in async_iter_pages(fetch, {})]
    assert len(results) == 2


@pytest.mark.asyncio
async def test_async_iter_pages_two_pages() -> None:
    call_count = 0
    pages = [
        _make_page(["a", "b"], next_url="?pageIndex=1"),
        _make_page(["c"]),
    ]

    async def fetch(**kw: Any) -> CollectionPage[str]:
        nonlocal call_count
        page = pages[call_count]
        call_count += 1
        return page

    results = [r async for r in async_iter_pages(fetch, {})]
    assert len(results) == 3
