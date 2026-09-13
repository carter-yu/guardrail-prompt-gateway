"""Shared library: telemetry, prices, Fake LLM (Slice 0).

This package is the LLM *component* seam, not an agent runtime:

- ``llm`` — ``LLMClient`` protocol, Fake stub, ``TelemetryLLMClient`` wrapper
- ``logger`` — coerce + emit constitution §3.1 ``llm_call`` JSON
- ``tracer`` — Langfuse protocol + no-op (rule 19)
- ``prices`` — pinned ``eval/prices.yaml`` cost estimates
- ``clock`` — injectable Asia/Hong_Kong timestamps

Graph and router import these. They do not import LangChain Chat models here.
"""
