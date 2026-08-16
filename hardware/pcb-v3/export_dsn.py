#!/usr/bin/env python3
"""
export_dsn.py — Export the PCB to Specctra DSN format for FreeRouting.

KiCad 10's kicad-cli doesn't have a `specctra` subcommand, but the Python
API does. This script bridges the gap.

After exporting, run FreeRouting (Java) on the .dsn file, then import
the .ses back via:

  kicad-cli pcb import specctra exports/wattplot.ses wattplot-v3.kicad_pcb

Or via this script: `python3 export_dsn.py import exports/wattplot.ses`

  & 'C:/Users/mokah/AppData/Local/Programs/KiCad/10.0/bin/python.exe' ^
    'C:/dev/wattplot/hardware/pcb-v3/export_dsn.py'
"""

import sys
from pathlib import Path
import pcbnew

ROOT = Path(__file__).parent
PCB = ROOT / "wattplot-v3.kicad_pcb"
DSN = ROOT / "exports" / "wattplot.dsn"
SES = ROOT / "exports" / "wattplot.ses"


def main():
    if not PCB.exists():
        print(f"[ERR] {PCB} not found")
        return 1

    board = pcbnew.LoadBoard(str(PCB))
    print(f"[INFO] Loaded {PCB.name}")

    if len(sys.argv) > 1 and sys.argv[1] == "import":
        if not SES.exists():
            print(f"[ERR] {SES} not found")
            return 1
        print(f"[INFO] Importing {SES.name}...")
        ok = pcbnew.ImportSpecctraSES(str(SES), board)
        if ok:
            pcbnew.SaveBoard(str(PCB), board)
            print(f"[OK] Imported and saved {PCB.name}")
        else:
            print(f"[ERR] Import failed")
        return 0 if ok else 1

    # Export
    DSN.parent.mkdir(exist_ok=True)
    print(f"[INFO] Exporting to {DSN.relative_to(ROOT)}...")
    ok = pcbnew.ExportSpecctraDSN(board, str(DSN))
    if ok:
        size = DSN.stat().st_size
        print(f"[OK] Exported {size:,} bytes")
        print()
        print("Next:")
        print("  1. Download FreeRouting: https://github.com/freerouting/freerouting/releases")
        print("  2. Open the DSN file (Java WebStart or downloaded JAR)")
        print("  3. Routing → Autoroute")
        print("  4. File → Export Specctra Session File → save as exports/wattplot.ses")
        print("  5. Back here: import the SES with:")
        print("     python3 export_dsn.py import")
        return 0
    else:
        print(f"[ERR] Export failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
