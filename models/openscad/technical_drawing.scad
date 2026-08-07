// =============================================================================
// technical_drawing.scad -- 2D technical drawings for the docs site
// =============================================================================
//
// Renders orthographic projections of the canonical Wattplot assembly
// at three view angles. Includes engineering-drawing dimension lines
// (lengths, heights, the panel tilt angle) via the _dimensions
// helper module. Exports to PNG for the docs engineering section.
//
// Outputs:
//   docs/renders/wattplot_top_view.png
//   docs/renders/wattplot_side_view.png
//   docs/renders/wattplot_front_view.png
//
// Render:
//   make scad-tech-drawings
//   or (from the repo root):
//     openscad --camera=0,20,0,0,0,0,200 \
//       --projection=o --imgsize=2000,1500 \
//       -o out_top.png models/openscad/technical_drawing.scad
//     openscad --camera=0,0,-20,0,0,90,200 \
//       --projection=o --imgsize=2000,1500 \
//       -o out_side.png models/openscad/technical_drawing.scad
//     openscad --camera=20,0,0,0,90,0,200 \
//       --projection=o --imgsize=2000,1500 \
//       -o out_front.png models/openscad/technical_drawing.scad
//
// The dim lines reference the same numbers as wattplot_params.scad
// (mirror of wattplot_params.py), so the CI parity test catches
// drift between this drawing and the underlying model.

include <wattplot_params.scad>
include <_dimensions.scad>
use <parts/bed.scad>
use <parts/posts.scad>
use <parts/hinges.scad>
use <parts/panel.scad>
use <parts/frame.scad>
use <parts/actuator.scad>

col_bed_skin   = [0.78, 0.55, 0.35];
col_bed_cleat  = [0.85, 0.65, 0.45];
col_skid       = [0.55, 0.40, 0.30];
col_soil       = [0.40, 0.25, 0.15];
col_post       = [0.70, 0.55, 0.40];
col_frame      = [0.90, 0.90, 0.88];
col_panel      = [0.20, 0.30, 0.55];
col_actuator   = [0.40, 0.40, 0.45];
col_hinge      = [0.60, 0.60, 0.65];

$fn = 32;  // smaller $fn for tech drawings (faster, less detail)

// ----------------------------------------------------------------------------
// Compose the assembly, project to 2D, and add dimension lines.
//
// Each function below handles one view. The view is selected by the
// --camera flag at render time, NOT by an internal flag -- that
// way one .scad file handles all three views.
// ----------------------------------------------------------------------------

module side_view_dimensions() {
    // Side view from -Z (south). X = bed length, Y = up.
    // The assembly is at Y = 0 (skid bottom) to Y = ~10' (panel top).
    // We add the dim lines on the EAST side (positive X margin)
    // so they don't overlap the model.

    // Total bed length (96" at 8 ft stock)
    dim_horizontal(
        x_start = -bed_outer_L_in/2,
        x_end   =  bed_outer_L_in/2,
        y_feat  = 0,             // ground level
        label   = str(bed_outer_L_in) + "in",
    );

    // Bed height (from ground to top of bed wall = rim)
    // The bed wall goes from y=skid_h (1.5) to y=skid_h+wall_h (29)
    // Plus the hinge on top adds another 0.5; the bed rim is at
    // bed_rim_h_in (29). We dim from the ground to bed_rim_h.
    dim_vertical(
        x_feat  = -bed_outer_L_in/2,
        y_start = 0,
        y_end   = bed_rim_h_in,
        label   = str(bed_rim_h_in) + "in",
    );

    // Post height (above the bed rim, 72" from rim to post top)
    dim_vertical(
        x_feat  = -bed_outer_L_in/2 + post_thk_in + 1,  // just inside the post
        y_start = bed_rim_h_in,
        y_end   = bed_rim_h_in + post_height_in,
        label   = str(post_height_in) + "in",
    );

    // Panel tilt angle: 35° arc at the hinge axis
    hinge_x = -bed_outer_L_in/2 + 1.5;  // near the south-west corner
    hinge_y = bed_rim_h_in + 0.5;
    r = 6.0;  // 6" radius arc
    // Arc from 0 (horizontal) to 35 (panel tilt)
    dim_angle_arc(hinge_x, hinge_y, r, 0, 35);
    // Label the angle
    color([0, 0, 0])
    translate([hinge_x + r * cos(17.5) - 0.6, hinge_y + r * sin(17.5) + 0.1, 0])
    text("35°", size=0.6, halign="right", valign="bottom");
}

module top_view_dimensions() {
    // Top view from +Y. X = bed length, Z = bed width.
    // The Z axis becomes Y in the 2D image (we rotate the model).

    // Bed length (X axis)
    dim_horizontal(
        x_start = -bed_outer_L_in/2,
        x_end   =  bed_outer_L_in/2,
        y_feat  =  bed_outer_W_in/2,   // north edge of bed
        label   = str(bed_outer_L_in) + "in",
    );

    // Bed width (Z axis; in the rotated view, this is Y)
    dim_vertical(
        x_feat  = bed_outer_L_in/2,    // east edge of bed
        y_start = -bed_outer_W_in/2,
        y_end   =  bed_outer_W_in/2,
        label   = str(bed_outer_W_in) + "in",
    );
}

module front_view_dimensions() {
    // Front view from +X. Z = bed width, Y = up.
    // Bed is 44.6" wide.

    // Bed width
    dim_horizontal(
        x_start = -bed_outer_W_in/2,
        x_end   =  bed_outer_W_in/2,
        y_feat  = 0,                  // ground
        label   = str(bed_outer_W_in) + "in",
    );

    // Bed height (from ground to top of bed wall)
    dim_vertical(
        x_feat  = -bed_outer_W_in/2,
        y_start = 0,
        y_end   = bed_rim_h_in,
        label   = str(bed_rim_h_in) + "in",
    );
}

// ----------------------------------------------------------------------------
// Top view: look down (rotate to put XZ plane as the image plane).
// ----------------------------------------------------------------------------
translate([0, 0, 0])
    rotate([-90, 0, 0])  // +Y becomes -Z in the image
    {
        bed_assembly();
        posts_assembly();
        hinges_assembly();
        actuator_assembly();
        frame_assembly();
        panel_assembly();
    }
    top_view_dimensions();

// ----------------------------------------------------------------------------
// Side view: look from -Z (south).
// ----------------------------------------------------------------------------
rotate([0, 90, 0])
{
    bed_assembly();
    posts_assembly();
    hinges_assembly();
    actuator_assembly();
    frame_assembly();
    panel_assembly();
}
side_view_dimensions();

// ----------------------------------------------------------------------------
// Front view: look from +X (east).
// ----------------------------------------------------------------------------
rotate([0, -90, 0])
    rotate([-90, 0, 0])
{
    bed_assembly();
    posts_assembly();
    hinges_assembly();
    actuator_assembly();
    frame_assembly();
    panel_assembly();
}
front_view_dimensions();