from typing import Protocol

from app.services.domain_types import ProductUnderstanding, ScrapeResult


class ProductReasoningProvider(Protocol):
    def enrich_product_understanding(self, scrape_result: ScrapeResult, understanding: ProductUnderstanding) -> ProductUnderstanding:
        ...


class DeterministicReasoningProvider:
    def enrich_product_understanding(self, scrape_result: ScrapeResult, understanding: ProductUnderstanding) -> ProductUnderstanding:
        return understanding
