// presets/large_format_1m65.scad -- 1.65m panels common in EU/Asia (e.g. REC Alpha 400)

include <../wattplot_params.scad>
panel_L_in     = 65.0;
panel_W_in     = 41.0;
panel_wattage  = 400;

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