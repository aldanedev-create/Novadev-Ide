from __future__ import annotations

"""Beginner-friendly NovaDev error types."""


class NovaError(Exception):
    """Base error for NovaDev failures."""


class NovaSyntaxError(NovaError):
    """Raised for parser errors."""


class NovaRuntimeError(NovaError):
    """Raised for runtime errors."""


class NovaNameError(NovaRuntimeError):
    """Raised when a variable or property is missing."""

