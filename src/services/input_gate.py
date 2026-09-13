"""Deterministic input gate. First failure wins. Never logs matched PII.

INPUT GATE (constitution §2.1 / KD-11)
--------------------------------------
Guardrails are **code**. A prompt saying "please ignore PII" is not a gate.
This module runs *before* any graph node or provider call
(``complete_request`` and ``POST /api/v1/generate``).

Order is schema-adjacent then cheap detectors; first hit returns:

1. Length — reject, do not truncate (T1.2). Truncation would still send a
   partial secret or a sliced injection to the model.
2. HKID pattern — **block**, do not redact-and-forward (KD-11).
3. Payment-card pattern + Luhn — same block. Bare 16-digit runs that fail
   Luhn are not blocked (reduces false positives on dates/ids).
4. Injection substrings — demo tripwire, not a jailbreak product.

On reject: structured log ``event=input_rejected``, ``outcome=skipped``,
``error_type`` from the closed ``ErrorType`` enum. The matched PII string is
never in the log (constitution §3.2).
"""

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
# Case-insensitive via casefold() at check time. These are *tokens*, not a model.
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
    """Closed reject reason. Callers map this onto GatewayResponse, not onto a retry."""

    error_type: ErrorType
    error_message: str
    pii_type: str | None = None


def check_input(prompt: str) -> GateReject | None:
    """Return a reject reason or None if the prompt may proceed.

    INPUT GATE entry. Does not call an LLM. Does not redact. None means the
    graph/router may continue; a GateReject means HTTP 400 / outcome=skipped.
    """
    # 1. Length — Python characters, not tokens. Pydantic max_length=2000 is the
    # schema half; this catches oversize that bypassed validation (raw JSON).
    if len(prompt) > MAX_PROMPT_CHARS:
        return _reject(ErrorType.PROMPT_TOO_LONG, "prompt exceeds 2000 characters")
    # 2. HKID — block. Do not log the match; pii_type is the category only.
    if _HKID.search(prompt):
        return _reject(ErrorType.PII_BLOCKED, "HKID pattern blocked", pii_type="hkid")
    # 3. PAN + Luhn — block. Non-Luhn digit runs are allowed through.
    if _has_luhn_pan(prompt):
        return _reject(ErrorType.PII_BLOCKED, "payment card pattern blocked", pii_type="pan")
    # 4. Injection tripwire — substring denylist. Untrusted text is never a
    # control channel; this is belt-and-suspenders before the system prompt.
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
