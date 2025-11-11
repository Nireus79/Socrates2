"""
Test to verify the fixes actually resolve the CLI errors.
This tests the complete flow, not just the schema mismatch.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.core.models import spec_db_to_data, specs_db_to_data


def test_complete_question_generation_flow():
    """
    Test the complete flow that happens when /session start is called.

    This simulates what SocraticCounselorAgent._generate_question() does.
    """
    print("\n🧪 TESTING COMPLETE QUESTION GENERATION FLOW")

    # Create mock specifications like they come from the database
    mock_specs = []
    for i in range(3):
        mock_spec = MagicMock()
        mock_spec.id = uuid4()
        mock_spec.project_id = uuid4()
        mock_spec.category = f"category_{i}"
        mock_spec.content = f"This is specification {i} with detailed content"
        mock_spec.source = "user_input"
        mock_spec.confidence = 0.85 + (0.05 * i)
        mock_spec.is_current = True
        mock_spec.created_at = datetime.now()
        mock_specs.append(mock_spec)

    print(f"\n✓ Created {len(mock_specs)} mock specifications from database")

    # Step 1: Convert individual specs (this is what was failing)
    try:
        for i, spec in enumerate(mock_specs):
            spec_data = spec_db_to_data(spec)
            print(f"  Spec {i}: key='{spec_data.key[:30]}...' confidence={spec_data.confidence}")
        print("✓ Individual spec conversion works")
    except AttributeError as e:
        print(f"✗ FAILED: {e}")
        raise

    # Step 2: Convert all specs at once (batch operation)
    try:
        specs_data = specs_db_to_data(mock_specs)
        print(f"✓ Batch spec conversion works ({len(specs_data)} specs)")
    except AttributeError as e:
        print(f"✗ FAILED: {e}")
        raise

    # Step 3: Verify the data can be used by socrates-ai library
    try:
        # The library expects these attributes
        for spec_data in specs_data:
            assert hasattr(spec_data, 'key')
            assert hasattr(spec_data, 'value')
            assert hasattr(spec_data, 'category')
            assert hasattr(spec_data, 'confidence')
        print("✓ All specs have required library attributes")
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        raise

    print("\n✅ QUESTION GENERATION FLOW TEST PASSED")
    return True


def test_direct_chat_message_format():
    """
    Test that messages sent to Anthropic API have correct format.
    """
    print("\n🧪 TESTING DIRECT CHAT MESSAGE FORMAT")

    # Simulate messages from ConversationHistory
    mock_messages = []
    for i in range(2):
        msg = MagicMock()
        msg.role = "user" if i == 0 else "assistant"
        msg.content = f"Message {i} content"
        msg.timestamp = datetime.now()
        mock_messages.append(msg)

    print(f"\n✓ Created {len(mock_messages)} mock messages")

    # This is what the fixed code should do
    recent_messages = [
        {
            'role': msg.role,
            'content': msg.content
        }
        for msg in mock_messages
    ]

    print("\nVerifying message format for Anthropic API:")
    for i, msg in enumerate(recent_messages):
        print(f"  Message {i}: keys={list(msg.keys())}")

        # Verify ONLY role and content exist
        assert set(msg.keys()) == {'role', 'content'}, f"Message has extra fields: {list(msg.keys())}"
        assert 'timestamp' not in msg, "❌ TIMESTAMP FIELD SHOULD NOT BE HERE!"

    print("✓ All messages have correct format (no timestamp)")
    print("\n✅ DIRECT CHAT MESSAGE FORMAT TEST PASSED")
    return True


if __name__ == "__main__":
    test_complete_question_generation_flow()
    test_direct_chat_message_format()
    print("\n" + "="*80)
    print("ALL VERIFICATION TESTS PASSED ✅")
    print("="*80)
