#!/usr/bin/env python3
import os
import sys
import platform
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"

WINDOWS_DEFAULT_BIN = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "bin"
UNIX_DEFAULT_BIN = Path.home() / ".local" / "bin"

CMD_NAME = "can-you"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path

def is_on_path(path: Path) -> bool:
    path_str = str(path)
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if Path(entry).resolve() == Path(path_str).resolve():
            return True
    return False

def add_to_path_windows(path: Path):
    # Adds path to user PATH via setx (affects future shells)
    current = os.environ.get("PATH", "")
    path_str = str(path)
    if path_str in current:
        return False
    os.system(f'setx PATH "{current}{os.pathsep}{path_str}"')
    return True

def install_windows(target_dir: Path):
    ensure_dir(target_dir)
    cmd_path = target_dir / f"{CMD_NAME}.cmd"
    ps1_path = target_dir / f"{CMD_NAME}.ps1"

    main_path = str(MAIN_PY)
    py_exe = sys.executable

    # .cmd wrapper (works in cmd and PowerShell)
    cmd_content = f"""@echo off
setlocal
set "PY_EXE={py_exe}"
set "MAIN_PATH={main_path}"
"%PY_EXE%" "%MAIN_PATH%" %*
"""
    cmd_path.write_text(cmd_content, encoding="utf-8")

    # PowerShell wrapper (direct)
    ps1_content = f"""
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
$py = "{py_exe}"
$main = "{main_path}"
& $py $main @Args
"""
    ps1_path.write_text(ps1_content, encoding="utf-8")

    added = False
    if not is_on_path(target_dir):
        try:
            added = add_to_path_windows(target_dir)
        except Exception:
            added = False

    return {
        "bin_dir": str(target_dir),
        "wrappers": [str(cmd_path), str(ps1_path)],
        "path_updated": added,
    }

def install_unix(target_dir: Path):
    ensure_dir(target_dir)
    wrapper_path = target_dir / CMD_NAME
    main_path = str(MAIN_PY)

    # Bash/Zsh/Fish-friendly wrapper that calls the project main.py
    wrapper_content = f"""#!/usr/bin/env bash
python3 "{main_path}" "$@"
"""
    wrapper_path.write_text(wrapper_content, encoding="utf-8")
    os.chmod(wrapper_path, 0o755)

    return {
        "bin_dir": str(target_dir),
        "wrappers": [str(wrapper_path)],
        "path_updated": False,
        "path_hint": str(target_dir),
    }

def main():
    if not MAIN_PY.exists():
        print(f"Error: main.py not found at {MAIN_PY}")
        sys.exit(1)

    system = platform.system()
    print(f"Installing '{CMD_NAME}' for {system}...")

    if system == "Windows":
        target_dir = WINDOWS_DEFAULT_BIN
        result = install_windows(target_dir)
        print(f"\nInstalled wrappers:")
        for w in result["wrappers"]:
            print(f" - {w}")
        print(f"\nAdd to PATH: {'updated' if result['path_updated'] else 'already present or failed'}")
        print(f"Bin directory: {result['bin_dir']}")
        print("\nNotes:")
        print(" - You may need to open a NEW terminal for PATH changes to take effect.")
        print(f" - After that, run: {CMD_NAME} -l find all python files in the current directory")
    else:
        target_dir = UNIX_DEFAULT_BIN
        result = install_unix(target_dir)
        print(f"\nInstalled wrapper:")
        for w in result["wrappers"]:
            print(f" - {w}")
        print(f"\nEnsure {result['path_hint']} is on your PATH. If not:")
        print(f"   echo 'export PATH=\"{result['path_hint']}:$PATH\"' >> ~/.bashrc && source ~/.bashrc")
        print(f"\nNow you can run: {CMD_NAME} -l find all python files in the current directory")

if __name__ == "__main__":
    main()
