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
    "panel": PANEL,
    "soil": SOIL,
    "actuator": ACTUATOR,
    "control": CONTROL,
    "crop": CROP,
}
