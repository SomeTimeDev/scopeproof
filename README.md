# ScopeProof

AI coding agents start focused, then drift. ScopeProof keeps their changes inside your
project's scope.

It checks agent-generated diffs for needless modules, duplicate abstractions, scope escape,
orphan files, and public API growth.

No LLM required. No cloud. No vendor lock-in.

## Problem

Small requested changes can quietly become new service layers, duplicate classes, unrelated file
edits, or public APIs that were never part of the task. ScopeProof is a deterministic CLI guardrail
for catching those signals before merge.

## What ScopeProof Checks

- `scope_escape`: changed files outside task paths or inside forbidden paths
- `module_sprawl`: too many new files or suspicious new modules
- `duplicate_symbol`: new public symbols that resemble existing symbols
- `orphan_new_file`: new production Python files that are not imported or tested
- `public_api_growth`: excessive public class/function growth for one task

## Installation

```bash
pip install scopeproof
```

For local development:

```bash
pip install -e ".[dev]"
```

## Quickstart

```bash
scopeproof init
scopeproof prompt "Add CSV export support"
scopeproof check --base HEAD
```

For pull requests:

```bash
scopeproof check --base origin/main --head HEAD
```

## Example `scopeproof.yml`

```yaml
version: 1
project:
  name: "demo"
  mission: "CLI for exporting structured data."
rules:
  max_new_files_per_task: 1
  duplicate_symbol_similarity: 0.82
  fail_on_module_sprawl: true
extension_points:
  - name: "Exporters"
    keywords: ["export", "csv"]
    prefer_existing_paths:
      - "src/**/exporters/**"
    allow_new_files_under:
      - "src/**/exporters/**"
      - "tests/**"
```

## Example `.scopeproof/task.yml`

```yaml
goal: "Add CSV export support"
allowed_paths:
  - "src/**/exporters/**"
  - "tests/**"
forbidden_paths:
  - "src/**/services/**"
prefer_modify:
  - "src/demo/exporters/base.py"
expected_behavior:
  - "Use the existing exporter interface."
verification:
  - "pytest -q"
```

## Example Report

```text
ScopeProof Report

Project: demo
Task: Add CSV export support
Diff: HEAD -> working tree

FAIL scope_escape
  src/demo/services/csv_export_service.py: Changed file matches a forbidden task path.

FAIL module_sprawl
  src/demo/services/csv_export_service.py: New file was added outside matched extension point paths.

Overall: FAIL
```

## GitHub Actions

```yaml
name: ScopeProof

on:
  pull_request:

jobs:
  scopeproof:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install scopeproof

      - run: scopeproof check --base origin/main --head HEAD --format markdown --output scopeproof-report.md
```

ScopeProof does not post PR comments in v0.1.0.

## Philosophy And Limitations

ScopeProof does not prove semantic correctness. It catches deterministic drift signals:

- changed files outside allowed paths
- suspicious new modules
- duplicated-looking symbols
- orphan new files
- unexpected public API growth

It only indexes Python with the standard library `ast` module in v0.1.0. Non-Python files can be
checked for path scope, but not for symbol-level behavior.

## Roadmap

- TypeScript/JavaScript indexing
- GitHub PR comments
- Layer/import violation checks
- Optional hook examples

## License

MIT

