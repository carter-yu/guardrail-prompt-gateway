"""Slice 3 refine-node output. Validated in code, not trusted from the model.

OUTPUT GATE (constitution §2.3)
-------------------------------
``refine_prompt`` asks the LLM for JSON, then
``RefinedPromptSchema.model_validate_json``. Downstream (execute node, HTTP
``refined`` field, later ``flight_search`` args) consumes **this object**,
never assistant prose.

Why a dedicated schema instead of "whatever JSON the model wrote":
- Closed ``language`` literal (yue-HK / en / mixed) — no Simplified-Chinese tag
- Dates are ``date``, not free strings, so execute cannot invent "next Friday"
- Missing travel fields are ``None``, not hallucinated IATA codes
- On validation failure the node retries **once**, then ``SCHEMA_INVALID``

The pinned prompt ``prompts/prompt_refiner.v1.md`` describes this shape. The
prompt is not the gate — this class is.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class RefinedPromptSchema(BaseModel):
    """Structured travel/family intent. ``objective`` is the only required field."""

    objective: str
    origin: str | None = None
    destination: str | None = None
    departure_date: date | None = None
    return_date: date | None = None
    constraints: list[str] = Field(default_factory=list)
    language: Literal["yue-HK", "en", "mixed"] = "mixed"
