#!/usr/bin/env python3
"""
place_components.py — Place all 46 components in the PCB by subsystem.

Run AFTER running `Tools → Update PCB from Schematic (F8)` in the KiCad
GUI once (to seed the PCB with components and nets). Then close KiCad
and run this script.

Layout philosophy (80×60mm board, top side only):
- Power tree on the LEFT (J1 12V in → buck → 3.3V LDO)
- ESP32-S3 at TOP-CENTER (antenna at top, away from mounting holes)
- Connectors on the BOTTOM edge (cables exit downward, opposite the antenna)
- DRV8871 H-bridges near their output connectors
- INA219s near the shunts they measure
- Sensor connectors (J5, J6) on the bottom edge
- USB-C (J7) on a short edge, near ESP32

After placement, run FreeRouting for the actual traces.

  & 'C:/Users/mokah/AppData/Local/Programs/KiCad/10.0/bin/python.exe' ^
    'C:/dev/wattplot/hardware/pcb-v3/place_components.py'
"""

from pathlib import Path
import pcbnew

ROOT = Path(__file__).parent
PCB = ROOT / "wattplot-v3.kicad_pcb"


def mm(x):
    return int(x * 1_000_000)


# Placement map: refdes -> (x_mm, y_mm, rotation_deg, side)
# All positions are component CENTERS. Rotation is in degrees (clockwise).
# Side is 'top' (F.Cu) or 'bot' (B.Cu).
PLACEMENT = {
    # ----- Power tree (left side, top-to-bottom flow) -----
    "J1":  (5.0,  8.0, 0, "top"),     # XT60 battery input
    "F1":  (12.0, 8.0, 0, "top"),     # 3A PTC fuse
    "D1":  (18.0, 8.0, 0, "top"),     # SMBJ16A TVS
    "U1":  (28.0, 8.0, 0, "top"),     # MP1584EN buck
    "L1":  (34.0, 5.0, 0, "top"),     # 4.7µH inductor
    "C1":  (28.0, 14.0, 0, "top"),    # 22µF/25V Cin
    "C2":  (40.0, 8.0, 0, "top"),     # 22µF/10V Cout
    "U2":  (50.0, 8.0, 0, "top"),     # AMS1117-3.3 LDO
    "C3":  (50.0, 14.0, 0, "top"),    # 10µF/10V Cin
    "C4":  (60.0, 8.0, 0, "top"),     # 22µF/10V Cout

    # ----- ESP32-S3 (top center) -----
    "U3":  (40.0, 30.0, 0, "top"),    # ESP32-S3-WROOM-1, antenna up
    "J2":  (40.0, 45.0, 0, "top"),    # USB-C receptacle
    "U4":  (52.0, 45.0, 0, "top"),    # USBLC6-2P6 ESD
    "SW1": (52.0, 38.0, 0, "top"),    # Reset button
    "SW2": (28.0, 38.0, 0, "top"),    # Boot button
    "D2":  (28.0, 45.0, 0, "top"),    # Status LED
    "R1":  (28.0, 50.0, 0, "top"),    # 1k LED series
    "R2":  (52.0, 50.0, 0, "top"),    # 5.1k CC1 pull-down
    "R3":  (60.0, 45.0, 0, "top"),    # 5.1k CC2 pull-down
    "R4":  (60.0, 50.0, 0, "top"),    # 4.7k SDA pull-up
    "R5":  (20.0, 50.0, 0, "top"),    # 4.7k SCL pull-up

    # ----- 2x DRV8871 H-bridges (right side, near their outputs) -----
    "U5":  (60.0, 22.0, 0, "top"),    # DRV8871 actuator
    "U6":  (60.0, 30.0, 0, "top"),    # DRV8871 solenoid
    "C5":  (60.0, 16.0, 0, "top"),    # 100µF VM bulk cap
    "C6":  (60.0, 36.0, 0, "top"),    # 100µF VM bulk cap
    "R6":  (52.0, 22.0, 0, "top"),    # 1k ILIM actuator
    "R7":  (52.0, 30.0, 0, "top"),    # 1k ILIM solenoid
    "R8":  (52.0, 16.0, 0, "top"),    # 10k nFAULT pull-up actuator
    "R9":  (52.0, 36.0, 0, "top"),    # 10k nFAULT pull-up solenoid

    # ----- 2x INA219 (center) -----
    "U7":  (15.0, 22.0, 0, "top"),    # INA219 panel (0x41)
    "U8":  (15.0, 30.0, 0, "top"),    # INA219 actuator (0x40)
    "R10": (10.0, 22.0, 0, "top"),    # 0.1Ω panel shunt
    "R11": (10.0, 30.0, 0, "top"),    # 0.1Ω actuator shunt

    # ----- Connectors (bottom edge) -----
    "J3":  (12.0, 55.0, 0, "top"),    # Actuator motor
    "J4":  (24.0, 55.0, 0, "top"),    # Solenoid valve
    "J5":  (40.0, 55.0, 0, "top"),    # 1-Wire sensors
    "J6":  (52.0, 55.0, 0, "top"),    # Soil moisture
    "R12": (40.0, 50.0, 0, "top"),    # 4.7k 1-Wire pull-up

    # ----- Test points (left edge) -----
    "TP1": (3.0,  8.0, 0, "top"),     # +12V
    "TP2": (3.0, 22.0, 0, "top"),     # +5V
    "TP3": (3.0, 30.0, 0, "top"),     # +3.3V
    "TP4": (3.0, 45.0, 0, "top"),     # GND
    "TP5": (3.0, 55.0, 0, "top"),     # VBAT
}


def main():
    if not PCB.exists():
        print(f"[ERR] {PCB} not found. Run init_layout.py first, or open the")
        print("      project in KiCad and use Tools → Update PCB from Schematic (F8)")
        return 1

    board = pcbnew.LoadBoard(str(PCB))
    print(f"[INFO] Loaded {PCB.name}")

    # Get all current footprints
    all_fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    print(f"[INFO] Found {len(all_fps)} footprints on board")

    placed = 0
    missing = []
    for ref, (x, y, rot, side) in PLACEMENT.items():
        if ref not in all_fps:
            missing.append(ref)
            continue
        fp = all_fps[ref]
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientation(rot * 10)  # tenths of degrees
        if side == "bot":
            fp.SetLayer(pcbnew.B_Cu)
        else:
            fp.SetLayer(pcbnew.F_Cu)
        placed += 1

    print(f"[OK] Placed {placed} components")

    if missing:
        print(f"[WARN] {len(missing)} refs in PLACEMENT map but not on board:")
        print(f"       {', '.join(missing)}")
        print(f"       (Re-run Tools → Update PCB from Schematic if these are real)")

    # Show components on board but not in placement map
    on_board = set(all_fps.keys())
    in_map = set(PLACEMENT.keys())
    extra = on_board - in_map
    if extra:
        print(f"[WARN] {len(extra)} components on board but not in PLACEMENT map:")
        for ref in sorted(extra):
            fp = all_fps[ref]
            print(f"       {ref} (currently at {fp.GetPosition().x/1e6:.1f}, {fp.GetPosition().y/1e6:.1f})")
        print(f"       Add them to PLACEMENT or remove from board")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"[OK] Saved {PCB.name}")
    print()
    print("Next: open in KiCad GUI to review placement, then export DSN for FreeRouting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
