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
#   - Same firmware, same sensors, same DPS5005 MPPT as the full-size
#
# Compact enough for a kitchen window, workbench, or small patio. Good for
# 1-2 small herbs or a flower planter. Soil volume ~0.5 cu ft.
#
# Design rules (enforced):
#   1. NO MITER CUTS — every cut is a 90° square cut.
#   2. ALL HARDWARE OFF THE SHELF — Home Depot, Amazon, McMaster.
#   3. SIMPLE COMMON DIMENSIONS — 1x2 / 1x4 / 2x4 from 8ft stock.
#
# NOTE: This is the build that matches the parts already ordered. The earlier
# 100W bifacial + 24" actuator design is parked in git history (v2.1).
MINI = dict(
    # ----- bed dimensions (sized to ECO-WORTHY 10W panel: 13.3"x8.1") -----
    bed_outer_L_in=18.0,            # bed long axis (panel's 13.3" direction)
    bed_outer_W_in=14.0,            # bed short axis (panel's 8.1" direction)
    bed_wall_thk_in=0.75,           # 1x4 actual
    bed_wall_h_in=4.0,              # 4" deep walls (small herb planter)
    skid_h_in=0.75,                 # 1x2 actual (low COG for small bed)
    skid_side_in=0.75,              # 1x2 actual

    # ----- frame: 18" × 14" rectangle, 1x2 PT rails -----
    long_rail_length_in=18.0,       # 1x2x18" (cut from 1x2x8ft, 60" waste)
    cross_rail_length_in=12.5,      # 14 - 2*0.75 (frame thickness)
    long_rail_thk_in=0.75,          # 1x2 actual (0.75 × 1.5)
    long_rail_h_in=1.5,
    cross_rail_thk_in=0.75,
    cross_rail_h_in=1.5,
    diagonal_brace_length_in=21.0,  # sqrt(16.5^2 + 12.5^2) = 20.7", 21" from 2x4x8ft (75" waste)

    # ----- hinge: 1.5" butt hinge with ⅜" pin (v1 spec) -----
    hinge_leaf_in=1.5,
    hinge_pin_d_in=0.375,
    hinge_count=2,
    hinge_rod_length_in=22.0,       # ⅜" x 22" steel rod (Home Depot)

    # ----- panel: ECO-WORTHY 10W 12V Mono (or poly) -----
    # Source: https://www.amazon.com/dp/B00OZC3X1C
    # Product Dimensions: 13.3" L x 8.1" W x 0.7" H
    # Item Weight: 1.98 Pounds
    # Voc: 20.6V, Vmp: 17.3V, Imp: 0.58A, Isc: 0.69A
    panel_L_in=13.3,
    panel_W_in=8.1,
    panel_t_in=0.7,
    panel_wattage=10,
    panel_voc_V=20.6,
    panel_vmp_V=17.3,
    panel_imp_A=0.58,

    # ----- actuator: 100mm (3.94") stroke 12V 70N (15.7 lbf) KICKSTAND -----
    # Per Amazon listing. Way overkill for the 1.88 lb panel (only needs
    # ~0.67" stroke for 35 deg and ~5.5 lbf force), so the geometry is
    # very forgiving. Plenty of margin to scale up later if needed.
    actuator_stroke_in=3.94,        # 100mm
    actuator_rated_force_lb=15.7,   # 70N
    kickstand_lever_arm_in=2.0,     # distance from hinge axis to top mount
    kickstand_top_mount_offset_in=2.0,  # 2" north of hinge on panel
    max_tilt_deg=35.0,              # firmware should cap tilt at this value

    # ----- clamps: 4 total (2 per long rail) -----
    # 1" mid-clamps for the small panel frame channel (panel frame is 0.7" tall)
    panel_clamp_size_in=1.0,        # IronRidge / Unirac 1" mid clamp
    panel_clamp_count=4,

    # ----- battery: 12V 7Ah LiFePO4 (ordered) -----
    battery_ah=7,
)
