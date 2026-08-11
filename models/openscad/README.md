# models/openscad -- OpenSCAD model of the Wattplot

The canonical parametric 3D model of the Wattplot planter, written
in [OpenSCAD](https://openscad.org/). Pairs with the FreeCAD
Python model under `models/freecad/`; the FreeCAD version is
authoritative, the OpenSCAD version is a teaching reference
implementation that doesn't require a GUI to render.

## Files

| File | Purpose |
|---|---|
| `wattplot.scad` | The full assembly. Renders the bed, posts, frame, panel, hinges, and actuator at the LONGi Hi-MO X10 620W preset, 35° panel tilt. ~150 lines (most of the geometry is in `parts/`). |
| `wattplot_params.scad` | A hand-maintained mirror of `wattplot_params.py` at the repo root. All dimensions in inches. The CI test `firmware/tests/test_openscad_params.py` verifies Python/SCAD parity so they don't drift. |
| `technical_drawing.scad` | Renders the same assembly as a 2D orthographic projection for the docs site's engineering section. Camera angle is set at render time (top / side / front). |
| `parts/` | Per-part modules. Each `.scad` in this directory is a self-contained part (bed, posts, hinges, panel, frame, actuator) that includes the params file and can be opened directly to render just that part. `wattplot.scad` is now a thin orchestrator that `use <>`s them. |
| `parts/_palette.scad` | Shared color palette (the canonical wattplot.scad defines its own palette inline; the per-part files each define defaults so they can render standalone). |
| `presets/` | Reserved for per-preset `.scad` files (not yet generated). The Makefile and `tools/render_openscad.sh` already render the canonical model with per-preset `-D` overrides. |

## Render

You need OpenSCAD 2021.01 or newer. Install with:
- macOS: `brew install openscad`
- Debian/Ubuntu: `apt install openscad`
- Windows: `choco install openscad`

Then either:

```bash
# one-liner (LONGi 620W only)
openscad -o wattplot.stl models/openscad/wattplot.scad

# all 5 panel presets (longi_620W, residential_60cell,
# residential_72cell, commercial_96cell, large_format_1m65)
make scad-stl-all

# preview PNGs for the docs site (camera angle set for the gallery)
make scad-preview

# 2D technical drawings (top, side, front orthographic projections)
make scad-tech-drawings

# render a single part standalone
openscad -o bed.stl models/openscad/parts/bed.scad
openscad -o frame.stl models/openscad/parts/frame.scad
```

The Makefile lives at the repo root. The shell-script wrapper is
`tools/render_openscad.sh`. Both keep the per-preset dimension
table in sync with `wattplot_params.py`'s `PANEL_PRESETS`.

## Changing a parameter

1. Edit `wattplot_params.py` first (the Python source of truth).
2. Edit `models/openscad/wattplot_params.scad` to match, with a
   comment that points at the Python location.
3. Run `pytest firmware/tests/test_openscad_params.py` to verify
   the test still passes.
4. Re-render the STLs.

If you change a value in the SCAD file first, the test will fail
and tell you which Python value is out of sync. Don't fight the
test -- fix the drift on the Python side.

## Coordinate system

- `X` = bed length (south → north). The hinge axis runs along X.
- `Y` = up.
- `Z` = bed width (east → west).

The hinge axis is at `Y = bed_rim_h_in + 0.5"` (top of the south
wall + a ½" hinge offset), `Z = -bed_outer_W_in/2 + 0.5"`. The
panel tilts around the X axis through this point.

## Show / hide flags

Each major component is gated by a `show_*` boolean at the top
of `wattplot.scad`:

```openscad
show_soil     = true;   // soil fill (visual placeholder)
show_bed      = true;   // walls + cleats + headers + skids
show_posts    = true;   // 4x4 corner posts + 2x6 panel rails
show_frame    = true;   // 2x6 perimeter + 2x4 diagonal brace
show_panel    = true;   // the panel
show_actuator = true;   // linear actuator + clevis blocks
show_hinges   = true;   // 4 butt hinges + steel rod
show_clamps   = true;   // 6 aluminum mid-clamps
show_grid     = false;  // 1' grid for scale (off by default)
```

Pass `-D show_soil=false` etc. to suppress a component. Useful
for technical drawings: `openscad -D 'show_soil=false' -D
'show_actuator=false' -o frame_only.stl models/openscad/wattplot.scad`.

## What's deliberately NOT in the model

- **Soil texture / roots** -- the soil fill is a single cube.
  Real soil is 4,000 lb of damp loam; modeling it as anything
  more than a placeholder would just inflate the STL.
- **Microinverter / MPPT** -- the model is mechanical, not
  electrical. The ESP32, INA219s, and DRV8871s are not in scope.
- **Fasteners** -- screws, bolts, and panel clamps are present
  but only as solid blocks. Real fasteners would need
  parametric threads.
- **The 5 panel presets** -- the canonical model uses the LONGi
  620W (the default). The Makefile and shell wrapper render the
  other 4 via `-D` overrides. Per-preset `.scad` files in
  `presets/` are a future commit; they're not strictly necessary
  because the `-D` overrides are deterministic.

## CI

`firmware/tests/test_openscad_params.py` is the source-of-truth
drift detector. It runs as part of the firmware pytest job (137+
tests) and as a `docs/` job step in `.github/workflows/test.yml`
(if we add one for the docs site). The test fails with a specific
diff on any Python/SCAD drift.

## What to render first

If you're reading this for the first time:

```bash
make scad                          # ~30s, $fn=16, ~500 KB
make scad-stl                      # ~2 min, $fn=64, ~2 MB
make scad-stl-all                  # all 5 presets, ~10 min
make scad-preview                  # 5 PNGs for the docs site
```

Open the PNGs in `renders/` to see the booth preview. The STL
files can be sliced with PrusaSlicer or any standard FDM
slicer. The Mini v2.4 build fits on a 250×210 mm bed; the
full-size is too big for FDM and is intended as a visualization
+ collision-check tool, not a print.
