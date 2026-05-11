"""ELI (European Legislation Identifier) parse and build helpers.

ELI format: https://eur-lex.europa.eu/eli-register/about.html

German federal law ELI example:
  eli/bgbl-1/2023/s1234/2023-06-07/1/deu/regelungstext-1

Work-level ELI (no expression suffix):
  eli/bgbl-1/2023/s1234
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, unquote


@dataclass(slots=True, frozen=True)
class ELI:
    """Parsed ELI components."""

    jurisdiction: str
    agent: str
    year: str
    natural_number: str
    point_in_time: str | None
    version: str | None
    language: str | None
    subtype: str | None

    @property
    def is_expression(self) -> bool:
        """True when this ELI identifies a specific expression (time + language)."""
        return self.point_in_time is not None

    def to_work(self) -> ELI:
        """Return the work-level ELI (strips expression components)."""
        return ELI(
            jurisdiction=self.jurisdiction,
            agent=self.agent,
            year=self.year,
            natural_number=self.natural_number,
            point_in_time=None,
            version=None,
            language=None,
            subtype=None,
        )

    def build(self) -> str:
        """Reconstruct the ELI path string."""
        parts = [self.jurisdiction, self.agent, self.year, self.natural_number]
        if self.point_in_time is not None:
            parts.append(self.point_in_time)
        if self.version is not None:
            parts.append(self.version)
        if self.language is not None:
            parts.append(self.language)
        if self.subtype is not None:
            parts.append(self.subtype)
        return "eli/" + "/".join(parts)

    def __str__(self) -> str:
        return self.build()


def parse_eli(eli_string: str) -> ELI:
    """Parse an ELI string into an ELI dataclass.

    Args:
        eli_string: Full ELI path, optionally URL-encoded. May start with "eli/" or not.

    Returns:
        Parsed ELI dataclass.

    Raises:
        ValueError: If the ELI string does not have the minimum required components.
    """
    decoded = unquote(eli_string.strip())
    if decoded.startswith("eli/"):
        decoded = decoded[4:]
    parts = decoded.split("/")
    if len(parts) < 3:
        raise ValueError(
            f"Invalid ELI: expected at least 3 components "
            f"(gazette/year/act), got {len(parts)}: {eli_string!r}"
        )
    return ELI(
        jurisdiction=parts[0],
        agent=parts[1],
        year=parts[2],
        natural_number=parts[3] if len(parts) > 3 else "",
        point_in_time=parts[4] if len(parts) > 4 else None,
        version=parts[5] if len(parts) > 5 else None,
        language=parts[6] if len(parts) > 6 else None,
        subtype=parts[7] if len(parts) > 7 else None,
    )


def build_eli(
    jurisdiction: str,
    agent: str,
    year: str | int,
    natural_number: str,
    *,
    point_in_time: str | None = None,
    version: str | None = None,
    language: str | None = None,
    subtype: str | None = None,
) -> str:
    """Construct an ELI path string from components."""
    eli = ELI(
        jurisdiction=jurisdiction,
        agent=agent,
        year=str(year),
        natural_number=natural_number,
        point_in_time=point_in_time,
        version=version,
        language=language,
        subtype=subtype,
    )
    return eli.build()


def eli_to_url_path(eli_string: str) -> str:
    """Encode an ELI string for use as a URL path segment.

    Percent-encodes components that are not safe in URL paths.
    """
    parsed = parse_eli(eli_string)
    parts = ["eli", parsed.jurisdiction, parsed.agent, parsed.year, parsed.natural_number]
    if parsed.point_in_time is not None:
        parts.append(parsed.point_in_time)
    if parsed.version is not None:
        parts.append(parsed.version)
    if parsed.language is not None:
        parts.append(parsed.language)
    if parsed.subtype is not None:
        parts.append(quote(parsed.subtype, safe=""))
    return "/".join(parts)
