"""Tests for content/download endpoints (.xml, .html, .zip) on NeuRISClient."""

from __future__ import annotations

import pytest

from neuris.client import NeuRISClient, AsyncNeuRISClient
from .conftest import MockTransport, AsyncMockTransport

_XML = b"<?xml version='1.0'?><root/>"
_HTML = b"<html><body>Urteil</body></html>"
_ZIP = b"PK\x03\x04fake-zip-content"


# ── Sync: case law ────────────────────────────────────────────────────────────

class TestGetCaseLawContent:
    def test_xml_returns_bytes(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/case-law/BGHE-001.xml", _XML)
        client = NeuRISClient(transport=mock_transport)
        result = client.get_case_law_xml("BGHE-001")
        assert result == _XML

    def test_xml_uses_correct_accept_header(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/case-law/BGHE-001.xml", _XML)
        NeuRISClient(transport=mock_transport).get_case_law_xml("BGHE-001")
        path, accept, _ = mock_transport._raw_calls[-1]
        assert path == "/case-law/BGHE-001.xml"
        assert accept == "application/xml"

    def test_html_returns_str(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/case-law/BGHE-001.html", _HTML)
        client = NeuRISClient(transport=mock_transport)
        result = client.get_case_law_html("BGHE-001")
        assert isinstance(result, str)
        assert result == _HTML.decode("utf-8")

    def test_html_uses_correct_accept_header(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/case-law/BGHE-001.html", _HTML)
        NeuRISClient(transport=mock_transport).get_case_law_html("BGHE-001")
        path, accept, _ = mock_transport._raw_calls[-1]
        assert path == "/case-law/BGHE-001.html"
        assert accept == "text/html"

    def test_zip_returns_bytes(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/case-law/BGHE-001.zip", _ZIP)
        client = NeuRISClient(transport=mock_transport)
        result = client.get_case_law_zip("BGHE-001")
        assert result == _ZIP

    def test_zip_uses_correct_accept_header(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/case-law/BGHE-001.zip", _ZIP)
        NeuRISClient(transport=mock_transport).get_case_law_zip("BGHE-001")
        path, accept, _ = mock_transport._raw_calls[-1]
        assert path == "/case-law/BGHE-001.zip"
        assert accept == "application/zip"


# ── Sync: legislation ─────────────────────────────────────────────────────────

class TestGetLegislationContent:
    _ELI = "eli/bgbl-1/2024/testgesetz"
    _SUBTYPE = "regelungstext-1"

    def test_xml_path_constructed_correctly(self, mock_transport: MockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.xml"
        mock_transport.register_raw(path, _XML)
        NeuRISClient(transport=mock_transport).get_legislation_xml(self._ELI, self._SUBTYPE)
        called_path, accept, _ = mock_transport._raw_calls[-1]
        assert called_path == path
        assert accept == "application/xml"

    def test_xml_strips_eli_prefix(self, mock_transport: MockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.xml"
        mock_transport.register_raw(path, _XML)
        NeuRISClient(transport=mock_transport).get_legislation_xml(self._ELI, self._SUBTYPE)
        called_path, _, _ = mock_transport._raw_calls[-1]
        assert called_path == path

    def test_xml_handles_leading_slash_in_eli(self, mock_transport: MockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.xml"
        mock_transport.register_raw(path, _XML)
        NeuRISClient(transport=mock_transport).get_legislation_xml("/eli/bgbl-1/2024/testgesetz", self._SUBTYPE)
        called_path, _, _ = mock_transport._raw_calls[-1]
        assert called_path == path

    def test_html_returns_str(self, mock_transport: MockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.html"
        mock_transport.register_raw(path, _HTML)
        result = NeuRISClient(transport=mock_transport).get_legislation_html(self._ELI, self._SUBTYPE)
        assert isinstance(result, str)

    def test_html_accept_header(self, mock_transport: MockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.html"
        mock_transport.register_raw(path, _HTML)
        NeuRISClient(transport=mock_transport).get_legislation_html(self._ELI, self._SUBTYPE)
        _, accept, _ = mock_transport._raw_calls[-1]
        assert accept == "text/html"

    def test_zip_returns_bytes(self, mock_transport: MockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.zip"
        mock_transport.register_raw(path, _ZIP)
        result = NeuRISClient(transport=mock_transport).get_legislation_zip(self._ELI, self._SUBTYPE)
        assert result == _ZIP

    def test_zip_accept_header(self, mock_transport: MockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.zip"
        mock_transport.register_raw(path, _ZIP)
        NeuRISClient(transport=mock_transport).get_legislation_zip(self._ELI, self._SUBTYPE)
        _, accept, _ = mock_transport._raw_calls[-1]
        assert accept == "application/zip"

    def test_article_html_returns_str(self, mock_transport: MockTransport) -> None:
        article_eid = "art-1"
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{article_eid}.html"
        mock_transport.register_raw(path, _HTML)
        result = NeuRISClient(transport=mock_transport).get_legislation_article_html(self._ELI, article_eid)
        assert isinstance(result, str)

    def test_article_html_path(self, mock_transport: MockTransport) -> None:
        article_eid = "art-2"
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{article_eid}.html"
        mock_transport.register_raw(path, _HTML)
        NeuRISClient(transport=mock_transport).get_legislation_article_html(self._ELI, article_eid)
        called_path, accept, _ = mock_transport._raw_calls[-1]
        assert called_path == path
        assert accept == "text/html"


# ── Sync: administrative directive ───────────────────────────────────────────

class TestGetAdministrativeDirectiveContent:
    def test_xml_path_and_accept(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/administrative-directive/VwV-001.xml", _XML)
        NeuRISClient(transport=mock_transport).get_administrative_directive_xml("VwV-001")
        path, accept, _ = mock_transport._raw_calls[-1]
        assert path == "/administrative-directive/VwV-001.xml"
        assert accept == "application/xml"

    def test_html_returns_str(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/administrative-directive/VwV-001.html", _HTML)
        result = NeuRISClient(transport=mock_transport).get_administrative_directive_html("VwV-001")
        assert isinstance(result, str)

    def test_html_path_and_accept(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/administrative-directive/VwV-001.html", _HTML)
        NeuRISClient(transport=mock_transport).get_administrative_directive_html("VwV-001")
        path, accept, _ = mock_transport._raw_calls[-1]
        assert path == "/administrative-directive/VwV-001.html"
        assert accept == "text/html"


# ── Sync: literature ──────────────────────────────────────────────────────────

class TestGetLiteratureContent:
    def test_xml_path_and_accept(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/literature/LIT-001.xml", _XML)
        NeuRISClient(transport=mock_transport).get_literature_xml("LIT-001")
        path, accept, _ = mock_transport._raw_calls[-1]
        assert path == "/literature/LIT-001.xml"
        assert accept == "application/xml"

    def test_html_returns_str(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/literature/LIT-001.html", _HTML)
        result = NeuRISClient(transport=mock_transport).get_literature_html("LIT-001")
        assert isinstance(result, str)

    def test_html_path_and_accept(self, mock_transport: MockTransport) -> None:
        mock_transport.register_raw("/literature/LIT-001.html", _HTML)
        NeuRISClient(transport=mock_transport).get_literature_html("LIT-001")
        path, accept, _ = mock_transport._raw_calls[-1]
        assert path == "/literature/LIT-001.html"
        assert accept == "text/html"


# ── Async: case law ───────────────────────────────────────────────────────────

class TestAsyncGetCaseLawContent:
    @pytest.mark.asyncio
    async def test_xml_returns_bytes(self, async_mock_transport: AsyncMockTransport) -> None:
        async_mock_transport.register_raw("/case-law/BGHE-001.xml", _XML)
        client = AsyncNeuRISClient(transport=async_mock_transport)
        result = await client.get_case_law_xml("BGHE-001")
        assert result == _XML

    @pytest.mark.asyncio
    async def test_html_returns_str(self, async_mock_transport: AsyncMockTransport) -> None:
        async_mock_transport.register_raw("/case-law/BGHE-001.html", _HTML)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_case_law_html("BGHE-001")
        assert isinstance(result, str)
        assert result == _HTML.decode("utf-8")

    @pytest.mark.asyncio
    async def test_zip_returns_bytes(self, async_mock_transport: AsyncMockTransport) -> None:
        async_mock_transport.register_raw("/case-law/BGHE-001.zip", _ZIP)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_case_law_zip("BGHE-001")
        assert result == _ZIP


# ── Async: legislation ────────────────────────────────────────────────────────

class TestAsyncGetLegislationContent:
    _ELI = "eli/bgbl-1/2024/testgesetz"
    _SUBTYPE = "regelungstext-1"

    @pytest.mark.asyncio
    async def test_xml_returns_bytes(self, async_mock_transport: AsyncMockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.xml"
        async_mock_transport.register_raw(path, _XML)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_legislation_xml(self._ELI, self._SUBTYPE)
        assert result == _XML

    @pytest.mark.asyncio
    async def test_html_returns_str(self, async_mock_transport: AsyncMockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.html"
        async_mock_transport.register_raw(path, _HTML)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_legislation_html(self._ELI, self._SUBTYPE)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_zip_returns_bytes(self, async_mock_transport: AsyncMockTransport) -> None:
        path = f"/legislation/eli/bgbl-1/2024/testgesetz/{self._SUBTYPE}.zip"
        async_mock_transport.register_raw(path, _ZIP)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_legislation_zip(self._ELI, self._SUBTYPE)
        assert result == _ZIP

    @pytest.mark.asyncio
    async def test_article_html_returns_str(self, async_mock_transport: AsyncMockTransport) -> None:
        path = "/legislation/eli/bgbl-1/2024/testgesetz/art-1.html"
        async_mock_transport.register_raw(path, _HTML)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_legislation_article_html(self._ELI, "art-1")
        assert isinstance(result, str)


# ── Async: administrative directive + literature ──────────────────────────────

class TestAsyncOtherContent:
    @pytest.mark.asyncio
    async def test_admin_directive_xml(self, async_mock_transport: AsyncMockTransport) -> None:
        async_mock_transport.register_raw("/administrative-directive/VwV-001.xml", _XML)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_administrative_directive_xml("VwV-001")
        assert result == _XML

    @pytest.mark.asyncio
    async def test_admin_directive_html(self, async_mock_transport: AsyncMockTransport) -> None:
        async_mock_transport.register_raw("/administrative-directive/VwV-001.html", _HTML)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_administrative_directive_html("VwV-001")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_literature_xml(self, async_mock_transport: AsyncMockTransport) -> None:
        async_mock_transport.register_raw("/literature/LIT-001.xml", _XML)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_literature_xml("LIT-001")
        assert result == _XML

    @pytest.mark.asyncio
    async def test_literature_html(self, async_mock_transport: AsyncMockTransport) -> None:
        async_mock_transport.register_raw("/literature/LIT-001.html", _HTML)
        result = await AsyncNeuRISClient(transport=async_mock_transport).get_literature_html("LIT-001")
        assert isinstance(result, str)
