"""
Wattplot v2 - Single source of truth for all parameters.

Both the 3D model (models/wattplot_v2_model.py) and the simulation
(analysis/sun_simulator.py) read from this file. Change a value here
and both update.

Units: inches throughout (imperial, for US yard / lumber compatibility).
        Tilt angles in degrees.
        Time in hours from midnight (0-24) for daily computations.
"""

# =============================================================================
# LOCATION
# =============================================================================
LOCATION = {
    "name": "Phoenix, AZ",
    "latitude": 33.45,
    "longitude": -112.07,
    "elevation_m": 337,
    "timezone": "America/Phoenix",
    "design_wind_speed_mph": 115.0,    # ASCE 7-22, Risk Cat II 700-yr
    "design_wind_exposure": "C",
    "soil_bearing_psf": 1500,           # Phoenix desert soil, typical
}

# =============================================================================
# PLANTER LIMITS - single-planter max is set by lumber stocking length
# =============================================================================
# A single Wattplot planter is bounded by what you can build from 8-ft
# lumber stock with reasonable waste:
#
#   - 8 ft long direction: long rails = 8 ft, zero waste. Anything longer
#     jumps to 10-ft or 12-ft stock, which costs more and is harder to
#     transport.
#   - 5 ft cross direction: two cross-rails cut from one 8-ft board with
#     6-12" waste. Comfortable single-person build width. Two adult
#     gardeners can work side by side.
#
# Chain multiple planters in a row for larger arrays. A single planter
# is the spec.
MAX_PLANTER_L_IN = 96.0   # 8 ft (8-ft lumber, no waste on long rails)
MAX_PLANTER_W_IN = 60.0   # 5 ft (8-ft cross-cut, 2 cross-rails per board)
MIN_PLANTER_W_IN = 24.0   # 2 ft (below this, build gets tippy)

# =============================================================================
# BED (planter, ballasted)
# =============================================================================
# Bed is sized to fit the panel plus the frame's margin. Defaults below
# match the LONGi Hi-MO X10 620W bifacial (8.08 × 3.72 ft) - for a
# different panel, see PANEL_PRESETS below and `docs/upcycling.md`.
# Bed is constrained to MAX_PLANTER_L_IN × MAX_PLANTER_W_IN.
BED = {
    "outer_L_in": 96.0,                # 8 ft (capped at MAX_PLANTER_L_IN)
    "outer_W_in": 44.6,                # matches panel width
    "wall_thk_in": 0.75,               # 1x trade lumber (3/4" actual) skin
    "wall_h_in": 27.5,                 # 5 courses of 1x6 (5.5" actual each).
                                    # Rim = wall + skid = 29" — top of the
                                    # wheelchair-accessible seated-gardening
                                    # range (24-30").
                                    #
                                    # WIND-SIZED, and this is the binding
                                    # constraint: the panel sits on 72" posts
                                    # (POSTS below), so its drag acts on a
                                    # ~7.5 ft lever arm about the bed edge -
                                    # roughly 3x the old bed-level hinge. At
                                    # 4 courses / 20" soil the structure only
                                    # reaches SF_overturning 1.81 at 35° tilt
                                    # (FAIL). 5 courses / 25.5" soil gives
                                    # SF 2.55, rated ~130 mph. 6 courses would
                                    # give more margin but puts the rim at
                                    # 34.5", breaking accessibility - so the
                                    # tilt cap (35°, CONTROL below) is what
                                    # carries the rest of the safety margin.
    "soil_fill_in": 25.5,              # soil depth actually counted as ballast
                                    # (2" freeboard below the rim).
                                    # ~60 cu ft = 2.2 cu yd = ~4,000 lb.
    "skid_h_in": 1.5,                  # walls rest directly on the 2x4 footers laid on wide side
                                    # (footers are 1.5" tall × 3.5" wide — gives slats 2.75" of
                                    # bearing per end). Slats also sit on the footers at y=1.5 to
                                    # y=3.0, inside the walls (walls are 0.75" thick, so slats are
                                    # tucked between the wall inner faces)
    "skid_side_in": 3.5,               # 4x nominal
    "bottomless": True,                # no floor, soil on native ground
}

# Wall construction: 1x6 cedar SKIN over vertical 2x4 CLEATS, with a 2x6
# top CAP on the hinge (south) and strut (north) walls. Rationale:
#   - 3/4" skin alone would bow under ~130 psf lateral soil pressure at
#     the base of a 22" wall; cleats every <= 24" carry the span.
#   - Hinges see up to ~550 lb of panel uplift; screws must bite into
#     the 2x6 cap (1.5" thick), never the 3/4" skin.
# All square cuts. Cedar for ground contact (1x PT is rare and thin
# boards rot fast).
BED_WALL = {
    "skin_nominal": "1x6",
    "skin_thk_in": 0.75,
    "course_h_in": 5.5,
    "courses": 5,                      # 5 × 5.5" = 27.5" wall (wind-sized)
    "cleat_nominal": "2x4",
    "cleat_spacing_max_in": 24.0,      # 5 cleats per long wall, 3 per short wall
    "cleats_long_wall": 5,
    "cleats_short_wall": 3,
    # Wall header: 2x4 cedar laid on its wide face (1.5" tall × 3.5" wide)
    # on top of every planter wall. Length = space between the 4x4 uprights.
    # Replaces the old 2x6 cap (which was only on the long walls).
    "header_nominal": "2x4",
    "header_walls": ("south_hinge", "north_strut", "east", "west"),
}

# =============================================================================
# POSTS - the 72" corner uprights that carry the canopy (CANONICAL v2 design)
# =============================================================================
# Four 4x4 PT posts at the outside corners of the bed carry the panel at
# walk-under height. The bed walls fit BETWEEN the posts, so the wall
# length is the bed outer dimension minus 2x post thickness.
#
# This is the structural design of record - it replaces the earlier
# "panel hinged on the bed's south wall" arrangement. The consequence is
# a much longer wind lever arm (panel centroid ~7.5 ft up instead of
# ~2 ft), which is why the tilt is capped at 35° and the bed carries
# 25.5" of soil ballast. See analysis/wind_load_report.md.
POSTS = {
    "nominal": "4x4",
    "thickness_in": 3.5,
    "height_in": 72.0,                 # 6 ft - walk-under / reach-under canopy
    "count": 4,
    "rail_nominal": "2x6",             # panel rails laid flat on the post tops
    "rail_thickness_in": 1.5,
    "rail_width_in": 5.5,
}

# =============================================================================
# PANEL
# =============================================================================
# Defaults to a LONGi Hi-MO X10 620 W bifacial (8.08 × 3.72 ft).
# For other panels, swap PANEL_PRESETS and see `docs/upcycling.md`.
#
# Wattplot's primary use case is **upcycling old panels that would
# otherwise be landfilled**. A typical 15-20 year-old residential panel
# has lost 8-15% of its nameplate output and is no longer cost-effective
# for grid-tie, but is still perfectly good for shade + some power.
# Set `panel_age_years` and `panel_efficiency_pct` to match your salvage.
PANEL = {
    "L_in": 97.0,                       # 8.08 ft
    "W_in": 44.6,                       # 3.72 ft
    "thickness_in": 1.4,
    "mass_lb": 65.0,
    "wattage": 620,                     # nameplate (new); derate for old panels
    "system_derate": 0.85,              # inverter, wiring, mismatch
    "bifacial_bonus": 0.10,             # 10% extra for bifacial gain (0 for mono)
    "panel_tilt_deg": 35.0,             # current commanded angle (for static sims)

    # Second-life panel modeling (for upcycling use case)
    "panel_age_years": 0,               # 0 = new; typical salvage = 10-20
    "panel_bifacial": False,            # most pre-2018 residential panels are mono
    "panel_efficiency_pct": 21.0,       # new ~21%; old ~16-18%
}

# =============================================================================
# PANEL PRESETS - named configurations for common residential panels
# =============================================================================
# Use these with `apply_panel_preset(name)` (see below) to swap the
# PANEL dict for a different size without editing the file by hand.
# All dimensions in inches.
#
# Each preset is the panel's actual frame dimensions (with the aluminum
# frame, which is what the mid-clamps grip). The bed is then sized to
# fit the panel plus a 0.5"-1" margin, capped at MAX_PLANTER_*_IN.
PANEL_PRESETS = {
    "longi_620W": {                  # default: LONGi Hi-MO X10 (new)
        "label": "LONGi Hi-MO X10 620W bifacial",
        "L_in": 97.0, "W_in": 44.6, "thickness_in": 1.4,
        "mass_lb": 65.0, "wattage": 620,             # new nameplate
        "panel_age_years": 0, "panel_bifacial": True, "panel_efficiency_pct": 21.5,
    },
    "residential_60cell": {          # common 2007-2015 residential salvage
        "label": "Residential 60-cell (e.g., Kyocera KD215, Sanyo HIT)",
        "L_in": 65.0, "W_in": 39.0, "thickness_in": 1.6,
        "mass_lb": 38.0, "wattage": 250,             # new nameplate
        "panel_age_years": 12, "panel_bifacial": False, "panel_efficiency_pct": 16.5,
    },
    "residential_72cell": {          # common 2012-2018 residential salvage
        "label": "Residential 72-cell (e.g., Canadian Solar CS6K-300)",
        "L_in": 77.0, "W_in": 39.0, "thickness_in": 1.6,
        "mass_lb": 45.0, "wattage": 300,             # new nameplate
        "panel_age_years": 8, "panel_bifacial": False, "panel_efficiency_pct": 17.5,
    },
    "commercial_96cell": {           # common 2014-2020 commercial salvage
        "label": "Commercial 96-cell (e.g., SunPower SPR-400)",
        "L_in": 65.0, "W_in": 41.0, "thickness_in": 1.6,
        "mass_lb": 42.0, "wattage": 400,             # new nameplate
        "panel_age_years": 6, "panel_bifacial": False, "panel_efficiency_pct": 19.5,
    },
    "large_format_1m65": {           # 1.65m panels, common in EU/Asia salvage
        "label": "Large-format 1.65m (e.g., REC Alpha 400)",
        "L_in": 65.0, "W_in": 41.0, "thickness_in": 1.4,
        "mass_lb": 41.0, "wattage": 400,             # new nameplate
        "panel_age_years": 4, "panel_bifacial": True, "panel_efficiency_pct": 20.5,
    },
    # Note: for two 60-cell panels side by side (80" wide combined), build
    # TWO separate planters in a row. The single-planter cap is 8x5 ft.
}


def apply_panel_preset(name):
    """Swap PANEL dict to a named preset. Returns the previous PANEL for undo.

    The bed is automatically resized to fit the panel (capped at the
    MAX_PLANTER_*_IN limits). The BED['outer_L_in'] is set to the
    panel L + 0.5" margin; BED['outer_W_in'] to panel W + 0.5" margin.
    For widths > 60" the bed is over the cap and the function warns.
    """
    if name not in PANEL_PRESETS:
        raise ValueError(f"Unknown preset: {name}. Known: {list(PANEL_PRESETS)}")
    prev = dict(PANEL)
    preset = PANEL_PRESETS[name]
    PANEL.update(preset)
    # Recompute bed from panel dims, clamped to MAX_PLANTER_*_IN.
    # The panel can overhang the bed by up to 0.5" per side (panel
    # mid-clamps grip the aluminum frame, which sits on the rails).
    # So a 96" bed accepts a panel up to 97" (1" total overhang).
    overhang_per_side = 0.5
    max_panel_L = MAX_PLANTER_L_IN + 2 * overhang_per_side  # 97" for 8-ft cap
    max_panel_W = MAX_PLANTER_W_IN + 2 * overhang_per_side
    if PANEL['L_in'] > max_panel_L:
        raise ValueError(f"Panel L {PANEL['L_in']}\" exceeds max {max_panel_L}\" "
                         f"(MAX_PLANTER_L_IN {MAX_PLANTER_L_IN} + 1\" overhang). "
                         f"Use a chain (multiple planters).")
    if PANEL['W_in'] > max_panel_W:
        raise ValueError(f"Panel W {PANEL['W_in']}\" exceeds max {max_panel_W}\" "
                         f"(MAX_PLANTER_W_IN {MAX_PLANTER_W_IN} + 1\" overhang). "
                         f"Use a chain (multiple planters).")
    # Bed is min(panel, MAX) so the bed never exceeds the lumber cap.
    BED['outer_L_in'] = min(PANEL['L_in'], MAX_PLANTER_L_IN)
    BED['outer_W_in'] = min(PANEL['W_in'], MAX_PLANTER_W_IN)
    # Monofacial panels don't have the bifacial bonus; bifacial gets 10%.
    if PANEL.get('panel_bifacial', False):
        PANEL['bifacial_bonus'] = 0.10
    else:
        PANEL['bifacial_bonus'] = 0.0
    # Auto-derate wattage by panel age (linear: 0.5% per year, typical).
    # Store the original nameplate as 'wattage_nameplate' so we can show
    # both the nameplate and the derated value (e.g., "250 W → 235 W after 12 yr").
    age = PANEL.get('panel_age_years', 0)
    PANEL['wattage_nameplate'] = PANEL['wattage']  # save before derate
    if age > 0:
        derate = max(0.70, 1.0 - 0.005 * age)  # floor at 70% (very old panel)
        PANEL['wattage'] = round(PANEL['wattage'] * derate, 0)
    return prev


def panel_area_sqft():
    return (PANEL['L_in'] / 12.0) * (PANEL['W_in'] / 12.0)

# =============================================================================
# SOIL
# =============================================================================
SOIL = {
    "density_pcf": 75.0,                # wet loam/compost, conservatively
    "saturation_factor": 1.0,
    "friction_mu": 0.40,                # bed on dirt
}

# =============================================================================
# TIER - two builds, one frame
# =============================================================================
# Every Wattplot shares the same bed, frame, hinges, and clamps. The tilt
# mechanism is the only difference:
#
#   'basic' - fixed tilt via a pinned prop strut (no electronics, no
#             actuator, no controller). Tilt is set by hand: lift the
#             frame, drop a 1/2" pin through the strut hole for the angle
#             you want. Storm stow = pull the pin, lay the frame flat.
#             The weekend / salvage-panel build.
#
#   'smart' - motorized tilt via linear actuator + ESP32 controller
#             (auto-fold on wind, sun scheduling, telemetry). The
#             flagship build. Superset of 'basic': the strut holes are
#             still drilled, so a smart build degrades gracefully to a
#             pinned basic build if the electronics are removed.
TIER = 'smart'                        # 'basic' or 'smart'

TIERS = {
    "basic": {
        "tilt_mechanism": 'pinned_strut',
        "electronics": False,
        "stow": 'manual',                # pull pin, lay flat before storms
    },
    "smart": {
        "tilt_mechanism": 'actuator',
        "electronics": True,
        "stow": 'auto_fold',             # controller folds flat on wind trigger
    },
}


def apply_tier(name):
    """Set the active tier ('basic' or 'smart'). Returns previous tier."""
    global TIER
    if name not in TIERS:
        raise ValueError(f"unknown tier {name!r}; use one of {list(TIERS)}")
    prev, TIER = TIER, name
    return prev


def tier_uses_actuator():
    return TIERS[TIER]['tilt_mechanism'] == 'actuator'


# =============================================================================
# FIXED STRUT (basic tier) - pinned prop strut, square cuts only
# =============================================================================
# A 2x4 strut props the frame's north rail. Square ends (no miter): the
# top end butts under the north rail against a 2x4 stop block; the bottom
# end sits in a 2x4 shoe screwed to the bed's north wall. A 1/2" steel
# pin through the shoe + strut locks the angle. One hole per tilt angle.
# Pulling the pin and lowering the frame = storm stow (see wind report:
# a stowed/flat panel carries ~zero uplift).
FIXED_STRUT = {
    "nominal": "2x4",
    "thickness_in": 1.5,
    "height_in": 3.5,
    "source": "2x4x8ft, one board makes both struts",
    "count": 2,                          # one per cross rail end
    "pin_d_in": 0.5,                     # same 1/2" pin stock as the hinges
    "tilt_stops_deg": [0, 15, 25, 35],  # 0 = stowed flat; 35 = max (wind-limited)
}

# =============================================================================
# ACTUATOR (smart tier only)
# =============================================================================
ACTUATOR = {
    "rated_force_lb": 330,
    "stroke_in": 4.0,                    # ECO-WORTHY 12V
    "no_load_speed_in_per_sec": 2.0,
    "duty_cycle": 0.10,                 # 10% rated
}

# =============================================================================
# FRAME (lumber perimeter around the panel - replaces the post+beam design)
# =============================================================================
# Design rules (enforced):
#   1. NO MITER CUTS - every cut is a 90° square cut. Joints are butt, half-lap,
#      or lap. The diagonal brace has square ends that butt into the long rails.
#   2. ALL HARDWARE OFF THE SHELF - hinges, clamps, bolts, screws, rod, pins.
#      Standard sizes from Home Depot, McMaster, or solar mounting suppliers.
#   3. SIMPLE COMMON DIMENSIONS - long members from 8ft stock (96"), cross
#      rails from 2x6x8ft cut to 42", diagonal brace from 2x4x10ft (102").
#
# All dimensions in inches. Nominal → actual: 2x4 = 1.5×3.5, 2x6 = 1.5×5.5,
# 2x12 = 1.5×11.25. Use the actual values for modeling.
FRAME = {
    # Long rails (parallel to panel long axis). 2x6 PT DF, actual 1.5×5.5.
    # length_in = 96" = 8ft stock, no waste. The 97" panel overhangs 0.5" each
    # end of the rail; clamps grip the panel frame at the ends.
    "long_rail": {
        "nominal": "2x6",
        "thickness_in": 1.5,
        "height_in": 5.5,
        "length_in": 96.0,
        "source": "2x6x8ft, no waste",
        "count": 2,
    },
    # Cross rails (perpendicular to long rails). 2x6 PT DF.
    # length_in = 42" (from 2x6x8ft, 6" waste per board, 2 cross rails per board).
    # Cross rails butt into the inside faces of the long rails (no miter).
    "cross_rail": {
        "nominal": "2x6",
        "thickness_in": 1.5,
        "height_in": 5.5,
        "length_in": 42.0,
        "source": "2x6x8ft cut to 42\", 6\" waste per board",
        "count": 2,
    },
    # Diagonal brace. 2x4 PT DF, only loaded at 90° tilt.
    # length_in = 102" (from 2x4x10ft, 18" waste). Square ends butt into the
    # inside faces of the long rails - no miter cut at the corners.
    "diagonal_brace": {
        "nominal": "2x4",
        "thickness_in": 1.5,
        "height_in": 3.5,
        "length_in": 102.0,
        "source": "2x4x10ft, 18\" waste",
    },
    # Galvanized butt hinges, 4"×4" leaf, ½" pin (Home Depot / McMaster).
    # 4 hinges spaced 22" apart along the 88" hinge axis (centered, 4" margin
    # on each end of the 96" bed wall). A single ½" × 72" steel rod threads
    # through all 4 hinge knuckles (one continuous pin, off the shelf at HD).
    "hinge": {
        "type": "galvanized_butt",
        "leaf_in": 4.0,
        "pin_d_in": 0.5,
        "count": 4,
        "spacing_in": 22.0,
        "rod_length_in": 72.0,                 # ½" × 72" steel rod (HD)
        "rod_source": "Home Depot ½\" × 72\" steel rod",
    },
    # Aluminum mid-clamps for the panel. 35mm channel fits most 156 half-cell
    # commercial panels. 2 per long rail + 1 per cross rail = 6 total.
    # IronRidge / Unirac / Quick Mount all make compatible clamps (~$3 each).
    "panel_clamp": {
        "type": "aluminum_mid",
        "length_in": 2.0,
        "height_in": 2.0,
        "thickness_in": 0.4,
        "per_long_rail": 2,
        "per_cross_rail": 1,
        "source": "IronRidge / Unirac mid-clamp, 35mm channel",
    },
    # Actuator mount blocks. 2x6 PT DF clevis on the north rail of the frame
    # + matching block on the bed's north wall. ½" steel pin between them.
    "actuator_mount": {
        "block_nominal": "2x6",
        "block_thickness_in": 1.5,
        "block_height_in": 5.5,
        "block_length_in": 6.0,
    },
}

# =============================================================================
# MPPT SUBSYSTEM (charges the 12V battery from the solar panel)
# =============================================================================
# Mini build (v2.4+): a standalone Sunapex 10A MPPT (IP67,
# LiFePO4-aware) sits on the bed wall, no host connection. The ESP32
# only reads the resulting battery voltage via the on-PCB 10k/10k
# divider (GPIO 33 on the C3, GPIO 33 on the WROOM-32). There is no
# UART, no firmware-side MPPT loop, no DPS5005 setpoint commands.
#
# Full-size v2 build (620W panel): the Sunapex is undersized (10 A,
# 30 V max PV vs the 620W panel's 40 V Voc, 19 A Imp). The full-size
# build needs a real 30-40 A MPPT. Recommended: Victron SmartSolar
# 100/30 (30 A, 100 V max Voc, VE.Direct UART for telemetry +
# Bluetooth for phone monitoring) or EPEver Tracer 4210AN (40 A,
# 100 V max Voc, RS-485 Modbus). Both have explicit LiFePO4 charge
# profiles and re-use the PCB's J4 footprint (GPIO 26/27) for comms.
#
# The DPS5005 + UART-MPPT pattern was the original design (v2.0-2.3)
# but was retired: the DPS5005 was a hack (using a bench PSU as a
# charge controller) and was also undersized even for the 620W panel
# (only 5 A output vs the panel's 19 A Imp - would have thrown away
# ~90% of the panel's potential). See `docs/build_guide.md` §7 for
# the full-size v2 MPPT spec.
MPPT = {
    # Mini build
    "mini_model": "Sunapex 10A MPPT",
    "mini_charge_current_max_A": 10.0,    # 17x headroom over the 10W panel
    "mini_pv_input_v_max": 45.0,          # panel Voc 20.6V, plenty of margin
    "mini_waterproof": "IP67",
    "mini_charge_chemistry": "LiFePO4",   # MUST be set on first power-up (MODE button)
    "mini_host_connection": "none",       # standalone, no UART
    "mini_connector_style": "SAE",        # ships with SAE on both sides + polarity reversal adapter

    # Full-size v2 build (placeholder - choose before full-size build)
    "fullsize_model": "TBD",
    "fullsize_charge_current_max_A": 30.0,  # 620W / 14.4V ≈ 43A, size up
    "fullsize_pv_input_v_max": 100.0,       # 620W panel Voc 40V, headroom
    "fullsize_waterproof": "IP43 (in enclosure)",
    "fullsize_charge_chemistry": "LiFePO4",
    "fullsize_host_connection": "VE.Direct or RS-485",

    # Battery-side telemetry (both builds)
    "converter_output_v_nom": 14.4,        # 12V LiFePO4 charge voltage (informational)
    "converter_efficiency": 0.965,         # Sunapex spec (vs 0.92 for DPS5005 hack, 0.96 for typical MPPT)
}

# =============================================================================
# IMU (panel tilt feedback - closed-loop position, not just step counting)
# =============================================================================
# A BMI160 IMU on the panel reports actual tilt via accelerometer fusion.
# Without it, the actuator's open-loop position drifts; with it, we have
# closed-loop position control. ~$2, I2C, easy to add to the PCB.
IMU = {
    "model": "BMI160",
    "interface": "I2C",
    "sample_rate_hz": 100,
    "tilt_accuracy_deg": 0.5,
    "address": 0x68,                     # default I2C address
}

# =============================================================================
# CONTROL TARGETS
# =============================================================================
CONTROL = {
    "max_tilt_deg": 35.0,               # STRUCTURAL cap. The panel rides on
                                     # 72" posts, so drag acts on a ~7.5 ft
                                     # lever arm about the bed edge. With
                                     # 25.5" of soil ballast the structure
                                     # passes SF_overturning >= 2.0 only to
                                     # ~35° (SF 2.55); 45° drops to 1.89 and
                                     # 90° is far below 1. Do not raise this
                                     # without re-running analysis/wind_load.py.
    "target_current_A": 0.5,            # PI setpoint (motor current)
    "deadband_A": 0.15,
    "max_step_deg_per_sec": 3.0,
    "hard_current_limit_A": 2.5,        # emergency fold trigger
    "i_safe_A": 2.5,                    # structural safety
}

# =============================================================================
# AGRONOMY (tomato)
# =============================================================================
CROP = {
    "type": "tomato",
    "dli_optimal_mol": 25.0,
    "dli_heat_stress_mol": 32.0,
    "max_yield_per_plant_kg": 30.0,
    "plants_in_bed": 4,
    "yield_utilization": 0.65,
    "photoperiod_target_hr": 16,        # 16 hr light, 8 hr dark
    "min_dark_hr": 8,                   # never less than 8 hr dark
}

# =============================================================================
# DERIVED (computed from primary params)
# =============================================================================
def bed_area_sqft():
    return (BED['outer_L_in'] / 12.0) * (BED['outer_W_in'] / 12.0)


def bed_dims_for_geom():
    """Returns (length, width) in feet for geometry calculations."""
    return (BED['outer_L_in'] / 12.0, BED['outer_W_in'] / 12.0)


# Convenience: a single dict for legacy code that imports P
P = {
    "location": LOCATION,
    "bed": BED,
    "bed_wall": BED_WALL,
    "posts": POSTS,
    "frame": FRAME,
    "panel": PANEL,
    "soil": SOIL,
    "tier": TIERS,
    "fixed_strut": FIXED_STRUT,
    "actuator": ACTUATOR,
    "mppt": MPPT,
    "imu": IMU,
    "control": CONTROL,
    "crop": CROP,
}

# =============================================================================
# MINI v2.2 (18" × 14" bed, ECO-WORTHY 10W panel, 100mm kickstand actuator)
# =============================================================================
# A small benchtop/desk-side planter with a real 10W trickle-charger panel.
# Sized to fit the ECO-WORTHY 10W (13.3" × 8.1" × 0.7", 1.88 lb) and the
# 100mm / 70N linear actuator that was ordered for this build.
#
# Validates:
#   - Real 10W solar panel (real power generation, real charging)
#   - 100mm kickstand actuator geometry (compression, low-side mount, 0-35°)
#   - 1x2 frame on a small bed
#   - Same firmware, same sensors, same Sunapex-class MPPT as the full-size
#     (full-size v2 swaps the Sunapex for a Victron 100/30 or similar
#     when the 620W panel comes in - same firmware-side architecture)
#
# Compact enough for a kitchen window, workbench, or small patio. Good for
# 1-2 small herbs or a flower planter. Soil volume ~0.5 cu ft.
#
# Design rules (enforced):
#   1. NO MITER CUTS - every cut is a 90° square cut.
#   2. ALL HARDWARE OFF THE SHELF - Home Depot, Amazon, McMaster.
#   3. SIMPLE COMMON DIMENSIONS - 1x2 / 1x4 / 2x4 from 8ft stock.
#
# NOTE: This is the build that matches the parts already ordered. The earlier
# 100W bifacial + 24" actuator design is parked in git history (v2.1).
MINI = {
    # ----- bed dimensions (sized to ECO-WORTHY 10W panel: 13.3"x8.1") -----
    "bed_outer_L_in": 18.0,            # bed long axis (panel's 13.3" direction)
    "bed_outer_W_in": 14.0,            # bed short axis (panel's 8.1" direction)
    "bed_wall_thk_in": 0.75,           # 1x4 actual
    "bed_wall_h_in": 4.0,              # 4" deep walls (small herb planter)
    "skid_h_in": 0.75,                 # 1x2 actual (low COG for small bed)
    "skid_side_in": 0.75,              # 1x2 actual

    # ----- frame: 18" × 14" rectangle, 1x2 PT rails -----
    "long_rail_length_in": 18.0,       # 1x2x18" (cut from 1x2x8ft, 60" waste)
    "cross_rail_length_in": 12.5,      # 14 - 2*0.75 (frame thickness)
    "long_rail_thk_in": 0.75,          # 1x2 actual (0.75 × 1.5)
    "long_rail_h_in": 1.5,
    "cross_rail_thk_in": 0.75,
    "cross_rail_h_in": 1.5,
    "diagonal_brace_length_in": 21.0,  # sqrt(16.5^2 + 12.5^2) = 20.7", 21" from 2x4x8ft (75" waste)

    # ----- hinge: 1.5" butt hinge with ⅜" pin (v1 spec) -----
    "hinge_leaf_in": 1.5,
    "hinge_pin_d_in": 0.375,
    "hinge_count": 2,
    "hinge_rod_length_in": 22.0,       # ⅜" x 22" steel rod (Home Depot)

    # ----- panel: ECO-WORTHY 10W 12V Mono (or poly) -----
    # Source: https://www.amazon.com/dp/B00OZC3X1C
    # Product Dimensions: 13.3" L x 8.1" W x 0.7" H
    # Item Weight: 1.98 Pounds
    # Voc: 20.6V, Vmp: 17.3V, Imp: 0.58A, Isc: 0.69A
    "panel_L_in": 13.3,
    "panel_W_in": 8.1,
    "panel_t_in": 0.7,
    "panel_wattage": 10,
    "panel_voc_V": 20.6,
    "panel_vmp_V": 17.3,
    "panel_imp_A": 0.58,

    # ----- actuator: 100mm (3.94") stroke 12V 70N (15.7 lbf) KICKSTAND -----
    # Per Amazon listing. Way overkill for the 1.88 lb panel (only needs
    # ~0.67" stroke for 35 deg and ~5.5 lbf force), so the geometry is
    # very forgiving. Plenty of margin to scale up later if needed.
    "actuator_stroke_in": 3.94,        # 100mm
    "actuator_rated_force_lb": 15.7,   # 70N
    "kickstand_lever_arm_in": 2.0,     # distance from hinge axis to top mount
    "kickstand_top_mount_offset_in": 2.0,  # 2" north of hinge on panel
    "max_tilt_deg": 35.0,              # firmware should cap tilt at this value

    # ----- clamps: 4 total (2 per long rail) -----
    # 1" mid-clamps for the small panel frame channel (panel frame is 0.7" tall)
    "panel_clamp_size_in": 1.0,        # IronRidge / Unirac 1" mid clamp
    "panel_clamp_count": 4,

    # ----- battery: 12V 7Ah LiFePO4 (ordered) -----
    # (battery_ah=7 is defined in the energy monitoring section below)
    # ----- smart planter: sensors + watering system (v2.3) -----
    # Sensors (all on the same 1-Wire bus except soil moisture which is analog)
    "panel_temp_sensor": "DS18B20",    # back of panel, telemetry only (Sunapex does its own temp derating)
    "soil_temp_sensor": "DS18B20",      # buried in soil, for plant health
    "battery_temp_sensor": "DS18B20",   # on battery, for safety cutoff
    "soil_moisture_sensor": "V1.2_capacitive",  # Stemedu V1.2, analog output
    "soil_moisture_dry_pct": 30,        # below this, trigger watering (herbs)
    "soil_moisture_wet_pct": 60,        # above this, skip watering

    # Watering system (v2.4: solenoid on tap water, no pump/reservoir)
    "water_source": "tap_pressurized",  # tap water, 40-80 PSI, no pump needed
    "solenoid_model": "12V_NC_1/4in",   # 12V DC normally-closed solenoid valve
    "solenoid_voltage_v": 12,           # matches battery voltage
    "solenoid_holding_power_w": 4,      # typical 12V solenoid holding current
    "solenoid_flow_rate_ml_per_sec": 2,  # at 30 PSI tap, with drip emitter
    "solenoid_max_runtime_sec": 30,     # safety: never run more than 30s
    "solenoid_water_volume_ml_default": 100,  # ~50 sec at 2 mL/sec = 100 mL per event
    "solenoid_max_events_per_day": 3,    # safety: max 3 watering events per 24h
    "watering_block_panel_temp_c": 45,  # don't water if panel > 45C (heat stress)
    "watering_block_battery_v": 11.5,   # don't water if battery < 11.5V
    "watering_block_night": True,       # don't water at night (no solar charging)

    # Energy monitoring + battery SOC (v2.4)
    # Battery: 12V 7Ah LiFePO4 (ordered)
    "battery_ah": 7,
    # LiFePO4 voltage-to-SOC lookup (12V = 4S, approximate)
    # 13.6V = 100% (full), 12.0V = 10% (cutoff), 10.5V = 0% (BMS cutoff)
    "battery_soc_lut": [(13.6, 100), (13.4, 95), (13.3, 90), (13.2, 80),
                       (13.0, 60), (12.8, 40), (12.5, 20), (12.0, 10),
                       (10.5, 0)],  # [(voltage, soc_pct)]
    # Panel specs for POA irradiance calculation
    "panel_rated_efficiency_pct": 18,    # typical 10W panel ~15-18% efficient
    # Energy integration
    "energy_integration_interval_s": 1,  # sample panel V/I every 1s
    "energy_total_max_kwh": 10000,       # safety: cap total counter at 10 MWh

    # ESP32 pin assignments (ESP32-C3 PRO Mini)
    "pin_onewire": 10,                  # DS18B20 data (with 4.7k pullup to 3.3V)
    "pin_soil_moisture": 4,              # capacitive V1.2 analog out
    "pin_solenoid_relay": 5,             # relay control (low-side switch, solenoid)
    # v2.4+: No DPS5005 UART on the mini. The previous pin_dps5005_tx/rx
    # assignments (20/21) are now RESERVED for the full-size v2 build's
    # MPPT comms (Victron VE.Direct or EPEver RS-485). The mini firmware
    # declares no UART; GPIO 26/27 on the WROOM-32 variant are also
    # reserved for the same future use.
    "pin_mppt_reserved_tx": 20,         # reserved for full-size MPPT UART/RS-485
    "pin_mppt_reserved_rx": 21,         # reserved for full-size MPPT UART/RS-485
    "pin_imu_sda": 8,                   # I2C SDA (BMI160 + INA219)
    "pin_imu_scl": 9,                   # I2C SCL
    "pin_limit_0": 6,                   # 0-deg limit switch
    "pin_limit_35": 7,                  # 35-deg limit switch
}


# ----------------------------------------------------------------------------
# Self-validation
# ----------------------------------------------------------------------------
# Catch obvious bugs at import time rather than deep inside apply_panel_preset
# or the wind / sun / shadow calculators. Validates:
#   - every PANEL_PRESETS entry has the required keys with positive values
#   - the default PANEL dict references the same keys
#   - LOCATION latitude is in [-90, 90] and longitude is in [-180, 180]
#   - PANEL fits inside MAX_PLANTER + 2 * overhang
#   - POSTS count is even and the post height clears the canopy
# Raises WattplotConfigError if any of these fail.

_REQUIRED_PANEL_KEYS = (
    "label", "L_in", "W_in", "thickness_in", "mass_lb", "wattage",
    "panel_age_years", "panel_bifacial", "panel_efficiency_pct",
)

# label is required for presets (they show up in docs) but the default
# PANEL dict can omit it -- apply_panel_preset always populates it.
_REQUIRED_PRESET_KEYS = _REQUIRED_PANEL_KEYS
_REQUIRED_DEFAULT_KEYS = tuple(k for k in _REQUIRED_PANEL_KEYS if k != "label")

for _preset_name, _preset in PANEL_PRESETS.items():
    _missing = [k for k in _REQUIRED_PRESET_KEYS if k not in _preset]
    if _missing:
        raise RuntimeError(
            f"PANEL_PRESETS[{_preset_name!r}] is missing required keys: "
            f"{_missing}. Check the preset dict against _REQUIRED_PRESET_KEYS "
            f"in wattplot_params.py."
        )
    _bad = [
        k for k in ("L_in", "W_in", "thickness_in", "mass_lb", "wattage")
        if not isinstance(_preset[k], (int, float)) or _preset[k] <= 0
    ]
    if _bad:
        raise RuntimeError(
            f"PANEL_PRESETS[{_preset_name!r}] has non-positive values for: "
            f"{_bad}. Got: {{k: _preset[k] for k in _bad}}."
        )

_missing_in_default = [k for k in _REQUIRED_DEFAULT_KEYS if k not in PANEL]
if _missing_in_default:
    raise RuntimeError(
        f"Default PANEL dict is missing keys that PANEL_PRESETS expects: "
        f"{_missing_in_default}. Keep them in sync."
    )

if not (-90.0 <= LOCATION["latitude"] <= 90.0):
    raise RuntimeError(
        f"LOCATION['latitude'] = {LOCATION['latitude']} is out of range "
        f"[-90, 90]. pvlib will reject it."
    )
if not (-180.0 <= LOCATION["longitude"] <= 180.0):
    raise RuntimeError(
        f"LOCATION['longitude'] = {LOCATION['longitude']} is out of range "
        f"[-180, 180]. pvlib will reject it."
    )

if POSTS["count"] % 2 != 0:
    raise RuntimeError(
        f"POSTS['count'] = {POSTS['count']} is odd. The wind calc assumes "
        f"a symmetric 2- or 4-post layout; an odd count breaks the "
        f"'leeward pair is fully shielded' assumption."
    )

if PANEL["L_in"] > MAX_PLANTER_L_IN + 1.0:
    raise RuntimeError(
        f"Default PANEL['L_in'] = {PANEL['L_in']}\" exceeds the max "
        f"({MAX_PLANTER_L_IN}\" + 1\" overhang). The default should be the "
        f"largest preset; check PANEL_PRESETS."
    )
