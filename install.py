#!/usr/bin/env python3
"""MathRender — cross-platform installer for Claude Code hooks."""

import json
import platform
import sys
from pathlib import Path

DIR = Path(__file__).parent.resolve()


def get_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def get_hook_command() -> str:
    hook_script = DIR / "hook_send_formulas.py"
    hook_path = str(hook_script).replace("\\", "/")
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

    existing = [
        h for entry in settings["hooks"]["Stop"]
        for h in entry.get("hooks", [])
        if "hook_send_formulas" in h.get("command", "")
    ]
    if not existing:
        settings["hooks"]["Stop"].append(hook_entry)
        print("[OK] Stop hook added to settings.json")
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
    print("     code --install-extension mathrender-0.1.0.vsix")
    print()
    print("  3. In VS Code: Ctrl+Shift+P -> 'MathRender: Show Panel'")


if __name__ == "__main__":
    install()
