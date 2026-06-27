from __future__ import annotations

import subprocess
from pathlib import Path

from scopeproof.errors import ScopeProofError
from scopeproof.models import ChangedFile
from scopeproof.paths import normalize_path


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    command = ["git", *args]
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise ScopeProofError(
            "Git command failed.",
            command=command,
            exit_code=completed.returncode,
            stderr=completed.stderr.strip(),
            suggestion="Check that the repository and refs exist.",
        )
    return completed


def ensure_git_repo(cwd: Path) -> None:
    try:
        _run_git(["rev-parse", "--is-inside-work-tree"], cwd)
    except ScopeProofError as exc:
        raise ScopeProofError(
            "ScopeProof must run inside a Git repository.",
            command=exc.command,
            exit_code=exc.exit_code,
            stderr=exc.stderr,
            suggestion="Run 'git init' first.",
        ) from exc


def get_repo_root(cwd: Path) -> Path:
    ensure_git_repo(cwd)
    completed = _run_git(["rev-parse", "--show-toplevel"], cwd)
    candidate = Path(completed.stdout.strip()).resolve()
    if candidate.exists():
        return candidate
    for parent in [cwd.resolve(), *cwd.resolve().parents]:
        if (parent / ".git").exists():
            return parent
    return candidate


def parse_name_status(output: str) -> list[ChangedFile]:
    changed: list[ChangedFile] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        status_token = parts[0]
        status = status_token[0]
        if status in {"R", "C"} and len(parts) >= 3:
            changed.append(
                ChangedFile(
                    path=normalize_path(parts[2]),
                    status=status,
                    old_path=normalize_path(parts[1]),
                )
            )
        elif len(parts) >= 2:
            changed.append(ChangedFile(path=normalize_path(parts[1]), status=status))
    return changed


def get_untracked_files(cwd: Path) -> list[ChangedFile]:
    completed = _run_git(["ls-files", "--others", "--exclude-standard"], cwd)
    return [
        ChangedFile(path=normalize_path(line), status="A")
        for line in completed.stdout.splitlines()
        if line.strip()
    ]


def get_changed_files(
    base: str,
    head: str | None,
    cwd: Path,
    include_untracked: bool | None = None,
    staged: bool = False,
) -> list[ChangedFile]:
    if include_untracked is None:
        include_untracked = head is None and not staged

    args = ["diff", "--name-status", "--find-renames"]
    if staged:
        if head:
            raise ScopeProofError(
                "--staged cannot be combined with --head.",
                suggestion="Use --staged with --base REF, or use --base/--head without --staged.",
            )
        args.append("--cached")
        args.append(base)
        include_untracked = False
    elif head:
        args.append(f"{base}...{head}")
    else:
        args.append(base)
    completed = _run_git(args, cwd)
    changed = parse_name_status(completed.stdout)
    if include_untracked:
        seen = {item.path for item in changed}
        changed.extend(item for item in get_untracked_files(cwd) if item.path not in seen)
    return changed


def get_file_at_ref(path: str, ref: str, cwd: Path) -> str | None:
    command_path = normalize_path(path)
    completed = subprocess.run(
        ["git", "show", f"{ref}:{command_path}"],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def get_file_at_index(path: str, cwd: Path) -> str | None:
    command_path = normalize_path(path)
    completed = subprocess.run(
        ["git", "show", f":{command_path}"],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def list_tracked_files(cwd: Path) -> list[str]:
    completed = _run_git(["ls-files"], cwd)
    return [normalize_path(line) for line in completed.stdout.splitlines() if line.strip()]
