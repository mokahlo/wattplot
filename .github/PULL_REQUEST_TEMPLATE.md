---
name: Pull Request
about: Submit a change to Wattplot
---

## What does this PR do?

One-paragraph summary. Link the issue it closes (`Closes #N`).

## Type of change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing
      functionality to change)
- [ ] Documentation only
- [ ] Refactor / cleanup (no behavior change)
- [ ] Firmware / pin map / hardware
- [ ] Docs (stale banner removal)

## How was this tested?

- [ ] `pytest firmware/tests/` passes locally
- [ ] `ruff check .` and `ruff format --check .` clean
- [ ] Manually verified on the bench / mini (describe below)
- [ ] N/A — docs / comment / non-functional change

Describe the test or manual verification:

```
paste command + output here
```

## Checklist

- [ ] New code follows the repo conventions (Conventional Commits,
      `pyproject.toml` ruff config)
- [ ] New files have docstrings / comments where appropriate
- [ ] Public API changes are reflected in `docs/api.md` if applicable
- [ ] Stale docs flagged with a `STALE` banner instead of silently
      rewritten, unless this PR **is** the fix
- [ ] No secrets, API keys, or Wi-Fi passwords committed
- [ ] Linked to an issue (or explained why one isn't needed)
- [ ] If a firmware change: pin map / entity IDs match schematic rev B
- [ ] If a BOM / preset change: `wattplot_params.PANEL_PRESETS`
      updated AND `docs/upcycling.md` cross-referenced

## Screenshots / output

If the PR changes user-visible behavior (UI, dashboard, rendered
STL, generated report), attach before/after screenshots or the
generated output inline.

## Known follow-ups

Anything left undone that should be tracked. Link to issues or note
"will be addressed in a follow-up PR".