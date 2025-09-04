import pytest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.models import (
    InterviewTemplate, InterviewSession, 
    InterviewTemplateCreate, InterviewTemplateUpdate, InterviewTemplateResponse,
    InterviewSessionCreate, InterviewSessionResponse, ChatMessage, ChatResponse
)

class TestDatabaseModels:
    
    def test_interview_template_creation(self, test_db):
        """Test creating an InterviewTemplate in the database."""
        questions_schema = {
            "name": {"prompt": "What is your name?", "type": "string"},
            "experience": {"prompt": "Tell me about your experience.", "type": "story"}
        }
        
        template = InterviewTemplate(
            name="Test Template",
            description="A test template",
            questions_schema=questions_schema
        )
        
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        assert template.id is not None
        assert template.name == "Test Template"
        assert template.description == "A test template"
        assert template.questions_schema == questions_schema
        assert template.is_active is True
        assert isinstance(template.created_at, datetime)

    def test_interview_template_defaults(self, test_db):
        """Test InterviewTemplate default values."""
        template = InterviewTemplate(
            name="Minimal Template",
            questions_schema={}
        )
        
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        assert template.description is None
        assert template.is_active is True
        assert template.created_at is not None
        assert template.updated_at is None  # Only set on update

    def test_interview_session_creation(self, test_db):
        """Test creating an InterviewSession in the database."""
        # First create a template
        template = InterviewTemplate(
            name="Test Template",
            questions_schema={"test": {"prompt": "Test?", "type": "string"}}
        )
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Create session
        session = InterviewSession(
            template_id=template.id,
            session_data={"test": "answer"},
            current_question_index=1
        )
        
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        assert session.id is not None
        assert session.template_id == template.id
        assert session.session_data == {"test": "answer"}
        assert session.current_question_index == 1
        assert session.is_completed is False
        assert isinstance(session.created_at, datetime)

    def test_interview_session_defaults(self, test_db):
        """Test InterviewSession default values."""
        template = InterviewTemplate(
            name="Test Template",
            questions_schema={}
        )
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        session = InterviewSession(template_id=template.id)
        
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        assert session.session_data is None
        assert session.current_question_index == 0
        assert session.is_completed is False

class TestPydanticModels:
    
    def test_interview_template_create_valid(self):
        """Test InterviewTemplateCreate validation with valid data."""
        questions_schema = {
            "name": {"prompt": "What is your name?", "type": "string"}
        }
        
        template_create = InterviewTemplateCreate(
            name="Test Template",
            description="Test description",
            questions_schema=questions_schema
        )
        
        assert template_create.name == "Test Template"
        assert template_create.description == "Test description"
        assert template_create.questions_schema == questions_schema

    def test_interview_template_create_minimal(self):
        """Test InterviewTemplateCreate with minimal required data."""
        questions_schema = {"test": {"prompt": "Test?", "type": "string"}}
        
        template_create = InterviewTemplateCreate(
            name="Minimal Template",
            questions_schema=questions_schema
        )
        
        assert template_create.name == "Minimal Template"
        assert template_create.description is None
        assert template_create.questions_schema == questions_schema

    def test_interview_template_create_validation_error(self):
        """Test InterviewTemplateCreate validation errors."""
        with pytest.raises(ValueError):
            InterviewTemplateCreate(
                questions_schema={}  # Missing required 'name'
            )

    def test_interview_template_update(self):
        """Test InterviewTemplateUpdate model."""
        update_data = InterviewTemplateUpdate(
            name="Updated Name",
            is_active=False
        )
        
        assert update_data.name == "Updated Name"
        assert update_data.is_active is False
        assert update_data.description is None
        assert update_data.questions_schema is None

    def test_interview_template_update_empty(self):
        """Test InterviewTemplateUpdate with no data."""
        update_data = InterviewTemplateUpdate()
        
        assert update_data.name is None
        assert update_data.description is None
        assert update_data.questions_schema is None
        assert update_data.is_active is None

    def test_interview_session_create(self):
        """Test InterviewSessionCreate model."""
        session_create = InterviewSessionCreate(template_id=1)
        
        assert session_create.template_id == 1

    def test_interview_session_create_validation_error(self):
        """Test InterviewSessionCreate validation."""
        with pytest.raises(ValueError):
            InterviewSessionCreate()  # Missing required template_id

    def test_chat_message(self):
        """Test ChatMessage model."""
        message = ChatMessage(message="Hello, how are you?")
        
        assert message.message == "Hello, how are you?"

    def test_chat_message_validation_error(self):
        """Test ChatMessage validation."""
        with pytest.raises(ValueError):
            ChatMessage()  # Missing required message

    def test_chat_response_minimal(self):
        """Test ChatResponse with minimal data."""
        response = ChatResponse(
            response="Hello!",
            is_complete=False
        )
        
        assert response.response == "Hello!"
        assert response.is_complete is False
        assert response.session_data is None

    def test_chat_response_with_session_data(self):
        """Test ChatResponse with session data."""
        session_data = {"name": "John", "experience": "5 years"}
        
        response = ChatResponse(
            response="Interview complete!",
            is_complete=True,
            session_data=session_data
        )
        
        assert response.response == "Interview complete!"
        assert response.is_complete is True
        assert response.session_data == session_data

    def test_interview_template_response_from_db_model(self, test_db):
        """Test InterviewTemplateResponse conversion from database model."""
        questions_schema = {"test": {"prompt": "Test?", "type": "string"}}
        
        # Create database model
        template = InterviewTemplate(
            name="Test Template",
            description="Test description",
            questions_schema=questions_schema
        )
        
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Convert to response model
        response = InterviewTemplateResponse.model_validate(template)
        
        assert response.id == template.id
        assert response.name == template.name
        assert response.description == template.description
        assert response.questions_schema == template.questions_schema
        assert response.is_active == template.is_active
        assert response.created_at == template.created_at

    def test_interview_session_response_from_db_model(self, test_db):
        """Test InterviewSessionResponse conversion from database model."""
        # Create template first
        template = InterviewTemplate(
            name="Test Template",
            questions_schema={}
        )
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Create session
        session = InterviewSession(
            template_id=template.id,
            session_data={"test": "data"},
            current_question_index=2,
            is_completed=True
        )
        
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        # Convert to response model
        response = InterviewSessionResponse.model_validate(session)
        
        assert response.id == session.id
        assert response.template_id == session.template_id
        assert response.session_data == session.session_data
        assert response.current_question_index == session.current_question_index
        assert response.is_completed == session.is_completed
        assert response.created_at == session.created_at

class TestModelRelationships:
    
    def test_template_to_session_relationship(self, test_db):
        """Test that we can create sessions linked to templates."""
        # Create template
        template = InterviewTemplate(
            name="Template with Sessions",
            questions_schema={"q1": {"prompt": "Question 1?", "type": "string"}}
        )
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Create multiple sessions for the template
        session1 = InterviewSession(template_id=template.id)
        session2 = InterviewSession(template_id=template.id)
        
        test_db.add(session1)
        test_db.add(session2)
        test_db.commit()
        
        # Query sessions by template
        sessions = test_db.query(InterviewSession).filter(
            InterviewSession.template_id == template.id
        ).all()
        
        assert len(sessions) == 2
        assert all(session.template_id == template.id for session in sessions)

    def test_template_deletion_behavior(self, test_db):
        """Test behavior when template is soft-deleted."""
        template = InterviewTemplate(
            name="Template to Delete",
            questions_schema={},
            is_active=True
        )
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Soft delete template
        template.is_active = False
        test_db.commit()
        
        # Verify template is marked inactive
        inactive_template = test_db.query(InterviewTemplate).filter(
            InterviewTemplate.id == template.id
        ).first()
        
        assert inactive_template.is_active is False