"""
Wattplot v2 — Single source of truth for all parameters.

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
LOCATION = dict(
    name="Phoenix, AZ",
    latitude=33.45,
    longitude=-112.07,
    elevation_m=337,
    timezone="America/Phoenix",
    design_wind_speed_mph=115.0,    # ASCE 7-22, Risk Cat II 700-yr
    design_wind_exposure="C",
    soil_bearing_psf=1500,           # Phoenix desert soil, typical
)

# =============================================================================
# BED (planter, ballasted)
# =============================================================================
BED = dict(
    outer_L_in=96.0,                # 8 ft
    outer_W_in=44.6,                # matches panel width
    wall_thk_in=1.5,                # 2x nominal
    wall_h_in=12.0,                 # 12" soil depth
    skid_h_in=3.0,                  # 3" off grade
    skid_side_in=3.5,               # 4x nominal
    bottomless=True,                # no floor, soil on native ground
)

# =============================================================================
# STRUCTURE (posts + beam, hinged at bed)
# =============================================================================
STRUCTURE = dict(
    post_side_in=5.5,               # 6x6 nominal
    post_height_in=120.0,           # 10 ft
    post_inset_in=6.0,              # from bed end
    beam_side_in=5.5,               # 6x6
    beam_length_in=84.0,            # 7 ft between posts
    beam_attach_h_in=108.0,         # height to beam centerline
    hinge_d_in=0.5,                 # 1/2" continuous hinge
)

# =============================================================================
# PANEL
# =============================================================================
PANEL = dict(
    L_in=97.0,                       # 8.08 ft
    W_in=44.6,                       # 3.72 ft
    thickness_in=1.4,
    mass_lb=65.0,
    wattage=620,                     # nameplate
    system_derate=0.85,              # inverter, wiring, mismatch
    bifacial_bonus=0.10,             # 10% extra for bifacial gain
    panel_tilt_deg=35.0,             # current commanded angle (for static sims)
)

# =============================================================================
# SOIL
# =============================================================================
SOIL = dict(
    density_pcf=75.0,                # wet loam/compost, conservatively
    saturation_factor=1.0,
    friction_mu=0.40,                # bed on dirt
)

# =============================================================================
# ACTUATOR
# =============================================================================
ACTUATOR = dict(
    rated_force_lb=330,
    stroke_in=4.0,                    # ECO-WORTHY 12V
    no_load_speed_in_per_sec=2.0,
    duty_cycle=0.10,                 # 10% rated
)

# =============================================================================
# FRAME (lumber perimeter around the panel — replaces the post+beam design)
# =============================================================================
# Design rules (enforced):
#   1. NO MITER CUTS — every cut is a 90° square cut. Joints are butt, half-lap,
#      or lap. The diagonal brace has square ends that butt into the long rails.
#   2. ALL HARDWARE OFF THE SHELF — hinges, clamps, bolts, screws, rod, pins.
#      Standard sizes from Home Depot, McMaster, or solar mounting suppliers.
#   3. SIMPLE COMMON DIMENSIONS — long members from 8ft stock (96"), cross
#      rails from 2x6x8ft cut to 42", diagonal brace from 2x4x10ft (102").
#
# All dimensions in inches. Nominal → actual: 2x4 = 1.5×3.5, 2x6 = 1.5×5.5,
# 2x12 = 1.5×11.25. Use the actual values for modeling.
FRAME = dict(
    # Long rails (parallel to panel long axis). 2x6 PT DF, actual 1.5×5.5.
    # length_in = 96" = 8ft stock, no waste. The 97" panel overhangs 0.5" each
    # end of the rail; clamps grip the panel frame at the ends.
    long_rail=dict(
        nominal="2x6",
        thickness_in=1.5,
        height_in=5.5,
        length_in=96.0,
        source="2x6x8ft, no waste",
        count=2,
    ),
    # Cross rails (perpendicular to long rails). 2x6 PT DF.
    # length_in = 42" (from 2x6x8ft, 6" waste per board, 2 cross rails per board).
    # Cross rails butt into the inside faces of the long rails (no miter).
    cross_rail=dict(
        nominal="2x6",
        thickness_in=1.5,
        height_in=5.5,
        length_in=42.0,
        source="2x6x8ft cut to 42\", 6\" waste per board",
        count=2,
    ),
    # Diagonal brace. 2x4 PT DF, only loaded at 90° tilt.
    # length_in = 102" (from 2x4x10ft, 18" waste). Square ends butt into the
    # inside faces of the long rails — no miter cut at the corners.
    diagonal_brace=dict(
        nominal="2x4",
        thickness_in=1.5,
        height_in=3.5,
        length_in=102.0,
        source="2x4x10ft, 18\" waste",
    ),
    # Galvanized butt hinges, 4"×4" leaf, ½" pin (Home Depot / McMaster).
    # 4 hinges spaced 22" apart along the 88" hinge axis (centered, 4" margin
    # on each end of the 96" bed wall). A single ½" × 72" steel rod threads
    # through all 4 hinge knuckles (one continuous pin, off the shelf at HD).
    hinge=dict(
        type="galvanized_butt",
        leaf_in=4.0,
        pin_d_in=0.5,
        count=4,
        spacing_in=22.0,
        rod_length_in=72.0,                 # ½" × 72" steel rod (HD)
        rod_source="Home Depot ½\" × 72\" steel rod",
    ),
    # Aluminum mid-clamps for the panel. 35mm channel fits most 156 half-cell
    # commercial panels. 2 per long rail + 1 per cross rail = 6 total.
    # IronRidge / Unirac / Quick Mount all make compatible clamps (~$3 each).
    panel_clamp=dict(
        type="aluminum_mid",
        length_in=2.0,
        height_in=2.0,
        thickness_in=0.4,
        per_long_rail=2,
        per_cross_rail=1,
        source="IronRidge / Unirac mid-clamp, 35mm channel",
    ),
    # Actuator mount blocks. 2x6 PT DF clevis on the north rail of the frame
    # + matching block on the bed's north wall. ½" steel pin between them.
    actuator_mount=dict(
        block_nominal="2x6",
        block_thickness_in=1.5,
        block_height_in=5.5,
        block_length_in=6.0,
    ),
)

# =============================================================================
# MPPT SUBSYSTEM (charges the 12V battery from the main 620W panel)
# =============================================================================
# The 620W main panel feeds the microinverter (for AC out) AND a DPS5005
# programmable buck converter (for 12V battery charging). No separate trickle
# panel — the main panel is way more than enough to keep the controller
# battery topped off (~50 Wh/day controller load vs ~2000+ Wh/day panel yield).
MPPT = dict(
    # DPS5005 programmable buck converter (Ruideng), UART-controlled
    converter_model="DPS5005",
    converter_input_v_max=60.0,        # 620W panel Vmp ~33V, Voc ~40V
    converter_output_v_nom=14.4,      # 12V LiFePO4 charge voltage
    converter_output_i_max=5.0,       # amps to battery
    converter_efficiency=0.92,        # typical for DPS5005
    uart_baud=9600,                   # DPS5005 serial protocol
)

# =============================================================================
# IMU (panel tilt feedback — closed-loop position, not just step counting)
# =============================================================================
# A BMI160 IMU on the panel reports actual tilt via accelerometer fusion.
# Without it, the actuator's open-loop position drifts; with it, we have
# closed-loop position control. ~$2, I2C, easy to add to the PCB.
IMU = dict(
    model="BMI160",
    interface="I2C",
    sample_rate_hz=100,
    tilt_accuracy_deg=0.5,
    address=0x68,                     # default I2C address
)

# =============================================================================
# CONTROL TARGETS
# =============================================================================
CONTROL = dict(
    target_current_A=0.5,            # PI setpoint (motor current)
    deadband_A=0.15,
    max_step_deg_per_sec=3.0,
    hard_current_limit_A=2.5,        # emergency fold trigger
    i_safe_A=2.5,                    # structural safety
)

# =============================================================================
# AGRONOMY (tomato)
# =============================================================================
CROP = dict(
    type="tomato",
    dli_optimal_mol=25.0,
    dli_heat_stress_mol=32.0,
    max_yield_per_plant_kg=30.0,
    plants_in_bed=4,
    yield_utilization=0.65,
    photoperiod_target_hr=16,        # 16 hr light, 8 hr dark
    min_dark_hr=8,                   # never less than 8 hr dark
)

# =============================================================================
# DERIVED (computed from primary params)
# =============================================================================
def bed_area_sqft():
    return (BED['outer_L_in'] / 12.0) * (BED['outer_W_in'] / 12.0)


def panel_area_sqft():
    return (PANEL['L_in'] / 12.0) * (PANEL['W_in'] / 12.0)


def bed_dims_for_geom():
    """Returns (length, width) in feet for geometry calculations."""
    return (BED['outer_L_in'] / 12.0, BED['outer_W_in'] / 12.0)


# Convenience: a single dict for legacy code that imports P
P = {
    "location": LOCATION,
    "bed": BED,
    "structure": STRUCTURE,
    "frame": FRAME,
    "panel": PANEL,
    "soil": SOIL,
    "actuator": ACTUATOR,
    "mppt": MPPT,
    "imu": IMU,
    "control": CONTROL,
    "crop": CROP,
}

# =============================================================================
# MINI v2 (40" × 22" bed, 100W bifacial, 24" stroke actuator for true 90°)
# =============================================================================
# A benchtop validation prototype. Larger than the original 1/5 mini (which
# couldn't fit a real bifacial off-shelf and had too short a stroke for 90°),
# but still small enough to fit on a workbench. Validates:
#   - 100W bifacial panel (real power generation, real rear-side gain)
#   - 24" stroke actuator (true 0-90° tilt range)
#   - Same firmware, same sensors, same MPPT controller
#
# This is roughly 1/2.4 of the full-size (96" × 44.6" → 40" × 22"),
# bigger than the 1/5 windowsill mini, more "real" as a system.
#
# Design rules (enforced):
#   1. NO MITER CUTS — every cut is a 90° square cut.
#   2. ALL HARDWARE OFF THE SHELF — Home Depot, Amazon, McMaster.
#   3. SIMPLE COMMON DIMENSIONS — 2x2 / 1x4 / 2x4 from 8ft stock.
#
# If the mini works on the bench for a week, the full-size will work too.
MINI = dict(
    # ----- bed dimensions -----
    bed_outer_L_in=40.0,            # sized to fit panel (38.58") + 2x 2x2 rails (3")
                                   # interior = 40 - 3 = 37" (panel fits with 0.58" margin)
    bed_outer_W_in=22.0,            # sized to fit panel (20.87") + 2x 2x2 rails (3")
                                   # interior = 22 - 3 = 19" (panel fits with 1.87" margin)
    bed_wall_thk_in=0.75,           # 1x4 actual
    bed_wall_h_in=3.5,              # 1x4 actual (real soil depth for small plant)
    skid_h_in=1.5,                  # 2x2 actual
    skid_side_in=1.5,               # 2x2 actual

    # ----- frame: 40" × 22" rectangle, 2x2 PT rails -----
    long_rail_length_in=40.0,       # 2x2x40" (cut from 2x2x8ft, 56" waste per board)
    cross_rail_length_in=19.0,      # 22 - 2*1.5 (frame thickness)
    long_rail_thk_in=1.5,          # 2x2 actual (1.5 × 1.5)
    long_rail_h_in=1.5,
    cross_rail_thk_in=1.5,
    cross_rail_h_in=1.5,
    diagonal_brace_length_in=42.0,  # sqrt(37^2 + 19^2) = 41.6"; 42" from 2x4x8ft (12" waste)

    # ----- hinge: 4" butt hinge with ⅜" pin (full-size hinge for bigger load) -----
    hinge_leaf_in=4.0,
    hinge_pin_d_in=0.5,             # ½" pin (vs ⅜" in v1 mini) for the heavier panel
    hinge_count=2,                  # 2 hinges (smaller load than full-size 4)
    hinge_rod_length_in=44.0,       # ½" x 44" steel rod (Home Depot)

    # ----- panel: Newpowa 100W 12V Bifacial, 38.58" × 20.87" × 1.18" -----
    # (smallest off-the-shelf bifacial panel that gives meaningful power)
    panel_L_in=38.58,
    panel_W_in=20.87,
    panel_t_in=1.18,
    panel_wattage=100,
    panel_voc_V=22.0,               # typical 100W 12V mono bifacial: Voc=22V, Vmp=18V
    panel_vmp_V=18.0,
    panel_imp_A=5.56,               # 100W / 18V = 5.56A

    # ----- actuator: 4" stroke 12V 75 lbf KICKSTAND (low side, 0-35° tilt) -----
    # Kickstand geometry: actuator mounted on the bed's south wall (low side)
    # with one end on the wall and the other end on the panel's underside.
    # Limited to 0-35° tilt (the power-optimal range per the Phoenix sun sim:
    # 159 kWh/yr at 35° vs 170 kWh/yr at 0° but 0° is just a flat panel).
    # Benefits: $18 small actuator vs $90 24" stroke, in compression (safer
    # in wind, fails to flat if power dies), much more compact.
    actuator_stroke_in=4.0,         # ECO-WORTHY 4" stroke 12V 75 lbf, ~$18
    actuator_rated_force_lb=75,
    # Kickstand geometry (relative to bed corner at south wall outer face):
    #   Bottom mount (fixed): on bed's south wall, y=0.75 (skid mid-height)
    #   Top mount (moving): on panel's underside, ~6" north of south edge
    #   Lever arm: 6" from hinge axis to top mount
    #   Geometry chosen for 4" stroke to cover 0-35° tilt comfortably
    kickstand_lever_arm_in=6.0,    # distance from hinge axis to top mount
    kickstand_top_mount_offset_in=6.0,  # how far north of hinge on panel
    max_tilt_deg=35.0,              # firmware should cap tilt at this value

    # ----- clamps: 6 total (2 per long rail + 1 per cross rail) -----
    # Aluminum mid-clamps for 35mm panel frame channel (same as full-size)
    panel_clamp_size_in=2.0,        # IronRidge / Unirac standard
    panel_clamp_count=6,

    # ----- electronics: identical to full-size -----
    # ESP32-WROOM-32 (same)
    # DPS5005 MPPT (same — 5A, well within 100W panel's 5.56A Imp)
    # BMI160 IMU (same)
    # INA219 current sensor (same)
    # DS18B20 temp (same)
    # Soil moisture sensor (same)

    # ----- battery: 12V 20Ah LiFePO4 (heavier load than v1 mini's 5Ah) -----
    battery_ah=20,
)
