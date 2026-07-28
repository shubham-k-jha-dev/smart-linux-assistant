"""
Redacts sensitive information from shell commands and stderr before API transmission.
"""
import re

# Common patterns for secrets in CLI usage
SECRET_PATTERNS = [
    # Bearer tokens: Authorization: Bearer <token>
    (r'(?i)(bearer\s+)[\w\-\.\~]+', r'\1[REDACTED]'),
    
    # Environment variables or standard flags: API_KEY=xyz, DB_PASS="abc", --password="123"
    # -> Added 'pass' and 'pwd' to the keyword capture group
    (r'(?i)(api_?key|password|pass|pwd|secret|token|auth_?token)(\s*=\s*["\']?)[\w\-\.\~]+(["\']?)', r'\1\2[REDACTED]\3'),
    
    # Inline password flags: mysql -pMySecret (no space) or --password abc
    # -> Specifically looks for -p immediately followed by characters to avoid redacting ports (e.g. ssh -p 22)
    (r'(?i)(\s-p(?!\s)|\-\-password\s*=?\s*)[\w\-\.\~]+', r'\1[REDACTED]'),
    
    # AWS-style keys
    (r'(?i)(AKIA[0-9A-Z]{16})', r'[REDACTED_AWS_KEY]'),
    
    # Passwords in URLs: https://user:pass@host.com
    (r'(https?://[^:]+:)([^@]+)(@)', r'\1[REDACTED]\3')
]

def scrub_secrets(text: str) -> str:
    """
    Applies regex patterns to redact potential secrets from text.
    """
    if not text:
        return text
        
    redacted_text = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted_text = re.sub(pattern, replacement, redacted_text)
        
    return redacted_text