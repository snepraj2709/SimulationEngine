from __future__ import annotations

from urllib.parse import urlparse

from app.services.domain_types import ProductUnderstanding, ScrapeResult
from app.services.llm.providers import DeterministicReasoningProvider, ProductReasoningProvider
from app.utils.text import dedupe_preserve_order, truncate_text


class ProductUnderstandingService:
    def __init__(self, provider: ProductReasoningProvider | None = None) -> None:
        self.provider = provider or DeterministicReasoningProvider()

    def build(self, scrape_result: ScrapeResult) -> ProductUnderstanding:
        raw_text = scrape_result.raw_text.lower()
        company_name = self._derive_company_name(scrape_result)
        product_name = self._derive_product_name(scrape_result, company_name)
        category, subcategory = self._classify_category(raw_text)
        pricing_model = self._infer_pricing_model(raw_text, scrape_result.pricing_clues)
        feature_clusters = self._derive_feature_clusters(scrape_result, subcategory)
        target_customer_signals = self._derive_target_customers(scrape_result, category, subcategory)
        positioning_summary = self._build_positioning_summary(scrape_result)
        monetization_hypothesis = self._build_monetization_hypothesis(pricing_model, subcategory)
        warnings: list[str] = []
        if not scrape_result.pricing_clues:
            warnings.append("Pricing was not clearly visible; revenue assumptions use category defaults.")
        if len(scrape_result.headings) < 2 and len(scrape_result.paragraphs) < 3:
            warnings.append("Sparse page content lowered extraction confidence.")
        if category == "Unknown":
            warnings.append("The site did not present enough product signals to classify confidently.")

        confidence_scores = self._build_confidence_scores(scrape_result, category, pricing_model, target_customer_signals)
        confidence_score = round(sum(confidence_scores.values()) / len(confidence_scores), 2)

        understanding = ProductUnderstanding(
            company_name=company_name,
            product_name=product_name,
            category=category,
            subcategory=subcategory,
            positioning_summary=positioning_summary,
            pricing_model=pricing_model,
            feature_clusters=feature_clusters,
            monetization_hypothesis=monetization_hypothesis,
            target_customer_signals=target_customer_signals,
            confidence_score=confidence_score,
            confidence_scores=confidence_scores,
            warnings=warnings,
            raw_extracted_json=scrape_result.raw_extracted_json,
        )
        enriched = self.provider.enrich_product_understanding(scrape_result, understanding)
        enriched.normalized_json = enriched.model_dump()
        return enriched

    def build_from_normalized(self, normalized_json: dict) -> ProductUnderstanding:
        payload = dict(normalized_json)
        payload.setdefault("raw_extracted_json", {})
        payload.setdefault("normalized_json", normalized_json)
        return ProductUnderstanding(**payload)

    def _derive_company_name(self, scrape_result: ScrapeResult) -> str:
        hostname = urlparse(scrape_result.final_url).hostname or ""
        if "netflix" in hostname:
            return "Netflix"
        if scrape_result.title:
            for separator in (" - ", " | ", " — ", ": "):
                if separator in scrape_result.title:
                    return scrape_result.title.split(separator, 1)[0].strip()
        root = hostname.replace("www.", "").split(".")[0]
        return root.replace("-", " ").title() or "Unknown Company"

    def _derive_product_name(self, scrape_result: ScrapeResult, company_name: str) -> str:
        if "netflix" in company_name.lower():
            return "Netflix Streaming Subscription"
        if scrape_result.headings:
            return truncate_text(scrape_result.headings[0], 80)
        return company_name

    def _classify_category(self, raw_text: str) -> tuple[str, str]:
        if any(keyword in raw_text for keyword in ("watch", "movies", "tv shows", "stream", "episodes", "series")):
            return "Consumer Subscription Software", "Video Streaming"
        if any(keyword in raw_text for keyword in ("crm", "pipeline", "sales team", "leads")):
            return "B2B Software", "CRM"
        if any(keyword in raw_text for keyword in ("analytics", "dashboard", "business intelligence", "metrics")):
            return "B2B Software", "Analytics"
        if any(keyword in raw_text for keyword in ("payments", "checkout", "invoice", "billing")):
            return "Fintech", "Payments"
        if any(keyword in raw_text for keyword in ("ai", "copilot", "assistant", "automation")):
            return "AI Software", "Productivity AI"
        if any(keyword in raw_text for keyword in ("store", "catalog", "shopping", "commerce")):
            return "Commerce Platform", "E-commerce"
        return "Unknown", "General Product Website"

    def _infer_pricing_model(self, raw_text: str, pricing_clues: list[str]) -> str:
        combined = " ".join(pricing_clues).lower() + " " + raw_text
        if any(keyword in combined for keyword in ("plans", "monthly", "cancel anytime", "subscription")):
            return "tiered_subscription"
        if "free trial" in combined or ("free" in combined and "upgrade" in combined):
            return "freemium"
        if "contact sales" in combined or "request a demo" in combined:
            return "sales_led_custom_pricing"
        if any(keyword in combined for keyword in ("one-time", "lifetime")):
            return "one_time_purchase"
        return "usage_or_custom"

    def _derive_feature_clusters(self, scrape_result: ScrapeResult, subcategory: str) -> list[str]:
        features = dedupe_preserve_order(scrape_result.feature_clues + scrape_result.headings + scrape_result.paragraphs)
        lowered = " ".join(features).lower()
        if subcategory == "Video Streaming":
            canonical = [
                "content library access",
                "device support",
                "video quality tiers",
                "simultaneous streams",
                "ad-supported plan options",
            ]
            if "kids" in lowered:
                canonical.append("household profile management")
            return canonical[:6]
        if subcategory == "CRM":
            return ["pipeline management", "team workflows", "forecasting", "reporting", "integrations"]
        if subcategory == "Analytics":
            return ["dashboarding", "data connectors", "reporting", "alerts", "team collaboration"]
        if subcategory == "Payments":
            return ["checkout", "subscriptions", "payouts", "fraud controls", "developer APIs"]
        extracted = [truncate_text(feature, 60).lower() for feature in features[:6]]
        return extracted or ["core product workflow", "pricing and packaging", "support experience"]

    def _derive_target_customers(self, scrape_result: ScrapeResult, category: str, subcategory: str) -> list[str]:
        text = " ".join(scrape_result.audience_clues + scrape_result.paragraphs + scrape_result.headings).lower()
        if subcategory == "Video Streaming":
            return [
                "entertainment-seeking households",
                "mobile-first viewers",
                "price-sensitive individuals",
                "premium content consumers",
            ]
        signals: list[str] = []
        if "teams" in text or "business" in text:
            signals.append("cross-functional teams")
        if "developers" in text:
            signals.append("developer-led buyers")
        if "founders" in text or "startup" in text:
            signals.append("startup operators")
        if category == "Unknown":
            signals.append("general digital product buyers")
        return dedupe_preserve_order(signals)[:5] or ["general product evaluators"]

    def _build_positioning_summary(self, scrape_result: ScrapeResult) -> str:
        if scrape_result.meta_description:
            return truncate_text(scrape_result.meta_description, 180)
        if scrape_result.headings:
            summary = " ".join(scrape_result.headings[:2])
            return truncate_text(summary, 180)
        return "The site provides limited public information, so positioning was inferred from sparse landing page signals."

    def _build_monetization_hypothesis(self, pricing_model: str, subcategory: str) -> str:
        if pricing_model == "tiered_subscription":
            if subcategory == "Video Streaming":
                return "Recurring monthly subscription revenue across multiple plan tiers."
            return "Recurring subscription revenue with tiered feature access."
        if pricing_model == "freemium":
            return "Free entry with conversion pressure toward paid usage or premium tiers."
        if pricing_model == "sales_led_custom_pricing":
            return "Contract revenue from negotiated enterprise packages."
        if pricing_model == "one_time_purchase":
            return "Upfront revenue with optional support or add-on monetization."
        return "Likely recurring or negotiated monetization inferred from category norms."

    def _build_confidence_scores(
        self,
        scrape_result: ScrapeResult,
        category: str,
        _pricing_model: str,
        target_customer_signals: list[str],
    ) -> dict[str, float]:
        return {
            "company_name": 0.9 if scrape_result.title else 0.6,
            "category": 0.85 if category != "Unknown" else 0.45,
            "pricing_model": 0.82 if scrape_result.pricing_clues else 0.38,
            "feature_clusters": 0.84 if scrape_result.feature_clues or scrape_result.headings else 0.5,
            "target_customer_signals": 0.8 if target_customer_signals else 0.45,
            "positioning_summary": 0.88 if scrape_result.meta_description or scrape_result.headings else 0.52,
        }
