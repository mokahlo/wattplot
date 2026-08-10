# Contributing to Wattplot

Thanks for your interest in Wattplot — the open-source solar-canopy
planter. The project is small enough to read in an afternoon, and we
welcome issues, PRs, and forks.

## Code of conduct

This project follows the spirit of the [Contributor Covenant](https://www.contributor-covenant.org/).
Be kind, assume good faith, focus on the technical merit. Disagreements
about design choices are expected and welcome; rudeness is not.

## What to work on

Issues tagged **good first issue** are scoped for first-time
contributors. Issues tagged **help wanted** are bigger and need
domain context (firmware, FreeCAD, JLCPCB, wind engineering). Anything
else is fair game — open an issue first to align before sinking time
into a PR.

For documentation typos, broken links, or stale info, open a PR
directly — no issue needed. Use the `doc` label.

## Development setup

```bash
# Clone
git clone https://github.com/mokahlo/wattplot.git
cd wattplot

# Runtime + dev deps
pip install -r requirements.txt -r requirements-dev.txt

# Run the linter and formatter
ruff check .
ruff format .

# Run the firmware regression suite
pytest firmware/tests/

# (Optional) Run the analysis scripts
python wattplot.py --skip-model

# (Optional) Build the Jekyll site locally
# Requires Ruby + bundler; the docs build is also exercised in CI.
```

See `firmware/README.md` for the ESPHome / chip workflow and
`docs/control.html` + `tools/wattplot_control.py` for the live control
panel workflow.

## Repo conventions

- **Branch names** — Conventional Branch format: `feature/...`,
  `bugfix/...`, `hotfix/...`, `release/...`, `chore/...`. Examples:
  `feature/jekyll-404-page`, `bugfix/cut-list-stale-comment`,
  `hotfix/rotate-api-key`.
- **Commit messages** — Conventional Commits format:
  `type(scope): summary`. Examples:
  `docs(control): refresh stale banner copy`,
  `fix(tools): read API key from secrets not hardcode`.
  Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`,
  `security`, `perf`. Scopes: `firmware`, `analysis`, `models`,
  `tools`, `docs`, `ci`, `repo`.
- **PRs** — One logical change per PR. Squash-merge with the
  conventional-commit message so `git log --oneline` reads cleanly.
- **Code style** — ruff (configured in `pyproject.toml`). Run
  `ruff check .` and `ruff format .` before pushing. Pre-commit
  hooks (`.pre-commit-config.yaml`) run the same on commit.
- **Tests** — `firmware/tests/` is the live regression suite. Add a
  test for any bug fix. New analysis scripts should ship with an
  `if __name__ == "__main__"` smoke test, and ideally a real pytest.

## How the firmware is tested

The firmware regression suite (`firmware/tests/`) reads `wattplot.yaml`
as text and asserts:
  - Required entity IDs are present (`REQUIRED_IDS` list)
  - Pin assignments match the schematic rev B pin map
  - S3-specific constraints are respected (no native-USB pins, no
    SPI flash pins, no PSRAM pins)
  - Generated C++ doesn't reference retired APIs (e.g., no
    `id(script_*)` or `.state.c_str()` on TemplateSelects)

The codegen tier (which shells out to `esphome config` to compile the
YAML and inspect the generated C++) is skipped unless ESPHome is
installed locally — see the `requires_esphome` marker in
`conftest.py`.

## How the docs site is built

The site is plain Jekyll, dark theme, no plugins beyond defaults.
Layout is `docs/_layouts/default.html`; page metadata via YAML front
matter. Live at https://wattplot.org/.

Every Markdown page under `docs/` becomes a served HTML page. Internal
notes (the `docs/_internal/` folder) are excluded from the Jekyll
build via `_config.yml`.

## Releasing

There is no formal release cadence yet. Bumps to `firmware/wattplot.yaml`
header `comment: "Wattplot v..."` are the version bump. Add an entry to
`CHANGELOG.md` under "Unreleased" or a new version section when you
bump.

## Security

Found a vulnerability? Email mokahlou@gmail.com instead of opening a
public issue. The ESPHome API encryption key was leaked in 5 commits
between 2026-08-05 and 2026-08-06 (see `tools/_secrets.py` for the
post-mortem); treat any historical key references in old commits as
compromised.

## Questions

Open an issue with the `question` label. The Discussions tab (when
enabled) is for open-ended conversation; issues are for actionable
work.