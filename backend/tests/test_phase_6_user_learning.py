"""
Test Phase 6 - User Learning & Adaptation

Tests for:
- UserLearningAgent
- User behavior pattern tracking
- Question effectiveness metrics
- Knowledge base document upload
- Personalized question recommendations
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.agents.user_learning import UserLearningAgent
from app.models import (
    User, Project, Session, Question,
    UserBehaviorPattern, QuestionEffectiveness, KnowledgeBaseDocument
)


def test_user_learning_agent_capabilities(service_container):
    """Test UserLearningAgent exposes correct capabilities"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    capabilities = agent.get_capabilities()

    assert 'track_question_effectiveness' in capabilities
    assert 'learn_behavior_pattern' in capabilities
    assert 'recommend_next_question' in capabilities
    assert 'upload_knowledge_document' in capabilities
    assert 'get_user_profile' in capabilities


def test_track_question_effectiveness(service_container, test_user, test_project):
    """Test tracking question effectiveness for a user"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    # Create a question
    specs_db = service_container.get_database_specs()
    question = Question(
        session_id=uuid4(),
        text="What is your project's main goal?",
        category="goals",
        difficulty="basic",
        asked_at=datetime.now(timezone.utc)
    )
    specs_db.add(question)
    specs_db.commit()
    specs_db.refresh(question)

    # Track effectiveness
    result = agent.process_request('track_question_effectiveness', {
        'user_id': str(test_user.id),
        'question_id': str(question.id),
        'effectiveness_score': 0.85,
        'time_to_answer_seconds': 45,
        'answer_length': 150,
        'led_to_specs': True,
        'specs_extracted_count': 3
    })

    assert result['success'] is True
    assert 'effectiveness_id' in result

    # Verify record was created
    effectiveness = specs_db.query(QuestionEffectiveness).filter(
        QuestionEffectiveness.user_id == test_user.id
    ).first()

    assert effectiveness is not None
    assert effectiveness.question_id == question.id
    assert effectiveness.effectiveness_score == 0.85
    assert effectiveness.specs_extracted == 3

    specs_db.close()


def test_learn_behavior_pattern(service_container, test_user):
    """Test learning user behavior patterns"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    result = agent.process_request('learn_behavior_pattern', {
        'user_id': str(test_user.id),
        'pattern_type': 'communication_style',
        'pattern_data': {
            'verbosity': 'detailed',
            'technical_level': 'intermediate',
            'prefers_examples': True,
            'typical_response_length': 200
        }
    })

    assert result['success'] is True
    assert 'pattern_id' in result

    # Verify pattern was stored
    specs_db = service_container.get_database_specs()
    pattern = specs_db.query(UserBehaviorPattern).filter(
        UserBehaviorPattern.user_id == test_user.id
    ).first()

    assert pattern is not None
    assert pattern.pattern_type == 'communication_style'
    assert pattern.pattern_data['verbosity'] == 'detailed'

    specs_db.close()


def test_upload_knowledge_document(service_container, test_user, test_project):
    """Test uploading knowledge base document"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    result = agent.process_request('upload_knowledge_document', {
        'project_id': str(test_project.id),
        'user_id': str(test_user.id),
        'document_type': 'requirements',
        'title': 'API Requirements Document',
        'content': '''
        The system must provide REST API endpoints for:
        - User authentication
        - Project management
        - Specification extraction

        All endpoints must be secured with JWT tokens.
        '''
    })

    assert result['success'] is True
    assert 'document_id' in result

    # Verify document was stored
    specs_db = service_container.get_database_specs()
    doc = specs_db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.project_id == test_project.id
    ).first()

    assert doc is not None
    assert doc.title == 'API Requirements Document'
    assert 'REST API' in doc.content
    assert doc.document_type == 'requirements'

    specs_db.close()


def test_recommend_next_question(service_container, test_user, test_project):
    """Test recommending next question based on learned patterns"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    # First, learn some behavior
    agent.process_request('learn_behavior_pattern', {
        'user_id': str(test_user.id),
        'pattern_type': 'question_difficulty',
        'pattern_data': {
            'prefers_detailed_questions': True,
            'struggles_with': ['architecture', 'scaling'],
            'excels_at': ['features', 'ui_ux']
        }
    })

    # Now ask for recommendation
    result = agent.process_request('recommend_next_question', {
        'user_id': str(test_user.id),
        'project_id': str(test_project.id),
        'current_phase': 'discovery'
    })

    assert result['success'] is True
    assert 'recommended_category' in result
    assert 'recommended_difficulty' in result

    # Should recommend easier questions for weak areas
    # or more detailed questions in strong areas


def test_get_user_profile(service_container, test_user, test_project):
    """Test getting complete user learning profile"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    # Create some learning data first
    specs_db = service_container.get_database_specs()

    # Add behavior pattern
    pattern = UserBehaviorPattern(
        user_id=test_user.id,
        pattern_type='communication_style',
        pattern_data={'verbosity': 'concise'},
        confidence_score=0.8,
        learned_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    specs_db.add(pattern)

    # Add question effectiveness
    question = Question(
        session_id=uuid4(),
        text="Test question",
        category="features",
        difficulty="basic",
        asked_at=datetime.now(timezone.utc)
    )
    specs_db.add(question)
    specs_db.commit()
    specs_db.refresh(question)

    effectiveness = QuestionEffectiveness(
        user_id=test_user.id,
        question_id=question.id,
        effectiveness_score=0.9,
        time_to_answer_seconds=30,
        answer_length=100,
        led_to_specs=True,
        specs_extracted=2,
        updated_at=datetime.now(timezone.utc)
    )
    specs_db.add(effectiveness)
    specs_db.commit()
    specs_db.close()

    # Get profile
    result = agent.process_request('get_user_profile', {
        'user_id': str(test_user.id)
    })

    assert result['success'] is True
    assert 'behavior_patterns' in result
    assert 'question_effectiveness' in result
    assert len(result['behavior_patterns']) > 0
    assert len(result['question_effectiveness']) > 0


def test_track_effectiveness_validation(service_container, test_user):
    """Test validation in track_question_effectiveness"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    # Missing required fields
    result = agent.process_request('track_question_effectiveness', {
        'user_id': str(test_user.id),
        # Missing question_id and other required fields
    })

    assert result['success'] is False
    assert 'error' in result or 'error_code' in result


def test_learn_pattern_validation(service_container, test_user):
    """Test validation in learn_behavior_pattern"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    # Missing pattern_data
    result = agent.process_request('learn_behavior_pattern', {
        'user_id': str(test_user.id),
        'pattern_type': 'communication_style',
        # Missing pattern_data
    })

    assert result['success'] is False
    assert 'error' in result or 'error_code' in result


def test_upload_document_validation(service_container, test_user, test_project):
    """Test validation in upload_knowledge_document"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    # Missing content
    result = agent.process_request('upload_knowledge_document', {
        'project_id': str(test_project.id),
        'user_id': str(test_user.id),
        'document_type': 'requirements',
        'title': 'Test Document',
        # Missing content
    })

    assert result['success'] is False
    assert 'error' in result or 'error_code' in result


def test_get_profile_nonexistent_user(service_container):
    """Test getting profile for nonexistent user"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    result = agent.process_request('get_user_profile', {
        'user_id': str(uuid4())  # Random UUID that doesn't exist
    })

    # Should return success but empty data
    assert result['success'] is True
    assert 'behavior_patterns' in result
    assert len(result['behavior_patterns']) == 0


def test_recommend_without_patterns(service_container, test_user, test_project):
    """Test recommendation when no behavior patterns exist yet"""
    agent = UserLearningAgent("learning", "User Learning Agent", service_container)

    result = agent.process_request('recommend_next_question', {
        'user_id': str(test_user.id),
        'project_id': str(test_project.id),
        'current_phase': 'discovery'
    })

    # Should still work, returning default recommendations
    assert result['success'] is True
    assert 'recommended_category' in result
