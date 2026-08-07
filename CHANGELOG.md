# Changelog

All notable changes to Wattplot are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Versioning of the firmware is tracked in the `comment:` field of
`firmware/wattplot.yaml`. Mechanical / docs-only changes do not bump
the firmware version; they get a `## Unreleased` section here until the
next firmware release.

## [Unreleased]

### Security
- **Removed hardcoded API encryption key from 9 tools files.** The
  `cz0STvY6M+0ob9ydfsi28MDAL9b5P8VsmXsnZv3t7BU=` key had been committed
  in 5 public commits (2026-08-05 → 2026-08-06). All tools now resolve
  the key via `tools/_secrets.py` (env var → `firmware/secrets.yaml`
  → `~/.config/wattplot/api_key`). **Operator action required:**
  rotate the key on the chip and update `firmware/secrets.yaml`.
  See `tools/_secrets.py` for the rotation procedure.

### Changed
- **Docs accuracy pass.** Fixed broken `<a>` markup in 9 nav blocks,
  3D viewer STL 404, MPPT model number (`75/15` → `100/30`), README
  self-contradiction, broken `STRUCTURE` import in
  `models/shadow_raycaster.py`, missing gallery tiles, and
  `firmware/README.md` rewritten against `wattplot.yaml` v3.2.
- **18 stale docs stamped with `STALE` banners** pointing at the
  canonical sources (`docs/pinmap.html`, `docs/schematic.html`,
  `firmware/wattplot.yaml`, `firmware/README.md`). The build,
  wiring, PCB, sensor-placement, watering, test-checklist, and
  control-law MDs reference the v1/v2.4 architecture (ESP32-WROOM-32
  + BMI160 + limit switches + 90° BedSun mode) and need a future
  regeneration pass against the current YAML.
- **Logging doc refreshed** against `wattplot.yaml` v3.2
  `logger.logs:`: `mppt` / `imu` / `watering` / `controller` tags
  removed (retired); `boot` / `state` / `nfault` / `solenoid` /
  `endpoint` / `calib` / `alarm` / `control` tags added. Example
  log lines and line numbers updated.
- **ROADMAP replaced** with the README's live Status table + a
  prioritized "Next up" queue. The previous phase 1-7 checklist was
  3 phases behind reality.

### Added
- **`tools/_secrets.py`** — central API key loader (see Security).
- **`tools/wattplot_control.py` rewrite** — zeroconf-based mDNS
  discovery, link watchdog (force-reconnect after 30 s stale),
  CORS allowlist for github.io reads, `/api/whoami`,
  `/logs.html` route.
- **`docs/control.html` UI** — stale-data banner, auth banner, and
  control gating that integrates with Cloudflare Access.
- **`docs/logs.html`** — self-contained viewer for the wattplot.log
  files served by `/api/logs`.
- **`analysis/post_bending.py` + report** — closes the gap where
  `wind_load.py` treats the structure as a rigid body. 4x4 unbraced
  posts fail at 35° (SF 0.65 vs target 1.5); remedies: 6x6 posts or
  square-cut lateral bracing.
- **`analysis/wind_load.py` verdict refreshed** for 27.5" walls /
  25.5" soil fill / corner-post drag included. 35° → SF 2.55.
- **`firmware/wattplot.yaml` v3.2** — boot log banner (firmware
  version, restart reason, free heap), IPROPI fast/slow sensor
  split (fixes 294 MB/day log blow-up).
- **CI runs firmware pytest + post-bending.**
- **`.gitignore`** updated for `logs/`, ESPHome build logs, sim HTML
  intermediates, commit_msg drafts, `parts/` (vendor reference PDFs),
  `renders/*.svg`.
- **`requirements-dev.txt`** — pytest + ruff for the test suite.
- **Five new bench/booth utilities** in `tools/`:
  `audit_gallery.py`, `check_soil.py`, `demo_tilt.py`,
  `show_state.py`, `test_solenoid.py`.
- **`tools/add_live_nav_link.ps1`** — splice the Live link into every
  HTML page that has the topnav.
- **CONTRIBUTING.md, CHANGELOG.md** (this file), `.editorconfig`,
  `.gitattributes`, `.pre-commit-config.yaml`,
  `.github/dependabot.yml`, GitHub issue + PR templates.

### Removed
- `models/legacy_cadquery/` (3 files) — old cadquery model, replaced
  by `models/freecad/`.
- `booth/*.md` duplicates of `docs/*.md` (APPLICATION, FAQ,
  ONE_PAGER, DEMO_SCRIPT, POSTER, oc_application draft) — the docs/
  versions are canonical and served by Jekyll.
- `booth/viewer.html`, `booth/sim_dashboard.html` (old copies;
  canonical versions live in `docs/booth/`).
- `booth/wattplot_v2*.stl`, `booth/*.bak`, `booth/wood_*_preview.png`
  (9 deleted-PNG references from the gallery).
- `tools/commit_msg_*.txt` (commit-message drafts) and
  `tools/sim_inline_*.html` (gitignored intermediates).

## [3.2] — 2026-08-05

### Changed
- **Pin map migrated to schematic rev B (2026-08-03).** ESP32-S3
  replaces ESP32-WROOM-32. H-bridge IN1/IN2 = GPIO1/GPIO2,
  EN = GPIO11 (compat-only, schematic ties EN → 3V3). Solenoid on
  second DRV8871 (U5b) on GPIO10. Soil on GPIO6, battery V on GPIO7
  (100k/10k divider), DS18B20 on GPIO16. Two INA219s at I²C 0x40
  (motor) and 0x41 (panel).
- **BedSun (90°) mode retired.** Wind calc fails at design wind
  (SF_overturning 1.26 at 90°); structural max is 35°.
- **Limit switches removed.** Current-based homing via actuator
  IPROPI pin (GPIO4) replaces them.

### Added
- IPROPI current sense (motor + solenoid) on GPIO4 / GPIO5 with
  endstop-current detection (default 0.90 A, 1000 ms debounce).
- Self-calibration script (`button.calibrate_actuator`).
- v3 IPROPI baseline patch (firmware/v3 commit 15cf314).

## [3.1] — 2026-08-05

### Removed
- **Limit switches** at hinge endstops (GPIO34, GPIO35). Replaced by
  current-based homing.

## [3.0] — 2026-08-05

### Changed
- Migrated from ESP32-C3 → ESP32-S3.
- Dual DRV8871 (actuator + solenoid) replaces single DRV8871 +
  relay.
- Sunapex 10A MPPT standalone (no host connection) replaces the
  v2.x DPS5005-as-MPPT pattern.
- 35° structural cap replaces 90° BedSun mode.

## [2.x] — 2026-07 (pre-Mini)

- ESP32-C3 Pro Mini + BMI160 IMU + 1-channel relay + DPS5005 MPPT.
- GPIO5 solenoid relay, GPIO4 soil, GPIO10 1-Wire, GPIO8/9 I²C,
  GPIO20/21 UART.
- 90° "wring-out" BedSun mode and azimuth tracking included.
- See git history pre-`15cf314` for the full v2.x line.

## [1] — 2026-07-21

- Initial commit (`4e21a59`). ESP32-WROOM-32 dev board, no PCB.
- Single linear actuator + 4×4 posts, 20" soil fill, 12" deep walls.
- See `firmware/README.md` §"Files" for the early history.

[Unreleased]: https://github.com/mokahlo/wattplot/compare/main...HEAD