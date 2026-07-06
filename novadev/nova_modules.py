from __future__ import annotations

"""Safe Python standard-library bridge exposed as `Nova.*` in NovaDev 0.4."""

import csv
import datetime as _datetime
import hashlib
import hmac
import json
import math
import random
import re
import secrets
import sqlite3
import statistics
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlopen


class NovaFiles:
    def read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write(self, path: str, text: str) -> bool:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True) if target.parent != Path(".") else None
        target.write_text(str(text), encoding="utf-8")
        return True

    def append(self, path: str, text: str) -> bool:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True) if target.parent != Path(".") else None
        with target.open("a", encoding="utf-8") as handle:
            handle.write(str(text))
        return True


class NovaJson:
    def parse(self, text: str):
        return json.loads(text)

    def stringify(self, value) -> str:
        return json.dumps(value, default=str)

    def pretty(self, value) -> str:
        return json.dumps(value, indent=2, default=str)


class NovaRegex:
    def match(self, pattern: str, text: str) -> bool:
        return re.search(pattern, text) is not None

    def replace(self, pattern: str, replacement: str, text: str) -> str:
        return re.sub(pattern, replacement, text)

    def findall(self, pattern: str, text: str):
        return re.findall(pattern, text)


class NovaCrypto:
    def sha256(self, text: str) -> str:
        return hashlib.sha256(str(text).encode("utf-8")).hexdigest()

    def token(self, length: int = 16) -> str:
        return secrets.token_hex(int(length))

    def hmac_sha256(self, key: str, text: str) -> str:
        return hmac.new(str(key).encode(), str(text).encode(), hashlib.sha256).hexdigest()


class NovaHttp:
    def get(self, url: str) -> str:
        with urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8")


class NovaPath:
    def join(self, *parts: str) -> str:
        return str(Path(*map(str, parts)))

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def name(self, path: str) -> str:
        return Path(path).name


class NovaSafeOS:
    def cwd(self) -> str:
        return str(Path.cwd())

    def listdir(self, path: str = "."):
        return [item.name for item in Path(path).iterdir()]


class NovaCsv:
    def read(self, path: str):
        with Path(path).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))


class NovaSQLite:
    def connect(self, path: str):
        return sqlite3.connect(path)


class NovaEmail:
    def message(self, subject: str, body: str):
        return {"subject": subject, "body": body}


def nova_root():
    """Create the object available as `Nova` inside NovaDev programs."""
    return SimpleNamespace(
        math=math,
        random=random,
        datetime=_datetime,
        json=NovaJson(),
        files=NovaFiles(),
        csv=NovaCsv(),
        sqlite=NovaSQLite(),
        regex=NovaRegex(),
        uuid=uuid,
        crypto=NovaCrypto(),
        http=NovaHttp(),
        email=NovaEmail(),
        os=SimpleNamespace(safe=NovaSafeOS()),
        path=NovaPath(),
        time=time,
        statistics=statistics,
    )
