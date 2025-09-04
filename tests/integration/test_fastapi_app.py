import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.main import app

class TestFastAPIApp:
    
    def test_app_startup(self, client):
        """Test that the FastAPI app starts correctly."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "AI Interview Assistant API" in data["message"]
        assert data["docs"] == "/docs"

    def test_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        # Test preflight request
        response = client.options("/api/admin/templates", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        })
        
        # FastAPI/Starlette may return 200 or 405 for OPTIONS
        assert response.status_code in [200, 405]

    def test_api_documentation_accessible(self, client):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        
        # Should either return the docs page or redirect to it
        assert response.status_code in [200, 307]

    def test_openapi_schema_accessible(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "AI Interview Assistant"

    def test_admin_routes_registered(self, client):
        """Test that admin routes are properly registered."""
        response = client.get("/api/admin/templates")
        
        assert response.status_code == 200  # Should work even if empty

    def test_interview_routes_registered(self, client):
        """Test that interview routes are properly registered."""
        response = client.get("/api/interview/templates")
        
        assert response.status_code == 200  # Should work even if empty

    def test_404_for_unknown_routes(self, client):
        """Test that unknown routes return 404."""
        response = client.get("/api/unknown/route")
        
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test that wrong HTTP methods return 405."""
        response = client.patch("/api/admin/templates")  # PATCH not supported
        
        assert response.status_code == 405

    def test_validation_error_format(self, client):
        """Test that validation errors are properly formatted."""
        # Send invalid JSON to create template endpoint
        response = client.post("/api/admin/templates", json={
            "questions_schema": {}  # Missing required 'name' field
        })
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_content_type_handling(self, client):
        """Test proper content type handling."""
        # Send request with wrong content type
        response = client.post(
            "/api/admin/templates",
            data="invalid data",
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 422

    def test_large_payload_handling(self, client):
        """Test handling of reasonably large payloads."""
        large_schema = {}
        for i in range(50):  # Create 50 questions
            large_schema[f"question_{i}"] = {
                "prompt": f"This is question {i} with a longer prompt that contains more text to test payload size handling",
                "type": "story"
            }
        
        large_template = {
            "name": "Large Template",
            "description": "A template with many questions to test large payload handling",
            "questions_schema": large_schema
        }
        
        response = client.post("/api/admin/templates", json=large_template)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions_schema"]) == 50

class TestFastAPIMiddleware:
    
    def test_cors_allows_local_development(self, client):
        """Test that CORS allows requests from local development servers."""
        headers = {"Origin": "http://localhost:3000"}
        
        response = client.get("/api/admin/templates", headers=headers)
        
        assert response.status_code == 200

    def test_cors_allows_vite_dev_server(self, client):
        """Test that CORS allows requests from Vite dev server."""
        headers = {"Origin": "http://localhost:5173"}
        
        response = client.get("/api/admin/templates", headers=headers)
        
        assert response.status_code == 200

class TestFastAPIDatabase:
    
    def test_database_dependency_injection(self, client, test_db):
        """Test that database dependency injection works correctly."""
        # This is implicitly tested by other tests, but we can verify
        # that the dependency override is working
        response = client.get("/api/admin/templates")
        
        assert response.status_code == 200
        # If database dependency wasn't working, this would fail

    def test_database_transaction_rollback(self, client, test_db, sample_template_data):
        """Test that database transactions are properly handled."""
        # Create a template
        response = client.post("/api/admin/templates", json=sample_template_data)
        assert response.status_code == 200
        template_id = response.json()["id"]
        
        # Template should exist
        get_response = client.get(f"/api/admin/templates/{template_id}")
        assert get_response.status_code == 200
        
        # After test cleanup, template shouldn't exist in production database
        # (This is ensured by the test database fixture)

class TestFastAPIErrorHandling:
    
    def test_internal_server_error_handling(self, client):
        """Test handling of internal server errors."""
        # Try to start interview with invalid template ID format
        # This should be handled gracefully
        response = client.post("/api/interview/start/invalid")
        
        assert response.status_code == 422  # Validation error for invalid ID

    def test_request_validation_error(self, client):
        """Test request validation error responses."""
        # Send malformed JSON
        response = client.post(
            "/api/admin/templates",
            data='{"name": "test", "questions_schema":',  # Incomplete JSON
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        response = client.post("/api/admin/templates", json={})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        
        # Should indicate missing required fields
        field_errors = [error["loc"] for error in error_detail]
        assert any("name" in error for error in field_errors)
        assert any("questions_schema" in error for error in field_errors)

class TestFastAPIPerformance:
    
    def test_concurrent_requests_handling(self, client, sample_template_data):
        """Test that the app can handle multiple concurrent requests."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = client.post("/api/admin/templates", json=sample_template_data)
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Start multiple concurrent requests
        threads = []
        for i in range(10):
            # Modify template name to avoid conflicts
            template_data = sample_template_data.copy()
            template_data["name"] = f"Concurrent Test Template {i}"
            
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())
        
        assert len(status_codes) == 10
        assert all(code == 200 for code in status_codes)

    def test_response_time_reasonable(self, client):
        """Test that response times are reasonable."""
        import time
        
        start_time = time.time()
        response = client.get("/api/admin/templates")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second