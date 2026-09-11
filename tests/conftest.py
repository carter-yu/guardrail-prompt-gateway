"""Shared pytest fixtures."""

from __future__ import annotations

from guardrail_prompt_gateway.logging import setup_logging


def pytest_configure() -> None:
    setup_logging(level="INFO")
