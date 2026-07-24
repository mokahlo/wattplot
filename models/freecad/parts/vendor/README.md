# Vendor 3D Models (STEP files)

This directory holds STEP files for off-the-shelf hardware that
Wattplot uses. The FreeCAD model imports these via
`lumber.load_vendor_part(filename)` for accurate visual representation
and collision-checking.

## Recommended files

| Filename | What it is | Where to get it |
|---|---|---|
| `butt_hinge_4x4.step` | 4×4" galvanized butt hinge, ½" pin | McMaster-Carr 1529A14, or National Hardware N264-456 |
| `mid_clamp_ironridge.step` | IronRidge / Unirac 35mm mid-clamp | IronRidge.com product page → "Resources" → STEP |
| `actuator_eco_worthy.step` | ECO-WORTHY 100mm 12V linear actuator | ECO-WORTHY.com or Amazon listing (request from seller) |
| `actuator_eco_worthy_4in.step` | ECO-WORTHY 4" stroke 330 lbf | Same as above |
| `panel_longi_620W.step` | LONGi Hi-MO X10 620W bifacial | LONGi product page (sometimes available, otherwise use a generic 970×446×35 box) |

## How to import in a part file

```python
from models.freecad.parts.lumber import load_vendor_part

# Loads and returns a Part.Shape
hinge = load_vendor_part("butt_hinge_4x4.step")
hinge.translate(App.Vector(0, 0, 0))   # position it
hinge.rotate(...)                       # orient it
# Then add to doc, fuse with other parts, etc.
```

## Where to find STEP files

- **McMaster-Carr** (mcmaster.com): every product has a STEP download.
  Free, no account needed.
- **IronRidge / Unirac / Quick Mount**: product page → Resources tab.
  Free, may require a "professional account."
- **TraceParts** (traceparts.com): 100M+ parts across all vendors.
  Free account.
- **GrabCAD** (grabcad.com): user-uploaded, mixed quality, free.
- **3DContentCentral** (3dcontentcentral.com): user-uploaded, free.
- **Manufacturer sites**: LONGi, REC, Canadian Solar, etc.
  Quality varies; sometimes only a PDF drawing.

## If you can't find a STEP file

Use a `make_*()` function in `lumber.py`:
- `make_bolt(diameter, length)` for a parametric hex bolt
- `make_panel_rect(L, W, thickness)` for a flat panel
- `make_lumber("2x6", length=42)` for dimensional lumber

These are simplified (no thread detail, no rounded edges) but
correct for layout and collision-checking.

## File hygiene

- Keep the original vendor filename in the STEP file (FreeCAD preserves it)
- Don't modify the STEP file (loses the link to the vendor's drawing)
- If a vendor updates a part, re-download and overwrite; the import
  code should still work
- If the file is large (>10 MB), consider compressing with `gzip` and
  using `Part.Shape.read` with the appropriate reader

## License notes

Vendor STEP files typically have permissive licenses (most are MIT or
BSD for the geometry, though the part itself is the vendor's
intellectual property). Don't redistribute without checking the
license. For Wattplot, the STEP files in this directory are for
personal/educational use; the project's MIT license doesn't extend
to vendor parts.
