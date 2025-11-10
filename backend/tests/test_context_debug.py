#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.agents.orchestrator import AgentOrchestrator, initialize_default_agents
from app.core.dependencies import ServiceContainer
from app.core.database import SessionLocalSpecs
from app.models.project import Project
from app.models.session import Session as SessionModel
from app.models.question import Question
from datetime import datetime, timezone

services = ServiceContainer()
orchestrator = AgentOrchestrator(services)
initialize_default_agents(orchestrator)

db = SessionLocalSpecs()

# Create test project and session
test_user_id = "00000000-0000-0000-0000-000000000001"
project = Project(
    name="Test Project",
    description="For testing",
    creator_id=test_user_id,
    owner_id=test_user_id,
    user_id=test_user_id,
    current_phase="discovery"
)
db.add(project)
db.commit()
db.refresh(project)

# Create a session
session = SessionModel(
    project_id=project.id,
    status='active',
    started_at=datetime.now(timezone.utc)
)
db.add(session)
db.commit()
db.refresh(session)

# Create a question
question = Question(
    project_id=project.id,
    session_id=session.id,
    text="What are the main goals of your application?",
    category="goals"
)
db.add(question)
db.commit()
db.refresh(question)

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

# Cleanup
try:
    db.query(Question).filter(Question.id == question.id).delete()
    db.query(SessionModel).filter(SessionModel.id == session.id).delete()
    db.query(Project).filter(Project.id == project.id).delete()
    db.commit()
except:
    pass
finally:
    db.close()
