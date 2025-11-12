"""

Debug test for context analyzer agent.



Tests the context extraction functionality with proper database fixtures.

"""

import pytest

from datetime import datetime, timezone

from uuid import uuid4

from app.models import Project, Session as SessionModel, Question


@pytest.mark.e2e
def test_context_analyzer_with_proper_data(db_specs):
    """Test context analyzer agent with proper database setup."""

    from app.agents.orchestrator import AgentOrchestrator, initialize_default_agents

    from app.core.dependencies import ServiceContainer

    # Create service container and orchestrator

    services = ServiceContainer()

    orchestrator = AgentOrchestrator(services)

    initialize_default_agents(orchestrator)

    # Create test project with proper UUID

    test_user_id = str(uuid4())

    project = Project(

        name="Test Project",

        description="For testing",

        creator_id=test_user_id,

        owner_id=test_user_id,

        user_id=test_user_id,

        current_phase="discovery"

    )

    db_specs.add(project)

    db_specs.commit()

    db_specs.refresh(project)

    # Create a session

    session = SessionModel(

        project_id=project.id,

        status='active',

        started_at=datetime.now(timezone.utc)

    )

    db_specs.add(session)

    db_specs.commit()

    db_specs.refresh(session)

    # Create a question

    question = Question(

        project_id=project.id,

        session_id=session.id,

        text="What are the main goals of your application?",

        category="goals"

    )

    db_specs.add(question)

    db_specs.commit()

    db_specs.refresh(question)

    # Test context analyzer with proper data

    print(f"Testing ContextAnalyzerAgent...")

    print(f"Session ID: {session.id}")

    print(f"Question ID: {question.id}")

    result = orchestrator.route_request(

        'context',

        'extract_specifications',

        {

            'session_id': str(session.id),

            'question_id': str(question.id),

            'answer': "Build a scalable web application for e-commerce with real-time notifications",

            'user_id': test_user_id

        }

    )

    print(f"Result: {result}")

    assert result is not None

    assert isinstance(result, dict)
