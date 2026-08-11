// =============================================================================
// wattplot.scad -- canonical OpenSCAD model of the Wattplot planter
// =============================================================================
//
// The flagship 3D model. Renders the full assembly at the LONGi Hi-MO
// X10 620W preset (the default), 35° panel tilt, in the 'smart'
// tier (with linear actuator and electronic hinge/frame -- basic
// tier just removes the actuator mount + block).
//
// Render:
//   openscad -o wattplot_longi_620W.stl models/openscad/wattplot.scad
//   or `make scad-stl` (see Makefile)
//
// Modify the panel by editing wattplot_params.scad or by passing
// a parameter on the command line:
//   openscad -D 'panel_preset="residential_60cell"' \
//            -o wattplot_60cell.stl models/openscad/wattplot.scad
//
// Architecture:
//   This file is a thin orchestrator. The per-part geometry lives
//   in models/openscad/parts/ (bed, posts, frame, panel, hinges,
//   actuator). Each part is a self-contained .scad file that
//   includes wattplot_params.scad for its dimensions and can be
//   opened directly to render just that part. This file uses
//   the canonical LONGi palette; the per-part files define
//   their own defaults so they can render standalone.
//
// Coordinate system:
//   X = bed length (south -> north)
//   Y = up
//   Z = bed width (east -> west)
// Hinge axis runs along the south wall (low Y of the bed).
// Panel tilts up from the hinge, around the X axis.
//
// All dimensions come from wattplot_params.scad -- edit there
// and the model updates. A CI test verifies Python/SCAD parity.

include <wattplot_params.scad>
use <parts/bed.scad>
use <parts/posts.scad>
use <parts/hinges.scad>
use <parts/panel.scad>
use <parts/frame.scad>
use <parts/actuator.scad>

// ----------------------------------------------------------------------------
// Show / hide flags. Default: everything visible for the booth preview.
// Pass `-D show_soil=false` to hide the soil fill (it's just a
// visual placeholder; the model without soil is the real build
// state).
// ----------------------------------------------------------------------------
show_soil       = true;
show_bed        = true;
show_posts      = true;
show_frame      = true;
show_panel      = true;
show_actuator   = true;
show_hinges     = true;
show_clamps     = true;
show_grid       = false;  // optional 1' grid for scale

// ----------------------------------------------------------------------------
// Canonical palette. The per-part modules define their own
// _default colors; we shadow those here so the assembled view
// uses one consistent palette. To swap a single part's color,
// edit the per-part module's *_default variable.
// ----------------------------------------------------------------------------
col_bed_skin   = [0.78, 0.55, 0.35];   // cedar
col_bed_cleat  = [0.85, 0.65, 0.45];
col_skid       = [0.55, 0.40, 0.30];   // PT DF
col_soil       = [0.40, 0.25, 0.15];   // wet loam
col_post       = [0.70, 0.55, 0.40];
col_frame      = [0.90, 0.90, 0.88];   // 2x6 painted
col_panel      = [0.20, 0.30, 0.55];   // LONGi blue
col_actuator   = [0.40, 0.40, 0.45];
col_hinge      = [0.60, 0.60, 0.65];

// ----------------------------------------------------------------------------
// Optional 1 ft grid for scale (off by default)
// ----------------------------------------------------------------------------
module scale_grid() {
    if (!show_grid) children();
    for (x = [-4:4]) color([0.2, 0.4, 0.2, 0.3]) translate([x*12, 0, 0]) cube([0.1, 0.1, 60]);
    for (z = [-3:3]) color([0.2, 0.4, 0.2, 0.3]) translate([0, 0, z*12]) cube([96, 0.1, 0.1]);
}

// ----------------------------------------------------------------------------
// Assembly. The show_* flags gate the individual part modules.
// ----------------------------------------------------------------------------
scale_grid();
if (show_bed)       bed_assembly(show_soil=show_soil);
if (show_posts)     posts_assembly();
if (show_hinges)    hinges_assembly();
if (show_actuator)  actuator_assembly();
if (show_frame)     frame_assembly(show_clamps=show_clamps);
if (show_panel)     panel_assembly();