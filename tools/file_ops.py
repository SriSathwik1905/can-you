import os


def read_config_file(path, max_lines=100):
    """
    Read contents of a configuration file.
    Limits output to avoid token overflow.
    """
    try:
        if not os.path.exists(path):
            return {"error": f"File does not exist: {path}"}
        
        if not os.path.isfile(path):
            return {"error": f"Path is not a file: {path}"}
        
        if not os.access(path, os.R_OK):
            return {"error": f"Permission denied reading: {path}"}
        
        # Check file size
        size = os.path.getsize(path)
        if size > 1024 * 1024:  # 1MB
            return {"error": f"File too large to read: {size} bytes"}
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"\n... (truncated, showing first {max_lines} lines)")
                    break
                lines.append(line.rstrip())
        
        return {
            "path": path,
            "content": '\n'.join(lines),
            "truncated": len(lines) > max_lines
        }
        
    except UnicodeDecodeError:
        return {"error": f"File is not a text file or has incompatible encoding: {path}"}
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}


def check_write_permission(path):
    """Check if the current user has write permission to a path"""
    try:
        # Check if path exists
        if os.path.exists(path):
            writable = os.access(path, os.W_OK)
            return {
                "path": path,
                "exists": True,
                "writable": writable
            }
        else:
            # Check parent directory for new file creation
            parent = os.path.dirname(os.path.abspath(path))
            if os.path.exists(parent):
                writable = os.access(parent, os.W_OK)
                return {
                    "path": path,
                    "exists": False,
                    "parent_writable": writable,
                    "can_create": writable
                }
            else:
                return {
                    "path": path,
                    "exists": False,
                    "error": "Parent directory does not exist"
                }
    except Exception as e:
        return {"error": f"Error checking permissions: {str(e)}"}


def find_config_files(directory, config_patterns=None):
    """
    Find configuration files in a directory.
    Looks for common config file patterns.
    """
    if config_patterns is None:
        config_patterns = [
            '.conf', '.config', '.cfg', '.ini', '.yaml', '.yml', 
            '.json', '.toml', '.env', 'rc', 'config'
        ]
    
    try:
        if not os.path.exists(directory):
            return {"error": f"Directory does not exist: {directory}"}
        
        if not os.path.isdir(directory):
            return {"error": f"Path is not a directory: {directory}"}
        
        config_files = []
        
        for root, dirs, files in os.walk(directory):
            # Limit depth
            if root.count(os.sep) - directory.count(os.sep) > 2:
                continue
            
            for file in files:
                file_lower = file.lower()
                if any(pattern in file_lower for pattern in config_patterns):
                    full_path = os.path.join(root, file)
                    config_files.append(full_path)
        
        return {
            "directory": directory,
            "config_files": config_files[:50],  # Limit results
            "count": len(config_files)
        }
        
    except Exception as e:
        return {"error": f"Error finding config files: {str(e)}"}
