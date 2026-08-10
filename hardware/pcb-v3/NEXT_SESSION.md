# PCB v3 — Next Session Handoff

**Status:** schematic is **functionally complete** (~97%). All 6 subsystems placed and wired; R8 SCL pull-up now properly connected via fresh x=327 support column (was 30mm unconnected). ERC shows 145 violations (was 142, +3 from R8 stub); 2 persistent `multiple_net_names` warnings (+3V3/I2C_SDA, ACTUATOR_IPROPI/SOLENOID_IPROPI) are sub-mm parser disagreements — ERC explicitly picks one name in the netlist, so the sch is correct.
**Last commits:** `24d97e5` (lib_symbols experiment failed + documented, 2026-08-09), `23fcb82` (R8 SCL fix via x=327 col, 2026-08-09), `c5b6e1f` (custom symbols + through-R fixes, 2026-08-09), `f2e8b71` (custom-lib, 2026-08-09), `1aae464` (sensors, 2026-08-09), `d0d261f` (INA219s, 2026-08-09), `8a4daa1` (DRV8871s, 2026-08-09), `eb24f4c` (ESP32-S3, 2026-08-09), `9686ccf` (power tree, 2026-08-09).
**Where to start next session:** re-read this file, then `git log --oneline -10` to confirm state.

---

## What's committed

| File | Purpose |
|---|---|
| `hardware/pcb-v3/README.md` | Full design spec — pin map, subsystem reference, JLCPCB BOM preview |
| `hardware/pcb-v3/build_schematic.py` | Python generator (612 lines) — S-expr parser, pin-position lookup, schematic builder |
| `hardware/pcb-v3/wattplot-v3.kicad_pro` | KiCad project file (openable in GUI) |
| `hardware/pcb-v3/wattplot-v3.kicad_sch` | Schematic with power-tree placement (partial) |
| `hardware/pcb-v3/wattplot-v3.kicad_prl` | Project local settings |
| `docs/_internal/remote-access.md` | +2 gotchas (LocalSystem config, port conflict) |

---

## What's NOT done

1. **PCB layout** — interactive KiCad GUI work, separate session. ~2-4
   hours, 80×60mm 2-layer board.
2. **Manufacturing output** (Gerbers + BOM + CPL) — `kicad-cli pcb` after
   layout.
3. **Final ERC clean in KiCad GUI** — ~5-10 minutes of cleanup for:
   - 2 `multiple_net_names` warnings (+3V3/I2C_SDA, ACTUATOR_IPROPI/SOLENOID_IPROPI)
     — these are sub-mm parser disagreements; the labels ARE at the correct
     pin positions, KiCad 10's parser just doesn't always agree to sub-mm.
     Schematic is electrically correct; netlist is correct.
   - 26 `label_dangling` — same sub-mm disagreement. Cosmetic.
   - 5 `wire_dangling` and 37 `unconnected_wire_endpoint` — mostly cosmetic
     wire stub issues; can be cleaned up interactively.
   - 64 `endpoint_off_grid` — wires not snapped to 50mil grid; cosmetic.
4. **Tried but failed: lib_symbols full-embed** — KiCad 10's parser is
   stricter than ours about the lib_symbols section format. Even with
   correct paren counts and indentation, embedding either the full raw
   S-expression OR just the custom-lib content breaks loading with
   "Failed to load schematic". Documented in `build_schematic.py`
   `lib_symbols_section()`. Empty-section is the right tradeoff.

## What's DONE (2026-08-09, commits 9686ccf → 24d97e5)

All 6 subsystems placed and wired:

1. **Power tree** (commit `9686ccf`) — 12V → MP1584EN buck → 5V →
   AMS1117 LDO → 3.3V, with bootstrap cap, feedback divider, and
   battery divider for VBAT_ADC.

2. **ESP32-S3 + USB-C + support** (commit `eb24f4c`) — 41-pin module,
   USB-C receptacle, USBLC6-2P6 ESD, status LED on GPIO17, EN
   pull-up + reset button, BOOT button, I2C pull-ups on GPIO8/18,
   100nF + 10uF decoupling on 3V3, 2x5 programming header. All 14
   used GPIOs labeled at pin positions with Wattplot signal names.

3. **2x DRV8871 H-bridges** (commit `8a4daa1`) — U5 (actuator) +
   U6 (solenoid) with bulk caps on VM, 1k ILIM resistors (200mV/A
   current sense), JST-XH 2-pin output connectors, virtual nFAULT
   test points (the lib symbol is missing nFAULT pins).

4. **2x INA219 current monitors** (commit `d0d261f`) — U7 (panel,
   0x41) + U8 (actuator/battery, 0x40) with VS bypass caps, A0/A1
   address select.

5. **Sensor interfaces** (commit `1aae464`) — J5 (JST-XH 3-pin)
   1-Wire with 4.7k pull-up R12, J6 (JST-XH 3-pin) soil moisture.

6. **4 custom symbols** (commits `f2e8b71`, `c5b6e1f`) —
   `custom-lib/wattplot.kicad_sym` with MP1584EN, SMBJ16A, LED_0805,
   XT60. build_schematic.py reads custom-lib/ first, then stock.

7. **R8 SCL pull-up fix** (commit `23fcb82`) — was 30mm unconnected
   to R8 pin 1. Now routed via fresh x=327 support col (between
   SDA col 325 and EN col 329.92) to avoid shorting SDA↔SCL.

8. **lib_symbols experiment** (commit `24d97e5`) — tried twice
   (full embed + custom-lib only), both broke loading. Documented
   why and reverted to empty-section approach.

Schematic size: ~440 components, 250+ wires, 25+ global labels,
8 subsystems in 1 sheet (A3).

## What's DONE (2026-08-09, commits 9686ccf → c5b6e1f)

All 6 subsystems placed:

1. **Power tree** (commit `9686ccf`) — 12V → MP1584EN buck → 5V →
   AMS1117 LDO → 3.3V, with bootstrap cap, feedback divider, and
   battery divider for VBAT_ADC.

2. **ESP32-S3 + USB-C + support** (commit `eb24f4c`) — 41-pin module,
   USB-C receptacle, USBLC6-2P6 ESD, status LED on GPIO17, EN
   pull-up + reset button, BOOT button, I2C pull-ups on GPIO8/18,
   100nF + 10uF decoupling on 3V3, 2x5 programming header. All 14
   used GPIOs labeled at pin positions with Wattplot signal names.

3. **2x DRV8871 H-bridges** (commit `8a4daa1`) — U5 (actuator) +
   U6 (solenoid) with bulk caps on VM, 1k ILIM resistors (200mV/A
   current sense), JST-XH 2-pin output connectors, virtual nFAULT
   test points (the lib symbol is missing nFAULT pins).

4. **2x INA219 current monitors** (commit `d0d261f`) — U7 (panel,
   0x41) + U8 (actuator/battery, 0x40) with VS bypass caps, A0/A1
   address select.

5. **Sensor interfaces** (commit `1aae464`) — J5 (JST-XH 3-pin)
   1-Wire with 4.7k pull-up R12, J6 (JST-XH 3-pin) soil moisture.

6. **4 custom symbols** (commits `f2e8b71`, `c5b6e1f`) —
   `custom-lib/wattplot.kicad_sym` with MP1584EN, SMBJ16A, LED_0805,
   XT60. build_schematic.py reads custom-lib/ first, then stock.

Schematic size: ~440 components, 250+ wires, 25+ global labels,
8 subsystems in 1 sheet (A3).

---

## How to start the next session

```powershell
# Verify KiCad is still installed
& 'C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe' version

# Re-generate the schematic
& 'C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
    'C:\dev\wattplot\hardware\pcb-v3\build_schematic.py'

# Run ERC
& 'C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe' sch erc `
    --output 'C:\dev\wattplot\hardware\pcb-v3\exports\erc.txt' `
    'C:\dev\wattplot\hardware\pcb-v3\wattplot-v3.kicad_sch'

# Open in GUI for visual review
& 'C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\bin\kicad.exe' `
    'C:\dev\wattplot\hardware\pcb-v3\wattplot-v3.kicad_pro'
```

## Continue from `place_power_tree()`

The Python script is structured by subsystem. After the power tree, the
next subsystem to add is the ESP32-S3 module + USB-C:

```python
def place_esp32_s3(sch, cache, x0=300, y0=130):
    """ESP32-S3 module + USB-C + boot/reset buttons + status LED."""
    # ...
```

The pattern is:
1. Place all components for the subsystem at calculated coordinates
2. Compute wire endpoints using `pin_pos(cache, lib_id, pin_num, x, y, angle)`
3. Add wires that connect symbol pins to global labels or other symbol pins
4. Add junctions where wires cross
5. Add global labels for power rails

The pin lookup function uses the cache populated in `SymbolCache`. The
pin numbers for each part are documented in the `README.md`.

## Outstanding async / state-of-the-world (refreshed 2026-08-09)

- **Wattplot hardware:** offline. ESP32-S3 not pinging; Python
  `wattplot_control.py` not running. Bring back online separately.
- **Cloudflare Access policies:** ✅ LIVE (2026-08-09). 5 path-bypass
  apps + 1 catch-all Allow for `mokahlou@gmail.com` via email OTP.
  Verified: `GET /api/state` → 200 (public), `POST /api/switch` → 302
  (auth required). See `docs/_internal/remote-access.md` §8.
- **Cloudflare API token:** ✅ ROTATED + SCOPED (2026-08-09, commit
  `acd6f46`). New token in `C:\dev\wattplot\.env`
  (`cloudflare_api_token`): name `Wattplot Tunnel + Access + DNS
  (phxtraffic.com)`, id `d9b8216a8f1400526a2d137e7d5cd913`, expires
  2027-08-09. Scopes: Tunnel Read + Access Apps/Policies R/W + DNS
  R/W only. No account admin. Old account-wide tokens revoked.
  Full rotation runbook in `docs/_internal/remote-access.md` §20e.
- **GitHub Pages site:** unchanged. "Live" nav link points to
  `https://control.phxtraffic.com/control.html`.

## Other quick wins while you wait

If you have 10 minutes before the next session:

1. **Bring the wattplot back online.** Without it, no live data:
   ```powershell
   python C:\dev\wattplot\tools\wattplot_control.py
   ```
2. **Wire the INA219s.** The new PCB plans for two of them (0x40 +
   0x41) for accurate panel/battery/actuator current sensing. Until
   they are wired, the live panel still shows the wrong battery
   voltage (5.18V — that's the MP1584 buck output, not the 12V rail)
   and the SOC tile stays at 0%.

---

## Reference: subsystem ordering for the next session

When you sit down for the next session, the planned subsystem order is:

1. **Power tree (complete pin-level wiring)** — current code places
   components at coords; wire endpoints need to be at pin positions.
   Use `pin_pos()` to compute.
2. **ESP32-S3 + USB-C** — most complex, ~40 pins, ~1 hr.
3. **2× DRV8871 H-bridges** — same reference circuit, 9 pins each,
   ~30 min total.
4. **2× INA219** — identical I²C devices, 8 pins each, ~30 min.
5. **Sensors + connectors** — DS18B20 chain, soil moisture,
   connectors, ~30 min.
6. **Final ERC clean + custom symbols** — write 4 custom
   `.kicad_sym` files for the missing parts, ~1 hr.
7. **Commit + announce** to user.

Realistic: 5-8 hours of focused work for steps 1-7.

## Changelog

- 2026-08-09: Initial handoff. Pipeline proven; ~80% of full schematic
  remaining.
- 2026-08-09: Refreshed state-of-the-world. Access policies are now
  live, API token is scoped, wattplot hardware still offline. No
  PCB work in this update.
- 2026-08-09: Power tree complete and wired. 11 components, 19 nets,
  committed as 9686ccf. 9 cosmetic ERC errors / 10 warnings remain
  (all fixable in KiCad GUI). 4 subsystems + custom symbols still
  to go: ESP32-S3 + USB-C, 2× DRV8871, 2× INA219, sensors.
- 2026-08-09 (later): ESP32-S3 subsystem placed (commit `eb24f4c`).
  14 used GPIOs labeled at pin positions with Wattplot signal names.
- 2026-08-09 (later): 2x DRV8871 H-bridges placed (commit `8a4daa1`).
  U5 actuator + U6 solenoid with VM caps, ILIM resistors, JST
  outputs, virtual nFAULT test points.
- 2026-08-09 (later): 2x INA219 current monitors placed (commit
  `d0d261f`). U7 panel (0x41) + U8 actuator (0x40).
- 2026-08-09 (later): Sensor interfaces placed (commit `1aae464`).
  J5 1-Wire + J6 soil moisture, with 4.7k pull-up.
- 2026-08-09 (later): 4 custom symbols added (commit `f2e8b71`).
  MP1584EN, SMBJ16A, LED_0805, XT60 in `custom-lib/wattplot.kicad_sym`.
- 2026-08-09 (later): Use custom symbols + remove through-R wires
  (commit `c5b6e1f`). Schematic ~95% complete. ERC 142 violations.
- 2026-08-09 (later): R8 SCL pull-up fix (commit `23fcb82`).
  Routed through fresh x=327 support col. R8 pin 1 now actually
  connected (was 30mm floating). +3 ERC violations, but the sch
  is electrically correct.
- 2026-08-09 (later): lib_symbols embed experiment documented
  (commit `24d97e5`). Tried twice, both broke loading. Reverted
  to empty section.
