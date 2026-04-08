from __future__ import annotations

import re
from urllib.parse import urlparse

from app.services.domain_types import (
    BusinessModelSignal,
    CustomerLogic,
    FeatureCluster,
    MonetizationModel,
    ProductUnderstanding,
    ScrapeResult,
    SimulationLever,
    SourceCoverage,
    UncertaintyItem,
)
from app.services.llm.providers import DeterministicReasoningProvider, ProductReasoningProvider
from app.utils.text import dedupe_preserve_order, normalize_text, truncate_text

SIGNAL_ORDER: tuple[str, ...] = (
    "buyer_type",
    "sales_motion",
    "pricing_visibility",
    "deployment_complexity",
    "time_to_value",
    "workflow_criticality",
    "compliance_sensitivity",
    "switching_friction",
    "expansion_potential",
    "monetization_style",
)

SIGNAL_LABELS: dict[str, str] = {
    "buyer_type": "Buyer Type",
    "sales_motion": "Sales Motion",
    "pricing_visibility": "Pricing Visibility",
    "deployment_complexity": "Deployment Complexity",
    "time_to_value": "Time-to-Value",
    "workflow_criticality": "Workflow Criticality",
    "compliance_sensitivity": "Compliance Sensitivity",
    "switching_friction": "Switching Friction",
    "expansion_potential": "Expansion Potential",
    "monetization_style": "Monetization Style",
}

IMPORTANCE_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


class ProductUnderstandingService:
    def __init__(self, provider: ProductReasoningProvider | None = None) -> None:
        self.provider = provider or DeterministicReasoningProvider()

    def build(self, scrape_result: ScrapeResult) -> ProductUnderstanding:
        raw_text = scrape_result.raw_text.lower()
        company_name = self._derive_company_name(scrape_result)
        product_name = self._derive_product_name(scrape_result, company_name)
        category, subcategory = self._classify_category(raw_text)
        pricing_model = self._infer_pricing_model(raw_text, scrape_result.pricing_clues)
        feature_clusters = self._derive_feature_cluster_labels(scrape_result, subcategory)
        buyer_type = self._derive_buyer_type(
            explicit_buyer_type="",
            raw_payload=scrape_result.raw_extracted_json,
            category=category,
            subcategory=subcategory,
            legacy_target_signals=[],
        )
        summary_line = self._build_summary_line(scrape_result)
        monetization_hypothesis = self._build_monetization_hypothesis(pricing_model, subcategory)
        confidence_scores = self._default_confidence_scores(
            raw_payload=scrape_result.raw_extracted_json,
            category=category,
            pricing_model=pricing_model,
            has_customer_logic=False,
            has_feature_clusters=bool(feature_clusters),
        )

        understanding = ProductUnderstanding(
            company_name=company_name,
            product_name=product_name,
            category=category,
            subcategory=subcategory,
            positioning_summary=summary_line,
            pricing_model=pricing_model,
            feature_clusters=feature_clusters,
            monetization_hypothesis=monetization_hypothesis,
            target_customer_signals=[buyer_type] if buyer_type else [],
            confidence_score=round(sum(confidence_scores.values()) / len(confidence_scores), 2),
            confidence_scores=confidence_scores,
            warnings=[],
            raw_extracted_json=scrape_result.raw_extracted_json,
            summary_line=summary_line,
            buyer_type=buyer_type,
            sales_motion="",
            customer_logic=CustomerLogic(
                core_job_to_be_done=self._derive_job_to_be_done(scrape_result, summary_line),
                why_they_buy=self._derive_why_they_buy(scrape_result),
                why_they_hesitate=self._derive_why_they_hesitate(scrape_result),
                what_it_replaces=self._derive_replacements(scrape_result, category),
            ),
            feature_cluster_details=[
                FeatureCluster(
                    key=self._slugify(label),
                    label=label,
                    importance="high" if index < 2 else "medium" if index < 4 else "low",
                )
                for index, label in enumerate(feature_clusters)
            ],
        )
        enriched = self.provider.enrich_product_understanding(scrape_result, understanding)
        finalized = self.finalize(enriched, scrape_result=scrape_result)
        finalized.normalized_json = finalized.model_dump()
        return finalized

    def build_from_normalized(self, normalized_json: dict) -> ProductUnderstanding:
        payload = dict(normalized_json)
        payload.setdefault("raw_extracted_json", {})
        payload.setdefault("normalized_json", normalized_json)

        feature_cluster_details = self._coerce_feature_cluster_details(
            payload.get("feature_cluster_details") or payload.get("feature_clusters") or []
        )
        customer_logic = CustomerLogic.model_validate(payload.get("customer_logic") or {})
        monetization_payload = payload.get("monetization_model") or {}
        monetization_model = MonetizationModel.model_validate(
            {
                "pricing_visibility": monetization_payload.get("pricing_visibility", "low"),
                "pricing_model": monetization_payload.get("pricing_model", payload.get("pricing_model", "usage_or_custom")),
                "monetization_hypothesis": monetization_payload.get(
                    "monetization_hypothesis",
                    payload.get("monetization_hypothesis", ""),
                ),
                "sales_motion": monetization_payload.get("sales_motion", payload.get("sales_motion", "")),
            }
        )

        understanding = ProductUnderstanding(
            company_name=payload.get("company_name") or "Unknown Company",
            product_name=payload.get("product_name") or payload.get("company_name") or "Unknown Product",
            category=payload.get("category") or "Unknown",
            subcategory=payload.get("subcategory") or "General Product Website",
            positioning_summary=payload.get("positioning_summary") or payload.get("summary_line") or "",
            pricing_model=payload.get("pricing_model") or monetization_model.pricing_model,
            feature_clusters=self._extract_feature_cluster_labels(feature_cluster_details, payload.get("feature_clusters")),
            monetization_hypothesis=payload.get("monetization_hypothesis") or monetization_model.monetization_hypothesis,
            target_customer_signals=self._coerce_string_list(payload.get("target_customer_signals") or []),
            confidence_score=float(payload.get("confidence_score") or 0),
            confidence_scores={str(key): float(value) for key, value in (payload.get("confidence_scores") or {}).items()},
            warnings=self._coerce_string_list(payload.get("warnings") or []),
            raw_extracted_json=dict(payload.get("raw_extracted_json") or {}),
            normalized_json=dict(payload.get("normalized_json") or normalized_json),
            summary_line=payload.get("summary_line") or payload.get("positioning_summary") or "",
            buyer_type=payload.get("buyer_type") or "",
            sales_motion=payload.get("sales_motion") or monetization_model.sales_motion,
            review_status=payload.get("review_status") or "ready",
            business_model_signals=[
                BusinessModelSignal.model_validate(item) for item in (payload.get("business_model_signals") or [])
            ],
            customer_logic=customer_logic,
            monetization_model=monetization_model,
            feature_cluster_details=feature_cluster_details,
            simulation_levers=[SimulationLever.model_validate(item) for item in (payload.get("simulation_levers") or [])],
            uncertainties=[UncertaintyItem.model_validate(item) for item in (payload.get("uncertainties") or [])],
            source_coverage=SourceCoverage.model_validate(payload.get("source_coverage") or {}),
        )
        finalized = self.finalize(understanding)
        finalized.normalized_json = finalized.model_dump()
        return finalized

    def finalize(
        self,
        understanding: ProductUnderstanding,
        *,
        scrape_result: ScrapeResult | None = None,
    ) -> ProductUnderstanding:
        raw_payload = dict(scrape_result.raw_extracted_json if scrape_result else understanding.raw_extracted_json)
        summary_line = truncate_text(
            normalize_text(
                understanding.summary_line
                or understanding.positioning_summary
                or raw_payload.get("meta_description")
                or raw_payload.get("title")
                or ""
            )
            or "Public website signals were limited, so this business model summary is partly inferred.",
            180,
        )
        feature_cluster_details = self._normalize_feature_cluster_details(
            understanding.feature_cluster_details,
            legacy_labels=understanding.feature_clusters,
            raw_payload=raw_payload,
        )
        feature_clusters = [cluster.label for cluster in feature_cluster_details]
        buyer_type = truncate_text(
            understanding.buyer_type
            or self._derive_buyer_type(
                explicit_buyer_type="",
                raw_payload=raw_payload,
                category=understanding.category,
                subcategory=understanding.subcategory,
                legacy_target_signals=understanding.target_customer_signals,
            ),
            120,
        )
        customer_logic = self._normalize_customer_logic(
            understanding.customer_logic,
            raw_payload=raw_payload,
            summary_line=summary_line,
            feature_clusters=feature_clusters,
            category=understanding.category,
        )
        monetization_model = self._normalize_monetization_model(
            understanding=understanding,
            existing=understanding.monetization_model,
            raw_payload=raw_payload,
        )
        confidence_scores = self._normalize_confidence_scores(
            existing=understanding.confidence_scores,
            raw_payload=raw_payload,
            category=understanding.category,
            pricing_model=monetization_model.pricing_model,
            has_customer_logic=bool(customer_logic.why_they_buy or customer_logic.why_they_hesitate),
            has_feature_clusters=bool(feature_cluster_details),
        )
        confidence_score = self._derive_confidence_score(understanding.confidence_score, confidence_scores)
        target_customer_signals = self._derive_target_customer_signals(
            buyer_type=buyer_type,
            raw_payload=raw_payload,
            legacy_signals=understanding.target_customer_signals,
        )
        business_model_signals = self._normalize_business_signals(
            existing=understanding.business_model_signals,
            buyer_type=buyer_type,
            monetization_model=monetization_model,
            category=understanding.category,
            subcategory=understanding.subcategory,
            feature_clusters=feature_clusters,
            raw_payload=raw_payload,
            confidence_scores=confidence_scores,
        )
        uncertainties = self._normalize_uncertainties(
            existing=understanding.uncertainties,
            warnings=understanding.warnings,
            raw_payload=raw_payload,
            company_name=understanding.company_name,
            product_name=understanding.product_name,
            category=understanding.category,
            summary_line=summary_line,
            buyer_type=buyer_type,
            business_model_signals=business_model_signals,
            confidence_score=confidence_score,
        )
        simulation_levers = self._normalize_simulation_levers(
            existing=understanding.simulation_levers,
            business_model_signals=business_model_signals,
            monetization_model=monetization_model,
            feature_clusters=feature_cluster_details,
            confidence_scores=confidence_scores,
            raw_payload=raw_payload,
        )
        source_coverage = self._derive_source_coverage(
            existing=understanding.source_coverage,
            raw_payload=raw_payload,
            product_name=understanding.product_name,
            company_name=understanding.company_name,
            buyer_type=buyer_type,
            monetization_model=monetization_model,
            business_model_signals=business_model_signals,
            feature_clusters=feature_cluster_details,
        )
        review_status = self._derive_review_status(confidence_score, uncertainties)
        warnings = dedupe_preserve_order([item.reason for item in uncertainties if item.needs_user_review])[:6]

        finalized = ProductUnderstanding(
            company_name=truncate_text(understanding.company_name.strip() or "Unknown Company", 120),
            product_name=truncate_text(understanding.product_name.strip() or understanding.company_name.strip() or "Unknown Product", 120),
            category=truncate_text(understanding.category.strip() or "Unknown", 120),
            subcategory=truncate_text(understanding.subcategory.strip() or "General Product Website", 120),
            positioning_summary=summary_line,
            pricing_model=monetization_model.pricing_model,
            feature_clusters=feature_clusters,
            monetization_hypothesis=monetization_model.monetization_hypothesis,
            target_customer_signals=target_customer_signals,
            confidence_score=confidence_score,
            confidence_scores=confidence_scores,
            warnings=warnings,
            raw_extracted_json=raw_payload,
            normalized_json=dict(understanding.normalized_json),
            summary_line=summary_line,
            buyer_type=buyer_type,
            sales_motion=monetization_model.sales_motion,
            review_status=review_status,
            business_model_signals=business_model_signals,
            customer_logic=customer_logic,
            monetization_model=monetization_model,
            feature_cluster_details=feature_cluster_details,
            simulation_levers=simulation_levers,
            uncertainties=uncertainties,
            source_coverage=source_coverage,
        )
        finalized.normalized_json = finalized.model_dump()
        return finalized

    def _derive_company_name(self, scrape_result: ScrapeResult) -> str:
        hostname = urlparse(scrape_result.final_url).hostname or ""
        if scrape_result.title:
            for separator in (" - ", " | ", " — ", ": "):
                if separator in scrape_result.title:
                    return scrape_result.title.split(separator, 1)[0].strip()
        root = hostname.replace("www.", "").split(".")[0]
        return root.replace("-", " ").title() or "Unknown Company"

    def _derive_product_name(self, scrape_result: ScrapeResult, company_name: str) -> str:
        if scrape_result.headings:
            return truncate_text(scrape_result.headings[0], 80)
        return company_name

    def _classify_category(self, raw_text: str) -> tuple[str, str]:
        if any(keyword in raw_text for keyword in ("watch", "movies", "tv shows", "stream", "episodes", "series")):
            return "Consumer Subscription Software", "Video Streaming"
        if any(keyword in raw_text for keyword in ("crm", "pipeline", "sales team", "revenue operations", "renewal")):
            return "B2B Software", "Revenue Operations"
        if any(keyword in raw_text for keyword in ("analytics", "dashboard", "business intelligence", "metrics")):
            return "B2B Software", "Analytics"
        if any(keyword in raw_text for keyword in ("payments", "checkout", "invoice", "billing")):
            return "Fintech", "Payments"
        if any(keyword in raw_text for keyword in ("ai", "copilot", "assistant", "automation", "agent")):
            return "AI Software", "Workflow Automation"
        if any(keyword in raw_text for keyword in ("store", "catalog", "shopping", "commerce")):
            return "Commerce Platform", "E-commerce"
        return "Unknown", "General Product Website"

    def _infer_pricing_model(self, raw_text: str, pricing_clues: list[str]) -> str:
        combined = " ".join(pricing_clues).lower() + " " + raw_text
        if any(keyword in combined for keyword in ("plans", "monthly", "cancel anytime", "subscription", "annual")):
            return "tiered_subscription"
        if "free trial" in combined or ("free" in combined and "upgrade" in combined):
            return "freemium"
        if "contact sales" in combined or "request a demo" in combined:
            return "sales_led_custom_pricing"
        if any(keyword in combined for keyword in ("one-time", "lifetime")):
            return "one_time_purchase"
        return "usage_or_custom"

    def _derive_feature_cluster_labels(self, scrape_result: ScrapeResult, subcategory: str) -> list[str]:
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
        if subcategory == "Revenue Operations":
            return ["workflow automation", "renewal analytics", "customer health visibility", "team reporting"]
        if subcategory == "Analytics":
            return ["dashboarding", "data connectors", "reporting", "alerts", "team collaboration"]
        if subcategory == "Payments":
            return ["checkout", "subscriptions", "payouts", "fraud controls", "developer APIs"]
        extracted = [truncate_text(feature, 60).lower() for feature in features[:6]]
        return extracted or ["core product workflow", "support experience"]

    def _build_summary_line(self, scrape_result: ScrapeResult) -> str:
        if scrape_result.meta_description:
            return truncate_text(scrape_result.meta_description, 180)
        if scrape_result.headings:
            return truncate_text(" ".join(scrape_result.headings[:2]), 180)
        return "The product understanding is inferred from sparse public website signals."

    def _build_monetization_hypothesis(self, pricing_model: str, subcategory: str) -> str:
        if pricing_model == "tiered_subscription":
            if subcategory == "Video Streaming":
                return "Recurring subscription revenue across visible plan tiers."
            return "Recurring subscription revenue with packaging tied to feature depth or team size."
        if pricing_model == "freemium":
            return "Free entry drives evaluation before conversion into paid usage or premium tiers."
        if pricing_model == "sales_led_custom_pricing":
            return "Contract revenue from negotiated enterprise packages and multi-stakeholder deals."
        if pricing_model == "one_time_purchase":
            return "Upfront purchase revenue with optional support or add-on expansion."
        return "Revenue likely depends on recurring usage or negotiated pricing that is not public."

    def _derive_job_to_be_done(self, scrape_result: ScrapeResult, summary_line: str) -> str:
        if scrape_result.headings:
            return truncate_text(scrape_result.headings[0], 140)
        return truncate_text(summary_line, 140)

    def _derive_why_they_buy(self, scrape_result: ScrapeResult) -> list[str]:
        candidates = dedupe_preserve_order(scrape_result.feature_clues + scrape_result.paragraphs)
        return [truncate_text(item, 110) for item in candidates[:3]] or ["Centralize a workflow that is currently fragmented."]

    def _derive_why_they_hesitate(self, scrape_result: ScrapeResult) -> list[str]:
        text = " ".join(scrape_result.paragraphs + scrape_result.headings).lower()
        reasons: list[str] = []
        if not scrape_result.pricing_clues:
            reasons.append("Pricing is not obvious before a sales conversation.")
        if any(keyword in text for keyword in ("security", "compliance", "enterprise", "integration", "migration")):
            reasons.append("Implementation risk may feel non-trivial during rollout.")
        if not reasons:
            reasons.append("Proof of ROI likely matters before the buyer commits.")
        return reasons[:3]

    def _derive_replacements(self, scrape_result: ScrapeResult, category: str) -> list[str]:
        if category == "B2B Software":
            return ["spreadsheets", "internal workflows", "point tools"]
        if category == "Consumer Subscription Software":
            return ["cable bundles", "competing subscriptions"]
        return ["manual workflow", "category alternatives"]

    def _normalize_customer_logic(
        self,
        existing: CustomerLogic,
        *,
        raw_payload: dict,
        summary_line: str,
        feature_clusters: list[str],
        category: str,
    ) -> CustomerLogic:
        core_job = truncate_text(
            existing.core_job_to_be_done.strip()
            or summary_line
            or (feature_clusters[0] if feature_clusters else "")
            or "Clarify the core job customers hire this product to do.",
            160,
        )
        why_buy = self._coerce_string_list(existing.why_they_buy)[:4]
        why_hesitate = self._coerce_string_list(existing.why_they_hesitate)[:4]
        replacements = self._coerce_string_list(existing.what_it_replaces)[:4]

        if not why_buy:
            why_buy = self._derive_benefit_reasons(raw_payload, feature_clusters)
        if not why_hesitate:
            why_hesitate = self._derive_hesitation_reasons(raw_payload, category)
        if not replacements:
            replacements = self._derive_replacement_candidates(raw_payload, category)

        return CustomerLogic(
            core_job_to_be_done=core_job,
            why_they_buy=why_buy,
            why_they_hesitate=why_hesitate,
            what_it_replaces=replacements,
        )

    def _normalize_monetization_model(
        self,
        *,
        understanding: ProductUnderstanding,
        existing: MonetizationModel,
        raw_payload: dict,
    ) -> MonetizationModel:
        pricing_model = normalize_text(existing.pricing_model or understanding.pricing_model or "usage_or_custom")
        pricing_visibility = normalize_text(
            existing.pricing_visibility or self._derive_pricing_visibility(raw_payload, pricing_model)
        )
        sales_motion = truncate_text(
            existing.sales_motion.strip()
            or understanding.sales_motion.strip()
            or self._derive_sales_motion(raw_payload, pricing_model),
            120,
        )
        monetization_hypothesis = truncate_text(
            existing.monetization_hypothesis.strip()
            or understanding.monetization_hypothesis.strip()
            or self._build_monetization_hypothesis(pricing_model, understanding.subcategory),
            220,
        )
        return MonetizationModel(
            pricing_visibility=pricing_visibility,
            pricing_model=pricing_model,
            monetization_hypothesis=monetization_hypothesis,
            sales_motion=sales_motion,
        )

    def _normalize_confidence_scores(
        self,
        *,
        existing: dict[str, float],
        raw_payload: dict,
        category: str,
        pricing_model: str,
        has_customer_logic: bool,
        has_feature_clusters: bool,
    ) -> dict[str, float]:
        defaults = self._default_confidence_scores(
            raw_payload=raw_payload,
            category=category,
            pricing_model=pricing_model,
            has_customer_logic=has_customer_logic,
            has_feature_clusters=has_feature_clusters,
        )
        merged = {**defaults, **{key: self._clamp(float(value), 0.0, 1.0) for key, value in existing.items()}}
        return merged

    def _default_confidence_scores(
        self,
        *,
        raw_payload: dict,
        category: str,
        pricing_model: str,
        has_customer_logic: bool,
        has_feature_clusters: bool,
    ) -> dict[str, float]:
        pricing_clues = raw_payload.get("pricing_clues") or []
        audience_candidates = raw_payload.get("audience_candidates") or []
        buttons = " ".join(raw_payload.get("buttons") or []).lower()
        return {
            "company_name": 0.9 if raw_payload.get("title") else 0.6,
            "summary_line": 0.88 if raw_payload.get("meta_description") or raw_payload.get("headings") else 0.58,
            "category": 0.84 if category != "Unknown" else 0.45,
            "buyer_type": 0.82 if audience_candidates else 0.56,
            "customer_logic": 0.78 if has_customer_logic else 0.58,
            "pricing_model": 0.86 if pricing_clues else 0.44,
            "monetization_model": 0.84 if pricing_clues or any(token in buttons for token in ("pricing", "demo", "contact sales")) else 0.52,
            "feature_clusters": 0.84 if has_feature_clusters else 0.5,
            "business_model_signals": 0.76,
            "simulation_levers": 0.7,
        }

    def _derive_confidence_score(self, existing: float, confidence_scores: dict[str, float]) -> float:
        if existing:
            return self._clamp(existing, 0.0, 1.0)
        if not confidence_scores:
            return 0.6
        return round(sum(confidence_scores.values()) / len(confidence_scores), 2)

    def _derive_target_customer_signals(
        self,
        *,
        buyer_type: str,
        raw_payload: dict,
        legacy_signals: list[str],
    ) -> list[str]:
        candidates = self._coerce_string_list(legacy_signals)
        candidates.extend(self._coerce_string_list(raw_payload.get("audience_candidates") or []))
        if buyer_type:
            candidates.insert(0, buyer_type)
        return dedupe_preserve_order([truncate_text(item, 120) for item in candidates])[:5] or ["General product evaluators"]

    def _normalize_business_signals(
        self,
        *,
        existing: list[BusinessModelSignal],
        buyer_type: str,
        monetization_model: MonetizationModel,
        category: str,
        subcategory: str,
        feature_clusters: list[str],
        raw_payload: dict,
        confidence_scores: dict[str, float],
    ) -> list[BusinessModelSignal]:
        explicit = {signal.key: signal for signal in existing}
        derived = self._derived_signal_map(
            buyer_type=buyer_type,
            monetization_model=monetization_model,
            category=category,
            subcategory=subcategory,
            feature_clusters=feature_clusters,
            raw_payload=raw_payload,
            confidence_scores=confidence_scores,
        )
        normalized: list[BusinessModelSignal] = []
        for key in SIGNAL_ORDER:
            if key in explicit:
                signal = explicit[key]
                normalized.append(
                    BusinessModelSignal(
                        key=key,
                        label=SIGNAL_LABELS[key],
                        value=truncate_text(signal.value, 120),
                        score_1_to_5=self._normalize_signal_score(signal.score_1_to_5),
                        confidence=self._clamp(signal.confidence, 0.0, 1.0),
                        editable=signal.editable,
                    )
                )
                continue
            normalized.append(derived[key])
        return normalized

    def _derived_signal_map(
        self,
        *,
        buyer_type: str,
        monetization_model: MonetizationModel,
        category: str,
        subcategory: str,
        feature_clusters: list[str],
        raw_payload: dict,
        confidence_scores: dict[str, float],
    ) -> dict[str, BusinessModelSignal]:
        text = " ".join(
            self._coerce_string_list(raw_payload.get("headings") or [])
            + self._coerce_string_list(raw_payload.get("paragraphs") or [])
            + self._coerce_string_list(raw_payload.get("buttons") or [])
            + feature_clusters
        ).lower()
        deployment_score = 1
        if category in {"B2B Software", "AI Software", "Fintech"}:
            deployment_score += 1
        if monetization_model.sales_motion.lower().startswith("demo-led") or monetization_model.sales_motion.lower().startswith("enterprise"):
            deployment_score += 1
        if any(keyword in text for keyword in ("integration", "api", "workflow", "automation", "platform", "migration")):
            deployment_score += 1
        if any(keyword in text for keyword in ("compliance", "security", "healthcare", "insurance", "audit", "procurement")):
            deployment_score += 1
        deployment_score = min(5, deployment_score)

        time_to_value_score = max(1, min(5, deployment_score - (1 if monetization_model.pricing_visibility == "high" else 0)))
        workflow_criticality_score = min(
            5,
            2
            + (1 if category in {"B2B Software", "AI Software", "Fintech"} else 0)
            + (1 if any(keyword in text for keyword in ("revenue", "payments", "operations", "support", "renewal", "customer health")) else 0)
            + (1 if any(keyword in text for keyword in ("compliance", "security", "risk", "accuracy")) else 0),
        )
        compliance_score = min(
            5,
            1 + sum(
                1
                for keyword in ("compliance", "security", "soc 2", "hipaa", "gdpr", "audit", "healthcare", "insurance", "fintech")
                if keyword in text
            ),
        )
        switching_score = min(
            5,
            1
            + (1 if deployment_score >= 4 else 0)
            + (1 if workflow_criticality_score >= 4 else 0)
            + (1 if monetization_model.sales_motion.lower().startswith(("demo-led", "enterprise")) else 0)
            + (1 if any(keyword in text for keyword in ("integration", "workflow", "analytics", "historical data")) else 0),
        )
        expansion_score = min(
            5,
            1
            + (1 if category in {"B2B Software", "AI Software"} else 0)
            + (1 if any(keyword in text for keyword in ("team", "enterprise", "multi", "cross-functional")) else 0)
            + (1 if len(feature_clusters) >= 4 else 0)
            + (1 if monetization_model.pricing_model in {"tiered_subscription", "sales_led_custom_pricing", "freemium"} else 0),
        )

        pricing_visibility_score = {"high": 5, "medium": 3, "low": 2, "none": 1}.get(monetization_model.pricing_visibility.lower(), 2)
        monetization_style = self._monetization_style(monetization_model.pricing_model)

        return {
            "buyer_type": BusinessModelSignal(
                key="buyer_type",
                label=SIGNAL_LABELS["buyer_type"],
                value=truncate_text(buyer_type or "General business evaluators", 120),
                confidence=confidence_scores.get("buyer_type", 0.6),
                editable=True,
            ),
            "sales_motion": BusinessModelSignal(
                key="sales_motion",
                label=SIGNAL_LABELS["sales_motion"],
                value=truncate_text(monetization_model.sales_motion, 120),
                confidence=confidence_scores.get("monetization_model", 0.6),
                editable=True,
            ),
            "pricing_visibility": BusinessModelSignal(
                key="pricing_visibility",
                label=SIGNAL_LABELS["pricing_visibility"],
                value=monetization_model.pricing_visibility.title(),
                score_1_to_5=pricing_visibility_score,
                confidence=confidence_scores.get("pricing_model", 0.6),
                editable=True,
            ),
            "deployment_complexity": self._scale_signal(
                key="deployment_complexity",
                score=deployment_score,
                labels={1: "Very low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very high"},
                confidence=confidence_scores.get("business_model_signals", 0.6),
            ),
            "time_to_value": self._scale_signal(
                key="time_to_value",
                score=time_to_value_score,
                labels={1: "Immediate", 2: "Fast", 3: "Moderate", 4: "Slow", 5: "Long"},
                confidence=confidence_scores.get("business_model_signals", 0.6),
            ),
            "workflow_criticality": self._scale_signal(
                key="workflow_criticality",
                score=workflow_criticality_score,
                labels={1: "Low", 2: "Light", 3: "Moderate", 4: "High", 5: "Mission-critical"},
                confidence=confidence_scores.get("business_model_signals", 0.6),
            ),
            "compliance_sensitivity": self._scale_signal(
                key="compliance_sensitivity",
                score=compliance_score,
                labels={1: "Low", 2: "Limited", 3: "Moderate", 4: "High", 5: "Very high"},
                confidence=confidence_scores.get("business_model_signals", 0.6),
            ),
            "switching_friction": self._scale_signal(
                key="switching_friction",
                score=switching_score,
                labels={1: "Low", 2: "Low-medium", 3: "Medium", 4: "High", 5: "Very high"},
                confidence=confidence_scores.get("business_model_signals", 0.6),
            ),
            "expansion_potential": self._scale_signal(
                key="expansion_potential",
                score=expansion_score,
                labels={1: "Low", 2: "Limited", 3: "Moderate", 4: "High", 5: "Very high"},
                confidence=confidence_scores.get("business_model_signals", 0.6),
            ),
            "monetization_style": BusinessModelSignal(
                key="monetization_style",
                label=SIGNAL_LABELS["monetization_style"],
                value=monetization_style,
                confidence=confidence_scores.get("monetization_model", 0.6),
                editable=True,
            ),
        }

    def _scale_signal(
        self,
        *,
        key: str,
        score: int,
        labels: dict[int, str],
        confidence: float,
    ) -> BusinessModelSignal:
        normalized_score = self._normalize_signal_score(score) or 3
        return BusinessModelSignal(
            key=key,
            label=SIGNAL_LABELS[key],
            value=labels[normalized_score],
            score_1_to_5=normalized_score,
            confidence=self._clamp(confidence, 0.0, 1.0),
            editable=True,
        )

    def _normalize_uncertainties(
        self,
        *,
        existing: list[UncertaintyItem],
        warnings: list[str],
        raw_payload: dict,
        company_name: str,
        product_name: str,
        category: str,
        summary_line: str,
        buyer_type: str,
        business_model_signals: list[BusinessModelSignal],
        confidence_score: float,
    ) -> list[UncertaintyItem]:
        if existing:
            normalized = [
                UncertaintyItem(
                    key=item.key or self._slugify(item.label),
                    label=truncate_text(item.label, 80),
                    reason=truncate_text(item.reason, 180),
                    severity=item.severity,
                    needs_user_review=item.needs_user_review,
                )
                for item in existing
            ]
            return normalized[:6]

        derived: list[UncertaintyItem] = []
        pricing_clues = raw_payload.get("pricing_clues") or []
        audience_candidates = raw_payload.get("audience_candidates") or []
        text = " ".join(self._coerce_string_list(raw_payload.get("paragraphs") or [])).lower()

        if not pricing_clues:
            derived.append(
                UncertaintyItem(
                    key="pricing_visibility",
                    label="Pricing visibility",
                    reason="Pricing is not visible on the public website, so willingness-to-pay and packaging assumptions are inferred.",
                    severity="high",
                    needs_user_review=True,
                )
            )
        if normalize_text(product_name).lower() == normalize_text(company_name).lower():
            derived.append(
                UncertaintyItem(
                    key="product_name",
                    label="Product naming",
                    reason="The public site does not clearly separate product name from company name.",
                    severity="medium",
                    needs_user_review=True,
                )
            )
        if not audience_candidates and buyer_type:
            derived.append(
                UncertaintyItem(
                    key="buyer_type",
                    label="Buyer type",
                    reason="Buyer type is inferred from positioning language rather than explicit audience statements.",
                    severity="medium",
                    needs_user_review=True,
                )
            )
        if not any(keyword in text for keyword in ("implementation", "deploy", "migration", "integration", "api")):
            derived.append(
                UncertaintyItem(
                    key="deployment_complexity",
                    label="Deployment complexity",
                    reason="Deployment complexity is inferred from product category and workflow language, not from explicit rollout details.",
                    severity="medium",
                    needs_user_review=False,
                )
            )
        if category == "Unknown" or confidence_score < 0.68:
            derived.append(
                UncertaintyItem(
                    key="business_category",
                    label="Category fit",
                    reason="The crawl had limited evidence for a precise category or product positioning.",
                    severity="high",
                    needs_user_review=True,
                )
            )
        if not raw_payload.get("headings") and not raw_payload.get("paragraphs"):
            derived.append(
                UncertaintyItem(
                    key="source_coverage",
                    label="Sparse source coverage",
                    reason="The public page exposed very little descriptive text, which reduced interpretation confidence.",
                    severity="high",
                    needs_user_review=True,
                )
            )
        for warning in warnings:
            derived.append(
                UncertaintyItem(
                    key=self._slugify(warning),
                    label=truncate_text(warning, 48),
                    reason=truncate_text(warning, 180),
                    severity="medium",
                    needs_user_review=True,
                )
            )
        deduped: list[UncertaintyItem] = []
        seen: set[str] = set()
        for item in derived:
            if item.key in seen:
                continue
            seen.add(item.key)
            deduped.append(item)
        return deduped[:6]

    def _normalize_simulation_levers(
        self,
        *,
        existing: list[SimulationLever],
        business_model_signals: list[BusinessModelSignal],
        monetization_model: MonetizationModel,
        feature_clusters: list[FeatureCluster],
        confidence_scores: dict[str, float],
        raw_payload: dict,
    ) -> list[SimulationLever]:
        if existing:
            return [
                SimulationLever(
                    key=lever.key or self._slugify(lever.label),
                    label=truncate_text(lever.label, 60),
                    why_it_matters=truncate_text(lever.why_it_matters, 180),
                    confidence=self._clamp(lever.confidence, 0.0, 1.0),
                    editable=lever.editable,
                )
                for lever in existing[:6]
            ]

        signal_map = {signal.key: signal for signal in business_model_signals}
        derived: list[SimulationLever] = []

        def add(key: str, label: str, why: str, confidence_key: str) -> None:
            if any(item.key == key for item in derived):
                return
            derived.append(
                SimulationLever(
                    key=key,
                    label=label,
                    why_it_matters=truncate_text(why, 180),
                    confidence=confidence_scores.get(confidence_key, 0.66),
                    editable=True,
                )
            )

        add(
            "pricing",
            "Pricing",
            "Price changes will directly affect conversion, retention, and expansion if buyers are comparing value closely.",
            "pricing_model",
        )

        if monetization_model.pricing_model in {"tiered_subscription", "sales_led_custom_pricing", "freemium"}:
            add(
                "packaging",
                "Packaging",
                "Plan structure and tier boundaries shape perceived value, expansion paths, and deal complexity.",
                "monetization_model",
            )

        if (signal_map.get("deployment_complexity") and (signal_map["deployment_complexity"].score_1_to_5 or 1) >= 4):
            add(
                "deployment_effort",
                "Deployment Effort",
                "Rollout friction can slow activation and weaken scenario uptake even when value is clear.",
                "business_model_signals",
            )
            add(
                "onboarding_time",
                "Onboarding Time",
                "Time-to-value changes proof requirements and the speed at which buyers feel confident enough to expand.",
                "business_model_signals",
            )

        feature_text = " ".join(cluster.label.lower() for cluster in feature_clusters)
        if any(keyword in feature_text for keyword in ("automation", "workflow", "agent")):
            add(
                "automation_coverage",
                "Automation Coverage",
                "Depth of workflow coverage changes the size of the before-vs-after value story.",
                "feature_clusters",
            )
        if any(keyword in feature_text for keyword in ("integration", "api", "connector", "data")) or any(
            keyword in " ".join(self._coerce_string_list(raw_payload.get("paragraphs") or [])).lower()
            for keyword in ("integration", "api", "connector", "data sync")
        ):
            add(
                "integration_depth",
                "Integration Depth",
                "Connected workflows increase switching friction and determine whether the product becomes operationally central.",
                "feature_clusters",
            )
        if (signal_map.get("compliance_sensitivity") and (signal_map["compliance_sensitivity"].score_1_to_5 or 1) >= 4):
            add(
                "compliance_readiness",
                "Compliance Readiness",
                "Security and compliance readiness can determine who is allowed to buy and how long deals take to close.",
                "business_model_signals",
            )
        if monetization_model.pricing_visibility.lower() in {"low", "none"} or monetization_model.sales_motion.lower().startswith(("demo-led", "enterprise")):
            add(
                "proof_case_studies",
                "Proof and Case Studies",
                "When pricing and ROI are not self-evident, trust signals become a major lever in evaluation and expansion.",
                "monetization_model",
            )
        if len(feature_clusters) >= 3:
            add(
                "feature_breadth",
                "Feature Breadth",
                "Breadth influences replacement value, bundling logic, and how many teams can justify the product internally.",
                "feature_clusters",
            )
        return derived[:6]

    def _derive_source_coverage(
        self,
        *,
        existing: SourceCoverage,
        raw_payload: dict,
        product_name: str,
        company_name: str,
        buyer_type: str,
        monetization_model: MonetizationModel,
        business_model_signals: list[BusinessModelSignal],
        feature_clusters: list[FeatureCluster],
    ) -> SourceCoverage:
        if existing.fields_observed_explicitly or existing.fields_inferred or existing.fields_missing:
            return existing

        observed: list[str] = []
        inferred: list[str] = []
        missing: list[str] = []

        if raw_payload.get("title"):
            observed.append("Company name")
        if product_name and normalize_text(product_name).lower() != normalize_text(company_name).lower():
            observed.append("Product name")
        else:
            missing.append("Distinct product name")
        if raw_payload.get("meta_description") or raw_payload.get("headings"):
            observed.append("Product summary")
        if raw_payload.get("audience_candidates"):
            observed.append("Buyer audience")
        else:
            inferred.append("Buyer type")
        if raw_payload.get("pricing_clues"):
            observed.append("Pricing visibility")
            observed.append("Pricing model")
        else:
            missing.append("Public pricing")
            inferred.append("Pricing model")
        if any(token in " ".join(self._coerce_string_list(raw_payload.get("buttons") or [])).lower() for token in ("demo", "contact sales", "book")):
            observed.append("Sales motion")
        else:
            inferred.append("Sales motion")
        if feature_clusters:
            observed.append("Feature clusters")
        if any(signal.key in {"deployment_complexity", "time_to_value", "workflow_criticality", "switching_friction"} for signal in business_model_signals):
            inferred.extend(["Deployment complexity", "Time-to-value", "Workflow criticality", "Switching friction"])
        if monetization_model.pricing_visibility.lower() in {"low", "none"}:
            missing.append("Pricing detail")

        return SourceCoverage(
            fields_observed_explicitly=dedupe_preserve_order(observed),
            fields_inferred=dedupe_preserve_order(inferred),
            fields_missing=dedupe_preserve_order(missing),
        )

    def _derive_review_status(self, confidence_score: float, uncertainties: list[UncertaintyItem]) -> str:
        if confidence_score < 0.74:
            return "needs_review"
        if any(item.needs_user_review and item.severity in {"high", "medium"} for item in uncertainties):
            return "needs_review"
        return "ready"

    def _derive_buyer_type(
        self,
        *,
        explicit_buyer_type: str,
        raw_payload: dict,
        category: str,
        subcategory: str,
        legacy_target_signals: list[str],
    ) -> str:
        if explicit_buyer_type.strip():
            return truncate_text(explicit_buyer_type.strip(), 120)

        audience_text = " ".join(
            self._coerce_string_list(legacy_target_signals)
            + self._coerce_string_list(raw_payload.get("audience_candidates") or [])
            + self._coerce_string_list(raw_payload.get("headings") or [])
            + self._coerce_string_list(raw_payload.get("paragraphs") or [])
        ).lower()
        if any(keyword in audience_text for keyword in ("revenue", "customer success", "renewal", "revops")):
            return "Revenue and customer success teams"
        if any(keyword in audience_text for keyword in ("operations", "back office", "portal", "workflow")):
            return "Operations teams"
        if any(keyword in audience_text for keyword in ("developer", "engineering", "api")):
            return "Developer and platform teams"
        if any(keyword in audience_text for keyword in ("product team", "support team", "feedback")):
            return "Product and support teams"
        if subcategory == "Video Streaming":
            return "Household and individual viewers"
        if category == "B2B Software":
            return "Cross-functional business teams"
        return "General digital product buyers"

    def _derive_pricing_visibility(self, raw_payload: dict, pricing_model: str) -> str:
        pricing_clues = self._coerce_string_list(raw_payload.get("pricing_clues") or [])
        text = " ".join(pricing_clues).lower()
        if any(symbol in text for symbol in ("$", "₹", "€", "£")) or any(token in text for token in ("/month", "monthly", "annual", "yearly")):
            return "high"
        if pricing_clues:
            return "medium"
        if pricing_model == "sales_led_custom_pricing":
            return "low"
        return "low"

    def _derive_sales_motion(self, raw_payload: dict, pricing_model: str) -> str:
        button_text = " ".join(self._coerce_string_list(raw_payload.get("buttons") or [])).lower()
        if any(token in button_text for token in ("contact sales", "request demo", "book demo", "talk to sales")):
            return "Demo-led / enterprise sales"
        if pricing_model == "sales_led_custom_pricing":
            return "Demo-led / enterprise sales"
        if pricing_model == "freemium":
            return "Product-led self-serve"
        if any(token in button_text for token in ("get started", "start free", "sign up")):
            return "Product-led self-serve"
        if pricing_model == "tiered_subscription":
            return "Self-serve plans"
        return "Hybrid / assisted sales"

    def _monetization_style(self, pricing_model: str) -> str:
        mapping = {
            "tiered_subscription": "Tiered subscription",
            "freemium": "Freemium conversion",
            "sales_led_custom_pricing": "Contract revenue",
            "one_time_purchase": "One-time purchase",
            "usage_or_custom": "Usage-based or custom",
        }
        return mapping.get(pricing_model, "Usage-based or custom")

    def _normalize_feature_cluster_details(
        self,
        existing: list[FeatureCluster],
        *,
        legacy_labels: list[str],
        raw_payload: dict,
    ) -> list[FeatureCluster]:
        normalized = self._coerce_feature_cluster_details(existing)
        if not normalized:
            normalized = self._coerce_feature_cluster_details(legacy_labels)
        if not normalized:
            candidates = self._coerce_string_list(raw_payload.get("feature_candidates") or raw_payload.get("headings") or [])
            normalized = self._coerce_feature_cluster_details(candidates[:6])
        if not normalized:
            normalized = [
                FeatureCluster(key="core-workflow", label="Core workflow", importance="high"),
            ]

        normalized.sort(key=lambda item: (IMPORTANCE_ORDER.get(item.importance, 3), item.label.lower()))
        return normalized[:6]

    def _coerce_feature_cluster_details(self, values: list[FeatureCluster] | list[dict] | list[str]) -> list[FeatureCluster]:
        normalized: list[FeatureCluster] = []
        for index, value in enumerate(values):
            if isinstance(value, FeatureCluster):
                normalized.append(
                    FeatureCluster(
                        key=value.key or self._slugify(value.label),
                        label=truncate_text(value.label, 60),
                        importance=value.importance,
                        description=truncate_text(value.description, 140) if value.description else None,
                    )
                )
                continue
            if isinstance(value, dict):
                label = str(value.get("label") or "").strip()
                if not label:
                    continue
                normalized.append(
                    FeatureCluster(
                        key=str(value.get("key") or self._slugify(label)),
                        label=truncate_text(label, 60),
                        importance=str(value.get("importance") or ("high" if index < 2 else "medium" if index < 4 else "low")),
                        description=truncate_text(str(value.get("description") or "").strip(), 140) or None,
                    )
                )
                continue
            label = str(value).strip()
            if not label:
                continue
            normalized.append(
                FeatureCluster(
                    key=self._slugify(label),
                    label=truncate_text(label, 60),
                    importance="high" if index < 2 else "medium" if index < 4 else "low",
                )
            )
        return normalized

    def _extract_feature_cluster_labels(self, feature_cluster_details: list[FeatureCluster], fallback: object) -> list[str]:
        if feature_cluster_details:
            return [cluster.label for cluster in feature_cluster_details]
        return self._coerce_string_list(fallback if isinstance(fallback, list) else [])

    def _derive_benefit_reasons(self, raw_payload: dict, feature_clusters: list[str]) -> list[str]:
        reasons = self._coerce_string_list(raw_payload.get("headings") or [])[:2]
        reasons.extend(feature_clusters[:2])
        reasons = dedupe_preserve_order(reasons)
        return [truncate_text(item, 110) for item in reasons[:3]] or ["Reduce manual effort in a key workflow."]

    def _derive_hesitation_reasons(self, raw_payload: dict, category: str) -> list[str]:
        text = " ".join(self._coerce_string_list(raw_payload.get("paragraphs") or [])).lower()
        reasons: list[str] = []
        if not raw_payload.get("pricing_clues"):
            reasons.append("Pricing is not explicit before evaluation.")
        if any(keyword in text for keyword in ("integration", "migration", "workflow", "security")):
            reasons.append("Implementation effort may feel hard to size upfront.")
        if category in {"B2B Software", "AI Software"}:
            reasons.append("Buyers will likely need proof before rolling this out broadly.")
        return dedupe_preserve_order(reasons)[:3] or ["The value case may require more explicit proof."]

    def _derive_replacement_candidates(self, raw_payload: dict, category: str) -> list[str]:
        text = " ".join(self._coerce_string_list(raw_payload.get("paragraphs") or [])).lower()
        replacements: list[str] = []
        if any(keyword in text for keyword in ("manual", "spreadsheet", "handoff")):
            replacements.append("manual workflows")
            replacements.append("spreadsheets")
        if category in {"B2B Software", "AI Software"}:
            replacements.append("point tools")
            replacements.append("internal scripts")
        if category == "Consumer Subscription Software":
            replacements.append("competing subscriptions")
        return dedupe_preserve_order(replacements)[:4] or ["category alternatives"]

    def _normalize_signal_score(self, value: int | None) -> int | None:
        if value is None:
            return None
        return max(1, min(5, int(value)))

    def _coerce_string_list(self, values: list | tuple) -> list[str]:
        cleaned = [truncate_text(normalize_text(str(value)), 180) for value in values if normalize_text(str(value))]
        return dedupe_preserve_order(cleaned)

    def _slugify(self, value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", normalize_text(value).lower()).strip("-")
        return normalized or "item"

    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        return round(min(maximum, max(minimum, float(value))), 4)
