#!/usr/bin/env python3
"""MathRender — cross-platform installer for Claude Code hooks."""

import json
import platform
import sys
from pathlib import Path

DIR = Path(__file__).parent.resolve()
HOOK_DIR = Path.home() / ".mathrender"
HOOK_FILE = HOOK_DIR / "hook_send_formulas.py"


def get_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def _set_permissions() -> None:
    """Restrict ~/.mathrender/ to owner-only on Unix."""
    if platform.system() != "Windows":
        try:
            HOOK_DIR.chmod(0o700)
            if HOOK_FILE.exists():
                HOOK_FILE.chmod(0o600)
        except OSError:
            pass


def copy_hook() -> None:
    """Copy hook script to ~/.mathrender/ so it survives repo moves."""
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    _set_permissions()
    src = DIR / "hook_send_formulas.py"
    if not src.exists():
        print(f"Error: {src} not found")
        sys.exit(1)
    if not HOOK_FILE.exists() or src.read_bytes() != HOOK_FILE.read_bytes():
        HOOK_FILE.write_bytes(src.read_bytes())
        _set_permissions()
        print(f"[OK] Hook copied to {HOOK_FILE}")
    else:
        print(f"[OK] Hook already up to date in {HOOK_FILE}")


def get_hook_command() -> str:
    hook_path = str(HOOK_FILE).replace("\\", "/")
    if platform.system() == "Windows":
        return f'python "{hook_path}"'
    else:
        return f'python3 "{hook_path}"'


def install():
    print("MathRender — installation")
    print(f"Directory: {DIR}")
    print(f"Platform: {platform.system()}")
    print()

    # Check Python
    print(f"[OK] Python {sys.version.split()[0]}")

    # Copy hook to stable location
    copy_hook()

    # Check settings
    settings_path = get_settings_path()
    if not settings_path.exists():
        print(f"Error: {settings_path} not found. Is Claude Code installed?")
        sys.exit(1)
    print("[OK] Claude Code settings found")

    # Read settings
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {settings_path} contains invalid JSON. Fix it manually or delete and restart Claude Code.")
        sys.exit(1)

    hook_cmd = get_hook_command()

    hook_entry = {
        "hooks": [{
            "type": "command",
            "command": hook_cmd,
            "timeout": 5,
            "async": True,
        }]
    }

    if "hooks" not in settings:
        settings["hooks"] = {}

    # Stop hook
    if "Stop" not in settings["hooks"]:
        settings["hooks"]["Stop"] = []

    # Find existing hook and update path if needed
    found = False
    updated = False
    for entry in settings["hooks"]["Stop"]:
        for h in entry.get("hooks", []):
            if "hook_send_formulas" in h.get("command", ""):
                found = True
                if h["command"] != hook_cmd:
                    h["command"] = hook_cmd
                    updated = True

    if not found:
        settings["hooks"]["Stop"].append(hook_entry)
        print("[OK] Stop hook added to settings.json")
    elif updated:
        print("[OK] Stop hook path updated")
    else:
        print("[OK] Stop hook already installed")

    # Write settings
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print()
    print("Installation complete!")
    print()
    print("Next steps:")
    print("  1. Build the VS Code extension:")
    print(f"     cd \"{DIR / 'extension'}\"")
    print("     npm install && npm run compile")
    print()
    print("  2. Package and install:")
    print("     npx @vscode/vsce package")
    print("     code --install-extension mathrender-*.vsix")
    print()
    print("  3. In VS Code: Ctrl+Shift+P -> 'MathRender: Show Panel'")


if __name__ == "__main__":
    install()
