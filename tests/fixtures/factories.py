import factory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from backend.app.models import InterviewTemplate, InterviewSession

class InterviewTemplateFactory(SQLAlchemyModelFactory):
    class Meta:
        model = InterviewTemplate
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("text", max_nb_chars=200)
    questions_schema = factory.LazyAttribute(lambda obj: {
        "name": {"prompt": "What is your name?", "type": "string"},
        "experience": {"prompt": "Tell me about your experience.", "type": "story"}
    })
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)
    is_active = True

class InterviewSessionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = InterviewSession
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n)
    template_id = factory.SubFactory(InterviewTemplateFactory)
    session_data = factory.LazyAttribute(lambda obj: {})
    current_question_index = 0
    is_completed = False
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)