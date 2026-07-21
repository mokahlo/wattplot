"""
Wattplot v2 — Sun + tilt schedule simulator for Phoenix, AZ.
Compares 4 tilt schedules and reports annual kWh, bed DLI, tomato yield, actuator cycles.

Run: python analysis/sun_simulator.py
Outputs: renders/sun_simulator_*.png + a comparison table in stdout.
"""

import os
import sys
import math
import numpy as np
import pandas as pd
import pvlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Allow imports from project root and sibling dirs
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "models"))

# Single source of truth for parameters
from wattplot_params import LOCATION, BED, PANEL, SOIL, CROP
from shadow_raycaster import compute_bed_sunlit_fraction

# ============================================================================
# INPUTS (loaded from wattplot_params.py — single source of truth)
# ============================================================================
LAT, LON = LOCATION['latitude'], LOCATION['longitude']
TZ = LOCATION['timezone']
ALT = LOCATION['elevation_m']

# Panel (620W bifacial, 156 half-cell)
PANEL_WATT = PANEL['wattage']
SYSTEM_DERATE = PANEL['system_derate']
BIFACIAL_BONUS = PANEL['bifacial_bonus']

# Bed (from wattplot_params)
BED_L_IN = BED['outer_L_in']
BED_W_IN = BED['outer_W_in']
BED_L = BED_L_IN / 12.0
BED_W = BED_W_IN / 12.0
BED_AREA = BED_L * BED_W  # 29.76 sq ft

# Hinge position (from wattplot_params)
HINGE_Y_IN = BED['wall_h_in']
HINGE_Z_IN = BED['outer_W_in'] / 2.0

# Tomato yield model (from wattplot_params)
DLI_OPTIMAL = CROP['dli_optimal_mol']
DLI_HEAT_STRESS = CROP['dli_heat_stress_mol']
MAX_YIELD_PER_PLANT = CROP['max_yield_per_plant_kg']
PLANTS_IN_BED = CROP['plants_in_bed']
YIELD_UTILIZATION = CROP['yield_utilization']

# Actuator cycle estimates (per year)
LOAD_AWARE_CYCLES_PER_YEAR = 6   # wind reductions, occasional

YEAR = 2025


# ============================================================================
# SUN POSITION + WEATHER
# ============================================================================
def build_solar_timeseries():
    """Hourly solar position + clear-sky irradiance for Phoenix 2025."""
    times = pd.date_range(f'{YEAR}-01-01', f'{YEAR}-12-31 23:00', freq='h', tz=TZ)

    loc = pvlib.location.Location(LAT, LON, tz=TZ, altitude=ALT)
    solpos = pvlib.solarposition.get_solarposition(times, LAT, LON)
    cs = loc.get_clearsky(times)  # ghi, dni, dhi

    df = pd.DataFrame({
        'ghi': cs['ghi'],
        'dni': cs['dni'],
        'dhi': cs['dhi'],
        'sun_zenith': solpos['apparent_zenith'],
        'sun_azimuth': solpos['azimuth'],
        'sun_elevation': solpos['apparent_elevation'],
    })

    # Daylight mask
    df['daylight'] = df['sun_elevation'] > 0

    # PAR = photosynthetically active radiation, ~45% of GHI
    df['par'] = df['ghi'] * 0.45

    return df


# ============================================================================
# PANEL ANGLE → POWER
# ============================================================================
def panel_output_w(panel_tilt, panel_azimuth, sun_zenith, sun_azimuth, bifacial=True):
    """Power output in W for a tilted panel given sun position.

    Convention (pvlib-style):
      panel_tilt: 0 = flat (face up), 90 = vertical
      panel_azimuth: 0 = north, 90 = east, 180 = south, 270 = west
      sun_zenith: 0 = overhead, 90 = horizon
      sun_azimuth: same as panel
    """
    p_t = np.radians(panel_tilt)
    p_az = np.radians(panel_azimuth)
    s_z = np.radians(sun_zenith)
    s_az = np.radians(sun_azimuth)

    # Panel normal in cartesian (east, up, north)
    nx_p = np.sin(p_t) * np.sin(p_az)
    ny_p = np.cos(p_t)
    nz_p = np.sin(p_t) * np.cos(p_az)

    # Sun direction (origin → sun)
    nx_s = np.sin(s_z) * np.sin(s_az)
    ny_s = np.cos(s_z)
    nz_s = np.sin(s_z) * np.cos(s_az)

    # cos(angle) between panel normal and sun
    cos_a = nx_p * nx_s + ny_p * ny_s + nz_p * nz_s
    cos_a = np.maximum(cos_a, 0)

    # Power: cos angle × rated × system derate × optional bifacial
    p = cos_a * PANEL_WATT * SYSTEM_DERATE
    if bifacial:
        p *= (1 + BIFACIAL_BONUS)
    return p


# ============================================================================
# BED SUNLIT FRACTION (geometric raycaster — uses the actual 3D panel geometry)
# ============================================================================
def bed_sunlit_fraction(panel_tilt_deg, sun_azimuth_deg, sun_elevation_deg):
    """Geometric raycaster: project the panel onto the ground and intersect with bed.

    This is the ACCURATE shadow calculation, replacing the empirical formula.
    Uses the actual panel geometry from wattplot_params.py.
    """
    return compute_bed_sunlit_fraction(
        panel_tilt_deg, sun_azimuth_deg, sun_elevation_deg,
        BED_L_IN, BED_W_IN,
        PANEL['L_in'], PANEL['W_in'],
        HINGE_Y_IN, HINGE_Z_IN,
    )


# ============================================================================
# SCHEDULES
# ============================================================================
def schedule_static(times, tilt_deg, azimuth_deg=180.0):
    return np.full(len(times), tilt_deg), np.full(len(times), azimuth_deg)


def schedule_seasonal(times):
    """90° in winter (Oct-Mar), 35° in summer (Apr-Sep), south-facing."""
    month = times.month
    tilt = np.where(month.isin([10, 11, 12, 1, 2, 3]), 90.0, 35.0)
    az = np.full(len(times), 180.0)
    return tilt, az


def schedule_tracking_azimuth(times, sun_azimuth, base_tilt=35.0):
    """Single-axis azimuth tracker: panel always faces the sun horizontally.
    Tilt stays at base_tilt (35° for partial bed sun).
    """
    tilt = np.full(len(times), base_tilt)
    az = sun_azimuth.values.copy()
    return tilt, az


def schedule_dual_axis(times, sun_zenith, sun_azimuth):
    """Full dual-axis tracker: panel normal always points at sun.
    Maximum panel output but maximum actuator cycles.
    """
    # Tilt = 90 - sun_elevation (so panel normal is at sun's elevation)
    # Azimuth = sun_azimuth
    tilt = (90.0 - sun_zenith.values).clip(min=0)
    az = sun_azimuth.values.copy()
    return tilt, az


# ============================================================================
# DLI CALCULATION
# ============================================================================
def daily_dli_mol(par_w_m2, bed_sunlit, index, hours_per_sample=1.0):
    """
    Convert hourly PAR + bed sunlit fraction to daily DLI in mol/m²/day.

    1 W/m² of PAR ≈ 4.6 μmol/m²/s (PPFD conversion).
    Over 1 hour: PPFD × 3600 sec = 4.6 × 3600 μmol/m² = 16.56 mmol/m² = 0.01656 mol/m²
    DLI_daily = sum_hourly(PPFD × 3600 × bed_sunlit) / 1e6  (mol/m²/day)
    """
    ppfd = par_w_m2 * 4.6  # μmol/m²/s
    # Sum per day
    series = pd.Series(ppfd * 3600 * hours_per_sample * bed_sunlit / 1e6, index=index)
    return series.groupby(pd.Grouper(freq='D')).sum()


def yield_from_dli(dli_daily, dli_optimal=DLI_OPTIMAL, heat_stress_dli=DLI_HEAT_STRESS,
                   max_yield=MAX_YIELD_PER_PLANT, plants=PLANTS_IN_BED,
                   utilization=YIELD_UTILIZATION):
    """
    Estimate annual tomato yield from daily DLI.

    yield = max × min(1, DLI/DLI_optimal) × heat_stress × plants × utilization
    heat_stress = 1.0 if DLI < heat_stress else exp(-(DLI - heat_stress)/5)
    """
    # Per-day yield potential (kg/plant, summed over season's days)
    dli_arr = dli_daily.values if hasattr(dli_daily, 'values') else dli_daily

    def per_day_yield(dli):
        if dli < 1:
            return 0
        light_factor = min(1.0, dli / dli_optimal)
        if dli > heat_stress_dli:
            heat_factor = math.exp(-(dli - heat_stress_dli) / 5.0)
        else:
            heat_factor = 1.0
        # Per-day fraction of season's max yield (rough)
        # Season ~180 days at full production; scale by dli/optimal
        daily_fraction = light_factor * heat_factor / 180.0
        return max_yield * daily_fraction

    total_per_plant = sum(per_day_yield(d) for d in dli_arr)
    annual_kg = total_per_plant * plants * utilization
    return annual_kg


# ============================================================================
# ACTUATOR CYCLES
# ============================================================================
def count_actuator_cycles(tilt_history, threshold_deg=2.0):
    """Count number of significant tilt transitions in a tilt history."""
    if len(tilt_history) < 2:
        return 0
    diffs = np.abs(np.diff(tilt_history))
    transitions = (diffs > threshold_deg).sum()
    return int(transitions)


# ============================================================================
# RUN ALL SCHEDULES
# ============================================================================
def run_simulation():
    df = build_solar_timeseries()
    times = df.index

    schedules = {
        'Static 90° (bed sun)': schedule_static(times, 90.0),
        'Static 35° (max power)': schedule_static(times, 35.0),
        'Seasonal 90/35°': schedule_seasonal(times),
        'Azimuth tracking 35°': schedule_tracking_azimuth(times, df['sun_azimuth'], 35.0),
        'Dual-axis tracking': schedule_dual_axis(times, df['sun_zenith'], df['sun_azimuth']),
    }

    results = {}
    for name, (tilt, az) in schedules.items():
        # Panel output (only during daylight)
        power = panel_output_w(tilt, az, df['sun_zenith'].values, df['sun_azimuth'].values)
        power = power * df['daylight'].values
        # Annual kWh
        annual_kwh = power.sum() / 1000.0

        # Bed sunlit fraction (per-hour) — uses geometric raycaster
        bed_sun = np.array([
            bed_sunlit_fraction(t, az, el)
            for t, az, el in zip(tilt, df['sun_azimuth'].values, df['sun_elevation'].values)
        ])
        bed_sun = bed_sun * df['daylight'].values

        # Daily DLI
        dli_daily = daily_dli_mol(df['par'].values, bed_sun, df.index)
        dli_annual = dli_daily.sum()
        dli_mean = dli_daily.mean()
        dli_median = dli_daily.median()

        # Tomato yield
        yield_kg = yield_from_dli(dli_daily)

        # Actuator cycles (rough)
        # Static: 0 daily cycles + load-aware
        # Seasonal: 1 daily cycle (sunrise/sunset) + ~2 seasonal changeovers + load-aware
        # Tracking: continuous motion, ~50-100 small moves per day
        n_cycles_tilt = count_actuator_cycles(tilt)
        n_cycles_az = count_actuator_cycles(az)
        if 'Static' in name:
            cycles = LOAD_AWARE_CYCLES_PER_YEAR
        elif 'Seasonal' in name:
            cycles = 365 + 2 + LOAD_AWARE_CYCLES_PER_YEAR
        elif 'Azimuth' in name:
            # Tracking: ~100 moves per day for smooth azimuth tracking
            cycles = 100 * 365 + LOAD_AWARE_CYCLES_PER_YEAR
        elif 'Dual' in name:
            cycles = 200 * 365 + LOAD_AWARE_CYCLES_PER_YEAR
        else:
            cycles = n_cycles_tilt + n_cycles_az + LOAD_AWARE_CYCLES_PER_YEAR

        results[name] = {
            'tilt': tilt,
            'az': az,
            'power': power,
            'annual_kwh': annual_kwh,
            'bed_sun': bed_sun,
            'dli_daily': dli_daily,
            'dli_annual': dli_annual,
            'dli_mean': dli_mean,
            'dli_median': dli_median,
            'dli_min': dli_daily.min(),
            'dli_max': dli_daily.max(),
            'yield_kg': yield_kg,
            'actuator_cycles': cycles,
        }

    return results, df


# ============================================================================
# OUTPUT
# ============================================================================
def print_comparison(results):
    print()
    print('=' * 90)
    print(f'Wattplot v2 — Phoenix 2025 — Sun + Tilt Simulator')
    print('=' * 90)
    print()
    print(f'{"Schedule":<28} {"kWh":>7} {"DLI avg":>9} {"DLI winter":>11} '
          f'{"Tomato kg":>10} {"Cycles":>8}')
    print('-' * 90)
    for name, r in results.items():
        dli_winter = r['dli_daily'][r['dli_daily'].index.month.isin([12, 1, 2])].mean()
        print(f'{name:<28} {r["annual_kwh"]:>7.0f} {r["dli_mean"]:>9.1f} '
              f'{dli_winter:>11.1f} {r["yield_kg"]:>10.1f} {r["actuator_cycles"]:>8d}')
    print('-' * 90)
    print(f'Bed: 8 ft × 3.72 ft = {BED_AREA:.1f} sq ft, '
          f'Panel: 620W bifacial, {PLANTS_IN_BED} tomato plants')
    print(f'Tomato yield target: ~{MAX_YIELD_PER_PLANT * PLANTS_IN_BED * YIELD_UTILIZATION:.0f} kg/season at ideal DLI')
    print()


def plot_results(results, df, outdir):
    os.makedirs(outdir, exist_ok=True)

    # --- Plot 1: Annual DLI heatmap for one schedule (e.g. static 35°) ---
    r35 = results['Static 35° (max power)']
    dli_by_doy_hour = r35['dli_daily'].copy()
    # Reindex to full year
    full_year = pd.date_range(f'{YEAR}-01-01', f'{YEAR}-12-31', freq='D', tz=TZ)
    dli_by_doy_hour = dli_by_doy_hour.reindex(full_year).fillna(0)
    doy = dli_by_doy_hour.index.dayofyear

    # Average DLI by month for each schedule
    fig, ax = plt.subplots(figsize=(13, 6))
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_centers = [15, 45, 75, 105, 135, 165, 196, 227, 258, 288, 319, 349]

    colors = {
        'Static 90° (bed sun)': '#2c3e50',
        'Static 35° (max power)': '#e74c3c',
        'Seasonal 90/35°': '#27ae60',
        'Azimuth tracking 35°': '#8e44ad',
        'Dual-axis tracking': '#f39c12',
    }

    for name, r in results.items():
        monthly_dli = []
        for m in range(1, 13):
            d = r['dli_daily'][r['dli_daily'].index.month == m].mean()
            monthly_dli.append(d if not np.isnan(d) else 0)
        ax.plot(month_centers, monthly_dli, 'o-', color=colors.get(name, 'gray'),
                label=name, linewidth=2, markersize=6)

    ax.set_xticks(month_centers)
    ax.set_xticklabels(months)
    ax.set_xlabel("Month")
    ax.set_ylabel("Bed DLI (mol/m²/day)")
    ax.set_title(f"Wattplot v2 — Monthly average bed DLI by tilt schedule\n"
                 f"Phoenix AZ 33.45°N, 2025 clear-sky, 620W bifacial panel")
    ax.grid(True, alpha=0.3)
    ax.axhline(DLI_OPTIMAL, color='green', linestyle=':', alpha=0.7, label=f'DLI optimal for tomato ({DLI_OPTIMAL})')
    ax.axhline(DLI_HEAT_STRESS, color='red', linestyle=':', alpha=0.7, label=f'Heat stress threshold ({DLI_HEAT_STRESS})')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
    ax.set_ylim(0, 50)
    plt.tight_layout()
    out1 = os.path.join(outdir, 'sun_simulator_monthly_dli.png')
    plt.savefig(out1, dpi=130)
    plt.close()
    print(f"[sim] wrote {out1}")

    # --- Plot 2: Comparison scatter (kWh vs DLI) ---
    fig, ax = plt.subplots(figsize=(10, 8))
    for name, r in results.items():
        ax.scatter(r['annual_kwh'], r['dli_mean'],
                   s=200, color=colors.get(name, 'gray'),
                   label=name, edgecolors='black', linewidth=1.5, alpha=0.85)
        ax.annotate(f"  {r['yield_kg']:.0f} kg",
                    (r['annual_kwh'], r['dli_mean']),
                    fontsize=9, color=colors.get(name, 'gray'),
                    fontweight='bold')

    ax.set_xlabel("Annual panel energy (kWh)", fontsize=11)
    ax.set_ylabel("Average bed DLI (mol/m²/day)", fontsize=11)
    ax.set_title("Wattplot v2 — Tilt schedule comparison\n"
                 "Pareto-style scatter: top-right is best (more kWh + more bed sun)\n"
                 "Label = estimated annual tomato yield")
    ax.grid(True, alpha=0.3)
    ax.axhline(DLI_OPTIMAL, color='green', linestyle=':', alpha=0.5)
    ax.axvline(800, color='gray', linestyle=':', alpha=0.5)  # ~baseline
    ax.legend(loc='lower right', fontsize=9, framealpha=0.9)
    plt.tight_layout()
    out2 = os.path.join(outdir, 'sun_simulator_scatter.png')
    plt.savefig(out2, dpi=130)
    plt.close()
    print(f"[sim] wrote {out2}")

    # --- Plot 3: Daily DLI through the year (3 schedules) ---
    fig, ax = plt.subplots(figsize=(13, 6))
    days = np.arange(1, 366)
    for name in ['Static 90° (bed sun)', 'Static 35° (max power)', 'Azimuth tracking 35°']:
        r = results[name]
        dli_series = r['dli_daily'].reindex(full_year).fillna(0).values
        ax.plot(days, dli_series, color=colors[name], label=name, linewidth=1.5, alpha=0.85)
    ax.fill_between(days, 0, DLI_OPTIMAL, color='green', alpha=0.07, label=f'Below optimal ({DLI_OPTIMAL})')
    ax.fill_between(days, DLI_HEAT_STRESS, 50, color='red', alpha=0.07, label=f'Heat stress (>{DLI_HEAT_STRESS})')
    ax.set_xlabel("Day of year")
    ax.set_ylabel("Bed DLI (mol/m²/day)")
    ax.set_title("Wattplot v2 — Daily bed DLI through the year\n"
                 "Tomato DLI optimal range: green band; heat stress: red band")
    ax.set_xlim(1, 365)
    ax.set_ylim(0, 50)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
    plt.tight_layout()
    out3 = os.path.join(outdir, 'sun_simulator_daily_dli.png')
    plt.savefig(out3, dpi=130)
    plt.close()
    print(f"[sim] wrote {out3}")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, "..", "renders")
    os.makedirs(outdir, exist_ok=True)

    print("[sim] Building solar timeseries for Phoenix 2025 ...")
    results, df = run_simulation()

    print("[sim] Schedule comparison:")
    print_comparison(results)

    print("[sim] Generating plots ...")
    plot_results(results, df, outdir)

    print()
    print("[sim] Done.")
