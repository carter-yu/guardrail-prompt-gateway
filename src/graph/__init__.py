"""Explicit LangGraph optimizer package (Slice 3).

This package is the control plane. It is **not** a LangChain agent:

- ``StateGraph`` + named nodes + typed ``OptimizerState`` (see ``state.py``)
- Explicit edges in ``optimizer.build_graph`` (no ``create_agent``, no prebuilt)
- Nodes call ``complete_llm`` (provider + retry) and never ``complete_request``
  (that would re-run the input gate on the optimized prompt — KD-10)

Intelligence is supposed to come from contracts + guardrails, not from a
supervisor blob that can pick any tool or recurse forever (constitution rule 8).
"""
