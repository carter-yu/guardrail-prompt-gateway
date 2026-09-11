"""T2.3: UI catalog and templates have no Simplified-only glyphs."""

from __future__ import annotations

from pathlib import Path

from app.i18n import SIMPLIFIED_DENYLIST, UI

TEMPLATES = Path(__file__).resolve().parents[1] / "src" / "app" / "templates"


def test_catalog_has_frozen_strings() -> None:
    assert UI["prompt_label"] == "輸入提示詞 (Enter Prompt)"
    assert UI["model_label"] == "選擇模型 (Select Model)"
    assert UI["submit"] == "送出 (Submit)"
    assert "耗時" in UI["telemetry"]
    assert "消耗 Token" in UI["telemetry"]
    assert "預估成本" in UI["telemetry"]


def test_no_simplified_in_catalog_or_templates() -> None:
    blobs = ["".join(UI.values())]
    for path in TEMPLATES.glob("*.html"):
        blobs.append(path.read_text(encoding="utf-8"))
    combined = "\n".join(blobs)
    for glyph in SIMPLIFIED_DENYLIST:
        assert glyph not in combined, glyph
