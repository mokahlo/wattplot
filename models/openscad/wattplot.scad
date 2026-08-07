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

// Color palette (soft pastels for the booth print, muted for
// the on-screen viewer). OpenSCAD colors are 0-1 floats.
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
// Bed walls: 1x6 cedar skin + 2x4 cleats + 2x4 header.
// Sits on the skids. Walls face inward; skin boards on the
// outside, cleats on the inside, header on top.
// ----------------------------------------------------------------------------
module bed_assembly() {
    if (!show_bed) children();
    
    // The 4 walls: long (N/S) on the X axis, short (E/W) on Z.
    // Y = wall_h_in. Walls are thin (skin_thk) boards.
    // South wall = the hinge side.
    // North wall = the strut / actuator-mount side.
    
    // Long walls (X axis, run the full bed length)
    color(col_bed_skin)
    translate([0, bed_skid_h_in,  bed_outer_W_in/2 - wall_skin_thk_in/2])
        cube([bed_outer_L_in, bed_wall_h_in, wall_skin_thk_in], center=true);
    color(col_bed_skin)
    translate([0, bed_skid_h_in, -bed_outer_W_in/2 + wall_skin_thk_in/2])
        cube([bed_outer_L_in, bed_wall_h_in, wall_skin_thk_in], center=true);
    
    // Short walls (Z axis, between the long walls)
    color(col_bed_skin)
    translate([ bed_outer_L_in/2 - wall_skin_thk_in/2, bed_skid_h_in, 0])
        cube([wall_skin_thk_in, bed_wall_h_in, bed_inner_W_in], center=true);
    color(col_bed_skin)
    translate([-bed_outer_L_in/2 + wall_skin_thk_in/2, bed_skid_h_in, 0])
        cube([wall_skin_thk_in, bed_wall_h_in, bed_inner_W_in], center=true);
    
    // Cleats: vertical 2x4s, evenly spaced (>=24" o.c. per design
    // rule #3). 5 per long wall, 3 per short wall.
    color(col_bed_cleat)
    for (i = [0:wall_cleats_long-1]) {
        x = -bed_outer_L_in/2 + bed_outer_L_in * (i + 0.5) / wall_cleats_long;
        translate([x, bed_skid_h_in,  bed_outer_W_in/2 - wall_skin_thk_in - wall_cleat_wid_in/2])
            cube([wall_cleat_thk_in, bed_wall_h_in, wall_cleat_wid_in], center=true);
        translate([x, bed_skid_h_in, -bed_outer_W_in/2 + wall_skin_thk_in + wall_cleat_wid_in/2])
            cube([wall_cleat_thk_in, bed_wall_h_in, wall_cleat_wid_in], center=true);
    }
    color(col_bed_cleat)
    for (i = [0:wall_cleats_short-1]) {
        z = -bed_outer_W_in/2 + bed_outer_W_in * (i + 0.5) / wall_cleats_short;
        translate([ bed_outer_L_in/2 - wall_skin_thk_in - wall_cleat_wid_in/2, bed_skid_h_in, z])
            cube([wall_cleat_wid_in, bed_wall_h_in, wall_cleat_thk_in], center=true);
        translate([-bed_outer_L_in/2 + wall_skin_thk_in + wall_cleat_wid_in/2, bed_skid_h_in, z])
            cube([wall_cleat_wid_in, bed_wall_h_in, wall_cleat_thk_in], center=true);
    }
    
    // Header: 2x4 cedar on its wide face, on top of every planter wall
    color(col_bed_skin)
    translate([0, bed_rim_h_in,  bed_outer_W_in/2 - wall_skin_thk_in/2])
        cube([bed_outer_L_in, wall_header_thk_in, wall_header_wid_in], center=true);
    color(col_bed_skin)
    translate([0, bed_rim_h_in, -bed_outer_W_in/2 + wall_skin_thk_in/2])
        cube([bed_outer_L_in, wall_header_thk_in, wall_header_wid_in], center=true);
    color(col_bed_skin)
    translate([ bed_outer_L_in/2 - wall_skin_thk_in/2, bed_rim_h_in, 0])
        cube([wall_header_wid_in, wall_header_thk_in, bed_inner_W_in], center=true);
    color(col_bed_skin)
    translate([-bed_outer_L_in/2 + wall_skin_thk_in/2, bed_rim_h_in, 0])
        cube([wall_header_wid_in, wall_header_thk_in, bed_inner_W_in], center=true);
    
    // Skids: 2x4 PT DF laid on wide side, 8 ft long, under the bed
    color(col_skid)
    translate([0, bed_skid_h_in/2,  bed_outer_W_in/4])
        cube([bed_outer_L_in, bed_skid_h_in, bed_skid_side_in], center=true);
    color(col_skid)
    translate([0, bed_skid_h_in/2, -bed_outer_W_in/4])
        cube([bed_outer_L_in, bed_skid_h_in, bed_skid_side_in], center=true);
    
    // Soil fill (visual placeholder -- not structural)
    if (show_soil)
    color(col_soil)
    translate([0, bed_skid_h_in + bed_soil_fill_in/2, 0])
        cube([bed_inner_L_in, bed_soil_fill_in, bed_inner_W_in], center=true);
}

// ----------------------------------------------------------------------------
// Posts: 4x4 PT DF, 6 ft tall, at the four corners of the bed.
// The bed walls fit between the posts (bed_inner_* = bed_outer_*
// minus 2 * post_thk).
// ----------------------------------------------------------------------------
module post(x, z) {
    color(col_post)
    translate([x, bed_rim_h_in + post_height_in/2, z])
        cube([post_thk_in, post_height_in, post_thk_in], center=true);
}

module posts_assembly() {
    if (!show_posts) children();
    // The 4 posts at the bed corners (outside the wall thickness)
    post( bed_outer_L_in/2 - post_thk_in/2,  bed_outer_W_in/2 - post_thk_in/2);
    post( bed_outer_L_in/2 - post_thk_in/2, -bed_outer_W_in/2 + post_thk_in/2);
    post(-bed_outer_L_in/2 + post_thk_in/2,  bed_outer_W_in/2 - post_thk_in/2);
    post(-bed_outer_L_in/2 + post_thk_in/2, -bed_outer_W_in/2 + post_thk_in/2);
    
    // Panel rails: 2x6 PT DF on top of the post tops, parallel to
    // the bed long axis. These carry the panel + frame.
    color(col_frame)
    translate([0, bed_rim_h_in + post_height_in + post_rail_thk_in/2,  bed_outer_W_in/2 - post_rail_wid_in/2])
        cube([bed_outer_L_in, post_rail_thk_in, post_rail_wid_in], center=true);
    color(col_frame)
    translate([0, bed_rim_h_in + post_height_in + post_rail_thk_in/2, -bed_outer_W_in/2 + post_rail_wid_in/2])
        cube([bed_outer_L_in, post_rail_thk_in, post_rail_wid_in], center=true);
}

// ----------------------------------------------------------------------------
// Hinges: 4 galvanized butt hinges (4"x4" leaf) on the south wall,
// spaced 22" o.c., connected by a 1/2" x 72" steel rod. The rod
// is the pivot axis; the frame rotates around it.
// ----------------------------------------------------------------------------
module hinges_assembly() {
    if (!show_hinges) children();
    // Hinge axis Y position: top of the south wall, +1" up for the
    // hinge knuckle. The frame's south rail sits on this.
    hinge_y = bed_rim_h_in + 0.5;
    hinge_z = -bed_outer_W_in/2 + 0.5;  // 0.5" inboard of the wall outer face
    // Hinge leaves (just visual placeholders; the real hinge is
    // a 4"x4"x1/8" steel leaf with a 0.5" knuckle)
    for (i = [0:hinge_count-1]) {
        x = -hinge_spacing_in * (hinge_count-1) / 2 + i * hinge_spacing_in;
        color(col_hinge)
        translate([x, hinge_y, hinge_z])
            cube([hinge_leaf_in, hinge_leaf_in, 0.4], center=true);
    }
    // The 1/2" rod (visualized as a thin cylinder along the hinge axis)
    color(col_hinge)
    translate([0, hinge_y, hinge_z])
        rotate([0, 90, 0])
            cylinder(h=bed_outer_L_in, d=hinge_pin_d_in, center=true);
}

// ----------------------------------------------------------------------------
// Panel: LONGi Hi-MO X10 620W at 35 deg tilt, hinged on the south.
// Tilts around the hinge axis (X axis at Y = bed_rim_h_in + 0.5,
// Z = -bed_outer_W_in/2 + 0.5).
// ----------------------------------------------------------------------------
module panel_assembly() {
    if (!show_panel) children();
    hinge_y = bed_rim_h_in + 0.5;
    hinge_z = -bed_outer_W_in/2 + 0.5;
    // The panel is centered on the hinge axis and rotates around X.
    // Center of panel at tilt = 0 is right above the hinge.
    panel_pivot_x = 0;
    color(col_panel)
    translate([panel_pivot_x, hinge_y, hinge_z])
        rotate([panel_tilt_deg, 0, 0])   // tilt around the X axis
            translate([0, panel_clearance_in + panel_thk_in/2, bed_outer_W_in/2 - panel_W_in/2])
                cube([panel_L_in, panel_thk_in, panel_W_in], center=true);
}

// ----------------------------------------------------------------------------
// Frame: 2x6 perimeter around the panel, plus 2x4 diagonal brace.
// Tilts with the panel. Hinged on the south; the diagonal brace
// carries the load at 90 deg tilt (not used at 35 deg but modeled
// for completeness).
// ----------------------------------------------------------------------------
module frame_assembly() {
    if (!show_frame) children();
    hinge_y = bed_rim_h_in + 0.5;
    hinge_z = -bed_outer_W_in/2 + 0.5;
    panel_pivot_x = 0;
    color(col_frame)
    translate([panel_pivot_x, hinge_y, hinge_z])
        rotate([panel_tilt_deg, 0, 0])
            // Long rails (X axis, panel length)
            translate([0, panel_clearance_in + frame_long_rail_thk_in/2, bed_outer_W_in/2 - frame_long_rail_wid_in/2])
                cube([frame_long_rail_length_in, frame_long_rail_thk_in, frame_long_rail_wid_in], center=true);
            translate([0, panel_clearance_in + frame_long_rail_thk_in/2, -bed_outer_W_in/2 + frame_long_rail_wid_in/2])
                cube([frame_long_rail_length_in, frame_long_rail_thk_in, frame_long_rail_wid_in], center=true);
            // Cross rails (Z axis, between long rails)
            translate([ bed_outer_L_in/2 - frame_cross_rail_length_in/2, panel_clearance_in + frame_cross_rail_thk_in/2, 0])
                cube([frame_cross_rail_length_in, frame_cross_rail_thk_in, frame_cross_rail_wid_in], center=true);
            translate([-bed_outer_L_in/2 + frame_cross_rail_length_in/2, panel_clearance_in + frame_cross_rail_thk_in/2, 0])
                cube([frame_cross_rail_length_in, frame_cross_rail_thk_in, frame_cross_rail_wid_in], center=true);
            // Diagonal brace: 2x4, butts into the long rails
            // (only structural at 90 deg tilt, but always there)
            rotate([0, 0, 45])
                translate([0, panel_clearance_in + frame_brace_thk_in/2, 0])
                    cube([frame_brace_length_in, frame_brace_thk_in, frame_brace_wid_in], center=true);
    
    // Panel clamps: 6 total (2 per long rail + 1 per cross rail)
    if (show_clamps)
    color(col_hinge)
    translate([panel_pivot_x, hinge_y, hinge_z])
        rotate([panel_tilt_deg, 0, 0])
        for (i = [0:panel_clamps_per_long_rail-1]) {
            x = -bed_outer_L_in/4 + i * (bed_outer_L_in / 2) /
                  max(1, panel_clamps_per_long_rail - 1);
            translate([x, panel_clearance_in + panel_thk_in + panel_clamp_height_in/2, bed_outer_W_in/2 - panel_clamp_thk_in/2])
                cube([panel_clamp_length_in, panel_clamp_height_in, panel_clamp_thk_in], center=true);
            translate([x, panel_clearance_in + panel_thk_in + panel_clamp_height_in/2, -bed_outer_W_in/2 + panel_clamp_thk_in/2])
                cube([panel_clamp_length_in, panel_clamp_height_in, panel_clamp_thk_in], center=true);
        }
        for (i = [0:panel_clamps_per_cross_rail-1]) {
            z = 0;
            translate([ bed_outer_L_in/2 - panel_clamp_thk_in/2, panel_clearance_in + panel_thk_in + panel_clamp_height_in/2, z])
                cube([panel_clamp_thk_in, panel_clamp_height_in, panel_clamp_length_in], center=true);
            translate([-bed_outer_L_in/2 + panel_clamp_thk_in/2, panel_clearance_in + panel_thk_in + panel_clamp_height_in/2, z])
                cube([panel_clamp_thk_in, panel_clamp_height_in, panel_clamp_length_in], center=true);
        }
}

// ----------------------------------------------------------------------------
// Linear actuator: 12V, 4" stroke, 330 lb. Mounted between the bed's
// north wall (clevis block) and the frame's north rail (clevis
// block). Tilts with the frame on the rail side; fixed on the bed
// side.
// ----------------------------------------------------------------------------
module actuator_assembly() {
    if (!show_actuator) children();
    hinge_y = bed_rim_h_in + 0.5;
    hinge_z = -bed_outer_W_in/2 + 0.5;
    panel_pivot_x = 0;
    // Clevis block on the bed's north wall (fixed -- doesn't tilt)
    color(col_actuator)
    translate([0, bed_rim_h_in + 1.0, bed_outer_W_in/2 - wall_skin_thk_in - actuator_block_wid_in/2])
        cube([actuator_block_length_in, actuator_block_thk_in, actuator_block_wid_in], center=true);
    // Clevis block on the frame's north rail (moves with the frame)
    color(col_actuator)
    translate([panel_pivot_x, hinge_y, hinge_z])
        rotate([panel_tilt_deg, 0, 0])
        translate([0, panel_clearance_in + 1.0, -bed_outer_W_in/2 + actuator_block_wid_in/2])
            cube([actuator_block_length_in, actuator_block_thk_in, actuator_block_wid_in], center=true);
    // The actuator body itself: visualized as a cylinder between
    // the two clevis blocks. Real actuator is a 12V worm-drive
    // unit; we model it as a cylinder for visual scale only.
    // Position the cylinder mid-stroke; an accurate 3D model
    // would be parametric on stroke position.
    color(col_actuator)
    translate([0, bed_rim_h_in + 1.0 + 1.5, bed_outer_W_in/2 - wall_skin_thk_in - actuator_block_wid_in/2 - 0.5])
        rotate([0, 0, 90])
            cylinder(h=actuator_stroke_in, d=1.0, center=true);
}

// ----------------------------------------------------------------------------
// Optional 1 ft grid for scale (off by default)
// ----------------------------------------------------------------------------
module scale_grid() {
    if (!show_grid) children();
    for (x = [-4:4]) color([0.2, 0.4, 0.2, 0.3]) translate([x*12, 0, 0]) cube([0.1, 0.1, 60]);
    for (z = [-3:3]) color([0.2, 0.4, 0.2, 0.3]) translate([0, 0, z*12]) cube([96, 0.1, 0.1]);
}

// ----------------------------------------------------------------------------
// Assembly
// ----------------------------------------------------------------------------
scale_grid();
bed_assembly();
posts_assembly();
hinges_assembly();
actuator_assembly();
frame_assembly();
panel_assembly();