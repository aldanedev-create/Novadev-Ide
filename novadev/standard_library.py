from __future__ import annotations

"""NovaDev standard library foundation.

The interpreter can expose these helpers as `Nova.files`, `Nova.json`,
`Nova.sqlite`, and similar modules. They are small wrappers around Python's
standard library so Nova code can grow into a general-purpose language without
requiring custom Python blocks for everyday work.
"""

import csv
import datetime as _datetime
import hashlib
import hmac
import json
import math
import os
import random
import re
import secrets
import shutil
import smtplib
import sqlite3
import statistics
import time
import urllib.error
import urllib.request
import uuid
from types import SimpleNamespace
from pathlib import Path
from email.message import EmailMessage
from typing import Any


class NovaFiles:
    def read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write(self, path: str, content: Any) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(content), encoding="utf-8")
        return str(target)

    def append(self, path: str, content: Any) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(str(content))
        return str(target)

    def delete(self, path: str) -> bool:
        target = Path(path)
        if target.exists():
            target.unlink()
            return True
        return False

    def copy(self, source: str, target: str) -> str:
        destination = Path(target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return str(destination)

    def move(self, source: str, target: str) -> str:
        destination = Path(target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)
        return str(destination)

    def mkdir(self, path: str) -> str:
        target = Path(path)
        target.mkdir(parents=True, exist_ok=True)
        return str(target)

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def list(self, path: str = ".") -> list[str]:
        return [item.name for item in Path(path).iterdir()]


class NovaJson:
    def parse(self, text: str) -> Any:
        return json.loads(text)

    def stringify(self, value: Any, indent: int = 2) -> str:
        return json.dumps(value, indent=indent)

    def pretty(self, value: Any) -> str:
        return json.dumps(value, indent=2, default=str)

    def read(self, path: str) -> Any:
        return self.parse(Path(path).read_text(encoding="utf-8"))

    def write(self, path: str, value: Any) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.stringify(value), encoding="utf-8")
        return str(target)


class NovaCsv:
    def read(self, path: str) -> list[dict[str, str]]:
        with Path(path).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def write(self, path: str, rows: list[dict[str, Any]]) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = sorted({key for row in rows for key in row})
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return str(target)

    def append(self, path: str, row: dict[str, Any]) -> str:
        target = Path(path)
        exists = target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if not exists:
                writer.writeheader()
            writer.writerow(row)
        return str(target)


class NovaHttp:
    def get(self, url: str, timeout: int = 10) -> dict[str, Any]:
        return self.request("GET", url, timeout=timeout)

    def post(self, url: str, body: Any = None, timeout: int = 10) -> dict[str, Any]:
        payload = json.dumps(body or {}).encode("utf-8")
        return self.request("POST", url, body=payload, timeout=timeout, headers={"Content-Type": "application/json"})

    def put(self, url: str, body: Any = None, timeout: int = 10) -> dict[str, Any]:
        payload = json.dumps(body or {}).encode("utf-8")
        return self.request("PUT", url, body=payload, timeout=timeout, headers={"Content-Type": "application/json"})

    def delete(self, url: str, timeout: int = 10) -> dict[str, Any]:
        return self.request("DELETE", url, timeout=timeout)

    def download(self, url: str, path: str, timeout: int = 20) -> str:
        response = self.get(url, timeout=timeout)
        if not response["ok"]:
            raise RuntimeError(response["body"])
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(response["body"], encoding="utf-8")
        return str(target)

    def request(self, method: str, url: str, body: bytes | None = None, timeout: int = 10, headers: dict[str, str] | None = None) -> dict[str, Any]:
        request = urllib.request.Request(url, method=method.upper(), data=body, headers=headers or {})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8")
                return {"ok": True, "status": response.status, "body": text}
        except urllib.error.HTTPError as error:
            return {"ok": False, "status": error.code, "body": error.read().decode("utf-8", errors="replace")}
        except urllib.error.URLError as error:
            return {"ok": False, "status": 0, "body": str(error)}


class NovaSqlite:
    def connect(self, database: str):
        return sqlite3.connect(database)

    def query(self, database: str, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        with sqlite3.connect(database) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql, params or []).fetchall()
            return [dict(row) for row in rows]

    def execute(self, database: str, sql: str, params: list[Any] | None = None) -> int:
        with sqlite3.connect(database) as connection:
            cursor = connection.execute(sql, params or [])
            connection.commit()
            return cursor.rowcount

    def insert(self, database: str, table: str, row: dict[str, Any]) -> int:
        keys = list(row.keys())
        placeholders = ", ".join("?" for _ in keys)
        sql = f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({placeholders})"
        return self.execute(database, sql, [row[key] for key in keys])

    def table(self, database: str, table: str) -> list[dict[str, Any]]:
        return self.query(database, f"SELECT * FROM {table}")


class NovaMath:
    def round(self, value: float, digits: int = 0) -> float:
        return round(value, digits)

    def sqrt(self, value: float) -> float:
        return math.sqrt(value)

    def floor(self, value: float) -> int:
        return math.floor(value)

    def ceil(self, value: float) -> int:
        return math.ceil(value)

    def percent(self, value: float, total: float) -> float:
        return 0 if total == 0 else (value / total) * 100

    def avg(self, values: list[float]) -> float:
        return sum(values) / len(values) if values else 0

    def min(self, values: list[float]) -> float:
        return min(values) if values else 0

    def max(self, values: list[float]) -> float:
        return max(values) if values else 0

    def clamp(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))


class NovaStats:
    def mean(self, values: list[float]) -> float:
        return statistics.mean(values) if values else 0

    def median(self, values: list[float]) -> float:
        return statistics.median(values) if values else 0

    def mode(self, values: list[Any]) -> Any:
        return statistics.mode(values) if values else None

    def variance(self, values: list[float]) -> float:
        return statistics.variance(values) if len(values) > 1 else 0

    def stdev(self, values: list[float]) -> float:
        return statistics.stdev(values) if len(values) > 1 else 0

    def percentile(self, values: list[float], percent: float) -> float:
        if not values:
            return 0
        ordered = sorted(values)
        index = round((percent / 100) * (len(ordered) - 1))
        return ordered[index]


class NovaCrypto:
    def md5(self, value: Any) -> str:
        return hashlib.md5(str(value).encode("utf-8")).hexdigest()

    def sha256(self, value: Any) -> str:
        return hashlib.sha256(str(value).encode("utf-8")).hexdigest()

    def token(self, length: int = 32) -> str:
        return secrets.token_urlsafe(length)

    def hmac_sha256(self, key: str, value: Any) -> str:
        return hmac.new(str(key).encode("utf-8"), str(value).encode("utf-8"), hashlib.sha256).hexdigest()

    def passwordHash(self, value: Any) -> str:
        salt = self.token(12)
        digest = hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()
        return f"{salt}:{digest}"

    def verifyPassword(self, value: Any, hashed: str) -> bool:
        salt, _, digest = hashed.partition(":")
        return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest() == digest


class NovaEnv:
    def get(self, name: str, default: str = "") -> str:
        return os.environ.get(name, default)

    def require(self, name: str) -> str:
        value = os.environ.get(name)
        if value is None:
            raise RuntimeError(f"Missing environment variable: {name}")
        return value

    def bool(self, name: str, default: bool = False) -> bool:
        value = os.environ.get(name)
        if value is None:
            return default
        return value.lower() in {"1", "true", "yes", "on"}

    def int(self, name: str, default: int = 0) -> int:
        try:
            return int(os.environ.get(name, default))
        except ValueError:
            return default


class NovaTime:
    def now(self) -> float:
        return time.time()

    def today(self) -> str:
        return _datetime.date.today().isoformat()

    def format(self, timestamp: float | None = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        return _datetime.datetime.fromtimestamp(timestamp or time.time()).strftime(fmt)

    def parse(self, value: str, fmt: str = "%Y-%m-%d") -> float:
        return _datetime.datetime.strptime(value, fmt).timestamp()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class NovaEmail:
    def message(self, to: str, subject: str, body: str, sender: str = "") -> dict[str, str]:
        return {"to": to, "subject": subject, "body": body, "sender": sender}

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        sender: str = "",
        host: str = "",
        port: int = 587,
        username: str = "",
        password: str = "",
        use_tls: bool = True,
    ) -> dict[str, Any]:
        sender = sender or username
        if not sender:
            raise RuntimeError("Nova.email.send needs sender or username")
        host = host or os.environ.get("SMTP_HOST", "")
        username = username or os.environ.get("SMTP_USERNAME", "")
        password = password or os.environ.get("SMTP_PASSWORD", "")
        if not host:
            raise RuntimeError("Nova.email.send needs SMTP host")
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(host, port) as server:
            if use_tls:
                server.starttls()
            if username:
                server.login(username, password)
            server.send_message(msg)
        return {"ok": True, "to": to, "subject": subject}


class NovaDataFrame:
    def __init__(self, frame: Any):
        self.frame = frame

    def sum(self, column: str) -> float:
        return float(self.frame[column].sum())

    def avg(self, column: str) -> float:
        return float(self.frame[column].mean())

    def groupBy(self, column: str) -> "NovaGroupFrame":
        return NovaGroupFrame(self.frame.groupby(column))

    def filter(self, column: str, equals: Any) -> "NovaDataFrame":
        return NovaDataFrame(self.frame[self.frame[column] == equals])

    def toRows(self) -> list[dict[str, Any]]:
        return self.frame.to_dict(orient="records")

    def toCsv(self, path: str) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.frame.to_csv(target, index=False)
        return str(target)


class NovaGroupFrame:
    def __init__(self, group: Any):
        self.group = group

    def sum(self, column: str) -> dict[str, Any]:
        return self.group[column].sum().to_dict()

    def avg(self, column: str) -> dict[str, Any]:
        return self.group[column].mean().to_dict()

    def count(self) -> dict[str, Any]:
        return self.group.size().to_dict()


class NovaDataframes:
    def readCsv(self, path: str) -> NovaDataFrame:
        pd = require_optional("pandas", "Nova.dataframes needs pandas. Install it with: pip install pandas")
        return NovaDataFrame(pd.read_csv(path))

    def readExcel(self, path: str, sheet: str | int = 0) -> NovaDataFrame:
        pd = require_optional("pandas", "Nova.dataframes needs pandas and openpyxl. Install them with: pip install pandas openpyxl")
        return NovaDataFrame(pd.read_excel(path, sheet_name=sheet))

    def fromRows(self, rows: list[dict[str, Any]]) -> NovaDataFrame:
        pd = require_optional("pandas", "Nova.dataframes needs pandas. Install it with: pip install pandas")
        return NovaDataFrame(pd.DataFrame(rows))


class NovaArrays:
    def array(self, values: list[Any]) -> Any:
        np = require_optional("numpy", "Nova.arrays needs numpy. Install it with: pip install numpy")
        return np.array(values)

    def mean(self, values: list[float]) -> float:
        np = require_optional("numpy", "Nova.arrays needs numpy. Install it with: pip install numpy")
        return float(np.mean(values))

    def sum(self, values: list[float]) -> float:
        np = require_optional("numpy", "Nova.arrays needs numpy. Install it with: pip install numpy")
        return float(np.sum(values))

    def normalize(self, values: list[float]) -> list[float]:
        np = require_optional("numpy", "Nova.arrays needs numpy. Install it with: pip install numpy")
        arr = np.array(values, dtype=float)
        high = arr.max()
        low = arr.min()
        if high == low:
            return [0 for _ in values]
        return ((arr - low) / (high - low)).tolist()


class NovaTrading:
    def sma(self, values: list[float], window: int) -> list[float]:
        if window <= 0:
            return []
        return [sum(values[max(0, i - window + 1) : i + 1]) / len(values[max(0, i - window + 1) : i + 1]) for i in range(len(values))]

    def riskReward(self, entry: float, stop_loss: float, take_profit: float) -> float:
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        return 0 if risk == 0 else reward / risk

    def positionSize(self, account: float, risk_percent: float, entry: float, stop_loss: float) -> float:
        risk_amount = account * (risk_percent / 100)
        per_unit_risk = abs(entry - stop_loss)
        return 0 if per_unit_risk == 0 else risk_amount / per_unit_risk


class NovaSecurity:
    def checkHeaders(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=10) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
        required = ["content-security-policy", "x-frame-options", "x-content-type-options"]
        missing = [name for name in required if name not in headers]
        return {"url": url, "missing": missing, "score": max(0, 100 - len(missing) * 25)}

    def scoreTarget(self, checks: dict[str, Any]) -> int:
        missing = checks.get("missing", [])
        return max(0, 100 - len(missing) * 25)


class NovaRegex:
    def match(self, pattern: str, text: str) -> bool:
        return re.search(pattern, text) is not None

    def replace(self, pattern: str, replacement: str, text: str) -> str:
        return re.sub(pattern, replacement, text)

    def findall(self, pattern: str, text: str) -> list[str]:
        return re.findall(pattern, text)


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

    def listdir(self, path: str = ".") -> list[str]:
        return [item.name for item in Path(path).iterdir()]


def require_optional(module_name: str, message: str) -> Any:
    try:
        return __import__(module_name)
    except ImportError as exc:
        raise RuntimeError(message) from exc


def standard_library() -> dict[str, Any]:
    return {
        "Nova.files": NovaFiles(),
        "Nova.json": NovaJson(),
        "Nova.csv": NovaCsv(),
        "Nova.http": NovaHttp(),
        "Nova.sqlite": NovaSqlite(),
        "Nova.math": NovaMath(),
        "Nova.stats": NovaStats(),
        "Nova.crypto": NovaCrypto(),
        "Nova.env": NovaEnv(),
        "Nova.time": NovaTime(),
        "Nova.email": NovaEmail(),
        "Nova.dataframes": NovaDataframes(),
        "Nova.arrays": NovaArrays(),
        "Nova.trading": NovaTrading(),
        "Nova.security": NovaSecurity(),
        "Nova.regex": NovaRegex(),
        "Nova.path": NovaPath(),
        "Nova.os.safe": NovaSafeOS(),
    }


def nova_root() -> SimpleNamespace:
    """Create the single `Nova` object used by the interpreter."""
    library = standard_library()
    return SimpleNamespace(
        files=library["Nova.files"],
        json=library["Nova.json"],
        csv=library["Nova.csv"],
        http=library["Nova.http"],
        sqlite=library["Nova.sqlite"],
        math=library["Nova.math"],
        stats=library["Nova.stats"],
        crypto=library["Nova.crypto"],
        env=library["Nova.env"],
        time=library["Nova.time"],
        email=library["Nova.email"],
        dataframes=library["Nova.dataframes"],
        arrays=library["Nova.arrays"],
        trading=library["Nova.trading"],
        security=library["Nova.security"],
        regex=library["Nova.regex"],
        path=library["Nova.path"],
        os=SimpleNamespace(safe=library["Nova.os.safe"]),
        random=random,
        datetime=_datetime,
        statistics=statistics,
        uuid=uuid,
    )


NovaSQLite = NovaSqlite
