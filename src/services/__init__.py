"""Gateway services: input gate, router, provider factory.

These modules are the *deterministic* control plane around the LLM:

- ``input_gate`` — INPUT GATE (schema/length/PII/injection) before any model call
- ``router`` — ``get_client`` + ``complete_llm`` / ``complete_request`` (KD-10)
- ``providers`` — closed ProviderEnum factory; live SDKs stay lazy/stubbed

Graph nodes import ``complete_llm`` from here (via ``router``) and must not
import ``complete_request``.
"""
