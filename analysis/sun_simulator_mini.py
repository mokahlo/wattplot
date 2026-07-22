"""
Wattplot Mini — quick sun sim for the 10W 12V Newpowa panel.
Same Phoenix location + pvlib model as the full-size sun sim, but
parameterized for the mini panel.
"""
import os
import sys
import pandas as pd
import pvlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from wattplot_params import LOCATION, MINI, CROP  # noqa: E402

LAT, LON = LOCATION['latitude'], LOCATION['longitude']
TZ = LOCATION['timezone']
ALT = LOCATION['elevation_m']

# Mini panel
PANEL_W = MINI['panel_wattage']           # 10
PANEL_L = MINI['panel_L_in']              # 17.32
PANEL_W_IN = MINI['panel_W_in']           # 8.46
PANEL_T = MINI['panel_t_in']             # 0.71
SYSTEM_DERATE = 0.85
BIFACIAL_BONUS = 0.10

# Mini bed
BED_L_IN = MINI['bed_outer_L_in']         # 19
BED_W_IN = MINI['bed_outer_W_in']         # 10
BED_L = BED_L_IN / 12.0
BED_W = BED_W_IN / 12.0
BED_AREA = BED_L * BED_W                  # 1.319 sq ft

HINGE_Y_IN = MINI['bed_wall_h_in']        # 3.5
HINGE_Z_IN = BED_W_IN / 2.0              # 5

DLI_OPTIMAL = CROP['dli_optimal_mol']
DLI_HEAT_STRESS = CROP['dli_heat_stress_mol']


def run_mini_sim(tilt_deg=35, year=2025):
    """Quick mini sim at one tilt angle. Returns annual kWh and bed DLI."""
    times = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00",
                          freq="h", tz=TZ)

    solpos = pvlib.solarposition.get_solarposition(times, LAT, LON, ALT)
    csi = pvlib.clearsky.bird(
        solpos['apparent_zenith'], 1.0, ALT, 1.0,
        precipitable_water=1.0  # typical Phoenix atmospheric water vapor
    )

    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt_deg, surface_azimuth=180,
        solar_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        dni=csi["dni"], ghi=csi["ghi"], dhi=csi["dhi"], dni_extra=pvlib.irradiance.get_extra_radiation(times)
    )
    poa_global = poa["poa_global"].clip(lower=0)

    # Panel power (10W peak, bifacial +10%)
    efficiency = SYSTEM_DERATE * (1 + BIFACIAL_BONUS)
    panel_power_w = poa_global / 1000.0 * PANEL_W * efficiency   # W at any moment
    annual_kwh = panel_power_w.sum() / 1000.0                    # 8760 hours → kWh

    # Bed DLI (mol photons per m² per day)
    PAR = poa_global * 0.45   # umol/m²/s = W/m² × 4.57 / 2 ; simplified to *0.45
    daily_PAR = PAR.resample("D").sum() * 3600  # umol/m²/day = J/m²/day / (J/umol) = umol/m²/day
    DLI = daily_PAR / 1e6       # mol/m²/day (1e6 umol per mol)
    avg_dli = DLI.mean()
    winter_dli = DLI[DLI.index.month.isin([12, 1, 2])].mean()

    print(f"  Mini panel: {PANEL_W}W, {PANEL_L}\"x{PANEL_W_IN}\"")
    print(f"  Bed: {BED_L:.2f}ft x {BED_W:.2f}ft = {BED_AREA:.2f} sq ft")
    print(f"  Tilt: {tilt_deg}°")
    print(f"  Annual yield: {annual_kwh:.2f} kWh")
    print(f"  Daily peak (clear noon summer): {panel_power_w.max():.1f} W")
    print(f"  Bed DLI avg: {avg_dli:.1f} mol/m²/day (optimal {DLI_OPTIMAL}, heat stress {DLI_HEAT_STRESS})")
    print(f"  Bed DLI winter (Dec-Feb): {winter_dli:.1f} mol/m²/day")
    return {
        "annual_kwh": annual_kwh,
        "avg_dli": avg_dli,
        "winter_dli": winter_dli,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Wattplot Mini — Phoenix 2025 — Sun + Tilt Sim")
    print("=" * 60)
    for tilt in (0, 35, 90):
        print(f"\n--- Tilt: {tilt}° ---")
        run_mini_sim(tilt_deg=tilt)
