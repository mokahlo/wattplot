// =============================================================================
// parts/frame.scad -- 2x6 perimeter around the panel + 2x4 diagonal brace + 6 clamps
// =============================================================================
//
// Tilts with the panel. Hinged on the south; the diagonal brace carries
// the load at 90 deg tilt (not used at 35 deg but modeled for
// completeness). The 6 aluminum mid-clamps grip the panel frame.

include <../wattplot_params.scad>

module frame_assembly(show_clamps=true) {
    hinge_y = bed_rim_h_in + 0.5;
    hinge_z = -bed_outer_W_in/2 + 0.5;
    panel_pivot_x = 0;
    color(col_frame_default)
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
    
    if (show_clamps)
    color(col_hinge_default)
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

col_frame_default = [0.90, 0.90, 0.88];
col_hinge_default = [0.60, 0.60, 0.65];

if (is_undef($use_only)) {
    $fn = 64;
    frame_assembly();
}