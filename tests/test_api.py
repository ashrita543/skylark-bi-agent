from unittest.mock import patch

from fastapi.testclient import TestClient

from api.index import app

client = TestClient(app)


def test_health_reports_missing_configuration():
    with patch("api.index.Config.validate", return_value=(False, ["MONDAY_API_TOKEN"])):
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["monday_configured"] is False
    assert response.json()["missing"] == ["MONDAY_API_TOKEN"]


def test_connection_rejects_missing_configuration():
    with patch("api.index.Config.validate", return_value=(False, ["MONDAY_API_TOKEN"])):
        response = client.get("/api/connection")
    assert response.status_code == 503
    assert response.json()["detail"]["missing"] == ["MONDAY_API_TOKEN"]


def test_connection_reports_success():
    with patch("api.index.Config.validate", return_value=(True, [])), patch("api.index.MondayClient") as client_class:
        client_class.return_value.test_connection.return_value = True
        response = client.get("/api/connection")
    assert response.status_code == 200
    assert response.json() == {"connected": True}


def test_question_requires_a_valid_question():
    response = client.post("/api/questions", json={"question": "x"})
    assert response.status_code == 422


def test_question_returns_agent_result():
    result = {"success": True, "type": "analysis", "response": "Pipeline is healthy.", "analysis": {}, "caveats": []}
    with patch("api.index.Config.validate", return_value=(True, [])), patch("api.index.agent.execute_query", return_value=result):
        response = client.post("/api/questions", json={"question": "How is the pipeline?"})
    assert response.status_code == 200
    assert response.json()["response"] == "Pipeline is healthy."
