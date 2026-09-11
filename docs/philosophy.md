# Philosophy

guardrail-prompt-gateway is a **learning vivisystem**: a small swarm of contracts around an LLM, not a single clever agent.

## Guiding principles (Kevin Kelly)

- Grow from the bottom up
- Maximize decentralization
- Honor errors (visible, recoverable)
- Hive mind: intelligence from boundaries, not one brain
- Distributed control: design the environment; components act inside it

## LLM-specific

- The model is a **component**, never source of truth
- Prompts are not a control plane — guardrails are **code** (schema, allowlist, validators)
- Fake LLM in the default test suite; live calls are opt-in
- Human confirmation + dry-run for irreversible side effects
