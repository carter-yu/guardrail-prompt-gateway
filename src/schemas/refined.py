"""Slice 3 refine-node output. Validated in code, not trusted from the model."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class RefinedPromptSchema(BaseModel):
    objective: str
    origin: str | None = None
    destination: str | None = None
    departure_date: date | None = None
    return_date: date | None = None
    constraints: list[str] = Field(default_factory=list)
    language: Literal["yue-HK", "en", "mixed"] = "mixed"
