# AGENTS.md

## Project mission

ScopeProof is a tiny deterministic CLI that checks AI-agent-generated diffs for project-scope drift.

## Non-goals

- Do not add LLM calls.
- Do not add cloud services.
- Do not build a web UI.
- Do not expand beyond Python analysis in v0.1.x.
- Do not add dependencies unless they are listed in the spec.

## Engineering rules

- Keep the code simple and testable.
- Prefer small functions and dataclasses.
- Use subprocess for Git commands.
- Use Python ast for symbol indexing.
- Keep CLI output stable and covered by tests where practical.
- Do not create needless abstraction layers.

## Verification

Before claiming done, run:

```bash
python -m pytest -q
python -m ruff check .
scopeproof --help
scopeproof init --help
scopeproof check --help
```
