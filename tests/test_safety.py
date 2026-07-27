"""
Tests for the safety interceptor.
"""
from linux_assistant.core.safety import is_dangerous_command

def test_safe_commands():
    assert not is_dangerous_command("ls -la /var/log")
    assert not is_dangerous_command("echo 'hello world'")
    assert not is_dangerous_command("git status")
    assert not is_dangerous_command("cat /etc/os-release")

def test_dangerous_commands():
    assert is_dangerous_command("rm -rf /")
    assert is_dangerous_command("sudo rm -f /var/log/syslog")
    assert is_dangerous_command("dd if=/dev/zero of=/dev/nvme0n1")
    assert is_dangerous_command("mkfs.ext4 /dev/sda1")
    assert is_dangerous_command("chmod -R 777 /var/www/html")
    assert is_dangerous_command("echo 'wipe' > /dev/sda")