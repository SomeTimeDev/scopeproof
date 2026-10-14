# Releasing

ScopeProof is published to PyPI by `.github/workflows/publish.yml` using
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (no API token stored in GitHub).

## One-time setup

1. Sign in to PyPI and open **Your projects → Publishing → Add a new pending publisher**.
2. Fill in:
   - PyPI project name: `scopeproof`
   - Owner: `SomeTimeDev`
   - Repository: `scopeproof`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. In GitHub, create an environment named `pypi` under **Settings → Environments**
   (optionally require your approval before it runs).

## Each release

1. Bump `version` in `pyproject.toml` and `__version__` in `scopeproof/__init__.py`.
2. Merge to `main`.
3. Create a GitHub release with tag `vX.Y.Z` matching that version.
   The workflow builds, runs `twine check`, refuses mismatched tags and uploads to PyPI.
