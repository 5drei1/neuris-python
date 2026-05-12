"""Unit tests for NeuRIS models."""

from __future__ import annotations

from datetime import date

import pytest

from neuris.models import (
    AdministrativeDirective,
    CollectionPage,
    Court,
    Decision,
    Legislation,
    Literature,
    PartialCollectionView,
    Statistics,
    TextMatch,
    _dispatch_item,
    _parse_date,
)

# ── _parse_date ───────────────────────────────────────────────────────────────

def test_parse_date_iso_string() -> None:
    assert _parse_date("2023-06-15") == date(2023, 6, 15)


def test_parse_date_with_time() -> None:
    assert _parse_date("2023-06-15T10:30:00") == date(2023, 6, 15)


def test_parse_date_none() -> None:
    assert _parse_date(None) is None


def test_parse_date_invalid() -> None:
    assert _parse_date("not-a-date") is None


# ── Legislation ───────────────────────────────────────────────────────────────

def test_legislation_from_api_full() -> None:
    data = {
        "@type": "Legislation",
        "legislationIdentifier": "eli/bgbl-1/1949/gg/2023-12-19/1/deu/regelungstext-1",
        "name": "Grundgesetz",
        "abbreviation": "GG",
        "officialLongTitle": "Grundgesetz für die Bundesrepublik Deutschland",
        "publicationDate": "1949-05-23",
        "versionDate": "2023-12-19",
        "eliWork": "eli/bgbl-1/1949/gg",
        "hasPart": [
            {"eli": "eli/bgbl-1/1949/gg/art-1", "legislationWorkIdentifier": "eli/bgbl-1/1949/gg/art-1"}
        ],
    }
    law = Legislation.from_api(data)
    assert law.name == "Grundgesetz"
    assert law.abbreviation == "GG"
    assert law.publication_date == date(1949, 5, 23)
    assert law.version_date == date(2023, 12, 19)
    assert law.eli_work == "eli/bgbl-1/1949/gg"
    assert len(law.has_part) == 1
    assert law.has_part[0].eli == "eli/bgbl-1/1949/gg/art-1"


def test_legislation_from_api_minimal() -> None:
    data = {
        "legislationIdentifier": "eli/test",
        "name": "Test",
        "abbreviation": "T",
    }
    law = Legislation.from_api(data)
    assert law.has_part == ()
    assert law.official_long_title is None
    assert law.publication_date is None


def test_legislation_is_frozen() -> None:
    data = {"legislationIdentifier": "eli/test", "name": "T", "abbreviation": "T"}
    law = Legislation.from_api(data)
    with pytest.raises((AttributeError, TypeError)):
        law.name = "Changed"  # type: ignore[misc]


# ── Decision ──────────────────────────────────────────────────────────────────

def test_decision_from_api_full() -> None:
    data = {
        "@type": "Decision",
        "documentNumber": "BGH-2023-0001",
        "ecli": "ECLI:DE:BGH:2023:0001.URev.ZR1.23.0",
        "guidingPrinciple": "Leitsatz.",
        "tenor": "Tenor.",
        "decisionDate": "2023-03-15",
        "fileNumbers": ["I ZR 1/23", "I ZR 2/23"],
        "courtType": "BGH",
        "courtLocation": "Karlsruhe",
        "courtLabel": "Bundesgerichtshof",
        "legalEffect": "rechtskräftig",
        "documentType": "Urteil",
        "yearOfDecision": "2023",
        "headline": "BGH Urteil",
        "documentationOffice": "BGH",
    }
    dec = Decision.from_api(data)
    assert dec.document_number == "BGH-2023-0001"
    assert dec.ecli == "ECLI:DE:BGH:2023:0001.URev.ZR1.23.0"
    assert dec.decision_date == date(2023, 3, 15)
    assert len(dec.file_numbers) == 2
    assert dec.court_label == "Bundesgerichtshof"


def test_decision_ecli_is_optional() -> None:
    data = {
        "documentNumber": "D1",
        "courtType": "BGH",
        "documentType": "Beschluss",
        "fileNumbers": [],
    }
    dec = Decision.from_api(data)
    assert dec.ecli is None


def test_decision_is_frozen() -> None:
    data = {"documentNumber": "D1", "courtType": "BGH", "documentType": "U", "fileNumbers": []}
    dec = Decision.from_api(data)
    with pytest.raises((AttributeError, TypeError)):
        dec.document_number = "changed"  # type: ignore[misc]


# ── Court ─────────────────────────────────────────────────────────────────────

def test_court_from_api() -> None:
    data = {"type": "BGH", "location": "Karlsruhe", "label": "Bundesgerichtshof"}
    court = Court.from_api(data)
    assert court.type == "BGH"
    assert court.location == "Karlsruhe"
    assert court.label == "Bundesgerichtshof"


def test_court_no_location() -> None:
    data = {"type": "BVerfG", "label": "Bundesverfassungsgericht"}
    court = Court.from_api(data)
    assert court.location is None


# ── Statistics ────────────────────────────────────────────────────────────────

def test_statistics_from_api() -> None:
    data = {
        "legislationCount": 6534,
        "caseLawCount": 42871,
        "administrativeDirectiveCount": 0,
        "literatureCount": 0,
    }
    stats = Statistics.from_api(data)
    assert stats.legislation_count == 6534
    assert stats.case_law_count == 42871
    assert stats.administrative_directive_count == 0


def test_statistics_defaults() -> None:
    stats = Statistics.from_api({})
    assert stats.legislation_count == 0
    assert stats.case_law_count == 0


# ── TextMatch ─────────────────────────────────────────────────────────────────

def test_text_match_from_api() -> None:
    data = {"property": "name", "text": "<em>Grundgesetz</em>"}
    tm = TextMatch.from_api(data)
    assert tm.property == "name"
    assert "<em>" in tm.text


# ── PartialCollectionView ─────────────────────────────────────────────────────

def test_partial_collection_view_from_api() -> None:
    data = {
        "first": "?pageIndex=0",
        "last": "?pageIndex=5",
        "next": "?pageIndex=2",
        "previous": "?pageIndex=0",
    }
    view = PartialCollectionView.from_api(data)
    assert view.next == "?pageIndex=2"
    assert view.first == "?pageIndex=0"


def test_partial_collection_view_none() -> None:
    view = PartialCollectionView.from_api(None)
    assert view.next is None
    assert view.previous is None


# ── CollectionPage ────────────────────────────────────────────────────────────

def test_collection_page_has_next_true() -> None:
    view = PartialCollectionView(first=None, last=None, next="?pageIndex=1", previous=None)
    page: CollectionPage[Decision] = CollectionPage(total_items=100, members=(), view=view)
    assert page.has_next is True


def test_collection_page_has_next_false() -> None:
    view = PartialCollectionView(first=None, last=None, next=None, previous=None)
    page: CollectionPage[Decision] = CollectionPage(total_items=5, members=(), view=view)
    assert page.has_next is False


# ── _dispatch_item ────────────────────────────────────────────────────────────

def test_dispatch_item_decision() -> None:
    data = {
        "@type": "Decision",
        "documentNumber": "D1",
        "courtType": "BGH",
        "documentType": "Urteil",
        "fileNumbers": [],
    }
    result = _dispatch_item(data)
    assert isinstance(result, Decision)


def test_dispatch_item_legislation() -> None:
    data = {
        "@type": "Legislation",
        "legislationIdentifier": "eli/x",
        "name": "X",
        "abbreviation": "X",
        "hasPart": [],
    }
    result = _dispatch_item(data)
    assert isinstance(result, Legislation)


def test_dispatch_item_administrative_directive() -> None:
    data = {"@type": "AdministrativeDirective"}
    result = _dispatch_item(data)
    assert isinstance(result, AdministrativeDirective)


def test_dispatch_item_literature() -> None:
    data = {"@type": "Literature", "documentNumber": "LIT-2023-001"}
    result = _dispatch_item(data)
    assert isinstance(result, Literature)


def test_dispatch_item_type_decision_not_caselaw() -> None:
    """Regression: @type must be 'Decision', NOT 'CaseLaw'."""
    data_wrong = {"@type": "CaseLaw", "documentNumber": "D1", "courtType": "BGH", "documentType": "U", "fileNumbers": []}
    result_wrong = _dispatch_item(data_wrong)
    assert not isinstance(result_wrong, Decision), "@type='CaseLaw' must NOT map to Decision"

    data_correct = {"@type": "Decision", "documentNumber": "D1", "courtType": "BGH", "documentType": "U", "fileNumbers": []}
    result_correct = _dispatch_item(data_correct)
    assert isinstance(result_correct, Decision), "@type='Decision' must map to Decision"


def test_dispatch_item_unknown_returns_raw_dict() -> None:
    data = {"@type": "UnknownType", "someField": "value"}
    result = _dispatch_item(data)
    assert isinstance(result, dict)


# ── AdministrativeDirective & Literature ──────────────────────────────────────

def test_administrative_directive_from_api() -> None:
    ad = AdministrativeDirective.from_api({})
    assert isinstance(ad, AdministrativeDirective)


def test_literature_from_api() -> None:
    lit = Literature.from_api({"documentNumber": "LIT-2023-001"})
    assert isinstance(lit, Literature)
    assert lit.document_number == "LIT-2023-001"
    assert lit.year_of_publication is None
    assert lit.author is None
