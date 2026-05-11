#!/usr/bin/env python3
"""Refresh offline test fixtures from the live NeuRIS API.

Usage:
    NEURIS_LIVE=1 python tests/_refresh_fixtures.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def main() -> None:
    if not os.getenv("NEURIS_LIVE"):
        print("Set NEURIS_LIVE=1 to refresh fixtures from the live API.")
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from neuris import NeuRISClient

    FIXTURES_DIR.mkdir(exist_ok=True)

    with NeuRISClient() as client:
        page = client.search_legislation(size=2)
        # Rebuild as fixture format
        fixture = {
            "totalItems": page.total_items,
            "member": [
                {
                    "item": {
                        "@type": "Legislation",
                        "legislationIdentifier": r.item.legislation_identifier,
                        "name": r.item.name,
                        "abbreviation": r.item.abbreviation,
                        "officialLongTitle": r.item.official_long_title,
                        "publicationDate": r.item.publication_date.isoformat() if r.item.publication_date else None,
                        "versionDate": r.item.version_date.isoformat() if r.item.version_date else None,
                        "eliWork": r.item.eli_work,
                        "hasPart": [
                            {"eli": p.eli, "legislationWorkIdentifier": p.legislation_work_identifier}
                            for p in r.item.has_part
                        ],
                    },
                    "textMatches": [
                        {"property": m.property, "text": m.text}
                        for m in r.text_matches
                    ],
                }
                for r in page.members
            ],
            "view": {
                "first": page.view.first,
                "last": page.view.last,
                "next": page.view.next,
                "previous": page.view.previous,
            },
        }
        (FIXTURES_DIR / "legislation_list.json").write_text(json.dumps(fixture, indent=2, ensure_ascii=False))
        print("Refreshed legislation_list.json")

        cl_page = client.search_case_law(size=1)
        if cl_page.members:
            d = cl_page.members[0].item
            detail = client.get_case_law(d.document_number)
            detail_fixture = {
                "@type": "Decision",
                "documentNumber": detail.document_number,
                "ecli": detail.ecli,
                "guidingPrinciple": detail.guiding_principle,
                "tenor": detail.tenor,
                "decisionDate": detail.decision_date.isoformat() if detail.decision_date else None,
                "fileNumbers": list(detail.file_numbers),
                "courtType": detail.court_type,
                "courtLocation": detail.court_location,
                "courtLabel": detail.court_label,
                "legalEffect": detail.legal_effect,
                "documentType": detail.document_type,
                "yearOfDecision": detail.year_of_decision,
                "headline": detail.headline,
                "documentationOffice": detail.documentation_office,
            }
            (FIXTURES_DIR / "case_law_detail.json").write_text(
                json.dumps(detail_fixture, indent=2, ensure_ascii=False)
            )
            print("Refreshed case_law_detail.json")

        stats = client.get_statistics()
        stats_fixture = {
            "legislationCount": stats.legislation_count,
            "caseLawCount": stats.case_law_count,
            "administrativeDirectiveCount": stats.administrative_directive_count,
            "literatureCount": stats.literature_count,
        }
        (FIXTURES_DIR / "statistics.json").write_text(
            json.dumps(stats_fixture, indent=2, ensure_ascii=False)
        )
        print("Refreshed statistics.json")

        courts = client.list_courts()
        courts_fixture = {
            "totalItems": len(courts),
            "member": [
                {"type": c.type, "location": c.location, "label": c.label}
                for c in courts[:10]
            ],
        }
        (FIXTURES_DIR / "courts_list.json").write_text(
            json.dumps(courts_fixture, indent=2, ensure_ascii=False)
        )
        print("Refreshed courts_list.json")

    print("Done.")


if __name__ == "__main__":
    main()
