"""Pinned model price table (not live billing).

OBSERVABILITY HOOK — cost estimate
----------------------------------
Constitution §3.1 ``estimated_cost_usd`` is tokens times this YAML, rounded to
6 decimals, plus ``price_table_version``. Figures are **reproducible fixtures**
for eval/UI badges, not a billing webhook. Unknown ``model_id`` → ``0.0`` and
a WARNING (T0.3) so a new Grok id cannot crash the logger.

``TelemetryLLMClient`` and graph ``_add_usage`` both call ``estimate``. The
per-call log uses the wrapper; the HTTP badge uses the graph sum (KD-17).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger(__name__)

DEFAULT_PRICES_PATH = Path(__file__).resolve().parents[2] / "eval" / "prices.yaml"


class PriceTable:
    """Lookup USD per 1M tokens. Unknown ``model_id`` → 0.0 + WARNING."""

    def __init__(self, path: Path | None = None, data: dict[str, Any] | None = None) -> None:
        if data is not None:
            self._data = data
        else:
            source = path if path is not None else DEFAULT_PRICES_PATH
            self._data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
        self.version = str(self._data.get("version") or "unknown")
        models = self._data.get("models") or {}
        if not isinstance(models, dict):
            models = {}
        self._models: dict[str, dict[str, Any]] = {
            str(k): v for k, v in models.items() if isinstance(v, dict)
        }

    def estimate(self, *, model_id: str, token_in: int, token_out: int) -> float:
        row = self._models.get(model_id)
        if row is None:
            logger.warning(
                "unknown_model_price",
                component="prices",
                outcome="skipped",
                model_id=model_id,
            )
            return 0.0
        input_usd = float(row.get("input_usd") or 0.0)
        output_usd = float(row.get("output_usd") or 0.0)
        return round((token_in / 1_000_000) * input_usd + (token_out / 1_000_000) * output_usd, 6)
