import pytest
import os
import sys
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from backend.app.main import app
from backend.app.database import get_db
from backend.app.models import Base
from backend.app.config import Settings

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    return Settings(
        openrouter_api_key="test_key",
        openrouter_base_url="https://test.example.com",
        model_name="test/model",
        database_url=TEST_DATABASE_URL
    )

@pytest.fixture(scope="function")
def test_db(test_settings):
    """Create a test database for each test function."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        # Remove test database file
        try:
            os.unlink("test.db")
        except FileNotFoundError:
            pass

@pytest.fixture(scope="function")
def client(test_db, test_settings):
    """Create a test client with test database."""
    def get_test_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = get_test_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    
    # Mock chat completion response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"test_field": {"prompt": "Test question?", "type": "string"}}'
    
    mock_client.chat.completions.create.return_value = mock_response
    
    return mock_client

@pytest.fixture
def sample_questions_schema():
    """Sample questions schema for testing."""
    return {
        "name": {"prompt": "What is your name?", "type": "string"},
        "experience": {"prompt": "Tell me about your experience.", "type": "story"},
        "available": {"prompt": "Are you available for work?", "type": "yes/no"}
    }

@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "name": "Test Interview Template",
        "description": "A template for testing purposes",
        "questions_schema": {
            "name": {"prompt": "What is your name?", "type": "string"},
            "experience": {"prompt": "Tell me about your experience.", "type": "story"}
        }
    }