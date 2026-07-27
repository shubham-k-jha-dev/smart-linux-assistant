import re

def scrub_secrets(command: str) -> str:
    """
    Scans a raw terminal command and replaces sensitive API keys, passwords, tokens with [REDACTED] to ensure safe LLM transit. 
    """
    command = re.sub(
        r'(?i)([A-Z0-9_]*(?:KEY|TOKEN|PASSWORD|SECRET|PASS)[A-Z0-9_]*\s*=\s*["\']?)[^"\'\s]+(["\']?)',
        r'\g<1>[REDACTED]\g<2>',
        command 
    )
    
    command = re.sub(
        r'(-p|--password=?)\s*(["\']?)[^"\'\s]+(["\']?)',
        r'\1\2[REDACTED]\3',
        command
    )
    
    command = re.sub(
        r'([Bb]earer\s+)(["\']?)[^"\'\s]+(["\']?)',
        r'\1\2[REDACTED]\3',
        command
    )
    
    return command