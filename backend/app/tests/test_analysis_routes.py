from fastapi.testclient import TestClient


def test_create_and_fetch_analysis(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/analyses",
        json={"url": "https://www.netflix.com/", "run_async": False, "force_refresh": False},
        headers=auth_headers,
    )
    assert response.status_code == 202
    analysis_id = response.json()["analysis"]["id"]

    detail_response = client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["status"] == "completed"
    assert detail["extracted_product_data"]["company_name"] == "Netflix"
    assert len(detail["icp_profiles"]) == 5
    assert len(detail["scenarios"]) == 3
    assert len(detail["simulation_runs"]) == 3
    assert detail["simulation_runs"][0]["summary"]["scenario_title"]


def test_repeated_submission_reuses_existing_analysis(client: TestClient, auth_headers: dict[str, str]) -> None:
    first = client.post(
        "/api/v1/analyses",
        json={"url": "https://www.netflix.com/", "run_async": False},
        headers=auth_headers,
    )
    second = client.post(
        "/api/v1/analyses",
        json={"url": "https://www.netflix.com/", "run_async": False},
        headers=auth_headers,
    )
    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["reused"] is True
    assert second.json()["analysis"]["id"] == first.json()["analysis"]["id"]


def test_invalid_url_is_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/analyses",
        json={"url": "ftp://bad.example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 422
