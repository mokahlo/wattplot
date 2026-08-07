// =============================================================================
// parts/actuator.scad -- the linear actuator + 2 clevis blocks
// =============================================================================
//
// 12V, 4" stroke, 330 lb. Mounted between the bed's north wall (clevis
// block) and the frame's north rail (clevis block). Tilts with the
// frame on the rail side; fixed on the bed side.

include <../wattplot_params.scad>

module actuator_assembly() {
    hinge_y = bed_rim_h_in + 0.5;
    hinge_z = -bed_outer_W_in/2 + 0.5;
    panel_pivot_x = 0;
    // Clevis block on the bed's north wall (fixed -- doesn't tilt)
    color(col_actuator_default)
    translate([0, bed_rim_h_in + 1.0, bed_outer_W_in/2 - wall_skin_thk_in - actuator_block_wid_in/2])
        cube([actuator_block_length_in, actuator_block_thk_in, actuator_block_wid_in], center=true);
    // Clevis block on the frame's north rail (moves with the frame)
    color(col_actuator_default)
    translate([panel_pivot_x, hinge_y, hinge_z])
        rotate([panel_tilt_deg, 0, 0])
        translate([0, panel_clearance_in + 1.0, -bed_outer_W_in/2 + actuator_block_wid_in/2])
            cube([actuator_block_length_in, actuator_block_thk_in, actuator_block_wid_in], center=true);
    // The actuator body itself: visualized as a cylinder between
    // the two clevis blocks. Real actuator is a 12V worm-drive
    // unit; we model it as a cylinder for visual scale only.
    color(col_actuator_default)
    translate([0, bed_rim_h_in + 1.0 + 1.5, bed_outer_W_in/2 - wall_skin_thk_in - actuator_block_wid_in/2 - 0.5])
        rotate([0, 0, 90])
            cylinder(h=actuator_stroke_in, d=1.0, center=true);
}

col_actuator_default = [0.40, 0.40, 0.45];

if (is_undef($use_only)) {
    $fn = 64;
    actuator_assembly();
}