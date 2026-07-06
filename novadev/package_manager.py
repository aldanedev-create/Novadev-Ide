from __future__ import annotations

"""Local package manager for NovaDev.

`NovaPackageManager` installs the NovaDev language and local NovaDev packages
without external Python dependencies. It is intentionally simple: package
metadata is JSON, package contents are copied into a local NovaDev home folder,
and launcher scripts are written into `~/.novadev/bin`.
"""

import json
import os
import shutil
import sys
import tempfile
from urllib.parse import urljoin
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_REGISTRY = {
    "name": "novadev-local-registry",
    "version": "1.0.0",
    "packages": [
        {
            "name": "hello-ui",
            "version": "0.1.0",
            "description": "Example NovaDev UI package.",
            "source": "packages/hello-ui",
            "kind": "module",
        },
        {
            "name": "auth-kit",
            "version": "0.1.0",
            "description": "Starter auth declarations for NovaDev apps.",
            "source": "packages/auth-kit",
            "kind": "module",
        },
        {
            "name": "dashboard-kit",
            "version": "0.1.0",
            "description": "Reusable dashboard page declarations and UI helpers.",
            "source": "packages/dashboard-kit",
            "kind": "module",
        }
    ]
}


@dataclass
class PackageRecord:
    name: str
    version: str
    description: str
    path: str
    kind: str = "module"

    def to_data(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "path": self.path,
            "kind": self.kind,
        }


class PackageManagerError(Exception):
    """Raised when `novapm` cannot complete an operation."""


class NovaPackageManager:
    def __init__(self, home: Path | str | None = None, project_root: Path | str | None = None):
        self.home = Path(home or os.environ.get("NOVADEV_HOME") or Path.home() / ".novadev").expanduser().resolve()
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.bin_dir = self.home / "bin"
        self.language_dir = self.home / "language"
        self.packages_dir = self.home / "packages"
        self.cache_dir = self.home / "cache"
        self.registry_file = self.home / "registry.json"
        self.installed_file = self.home / "installed.json"
        self.config_file = self.home / "config.json"

    def ensure_home(self) -> None:
        for folder in [self.home, self.bin_dir, self.language_dir, self.packages_dir, self.cache_dir]:
            folder.mkdir(parents=True, exist_ok=True)
        if not self.registry_file.exists():
            self.write_json(self.registry_file, DEFAULT_REGISTRY)
        if not self.installed_file.exists():
            self.write_json(self.installed_file, {"packages": {}})
        if not self.config_file.exists():
            self.write_json(self.config_file, {"registry": str(self.registry_file)})

    def init_registry(self) -> Path:
        self.ensure_home()
        self.write_json(self.registry_file, DEFAULT_REGISTRY)
        return self.registry_file

    def configure_registry(self, registry: str) -> Path:
        self.ensure_home()
        config = self.read_json(self.config_file, {"registry": str(self.registry_file)})
        config["registry"] = registry
        self.write_json(self.config_file, config)
        return self.config_file

    def install_language(self, source: Path | str) -> List[Path]:
        self.ensure_home()
        source_path = Path(source).expanduser().resolve()
        if not source_path.exists():
            raise PackageManagerError(f"language source not found: {source_path}")
        if source_path.is_file() and source_path.suffix.lower() == ".zip":
            with tempfile.TemporaryDirectory() as tmp:
                with zipfile.ZipFile(source_path) as archive:
                    archive.extractall(tmp)
                roots = [item for item in Path(tmp).iterdir() if item.is_dir()]
                language_source = roots[0] if len(roots) == 1 else Path(tmp)
                return self.install_language(language_source)

        self.replace_dir(self.language_dir, source_path, exclude=language_excludes())
        written = self.write_launchers()
        self.write_json(
            self.home / "language-install.json",
            {
                "source": str(source_path),
                "language": str(self.language_dir),
                "bin": str(self.bin_dir),
                "python": sys.executable,
            },
        )
        return written

    def doctor(self) -> Dict[str, Any]:
        self.ensure_home()
        language_ok = (self.language_dir / "nova.py").exists()
        return {
            "home": str(self.home),
            "python": sys.executable,
            "languageInstalled": language_ok,
            "languageDir": str(self.language_dir),
            "binDir": str(self.bin_dir),
            "packages": len(self.installed_packages()),
            "pathHint": str(self.bin_dir),
        }

    def search(self, query: str = "") -> List[Dict[str, Any]]:
        self.ensure_home()
        registry = self.load_registry()
        query_lower = query.lower()
        results = []
        for package in registry.get("packages", []):
            haystack = " ".join(str(package.get(key, "")) for key in ["name", "description", "kind"]).lower()
            if not query_lower or query_lower in haystack:
                results.append(package)
        return results

    def info(self, package: str) -> Dict[str, Any]:
        installed = self.installed_packages().get(package)
        if installed:
            return {"installed": True, **installed}
        for item in self.search(package):
            if item.get("name") == package:
                return {"installed": False, **item}
        raise PackageManagerError(f"package not found: {package}")

    def list_installed(self) -> List[Dict[str, Any]]:
        return list(self.installed_packages().values())

    def install_package(self, package: str) -> PackageRecord:
        self.ensure_home()
        source = self.resolve_package_source(package)
        with self.local_source(source) as source_path:
            manifest = self.load_package_manifest(source_path)
            name = manifest["name"]
            version = manifest.get("version", "0.1.0")
            target = self.packages_dir / f"{safe_name(name)}@{safe_name(version)}"
            self.replace_dir(target, source_path, exclude={"__pycache__", ".git", "node_modules"})
            record = PackageRecord(
                name=name,
                version=version,
                description=manifest.get("description", ""),
                path=str(target),
                kind=manifest.get("kind", "module"),
            )
            installed = self.read_json(self.installed_file, {"packages": {}})
            installed.setdefault("packages", {})[name] = record.to_data()
            self.write_json(self.installed_file, installed)
            return record

    def remove_package(self, name: str) -> None:
        self.ensure_home()
        installed = self.read_json(self.installed_file, {"packages": {}})
        record = installed.get("packages", {}).pop(name, None)
        if not record:
            raise PackageManagerError(f"package is not installed: {name}")
        target = Path(record["path"]).resolve()
        self.ensure_inside_home(target)
        if target.exists():
            shutil.rmtree(target)
        self.write_json(self.installed_file, installed)

    def pack(self, package_dir: Path | str, output: Path | str | None = None) -> Path:
        source = Path(package_dir).expanduser().resolve()
        manifest = self.load_package_manifest(source)
        target = Path(output or f"{manifest['name']}-{manifest.get('version', '0.1.0')}.zip").resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in source.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    archive.write(path, path.relative_to(source))
        return target

    def load_registry(self) -> Dict[str, Any]:
        config = self.read_json(self.config_file, {"registry": str(self.registry_file)})
        registry = config.get("registry") or str(self.registry_file)
        if registry.startswith(("http://", "https://")):
            with urllib.request.urlopen(registry, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
                data.setdefault("_registry_base_url", registry.rsplit("/", 1)[0] + "/")
                return data
        registry_path = Path(registry).expanduser()
        if not registry_path.is_absolute():
            registry_path = self.project_root / registry_path
        data = self.read_json(registry_path, DEFAULT_REGISTRY)
        data.setdefault("_registry_base_path", str(registry_path.resolve().parent))
        return data

    def resolve_package_source(self, package: str) -> str:
        path = Path(package).expanduser()
        if path.exists() or package.startswith(("http://", "https://")):
            return package
        registry = self.load_registry()
        for item in registry.get("packages", []):
            if item.get("name") == package:
                source = str(item.get("source", package))
                if source.startswith(("http://", "https://")):
                    return source
                base_url = registry.get("baseUrl") or registry.get("_registry_base_url")
                if isinstance(base_url, str) and base_url.startswith(("http://", "https://")):
                    return urljoin(base_url, source)
                base_path = registry.get("_registry_base_path")
                if isinstance(base_path, str):
                    return str((Path(base_path) / source).resolve())
                return source
        raise PackageManagerError(f"package not found in registry or filesystem: {package}")

    def local_source(self, source: str):
        manager = self

        class LocalSource:
            def __init__(self) -> None:
                self.tmp: tempfile.TemporaryDirectory[str] | None = None
                self.path: Path | None = None

            def __enter__(self) -> Path:
                if source.startswith(("http://", "https://")):
                    self.tmp = tempfile.TemporaryDirectory()
                    download_target = Path(self.tmp.name) / "package.zip"
                    urllib.request.urlretrieve(source, download_target)
                    if zipfile.is_zipfile(download_target):
                        with zipfile.ZipFile(download_target) as archive:
                            archive.extractall(self.tmp.name)
                        candidates = [item for item in Path(self.tmp.name).iterdir() if item.is_dir()]
                        self.path = candidates[0] if len(candidates) == 1 else Path(self.tmp.name)
                    else:
                        raise PackageManagerError("remote packages must be zip files")
                    return self.path

                path = Path(source).expanduser()
                if not path.is_absolute():
                    path = manager.project_root / path
                path = path.resolve()
                if path.is_file() and path.suffix.lower() == ".zip":
                    self.tmp = tempfile.TemporaryDirectory()
                    with zipfile.ZipFile(path) as archive:
                        archive.extractall(self.tmp.name)
                    candidates = [item for item in Path(self.tmp.name).iterdir() if item.is_dir()]
                    self.path = candidates[0] if len(candidates) == 1 else Path(self.tmp.name)
                    return self.path
                if not path.is_dir():
                    raise PackageManagerError(f"package source is not a folder or zip: {path}")
                self.path = path
                return path

            def __exit__(self, exc_type, exc, tb) -> None:
                if self.tmp:
                    self.tmp.cleanup()

        return LocalSource()

    def load_package_manifest(self, package_dir: Path) -> Dict[str, Any]:
        manifest_path = package_dir / "nova-package.json"
        if not manifest_path.exists():
            raise PackageManagerError(f"missing package manifest: {manifest_path}")
        manifest = self.read_json(manifest_path, {})
        if not manifest.get("name"):
            raise PackageManagerError("package manifest needs a name")
        return manifest

    def installed_packages(self) -> Dict[str, Dict[str, Any]]:
        self.ensure_home()
        return self.read_json(self.installed_file, {"packages": {}}).get("packages", {})

    def write_launchers(self) -> List[Path]:
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        python = sys.executable
        nova_py = self.language_dir / "nova.py"
        shell_py = self.language_dir / "shell.py"
        novapm_py = self.language_dir / "novapm.py"
        manager_py = self.language_dir / "novadev_manager.py"
        launchers = {
            "nova.cmd": f'@echo off\r\nset "NOVADEV_HOME={self.home}"\r\n"{python}" "{nova_py}" %*\r\n',
            "nova-shell.cmd": f'@echo off\r\nset "NOVADEV_HOME={self.home}"\r\n"{python}" "{shell_py}" %*\r\n',
            "novapm.cmd": f'@echo off\r\nset "NOVADEV_HOME={self.home}"\r\n"{python}" "{novapm_py}" %*\r\n',
            "novadev-manager.cmd": f'@echo off\r\nset "NOVADEV_HOME={self.home}"\r\n"{python}" "{manager_py}" %*\r\n',
            "nova": f'#!/usr/bin/env sh\nexport NOVADEV_HOME="{self.home}"\nexec "{python}" "{nova_py}" "$@"\n',
            "nova-shell": f'#!/usr/bin/env sh\nexport NOVADEV_HOME="{self.home}"\nexec "{python}" "{shell_py}" "$@"\n',
            "novapm": f'#!/usr/bin/env sh\nexport NOVADEV_HOME="{self.home}"\nexec "{python}" "{novapm_py}" "$@"\n',
            "novadev-manager": f'#!/usr/bin/env sh\nexport NOVADEV_HOME="{self.home}"\nexec "{python}" "{manager_py}" "$@"\n',
        }
        written = []
        for name, content in launchers.items():
            target = self.bin_dir / name
            target.write_text(content, encoding="utf-8")
            if not name.endswith(".cmd"):
                target.chmod(0o755)
            written.append(target)
        return written

    def replace_dir(self, target: Path, source: Path, exclude: Iterable[str] | None = None) -> None:
        self.ensure_inside_home(target)
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        exclude_set = set(exclude or set())
        target_resolved = target.resolve()
        for item in source.iterdir():
            if item.name in exclude_set or item.name.startswith(".tmp-"):
                continue
            item_resolved = item.resolve()
            if item_resolved == target_resolved or item_resolved in target_resolved.parents:
                continue
            destination = target / item.name
            if item.is_dir():
                shutil.copytree(item, destination, ignore=shutil.ignore_patterns(*exclude_set))
            else:
                shutil.copy2(item, destination)

    def ensure_inside_home(self, path: Path) -> None:
        resolved = path.resolve()
        if self.home != resolved and self.home not in resolved.parents:
            raise PackageManagerError(f"refusing to write outside NovaDev home: {resolved}")

    def read_json(self, path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value).strip("-") or "package"


def language_excludes() -> set[str]:
    return {
        ".git",
        ".novadev",
        ".tmp-novapm-home",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "generated",
        "dist",
        "dist_ecommerce",
        "generated_backend",
        "generated_backend_django",
        "generated_backend_ecommerce",
        "generated_backend_express",
        "generated_backend_fastapi",
        "generated_docs_webshield",
        "generated_notes",
    }
