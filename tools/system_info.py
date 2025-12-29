import os
import subprocess
import platform
import shutil
from pathlib import Path


def get_file_tree(path, max_depth=3):
    """
    Get directory structure without assuming.
    Returns the tree as a string or error dict.
    """
    if not os.path.exists(path):
        return {"error": f"Path {path} does not exist"}
    
    tree = []
    try:
        path = os.path.abspath(path)
        tree.append(f"{path}/")
        
        for root, dirs, files in os.walk(path):
            level = root.replace(path, '').count(os.sep)
            if level >= max_depth:
                dirs[:] = []  # Don't descend further
                continue
            
            indent = '  ' * (level + 1)
            
            # Show directories
            for d in sorted(dirs):
                tree.append(f"{indent}{d}/")
            
            # Show files
            for f in sorted(files):
                tree.append(f"{indent}{f}")
                
    except PermissionError as e:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Error reading directory: {str(e)}"}
    
    return "\n".join(tree[:500])  # Limit output


def check_file_exists(path):
    """Check if a file or directory exists"""
    abs_path = os.path.abspath(path)
    exists = os.path.exists(abs_path)
    
    result = {
        "path": abs_path,
        "exists": exists
    }
    
    if exists:
        result["is_file"] = os.path.isfile(abs_path)
        result["is_directory"] = os.path.isdir(abs_path)
        result["is_symlink"] = os.path.islink(abs_path)
        
        try:
            stat = os.stat(abs_path)
            result["size_bytes"] = stat.st_size
            result["readable"] = os.access(abs_path, os.R_OK)
            result["writable"] = os.access(abs_path, os.W_OK)
            result["executable"] = os.access(abs_path, os.X_OK)
        except:
            pass
    
    return result


def check_port_in_use(port):
    """Check if a network port is already in use"""
    try:
        # Try using ss command (more reliable)
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        in_use = f":{port}" in result.stdout
        
        # Try to find what's using the port
        process_info = None
        if in_use:
            try:
                proc_result = subprocess.run(
                    ['ss', '-tulnp'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in proc_result.stdout.split('\n'):
                    if f":{port}" in line:
                        process_info = line.strip()
                        break
            except:
                pass
        
        return {
            "port": port,
            "in_use": in_use,
            "process_info": process_info
        }
        
    except FileNotFoundError:
        # Fallback to netstat if ss is not available
        try:
            result = subprocess.run(
                ['netstat', '-tuln'],
                capture_output=True,
                text=True,
                timeout=5
            )
            in_use = f":{port}" in result.stdout
            return {
                "port": port,
                "in_use": in_use
            }
        except:
            return {"error": "Cannot check port - neither ss nor netstat available"}
    
    except Exception as e:
        return {"error": f"Error checking port: {str(e)}"}


def get_disk_space(path="/"):
    """Get available disk space for a path"""
    try:
        stat = os.statvfs(path)
        
        # Calculate sizes
        total_bytes = stat.f_blocks * stat.f_frsize
        free_bytes = stat.f_bfree * stat.f_frsize
        available_bytes = stat.f_bavail * stat.f_frsize
        used_bytes = total_bytes - free_bytes
        
        return {
            "path": path,
            "total_gb": round(total_bytes / (1024**3), 2),
            "used_gb": round(used_bytes / (1024**3), 2),
            "free_gb": round(free_bytes / (1024**3), 2),
            "available_gb": round(available_bytes / (1024**3), 2),
            "percent_used": round((used_bytes / total_bytes) * 100, 1) if total_bytes > 0 else 0
        }
    except Exception as e:
        return {"error": f"Error getting disk space: {str(e)}"}


def get_system_info():
    """Get basic system information"""
    try:
        info = {
            "hostname": subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip(),
            "kernel": subprocess.run(['uname', '-r'], capture_output=True, text=True).stdout.strip(),
            "os": subprocess.run(['uname', '-s'], capture_output=True, text=True).stdout.strip(),
        }
        
        # Try to get distro info
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        info['distro'] = line.split('=')[1].strip().strip('"')
                        break
        except:
            pass
        
        return info
    except Exception as e:
        return {"error": f"Error getting system info: {str(e)}"}


def get_platform_info():
    """Get OS and shell information for command generation context"""
    info = {}
    
    # Detect OS
    system = platform.system()
    info['os'] = system
    info['os_version'] = platform.version()
    info['architecture'] = platform.machine()
    
    if system == 'Linux':
        info['platform'] = 'Linux'
        # Try to get distro info
        try:
            with open('/etc/os-release', 'r') as f:
                distro_info = {}
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        distro_info[key] = value.strip('"')
                info['distro'] = distro_info.get('PRETTY_NAME', 'Unknown Linux')
                info['distro_id'] = distro_info.get('ID', 'unknown')
        except:
            info['distro'] = 'Unknown Linux'
    elif system == 'Darwin':
        info['platform'] = 'macOS'
        info['distro'] = f"macOS {platform.mac_ver()[0]}"
    elif system == 'Windows':
        info['platform'] = 'Windows'
        info['distro'] = platform.win32_ver()[0]
    else:
        info['platform'] = system
    
    # Detect shell
    shell_info = detect_shell()
    info.update(shell_info)
    
    return info


def detect_shell():
    """Detect the current shell being used"""
    shell_info = {}
    
    # Try to detect from environment variables
    shell_path = os.environ.get('SHELL', '')
    if shell_path:
        shell_name = os.path.basename(shell_path)
        shell_info['shell'] = shell_name
        shell_info['shell_path'] = shell_path
    
    # On Windows, check for PowerShell or cmd
    if platform.system() == 'Windows':
        # Check if running in PowerShell
        if os.environ.get('PSModulePath'):
            shell_info['shell'] = 'PowerShell'
            shell_info['shell_type'] = 'PowerShell'
            # Check if it's PowerShell Core (pwsh) or Windows PowerShell
            if 'pwsh' in os.environ.get('PROMPT', '').lower() or os.environ.get('POWERSHELL_DISTRIBUTION_CHANNEL'):
                shell_info['shell_version'] = 'PowerShell Core (pwsh)'
            else:
                shell_info['shell_version'] = 'Windows PowerShell'
        else:
            shell_info['shell'] = 'cmd'
            shell_info['shell_type'] = 'cmd'
    else:
        # On Unix-like systems, try to get shell type
        if 'bash' in shell_path:
            shell_info['shell_type'] = 'bash'
        elif 'zsh' in shell_path:
            shell_info['shell_type'] = 'zsh'
        elif 'fish' in shell_path:
            shell_info['shell_type'] = 'fish'
        elif 'sh' in shell_path:
            shell_info['shell_type'] = 'sh'
        else:
            shell_info['shell_type'] = 'unknown'
    
    return shell_info


def build_shell_command(cmd: str):
    """
    Build a subprocess command list that executes the given string `cmd`
    using the user's detected shell on the current platform.

    - Windows PowerShell: [pwsh|powershell, -NoProfile, -ExecutionPolicy Bypass, -Command, cmd]
    - Windows cmd: [cmd, /c, cmd]
    - Unix-like (Linux/macOS): [SHELL or /bin/bash, -lc, cmd]
    """
    info = get_platform_info()
    system = info.get('platform') or platform.system()

    if system == 'Windows':
        # Prefer PowerShell if detected, default to cmd otherwise
        shell_type = info.get('shell_type') or info.get('shell') or ''

        # Find pwsh (PowerShell Core) or powershell.exe
        pwsh_path = shutil.which('pwsh')
        powershell_path = shutil.which('powershell') or shutil.which('powershell.exe')

        if 'PowerShell' in shell_type or shell_type.lower() == 'powershell':
            exe = pwsh_path or powershell_path or 'powershell'
            return [exe, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', cmd]
        else:
            # Fallback to cmd
            cmd_exe = shutil.which('cmd') or 'cmd'
            return [cmd_exe, '/c', cmd]
    else:
        # Unix-like: use login shell if available, else bash
        shell = os.environ.get('SHELL') or shutil.which('bash') or '/bin/sh'
        return [shell, '-lc', cmd]
