# AGENT.md — neuris-python

Quick-reference for AI agents working with this repository.

## Critical API facts

### Endpoints that DO NOT exist
- `/decisions` — does not exist; use `/case-law`
- `/search` — does not exist; use `/legislation`, `/case-law`, or `/document`

### Correct endpoints
| Resource | Endpoint |
|---|---|
| Legislation search | `GET /v1/legislation` |
| Legislation by ELI | `GET /v1/legislation/eli/{...}` |
| Case law search | `GET /v1/case-law` |
| Case law detail | `GET /v1/case-law/{documentNumber}` |
| Courts list | `GET /v1/case-law/courts` |
| Document search | `GET /v1/document` |
| Lucene search | `GET /v1/document/lucene-search[/{type}]` |
| Administrative directives | `GET /v1/administrative-directive` |
| Statistics | `GET /v1/statistics` |

### ECLI is NOT a URL path
ECLI is metadata only. To look up a decision:
```python
# WRONG — will return 404
client.get_case_law("ECLI:DE:BGH:2023:...")

# CORRECT
page = client.search_case_law(ecli="ECLI:DE:BGH:2023:...")
doc_number = page.members[0].item.document_number
decision = client.get_case_law(doc_number)
```

### @type discriminator
The API uses `@type == "Decision"` — NOT `"CaseLaw"`.
```python
# _dispatch_item() in models.py:
if item_type == "Decision":      # correct
    return Decision.from_api(data)
# NOT:
if item_type == "CaseLaw":       # wrong — this type does not appear in the API
```

### Rate limiting

- **Limit:** 600 requests per minute (per client/IP).
- **Status code:** The API returns **503 Service Unavailable** when the limit is exceeded — **not** the conventional 429.
- **Transport behaviour:** `TestphaseTransport` retries 503 up to 3 times (same as other 5xx). After retry exhaustion it raises `NeuRISServiceUnavailableError`, a subclass of `NeuRISServerError`.
- **Distinguishing rate-limit 503 from genuine outage:** inspect `exc.likely_rate_limited` (checks response body for rate-limit keywords) or read `exc.body` directly.

```python
from neuris.exceptions import NeuRISServiceUnavailableError

try:
    client.search_legislation(keyword="Grundgesetz")
except NeuRISServiceUnavailableError as exc:
    if exc.likely_rate_limited:
        # back off and retry after > 60 s
        ...
    else:
        # genuine server outage
        raise
```

### Known API quirks
| # | Issue | Workaround |
|---|---|---|
| 1 | `dateFrom/dateTo` excludes Änderungsgesetze | Use `temporalCoverageFrom/To` instead |
| 2 | ECLI is not a URL path → 404 if used directly | search → documentNumber → get_case_law() |
| 3 | Historical versions not available | Available only after final portal launch (H2 2026) |
| 4 | VwV + Literature endpoints currently return empty collections | Expected; test for empty, not error |
| 5 | Trial API — breaking changes possible | Pinned `semver 0.x`; run live tests before release |
| 6 | Production API not yet live | `ProductionTransport` is a stub that raises `NeuRISTransportError` |
| 7 | Rate-limit returns 503, not 429 | Catch `NeuRISServiceUnavailableError`; check `.likely_rate_limited` |

## Scope
This repo is a pure API client library.

**Not in scope:**
- LanceDB, embeddings, vector stores, or RAG code
- Database integrations
- Web scraping

## Transport configuration
```python
from neuris import NeuRISClient
from neuris.transport import TestphaseTransport, ProductionTransport

# Default: TestphaseTransport
client = NeuRISClient()

# Custom transport
client = NeuRISClient(transport=TestphaseTransport(timeout=60.0))

# Production stub (not yet live)
client = NeuRISClient(transport=ProductionTransport())
# raises NeuRISTransportError on .get()
```

## Common commands
```bash
uv sync                      # install all deps
pytest                       # run offline tests
NEURIS_LIVE=1 pytest -m live # run live integration tests
ruff check .                 # lint
mypy src/                    # type check
```

## Architecture
```
src/neuris/
├── __init__.py    — public API surface
├── client.py      — NeuRISClient + AsyncNeuRISClient
├── transport.py   — transport ABC + TestphaseTransport + ProductionTransport stub
├── models.py      — dataclasses (slots=True, frozen=True) + _dispatch_item()
├── exceptions.py  — exception hierarchy
├── eli.py         — ELI parse/build helpers
└── pagination.py  — auto-paginating iterators
```
