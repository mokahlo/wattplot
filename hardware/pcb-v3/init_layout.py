#!/usr/bin/env python3
"""
init_layout.py — Set up the PCB file with board outline, design rules,
layer stackup, mounting holes, and netlist import. Run from the
KiCad 10 python interpreter:

  & 'C:/Users/mokah/AppData/Local/Programs/KiCad/10.0/bin/python.exe' ^
    'C:/dev/wattplot/hardware/pcb-v3/init_layout.py'

After running, open wattplot-v3.kicad_pro in the KiCad GUI to do the
interactive component placement and routing.
"""

import os
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).parent
PROJ = ROOT / "wattplot-v3.kicad_pro"
PCB_OUT = ROOT / "wattplot-v3.kicad_pcb"
NETLIST = ROOT / "exports" / "wattplot-v3.net"

# Board dimensions (mm)
WIDTH = 80.0
HEIGHT = 60.0
CORNER_R = 2.0  # rounded corners

# Mounting holes (4× M3, 3.2mm pad, near corners)
MOUNT_OFFSET = 3.5  # mm from edge
MOUNT_DRILL = 3.2   # mm
MOUNT_PAD = 6.0     # mm annular ring


def mm_to_nm(mm):
    return int(mm * 1_000_000)


def main():
    # 1. Create / load the PCB
    if PCB_OUT.exists():
        print(f"[INFO] Loading existing {PCB_OUT.name}")
        board = pcbnew.LoadBoard(str(PCB_OUT))
    else:
        print(f"[INFO] Creating new {PCB_OUT.name}")
        board = pcbnew.NewBoard(str(PCB_OUT))

    # project init is automatic when loading from .kicad_pro project file

    # 2. Set up layer stackup (2-layer)
    # F.Cu (top) + B.Cu (bottom) only — minimal stackup
    board.SetCopperLayerCount(2)

    # 3. Draw board outline on Edge.Cuts
    edge_layer = pcbnew.Edge_Cuts
    pts = []
    # Rounded rectangle: 4 corner arcs + 4 straight edges
    # Use straight lines for simplicity; rounded corners can be added
    # manually in GUI
    pts.append(pcbnew.VECTOR2I(mm_to_nm(0), mm_to_nm(0)))
    pts.append(pcbnew.VECTOR2I(mm_to_nm(WIDTH), mm_to_nm(0)))
    pts.append(pcbnew.VECTOR2I(mm_to_nm(WIDTH), mm_to_nm(HEIGHT)))
    pts.append(pcbnew.VECTOR2I(mm_to_nm(0), mm_to_nm(HEIGHT)))
    pts.append(pcbnew.VECTOR2I(mm_to_nm(0), mm_to_nm(0)))
    for i in range(len(pts) - 1):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(edge_layer)
        seg.SetStart(pts[i])
        seg.SetEnd(pts[i + 1])
        seg.SetWidth(mm_to_nm(0.1))
        board.Add(seg)

    # 4. Add 4× M3 mounting holes
    mount_positions = [
        (MOUNT_OFFSET, MOUNT_OFFSET),
        (WIDTH - MOUNT_OFFSET, MOUNT_OFFSET),
        (WIDTH - MOUNT_OFFSET, HEIGHT - MOUNT_OFFSET),
        (MOUNT_OFFSET, HEIGHT - MOUNT_OFFSET),
    ]
    for x, y in mount_positions:
        # Mounting holes are circles on Edge.Cuts (no plating, no pad)
        hole = pcbnew.PCB_SHAPE(board)
        hole.SetShape(pcbnew.SHAPE_T_CIRCLE)
        hole.SetLayer(edge_layer)
        hole.SetCenter(pcbnew.VECTOR2I(mm_to_nm(x), mm_to_nm(y)))
        hole.SetWidth(mm_to_nm(0.1))
        hole.SetRadius(mm_to_nm(MOUNT_DRILL / 2))
        board.Add(hole)
    print(f"[OK] Added 4× M3 mounting holes")

    # 5. Design rules — JLCPCB-friendly
    # 6 mil trace / 6 mil space (1 oz) is the safe default.
    # 0.3mm via drill / 0.6mm via pad is a good JLCPCB default.
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm_to_nm(0.15)        # 6 mil
    ds.m_TrackMinClearance = mm_to_nm(0.15)    # 6 mil
    ds.m_ViaMinSize = mm_to_nm(0.6)            # 0.6mm via pad
    ds.m_ViaMinDrill = mm_to_nm(0.3)           # 0.3mm via drill
    ds.m_MinThroughDrill = mm_to_nm(0.3)
    ds.m_MinHoleClearance = mm_to_nm(0.25)

    # Net classes — m_NetSettings is the new path
    ns = ds.m_NetSettings
    nc = ns.GetDefaultNetclass()
    nc.SetClearance(mm_to_nm(0.15))
    nc.SetTrackWidth(mm_to_nm(0.25))           # 10 mil default
    nc.SetViaDiameter(mm_to_nm(0.6))
    nc.SetViaDrill(mm_to_nm(0.3))
    # Power net class: 12V / 5V / VM (high current)
    pwr = pcbnew.NETCLASS("Power")
    pwr.SetClearance(mm_to_nm(0.3))
    pwr.SetTrackWidth(mm_to_nm(0.5))           # 20 mil
    pwr.SetViaDiameter(mm_to_nm(0.8))
    pwr.SetViaDrill(mm_to_nm(0.4))
    ns.SetNetclass(pwr.GetName(), pwr)  # adds to netclass list
    print(f"[OK] Design rules set: 6 mil min, 0.3mm via, 'Power' netclass 0.5mm")

    # 6. Save the board
    pcbnew.SaveBoard(str(PCB_OUT), board)
    print(f"[OK] Saved {PCB_OUT}")

    # 7. Print summary
    print()
    print("=" * 60)
    print(f"Board: {WIDTH}×{HEIGHT} mm, 2-layer, 1.6mm FR4")
    print(f"Layer count: {board.GetCopperLayerCount()}")
    print(f"Footprints: {board.GetFootprints().size() if hasattr(board.GetFootprints(), 'size') else 'N/A'}")
    print()
    print("Next steps:")
    print("  1. Open wattplot-v3.kicad_pro in KiCad GUI")
    print("  2. Tools → Update Schematic from PCB (no-op, schematic is source of truth)")
    print("  3. File → Import → Netlist... (select exports/wattplot-v3.net if generated)")
    print("  4. Or just open the schematic then switch to PCB editor — footprints")
    print("     are already linked")
    print("  5. Place components: start with ESP32 (antenna top-center, away from")
    print("     mounting holes), then connectors (long edge, opposite the antenna),")
    print("     then power tree, then H-bridges near their output connectors")
    print("  6. Route: power first (12V → 5V → 3.3V), then signal")


if __name__ == "__main__":
    main()
