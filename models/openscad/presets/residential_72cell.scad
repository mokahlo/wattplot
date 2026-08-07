// presets/residential_72cell.scad -- common 2012-2018 salvage (e.g. Canadian Solar CS6K-300)

include <../wattplot_params.scad>
panel_L_in     = 77.0;
panel_W_in     = 39.0;
panel_wattage  = 300;

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