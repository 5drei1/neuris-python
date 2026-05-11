# neuris-python

Unofficial Python client for the [NeuRIS API](https://testphase.rechtsinformationen.bund.de/v1) — Germany's national legal information system (testphase).

> **Note:** This is an unofficial client for a trial API. The API may change without notice.

## Installation

```bash
pip install neuris-python
# or with uv:
uv add neuris-python
```

## Quick Start

### Search legislation

```python
from neuris import NeuRISClient

with NeuRISClient() as client:
    page = client.search_legislation(search_term="Grundgesetz", size=5)
    print(f"Found {page.total_items} laws")
    for result in page.members:
        law = result.item
        print(f"{law.abbreviation}: {law.name}")
```

### Fetch a court decision

```python
from neuris import NeuRISClient

with NeuRISClient() as client:
    # Search by ECLI — returns documentNumber for lookup
    page = client.search_case_law(ecli="ECLI:DE:BGH:2023:...")
    if page.members:
        doc_number = page.members[0].item.document_number
        decision = client.get_case_law(doc_number)
        print(f"{decision.document_type}: {decision.headline}")
        print(f"Date: {decision.decision_date}")
```

### Paginate through all results

```python
from neuris import NeuRISClient

with NeuRISClient() as client:
    for result in client.search_legislation_iter(search_term="Bundesrecht"):
        print(result.item.abbreviation)
```

### Async client

```python
import asyncio
from neuris import AsyncNeuRISClient

async def main():
    async with AsyncNeuRISClient() as client:
        page = await client.search_legislation(search_term="BGB")
        async for result in client.search_legislation_iter(search_term="BGB"):
            print(result.item.name)

asyncio.run(main())
```

## API Methods

### NeuRISClient

| Method | Description |
|--------|-------------|
| `search_legislation(**kw)` | Search legislation by term, ELI, date range |
| `search_legislation_iter(**kw)` | Auto-paginating iterator |
| `get_legislation_by_eli(eli)` | Fetch legislation by ELI path |
| `search_case_law(**kw)` | Search case law by term, file number, ECLI, court |
| `search_case_law_iter(**kw)` | Auto-paginating iterator |
| `get_case_law(document_number)` | Fetch decision by documentNumber (NOT ECLI) |
| `list_courts()` | List all available courts |
| `search_administrative_directives(**kw)` | Search VwV (currently empty) |
| `search_documents(**kw)` | Cross-type document search |
| `lucene_search(query, *, scope)` | Lucene query syntax |
| `get_statistics()` | Document count statistics |

`AsyncNeuRISClient` mirrors all methods as `async def`.

## Known Issues

| # | Issue | Workaround |
|---|---|---|
| 1 | `dateFrom/dateTo` excludes amending laws | Use `temporal_coverage_from/to` instead |
| 2 | ECLI is metadata — use `documentNumber` for lookups | `search_case_law(ecli=...)` → `.document_number` → `get_case_law()` |
| 3 | Historical law versions not available | Planned for H2 2026 final portal |
| 4 | Administrative directives + literature empty | API returns empty collections |
| 5 | Trial API — breaking changes possible | Pinned to `semver 0.x` |

## License

MIT © pj0tr
