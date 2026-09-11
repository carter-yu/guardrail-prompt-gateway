"""Frozen UI catalog (yue-HK + English). T2.3 scans this file and templates/."""

from __future__ import annotations

UI: dict[str, str] = {
    "title": "Guardrail Prompt Gateway",
    "prompt_label": "輸入提示詞 (Enter Prompt)",
    "model_label": "選擇模型 (Select Model)",
    "submit": "送出 (Submit)",
    "confirm": "確認執行 (Confirm)",
    "telemetry": "耗時 (Latency) | 消耗 Token (Tokens) | 預估成本 (Cost)",
    "dry_run": "模擬執行 (Dry run)",
    "provider_xai": "xAI (Grok)",
    "provider_google": "Google Gemini",
    "health": "狀態 (Status)",
}

# Simplified-only glyphs that must not appear in UI (T2.3).
SIMPLIFIED_DENYLIST: tuple[str, ...] = (
    "输入",
    "选择",
    "提交",
    "耗时",
    "预估",
    "确认",
)
