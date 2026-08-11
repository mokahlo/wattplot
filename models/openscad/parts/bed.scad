// =============================================================================
// parts/bed.scad -- the planter bed (walls + cleats + header + skids + soil)
// =============================================================================
//
// Self-contained part module. Include wattplot_params.scad for the
// dimensions; render with `use <bed.scad>` to compose into an
// assembly. Color and visibility gates are passed in by the parent
// (wattplot.scad).
//
// Coordinate system (matches the canonical model):
//   X = bed length (south -> north)
//   Y = up
//   Z = bed width (east -> west)

include <../wattplot_params.scad>

module bed_assembly(show_soil=true) {
    // The 4 walls: long (N/S) on the X axis, short (E/W) on Z.
    // Y = wall_h_in. Walls are thin (skin_thk) boards.
    // South wall = the hinge side.
    // North wall = the strut / actuator-mount side.
    
    // Long walls (X axis, run the full bed length)
    color(col_bed_skin_default)
    translate([0, bed_skid_h_in,  bed_outer_W_in/2 - wall_skin_thk_in/2])
        cube([bed_outer_L_in, bed_wall_h_in, wall_skin_thk_in], center=true);
    color(col_bed_skin_default)
    translate([0, bed_skid_h_in, -bed_outer_W_in/2 + wall_skin_thk_in/2])
        cube([bed_outer_L_in, bed_wall_h_in, wall_skin_thk_in], center=true);
    
    // Short walls (Z axis, between the long walls)
    color(col_bed_skin_default)
    translate([ bed_outer_L_in/2 - wall_skin_thk_in/2, bed_skid_h_in, 0])
        cube([wall_skin_thk_in, bed_wall_h_in, bed_inner_W_in], center=true);
    color(col_bed_skin_default)
    translate([-bed_outer_L_in/2 + wall_skin_thk_in/2, bed_skid_h_in, 0])
        cube([wall_skin_thk_in, bed_wall_h_in, bed_inner_W_in], center=true);
    
    // Cleats: vertical 2x4s, evenly spaced (>=24" o.c. per design
    // rule #3). 5 per long wall, 3 per short wall.
    color(col_bed_cleat_default)
    for (i = [0:wall_cleats_long-1]) {
        x = -bed_outer_L_in/2 + bed_outer_L_in * (i + 0.5) / wall_cleats_long;
        translate([x, bed_skid_h_in,  bed_outer_W_in/2 - wall_skin_thk_in - wall_cleat_wid_in/2])
            cube([wall_cleat_thk_in, bed_wall_h_in, wall_cleat_wid_in], center=true);
        translate([x, bed_skid_h_in, -bed_outer_W_in/2 + wall_skin_thk_in + wall_cleat_wid_in/2])
            cube([wall_cleat_thk_in, bed_wall_h_in, wall_cleat_wid_in], center=true);
    }
    color(col_bed_cleat_default)
    for (i = [0:wall_cleats_short-1]) {
        z = -bed_outer_W_in/2 + bed_outer_W_in * (i + 0.5) / wall_cleats_short;
        translate([ bed_outer_L_in/2 - wall_skin_thk_in - wall_cleat_wid_in/2, bed_skid_h_in, z])
            cube([wall_cleat_wid_in, bed_wall_h_in, wall_cleat_thk_in], center=true);
        translate([-bed_outer_L_in/2 + wall_skin_thk_in + wall_cleat_wid_in/2, bed_skid_h_in, z])
            cube([wall_cleat_wid_in, bed_wall_h_in, wall_cleat_thk_in], center=true);
    }
    
    // Header: 2x4 cedar on its wide face, on top of every planter wall
    color(col_bed_skin_default)
    translate([0, bed_rim_h_in,  bed_outer_W_in/2 - wall_skin_thk_in/2])
        cube([bed_outer_L_in, wall_header_thk_in, wall_header_wid_in], center=true);
    color(col_bed_skin_default)
    translate([0, bed_rim_h_in, -bed_outer_W_in/2 + wall_skin_thk_in/2])
        cube([bed_outer_L_in, wall_header_thk_in, wall_header_wid_in], center=true);
    color(col_bed_skin_default)
    translate([ bed_outer_L_in/2 - wall_skin_thk_in/2, bed_rim_h_in, 0])
        cube([wall_header_wid_in, wall_header_thk_in, bed_inner_W_in], center=true);
    color(col_bed_skin_default)
    translate([-bed_outer_L_in/2 + wall_skin_thk_in/2, bed_rim_h_in, 0])
        cube([wall_header_wid_in, wall_header_thk_in, bed_inner_W_in], center=true);
    
    // Skids: 2x4 PT DF laid on wide side, 8 ft long, under the bed
    color(col_skid_default)
    translate([0, bed_skid_h_in/2,  bed_outer_W_in/4])
        cube([bed_outer_L_in, bed_skid_h_in, bed_skid_side_in], center=true);
    color(col_skid_default)
    translate([0, bed_skid_h_in/2, -bed_outer_W_in/4])
        cube([bed_outer_L_in, bed_skid_h_in, bed_skid_side_in], center=true);
    
    // Soil fill (visual placeholder -- not structural)
    if (show_soil)
    color(col_soil_default)
    translate([0, bed_skid_h_in + bed_soil_fill_in/2, 0])
        cube([bed_inner_L_in, bed_soil_fill_in, bed_inner_W_in], center=true);
}

// Default colors for standalone use. The canonical wattplot.scad
// overrides these with its own palette.
col_bed_skin_default = [0.78, 0.55, 0.35];   // cedar
col_bed_cleat_default = [0.85, 0.65, 0.45];
col_skid_default       = [0.55, 0.40, 0.30];   // PT DF
col_soil_default       = [0.40, 0.25, 0.15];   // wet loam

// Render the bed alone when this file is opened directly. The
// if/else avoids a recursive render when used via `use <bed.scad>`.
if (is_undef($use_only)) {
    $fn = 64;
    bed_assembly();
}