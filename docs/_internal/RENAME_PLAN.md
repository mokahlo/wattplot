# Rename plan — Plan B if coexistence request is declined

**Why this exists:** If Andrew Welch at wattplot.com is not comfortable
with coexistence, we rename the Wattplot project before it has any
users. This is a one-session operation, not a panicked migration.

## Status as of plan creation (2026-08-05)

The Wattplot project name is in active use across:

| Layer | Count | Effort |
| --- | --- | --- |
| GitHub repo `mokahlo/wattplot` | 1 | Mechanical (GitHub redirect handles it) |
| GitHub Pages site `mokahlo.github.io/wattplot/` | ~30 pages | Find-and-replace per page |
| Firmware file `firmware/wattplot.yaml` | 1 | Find-and-replace, then re-validate + re-compile |
| ESPHome `name:` and `friendly_name:` | 2 fields | Same file |
| `project.name` in ESPHome | 1 | Same file |
| Home Assistant `device.name` (live, on flashed chip) | 1 | OTA after flash |
| GitHub Actions / workflows | depends on `.github/` contents | Find-and-replace |
| `README.md`, `hardware/`, `booth/` material | ~20 files | Find-and-replace |
| Favicon / logo SVG text | none (no wordmark in the mark, just symbols) | None — logo is symbol-only, no rename needed |
| GitHub Issue/PR titles in history | preserved | None — GitHub preserves them |
| Public stars / forks | preserved | None — they're tied to the repo, not the name |

**Total wall-clock estimate:** 2-4 hours for a careful rename, including
re-validation of firmware. Logo does **not** need to change — the
favicon is symbolic (panel + sun + planter) and contains no wordmark.

## Pre-flight: pick a new name

Names worth checking (no class 9 / 11 / 42 conflicts to my knowledge,
but verify on TESS before committing):

- **Sunbed** — short, evocative, but also a colloquial term for
  tanning bed. May have its own conflicts.
- **Solataire** — portmanteau of solar + solitaire/planter. Made-up,
  low conflict risk. Easy to spell.
- **Plotsol** — plot + sol. Short, descriptive.
- **Plantar** — Spanish/Portuguese for "to plant." Same root as
  "planter." Could work, but check that it's not already a brand.
- **Hortisol** — horticulture + solar. Awkward to say.
- **Panelsy** — silly, low-conflict.
- **Sunfold** — emphasizes the folding action. Good for marketing.

Recommendation: **Solataire** (low conflict, pronounceable, evokes
both solar and the single-unit nature of the design). Verify on TESS,
CIPO, and a Google search before committing.

## Rename steps (sequential)

### 1. Repo rename (GitHub)

1. GitHub → Settings → General → "Rename repository" → enter new name.
2. GitHub automatically redirects `github.com/mokahlo/wattplot` →
   `github.com/mokahlo/solataire` (or whatever).
3. The GitHub Pages URL changes: `mokahlo.github.io/wattplot/` →
   `mokahlo.github.io/solataire/`. Existing deep links to old URLs
   will continue to work via GitHub's redirect for HTTPS, but
   the canonical URL changes.

### 2. Local clone

```powershell
cd C:\dev
git clone https://github.com/mokahlo/solataire.git
# (or: rename the existing dir and re-point origin)
```

If you want to keep the existing working copy:

```powershell
cd C:\dev\wattplot
git remote set-url origin https://github.com/mokahlo/solataire.git
```

### 3. Bulk find-and-replace (PowerShell)

For each text file under the repo (excluding `.git/`, build outputs,
images):

```powershell
$root = 'C:\dev\solataire'
Get-ChildItem -Path $root -Recurse -File -Include '*.md','*.html','*.yaml','*.yml','*.py','*.ps1','*.sh','*.json','*.txt' |
  Where-Object { $_.FullName -notmatch '\.git\\' } |
  ForEach-Object {
    $c = Get-Content -Raw -Path $_.FullName -Encoding UTF8
    $new = $c -replace 'Wattplot','Solataire' -replace 'WATTPLOT','SOLATAIRE' -replace 'wattplot','solataire' -replace 'watt-plot','solataire' -replace 'watt_plot','solataire'
    if ($new -ne $c) {
      Set-Content -Path $_.FullName -Value $new -Encoding UTF8 -NoNewline
      Write-Host "updated: $($_.FullName.Substring($root.Length+1))"
    }
  }
```

This catches `Wattplot`, `wattplot`, `WATTPLOT`, `watt-plot`, `watt_plot`.
Re-check for `Wattplot` (case-sensitive) to make sure nothing was missed.

### 4. ESPHome name fields

In `firmware/solataire.yaml` (renamed from `wattplot.yaml`):

```yaml
esphome:
  name: solaire-controller      # was: wattplot-controller
  friendly_name: Solataire     # was: Wattplot
  project:
    name: mokahlo.solataire     # was: mokahlo.wattplot
```

After rename, **rename the file** `wattplot.yaml` → `solataire.yaml` and
update any references in scripts (`tools/`, `firmware/recover.ps1`, etc.).

Then re-validate + re-compile:

```powershell
& "C:\Program Files\PyManager\python.exe" -m esphome config firmware/solataire.yaml
& "C:\Program Files\PyManager\python.exe" -m esphome compile firmware/solataire.yaml
```

### 5. Live chip (Home Assistant)

When the chip is recovered and you flash the new firmware, HA will see
a new device. Old device stays in HA until you delete it. Rename
process in HA:

1. Flash new firmware with the new `name:`.
2. HA discovers the new device automatically (mDNS).
3. In HA → Settings → Devices & Services → ESPHome, remove the old
   `wattplot-controller` device entry.
4. Rename the new device to whatever you want for the dashboard.

### 6. Docs site

The GitHub Pages site lives at `docs/`. After the bulk rename, verify:

- All internal links still resolve (`grep -r 'href=".*wattplot' docs/`
  should be empty after step 3).
- The favicon (symbol-only) doesn't need to change, but its
  `aria-label="Wattplot"` should be updated to the new name.
- The `_config.yml` `title:` should be updated.
- The `disclaimers.html` trademark section should still be honest —
  the conflict has the same shape regardless of project name; the
  §3 text needs minimal edits (the prior-use paragraph stays, the
  contact email would now go to "Solataire" maintainer).

### 7. README, hardware docs, booth material

All under the repo root. Bulk rename in step 3 covers them. Manual
check: anything that reads "Wattplot" in a sentence that the bulk
rename didn't catch (e.g., image alt text, file names).

### 8. Commit + push

```powershell
git -c user.name='Mavis' -c user.email='Mavis@local' add -A
git -c user.name='Mavis' -c user.email='Mavis@local' commit -m "rename: Wattplot -> Solataire

* Repo renamed on GitHub (auto-redirect for old URLs)
* All docs, firmware, scripts, and metadata updated
* Firmware name fields updated (esphome.name, friendly_name, project.name)
* Firmware re-validated + re-compiled
* Logo does not change (symbol-only mark, no wordmark)
* Trademark notice in disclaimers.html updated to reflect new name"
git push origin master
```

### 9. One-time cleanup of `disclaimers.html` §3

Replace the "the author has chosen to keep the project name Wattplot
for now" paragraph with "the project is now called Solataire (renamed
2026-08-XX after the coexistence request to wattplot.com was declined;
see [RENAME_PLAN.md] for the history)." Short version, links to this
file.

## What's preserved automatically

- **GitHub stars, forks, watchers** — all tied to the repo, not
  the name. Move with the rename.
- **Old URLs** — GitHub redirects `mokahlo.github.io/wattplot/...` →
  `mokahlo.github.io/solataire/...` for the lifetime of the redirect.
- **Old git SHAs / blame** — preserved.
- **Issue history / PR history** — preserved with their original
  titles, but URL slug changes to match the new repo name.
- **Any external links pointing at `mokahlo/wattplot`** — will be
  redirected by GitHub for the lifetime of the repo. The repo
  itself is not deleted, so the redirect persists.

## Estimated user impact

If executed before the project has any users (now), rename cost is
~4 hours. If executed after 50 stars / 10 forks / anyone depends on
the URL, cost rises sharply — old links break, search results
become inconsistent, third-party tutorials go stale.

**Recommendation:** execute the rename if and only if Andrew declines
coexistence. Don't pre-emptively rename; the coexistence ask is
cheaper than the rename and has a positive expected outcome.
