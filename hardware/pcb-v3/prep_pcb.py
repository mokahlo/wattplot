#!/usr/bin/env python3
"""
prep_pcb.py — Programmatic PCB prep after placement, before autoroute.

Steps (in order):
  1. Add GND copper pour on B.Cu (full ground plane, 0.5mm clearance)
  2. Add 3V3 pour on F.Cu (flood fill around 3.3V nets)
  3. Set zone-to-pad clearance
  4. Save
  5. Run DRC
  6. Generate manufacturing outputs:
     - Gerbers (one file per layer)
     - Drill file (Excellon)
     - Position file (for JLCPCB SMT)
     - BOM (CSV)
  7. (Optional) Export Specctra DSN for FreeRouting

Run order (full pipeline):
  build_schematic.py → init_layout.py → import_schematic.py →
  place_components.py → prep_pcb.py → [FreeRouting] → export_dsn.py import
"""

import sys
from pathlib import Path
import pcbnew

ROOT = Path(__file__).parent
PCB = ROOT / "wattplot-v3.kicad_pcb"
SCH = ROOT / "wattplot-v3.kicad_sch"
EXPORTS = ROOT / "exports"
GERBERS = ROOT / "gerbers"


def mm(x):
    return int(x * 1_000_000)


def add_zone(board, net_name, layer, corners, clearance_mm=0.3, min_width_mm=0.25):
    """Add a filled copper zone on a layer connected to net_name.

    corners: list of (x_mm, y_mm) tuples defining the polygon.
    """
    # Find or create the net
    net = board.FindNet(net_name)
    if net is None or net.GetNet() == 0:
        # Try the dict-style
        try:
            nets_dict = board.GetNetsByName()
            if net_name in nets_dict:
                net = nets_dict[net_name]
            else:
                print(f"  [WARN] Net '{net_name}' not found on board, skipping zone")
                return None
        except Exception:
            print(f"  [WARN] Net '{net_name}' not found on board, skipping zone")
            return None

    # Create zone
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(net)

    # Outline
    outline = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in corners:
        outline.Append(pcbnew.VECTOR2I(mm(x), mm(y)))
    outline.SetClosed(True)
    zone.SetOutline(outline)

    # Pad connections: thermal reliefs for SMD
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)  # spokes
    zone.SetThermalReliefSpokeWidth(mm(0.5))
    zone.SetThermalReliefGap(mm(0.3))

    # Clearances
    zone.SetClearance(mm(clearance_mm))
    zone.SetMinWidth(mm(min_width_mm))
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_SMALLEST)  # fill everything

    # Hatch
    zone.SetHatch(pcbnew.ZONE_HATCH_PATTERN_45_DEG, mm(0.508))

    board.Add(zone)
    return zone


def main():
    if not PCB.exists():
        print(f"[ERR] {PCB} not found")
        return 1
    if not SCH.exists():
        print(f"[ERR] {SCH} not found")
        return 1

    board = pcbnew.LoadBoard(str(PCB))
    print(f"[INFO] Loaded {PCB.name}")
    print(f"[INFO] Found {board.GetFootprints().size() if hasattr(board.GetFootprints(), 'size') else len(list(board.GetFootprints()))} footprints")

    # Board outline corners (80x60mm) — match Edge.Cuts
    corners = [
        (0, 0), (80, 0), (80, 60), (0, 60),
    ]
    # Inset 1mm so the pour doesn't touch the board edge
    inset = 1.0
    inner = [
        (inset, inset), (80 - inset, inset),
        (80 - inset, 60 - inset), (inset, 60 - inset),
    ]

    print()
    print("[STEP 1/6] Adding GND copper pour (B.Cu, full plane)...")
    if add_zone(board, "GND", pcbnew.B_Cu, inner):
        print("  [OK] GND zone added")

    print()
    print("[STEP 2/6] Adding 3V3 power pour (F.Cu)...")
    if add_zone(board, "+3V3", pcbnew.F_Cu, inner):
        print("  [OK] 3V3 zone added")

    print()
    print("[STEP 3/6] Adding +5V pour (B.Cu)...")
    if add_zone(board, "+5V", pcbnew.B_Cu, inner):
        print("  [OK] +5V zone added")

    # Save before refilling
    pcbnew.SaveBoard(str(PCB), board)
    print()
    print(f"[OK] Saved {PCB.name}")

    # Step 4: Fill zones (compute copper)
    print()
    print("[STEP 4/6] Filling copper zones...")
    try:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        print("  [OK] Zones filled")
    except Exception as e:
        print(f"  [WARN] Zone fill failed: {e}")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"[OK] Saved {PCB.name}")

    # Step 5: DRC
    print()
    print("[STEP 5/6] Running design rule check...")
    drc_out = EXPORTS / "drc.txt"
    EXPORTS.mkdir(exist_ok=True)
    # Use the python API for DRC
    try:
        drc = pcbnew.DRC(board)
        drc.Run()
        # Get violations count
        violations = list(drc.GetViolations())
        print(f"  [OK] DRC: {len(violations)} violations")
        with open(drc_out, "w") as f:
            f.write(f"DRC: {len(violations)} violations\n")
            for v in violations[:20]:
                f.write(f"  {v}\n")
        if len(violations) > 20:
            f.write(f"  ... and {len(violations) - 20} more\n")
    except Exception as e:
        print(f"  [WARN] DRC failed: {e}")
        print("  (Run kicad-cli pcb drc manually if needed)")

    # Step 6: Manufacturing outputs
    print()
    print("[STEP 6/6] Generating manufacturing files...")
    GERBERS.mkdir(exist_ok=True)

    # Gerbers (use kicad-cli since it has the proper output)
    # The Python API doesn't have a direct gerber export; use kicad-cli
    import subprocess
    kicad_cli = Path(r"C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe")

    def run_kicad(args):
        try:
            r = subprocess.run([str(kicad_cli)] + args, capture_output=True, text=True, timeout=60)
            return r.returncode == 0, r.stdout + r.stderr
        except Exception as e:
            return False, str(e)

    # Gerbers
    ok, msg = run_kicad(["pcb", "export", "gerbers", "--output", str(GERBERS) + "\\", str(PCB)])
    if ok:
        gfiles = sorted(GERBERS.glob("*.gbr"))
        print(f"  [OK] {len(gfiles)} gerber files in {GERBERS.name}/")
    else:
        print(f"  [WARN] Gerber export failed: {msg[:200]}")

    # Drill
    ok, msg = run_kicad(["pcb", "export", "drill", "--output", str(GERBERS) + "\\", str(PCB)])
    if ok:
        dfiles = sorted(GERBERS.glob("*.drl")) + sorted(GERBERS.glob("*.xln"))
        print(f"  [OK] {len(dfiles)} drill files")
    else:
        print(f"  [WARN] Drill export failed: {msg[:200]}")

    # Position (for JLCPCB SMT)
    pos_out = EXPORTS / "pos.csv"
    ok, msg = run_kicad(["pcb", "export", "pos", "--format", "csv", "--output", str(pos_out), str(PCB)])
    if ok:
        print(f"  [OK] Position: {pos_out.name} ({pos_out.stat().st_size} bytes)")
    else:
        print(f"  [WARN] Position export failed: {msg[:200]}")

    # BOM (from schematic)
    bom_out = EXPORTS / "bom.csv"
    ok, msg = run_kicad(["sch", "export", "bom", "--output", str(bom_out), str(SCH)])
    if ok:
        print(f"  [OK] BOM: {bom_out.name} ({bom_out.stat().st_size} bytes)")
    else:
        print(f"  [WARN] BOM export failed: {msg[:200]}")

    # Also export the unrouted DSN for FreeRouting
    dsn_out = EXPORTS / "wattplot.dsn"
    if pcbnew.ExportSpecctraDSN(board, str(dsn_out)):
        print(f"  [OK] DSN (unrouted): {dsn_out.name} ({dsn_out.stat().st_size} bytes)")

    print()
    print("=" * 60)
    print("PCB prep complete. Summary:")
    print(f"  Footprints: {len(list(board.GetFootprints()))}")
    print(f"  Zones:      {len(list(board.Zones()))}")
    print(f"  Tracks:     {len(list(board.GetTracks()))}")
    print()
    print("Manufacturing files in:")
    print(f"  {GERBERS}/ (gerbers + drill)")
    print(f"  {EXPORTS}/ (position, BOM, DRC report, DSN)")
    print()
    print("Next:")
    print("  1. Authorize FreeRouting (Java, free):")
    print("     https://github.com/freerouting/freerouting/releases")
    print("  2. Open exports/wattplot.dsn → Routing → Autoroute")
    print("  3. Export as exports/wattplot.ses")
    print("  4. Import: python3 export_dsn.py import")
    print("  5. Re-run prep_pcb.py to regenerate gerbers with the routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
