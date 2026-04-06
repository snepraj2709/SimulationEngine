from __future__ import annotations

from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.services.domain_types import ScrapeResult
from app.utils.text import dedupe_preserve_order, extract_price_signals, normalize_text, top_keywords, truncate_text

logger = get_logger(__name__)


class ScraperService:
    USER_AGENT = "DecisionSimulationEngineBot/0.1 (+https://localhost)"

    async def scrape(self, normalized_url: str) -> ScrapeResult:
        settings = get_settings()
        timeout = httpx.Timeout(
            timeout=settings.request_timeout_seconds,
            connect=settings.connect_timeout_seconds,
        )
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        }
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
                response = await client.get(normalized_url)
        except httpx.TimeoutException as exc:
            logger.warning("Scrape timed out", extra={"extra_data": {"url": normalized_url}})
            raise AppException(504, "scrape_timeout", "The website timed out during extraction.") from exc
        except httpx.HTTPError as exc:
            raise AppException(502, "scrape_failed", "The website could not be reached for analysis.") from exc

        if response.status_code in {401, 403}:
            raise AppException(502, "scrape_blocked", "The website blocked automated retrieval.")
        if response.status_code >= 400:
            raise AppException(502, "scrape_failed", f"Website returned HTTP {response.status_code}.")

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            raise AppException(422, "non_html_content", "The submitted URL does not appear to be an HTML product page.")
        if len(response.content) > settings.scrape_max_bytes:
            raise AppException(413, "content_too_large", "The page content is too large to analyze safely.")
        return self._parse_html(str(response.url), response.text, fetch_source="network")

    def _parse_html(self, final_url: str, html: str, *, fetch_source: str) -> ScrapeResult:
        settings = get_settings()
        soup = BeautifulSoup(html, "html.parser")
        title = normalize_text(soup.title.string if soup.title and soup.title.string else "")
        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_description = normalize_text(str(meta_tag["content"]))

        headings = dedupe_preserve_order(
            [
                element.get_text(" ", strip=True)
                for element in soup.select("h1, h2, h3")
                if element.get_text(" ", strip=True)
            ]
        )[:12]

        paragraphs = dedupe_preserve_order(
            [
                element.get_text(" ", strip=True)
                for element in soup.select("p, li")
                if element.get_text(" ", strip=True)
            ]
        )[:24]

        buttons = dedupe_preserve_order(
            [
                element.get_text(" ", strip=True)
                for element in soup.select("button, a")
                if element.get_text(" ", strip=True)
            ]
        )[:20]

        raw_chunks = [title, meta_description, *headings, *paragraphs, *buttons]
        raw_text = truncate_text(" ".join(raw_chunks), settings.scrape_max_content_chars)

        feature_candidates = [chunk for chunk in headings + paragraphs if any(word in chunk.lower() for word in ("watch", "feature", "download", "analytics", "automation", "support", "manage", "profiles", "team", "dashboard"))]
        audience_candidates = [
            chunk
            for chunk in headings + paragraphs + buttons
            if any(word in chunk.lower() for word in ("for ", "teams", "households", "business", "developers", "kids", "families", "customers", "founders"))
        ]
        category_keywords = top_keywords(headings + paragraphs, limit=10)
        pricing_clues = extract_price_signals(raw_chunks)
        if not pricing_clues:
            pricing_clues = [chunk for chunk in paragraphs if any(word in chunk.lower() for word in ("pricing", "plans", "monthly", "annual", "cost", "cancel anytime"))][:5]

        parsed = urlparse(final_url)
        raw_payload = {
            "title": title,
            "meta_description": meta_description,
            "headings": headings,
            "paragraphs": paragraphs,
            "buttons": buttons,
            "host": parsed.hostname,
            "path": parsed.path,
            "pricing_clues": pricing_clues,
            "feature_candidates": feature_candidates[:10],
            "audience_candidates": audience_candidates[:10],
            "category_keywords": category_keywords,
        }

        return ScrapeResult(
            source_url=final_url,
            final_url=final_url,
            title=title or parsed.hostname or "Unknown product",
            meta_description=meta_description,
            headings=headings,
            paragraphs=paragraphs,
            feature_clues=dedupe_preserve_order(feature_candidates)[:10],
            pricing_clues=pricing_clues[:10],
            audience_clues=dedupe_preserve_order(audience_candidates)[:10],
            category_clues=category_keywords,
            raw_text=raw_text,
            raw_extracted_json=raw_payload,
            fetch_source=fetch_source,
        )
