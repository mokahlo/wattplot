# KiCad PCB Design — Programmatic Workflow

## Overview

Wattplot PCB v3 is a 2-layer, 80×60mm board with ~46 unique components. Doing
the full layout in the KiCad GUI is the **slowest path** because clicking
and dragging through hundreds of components is tedious. This doc describes
a faster, scripted path using `pcbnew` (KiCad's Python API) plus
FreeRouting for the actual trace routing.

---

## Why the auto-generated schematic is "unintelligible"

The current `build_schematic.py` places each component at a hardcoded (x, y)
position chosen to make wires **not cross** during auto-generation. It does
NOT group components by subsystem (power, MCU, motor drivers, sensors).

When you open the result in the GUI, the symbols are spread across the sheet
in a non-logical order. This is fine for ERC (which only cares about
connections, not visual layout) but miserable for human review.

**The fix is straightforward but optional:** either rearrange manually in
the GUI after generation (`M` to move, `G` to grab-drag), or modify
`build_schematic.py` to place by subsystem. The recommended approach is
the manual `M`-to-move pass — it's 5-10 min of focused work.

The schematic is **electrically correct** (ERC runs cleanly except for
2 cosmetic `multiple_net_names` warnings that are sub-mm parser
disagreements), so layout work doesn't need the GUI schematic to be
pretty — it just needs the **netlist** (which is what matters for the PCB).

---

## Programmatic PCB layout — the full flow

### 1. Generate the schematic (one-time, deterministic)
```powershell
& 'C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
    'C:\dev\wattplot\hardware\pcb-v3\build_schematic.py'
```
This regenerates `wattplot-v3.kicad_sch` from scratch. The sch has 46
components, 250+ wires, 25+ global labels.

### 2. Initialize the PCB file
```powershell
& 'C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
    'C:\dev\wattplot\hardware\pcb-v3\init_layout.py'
```
This creates `wattplot-v3.kicad_pcb` with:
- 80×60mm board outline
- 4× M3 mounting holes
- 2-layer stackup
- JLCPCB-friendly design rules (6 mil, 0.3mm via, 0.6mm pad)
- `Power` netclass (20 mil trace, 0.8mm via)

### 3. Import the netlist (CRITICAL STEP — known issue)

**Problem:** `kicad-cli sch export netlist` produces an EMPTY netlist because
the schematic's `lib_symbols` section is empty (KiCad 10's parser is
stricter than ours — embedding lib_symbols breaks loading). The CLI
exporter can't resolve lib_ids to footprints, so it gives up.

**Workaround options:**

| Method | Speed | Reliability |
|---|---|---|
| **A. Run "Update PCB from Schematic" in the GUI** | ~30s | ✅ Always works (GUI uses internal API) |
| **B. Use `extract_netlist.py` to parse S-expr directly** | ~5s | ⚠️ Only gets component list, no nets |
| **C. Add lib_symbols section programmatically via Python API** | ~30s | ✅ Most reliable for scripting |

**Recommended:** Run `Tools → Update PCB from Schematic (F8)` once in the
GUI to seed the PCB with components. Then save the file. All subsequent
layout work happens via Python scripts that load this file.

### 4. Programmatic component placement

The `pcbnew` Python API lets you:
- Load the board: `board = pcbnew.LoadBoard('wattplot-v3.kicad_pcb')`
- Get all footprints: `for fp in board.GetFootprints():`
- Move a footprint: `fp.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))`
- Rotate: `fp.SetOrientation(degrees * 10)` (tenths of degrees)
- Flip side: `fp.SetLayer(pcbnew.B_Cu)`
- Save: `pcbnew.SaveBoard(path, board)`

**Important gotcha:** Do NOT modify a PCB from a script while the
schematic or PCB is open in the GUI — file conflicts will corrupt the
project. Close KiCad first, run script, reopen.

**Coordinate system:**
- Origin is the top-left of the page
- Units are nanometers (1 mm = 1,000,000 nm)
- Use a helper: `def mm(x): return int(x * 1_000_000)`

**Subsystem placement plan (80×60mm board):**

```
        ESP32-S3 (antenna)
   ┌──────────────────────────┐
   │  [U1 MP1584] [U2 buck]   │  power
   │  [U3 AMS1117]             │  3.3V
   │                           │
   │  [U5a DRV8871] [U7 INA]  │  motor drive
   │  [U6b DRV8871] [U8 INA]  │
   │                           │
   │  [J1 XT60 battery]        │  input
   │  [J3 J4 J5 J6 J7 J8]     │  outputs/sensors
   │  [J2 USB-C]  [TP1-5]     │  test
   └──────────────────────────┘
       connector edge
```

### 5. Track routing

Two options:

**Option A: FreeRouting (recommended for first pass)**

1. Export the unrouted board to Specctra DSN:
   ```powershell
   & 'C:\...\kicad-cli.exe' pcb export specctra --output 'exports/wattplot.dsn' 'wattplot-v3.kicad_pcb'
   ```
2. Run FreeRouting (Java, free): http://freerouting.org/
   - Open the .dsn file
   - Routing → Autoroute
   - File → Export Specctra Session File
3. Import back:
   ```powershell
   & 'C:\...\kicad-cli.exe' pcb import specctra 'exports/wattplot.ses' 'wattplot-v3.kicad_pcb'
   ```

**Option B: KiCad's built-in interactive router (more work, more control)**

`Place → Route Single Track` (W). Click pad to start, click again to add
corner, click to end. The router respects design rules, net classes, and
via styles. For 250+ wires this is hours of work.

**Recommendation:** Use FreeRouting for the first 80% pass, then fix the
remaining 20% by hand in the GUI.

### 6. Design rule check (DRC)

```powershell
& 'C:\...\kicad-cli.exe' pcb drc --output 'exports/drc.txt' 'wattplot-v3.kicad_pcb'
```

View the report. Common issues:
- Clearance violations (move trace or add a via)
- Track width violations (right-click trace → Properties → adjust)
- Unconnected items (ratsnest will show)

### 7. Manufacturing outputs (JLCPCB)

```powershell
# Gerbers
& 'C:\...\kicad-cli.exe' pcb export gerbers --output 'gerbers/' 'wattplot-v3.kicad_pcb'

# Drill files (Excellon)
& 'C:\...\kicad-cli.exe' pcb export drill --output 'gerbers/' 'wattplot-v3.kicad_pcb'

# Position file (for JLCPCB SMT)
& 'C:\...\kicad-cli.exe' pcb export pos --format csv --output 'exports/pos.csv' 'wattplot-v3.kicad_pcb'

# BOM (for JLCPCB or manual sourcing)
& 'C:\...\kicad-cli.exe' sch export bom --output 'exports/bom.csv' 'wattplot-v3.kicad_sch'
```

Then zip the gerbers/ directory and upload to JLCPCB.

---

## Reference: pcbnew Python API cheatsheet

```python
import pcbnew

# Board lifecycle
board = pcbnew.LoadBoard('path.kicad_pcb')          # load existing
board = pcbnew.NewBoard('path.kicad_pcb')           # create new
pcbnew.SaveBoard('path.kicad_pcb', board)           # save

# Iterate
for fp in board.GetFootprints():                    # all footprints
    ref = fp.GetReference()
    pos = fp.GetPosition()                          # VECTOR2I
    fp.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))
    fp.SetOrientation(degrees * 10)                # tenths of degrees
    fp.SetLayer(pcbnew.F_Cu)                        # or pcbnew.B_Cu
    fp.Flip(pcbnew.B_Cu, False)                     # flip side

# Find by reference
fp = board.FindFootprintByReference('U1')

# Iterate pads
for pad in fp.Pads():
    name = pad.GetPadName()
    pos = pad.GetPosition()
    net = pad.GetNet()                              # NETINFO_ITEM
    pad.SetNet(net)

# Iterate tracks (routed wires)
for track in board.GetTracks():
    if track.Type() == pcbnew.PCB_TRACE_T:
        start = track.GetStart()
        end = track.GetEnd()
        width = track.GetWidth()
        net = track.GetNet()

# Add a track
track = pcbnew.PCB_TRACK(board)
track.SetStart(pcbnew.VECTOR2I(x1, y1))
track.SetEnd(pcbnew.VECTOR2I(x2, y2))
track.SetWidth(int(0.25 * 1_000_000))               # 0.25mm
track.SetLayer(pcbnew.F_Cu)
track.SetNet(net_obj)
board.Add(track)

# Add a via
via = pcbnew.PCB_VIA(board)
via.SetPosition(pcbnew.VECTOR2I(x, y))
via.SetDrill(int(0.3 * 1_000_000))                  # 0.3mm
via.SetWidth(int(0.6 * 1_000_000))                  # 0.6mm pad
board.Add(via)

# Add a zone (copper pour, e.g. GND plane)
zone = pcbnew.ZONE_CREATE(board)
zone.SetLayer(pcbnew.B_Cu)
zone.SetNetCode(0)                                  # GND
zone.AddPolygon([(0,0), (80,0), (80,60), (0,60)])
board.Add(zone)

# Design rules
ds = board.GetDesignSettings()
ds.m_TrackMinWidth = mm_to_nm(0.15)
ds.m_ViaMinSize = mm_to_nm(0.6)
ns = ds.m_NetSettings
default_nc = ns.GetDefaultNetclass()
default_nc.SetTrackWidth(mm_to_nm(0.25))
```

---

## Reference: Build a placement file

A plain text format for placing components:
```
# placement.txt
# ref  x_mm  y_mm  rotation_deg  side
U1     10.0   5.0   0             top
U2     20.0   5.0   90            top
J1     75.0  55.0   0             top
```

Read this file, look up each ref in the PCB's footprints, set its
position. This is how to iteratively refine placement without re-running
the whole script.

---

## Reference: FreeRouting integration

FreeRouting is a Java-based autorouter. The flow is:
1. Export `pcb-file.dsn` (Specctra DSN) from KiCad
2. Open in FreeRouting GUI → Autoroute → wait
3. Export `pcb-file.ses` (Specctra session)
4. Import the .ses back into KiCad

For wattplot v3, the key parameters to set in FreeRouting:
- Track width: 0.25mm (10 mil) for signal, 0.5mm (20 mil) for power
- Clearance: 0.2mm
- Via drill: 0.3mm
- Via pad: 0.6mm
- Layers: F.Cu (top) + B.Cu (bottom) for 2-layer

---

## Common pitfalls

1. **GUI open while script runs** — file conflict, corruption. Close KiCad.
2. **Wrong units** — pcbnew uses nanometers internally. 1mm = 1,000,000.
3. **Footprint not in library** — `FootprintLoad` returns None. Check the
   library name and footprint name.
4. **Same footprint used twice** — `FootprintLoad` returns a shared
   reference. Use `pcbnew.MODULE(board)` + `SetFPID()` to create a fresh
   instance, OR call `board.Add(footprint)` with each new instance.
5. **Empty lib_symbols section** — the schematic loads in GUI but the
   `kicad-cli sch export netlist` returns empty. Use the GUI's
   "Update PCB from Schematic" or the Python API workaround.

---

## See also

- `docs/cloudflare.md` — Cloudflare API reference
- `docs/github.md` — GitHub API reference
- `hardware/pcb-v3/README.md` — board spec, pin map, subsystem reference
- `hardware/pcb-v3/NEXT_SESSION.md` — schematic state, what's left
- `hardware/pcb-v3/build_schematic.py` — schematic generator
- `hardware/pcb-v3/init_layout.py` — PCB initialization
- `hardware/pcb-v3/extract_netlist.py` — netlist extraction workaround
