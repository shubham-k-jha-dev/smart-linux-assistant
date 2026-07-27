import subprocess
import os

# We will test the local CLI entrypoint
CLI_CMD = ["smart-linux"]

# Matrix of deliberate failures to test the exception hierarchy
test_cases = [
    # (Test Name, CLI Arguments, Environment Overrides)
    ("Command Not Found", ["run", "this_does_not_exist_123", "--check"], {}),
    ("Execution Timeout", ["run", "sleep 5", "--timeout", "1", "--check"], {}),
    ("Permission Denied", ["run", "cat /etc/shadow", "--check"], {}),
    ("Invalid CLI Flag", ["run", "ls --impossible-flag", "--check"], {}),
    ("Empty Command String", ["run", "   ", "--check"], {}),
    ("Missing API Key", ["explain", "ls /nope"], {"GROQ_API_KEY": ""}),
    ("Invalid API Key Auth", ["explain", "ls /nope"], {"GROQ_API_KEY": "gsk_invalid_fake_key"}),
    ("Invalid History Command", ["history", "--invalid-flag"], {}),
]

total = len(test_cases)
handled_cleanly = 0

print("========================================")
print("Initiating Fault Injection Matrix...")
print("========================================\n")

for name, args, env_override in test_cases:
    env = os.environ.copy()
    env.update(env_override)
    
    # Execute the command and capture stderr
    result = subprocess.run(
        CLI_CMD + args,
        capture_output=True,
        text=True,
        env=env
    )
    
    # A raw Python traceback means the exception hierarchy missed it
    if "Traceback (most recent call last):" in result.stderr:
        print(f"❌ {name}: FAILED (Leaked raw traceback)")
        print(f"   Snippet: {result.stderr.strip()[:100]}...\n")
    else:
        print(f"✅ {name}: CAUGHT CLEANLY")
        handled_cleanly += 1

coverage = (handled_cleanly / total) * 100

print("\n========================================")
print(f"Total Faults Injected: {total}")
print(f"Cleanly Handled: {handled_cleanly}")
print(f"Exception Hierarchy Coverage: {coverage:.1f}%")
print("========================================")
