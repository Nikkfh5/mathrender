#!/usr/bin/env python3
"""MathRender — cross-platform installer for agent hooks."""

import json
import platform
import sys
from pathlib import Path

DIR = Path(__file__).parent.resolve()
HOOK_DIR = Path.home() / ".mathrender"
HOOK_FILE = HOOK_DIR / "hook_send_formulas.py"
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
CODEX_HOOKS = Path.home() / ".codex" / "hooks.json"


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


def read_json_object(path: Path) -> dict:
    """Read a JSON object from path, or return an empty object if missing."""
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {path} contains invalid JSON. Fix it manually or delete it.")
        sys.exit(1)

    if not isinstance(settings, dict):
        print(f"Error: {path} must contain a JSON object.")
        sys.exit(1)
    return settings


def write_json_object(path: Path, settings: dict) -> None:
    """Write JSON atomically enough for local settings files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(path)


def ensure_stop_hook(settings: dict, hook: dict) -> str:
    """Install or update a MathRender Stop hook in a settings object."""
    if not isinstance(settings.get("hooks"), dict):
        settings["hooks"] = {}
    if not isinstance(settings["hooks"].get("Stop"), list):
        settings["hooks"]["Stop"] = []

    found = False
    updated = False
    for entry in settings["hooks"]["Stop"]:
        entry_hooks = entry.get("hooks", []) if isinstance(entry, dict) else []
        if not isinstance(entry_hooks, list):
            continue
        for h in entry_hooks:
            if not isinstance(h, dict):
                continue
            command = h.get("command")
            if isinstance(command, str) and "hook_send_formulas" in command:
                found = True
                for key, value in hook.items():
                    if h.get(key) != value:
                        h[key] = value
                        updated = True

    if not found:
        settings["hooks"]["Stop"].append({"hooks": [hook]})
        return "added"
    if updated:
        return "updated"
    return "already installed"


def install_hook_config(name: str, path: Path, hook: dict) -> None:
    settings = read_json_object(path)
    status = ensure_stop_hook(settings, hook)
    write_json_object(path, settings)
    print(f"[OK] {name} hook {status} in {path}")


def install():
    print("MathRender — installation")
    print(f"Directory: {DIR}")
    print(f"Platform: {platform.system()}")
    print()

    # Check Python
    print(f"[OK] Python {sys.version.split()[0]}")

    # Copy hook to stable location
    copy_hook()

    hook_cmd = get_hook_command()

    install_hook_config(
        "Claude Code",
        CLAUDE_SETTINGS,
        {
            "type": "command",
            "command": hook_cmd,
            "timeout": 5,
            "async": True,
        },
    )
    install_hook_config(
        "Codex",
        CODEX_HOOKS,
        {
            "type": "command",
            "command": hook_cmd,
            "timeout": 5,
            "statusMessage": "Sending LaTeX to MathRender",
        },
    )

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
