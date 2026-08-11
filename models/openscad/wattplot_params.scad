// =============================================================================
// wattplot_params.scad -- mirror of wattplot_params.py
// =============================================================================
//
// DO NOT EDIT THESE NUMBERS WITHOUT UPDATING wattplot_params.py AND
// firmware/tests/test_openscad_params.py.
//
// The Python source of truth is wattplot_params.py at the repo root.
// This file is a hand-maintained mirror so the OpenSCAD models can
// render without Python. A CI test (test_openscad_params.py) reads
// both and fails if any number has drifted.
//
// If you change a value here, change it in wattplot_params.py first
// and update the test expectations in test_openscad_params.py. The
// commit message should reference the param name (e.g.
// "scad: bump POSTS.height_in to 78 for v3.1 storm margin").
//
// All dimensions are in inches. OpenSCAD's $fn controls mesh
// resolution -- 64 gives a clean STL that's about 2 MB at this
// model's complexity.

// ---------- LOCATION ----------
location_latitude  = 33.45;     // Phoenix, AZ
location_longitude = -112.07;
location_elevation_m = 337;
location_design_wind_mph = 115.0; // ASCE 7-22, Risk Cat II 700-yr

// ---------- PLANTER LIMITS ----------
max_planter_L_in = 96.0;          // 8 ft stock, no waste on long rails
max_planter_W_in = 60.0;          // 5 ft (8 ft cross-cut, 2 cross-rails per board)

// ---------- BED (planter, ballasted) ----------
bed_outer_L_in       = 96.0;       // 8 ft (capped at max_planter_L_in)
bed_outer_W_in       = 44.6;       // matches panel width
bed_wall_thk_in      = 0.75;       // 1x6 cedar (3/4" actual)
bed_wall_h_in        = 27.5;       // 5 courses of 1x6 (5.5" actual)
                                   //   wind-sized: SF_overturning 2.55 at 35°
bed_soil_fill_in     = 25.5;       // 2" freeboard below the rim
                                   //   ~60 cu ft = 2.2 cu yd = ~4,000 lb
bed_skid_h_in        = 1.5;        // walls rest on 2x4 footers
bed_skid_side_in     = 3.5;        // 4x nominal

// ---------- BED WALL (1x6 cedar skin over 2x4 cleats) ----------
wall_skin_thk_in   = 0.75;
wall_course_h_in   = 5.5;
wall_courses       = 5;            // 5 x 5.5" = 27.5" wall
wall_cleat_thk_in  = 1.5;          // 2x4 actual
wall_cleat_wid_in  = 3.5;          // 2x4 actual
wall_cleats_long   = 5;            // per long wall
wall_cleats_short  = 3;            // per short wall
wall_header_thk_in = 1.5;         // 2x4 on wide face
wall_header_wid_in = 3.5;

// ---------- POSTS (4x4 PT, 72" tall, walk-under canopy) ----------
post_thk_in  = 3.5;               // 4x4 actual
post_height_in = 72.0;            // 6 ft -- walk-under / reach-under
post_count   = 4;
post_rail_thk_in = 1.5;          // 2x6 on post tops
post_rail_wid_in = 5.5;

// ---------- PANEL (LONGi Hi-MO X10 620W default) ----------
panel_L_in        = 97.0;         // 8.08 ft (overhangs bed 0.5"/side)
panel_W_in        = 44.6;         // 3.72 ft
panel_thk_in      = 1.4;
panel_mass_lb     = 65.0;
panel_wattage     = 620;
panel_tilt_deg    = 35.0;         // 0 = flat, 35 = max (wind-limited)

// ---------- CONTROL (tilt cap + PI setpoint) ----------
control_max_tilt_deg  = 35.0;     // STRUCTURAL cap. See ADR-001.
control_target_current_A = 0.5;
control_hard_current_limit_A = 2.5;

// ---------- FRAME (perimeter around the panel) ----------
frame_long_rail_thk_in   = 1.5;    // 2x6 actual
frame_long_rail_wid_in   = 5.5;
frame_long_rail_length_in = 96.0;  // 8 ft stock, no waste

frame_cross_rail_thk_in   = 1.5;   // 2x6 actual
frame_cross_rail_wid_in   = 5.5;
frame_cross_rail_length_in = 42.0; // 2x6x8ft cut to 42"

frame_brace_thk_in   = 1.5;         // 2x4 actual
frame_brace_wid_in   = 3.5;
frame_brace_length_in = 102.0;     // 2x4x10ft cut to 102"

// ---------- HINGES + PANEL CLAMPS ----------
hinge_leaf_in    = 4.0;            // 4"x4" leaf, 1/2" pin
hinge_pin_d_in    = 0.5;
hinge_count      = 4;
hinge_spacing_in = 22.0;           // 22" o.c.
hinge_rod_length_in = 72.0;        // 1/2" x 72" steel rod (HD)

panel_clamp_length_in = 2.0;       // IronRidge mid-clamp, 35mm channel
panel_clamp_height_in = 2.0;
panel_clamp_thk_in   = 0.4;
panel_clamps_per_long_rail  = 2;
panel_clamps_per_cross_rail = 1;

// ---------- ACTUATOR MOUNT ----------
actuator_block_thk_in  = 1.5;      // 2x6 actual
actuator_block_wid_in  = 5.5;
actuator_block_length_in = 6.0;
actuator_stroke_in     = 4.0;       // 12V linear actuator
actuator_width_in      = 2.0;       // body width (for clearance check)
actuator_height_in     = 2.5;

// ---------- DERIVED (don't change) ----------
// Bed is sized so the panel overhangs the rails by 0.5" per side.
// The panel mid-clamps grip the aluminum frame, not the glass.
bed_inner_L_in = bed_outer_L_in - 2 * post_thk_in;
bed_inner_W_in = bed_outer_W_in - 2 * wall_skin_thk_in;
// Wall sits on top of skid; rim = wall + skid.
bed_rim_h_in = bed_wall_h_in + bed_skid_h_in;
// Panel frame offset above the bed rail (clearance for the clamp).
panel_clearance_in = 2.0;         // 2" above the rail top

// Render resolution: $fn controls segment count for curves.
// 64 gives a clean STL ~2 MB. Lower for fast preview, higher for
// 3D printing.
$fn = 64;