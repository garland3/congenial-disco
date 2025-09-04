import pytest
from unittest.mock import patch
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.models import InterviewTemplate

class TestAdminAPI:
    
    def test_get_templates_empty(self, client):
        """Test getting templates when none exist."""
        response = client.get("/api/admin/templates")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_create_template_success(self, client, sample_template_data):
        """Test creating a new template."""
        response = client.post("/api/admin/templates", json=sample_template_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_template_data["name"]
        assert data["description"] == sample_template_data["description"]
        assert data["questions_schema"] == sample_template_data["questions_schema"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_template_minimal(self, client):
        """Test creating template with minimal required data."""
        template_data = {
            "name": "Minimal Template",
            "questions_schema": {"q1": {"prompt": "Question?", "type": "string"}}
        }
        
        response = client.post("/api/admin/templates", json=template_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Template"
        assert data["description"] is None
        assert data["questions_schema"] == template_data["questions_schema"]

    def test_create_template_validation_error(self, client):
        """Test creating template with invalid data."""
        invalid_data = {
            "questions_schema": {"q1": {"prompt": "Question?", "type": "string"}}
            # Missing required 'name' field
        }
        
        response = client.post("/api/admin/templates", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_get_templates_with_data(self, client, test_db, sample_template_data):
        """Test getting templates when some exist."""
        # Create a template in the database
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        response = client.get("/api/admin/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_template_data["name"]
        assert data[0]["id"] == template.id

    def test_get_templates_filters_inactive(self, client, test_db, sample_template_data):
        """Test that inactive templates are not returned."""
        # Create active template
        active_template = InterviewTemplate(**sample_template_data)
        test_db.add(active_template)
        
        # Create inactive template
        inactive_data = sample_template_data.copy()
        inactive_data["name"] = "Inactive Template"
        inactive_data["is_active"] = False
        inactive_template = InterviewTemplate(**inactive_data)
        test_db.add(inactive_template)
        
        test_db.commit()
        
        response = client.get("/api/admin/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_template_data["name"]

    def test_get_template_by_id(self, client, test_db, sample_template_data):
        """Test getting a specific template by ID."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        response = client.get(f"/api/admin/templates/{template.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template.id
        assert data["name"] == sample_template_data["name"]

    def test_get_template_not_found(self, client):
        """Test getting a template that doesn't exist."""
        response = client.get("/api/admin/templates/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_template_success(self, client, test_db, sample_template_data):
        """Test updating an existing template."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        update_data = {
            "name": "Updated Template Name",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/admin/templates/{template.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template Name"
        assert data["description"] == "Updated description"
        assert data["questions_schema"] == sample_template_data["questions_schema"]  # Unchanged

    def test_update_template_partial(self, client, test_db, sample_template_data):
        """Test partial update of a template."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        update_data = {"is_active": False}
        
        response = client.put(f"/api/admin/templates/{template.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["name"] == sample_template_data["name"]  # Unchanged

    def test_update_template_not_found(self, client):
        """Test updating a template that doesn't exist."""
        update_data = {"name": "Updated Name"}
        
        response = client.put("/api/admin/templates/999", json=update_data)
        
        assert response.status_code == 404

    def test_delete_template_success(self, client, test_db, sample_template_data):
        """Test soft deleting a template."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        response = client.delete(f"/api/admin/templates/{template.id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify template is soft deleted
        updated_template = test_db.query(InterviewTemplate).filter(
            InterviewTemplate.id == template.id
        ).first()
        assert updated_template.is_active is False

    def test_delete_template_not_found(self, client):
        """Test deleting a template that doesn't exist."""
        response = client.delete("/api/admin/templates/999")
        
        assert response.status_code == 404

    @patch('backend.app.services.llm_service.llm_service.generate_questions_from_goals')
    def test_generate_template_success(self, mock_generate, client):
        """Test generating template from goals."""
        goals = "Help me conduct user interviews"
        mock_questions = {
            "user_needs": {"prompt": "What are the user's main needs?", "type": "story"}
        }
        mock_generate.return_value = mock_questions
        
        response = client.post("/api/admin/generate-template", json={"goals": goals})
        
        assert response.status_code == 200
        data = response.json()
        assert "Generated Template" in data["name"]
        assert goals in data["description"]
        assert data["questions_schema"] == mock_questions
        
        mock_generate.assert_called_once_with(goals)

    def test_generate_template_missing_goals(self, client):
        """Test generating template without goals."""
        response = client.post("/api/admin/generate-template", json={})
        
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

    def test_generate_template_empty_goals(self, client):
        """Test generating template with empty goals."""
        response = client.post("/api/admin/generate-template", json={"goals": ""})
        
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

    @patch('backend.app.services.llm_service.llm_service.generate_questions_from_goals')
    def test_generate_template_llm_error(self, mock_generate, client):
        """Test handling LLM service errors during template generation."""
        mock_generate.side_effect = Exception("LLM service error")
        
        response = client.post("/api/admin/generate-template", json={"goals": "test goals"})
        
        assert response.status_code == 500
        assert "Failed to generate template" in response.json()["detail"]

class TestAdminAPIIntegration:
    
    def test_complete_template_workflow(self, client):
        """Test complete workflow: create, read, update, delete template."""
        # Create template
        template_data = {
            "name": "Workflow Test Template",
            "description": "Testing complete workflow",
            "questions_schema": {
                "name": {"prompt": "What is your name?", "type": "string"},
                "experience": {"prompt": "Tell me about your experience.", "type": "story"}
            }
        }
        
        create_response = client.post("/api/admin/templates", json=template_data)
        assert create_response.status_code == 200
        template_id = create_response.json()["id"]
        
        # Read template
        get_response = client.get(f"/api/admin/templates/{template_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == template_data["name"]
        
        # Update template
        update_data = {"name": "Updated Workflow Template"}
        update_response = client.put(f"/api/admin/templates/{template_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Workflow Template"
        
        # Verify in list
        list_response = client.get("/api/admin/templates")
        assert list_response.status_code == 200
        templates = list_response.json()
        assert len(templates) == 1
        assert templates[0]["name"] == "Updated Workflow Template"
        
        # Delete template
        delete_response = client.delete(f"/api/admin/templates/{template_id}")
        assert delete_response.status_code == 200
        
        # Verify not in list (soft deleted)
        final_list_response = client.get("/api/admin/templates")
        assert final_list_response.status_code == 200
        assert len(final_list_response.json()) == 0

    def test_multiple_templates_management(self, client):
        """Test managing multiple templates."""
        templates_data = [
            {
                "name": "Template 1",
                "questions_schema": {"q1": {"prompt": "Question 1?", "type": "string"}}
            },
            {
                "name": "Template 2", 
                "questions_schema": {"q2": {"prompt": "Question 2?", "type": "story"}}
            },
            {
                "name": "Template 3",
                "questions_schema": {"q3": {"prompt": "Question 3?", "type": "yes/no"}}
            }
        ]
        
        created_ids = []
        
        # Create multiple templates
        for template_data in templates_data:
            response = client.post("/api/admin/templates", json=template_data)
            assert response.status_code == 200
            created_ids.append(response.json()["id"])
        
        # Verify all templates exist
        list_response = client.get("/api/admin/templates")
        assert list_response.status_code == 200
        templates = list_response.json()
        assert len(templates) == 3
        
        template_names = [t["name"] for t in templates]
        for expected_name in ["Template 1", "Template 2", "Template 3"]:
            assert expected_name in template_names
        
        # Delete one template
        delete_response = client.delete(f"/api/admin/templates/{created_ids[1]}")
        assert delete_response.status_code == 200
        
        # Verify only 2 remain active
        final_list_response = client.get("/api/admin/templates")
        assert final_list_response.status_code == 200
        remaining_templates = final_list_response.json()
        assert len(remaining_templates) == 2
        
        remaining_names = [t["name"] for t in remaining_templates]
        assert "Template 1" in remaining_names
        assert "Template 3" in remaining_names
        assert "Template 2" not in remaining_names