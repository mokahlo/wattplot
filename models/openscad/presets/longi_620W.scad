// presets/longi_620W.scad -- LONGi Hi-MO X10 620W bifacial (default preset)
//
// OpenSCAD doesn't have a config-file equivalent, so the preset
// parameters are passed via -D on the command line. This file
// is a one-liner: include the canonical model + the panel dims.
//
// Render:
//   openscad -o wattplot_longi_620W.stl presets/longi_620W.scad
//   or: make scad-stl
//
// The Makefile's per-preset dimension table is the canonical
// source for these numbers -- update BOTH wattplot_params.py AND
// the Makefile when you add a new preset.

include <../wattplot_params.scad>
panel_L_in     = 97.0;
panel_W_in     = 44.6;
panel_wattage  = 620;

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