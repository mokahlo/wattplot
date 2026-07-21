"""
Wattplot v2 — Shadow raycaster using the actual 3D model geometry.

Given the panel's 4 corner positions (from the cadquery model) and a sun
direction, project the panel onto the ground plane and compute the
intersection with the bed rectangle. Returns the shaded area.

This replaces the empirical "bed sunlit fraction" formula in the simulator
with a geometrically correct calculation.
"""

import math
import numpy as np
from shapely.geometry import Polygon, box


def project_panel_to_ground(panel_corners_3d, sun_direction):
    """
    Project a 3D panel polygon onto the ground plane (y=0).

    Args:
        panel_corners_3d: 4×3 array of (x, y, z) corner positions in inches
        sun_direction: 3-tuple (sx, sy, sz), unit vector from origin to sun
                       (i.e., direction sunlight is COMING FROM)

    Returns:
        2D polygon (list of (x, z)) in inches, the projected shadow
    """
    sx, sy, sz = sun_direction
    if sy <= 0:
        # Sun below horizon, no shadow on ground
        return None

    shadow_pts = []
    for (x, y, z) in panel_corners_3d:
        # Project from point (x, y, z) along sun direction to y=0
        # t * sy = -y, so t = -y / sy
        t = -y / sy
        sx_proj = x + t * sx
        sz_proj = z + t * sz
        shadow_pts.append((sx_proj, sz_proj))

    return Polygon(shadow_pts)


def get_panel_corners(tilt_deg, panel_L_in, panel_W_in, hinge_y_in, hinge_z_in):
    """
    Compute the 4 panel center corners in 3D space given the tilt angle.

    Convention: hinge axis is along X (east-west). Hinge is at the south wall top.
    Panel extends in -Z direction (north) from the hinge. When tilted, the
    far edge lifts in +Y direction.

    Returns: 4×3 array of corners as (x, y, z) tuples — the panel CENTERLINE
    rectangle, not the full thickness. This avoids self-intersecting
    projections at extreme sun angles.
    """
    tilt = math.radians(tilt_deg)

    half_L = panel_L_in / 2.0
    half_W = panel_W_in / 2.0

    # Panel centerline corners (4 vertices of a flat rectangle in the panel plane)
    # Hinge edge at z=0, far edge at z=-W
    local = np.array([
        [-half_L,  0.0,  0.0],         # hinge, -X
        [+half_L,  0.0,  0.0],         # hinge, +X
        [+half_L,  0.0, -panel_W_in],  # far edge, +X
        [-half_L,  0.0, -panel_W_in],  # far edge, -X
    ])

    # Rotate about X axis by tilt_deg.
    # Local -Z direction maps to world (0, sin(tilt), -cos(tilt))
    R = np.array([
        [1, 0, 0],
        [0, math.cos(tilt), -math.sin(tilt)],
        [0, math.sin(tilt),  math.cos(tilt)],
    ])
    rotated = local @ R.T

    # Translate so hinge is at world position (0, hinge_y, hinge_z)
    rotated[:, 1] += hinge_y_in
    rotated[:, 2] += hinge_z_in

    return rotated


def compute_bed_sunlit_fraction(tilt_deg, sun_azimuth_deg, sun_elevation_deg,
                                 bed_L_in, bed_W_in, panel_L_in, panel_W_in,
                                 hinge_y_in, hinge_z_in, hinge_axis="X"):
    """
    Compute the fraction of the bed that is in direct sun.

    Args:
        tilt_deg: panel tilt from horizontal (0 = flat, 90 = vertical)
        sun_azimuth_deg: sun azimuth in pvlib convention (0=N, 90=E, 180=S, 270=W)
        sun_elevation_deg: sun elevation above horizon (0 = horizon, 90 = zenith)
        bed_L_in, bed_W_in: bed dimensions in inches (X × Z)
        panel_L_in, panel_W_in: panel dimensions
        hinge_y_in, hinge_z_in: hinge position (height, Z coord)
        hinge_axis: "X" (current design) or "Z" (east-west hinge)

    Returns:
        fraction of bed in sun (0.0 to 1.0)
    """
    if sun_elevation_deg <= 0:
        return 0.0  # sun below horizon

    # Sun direction (unit vector from origin to sun)
    # In our coord system: x=east, y=up, z=north
    # pvlib azimuth: 0=north, 90=east, 180=south, 270=west
    az_rad = math.radians(sun_azimuth_deg)
    el_rad = math.radians(sun_elevation_deg)
    sx = math.sin(az_rad) * math.cos(el_rad)  # east component
    sy = math.sin(el_rad)                      # up component
    sz = math.cos(az_rad) * math.cos(el_rad)  # north component

    # Get panel corners in 3D
    corners_3d = get_panel_corners(tilt_deg, panel_L_in, panel_W_in,
                                     hinge_y_in, hinge_z_in)

    # Project to ground plane
    shadow_2d = project_panel_to_ground(corners_3d, (sx, sy, sz))
    if shadow_2d is None or shadow_2d.is_empty:
        return 1.0  # no shadow

    # Build bed rectangle (centered at origin in XZ plane)
    bed_L_half = bed_L_in / 2.0
    bed_W_half = bed_W_in / 2.0
    bed_rect = box(-bed_L_half, -bed_W_half, bed_L_half, bed_W_half)

    # Compute intersection
    intersection = shadow_2d.intersection(bed_rect)
    if intersection.is_empty:
        return 1.0  # shadow doesn't hit the bed

    shaded_area = intersection.area
    bed_area = bed_L_in * bed_W_in

    sunlit_fraction = 1.0 - (shaded_area / bed_area)
    return max(0.0, min(1.0, sunlit_fraction))


# ============================================================================
# Quick test
# ============================================================================
if __name__ == "__main__":
    # Phoenix summer noon, 35° tilt
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from wattplot_params import BED, STRUCTURE, PANEL

    hinge_y = BED['wall_h_in']
    hinge_z = BED['outer_W_in'] / 2.0

    print("Bed sunlit fraction at noon, summer solstice, Phoenix:")
    for tilt in [0, 15, 35, 50, 75, 90]:
        for (az, el, hour) in [(120, 75, 8), (180, 80, 12), (240, 50, 16), (270, 30, 18)]:
            frac = compute_bed_sunlit_fraction(
                tilt, az, el,
                BED['outer_L_in'], BED['outer_W_in'],
                PANEL['L_in'], PANEL['W_in'],
                hinge_y, hinge_z
            )
            print(f"  Tilt {tilt:3d}° | Sun az {az:3d}° el {el:2d}° ({hour:02d}:00): bed sunlit = {frac*100:.1f}%")
        print()
