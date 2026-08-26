from fastapi.testclient import TestClient

from app.main import app
from app.services.analytics_service import _client


def test_user_agent_classification():
    assert _client("Mozilla/5.0 (Windows NT 10.0) Chrome/120") == ("desktop", "Chrome", "Windows")
    assert _client("Mozilla/5.0 (iPhone) Version/17 Mobile Safari/604") == ("mobile", "Safari", "iOS")


def test_admin_analytics_requires_key():
    response = TestClient(app).get("/api/v1/admin/analytics/summary?days=30")
    assert response.status_code == 401
    assert response.json()["detail"] == "Valid administrator key required"
