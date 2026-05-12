"""neuris-python — Unofficial Python client for the NeuRIS API."""

from .client import AsyncNeuRISClient, NeuRISClient
from .eli import ELI, build_eli, eli_to_url_path, parse_eli
from .exceptions import (
    NeuRISAPIError,
    NeuRISConnectionError,
    NeuRISError,
    NeuRISNotFoundError,
    NeuRISRateLimitError,
    NeuRISServerError,
    NeuRISTimeoutError,
    NeuRISTransportError,
    NeuRISValidationError,
)
from .models import (
    AdministrativeDirective,
    CollectionPage,
    Court,
    Decision,
    Legislation,
    LegislationPart,
    Literature,
    PartialCollectionView,
    SearchResult,
    Statistics,
    TextMatch,
)
from .transport import (
    AsyncNeuRISTransport,
    AsyncTestphaseTransport,
    NeuRISTransport,
    ProductionTransport,
    TestphaseTransport,
)

__version__ = "0.1.0"
__all__ = [
    "AdministrativeDirective",
    "AsyncNeuRISClient",
    "AsyncNeuRISTransport",
    "AsyncTestphaseTransport",
    "CollectionPage",
    "Court",
    "Decision",
    "ELI",
    "Legislation",
    "LegislationPart",
    "Literature",
    "NeuRISAPIError",
    "NeuRISClient",
    "NeuRISConnectionError",
    "NeuRISError",
    "NeuRISNotFoundError",
    "NeuRISRateLimitError",
    "NeuRISServerError",
    "NeuRISTimeoutError",
    "NeuRISTransport",
    "NeuRISTransportError",
    "NeuRISValidationError",
    "PartialCollectionView",
    "ProductionTransport",
    "SearchResult",
    "Statistics",
    "TestphaseTransport",
    "TextMatch",
    "build_eli",
    "eli_to_url_path",
    "parse_eli",
]
