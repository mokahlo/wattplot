// =============================================================================
// parts/posts.scad -- the 4 corner posts + the 2 panel rails on top
// =============================================================================

include <../wattplot_params.scad>

module posts_assembly() {
    // The 4 posts at the bed corners (outside the wall thickness)
    color(col_post_default)
    post( bed_outer_L_in/2 - post_thk_in/2,  bed_outer_W_in/2 - post_thk_in/2);
    color(col_post_default)
    post( bed_outer_L_in/2 - post_thk_in/2, -bed_outer_W_in/2 + post_thk_in/2);
    color(col_post_default)
    post(-bed_outer_L_in/2 + post_thk_in/2,  bed_outer_W_in/2 - post_thk_in/2);
    color(col_post_default)
    post(-bed_outer_L_in/2 + post_thk_in/2, -bed_outer_W_in/2 + post_thk_in/2);
    
    // Panel rails: 2x6 PT DF on top of the post tops, parallel to
    // the bed long axis. These carry the panel + frame.
    color(col_frame_default)
    translate([0, bed_rim_h_in + post_height_in + post_rail_thk_in/2,  bed_outer_W_in/2 - post_rail_wid_in/2])
        cube([bed_outer_L_in, post_rail_thk_in, post_rail_wid_in], center=true);
    color(col_frame_default)
    translate([0, bed_rim_h_in + post_height_in + post_rail_thk_in/2, -bed_outer_W_in/2 + post_rail_wid_in/2])
        cube([bed_outer_L_in, post_rail_thk_in, post_rail_wid_in], center=true);
}

// Single-post helper. Use posts_assembly() for the full set.
module post(x, z) {
    color(col_post_default)
    translate([x, bed_rim_h_in + post_height_in/2, z])
        cube([post_thk_in, post_height_in, post_thk_in], center=true);
}

col_post_default  = [0.70, 0.55, 0.40];
col_frame_default = [0.90, 0.90, 0.88];   // 2x6 painted

if (is_undef($use_only)) {
    $fn = 64;
    posts_assembly();
}