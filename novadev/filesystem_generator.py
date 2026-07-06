from __future__ import annotations

"""Reusable filesystem generator helpers for NovaDev 1.1."""

from pathlib import Path
from typing import Iterable, List

from .ast_nodes import FileNode, FolderNode, SourceFileNode


class FilesystemGenerator:
    def generate(self, entries: Iterable[object], root: Path | str) -> List[Path]:
        root_path = Path(root)
        root_path.mkdir(parents=True, exist_ok=True)
        written: List[Path] = []
        for entry in entries:
            if isinstance(entry, FolderNode):
                folder = self.safe_join(root_path, entry.name)
                folder.mkdir(parents=True, exist_ok=True)
                written.extend(self.generate(entry.entries, folder))
            elif isinstance(entry, FileNode):
                target = self.safe_join(root_path, entry.generate or entry.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(entry.content, encoding="utf-8")
                written.append(target)
            elif isinstance(entry, SourceFileNode):
                target = self.safe_join(root_path, entry.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(entry.content, encoding="utf-8")
                written.append(target)
        return written

    def safe_join(self, root: Path, relative: str) -> Path:
        root_resolved = root.resolve()
        target = (root / relative).resolve()
        if root_resolved != target and root_resolved not in target.parents:
            raise ValueError(f"Refusing to write outside root: {relative}")
        return target
