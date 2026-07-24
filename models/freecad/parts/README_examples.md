# Lumber library — usage examples

## Before / after

**Before** (current `bed_wall.py` style):
```python
from models.freecad.parts._helpers import box, add_feature
from models.freecad.materials import LUMBER

NOMINAL = "2x12"
T = LUMBER[NOMINAL]["actual_t"]    # 1.5
H = LUMBER[NOMINAL]["actual_h"]    # 11.25
NOTCH_DEPTH = 3.0

def make_bed_long_wall(doc, side="north", name=None):
    wall = box(BED_L, T, H, x=0, y=0, z=0)
    notch = box(NOTCH_DEPTH, H, T / 2.0, x=0, y=0, z=0)
    wall = wall.cut(notch)        # cut +X end
    notch = box(NOTCH_DEPTH, H, T / 2.0, x=BED_L - NOTCH_DEPTH, y=0, z=0)
    wall = wall.cut(notch)        # cut -X end
    return add_feature(doc, name, wall)
```

**After** (with `lumber.py`):
```python
from models.freecad.parts.lumber import make_lumber, cut_end_notch
from models.freecad.parts._helpers import add_feature

def make_bed_long_wall(doc, side="north", name=None):
    wall = make_lumber("2x12", length=BED_L, axis="X", origin=(0, 0, 0))
    wall = cut_end_notch(wall, "2x12", length=3.0,
                         end_offset=0, end_axis="X")                # +X end
    wall = cut_end_notch(wall, "2x12", length=3.0,
                         end_offset=BED_L - 3.0, end_axis="X")      # -X end
    return add_feature(doc, name, wall)
```

The "after" reads like a lumber yard: "a 2x12, 96 inches, with half-lap notches at both ends."

## Common patterns

### Place a 2x6 horizontal at a specific point
```python
from models.freecad.parts.lumber import make_lumber
beam = make_lumber("2x6", length=42, origin=(10, 0, 5))
```

### Vertical post
```python
post = make_lumber("4x4", length=120, axis="Y", origin=(0, 0, 0))
# Now you have a 10-ft post, base at origin, going up the Y axis
```

### A board with one half-lap end
```python
from models.freecad.parts.lumber import make_lumber, cut_end_notch
beam = make_lumber("2x6", length=42)
beam = cut_end_notch(beam, "2x6", length=3.0,
                     end_offset=42 - 3.0, end_axis="X")
```

### Drill a hole through a board
```python
from models.freecad.parts.lumber import make_lumber, make_drilled_hole
import FreeCAD as App

rail = make_lumber("2x6", length=42, origin=(0, 0, 0))
hole = make_drilled_hole(diameter=0.5, axis="Y", through=True)
hole.translate(App.Vector(21, 0, 2.75))   # 21" along X, 2.75" up from bottom
rail = rail.cut(hole)
```

### Full bed corner: 2 long walls + 2 short walls, all with half-laps
```python
from models.freecad.parts.lumber import make_lumber, cut_end_notch
from models.freecad.parts._helpers import add_feature

def make_bed(doc, name="Bed"):
    L, W = 96.0, 44.6
    T_long = make_lumber("2x12", length=L, origin=(0, 0, 0))           # north
    T_long = cut_end_notch(T_long, "2x12", 3.0, 0, "X")
    T_long = cut_end_notch(T_long, "2x12", 3.0, L - 3.0, "X")
    T_short = make_lumber("2x12", length=W, axis="Z", origin=(0, 0, 0))  # west
    T_short = cut_end_notch(T_short, "2x12", 3.0, 0, "Z")
    T_short = cut_end_notch(T_short, "2x12", 3.0, W - 3.0, "Z")
    # ... add east and south walls, position them, fuse or add separately
    return add_feature(doc, name, T_long)
```

## Why this is better than primitives

- **Read like a lumber yard.** `make_lumber("2x6", length=42)` is what you'd
  ask for at Home Depot.
- **Catalog enforced.** `make_lumber("2x5")` raises `ValueError` — there's
  no such lumber. Design rule #3 (simple common dimensions) is automatic.
- **One source of truth for dimensions.** The `LUMBER` dict in `materials.py`
  is the single place dimensions live. The library reads from it.
- **Lazy FreeCAD imports.** The file imports cleanly outside FreeCAD
  (for build calculators, etc.). FreeCAD is only imported when you call a
  function that needs it.
- **Same dimensions as the wind/sun sims.** The wood physics in
  `analysis/wind_load.py` and the panel cuts in `models/freecad/parts/`
  both read from `LUMBER` — no risk of drift.

## Vendor hardware (STEP files)

For hinges, panel clamps, and the linear actuator, the `lumber.py`
library has `load_vendor_part(filename)` that imports a STEP file from
`models/freecad/parts/vendor/`. See `vendor/README.md` for the recommended
files and where to download them.

If a STEP file isn't available, use the parametric helpers
(`make_bolt`, `make_panel_rect`) for a simplified visual representation.
