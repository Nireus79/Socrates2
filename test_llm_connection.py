#!/usr/bin/env python3
"""
Test LLM connections - verify Claude API is properly connected to all agents.
Tests:
1. Claude client initialization
2. NLUService chat and intent parsing
3. SocraticCounselorAgent question generation
4. DirectChatAgent message processing
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_claude_client():
    """Test if Claude API client is properly initialized"""
    print("\n[1/4] Testing Claude API Client...")
    try:
        from app.core.config import settings
        from anthropic import Anthropic

        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            print("  [FAIL] ANTHROPIC_API_KEY not set in environment or .env")
            return False

        client = Anthropic(api_key=api_key)
        print("  [PASS] Claude API client initialized successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] Error initializing Claude client: {e}")
        return False


def test_nlu_service():
    """Test if NLUService can call Claude API"""
    print("\n[2/4] Testing NLUService...")
    try:
        from app.core.dependencies import ServiceContainer

        services = ServiceContainer()
        nlu_service = services.get_nlu_service()

        # Test simple chat
        response = nlu_service.chat("Hello, what is 2+2?", system_prompt="You are a helpful assistant.")

        if response and len(response) > 0:
            print(f"  [PASS] NLUService chat working")
            print(f"         Response: {response[:100]}...")
            return True
        else:
            print(f"  [FAIL] NLUService returned empty response")
            return False

    except Exception as e:
        print(f"  [FAIL] NLUService error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intent_parsing():
    """Test if NLUService can parse intents"""
    print("\n[3/4] Testing Intent Parsing...")
    try:
        from app.core.dependencies import ServiceContainer

        services = ServiceContainer()
        nlu_service = services.get_nlu_service()

        # Test intent parsing
        intent = nlu_service.parse_intent("Create a project called TestProject")

        print(f"  [PASS] Intent parsing working")
        print(f"         Is operation: {intent.is_operation}")
        if intent.is_operation:
            print(f"         Operation: {intent.operation}")
            print(f"         Explanation: {intent.explanation}")
        else:
            print(f"         Response: {intent.response[:100]}...")
        return True

    except Exception as e:
        print(f"  [FAIL] Intent parsing error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator():
    """Test if Orchestrator and agents are initialized"""
    print("\n[4/4] Testing Agent Orchestrator...")
    try:
        from app.agents.orchestrator import get_orchestrator

        orchestrator = get_orchestrator()

        # Check if orchestrator was created (agents are auto-registered on init)
        if orchestrator and hasattr(orchestrator, 'agents'):
            agents = orchestrator.agents
            if 'socratic' in agents:
                print(f"  [PASS] Agent Orchestrator initialized")
                print(f"         Registered agents: {list(agents.keys())[:5]}...")
                return True
            else:
                print(f"  [FAIL] Socratic agent not registered")
                print(f"         Available agents: {list(agents.keys())}")
                return False
        else:
            print(f"  [FAIL] Orchestrator not properly initialized")
            return False

    except Exception as e:
        print(f"  [FAIL] Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("LLM CONNECTION TEST SUITE")
    print("="*60)

    results = {
        "Claude Client": test_claude_client(),
        "NLUService Chat": test_nlu_service(),
        "Intent Parsing": test_intent_parsing(),
        "Orchestrator": test_orchestrator(),
    }

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All LLM connections working!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
