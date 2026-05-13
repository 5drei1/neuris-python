# neuris-python

Unofficial Python client for the NeuRIS API (`testphase.rechtsinformationen.bund.de`) - Germany's national legal information system in test phase.

> Status: alpha (`0.x`). API behavior may change without notice.

## Contents

- [Project Goal](#project-goal)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Client API](#client-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Pagination](#pagination)
- [ELI Helpers](#eli-helpers)
- [Known API Quirks](#known-api-quirks)
- [Development](#development)
- [License](#license)

## Project Goal

`neuris-python` wraps the NeuRIS REST endpoints with:

- typed sync and async clients
- dataclass-like Python models for API resources
- automatic pagination iterators
- explicit exception mapping by HTTP status
- retry logic for transient server/rate-limit failures

## Installation

Requirements:

- Python `>=3.11`

Install from PyPI:

```bash
pip install neuris-python
```

With `uv`:

```bash
uv add neuris-python
```

## Quick Start

### Sync client

```python
from neuris import NeuRISClient

with NeuRISClient() as client:
    page = client.search_legislation(search_term="Grundgesetz", size=5)
    print(page.total_items)

    for result in page.members:
        law = result.item
        print(law.abbreviation, law.name)
```

### Async client

```python
import asyncio
from neuris import AsyncNeuRISClient

async def main() -> None:
    async with AsyncNeuRISClient() as client:
        page = await client.search_case_law(search_term="Revision", size=3)
        for result in page.members:
            print(result.item.document_number)

asyncio.run(main())
```

### Case law detail flow (ECLI -> document number -> detail)

```python
from neuris import NeuRISClient

with NeuRISClient() as client:
    hits = client.search_case_law(ecli="ECLI:DE:BGH:2023:...")
    if hits.members:
        doc_number = hits.members[0].item.document_number
        decision = client.get_case_law(doc_number)
        print(decision.headline)
```

## Client API

`AsyncNeuRISClient` mirrors `NeuRISClient` 1:1 as `async` methods.

### Legislation

- `search_legislation(...)`
- `search_legislation_iter(...)`
- `get_legislation_by_eli(eli)`
- `get_legislation_xml(eli, subtype)`
- `get_legislation_html(eli, subtype)`
- `get_legislation_zip(eli, point_in_time_manifestation)`
- `get_legislation_article_html(eli, article_eid)`

### Case law

- `search_case_law(...)`
- `search_case_law_iter(...)`
- `get_case_law(document_number)`
- `get_case_law_xml(document_number)`
- `get_case_law_html(document_number)`
- `get_case_law_zip(document_number)`
- `list_courts(prefix=None)`

### Administrative directives

- `search_administrative_directives(...)`
- `get_administrative_directive(document_number)`
- `get_administrative_directive_xml(document_number)`
- `get_administrative_directive_html(document_number)`

### Literature

- `search_literature(...)`
- `search_literature_iter(...)`
- `get_literature(document_number)`
- `get_literature_xml(document_number)`
- `get_literature_html(document_number)`

### Cross-resource and metadata

- `search_documents(...)` for mixed resource types
- `lucene_search(query, scope="all", ...)`
- `get_statistics()`

### Search parameter naming

Public client parameters use Python `snake_case`, internally mapped to NeuRIS API `camelCase` query params.

Examples:

- `search_term` -> `searchTerm`
- `page_index` -> `pageIndex`
- `date_from` -> `dateFrom`
- `temporal_coverage_from` -> `temporalCoverageFrom`

## Data Models

Main exported models:

- `Legislation`, `LegislationPart`
- `Decision`
- `AdministrativeDirective`
- `Literature`
- `Court`
- `Statistics`
- `SearchResult[T]`
- `CollectionPage[T]`
- `PartialCollectionView`
- `TextMatch`

For mixed `/document` responses, model dispatch is based on the NeuRIS `@type` discriminator.

## Error Handling

Transport maps HTTP/network failures to explicit exceptions:

- `NeuRISForbiddenError` (`403`)
- `NeuRISNotFoundError` (`404`)
- `NeuRISValidationError` (`422`)
- `NeuRISRateLimitError` (`429`)
- `NeuRISServiceUnavailableError` (`503`)
- `NeuRISServerError` (`5xx`)
- `NeuRISConnectionError` (connectivity)
- `NeuRISTimeoutError` (timeouts)
- `NeuRISTransportError` (non-operational transport, e.g. production stub)

Retry behavior (`TestphaseTransport`, `AsyncTestphaseTransport`):

- retries up to 3 attempts
- exponential backoff (1s to 10s)
- retries on `NeuRISServerError` and `NeuRISRateLimitError`

Example:

```python
from neuris import NeuRISClient, NeuRISAPIError

with NeuRISClient() as client:
    try:
        client.get_case_law("invalid-doc-number")
    except NeuRISAPIError as exc:
        print(exc.status_code, exc.url)
        print(exc.body)
```

## Pagination

Search methods return `CollectionPage[T]` and support explicit page access:

```python
with NeuRISClient() as client:
    page0 = client.search_legislation(search_term="BGB", size=20, page_index=0)
    page1 = client.search_legislation(search_term="BGB", size=20, page_index=1)
```

For convenience, use iterators that fetch all pages automatically:

```python
with NeuRISClient() as client:
    for result in client.search_legislation_iter(search_term="BGB", size=100):
        print(result.item.name)
```

Async variant:

```python
async with AsyncNeuRISClient() as client:
    async for result in client.search_literature_iter(search_term="Kommentar"):
        print(result.item.document_number)
```

## ELI Helpers

Utility functions exported from `neuris.eli`:

- `parse_eli(...)`
- `build_eli(...)`
- `eli_to_url_path(...)`
- `ELI` dataclass

`get_legislation_by_eli(...)` accepts either full ELI strings or normalized path forms and normalizes internally.

## Known API Quirks

- ECLI is metadata, not a detail endpoint path. For details, use `documentNumber`.
- Some dataset groups in test phase may return empty collections.
- `ProductionTransport` is intentionally a stub until the production API is live.
- Historical versions / full production parity are pending by NeuRIS rollout timeline.

## Development

Clone and install dev dependencies:

```bash
git clone https://github.com/5drei1/neuris-python
cd neuris-python
uv sync --dev
```

Quality checks:

```bash
uv run ruff check .
uv run mypy
uv run pytest
```

Run live API tests explicitly:

```bash
NEURIS_LIVE=1 uv run pytest -m live
```

## License

MIT - pj0tr
