// =============================================================================
// parts/panel.scad -- the LONGi Hi-MO X10 620W (or any other preset)
// =============================================================================
//
// Tilts around the hinge axis (X axis at Y = bed_rim_h_in + 0.5,
// Z = -bed_outer_W_in/2 + 0.5).

include <../wattplot_params.scad>

module panel_assembly() {
    hinge_y = bed_rim_h_in + 0.5;
    hinge_z = -bed_outer_W_in/2 + 0.5;
    panel_pivot_x = 0;
    color(col_panel_default)
    translate([panel_pivot_x, hinge_y, hinge_z])
        rotate([panel_tilt_deg, 0, 0])   // tilt around the X axis
            translate([0, panel_clearance_in + panel_thk_in/2, bed_outer_W_in/2 - panel_W_in/2])
                cube([panel_L_in, panel_thk_in, panel_W_in], center=true);
}

col_panel_default = [0.20, 0.30, 0.55];   // LONGi blue

if (is_undef($use_only)) {
    $fn = 64;
    panel_assembly();
}