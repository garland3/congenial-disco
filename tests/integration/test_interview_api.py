import pytest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.models import InterviewTemplate, InterviewSession

class TestInterviewAPI:
    
    def test_get_available_templates_empty(self, client):
        """Test getting available templates when none exist."""
        response = client.get("/api/interview/templates")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_get_available_templates_with_data(self, client, test_db, sample_template_data):
        """Test getting available templates when some exist."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        response = client.get("/api/interview/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_template_data["name"]

    def test_get_available_templates_filters_inactive(self, client, test_db, sample_template_data):
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
        
        response = client.get("/api/interview/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_template_data["name"]

    def test_start_interview_success(self, client, test_db, sample_template_data):
        """Test starting a new interview session."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        response = client.post(f"/api/interview/start/{template.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == template.id
        assert data["current_question_index"] == 0
        assert data["is_completed"] is False
        assert data["session_data"] == {}
        assert "id" in data
        assert "created_at" in data

    def test_start_interview_template_not_found(self, client):
        """Test starting interview with non-existent template."""
        response = client.post("/api/interview/start/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_start_interview_inactive_template(self, client, test_db, sample_template_data):
        """Test starting interview with inactive template."""
        inactive_data = sample_template_data.copy()
        inactive_data["is_active"] = False
        template = InterviewTemplate(**inactive_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        response = client.post(f"/api/interview/start/{template.id}")
        
        assert response.status_code == 404

    def test_get_interview_session(self, client, test_db, sample_template_data):
        """Test getting an interview session."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        session = InterviewSession(
            template_id=template.id,
            session_data={"test": "data"},
            current_question_index=1
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        response = client.get(f"/api/interview/session/{session.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session.id
        assert data["template_id"] == template.id
        assert data["session_data"] == {"test": "data"}
        assert data["current_question_index"] == 1

    def test_get_interview_session_not_found(self, client):
        """Test getting a session that doesn't exist."""
        response = client.get("/api/interview/session/999")
        
        assert response.status_code == 404

    def test_get_session_status(self, client, test_db, sample_template_data):
        """Test getting session status."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        session = InterviewSession(
            template_id=template.id,
            current_question_index=1
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        response = client.get(f"/api/interview/session/{session.id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session.id
        assert data["current_question"] == 2  # current_question_index + 1
        assert data["total_questions"] == 2  # sample_template_data has 2 questions
        assert data["is_completed"] is False
        assert data["progress_percentage"] == 50  # 1/2 * 100

    def test_get_session_status_not_found(self, client):
        """Test getting status for non-existent session."""
        response = client.get("/api/interview/session/999/status")
        
        assert response.status_code == 404

    @patch('backend.app.services.llm_service.llm_service.evaluate_response')
    def test_chat_with_session_first_message(self, mock_evaluate, client, test_db, sample_template_data):
        """Test first message in a chat session."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        session = InterviewSession(template_id=template.id, session_data={})
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        response = client.post(
            f"/api/interview/session/{session.id}/chat",
            json={"message": "I'm ready to start"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "first question" in data["response"].lower()
        assert data["is_complete"] is False

    @patch('backend.app.services.llm_service.llm_service.evaluate_response')
    def test_chat_with_session_sufficient_response(self, mock_evaluate, client, test_db, sample_template_data):
        """Test chat with sufficient response."""
        mock_evaluate.return_value = (True, None)  # Sufficient response
        
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        session = InterviewSession(
            template_id=template.id,
            session_data={"name": "John"},
            current_question_index=1  # Second question
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        response = client.post(
            f"/api/interview/session/{session.id}/chat",
            json={"message": "I have 5 years of software development experience"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_complete"] is True
        assert "complete" in data["response"].lower()
        assert data["session_data"] is not None

    @patch('backend.app.services.llm_service.llm_service.evaluate_response')
    def test_chat_with_session_insufficient_response(self, mock_evaluate, client, test_db, sample_template_data):
        """Test chat with insufficient response."""
        mock_evaluate.return_value = (False, "Please provide more detail")
        
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        session = InterviewSession(
            template_id=template.id,
            session_data={},
            current_question_index=0
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        response = client.post(
            f"/api/interview/session/{session.id}/chat",
            json={"message": "John"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "more detail" in data["response"]
        assert data["is_complete"] is False

    def test_chat_with_completed_session(self, client, test_db, sample_template_data):
        """Test chatting with already completed session."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        session = InterviewSession(
            template_id=template.id,
            is_completed=True,
            session_data={"name": "John", "experience": "5 years"}
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        response = client.post(
            f"/api/interview/session/{session.id}/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "already been completed" in data["response"]
        assert data["is_complete"] is True

    def test_chat_session_not_found(self, client):
        """Test chatting with non-existent session."""
        response = client.post(
            "/api/interview/session/999/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 404

class TestInterviewAPIIntegration:
    
    @patch('backend.app.services.llm_service.llm_service.evaluate_response')
    def test_complete_interview_workflow(self, mock_evaluate, client, test_db):
        """Test complete interview workflow from start to finish."""
        # Mock LLM evaluations - first answer insufficient, second sufficient
        mock_evaluate.side_effect = [
            (False, "Please provide more detail"),
            (True, None),
            (True, None)
        ]
        
        # Create template
        template_data = {
            "name": "Complete Workflow Test",
            "questions_schema": {
                "name": {"prompt": "What is your name?", "type": "string"},
                "experience": {"prompt": "Tell me about your experience.", "type": "story"}
            }
        }
        template = InterviewTemplate(**template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Start interview
        start_response = client.post(f"/api/interview/start/{template.id}")
        assert start_response.status_code == 200
        session_id = start_response.json()["id"]
        
        # Get session status
        status_response = client.get(f"/api/interview/session/{session_id}/status")
        assert status_response.status_code == 200
        assert status_response.json()["progress_percentage"] == 0
        
        # First message - insufficient response
        chat1_response = client.post(
            f"/api/interview/session/{session_id}/chat",
            json={"message": "John"}
        )
        assert chat1_response.status_code == 200
        assert "more detail" in chat1_response.json()["response"]
        assert not chat1_response.json()["is_complete"]
        
        # Second message - sufficient for first question
        chat2_response = client.post(
            f"/api/interview/session/{session_id}/chat",
            json={"message": "My full name is John Smith"}
        )
        assert chat2_response.status_code == 200
        assert "next question" in chat2_response.json()["response"].lower()
        assert not chat2_response.json()["is_complete"]
        
        # Check progress
        progress_response = client.get(f"/api/interview/session/{session_id}/status")
        assert progress_response.status_code == 200
        assert progress_response.json()["progress_percentage"] == 50
        
        # Third message - answer second question
        chat3_response = client.post(
            f"/api/interview/session/{session_id}/chat",
            json={"message": "I have 5 years of software development experience"}
        )
        assert chat3_response.status_code == 200
        assert chat3_response.json()["is_complete"] is True
        assert "complete" in chat3_response.json()["response"].lower()
        
        # Final status check
        final_status_response = client.get(f"/api/interview/session/{session_id}/status")
        assert final_status_response.status_code == 200
        assert final_status_response.json()["progress_percentage"] == 100
        assert final_status_response.json()["is_completed"] is True

    def test_multiple_concurrent_sessions(self, client, test_db, sample_template_data):
        """Test multiple concurrent interview sessions."""
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Start multiple sessions
        session_ids = []
        for i in range(3):
            response = client.post(f"/api/interview/start/{template.id}")
            assert response.status_code == 200
            session_ids.append(response.json()["id"])
        
        # Verify all sessions exist and are independent
        for session_id in session_ids:
            session_response = client.get(f"/api/interview/session/{session_id}")
            assert session_response.status_code == 200
            session_data = session_response.json()
            assert session_data["template_id"] == template.id
            assert session_data["current_question_index"] == 0
            assert session_data["is_completed"] is False
        
        # Verify sessions have different IDs
        assert len(set(session_ids)) == 3

    @patch('backend.app.services.llm_service.llm_service.evaluate_response')
    def test_session_state_persistence(self, mock_evaluate, client, test_db, sample_template_data):
        """Test that session state is properly persisted between requests."""
        mock_evaluate.return_value = (True, None)
        
        template = InterviewTemplate(**sample_template_data)
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Start session
        start_response = client.post(f"/api/interview/start/{template.id}")
        session_id = start_response.json()["id"]
        
        # Send first message
        client.post(
            f"/api/interview/session/{session_id}/chat",
            json={"message": "John Doe"}
        )
        
        # Verify session state was updated
        session_response = client.get(f"/api/interview/session/{session_id}")
        session_data = session_response.json()
        assert session_data["current_question_index"] == 1
        assert "name" in session_data["session_data"]
        assert session_data["session_data"]["name"] == "John Doe"
        
        # Send second message
        client.post(
            f"/api/interview/session/{session_id}/chat",
            json={"message": "I have extensive experience in software development"}
        )
        
        # Verify final state
        final_session_response = client.get(f"/api/interview/session/{session_id}")
        final_session_data = final_session_response.json()
        assert final_session_data["is_completed"] is True
        assert len(final_session_data["session_data"]) == 2
        assert final_session_data["session_data"]["name"] == "John Doe"