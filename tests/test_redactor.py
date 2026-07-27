import pytest
from linux_assistant.utils.redactor import scrub_secrets

def test_scrub_export_statements():
    raw = 'export GROQ_API_KEY="gsk_123456789"'
    expected = 'export GROQ_API_KEY="[REDACTED]"'
    assert scrub_secrets(raw) == expected

def test_scrub_inline_passwords():
    raw = 'mysql -u admin -pMySecretPassword123 database'
    # We want to catch standard password flags
    assert "[REDACTED]" in scrub_secrets(raw)
    assert "MySecretPassword123" not in scrub_secrets(raw)

def test_scrub_bearer_tokens():
    raw = 'curl -H "Authorization: Bearer eyJhbGciOi..." http://api.com'
    expected = 'curl -H "Authorization: Bearer [REDACTED]" http://api.com'
    assert scrub_secrets(raw) == expected

def test_leave_safe_commands_alone():
    raw = 'ls -la /var/log'
    assert scrub_secrets(raw) == raw

def test_multiple_secrets_in_one_line():
    raw = 'export DB_PASS=pass123 && curl -H "Authorization: Bearer abc" http://x'
    scrubbed = scrub_secrets(raw)
    assert "pass123" not in scrubbed
    assert "abc" not in scrubbed
    assert scrubbed.count("[REDACTED]") == 2