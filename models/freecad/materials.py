"""
Wattplot v2 — Materials & hardware reference.

Wood species, actual lumber dimensions, fasteners, metal hardware.
Single source of truth alongside wattplot_params.py for the physical
properties that the parametric FreeCAD model uses.

All units inches + pounds unless noted.
"""

# =============================================================================
# WOOD PROPERTIES (Pressure-Treated Douglas Fir, typical for outdoor builds)
# =============================================================================
# Source: NDS Supplement, 2018 edition. Values are for incised pressure-treated
# DF (the kind you buy at Home Depot for ground contact).
WOOD = dict(
    species="Douglas Fir (Pressure Treated)",
    grade="No. 2 or better",
    # Wet-use values (PT lumber starts wet, dries in service)
    bending_stress_psi=875,        # Fb (allowable)
    tension_stress_psi=450,        # Ft
    compression_parallel_psi=1150, # Fc_par
    compression_perp_psi=535,      # Fc_perp
    shear_parallel_psi=180,        # Fv
    modulus_elasticity_psi=1400000, # E (true, not NDS apparent)
    density_pcf=35.0,              # PT DF, ~35 pcf dry
    moisture_content=0.19,         # 19% MC at installation
)

# =============================================================================
# LUMBER (nominal → actual)
# =============================================================================
# Real dimensions of dressed (S4S) lumber. PT lumber may swell slightly when
# first wet; design with the actual dimensions below.
LUMBER = {
    "2x4":  {"actual_t": 1.5,  "actual_h": 3.5},
    "2x6":  {"actual_t": 1.5,  "actual_h": 5.5},
    "2x8":  {"actual_t": 1.5,  "actual_h": 7.25},
    "2x10": {"actual_t": 1.5,  "actual_h": 9.25},
    "2x12": {"actual_t": 1.5,  "actual_h": 11.25},
    "4x4":  {"actual_t": 3.5,  "actual_h": 3.5},
    "4x6":  {"actual_t": 3.5,  "actual_h": 5.5},
    "6x6":  {"actual_t": 5.5,  "actual_h": 5.5},
}

# Per-foot weight of common sizes (PT DF, ~35 pcf)
LUMBER_WEIGHT_LB_PER_FT = {
    "2x4":  1.28,
    "2x6":  2.00,
    "2x8":  2.64,
    "2x10": 3.36,
    "2x12": 4.10,
    "4x4":  2.98,
    "6x6":  6.84,
}

# =============================================================================
# FASTENERS
# =============================================================================
# Corrosion-resistant for PT lumber: hot-dip galvanized (HDG) or silicon bronze.
# Stainless (304/316) is best but expensive. HDG is the cost-effective choice
# for ACQ-treated lumber.
FASTENERS = {
    # For half-lap corner joints on the bed walls. Through-bolted, not screwed.
    "carriage_bolt_3_8": {
        "diameter_in": 0.375,
        "head": "domed (carriage)",
        "washer_in": 1.0,           # OD of fender washer
        "nut": "hex",
        "typical_length_in": 4.0,  # through 2x 1.5" walls + 1" nut stack
        "material": "HDG steel",
        "use": "bed corner joints, frame corner joints",
    },
    # For panel-to-rail clamps (mid-clamps) and frame assembly.
    "deck_screw_1_4": {
        "diameter_in": 0.25,
        "length_in": 3.0,           # through 1.5" rail + 1.4" panel frame
        "head": "Torx T-25",
        "material": "HDG or ceramic-coated",
        "use": "frame assembly, panel clamp fasteners",
    },
    # For hinge pin, actuator mount pin.
    "steel_pin_1_2": {
        "diameter_in": 0.5,
        "material": "1045 carbon steel, zinc plated",
        "typical_length_in": 90.0,  # continuous through all hinges
        "use": "hinge axis, actuator clevis pin",
    },
    # For lag-bolting the hinge leaf to the bed wall.
    "lag_bolt_5_16": {
        "diameter_in": 0.3125,
        "length_in": 3.0,
        "head": "hex",
        "material": "HDG steel",
        "use": "hinge-to-bed-wall mounting",
    },
}

# =============================================================================
# METAL HARDWARE
# =============================================================================
# Things that are NOT wood.
HARDWARE = {
    # 4 × galvanized butt hinges mount the frame to the bed's south wall.
    # Source: Home Depot / McMaster-Carr. Leaf 4"×4" with ½" knuckles.
    "butt_hinge_4x4": {
        "leaf_W_in": 4.0,
        "leaf_L_in": 4.0,
        "leaf_t_in": 0.075,
        "knuckle_d_in": 0.5,
        "pin_d_in": 0.5,
        "material": "HDG steel",
        "load_rating_lb": 200,    # per hinge, conservative
        "count": 4,
        "use": "frame-to-bed south wall hinge axis",
    },
    # Aluminum mid-clamps for the panel. IronRidge / Unirac / Quick Mount
    # all make compatible clamps. The 35mm height matches the panel frame
    # channel on most 156 half-cell commercial panels.
    "aluminum_mid_clamp": {
        "length_in": 2.0,
        "height_in": 2.0,
        "thickness_in": 0.4,
        "channel_depth_in": 0.4,   # 35mm panel frame sits in this channel
        "material": "6005-T5 aluminum, mill finish",
        "fastener": "M8 stainless bolt + EPDM washer",
        "count_long_rail": 2,
        "count_cross_rail": 1,
        "use": "panel-to-rail attachment",
    },
}
