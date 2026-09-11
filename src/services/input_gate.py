"""Deterministic input gate. First failure wins. Never logs matched PII."""

from __future__ import annotations

import re
from dataclasses import dataclass

from lib.logger import get_logger
from schemas.gateway import ErrorType

logger = get_logger(__name__)

MAX_PROMPT_CHARS = 2000

# 1–2 letters, 6 digits, check digit 0-9/A; optional parens around the check digit.
# Trailing (?![A-Za-z0-9]) so `A123456(7)` still matches (`)` is not a word char).
_HKID = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z]{1,2}\d{6}(?:[\dA]|[\(\（][\dA][\)\）])(?![A-Za-z0-9])",
)
_PAN_CANDIDATE = re.compile(r"(?:\d[ -]?){13,19}")
_INJECTION = (
    "ignore previous instructions",
    "ignore all previous",
    "<|system|>",
    "</system>",
    "[inst]",
    "developer mode",
)


@dataclass(frozen=True, slots=True)
class GateReject:
    error_type: ErrorType
    error_message: str
    pii_type: str | None = None


def check_input(prompt: str) -> GateReject | None:
    """Return a reject reason or None if the prompt may proceed."""
    if len(prompt) > MAX_PROMPT_CHARS:
        return _reject(ErrorType.PROMPT_TOO_LONG, "prompt exceeds 2000 characters")
    if _HKID.search(prompt):
        return _reject(ErrorType.PII_BLOCKED, "HKID pattern blocked", pii_type="hkid")
    if _has_luhn_pan(prompt):
        return _reject(ErrorType.PII_BLOCKED, "payment card pattern blocked", pii_type="pan")
    lowered = prompt.casefold()
    for token in _INJECTION:
        if token in lowered:
            return _reject(ErrorType.INJECTION_TOKEN, "injection token blocked")
    return None


def _reject(
    error_type: ErrorType, message: str, *, pii_type: str | None = None
) -> GateReject:
    logger.info(
        "input_rejected",
        component="input_gate",
        outcome="skipped",
        error_type=error_type.value,
        pii_type=pii_type,
    )
    return GateReject(error_type=error_type, error_message=message, pii_type=pii_type)


def _has_luhn_pan(prompt: str) -> bool:
    for match in _PAN_CANDIDATE.finditer(prompt):
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            return True
    return False


def _luhn_ok(digits: str) -> bool:
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0
