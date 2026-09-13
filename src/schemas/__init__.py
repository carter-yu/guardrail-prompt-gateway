"""Gateway request/response schemas.

Contracts at the seam: HTTP ``GatewayRequest`` / ``GatewayResponse`` and the
refine-node ``RefinedPromptSchema``. The LLM fills JSON; Pydantic decides
whether it is data. Nodes must not persist model prose as canonical state
(constitution rule 7).
"""
