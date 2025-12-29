import re
# bunch of fucking danger shit, hardcoding shit that I KNOW will fuck shit up

def validate_command_safety(command):
    """
    Validate if a command is safe to execute.
    Checks for dangerous patterns and operations.
    """
    dangerous_patterns = [
        r'\brm\s+-rf\s+/',  # rm -rf / variations
        r'\brm\s+-fr\s+/',
        r'\bdd\s+if=/dev/zero\s+of=/dev/',  # dd to disk device
        r':\(\)\s*{\s*:\|:&\s*};:',  # Fork bomb
        r'>\s*/dev/sd[a-z]',  # Writing to disk devices
        r'\bmkfs\.',  # Format filesystem
        r'\bfdisk\b',  # Partition manipulation
        r'\bcryptsetup\b',  # Disk encryption
        r'\bchmod\s+-R\s+777\s+/',  # Dangerous permissions
        r'\bchown\s+-R.*\s+/',  # Recursive ownership change on /
    ]
    
    # Check for dangerous patterns
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "safe": False,
                "reason": f"Command contains dangerous pattern: {pattern}",
                "command": command
            }
    
    # Warn about sudo/root operations
    if re.search(r'\b(sudo|su\s)', command):
        return {
            "safe": True,
            "requires_elevation": True,
            "warning": "Command requires elevated privileges",
            "command": command
        }
    
    # Warn about system-wide changes
    system_dirs = ['/etc', '/sys', '/proc', '/boot', '/usr/bin', '/usr/sbin']
    for sysdir in system_dirs:
        if sysdir in command and any(word in command.lower() for word in ['rm', 'delete', 'write', '>']):
            return {
                "safe": True,
                "warning": f"Command modifies system directory: {sysdir}",
                "requires_caution": True,
                "command": command
            }
    
    return {
        "safe": True,
        "command": command
    }


def parse_command_intent(command):
    """
    Parse a command to understand what it does.
    Helps LLM understand command structure.
    """
    parts = command.split()
    if not parts:
        return {"error": "Empty command"}
    
    base_command = parts[0]
    
    # Common command categories
    destructive_commands = ['rm', 'rmdir', 'dd', 'mkfs', 'fdisk', 'shred']
    file_commands = ['cp', 'mv', 'touch', 'mkdir', 'cat', 'less', 'more', 'head', 'tail']
    network_commands = ['curl', 'wget', 'ping', 'netstat', 'ss', 'nmap']
    package_commands = ['apt', 'yum', 'dnf', 'pacman', 'pip', 'npm']
    system_commands = ['systemctl', 'service', 'chmod', 'chown', 'useradd', 'usermod']
    
    intent = {
        "command": base_command,
        "category": "other"
    }
    
    if base_command in destructive_commands:
        intent["category"] = "destructive"
        intent["requires_confirmation"] = True
    elif base_command in file_commands:
        intent["category"] = "file_operation"
    elif base_command in network_commands:
        intent["category"] = "network"
    elif base_command in package_commands:
        intent["category"] = "package_management"
        intent["may_require_sudo"] = True
    elif base_command in system_commands:
        intent["category"] = "system_management"
        intent["may_require_sudo"] = True
    
    return intent
