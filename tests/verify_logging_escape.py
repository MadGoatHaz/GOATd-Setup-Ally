from rich.text import Text
from rich.markup import MarkupError, escape

def verify_markup(text, should_pass=True):
    print(f"Testing: '{text}'")
    try:
        Text.from_markup(text)
        print("  -> Parsed successfully")
        return True
    except MarkupError as e:
        print(f"  -> MarkupError: {e}")
        if not should_pass:
            return True # It failed as expected
        return False
    except Exception as e:
        print(f"  -> Unexpected error: {e}")
        return False

def verify_escape(text):
    print(f"Testing with escape(): '{text}'")
    escaped = escape(text)
    print(f"  -> Escaped: '{escaped}'")
    try:
        Text.from_markup(escaped)
        print("  -> Parsed successfully")
        return True
    except Exception as e:
        print(f"  -> Failed: {e}")
        return False

print("--- Verifying Problem ---")
# These should fail
fail_count = 0
scenarios = [
    "Error [/path/to/file] not found",
    "Executing [cmd arg]",
    "Standard output: [info] something"
]

for s in scenarios:
    if not verify_markup(s, should_pass=False):
        # It passed but we expected fail (or failed unexpectedly), wait.
        # If verify_markup returns True, it parsed successfully.
        # We expect it to FAIL (return False for 'should_pass=True').
        # My logic in verify_markup is a bit twisted.
        pass

# Let's just do it simpler
failures_expected = 0
for s in scenarios:
    try:
        Text.from_markup(s)
        print(f"  [UNEXPECTED PASS] '{s}'")
    except MarkupError:
        print(f"  [EXPECTED FAIL] '{s}'")
        failures_expected += 1

if failures_expected > 0:
    print(f"\nConfirmed: {failures_expected} strings caused MarkupError.")
else:
    print("\nWarning: Could not reproduce MarkupError.")

print("\n--- Verifying Fix Strategy ---")
# These should pass with escape
success_count = 0
for s in scenarios:
    if verify_escape(s):
        success_count += 1

if success_count == len(scenarios):
    print("\nSUCCESS: All scenarios passed when escaped.")
else:
    print("\nFAILURE: Some scenarios failed even when escaped.")