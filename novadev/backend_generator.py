from __future__ import annotations

"""Backend project generator for NovaDev 1.1.

The heavy lifting lives in `codegen.py`. This module gives NovaDev a clear
filename for backend generation while preserving the existing `BackendGenerator`
API used by the CLI and tests.
"""

from .codegen import BackendGenerator


__all__ = ["BackendGenerator"]
