from __future__ import annotations

import subprocess
from pathlib import Path


def write(repo: Path, path: str, content: str) -> Path:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def init_repo(repo: Path) -> None:
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")


def commit_all(repo: Path, message: str = "initial") -> None:
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", message)


def demo_scopeproof_config() -> str:
    return """
version: 1
project:
  name: "demo"
  mission: "CLI for exporting structured data."
paths:
  include:
    - "src/**"
    - "tests/**"
    - "README.md"
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
"""


def demo_task_config() -> str:
    return """
goal: "Add CSV export support"
allowed_paths:
  - "src/**/exporters/**"
  - "tests/**"
forbidden_paths:
  - "src/**/services/**"
prefer_modify:
  - "src/demo/exporters/base.py"
"""

