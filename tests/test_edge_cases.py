#!/usr/bin/env python
"""Test the 3 fixed edge case patterns"""

import sys
sys.path.insert(0, '.')

from Socrates import IntentParser

parser = IntentParser()

# Test the 3 edge cases
test_cases = [
    ('create an application', '/code generate'),
    ('show me the code status', '/code status'),
    ('show preview for gen_789', '/code preview'),
]

print('Testing 3 Edge Cases:')
print('=' * 70)

passed = 0
failed = 0

for input_text, expected_cmd in test_cases:
    result = parser.parse(input_text)
    if result:
        matches = expected_cmd in result['command']
        status = 'PASS' if matches else 'FAIL'
        if matches:
            passed += 1
        else:
            failed += 1
        print(f'[{status}] Input: "{input_text}"')
        print(f'       → Command: {result["command"]}')
        print(f'       → Confidence: {result["confidence"]}')
        print(f'       → Args: {result["args"]}')
    else:
        failed += 1
        print(f'[FAIL] Input: "{input_text}"')
        print(f'       → No match found')
    print()

print('=' * 70)
print(f'Results: {passed} PASSED, {failed} FAILED')
print(f'Status: {"100% PASSING" if failed == 0 else "INCOMPLETE"}')
