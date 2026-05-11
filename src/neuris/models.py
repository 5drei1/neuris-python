from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Generic, TypeVar

T = TypeVar("T")


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


@dataclass(slots=True, frozen=True)
class LegislationPart:
    eli: str
    legislation_work_identifier: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> LegislationPart:
        return cls(
            eli=data["eli"],
            legislation_work_identifier=data.get("legislationWorkIdentifier"),
        )


@dataclass(slots=True, frozen=True)
class Legislation:
    legislation_identifier: str
    name: str
    abbreviation: str
    has_part: tuple[LegislationPart, ...]
    official_long_title: str | None
    publication_date: date | None
    version_date: date | None
    eli_work: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Legislation:
        parts = tuple(
            LegislationPart.from_api(p) for p in data.get("hasPart", [])
        )
        return cls(
            legislation_identifier=data["legislationIdentifier"],
            name=data.get("name", ""),
            abbreviation=data.get("abbreviation", ""),
            has_part=parts,
            official_long_title=data.get("officialLongTitle"),
            publication_date=_parse_date(data.get("publicationDate")),
            version_date=_parse_date(data.get("versionDate")),
            eli_work=data.get("eliWork"),
        )


@dataclass(slots=True, frozen=True)
class Decision:
    document_number: str
    ecli: str | None
    guiding_principle: str | None
    tenor: str | None
    decision_date: date | None
    file_numbers: tuple[str, ...]
    court_type: str
    court_location: str | None
    court_label: str | None
    legal_effect: str | None
    document_type: str
    year_of_decision: str | None
    headline: str | None
    documentation_office: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Decision:
        return cls(
            document_number=data["documentNumber"],
            ecli=data.get("ecli"),
            guiding_principle=data.get("guidingPrinciple"),
            tenor=data.get("tenor"),
            decision_date=_parse_date(data.get("decisionDate")),
            file_numbers=tuple(data.get("fileNumbers", [])),
            court_type=data.get("courtType", ""),
            court_location=data.get("courtLocation"),
            court_label=data.get("courtLabel"),
            legal_effect=data.get("legalEffect"),
            document_type=data.get("documentType", ""),
            year_of_decision=data.get("yearOfDecision"),
            headline=data.get("headline"),
            documentation_office=data.get("documentationOffice"),
        )


@dataclass(slots=True, frozen=True)
class Court:
    type: str
    location: str | None
    label: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Court:
        return cls(
            type=data.get("type", ""),
            location=data.get("location"),
            label=data.get("label", ""),
        )


@dataclass(slots=True, frozen=True)
class Statistics:
    legislation_count: int
    case_law_count: int
    administrative_directive_count: int
    literature_count: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Statistics:
        return cls(
            legislation_count=data.get("legislationCount", 0),
            case_law_count=data.get("caseLawCount", 0),
            administrative_directive_count=data.get("administrativeDirectiveCount", 0),
            literature_count=data.get("literatureCount", 0),
        )


@dataclass(slots=True, frozen=True)
class TextMatch:
    property: str
    text: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> TextMatch:
        return cls(
            property=data.get("property", ""),
            text=data.get("text", ""),
        )


@dataclass(slots=True, frozen=True)
class SearchResult(Generic[T]):
    item: T
    text_matches: tuple[TextMatch, ...]


@dataclass(slots=True, frozen=True)
class PartialCollectionView:
    first: str | None
    last: str | None
    next: str | None
    previous: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any] | None) -> PartialCollectionView:
        if data is None:
            return cls(first=None, last=None, next=None, previous=None)
        return cls(
            first=data.get("first"),
            last=data.get("last"),
            next=data.get("next"),
            previous=data.get("previous"),
        )


@dataclass(slots=True, frozen=True)
class CollectionPage(Generic[T]):
    total_items: int
    members: tuple[Any, ...]
    view: PartialCollectionView

    @property
    def has_next(self) -> bool:
        return self.view.next is not None


@dataclass(slots=True, frozen=True)
class AdministrativeDirective:
    """Administrative directive (Verwaltungsvorschrift). Currently no documents in the API."""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AdministrativeDirective:
        return cls()


@dataclass(slots=True, frozen=True)
class Literature:
    """Literature entry. Currently no documents in the API."""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Literature:
        return cls()


def _dispatch_item(data: dict[str, Any]) -> Any:
    """Map API @type discriminator to the appropriate model class."""
    item_type = data.get("@type", "")
    if item_type == "Decision":
        return Decision.from_api(data)
    if item_type == "Legislation":
        return Legislation.from_api(data)
    if item_type == "AdministrativeDirective":
        return AdministrativeDirective.from_api(data)
    if item_type == "Literature":
        return Literature.from_api(data)
    return data


def _parse_collection_page(
    data: dict[str, Any],
    item_factory: Any,
) -> CollectionPage[Any]:
    """Parse a hydra:Collection response into a CollectionPage."""
    raw_members = data.get("member", data.get("hydra:member", []))
    members: list[SearchResult[Any]] = []
    for entry in raw_members:
        item_data = entry.get("item", entry)
        item = item_factory(item_data)
        text_matches = tuple(
            TextMatch.from_api(m) for m in entry.get("textMatches", [])
        )
        members.append(SearchResult(item=item, text_matches=text_matches))

    view_data = data.get("view", data.get("hydra:view"))
    view = PartialCollectionView.from_api(view_data)

    return CollectionPage(
        total_items=data.get("totalItems", data.get("hydra:totalItems", 0)),
        members=tuple(members),
        view=view,
    )
