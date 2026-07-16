from __future__ import annotations

"""Shared user-facing paths for NovaDev projects and generated source files."""

import os
from pathlib import Path


DOWNLOADS_FOLDER_ID = "{374DE290-123F-4565-9164-39C4925E467B}"


def downloads_directory() -> Path:
    """Return the current user's Downloads folder without requiring packages."""
    override = os.environ.get("NOVA_DOWNLOADS_HOME")
    if override:
        return Path(override).expanduser().resolve()

    if os.name == "nt":
        try:
            import winreg

            key_name = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name) as key:
                value, _ = winreg.QueryValueEx(key, DOWNLOADS_FOLDER_ID)
            return Path(os.path.expandvars(value)).expanduser().resolve()
        except (FileNotFoundError, OSError):
            pass

    return (Path.home() / "Downloads").resolve()


def source_workspace(create: bool = True) -> Path:
    """Return the folder where NovaDev creates user projects by default."""
    override = os.environ.get("NOVA_SOURCE_HOME")
    workspace = Path(override).expanduser().resolve() if override else downloads_directory() / "Nova source code"
    if create:
        workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def resolve_new_project(value: str | Path) -> Path:
    """Resolve a project name inside the source workspace.

    Relative names and nested paths are placed under ``Nova source code``.
    Absolute paths are accepted only when they already point inside that
    workspace, keeping command-created projects in one predictable location.
    """
    candidate = Path(value).expanduser()
    workspace = source_workspace()
    target = candidate.resolve() if candidate.is_absolute() else (workspace / candidate).resolve()
    if target == workspace or workspace not in target.parents:
        raise ValueError("Project path must stay inside the Nova source code folder")
    return target


def is_source_path(value: str | Path) -> bool:
    """Return True when a path can be safely managed as user Nova source."""
    workspace = source_workspace().resolve()
    candidate = Path(value).expanduser().resolve()
    return candidate != workspace and workspace in candidate.parents
