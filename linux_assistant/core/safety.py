"""
Safety heuristics and guardrails for command execution.
"""

import re

# Regex patterns for highly destructive Linux commands
DANGEROUS_PATTERNS = [
    r"rm\s+-r?[fF]",          # rm -rf, rm -f
    r"dd\s+if=",              # destructive disk copies
    r"mkfs\.",                # formatting partitions
    r"chmod\s+-R\s+777",      # recursive full permissions
    r"chown\s+-R",            # recursive chown
    r">\s*/dev/sda",          # redirecting output directly to disk
    r"mv\s+.*?\s+/dev/null"   # moving files to null
]

def is_dangerous_command(command: str) -> bool:
    """
    Scans a command string for known destructive patterns.
    Returns True if a dangerous pattern is detected, False otherwise.
    """
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False