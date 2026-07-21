"""Quick smoke test for bed_wall part. Run with:
  freecadcmd models/freecad/parts/_test.py
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import FreeCAD as App
from models.freecad.parts import bed_wall as bw

doc = App.newDocument("test_bed_walls")
n = bw.make_bed_long_wall(doc, "north")
s = bw.make_bed_long_wall(doc, "south")
w = bw.make_bed_short_wall(doc, "west")
e = bw.make_bed_short_wall(doc, "east")
doc.recompute()
for o in (n, s, w, e):
    print(f"  {o.Name}: vol = {o.Shape.Volume:.2f} in^3, "
          f"bbox X=[{o.Shape.BoundBox.XMin:.2f}, {o.Shape.BoundBox.XMax:.2f}] "
          f"Y=[{o.Shape.BoundBox.YMin:.2f}, {o.Shape.BoundBox.YMax:.2f}] "
          f"Z=[{o.Shape.BoundBox.ZMin:.2f}, {o.Shape.BoundBox.ZMax:.2f}]")
total = sum(o.Shape.Volume for o in (n, s, w, e))
print(f"  Total bed wood volume: {total:.2f} in^3 (~{total/12:.1f} bf)")
