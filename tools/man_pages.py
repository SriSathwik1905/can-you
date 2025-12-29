import subprocess


def get_man_page(command):
    """
    Fetch man page content for a command.
    Returns the full man page or an error message.
    """
    try:
        result = subprocess.run(
            ['man', command],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Limit output to avoid token overflow
            lines = result.stdout.split('\n')
            if len(lines) > 500:
                return '\n'.join(lines[:500]) + f"\n\n... (truncated, {len(lines) - 500} more lines)"
            return result.stdout
        else:
            return {"error": f"No man page found for '{command}'"}
            
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout fetching man page for '{command}'"}
    except FileNotFoundError:
        return {"error": "man command not available on this system"}
    except Exception as e:
        return {"error": f"Error fetching man page: {str(e)}"}


def get_command_help(command):
    """
    Get --help output for a command.
    Faster alternative to man pages.
    """
    try:
        # Try --help first
        result = subprocess.run(
            [command, '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout + result.stderr
        
        if output.strip():
            # Limit output
            lines = output.split('\n')
            if len(lines) > 300:
                return '\n'.join(lines[:300]) + f"\n\n... (truncated, {len(lines) - 300} more lines)"
            return output
        
        # Try -h as fallback
        result = subprocess.run(
            [command, '-h'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout + result.stderr
        if output.strip():
            lines = output.split('\n')
            if len(lines) > 300:
                return '\n'.join(lines[:300]) + f"\n\n... (truncated)"
            return output
        
        return {"error": f"No help output available for '{command}'"}
        
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout getting help for '{command}'"}
    except FileNotFoundError:
        return {"error": f"Command '{command}' not found"}
    except Exception as e:
        return {"error": f"Error getting help: {str(e)}"}


def check_command_exists(command):
    """Check if a command exists on the system"""
    try:
        result = subprocess.run(
            ['which', command],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        exists = result.returncode == 0
        
        return {
            "command": command,
            "exists": exists,
            "path": result.stdout.strip() if exists else None
        }
    except Exception as e:
        return {"error": f"Error checking command: {str(e)}"}
