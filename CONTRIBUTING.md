# Contributing

Thanks for contributing!

## Quick checklist

- [ ] Tests pass (`pytest -q`)
- [ ] **Docs updated** (user-facing and/or architecture changes)
  - If you changed code under `src/` or `cli.py`, update **README.md** and/or **ARCHITECTURE.md**.
  - If you changed file layout/storage paths, update **FILE_STORAGE_ARCHITECTURE.md**.

## CI

CI enforces a "docs updated" check on PRs:
- code changes require README/ARCHITECTURE updates
- storage/layout changes additionally require FILE_STORAGE_ARCHITECTURE updates

If the check is too strict for a specific change, add a short note to the relevant doc explaining why no user-visible/architectural change occurred.
