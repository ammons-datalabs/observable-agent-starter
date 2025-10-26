"""Tests for the FastAPI server."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from observable_agent_starter.servers.api import app, RouteRequest, RouteResponse


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Use with statement to ensure lifespan events are triggered
    with TestClient(app) as test_client:
        yield test_client


class TestRootEndpoint:
    """Tests for the root / endpoint."""

    def test_root_returns_service_info(self, client):
        """Test that root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "observable-agent-starter"
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"

    def test_root_content_type(self, client):
        """Test that root endpoint returns JSON."""
        response = client.get("/")

        assert response.headers["content-type"] == "application/json"


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_agent_status(self, client):
        """Test that health endpoint returns agent readiness."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "agent_ready" in data
        assert isinstance(data["agent_ready"], bool)
        assert data["service"] == "observable-agent-starter"

    def test_health_check_agent_ready(self, client):
        """Test health check shows agent as ready after initialization."""
        # After lifespan startup, agent should be initialized
        response = client.get("/health")

        data = response.json()
        assert data["agent_ready"] is True


class TestRouteEndpoint:
    """Tests for the /route POST endpoint."""

    def test_route_endpoint_billing_request(self, client):
        """Test routing a billing-related request."""
        response = client.post(
            "/route",
            json={"request": "My invoice has extra charges"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["route"] in ["billing", "tech", "sales"]
        assert "explanation" in data
        assert isinstance(data["explanation"], str)

    def test_route_endpoint_tech_request(self, client):
        """Test routing a technical support request."""
        response = client.post(
            "/route",
            json={"request": "The app keeps crashing when I log in"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["route"] in ["billing", "tech", "sales"]
        assert "explanation" in data

    def test_route_endpoint_sales_request(self, client):
        """Test routing a sales inquiry."""
        response = client.post(
            "/route",
            json={"request": "I want to upgrade to the enterprise plan"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["route"] in ["billing", "tech", "sales"]
        assert "explanation" in data

    def test_route_endpoint_validates_request_field(self, client):
        """Test that request field is required."""
        response = client.post(
            "/route",
            json={}  # Missing "request" field
        )

        assert response.status_code == 422  # Validation error

    def test_route_endpoint_rejects_invalid_json(self, client):
        """Test that invalid JSON is rejected."""
        response = client.post(
            "/route",
            data="not json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_route_endpoint_response_model(self, client):
        """Test that response matches RouteResponse model."""
        response = client.post(
            "/route",
            json={"request": "test request"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert set(data.keys()) == {"route", "explanation"}
        assert isinstance(data["route"], str)
        assert isinstance(data["explanation"], str)

    def test_route_endpoint_handles_empty_request(self, client):
        """Test handling of empty request string."""
        response = client.post(
            "/route",
            json={"request": ""}
        )

        # Should still return a valid response (fallback to policy)
        assert response.status_code == 200
        data = response.json()
        assert data["route"] in ["billing", "tech", "sales"]

    def test_route_endpoint_handles_long_request(self, client):
        """Test handling of very long request text."""
        long_request = "test " * 1000  # 5000 chars
        response = client.post(
            "/route",
            json={"request": long_request}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["route"] in ["billing", "tech", "sales"]


class TestAgentLifecycle:
    """Tests for agent initialization lifecycle."""

    def test_agent_initialized_on_startup(self, client):
        """Test that agent is initialized during app lifespan."""
        # Make a request to ensure app is started
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_ready"] is True

    def test_route_endpoint_fails_if_agent_not_initialized(self):
        """Test that route endpoint fails gracefully if agent is None."""
        # Create a test client without triggering lifespan (no context manager)
        # This simulates the case where agent initialization failed
        import observable_agent_starter.servers.api as server

        # Temporarily set agent to None
        original_agent = server.agent
        server.agent = None

        try:
            # Create client without context manager (agent won't be initialized)
            test_client = TestClient(app, raise_server_exceptions=False)
            response = test_client.post(
                "/route",
                json={"request": "test"}
            )

            assert response.status_code == 500
            assert "Agent not initialized" in response.text or response.status_code == 500
        finally:
            # Restore agent
            server.agent = original_agent


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation."""

    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Observable Agent Starter - Routing API"
        assert data["info"]["version"] == "0.1.0"

    def test_docs_endpoint_available(self, client):
        """Test that Swagger docs are accessible."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_available(self, client):
        """Test that ReDoc is accessible."""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestPydanticModels:
    """Tests for Pydantic models."""

    def test_route_request_model_validation(self):
        """Test RouteRequest model validation."""
        # Valid request
        valid = RouteRequest(request="test request")
        assert valid.request == "test request"

        # Test that empty string is allowed
        empty = RouteRequest(request="")
        assert empty.request == ""

    def test_route_response_model_validation(self):
        """Test RouteResponse model validation."""
        # Valid response
        valid = RouteResponse(route="billing", explanation="test explanation")
        assert valid.route == "billing"
        assert valid.explanation == "test explanation"

        # Test with empty explanation
        empty_explanation = RouteResponse(route="tech", explanation="")
        assert empty_explanation.explanation == ""


class TestErrorHandling:
    """Tests for error handling."""

    def test_method_not_allowed(self, client):
        """Test that wrong HTTP methods are rejected."""
        # GET on /route should fail
        response = client.get("/route")
        assert response.status_code == 405  # Method Not Allowed

    def test_route_not_found(self, client):
        """Test that unknown routes return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_content_type(self, client):
        """Test that non-JSON content type is rejected."""
        response = client.post(
            "/route",
            data="request=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Should fail validation
        assert response.status_code == 422


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_not_present_by_default(self, client):
        """Test that CORS headers are not present (not configured)."""
        response = client.get("/")

        # CORS not configured by default, so these headers should not be present
        assert "access-control-allow-origin" not in response.headers
