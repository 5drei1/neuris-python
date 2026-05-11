"""Pagination helpers: auto-paginating iterators for NeuRIS collection endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

if TYPE_CHECKING:
    from .models import CollectionPage, SearchResult


def _extract_page_index(next_url: str) -> int | None:
    """Extract pageIndex from a pagination URL."""
    try:
        parsed = urlparse(next_url)
        params = parse_qs(parsed.query)
        values = params.get("pageIndex", params.get("page", []))
        if values:
            return int(values[0])
    except (ValueError, AttributeError):
        pass
    return None


def iter_pages(
    fetch_page: Any,
    initial_kwargs: dict[str, Any],
) -> Iterator[SearchResult[Any]]:
    """Auto-paginate a collection endpoint.

    Args:
        fetch_page: Callable that accepts **kwargs and returns a CollectionPage.
        initial_kwargs: Initial keyword arguments for the first call.

    Yields:
        SearchResult items from every page.
    """
    kwargs = dict(initial_kwargs)
    while True:
        page: CollectionPage[Any] = fetch_page(**kwargs)
        yield from page.members
        if not page.has_next:
            break
        next_url = page.view.next
        if next_url is None:
            break
        next_idx = _extract_page_index(next_url)
        if next_idx is None:
            current = kwargs.get("page_index", 0)
            next_idx = int(current) + 1
        kwargs = {**kwargs, "page_index": next_idx}


async def async_iter_pages(
    fetch_page: Any,
    initial_kwargs: dict[str, Any],
) -> Any:
    """Async auto-paginating generator for collection endpoints."""
    kwargs = dict(initial_kwargs)
    while True:
        page: CollectionPage[Any] = await fetch_page(**kwargs)
        for item in page.members:
            yield item
        if not page.has_next:
            break
        next_url = page.view.next
        if next_url is None:
            break
        next_idx = _extract_page_index(next_url)
        if next_idx is None:
            current = kwargs.get("page_index", 0)
            next_idx = int(current) + 1
        kwargs = {**kwargs, "page_index": next_idx}
