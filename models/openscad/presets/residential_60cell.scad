// presets/residential_60cell.scad -- common 2007-2015 salvage (e.g. Kyocera KD215, Sanyo HIT)

include <../wattplot_params.scad>
panel_L_in     = 65.0;
panel_W_in     = 39.0;
panel_wattage  = 250;

use <../wattplot.scad>

if (is_undef($use_only)) {
    $fn = 64;
    bed_assembly();
    posts_assembly();
    hinges_assembly();
    actuator_assembly();
    frame_assembly();
    panel_assembly();
}