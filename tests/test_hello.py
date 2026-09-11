"""Phase 0 unit tests for hello / logging (offline)."""

from __future__ import annotations

from guardrail_prompt_gateway.hello import main
from guardrail_prompt_gateway.logging import get_logger, setup_logging


def test_setup_logging_does_not_raise() -> None:
    """H1: logging setup should work without errors."""
    setup_logging(level="INFO")


def test_get_logger_returns_logger() -> None:
    """H2: get_logger should return a usable logger."""
    setup_logging()
    log = get_logger("test")
    assert log is not None
    log.info("test_message", component="hello", outcome="success")


def test_main_runs_without_error() -> None:
    """H3: main() should execute cleanly."""
    main()
