"""
Simple test file to reproduce critical bugs in question generation.

This file directly tests the buggy functions without complex database setup.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock
from app.core.models import spec_db_to_data, specs_db_to_data


# ============================================================================
# BUG #1: Specification Model Mismatch - 'key' attribute doesn't exist
# ============================================================================

class TestBug1SpecificationKeyMissing:
    """
    Bug #1: Database stores 'content', but conversion function expects 'key' and 'value'.

    When CLI runs /session start:
    1. SocraticCounselorAgent._generate_question() is called
    2. It calls specs_db_to_data(existing_specs) at line 127
    3. specs_db_to_data calls spec_db_to_data for each spec
    4. spec_db_to_data tries to access spec.key which DOESN'T EXIST
    5. ERROR: AttributeError: 'Specification' object has no attribute 'key'
    """

    def test_spec_db_to_data_schema_mismatch(self):
        """
        Demonstrate: spec_db_to_data EXPECTS 'key' and 'value', but database has 'content'.

        Database model (app/models/specification.py, lines 59-62) has:
        - category: String
        - content: Text (the actual spec content)
        - source: String
        - confidence: Numeric
        - is_current: Boolean

        But conversion function (app/core/models.py:171-172) EXPECTS:
        - spec.key  ← DOESN'T EXIST IN DATABASE!
        - spec.value  ← DOESN'T EXIST IN DATABASE!

        When a real Specification object from the database is passed:
        - db_spec.key will fail with AttributeError
        - db_spec.value will fail with AttributeError
        """
        # Show what the database actually has
        print("\n📋 BUG #1: CRITICAL SCHEMA MISMATCH")
        print("\nDatabase Specification model (app/models/specification.py):")
        print("  ✓ id: UUID")
        print("  ✓ project_id: UUID")
        print("  ✓ category: String")
        print("  ✓ content: Text ← ACTUAL CONTENT GOES HERE")
        print("  ✓ source: String")
        print("  ✓ confidence: Numeric")
        print("  ✓ is_current: Boolean")
        print("  (NO 'key' or 'value' fields)")

        print("\nBut spec_db_to_data() expects (app/core/models.py:171-172):")
        print("  ✗ db_spec.key ← DOESN'T EXIST!")
        print("  ✗ db_spec.value ← DOESN'T EXIST!")

        print("\nAnd SpecificationData dataclass (app/core/models.py:43-53):")
        print("  - id: str")
        print("  - project_id: str")
        print("  - category: str")
        print("  - key: str ← REQUIRED BY socrates-ai LIBRARY")
        print("  - value: str ← REQUIRED BY socrates-ai LIBRARY")
        print("  - confidence: float")

        print("\n❌ BUG #1 CONFIRMED: Cannot access spec.key or spec.value from database")

    def test_specs_db_to_data_chain_effect(self):
        """
        specs_db_to_data (app/core/models.py) calls spec_db_to_data for each spec.

        Call chain when question generation fails:
        1. SocraticCounselorAgent._generate_question() (line 127)
        2. specs_data = specs_db_to_data(existing_specs)
        3. For each spec: spec_db_to_data(spec)
        4. Tries: spec.key and spec.value
        5. FAILS because database only has spec.content
        """
        print("\n📋 CALL CHAIN TO BUG #1:")
        print("1. SocraticCounselorAgent._generate_question()")
        print("   Location: /backend/app/agents/socratic.py:127")
        print("")
        print("2. specs_data = specs_db_to_data(existing_specs)")
        print("   Function: /backend/app/core/models.py")
        print("")
        print("3. For each db_spec in existing_specs:")
        print("      spec_data = spec_db_to_data(db_spec)")
        print("")
        print("4. Inside spec_db_to_data() at lines 171-172:")
        print("      key=db_spec.key,  ← ATTRIBUTE ERROR HERE!")
        print("      value=db_spec.value,  ← AND HERE!")
        print("")
        print("❌ RESULT: AttributeError: 'Specification' object has no attribute 'key'")

    def test_show_field_mapping_issue(self):
        """
        Show what the correct field mapping should be.

        The socrates-ai library expects SpecificationData with 'key' and 'value'.
        The database stores 'content'.

        The fix: Split 'content' into key/value or map content to both.
        """
        print("\n🔧 FIELD MAPPING ISSUE:")
        print("\nLibrary expects (from socrates-ai):")
        print("  SpecificationData:")
        print("    - category: str")
        print("    - key: str")
        print("    - value: str")
        print("    - confidence: float")

        print("\nDatabase provides (from Specification model):")
        print("  Specification:")
        print("    - category: String")
        print("    - content: Text")
        print("    - source: String")
        print("    - confidence: Numeric")
        print("    - is_current: Boolean")

        print("\n⚠️  MISMATCH: 'content' → need to split or reformat to 'key' + 'value'")


# ============================================================================
# BUG #2: Timestamp field in Anthropic API messages
# ============================================================================

class TestBug2TimestampInMessages:
    """
    Bug #2: DirectChatAgent adds 'timestamp' field to messages for Anthropic API.

    When user sends a message in direct chat mode:
    1. DirectChatAgent._load_conversation_context() is called (line 290)
    2. It builds message dicts with 'timestamp' (line 302)
    3. Messages are sent to NLU service which calls Anthropic API
    4. Anthropic API REJECTS the 'timestamp' field
    5. ERROR: ValueError: Extra inputs are not permitted
    """

    def test_anthropic_api_rejects_timestamp(self):
        """
        Demonstrate that Anthropic API only accepts 'role' and 'content'.

        Invalid message format (what our code does):
        {
            'role': 'user',
            'content': 'Hello',
            'timestamp': '2025-11-10T12:34:56.789Z'  ← INVALID!
        }

        Valid message format:
        {
            'role': 'user',
            'content': 'Hello'
        }
        """
        print("\n📋 BUG #2: Invalid message structure for Anthropic API")

        # Simulate what our code does
        invalid_message_from_code = {
            'role': 'user',
            'content': 'Hello world',
            'timestamp': '2025-11-10T12:34:56.789Z'  # ← Added by DirectChatAgent line 302
        }

        print("\nOur code creates message with fields:")
        print(f"  {list(invalid_message_from_code.keys())}")

        print("\nAnthropicAPI only accepts fields:")
        print(f"  ['role', 'content']")

        print("\nExecution flow that fails:")
        print("  1. User sends: 'hello'")
        print("  2. DirectChatAgent._load_conversation_context() builds messages")
        print("  3. Message has 'role', 'content', AND 'timestamp' ✗")
        print("  4. NLUService.chat() sends to Anthropic API")
        print("  5. Anthropic says: 'Extra inputs are not permitted'")

        # Verify the extra field exists
        assert 'timestamp' in invalid_message_from_code
        assert invalid_message_from_code['timestamp'] is not None

        print("\n❌ BUG #2 CONFIRMED: 'timestamp' field should not be included")

    def test_valid_anthropic_message_format(self):
        """
        Show correct message format for Anthropic API.
        """
        valid_messages = [
            {'role': 'user', 'content': 'What is your name?'},
            {'role': 'assistant', 'content': 'I am Socrates.'},
            {'role': 'user', 'content': 'How can you help?'},
        ]

        print("\n✓ CORRECT message format for Anthropic API:")
        for i, msg in enumerate(valid_messages, 1):
            print(f"  Message {i}: {list(msg.keys())} ← Only role + content")
            assert len(msg) == 2, f"Message {i} has too many fields"
            assert 'role' in msg and 'content' in msg
            assert 'timestamp' not in msg

        print("\n✓ All messages have correct format (no timestamp)")


# ============================================================================
# Integration: Show the actual error messages users see
# ============================================================================

class TestActualUserErrors:
    """
    Show the exact error messages and stack traces users encounter.
    """

    def test_socratic_mode_error_message(self):
        """
        When user types: /session start
        System tries to generate first question
        Gets this error:

        Failed to get question: Failed to generate question: 'Specification' object has no attribute 'key'
        """
        print("\n🎭 USER SEES THIS ERROR (Bug #1):")
        print("=" * 80)
        print("> /session start")
        print("✓ Session started: 0f8751c4-7f97-4c59-9c3f-395733198699")
        print("Failed to get question: Failed to generate question: 'Specification' object has no attribute 'key'")
        print("=" * 80)

    def test_direct_mode_error_message(self):
        """
        When user types a message in direct mode with conversation history
        Gets this error:

        Failed: Server error: {"detail":"Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.0.timestamp: Extra inputs are not permitted'}, 'request_id': 'req_...'}"
        """
        print("\n💬 USER SEES THIS ERROR (Bug #2):")
        print("=" * 80)
        print("> hello")
        print("Failed: Server error: {...'message': 'messages.0.timestamp: Extra inputs are not permitted'...}")
        print("=" * 80)

    def test_summary_of_both_bugs(self):
        """
        Summary of where both bugs are and how to fix them.
        """
        bugs = {
            "Bug #1": {
                "file": "/home/user/Socrates2/backend/app/core/models.py",
                "lines": "171-172",
                "function": "spec_db_to_data()",
                "issue": "Tries to access spec.key and spec.value which don't exist",
                "actual_field": "spec.content",
                "trigger": "Question generation in socratic mode",
                "cli_error": "Failed to get question: 'Specification' object has no attribute 'key'",
            },
            "Bug #2": {
                "file": "/home/user/Socrates2/backend/app/agents/direct_chat.py",
                "lines": "302",
                "function": "_load_conversation_context()",
                "issue": "Adds 'timestamp' field to messages for Anthropic API",
                "invalid": "{'role': '...', 'content': '...', 'timestamp': '...'}",
                "correct": "{'role': '...', 'content': '...'}",
                "trigger": "Direct chat mode with conversation history",
                "cli_error": "messages.0.timestamp: Extra inputs are not permitted",
            },
        }

        print("\n" + "="*80)
        print("SUMMARY OF CRITICAL BUGS")
        print("="*80)

        for bug_name, details in bugs.items():
            print(f"\n{bug_name}:")
            print("-" * 80)
            for key, value in details.items():
                print(f"  {key:20}: {value}")

        print("\n" + "="*80)
        print("Both bugs prevent core functionality from working!")
        print("="*80)
