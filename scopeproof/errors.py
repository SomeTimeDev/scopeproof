from __future__ import annotations


class ScopeProofError(Exception):
    """Base exception for clean CLI errors."""

    def __init__(
        self,
        message: str,
        *,
        command: list[str] | None = None,
        exit_code: int | None = None,
        stderr: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        self.suggestion = suggestion


class ConfigError(ScopeProofError):
    """Raised when config or task YAML cannot be loaded."""

