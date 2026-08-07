// =============================================================================
// parts/hinges.scad -- the 4 butt hinges + 1/2" steel rod (the pivot axis)
// =============================================================================

include <../wattplot_params.scad>

module hinges_assembly() {
    // Hinge axis Y position: top of the south wall, +1" up for the
    // hinge knuckle. The frame's south rail sits on this.
    hinge_y = bed_rim_h_in + 0.5;
    hinge_z = -bed_outer_W_in/2 + 0.5;  // 0.5" inboard of the wall outer face
    // Hinge leaves (just visual placeholders; the real hinge is
    // a 4"x4"x1/8" steel leaf with a 0.5" knuckle)
    for (i = [0:hinge_count-1]) {
        x = -hinge_spacing_in * (hinge_count-1) / 2 + i * hinge_spacing_in;
        color(col_hinge_default)
        translate([x, hinge_y, hinge_z])
            cube([hinge_leaf_in, hinge_leaf_in, 0.4], center=true);
    }
    // The 1/2" rod (visualized as a thin cylinder along the hinge axis)
    color(col_hinge_default)
    translate([0, hinge_y, hinge_z])
        rotate([0, 90, 0])
            cylinder(h=bed_outer_L_in, d=hinge_pin_d_in, center=true);
}

col_hinge_default = [0.60, 0.60, 0.65];

if (is_undef($use_only)) {
    $fn = 64;
    hinges_assembly();
}