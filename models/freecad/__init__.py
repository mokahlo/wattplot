"""Wattplot v2 — FreeCAD parametric model.

Each part lives in its own file under `parts/`. The master assembly is in
`assemble.py` and is run with `freecadcmd` (headless FreeCAD).

Coordinate system (matches wattplot_v2_model.py):
    +X = east  (long axis of bed, 8 ft)
    +Y = up    (0 at grade)
    +Z = south (wind direction in worst-case load)
"""
