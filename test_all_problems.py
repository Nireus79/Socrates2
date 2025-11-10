#!/usr/bin/env python3
"""
Comprehensive problem identification test.
Tests actual use cases that are failing in the CLI.
"""

import sys
import os
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_json_parsing_with_markdown():
    """Test if parse_intent handles markdown-wrapped JSON"""
    print("\n[Problem 1] Testing JSON parsing with markdown code blocks...")
    try:
        from app.core.dependencies import ServiceContainer

        services = ServiceContainer()
        nlu_service = services.get_nlu_service()

        # Test with a simple operation request
        intent = nlu_service.parse_intent("login with username test and password test123")

        if intent.is_operation or (not intent.is_operation and intent.response):
            print("  [PASS] Intent parsing works despite markdown issue")
            return True
        else:
            print("  [FAIL] Intent parsing returning empty response")
            return False

    except json.JSONDecodeError as e:
        print(f"  [FAIL] JSON parsing error: {e}")
        print("        Claude is likely returning markdown-wrapped JSON")
        return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_agent_registration():
    """Test if agents are properly registered in orchestrator"""
    print("\n[Problem 2] Testing agent registration...")
    try:
        from app.agents.orchestrator import AgentOrchestrator, initialize_default_agents
        from app.core.dependencies import ServiceContainer

        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        # Initialize agents
        initialize_default_agents(orchestrator)

        agents = orchestrator.agents

        print(f"  Registered agents: {len(agents)}")
        for agent_id, agent in list(agents.items())[:5]:
            print(f"    - {agent_id}: {agent.name}")

        if len(agents) > 0:
            print("  [PASS] Agents properly registered")
            return True
        else:
            print("  [FAIL] No agents registered")
            return False

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_socratic_agent_response():
    """Test if SocraticCounselorAgent returns proper response"""
    print("\n[Problem 3] Testing SocraticCounselorAgent response...")
    try:
        from app.agents.orchestrator import AgentOrchestrator, initialize_default_agents
        from app.core.dependencies import ServiceContainer
        from app.core.database import SessionLocalSpecs
        from app.models.project import Project
        from app.models.session import Session as SessionModel
        from datetime import datetime, timezone

        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        # Initialize agents
        initialize_default_agents(orchestrator)

        # Need to create a test project and session in database
        db = SessionLocalSpecs()

        try:
            # Create a minimal project with all required fields
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

            # Try to generate a question
            result = orchestrator.route_request(
                'socratic',
                'generate_question',
                {
                    'project_id': str(project.id),
                    'session_id': str(session.id)
                }
            )

            print(f"  Response success: {result.get('success')}")
            if result.get('success'):
                print(f"  Question generated: {result.get('question', {}).get('text', '')[:50]}...")
                print("  [PASS] SocraticCounselorAgent working")
                return True
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
                print("  [FAIL] SocraticCounselorAgent returning error")
                return False

        finally:
            # Cleanup
            try:
                db.query(SessionModel).filter(SessionModel.id == session.id).delete()
                db.query(Project).filter(Project.id == project.id).delete()
                db.commit()
            except:
                pass
            db.close()

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_analyzer_response():
    """Test if ContextAnalyzerAgent works"""
    print("\n[Problem 4] Testing ContextAnalyzerAgent response...")
    try:
        from app.agents.orchestrator import AgentOrchestrator, initialize_default_agents
        from app.core.dependencies import ServiceContainer
        from app.core.database import SessionLocalSpecs
        from app.models.project import Project
        from app.models.session import Session as SessionModel
        from app.models.question import Question
        from datetime import datetime, timezone

        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        # Initialize agents
        initialize_default_agents(orchestrator)

        db = SessionLocalSpecs()

        try:
            # Create test project and session with proper IDs
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

            if result and result.get('success'):
                print(f"  Specs extracted: {result.get('specs_extracted', 0)}")
                print("  [PASS] ContextAnalyzerAgent working")
                return True
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
                print("  [FAIL] ContextAnalyzerAgent returning error")
                return False

        finally:
            # Cleanup
            try:
                db.query(Question).filter(Question.id == question.id).delete()
                db.query(SessionModel).filter(SessionModel.id == session.id).delete()
                db.query(Project).filter(Project.id == project.id).delete()
                db.commit()
            except:
                pass
            db.close()

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_chat_agent():
    """Test if DirectChatAgent works"""
    print("\n[Problem 5] Testing DirectChatAgent response...")
    try:
        from app.agents.orchestrator import AgentOrchestrator, initialize_default_agents
        from app.core.dependencies import ServiceContainer
        from app.core.database import SessionLocalSpecs
        from app.models.project import Project
        from app.models.session import Session as SessionModel
        from datetime import datetime, timezone

        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        # Initialize agents
        initialize_default_agents(orchestrator)

        db = SessionLocalSpecs()

        try:
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

            session = SessionModel(
                project_id=project.id,
                status='active',
                mode='direct_chat',
                started_at=datetime.now(timezone.utc)
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            # Test direct chat
            result = orchestrator.route_request(
                'direct_chat',
                'process_chat_message',
                {
                    'session_id': str(session.id),
                    'user_id': str(project.user_id),
                    'message': 'Hello, I need help',
                    'project_id': str(project.id)
                }
            )

            if result and result.get('success'):
                response = result.get('response', '')
                print(f"  Chat response: {response[:50]}..." if response else "  No response")
                print("  [PASS] DirectChatAgent working")
                return True
            else:
                print(f"  Error: {result.get('error', 'Unknown error') if result else 'No result'}")
                print("  [FAIL] DirectChatAgent returning error")
                return False

        finally:
            try:
                db.query(SessionModel).filter(SessionModel.id == session.id).delete()
                db.query(Project).filter(Project.id == project.id).delete()
                db.commit()
            except:
                pass
            db.close()

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("COMPREHENSIVE PROBLEM IDENTIFICATION TEST")
    print("="*60)

    results = {
        "JSON Parsing with Markdown": test_json_parsing_with_markdown(),
        "Agent Registration": test_agent_registration(),
        "SocraticCounselorAgent": test_socratic_agent_response(),
        "ContextAnalyzerAgent": test_context_analyzer_response(),
        "DirectChatAgent": test_direct_chat_agent(),
    }

    print("\n" + "="*60)
    print("PROBLEM SUMMARY")
    print("="*60)

    for problem, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {problem}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTotal: {passed}/{total} working")

    if passed < total:
        print(f"\nIdentified {total - passed} problem(s) to fix")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
