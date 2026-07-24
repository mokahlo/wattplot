"""
Wood frame orchestrator — builds the wood structure of a Wattplot planter.

Structure (no hardware, just wood):
  - 4 floor footers (2x4 PT, 1.5" tall × 3.5" wide, laid on wide side)
    jointed at the 4 corners inside the 4x4 corner posts, hidden from
    outside the planter box. The wider 2x4 gives the bottom slats 2.75"
    of bearing per end (vs. 0.75" with the old 2x2 footers).
  - 4 bed walls (1x6 cedar skin + 2x4 cleats) with half-lap-style corners —
    the soil bin. Long walls span between the corner posts; short walls
    span between the corner posts. The 2x6 cap sits on top of each long wall.
  - Bottom slats (1x2 cedar) that span the bed width on top of the footers,
    supporting the mesh + soil ballast. Cedar (not PT) because they're above
    ground; soil sits on top.
  - 4 corner posts (4x4 PT) at the OUTSIDE corners of the bed — the
    panel support. Each post is 3.5"x3.5", extends from the footer top
    (y=0) up past the wall + cap top, and carries the panel.
  - 4 panel rails (2x6 cedar) on top of the posts — the panel rests on
    these. Cedar (not PT) because they're above ground.
  - 1 dummy panel slab on top of the 4 posts — a flat blue rectangle the
    size of the actual panel, used to visualize how the real panel sits
    on the wood structure.

The 4 corner posts replace the old 2x6 perimeter frame. They are at the
4 outside corners of the bed (flush with the bed outer faces) so the
walls fit between them with no recess, and the panel rests on their tops
with no offset.

Excludes hardware by design: no hinges, no mid-clamps, no actuator
mount, no fasteners. The wood is the structure; hardware is layered on
top in separate modules.

Usage in FreeCAD:
    >>> import sys; sys.path.insert(0, "C:/dev/wattplot")
    >>> from models.wood_frame import build_wood_frame
    >>> doc = App.newDocument("WoodFrame")
    >>> wood = build_wood_frame(doc)
    >>> doc.recompute()
"""
import sys
import os
import math

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.dirname(os.path.abspath("models/wood_frame.py"))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import FreeCAD as App
import Part

import wattplot_params as P
from models.freecad.materials import LUMBER
from models.frame_geometry import compute_bed_dimensions


# ---- color helpers ---------------------------------------------------------

# Post (upright) height. Parametric so the user can change the demo.
# 6 ft (72") is the planned demo height — the posts act as the panel support
# and a structural column. Adjust this to suit your build.
POST_H_IN = 72.0  # 6 ft
POST_T = LUMBER["4x4"]["actual_t"]  # 3.5" — 4x4 corner post actual thickness

COLORS = {
    "wood":    (0.55, 0.40, 0.25, 1.0),  # bed walls (skin)
    "skid":    (0.40, 0.28, 0.18, 1.0),  # skids (legacy, unused now)
    "upright": (0.48, 0.55, 0.36, 1.0),  # corner posts — pressure treated (olive)
    "cleat":   (0.62, 0.45, 0.28, 1.0),  # 2x4 cleats (slightly lighter)
    "cap":     (0.48, 0.34, 0.21, 1.0),  # 2x6 cap
    "panel":   (0.10, 0.18, 0.42, 1.0),  # dummy solar panel (dark blue)
    "pt":      (0.48, 0.55, 0.36, 1.0),  # pressure-treated (same as uprights)
}


def set_color(obj, rgba):
    if obj.ViewObject is None:
        return
    try:
        obj.ViewObject.ShapeColor = rgba[:3]
        obj.ViewObject.Transparency = int((1 - rgba[3]) * 100)
    except Exception:
        pass


# ---- core: build the wood parts --------------------------------------------

def _build_bed_walls(doc):
    """Build the 4 bed walls (skin + cleats, with cap on long walls).

    Wall lengths are derived from bed_outer - 2*POST_T so the walls
    fit between the corner posts (see bed_wall.py).
    """
    from models.freecad.parts.bed_wall import (
        make_bed_long_wall, make_bed_short_wall,
    )
    return [
        make_bed_long_wall(doc, "north"),
        make_bed_long_wall(doc, "south"),
        make_bed_short_wall(doc, "west"),
        make_bed_short_wall(doc, "east"),
    ]


def _build_skids(doc):
    """Build the 2 skids (4x4 PT, full bed length). Retained for
    back-compat but no longer called by build_wood_frame — the floor
    joists have replaced the skids at the base."""
    from models.freecad.parts.skid import make_skids
    return [make_skids(doc)]  # already a single compound


def _build_floor_joists(doc, bed_L_in, bed_W_in, post_t_in,
                        joist_nominal="2x4"):
    """Build 4 floor FOOTERS (2x4 PT, laid flat) jointed inside the uprights.

    All 4 footers are 2x4 PT (1.5" tall × 3.5" wide actual) laid on their
    WIDE side — i.e., 1.5" of vertical thickness and 3.5" of horizontal
    width. This is wider than the original 2x2 (which was 1.5" × 1.5")
    and gives the bottom slats much more bearing surface at their ends
    (2.75" of grip per slat end, vs. 0.75" with 2x2 — 3.7x more).

    The footers are jointed at the 4 corners inside the 4x4 corner posts.
    The centerline is 1.75" inside the bed outer dimension, so the
    footer's outer face stays flush with the bed outer (z = ±bed_W/2 for
    long footers, x = ±bed_L/2 for short footers). The 0.75"-thick wall
    covers the outer 0.75" of the footer, hiding it from outside the
    planter box; the inner 2.75" of the footer is the slat-bearing
    surface.

    Footer pairings (per the user):
      1-2: NW→NE (long side, north, along X at z=+(bed_W/2 - 1.75))
      3-4: SW→SE (long side, south, along X at z=-(bed_W/2 - 1.75))
      1-3: NW→SW (short side, west, along Z at x=-(bed_L/2 - 1.75))
      2-4: NE→SE (short side, east, along Z at x=+(bed_L/2 - 1.75))

    All 4 footers extend the full bed length/width (bed_L / bed_W), so
    their ends are 1.75" inside the corner posts. The butt joints at
    the 4 corners are hidden by the posts (the post covers the overlap
    region where long and short footers cross).
    """
    import Part
    from models.freecad.materials import LUMBER

    # 2x4 PT actual dimensions: 1.5" tall × 3.5" wide (laid on wide side).
    # vertical (Y) is the thin dimension; horizontal (perpendicular to
    # length) is the wide dimension. This gives the slats 3.5" of
    # bearing under each end instead of the 1.5" the old 2x2 footers had.
    FOOTER_THICKNESS = LUMBER[joist_nominal]["actual_t"]   # 1.5 (Y)
    FOOTER_WIDTH = LUMBER[joist_nominal]["actual_h"]       # 3.5 (Z or X)

    # Centerline: FOOTER_WIDTH/2 inside the bed outer dimension, so the
    # footer's outer face stays at z = bed_W/2 (flush with the bed outer).
    # The 0.75"-thick wall covers the outer 0.75" of the footer, hiding
    # it from outside; the remaining 2.75" of footer width is the slat
    # bearing surface (slats run along Z between the wall inner faces
    # at z = ±(bed_W/2 - 0.75), so they overhang the footer's inner
    # face by 2.75" — but they're still fully supported across the
    # 3.5"-wide footer zone).
    INSET = FOOTER_WIDTH / 2.0   # 0.75 for 2x2, 1.75 for 2x4
    long_z = bed_W_in / 2.0 - INSET   # 22.3 - 1.75 = 20.55
    short_x = bed_L_in / 2.0 - INSET  # 48 - 1.75 = 46.25

    footers = []

    # Long footers 1-2 (north) and 3-4 (south) — run along X
    for z_edge in (-long_z, +long_z):
        # Box: (X, Y, Z) = (bed_L, thickness, width)
        shape = Part.makeBox(bed_L_in, FOOTER_THICKNESS, FOOTER_WIDTH)
        shape.translate(App.Vector(
            -bed_L_in / 2.0,                  # X: center on bed center
            0,                                 # Y: at the ground (y=0)
            z_edge - FOOTER_WIDTH / 2.0,       # Z: center on z_edge
        ))
        footers.append(shape)

    # Short footers 1-3 (west) and 2-4 (east) — run along Z
    for x_edge in (-short_x, +short_x):
        # Box: (X, Y, Z) = (width, thickness, bed_W)
        shape = Part.makeBox(FOOTER_WIDTH, FOOTER_THICKNESS, bed_W_in)
        shape.translate(App.Vector(
            x_edge - FOOTER_WIDTH / 2.0,      # X: center on x_edge
            0,                                 # Y: at the ground (y=0)
            -bed_W_in / 2.0,                   # Z: center on bed center
        ))
        footers.append(shape)

    footer_objs = []
    names = ["FloorFooter_1_2_North", "FloorFooter_3_4_South",
             "FloorFooter_1_3_West",  "FloorFooter_2_4_East"]
    for name, shape in zip(names, footers):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        footer_objs.append(obj)
    return footer_objs


def _build_bottom_slats(doc, bed_L_in, bed_W_in, skid_h_in, num_slats=7,
                        slat_nominal="1x2"):
    """Build the bottom slats that support the mesh + soil ballast.

    1x2 CEDAR (not PT) slats span the bed width (along Z), spaced evenly
    along the bed length (along X). Cedar because the slats are above
    ground (sit on top of the footers) — soil sits on top of them.
    Hardware cloth is stapled to the slat tops and the soil sits on the
    mesh — soil is the actual ballast.
    """
    from models.freecad.parts.bed_wall import make_bottom_slats as _slats
    return _slats(doc,
                  bed_L_in=bed_L_in, bed_W_in=bed_W_in, skid_h_in=skid_h_in,
                  num_slats=num_slats, slat_nominal=slat_nominal,
                  name_prefix="WoodSlats")


def _build_panel_rails(doc, bed_L_in, bed_W_in, panel_L_in, panel_W_in,
                       post_top_y, rail_nominal="2x6"):
    """Build the 4 panel rails that span the top of the 4 corner posts.

    All 4 rails are 2x6 CEDAR (not PT) laid on their SHORT side
    (1.5" tall, 5.5" wide). Cedar because the rails are above ground
    — the panel rests on them, and they're exposed to weather. Cedar
    is naturally rot-resistant and doesn't need pressure treatment.

    Joist pairings (matching the floor joists):
      1-2: NW→NE (long, along X at z=+bed_W/2)
      3-4: SW→SE (long, along X at z=-bed_W/2)
      2-4: NE→SE (short, along Z at x=+bed_L/2)
      1-3: NW→SW (short, along Z at x=-bed_L/2)

    The long rails 1-2 and 3-4 are centered on the uprights' Z position
    (so the rail's center is on the upright's center line). The short
    rails 2-4 and 1-3 fit between the long rails' X span (so the
    short rail's X range is inside the long rails' X range, with the
    5.5" width tucked against the inner faces of the long rails).
    """
    import Part

    # Laid on short side: 1.5" tall (Y), 5.5" wide (perpendicular to length)
    RAIL_THICKNESS = 1.5   # short side, vertical (Y)
    RAIL_WIDTH = 5.5       # long side, horizontal

    rails = []
    # Long rails 1-2 (north) and 3-4 (south) — run along X
    for z_edge in (-bed_W_in / 2.0, +bed_W_in / 2.0):
        # Box: (X, Y, Z) = (panel_L, thickness, width)
        # Rail length = panel_L so it supports the 0.5" overhang on each end
        shape = Part.makeBox(panel_L_in, RAIL_THICKNESS, RAIL_WIDTH)
        shape.translate(App.Vector(
            -panel_L_in / 2.0,           # X: center on bed center
            post_top_y,                    # Y: at the top of the uprights
            z_edge - RAIL_WIDTH / 2.0,     # Z: centered on the upright
        ))
        rails.append(shape)

    # Short rails 2-4 (east) and 1-3 (west) — run along Z
    for x_edge in (-bed_L_in / 2.0, +bed_L_in / 2.0):
        # Box: (X, Y, Z) = (width, thickness, panel_W)
        # Rail length = panel_W (fits between the long rails' X span)
        shape = Part.makeBox(RAIL_WIDTH, RAIL_THICKNESS, panel_W_in)
        shape.translate(App.Vector(
            x_edge - RAIL_WIDTH / 2.0,    # X: centered on the upright
            post_top_y,                    # Y: at the top of the uprights
            -panel_W_in / 2.0,             # Z: center on bed center
        ))
        rails.append(shape)

    rail_objs = []
    names = ["PanelRail_1_2_North", "PanelRail_3_4_South",
             "PanelRail_2_4_East",  "PanelRail_1_3_West"]
    for name, shape in zip(names, rails):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        rail_objs.append(obj)
    return rail_objs


def _build_corner_posts(doc, bed_L_in, bed_W_in, post_len_in):
    """Build 4 vertical 4x4 PT corner posts at the OUTSIDE corners of the bed.

    Each post is 3.5" x 3.5" x post_len_in. The post's outer X and Z faces
    are flush with the bed's outer X and Z faces (so the post sits in the
    outside corner of the bed). The post extends from y=0 (skid bottom)
    to y = post_len_in (panel support height).
    """
    from models.freecad.parts.lumber import make_lumber

    post_t = LUMBER["4x4"]["actual_t"]  # 3.5

    posts = []
    for sign_x in (-1, +1):
        for sign_z in (-1, +1):
            # Outside corner of the bed at this quadrant
            corner_x = sign_x * bed_L_in / 2.0
            corner_z = sign_z * bed_W_in / 2.0
            # Post's outer faces flush with bed's outer faces.
            # Post extends INWARD from the corner (toward the bed center).
            if sign_x > 0:
                origin_x = corner_x - post_t  # post in X=[corner_x - post_t, corner_x]
            else:
                origin_x = corner_x             # post in X=[corner_x, corner_x + post_t]
            if sign_z > 0:
                origin_z = corner_z - post_t
            else:
                origin_z = corner_z

            post = make_lumber("4x4", length=post_len_in, axis="Y",
                               origin=(origin_x, 0, origin_z))
            post_obj = doc.addObject("Part::Feature",
                                      f"Post_{['west','east'][sign_x > 0]}_"
                                      f"{['south','north'][sign_z > 0]}")
            post_obj.Shape = post
            posts.append(post_obj)

    return posts


def _build_dummy_panel(doc, panel_L_in, panel_W_in, panel_t_in, post_top_y):
    """Build a flat dummy solar panel slab on top of the 4 corner posts.

    Used for visualization — shows how the real panel would sit on the
    wood structure. Colored like a real panel (dark blue).
    """
    panel_box = Part.makeBox(panel_L_in, panel_t_in, panel_W_in)
    # Centered on (0, post_top_y, 0)
    panel_box.translate(App.Vector(-panel_L_in / 2.0,
                                   post_top_y,
                                   -panel_W_in / 2.0))
    panel_obj = doc.addObject("Part::Feature", "DummyPanel")
    panel_obj.Shape = panel_box
    return panel_obj


# ---- the main entry point ---------------------------------------------------

def build_wood_frame(doc=None, name="WoodFrame", group_by_subsystem=True,
                     with_dummy_panel=True):
    """Build the complete wood frame (bed + skids + 4 corner posts + dummy panel).

    The wood skeleton consists of:
      - 4 bed walls (1x6 cedar skin + 2x4 cleats, 2x6 cap on long walls)
      - 2 skids (4x4 PT, full bed length)
      - 4 corner posts (4x4 PT, at the OUTSIDE corners of the bed)
      - 1 dummy solar panel slab (optional, on top of the 4 posts)

    All dimensions are derived from the current wattplot_params state
    (P.BED, P.PANEL), so any panel preset or custom spec works.

    Args:
        doc: FreeCAD document. If None, creates a new one.
        name: name for the top-level Part::Feature.
        group_by_subsystem: if True, creates 3 named groups (Bed, Posts,
            Panel) for clean tree organization.
        with_dummy_panel: if True, include a flat blue panel slab on top
            of the 4 corner posts (for visualization only).

    Returns:
        dict with keys:
            'compound': a single Part::Feature containing all wood parts
            'bed_walls': list of 4 wall Part::Features
            'skids': skid Part::Feature (single compound)
            'posts': list of 4 corner-post Part::Features
            'dummy_panel': dummy panel Part::Feature (or None)
            'groups': dict of group_name -> group (if group_by_subsystem)
            'bed_dims': the bed dimensions used
            'post_top_y': Y position of the top of the corner posts
    """
    if doc is None:
        doc = App.newDocument("Wattplot_WoodFrame")
    doc.recompute()

    bed_L = P.BED["outer_L_in"]
    bed_W = P.BED["outer_W_in"]
    wall_h = P.BED["wall_h_in"]              # 22.0 (1x6 cedar, 4 courses)
    sk_id_h = P.BED["skid_h_in"]              # 3.0
    cap_t = LUMBER["2x6"]["actual_t"]         # 1.5
    # Post (upright) height: parametric, default 6 ft. The post extends
    # from y=0 (skid bottom) to y=POST_H_IN, with the dummy panel sitting
    # on top at y=POST_H_IN.
    post_len = POST_H_IN
    post_top_y = POST_H_IN

    panel_L = P.PANEL["L_in"]
    panel_W = P.PANEL["W_in"]
    panel_t = P.PANEL["thickness_in"]
    panel_wattage = int(P.PANEL["wattage"])

    print(f"[wood] Building wood frame for:")
    print(f"[wood]   Panel: {panel_L}\" x {panel_W}\" ({panel_wattage} W)")
    print(f"[wood]   Bed:   {bed_L}\" x {bed_W}\" "
          f"({bed_L/12:.2f} x {bed_W/12:.2f} ft)")

    bed_dims = compute_bed_dimensions(bed_L, bed_W, skid_h_in=sk_id_h)

    print(f"[wood]   Long walls:    {bed_dims['long_wall_L']:.1f}\"  (between posts, 1x6 cedar)")
    print(f"[wood]   Short walls:   {bed_dims['short_wall_L']:.1f}\"  (between posts, 1x6 cedar)")
    print(f"[wood]   Floor footers: 4 x 2x4 PT on wide side (3.5\" bearing) "
          f"jointed inside the 4 corner posts (hidden)")
    print(f"[wood]   Slats:         7 x 1x2 cedar on top of the footers (mesh support)")
    print(f"[wood]   Corner posts:  4 x 4x4 PT, {post_len:.1f}\" tall "
          f"(at OUTSIDE corners, panel support)")
    if with_dummy_panel:
        print(f"[wood]   Dummy panel:   {panel_L}\" x {panel_W}\" x {panel_t}\" "
              f"(on top of posts, at y={post_top_y:.1f})")

    # Build subsystems
    bed_walls = _build_bed_walls(doc)
    floor_joists = _build_floor_joists(doc, bed_L, bed_W, POST_T)
    posts = _build_corner_posts(doc, bed_L, bed_W, post_len)
    # Slats sit on top of the 1.5"-tall footers (2x4 PT laid on wide side,
    # so the slats get 2.75" of grip under each end instead of 0.75").
    slats = _build_bottom_slats(doc, bed_L, bed_W, 1.5)
    panel_rails = _build_panel_rails(doc, bed_L, bed_W, panel_L, panel_W,
                                     post_top_y)
    dummy_panel = (_build_dummy_panel(doc, panel_L, panel_W, panel_t, post_top_y)
                   if with_dummy_panel else None)

    # Apply colors
    for w in bed_walls:
        set_color(w, COLORS["wood"])
    for j in floor_joists:
        set_color(j, COLORS["pt"])           # PT — ground contact
    for p in posts:
        set_color(p, COLORS["pt"])           # PT — ground contact (uprights)
    for sl in slats:
        set_color(sl, COLORS["wood"])        # cedar — above ground
    for r in panel_rails:
        set_color(r, COLORS["wood"])        # cedar — above ground
    if dummy_panel is not None:
        set_color(dummy_panel, COLORS["panel"])

    # Optional: organize into groups
    groups = {}
    if group_by_subsystem:
        bed_group = doc.addObject("App::DocumentObjectGroup", "Bed")
        bed_group.Label = "Bed (4 walls + 4 floor joists + slats)"
        for w in bed_walls:
            bed_group.addObject(w)
        for j in floor_joists:
            bed_group.addObject(j)
        for sl in slats:
            bed_group.addObject(sl)
        groups["bed"] = bed_group

        post_group = doc.addObject("App::DocumentObjectGroup", "CornerPosts")
        post_group.Label = "Corner posts (4 vertical 4x4 PT)"
        for p in posts:
            post_group.addObject(p)
        groups["posts"] = post_group

        if dummy_panel is not None:
            panel_group = doc.addObject("App::DocumentObjectGroup", "DummyPanel")
            panel_group.Label = "Dummy solar panel (visualization only)"
            panel_group.addObject(dummy_panel)
            groups["panel"] = panel_group

    # Build the unified compound
    all_shapes = ([w.Shape for w in bed_walls] +
                  [j.Shape for j in floor_joists] +
                  [p.Shape for p in posts] +
                  [sl.Shape for sl in slats] +
                  [r.Shape for r in panel_rails])
    if dummy_panel is not None:
        all_shapes.append(dummy_panel.Shape)
    compound = Part.makeCompound(all_shapes)
    compound_obj = doc.addObject("Part::Feature", name)
    compound_obj.Shape = compound
    if compound_obj.ViewObject is not None:
        compound_obj.ViewObject.ShapeColor = (0.50, 0.36, 0.22, 1.0)

    doc.recompute()

    # Wood-only mass (excludes dummy panel — it's not wood, it's a visual)
    wood_shapes = ([w.Shape for w in bed_walls] +
                   [j.Shape for j in floor_joists] +
                   [p.Shape for p in posts] +
                   [sl.Shape for sl in slats] +
                   [r.Shape for r in panel_rails])
    wood_compound = Part.makeCompound(wood_shapes)
    wood_vol = wood_compound.Volume
    wood_mass = wood_vol * 35 / 1728

    parts = (f"{len(bed_walls)} walls + {len(floor_joists)} floor joists + "
             f"{len(posts)} posts")
    n_parts = len(bed_walls) + len(floor_joists) + len(posts)
    if dummy_panel is not None:
        parts += " + 1 dummy panel"
    print(f"[wood] Wood structure: {parts} = {n_parts} wood parts "
          f"(+1 panel if dummy)")
    print(f"[wood] Wood volume: {wood_vol:.1f} in^3 ({wood_vol/1728:.2f} ft^3)")
    print(f"[wood] Wood mass:   {wood_mass:.1f} lb (PT DF, ~35 pcf)")

    return {
        "compound": compound_obj,
        "bed_walls": bed_walls,
        "floor_joists": floor_joists,
        "posts": posts,
        "slats": slats,
        "panel_rails": panel_rails,
        "dummy_panel": dummy_panel,
        "groups": groups,
        "bed_dims": bed_dims,
        "post_top_y": post_top_y,
    }


# ---- geometry verification -------------------------------------------------

def verify_geometry(result, verbose=True):
    """Sanity-check the wood frame geometry."""
    warnings = []
    bed_dims = result["bed_dims"]
    bed_walls = result["bed_walls"]
    posts = result["posts"]
    floor_joists = result.get("floor_joists", [])

    bed_outer_L = bed_dims["long_wall_L"] + 2 * bed_dims["post_t"]
    bed_outer_W = bed_dims["short_wall_L"] + 2 * bed_dims["post_t"]
    post_t = bed_dims["post_t"]

    # Walls should sit at y = skid_h to skid_h + WALL_H
    for wall in bed_walls:
        bb = wall.Shape.BoundBox
        if abs(bb.YMin - bed_dims["skid_h"]) > 0.01:
            warnings.append(f"Wall {wall.Name} Y-min is {bb.YMin:.2f}, "
                            f"expected {bed_dims['skid_h']:.2f}")

    # Floor footers should be at y=0 to y=1.5 (2x4 PT on wide side,
    # 1.5" tall × 3.5" wide), jointed inside the uprights, hidden from
    # outside. Centerline is 1.75" inside the bed outer, so the outer
    # face is flush with the bed outer Z and the 0.75"-thick wall
    # covers the outer 0.75" of the footer. The inner 2.75" of the
    # footer is the slat-bearing surface.
    for joist in floor_joists:
        bb = joist.Shape.BoundBox
        if abs(bb.YMin) > 0.01:
            warnings.append(f"Footer {joist.Name} Y-min is {bb.YMin:.2f}, expected 0")
        if abs(bb.YMax - 1.5) > 0.01:
            warnings.append(f"Footer {joist.Name} Y-max is {bb.YMax:.2f}, "
                            f"expected 1.50")
        # X or Z extent should reach the post centerline (±bed_outer/2)
        extents_ok = (abs(bb.XMin + bed_outer_L/2) < 0.01 or
                      abs(bb.XMax - bed_outer_L/2) < 0.01 or
                      abs(bb.ZMin + bed_outer_W/2) < 0.01 or
                      abs(bb.ZMax - bed_outer_W/2) < 0.01)
        if not extents_ok:
            warnings.append(f"Footer {joist.Name} should reach a post "
                            f"(X or Z at ±bed_outer/2), got "
                            f"X=[{bb.XMin:.2f}, {bb.XMax:.2f}], "
                            f"Z=[{bb.ZMin:.2f}, {bb.ZMax:.2f}]")

    # Posts should be at the OUTSIDE corners of the bed
    # (X = ±bed_outer_L/2, Z = ±bed_outer_W/2)
    expected_post_top = POST_H_IN
    for post in posts:
        bb = post.Shape.BoundBox
        if abs(bb.YMin) > 0.01:
            warnings.append(f"Post {post.Name} Y-min is {bb.YMin:.2f}, expected 0")
        if abs(bb.YMax - expected_post_top) > 0.01:
            warnings.append(f"Post {post.Name} Y-max is {bb.YMax:.2f}, "
                            f"expected {expected_post_top:.2f}")
        # Post's outer X and Z faces must align with the bed outer faces
        outside_x_pos = abs(bb.XMax - bed_outer_L / 2.0) < 0.01
        outside_x_neg = abs(bb.XMin + bed_outer_L / 2.0) < 0.01
        outside_z_pos = abs(bb.ZMax - bed_outer_W / 2.0) < 0.01
        outside_z_neg = abs(bb.ZMin + bed_outer_W / 2.0) < 0.01
        if not (outside_x_pos or outside_x_neg):
            warnings.append(f"Post {post.Name} outer X face not at bed edge: "
                            f"X range [{bb.XMin:.2f}, {bb.XMax:.2f}], "
                            f"bed edge ±{bed_outer_L/2.0:.2f}")
        if not (outside_z_pos or outside_z_neg):
            warnings.append(f"Post {post.Name} outer Z face not at bed edge: "
                            f"Z range [{bb.ZMin:.2f}, {bb.ZMax:.2f}], "
                            f"bed edge ±{bed_outer_W/2.0:.2f}")

    # Dummy panel (if present) should sit on top of the posts
    if result.get("dummy_panel") is not None:
        panel = result["dummy_panel"]
        bb = panel.Shape.BoundBox
        if abs(bb.YMin - expected_post_top) > 0.01:
            warnings.append(f"DummyPanel Y-min is {bb.YMin:.2f}, "
                            f"expected {expected_post_top:.2f} (post top)")

    if verbose:
        if warnings:
            print(f"[verify] {len(warnings)} warning(s):")
            for w in warnings:
                print(f"  - {w}")
        else:
            print(f"[verify] All geometry checks passed.")

    return warnings


# ---- self-test -------------------------------------------------------------

if __name__ == "__main__":
    # Build the entire wood setup piece by piece: bed walls, floor joists,
    # slats, corner posts, and panel rails. Export as wattplot.stl — the
    # viewer adds a procedural solar panel on top of the rails for tilting.
    doc = App.newDocument("Wattplot_Full_Test")
    result = build_wood_frame(doc, with_dummy_panel=False)
    print()
    verify_geometry(result, verbose=True)
    print(f"\nDone. {len(doc.Objects)} top-level objects in doc.")

    stl_path = os.path.join(ROOT, "models", "wattplot.stl")
    try:
        import Mesh
        import MeshPart
        all_shapes = ([w.Shape for w in result["bed_walls"]] +
                      [j.Shape for j in result["floor_joists"]] +
                      [sl.Shape for sl in result["slats"]] +
                      [u.Shape for u in result["posts"]] +
                      [r.Shape for r in result["panel_rails"]])
        compound = Part.makeCompound(all_shapes)
        mesh = MeshPart.meshFromShape(compound,
                                      LinearDeflection=1.0,
                                      AngularDeflection=0.5,
                                      Relative=False)
        mesh.write(stl_path)
        print(f"[wood] Exported wattplot STL: {stl_path} "
              f"({os.path.getsize(stl_path)/1024:.1f} KB)")
    except Exception as e:
        print(f"[wood] STL export failed: {e}")
