from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_SOURCE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"text/plain", "text/html", "application/xhtml+xml"}


class SourceAcquisitionError(Exception):
    """Raised when a source URL cannot be fetched safely as text."""


@dataclass(frozen=True)
class FetchedSource:
    text: str
    content_type: str
    final_uri: str


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"head", "script", "style", "noscript", "template"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"head", "script", "style", "noscript", "template"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise SourceAcquisitionError("Source redirects are not allowed")


class SafeSourceFetcher:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.opener = build_opener(_NoRedirectHandler())

    def fetch(self, source_uri: str) -> FetchedSource:
        self.validate_public_url(source_uri)
        request = Request(
            source_uri,
            headers={
                "Accept": "text/plain, text/html, application/xhtml+xml",
                "User-Agent": "literature-workbench/0.1",
            },
        )
        try:
            with self.opener.open(request, timeout=self.timeout_seconds) as response:
                final_uri = response.geturl()
                self.validate_public_url(final_uri)
                content_type = response.headers.get_content_type()
                if content_type not in ALLOWED_CONTENT_TYPES:
                    raise SourceAcquisitionError("Source content is not supported text")
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_SOURCE_BYTES:
                    raise SourceAcquisitionError("Source exceeds the 5 MB limit")
                text = response.read(MAX_SOURCE_BYTES + 1)
        except SourceAcquisitionError:
            raise
        except Exception as exc:
            raise SourceAcquisitionError("Source URL could not be fetched") from exc
        if len(text) > MAX_SOURCE_BYTES:
            raise SourceAcquisitionError("Source exceeds the 5 MB limit")
        try:
            decoded = text.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceAcquisitionError("Source is not UTF-8 text") from exc
        decoded = self.normalize_text(decoded, content_type)
        if not decoded:
            raise SourceAcquisitionError("Source contains no usable text")
        return FetchedSource(text=decoded, content_type=content_type, final_uri=final_uri)

    @staticmethod
    def normalize_text(text: str, content_type: str) -> str:
        if content_type in {"text/html", "application/xhtml+xml"}:
            parser = _VisibleTextParser()
            parser.feed(text)
            text = " ".join(parser.parts)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def validate_public_url(source_uri: str) -> None:
        parsed = urlsplit(source_uri)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise SourceAcquisitionError("Source URL must use HTTP(S) with a public host")
        try:
            addresses = {
                ipaddress.ip_address(info[4][0])
                for info in socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)
            }
        except (OSError, ValueError) as exc:
            raise SourceAcquisitionError("Source host could not be resolved") from exc
        if not addresses or any(not address.is_global for address in addresses):
            raise SourceAcquisitionError("Source URL must resolve to a public host")
