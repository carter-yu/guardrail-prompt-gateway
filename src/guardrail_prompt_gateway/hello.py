"""Minimal proof-of-life module for Phase 0."""

from __future__ import annotations

from guardrail_prompt_gateway import __version__
from guardrail_prompt_gateway.logging import get_logger, setup_logging

logger = get_logger(__name__)


def main() -> None:
    """Verify environment and structured logging."""
    setup_logging()
    logger.info(
        "guardrail_prompt_gateway_alive",
        component="hello",
        outcome="success",
        phase="0",
        version=__version__,
    )
    print(f"Hello from guardrail-prompt-gateway {__version__}!")


if __name__ == "__main__":
    main()
