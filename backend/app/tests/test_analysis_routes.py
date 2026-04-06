from app.tests.factories import sample_generated_icps, sample_generated_scenarios, sample_product_understanding, sample_scrape_result
from fastapi.testclient import TestClient


def test_create_and_fetch_analysis(client: TestClient, auth_headers: dict[str, str], monkeypatch) -> None:
    async def fake_scrape(self, normalized_url: str):
        return sample_scrape_result(normalized_url)

    async def fake_understanding(self, scrape_result, *, user_identifier: str):
        return sample_product_understanding()

    async def fake_artifacts(self, understanding, *, user_identifier: str):
        return sample_generated_icps(), sample_generated_scenarios()

    monkeypatch.setattr("app.services.scraper_service.ScraperService.scrape", fake_scrape)
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_product_understanding",
        fake_understanding,
    )
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_icps_and_scenarios",
        fake_artifacts,
    )

    response = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False, "force_refresh": False},
        headers=auth_headers,
    )
    assert response.status_code == 202
    analysis_id = response.json()["analysis"]["id"]

    detail_response = client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["status"] == "completed"
    assert detail["extracted_product_data"]["company_name"] == "Acme"
    assert len(detail["icp_profiles"]) == 3
    assert len(detail["scenarios"]) == 3
    assert len(detail["simulation_runs"]) == 3
    assert detail["simulation_runs"][0]["summary"]["scenario_title"]


def test_repeated_submission_reuses_existing_analysis(client: TestClient, auth_headers: dict[str, str], monkeypatch) -> None:
    async def fake_scrape(self, normalized_url: str):
        return sample_scrape_result(normalized_url)

    async def fake_understanding(self, scrape_result, *, user_identifier: str):
        return sample_product_understanding()

    async def fake_artifacts(self, understanding, *, user_identifier: str):
        return sample_generated_icps(), sample_generated_scenarios()

    monkeypatch.setattr("app.services.scraper_service.ScraperService.scrape", fake_scrape)
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_product_understanding",
        fake_understanding,
    )
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_icps_and_scenarios",
        fake_artifacts,
    )

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
    assert response.status_code == 422
