from fastapi.testclient import TestClient

from app.tests.factories import sample_generated_icps, sample_generated_scenarios, sample_product_understanding, sample_scrape_result


def _stub_generation(monkeypatch) -> None:
    async def fake_scrape(self, normalized_url: str):
        return sample_scrape_result(normalized_url)

    async def fake_understanding(self, scrape_result, *, user_identifier: str):
        return sample_product_understanding()

    async def fake_icps(self, understanding, *, user_identifier: str):
        return sample_generated_icps()

    async def fake_scenarios(self, understanding, icps, *, user_identifier: str):
        return sample_generated_scenarios()

    monkeypatch.setattr("app.services.scraper_service.ScraperService.scrape", fake_scrape)
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_product_understanding",
        fake_understanding,
    )
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_icps",
        fake_icps,
    )
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_scenarios",
        fake_scenarios,
    )


def test_create_and_progress_analysis_step_by_step(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    _stub_generation(monkeypatch)

    create_response = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False, "force_refresh": False},
        headers=auth_headers,
    )
    assert create_response.status_code == 202
    analysis_id = create_response.json()["analysis"]["id"]

    detail = client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers).json()
    assert detail["status"] == "awaiting_review"
    assert detail["current_stage"] == "product_understanding"
    assert detail["extracted_product_data"]["company_name"] == "Acme"
    assert detail["icp_profiles"] == []
    assert detail["scenarios"] == []

    icp_response = client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "product_understanding", "run_async": False},
        headers=auth_headers,
    )
    assert icp_response.status_code == 200
    icp_detail = icp_response.json()
    assert icp_detail["current_stage"] == "icp_profiles"
    assert icp_detail["status"] == "awaiting_review"
    assert len(icp_detail["icp_profiles"]) == 3
    assert icp_detail["icp_profiles"][0]["view_model"]["behavioral_signals"][0]["signal_key"] == "priceSensitivity"
    assert icp_detail["scenarios"] == []

    scenario_response = client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "icp_profiles", "run_async": False},
        headers=auth_headers,
    )
    assert scenario_response.status_code == 200
    scenario_detail = scenario_response.json()
    assert scenario_detail["current_stage"] == "scenarios"
    assert scenario_detail["status"] == "awaiting_review"
    assert len(scenario_detail["scenarios"]) == 3
    assert scenario_detail["scenarios"][0]["review_view"]["expected_impact"][0]["metric_key"] == "revenue"
    assert scenario_detail["scenarios"][0]["review_view"]["recommendation"]["priority_rank"] >= 1

    decision_flow_response = client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "scenarios", "run_async": False},
        headers=auth_headers,
    )
    assert decision_flow_response.status_code == 200
    decision_flow_detail = decision_flow_response.json()
    assert decision_flow_detail["current_stage"] == "decision_flow"
    assert decision_flow_detail["status"] == "awaiting_review"


def test_product_edit_reopens_analysis_and_clears_downstream(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    _stub_generation(monkeypatch)

    create_response = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False},
        headers=auth_headers,
    )
    analysis_id = create_response.json()["analysis"]["id"]

    client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "product_understanding", "run_async": False},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "icp_profiles", "run_async": False},
        headers=auth_headers,
    )

    product_update = client.patch(
        f"/api/v1/analyses/{analysis_id}/product-understanding",
        json={
            "company_name": "Acme",
            "product_name": "Acme Growth Platform",
            "category": "B2B Software",
            "subcategory": "Revenue Operations",
            "positioning_summary": "Updated summary from the user.",
            "pricing_model": "sales_led_custom_pricing",
            "feature_clusters": ["workflow automation", "renewal analytics"],
            "monetization_hypothesis": "Annual contracts for operations-heavy teams.",
            "target_customer_signals": ["revops leaders", "customer success leaders"],
            "warnings": [],
        },
        headers=auth_headers,
    )

    assert product_update.status_code == 200
    detail = product_update.json()
    assert detail["current_stage"] == "product_understanding"
    assert detail["extracted_product_data"]["is_user_edited"] is True
    assert detail["icp_profiles"] == []
    assert detail["scenarios"] == []
    assert detail["simulation_runs"] == []


def test_scenario_edit_and_simulation_unlock_final_review(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    _stub_generation(monkeypatch)

    create_response = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False},
        headers=auth_headers,
    )
    analysis_id = create_response.json()["analysis"]["id"]

    client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "product_understanding", "run_async": False},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "icp_profiles", "run_async": False},
        headers=auth_headers,
    )
    scenario_detail = client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "scenarios", "run_async": False},
        headers=auth_headers,
    ).json()

    scenario_id = scenario_detail["scenarios"][0]["id"]
    scenario_update = client.patch(
        f"/api/v1/analyses/{analysis_id}/scenarios/{scenario_id}",
        json={
            "title": "Increase annual contract price by 12%",
            "scenario_type": "pricing_increase",
            "description": "User-adjusted scenario.",
            "input_parameters": {"price_change_percent": 12, "current_price_estimate": 1200},
        },
        headers=auth_headers,
    )
    assert scenario_update.status_code == 200
    assert scenario_update.json()["current_stage"] == "scenarios"

    decision_flow = client.post(
        f"/api/v1/analyses/{analysis_id}/workflow/proceed",
        json={"expected_stage": "scenarios", "run_async": False},
        headers=auth_headers,
    )
    assert decision_flow.status_code == 200

    rerun = client.post(
        f"/api/v1/analyses/{analysis_id}/scenarios/{scenario_id}/simulate",
        json={"input_overrides": {}, "run_version": "1"},
        headers=auth_headers,
    )
    assert rerun.status_code == 200

    final_detail = client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers).json()
    assert final_detail["status"] == "completed"
    assert final_detail["current_stage"] == "final_review"
    assert len(final_detail["simulation_runs"]) == 1


def test_repeated_submission_reuses_existing_analysis(client: TestClient, auth_headers: dict[str, str], monkeypatch) -> None:
    _stub_generation(monkeypatch)

    first = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False},
        headers=auth_headers,
    )
    second = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False},
        headers=auth_headers,
    )
    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["reused"] is True
    assert second.json()["analysis"]["id"] == first.json()["analysis"]["id"]


def test_force_refresh_creates_a_new_analysis(client: TestClient, auth_headers: dict[str, str], monkeypatch) -> None:
    _stub_generation(monkeypatch)

    first = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False},
        headers=auth_headers,
    )
    second = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False, "force_refresh": True},
        headers=auth_headers,
    )

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["reused"] is False
    assert second.json()["analysis"]["id"] != first.json()["analysis"]["id"]


def test_create_analysis_requires_openai_key(client: TestClient, auth_headers: dict[str, str], test_settings) -> None:
    test_settings.openai_api_key = None

    response = client.post(
        "/api/v1/analyses",
        json={"url": "https://missing-key.example/", "run_async": False},
        headers=auth_headers,
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "openai_not_configured"


def test_invalid_url_is_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/analyses",
        json={"url": "ftp://bad.example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_bare_domain_is_accepted_and_normalized(client: TestClient, auth_headers: dict[str, str], monkeypatch) -> None:
    _stub_generation(monkeypatch)

    response = client.post(
        "/api/v1/analyses",
        json={"url": "incommon.ai", "run_async": False},
        headers=auth_headers,
    )

    assert response.status_code == 202
    assert response.json()["analysis"]["normalized_url"] == "http://incommon.ai/"
