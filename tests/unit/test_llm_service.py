import pytest
from unittest.mock import MagicMock, patch
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.services.llm_service import LLMService

class TestLLMService:
    
    @pytest.fixture
    def llm_service(self, mock_openai_client):
        """Create LLM service with mocked client."""
        service = LLMService()
        service.client = mock_openai_client
        return service

    @pytest.mark.asyncio
    async def test_generate_questions_from_goals_success(self, llm_service, mock_openai_client):
        """Test successful question generation from goals."""
        goals = "Help me document a software bug fix process"
        expected_schema = {
            "bug_description": {"prompt": "What was the bug?", "type": "story"}
        }
        
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps(expected_schema)
        
        result = await llm_service.generate_questions_from_goals(goals)
        
        assert result == expected_schema
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args
        assert goals in call_args[1]['messages'][1]['content']

    @pytest.mark.asyncio
    async def test_generate_questions_from_goals_fallback(self, llm_service, mock_openai_client):
        """Test fallback when API call fails."""
        goals = "Help me document a bug fix"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = await llm_service.generate_questions_from_goals(goals)
        
        # Should return bug-related fallback schema
        assert "issue_description" in result
        assert "steps_taken" in result
        assert "outcome" in result
        assert result["issue_description"]["type"] == "story"

    @pytest.mark.asyncio
    async def test_generate_questions_bug_keywords(self, llm_service, mock_openai_client):
        """Test fallback schema generation for bug-related keywords."""
        goals = "software error fix debugging"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = await llm_service.generate_questions_from_goals(goals)
        
        expected_fields = ["issue_description", "steps_taken", "outcome"]
        for field in expected_fields:
            assert field in result
            assert "prompt" in result[field]
            assert "type" in result[field]

    @pytest.mark.asyncio
    async def test_generate_questions_documentation_keywords(self, llm_service, mock_openai_client):
        """Test fallback schema generation for documentation keywords."""
        goals = "create documentation guide for process"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = await llm_service.generate_questions_from_goals(goals)
        
        expected_fields = ["topic", "key_points", "audience"]
        for field in expected_fields:
            assert field in result

    @pytest.mark.asyncio
    async def test_generate_questions_generic_fallback(self, llm_service, mock_openai_client):
        """Test generic fallback schema generation."""
        goals = "random topic with no specific keywords"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = await llm_service.generate_questions_from_goals(goals)
        
        # Should contain generic fields based on first word
        assert len(result) >= 2
        first_word = goals.split()[0]
        assert f"{first_word}_details" in result or f"{first_word}_summary" in result

    @pytest.mark.asyncio
    async def test_evaluate_response_sufficient(self, llm_service, mock_openai_client):
        """Test response evaluation when answer is sufficient."""
        question = "What is your name?"
        answer = "My name is John Doe"
        field_type = "string"
        
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = "SUFFICIENT"
        
        is_sufficient, feedback = await llm_service.evaluate_response(question, answer, field_type)
        
        assert is_sufficient is True
        assert feedback is None

    @pytest.mark.asyncio
    async def test_evaluate_response_insufficient(self, llm_service, mock_openai_client):
        """Test response evaluation when answer is insufficient."""
        question = "Tell me about your experience"
        answer = "Some experience"
        field_type = "story"
        
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = "INSUFFICIENT: Please provide more detail about your specific experience."
        
        is_sufficient, feedback = await llm_service.evaluate_response(question, answer, field_type)
        
        assert is_sufficient is False
        assert "Please provide more detail" in feedback

    @pytest.mark.asyncio
    async def test_evaluate_response_fallback_yes_no(self, llm_service, mock_openai_client):
        """Test fallback evaluation for yes/no questions."""
        question = "Are you available?"
        answer = "maybe"
        field_type = "yes/no"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        is_sufficient, feedback = await llm_service.evaluate_response(question, answer, field_type)
        
        assert is_sufficient is False
        assert "yes" in feedback.lower() and "no" in feedback.lower()

    @pytest.mark.asyncio
    async def test_evaluate_response_fallback_yes_valid(self, llm_service, mock_openai_client):
        """Test fallback evaluation for valid yes/no answer."""
        question = "Are you available?"
        answer = "yes"
        field_type = "yes/no"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        is_sufficient, feedback = await llm_service.evaluate_response(question, answer, field_type)
        
        assert is_sufficient is True

    @pytest.mark.asyncio
    async def test_evaluate_response_fallback_too_short(self, llm_service, mock_openai_client):
        """Test fallback evaluation for too short answers."""
        question = "Tell me about yourself"
        answer = "Good"
        field_type = "story"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        is_sufficient, feedback = await llm_service.evaluate_response(question, answer, field_type)
        
        assert is_sufficient is False
        assert "detailed" in feedback.lower()

    @pytest.mark.asyncio
    async def test_evaluate_response_fallback_sufficient_length(self, llm_service, mock_openai_client):
        """Test fallback evaluation for sufficiently long answers."""
        question = "Tell me about yourself"
        answer = "I am an experienced software developer with 5 years of experience."
        field_type = "story"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        is_sufficient, feedback = await llm_service.evaluate_response(question, answer, field_type)
        
        assert is_sufficient is True

    @pytest.mark.asyncio
    async def test_evaluate_response_api_error_fallback(self, llm_service, mock_openai_client):
        """Test that API errors are handled gracefully."""
        question = "Test question"
        answer = "Test answer with sufficient length"
        field_type = "string"
        
        mock_openai_client.chat.completions.create.side_effect = Exception("Network error")
        
        is_sufficient, feedback = await llm_service.evaluate_response(question, answer, field_type)
        
        # Should fall back to basic validation
        assert isinstance(is_sufficient, bool)

    def test_fallback_schema_bug_keywords(self, llm_service):
        """Test _fallback_schema method with bug keywords."""
        goals = "fix software bug error"
        
        result = llm_service._fallback_schema(goals)
        
        assert "issue_description" in result
        assert "steps_taken" in result
        assert "outcome" in result

    def test_fallback_schema_documentation_keywords(self, llm_service):
        """Test _fallback_schema method with documentation keywords."""
        goals = "create document guide"
        
        result = llm_service._fallback_schema(goals)
        
        assert "topic" in result
        assert "key_points" in result
        assert "audience" in result

    def test_fallback_schema_generic(self, llm_service):
        """Test _fallback_schema method with generic keywords."""
        goals = "general interview questions"
        
        result = llm_service._fallback_schema(goals)
        
        # Should create generic fields based on first word
        assert len(result) >= 2
        assert any("general" in key for key in result.keys())

    def test_fallback_evaluation_yes_no_valid(self, llm_service):
        """Test _fallback_evaluation method for valid yes/no."""
        is_sufficient, feedback = llm_service._fallback_evaluation("yes", "yes/no")
        assert is_sufficient is True

    def test_fallback_evaluation_yes_no_invalid(self, llm_service):
        """Test _fallback_evaluation method for invalid yes/no."""
        is_sufficient, feedback = llm_service._fallback_evaluation("maybe", "yes/no")
        assert is_sufficient is False
        assert "yes" in feedback and "no" in feedback

    def test_fallback_evaluation_too_short(self, llm_service):
        """Test _fallback_evaluation method for too short answer."""
        is_sufficient, feedback = llm_service._fallback_evaluation("short", "story")
        assert is_sufficient is False
        assert "detailed" in feedback.lower()

    def test_fallback_evaluation_sufficient_length(self, llm_service):
        """Test _fallback_evaluation method for sufficient length."""
        is_sufficient, feedback = llm_service._fallback_evaluation("This is a sufficiently long answer", "story")
        assert is_sufficient is True