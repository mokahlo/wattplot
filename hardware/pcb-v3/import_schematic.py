#!/usr/bin/env python3
"""
import_schematic.py — Replicate KiCad's "Update PCB from Schematic (F8)".

Reads the schematic S-expr, extracts components with their footprints,
loads each footprint from the KiCad library, and adds it to the PCB.
This bypasses the broken kicad-cli netlist export (which returns empty
when the lib_symbols section is empty) and lets us run the full
schematic → PCB flow without touching the GUI.

Run after init_layout.py. Then run place_components.py.

  & 'C:/Users/mokah/AppData/Local/Programs/KiCad/10.0/bin/python.exe' ^
    'C:/dev/wattplot/hardware/pcb-v3/import_schematic.py'
"""

import re
import sys
from pathlib import Path
import pcbnew

ROOT = Path(__file__).parent
SCH = ROOT / "wattplot-v3.kicad_sch"
PCB = ROOT / "wattplot-v3.kicad_pcb"


def extract_blocks(s, head):
    """Yield (body) for each top-level (head ...) block in s."""
    i = 0
    n = len(s)
    while i < n:
        i = s.find(f"({head}", i)
        if i < 0:
            return
        depth = 0
        start = i
        while i < n:
            c = s[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    yield s[start:i + 1]
                    break
            i += 1


def find_property(body, key):
    """Find (property "key" "value" ...) in a s-expr body."""
    pat = rf'\(property\s+"{re.escape(key)}"\s+"([^"]*)"'
    m = re.search(pat, body)
    return m.group(1) if m else ""


def find_kv(body, key):
    pat = rf'\({re.escape(key)}\s+"([^"]*)"\)'
    m = re.search(pat, body)
    if m:
        return m.group(1)
    pat = rf'\({re.escape(key)}\s+([^\s)]+)\)'
    m = re.search(pat, body)
    return m.group(1) if m else ""


def parse_schematic(sch_path):
    """Return list of components with Reference, Value, Footprint, lib_id."""
    text = sch_path.read_text(encoding="utf-8")
    components = []
    for body in extract_blocks(text, "symbol"):
        # Skip sub-symbols (instances like unit A, power symbols)
        ref = find_property(body, "Reference")
        if not ref:
            continue
        # Skip duplicates (e.g. multi-unit symbol's second unit)
        # We keep the first occurrence by checking if Reference already seen
        if any(c["ref"] == ref for c in components):
            continue
        value = find_property(body, "Value")
        fp = find_property(body, "Footprint")
        lib_id = find_kv(body, "lib_id")
        components.append({
            "ref": ref, "value": value, "footprint": fp, "lib_id": lib_id,
        })
    return components


def load_footprint(board, fp_spec, ref=None):
    """Load a footprint given 'Library:Footprint' spec, return FOOTPRINT or None.
    ref is the component reference (e.g. 'U5') used to override mis-mapped
    footprints in the schematic.
    """
    if ":" not in fp_spec:
        print(f"  [WARN] No library in '{fp_spec}'")
        return None
    lib_name, fp_name = fp_spec.split(":", 1)
    # Footprint overrides — schematic assigns wrong footprint for some refs.
    # Map ref → (fp_lib, fp_name)
    FOOTPRINT_OVERRIDES = {
        # DRV8871 is HTSSOP-28
        "U5": ("Package_SO", "HTSSOP-28-1EP_4.4x9.7mm_P0.65mm_EP3.4x9.5mm"),
        "U6": ("Package_SO", "HTSSOP-28-1EP_4.4x9.7mm_P0.65mm_EP3.4x9.5mm"),
        # J1 is the XT60 battery connector (custom), not USB-C
        "J1": ("Connector_AMASS", "AMASS_XT60PW-M_1x02_P7.20mm_Horizontal"),
        # Switches — 6x6 tactile
        "SW1": ("Button_Switch_SMD", "SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm"),
        "SW2": ("Button_Switch_SMD", "SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm"),
        # JST connectors — schematic uses PH-K series, library has XH-A
        "J3": ("Connector_JST", "JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"),
        "J4": ("Connector_JST", "JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"),
        "J5": ("Connector_JST", "JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical"),
        "J7": ("Connector_JST", "JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"),
        "J8": ("Connector_JST", "JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"),
    }
    if ref in FOOTPRINT_OVERRIDES:
        fp_lib, fp_name = FOOTPRINT_OVERRIDES[ref]
    else:
        # Map symbol library names → footprint library names
        LIB_MAP = {
            "Switch": "Button_Switch_SMD",
            "PinHeader_2.54mm": "Connector_PinHeader_2.54mm",
            "Connector": "Connector_USB",  # only used for J1/XT60 mismatch
            "RF_Module": "RF_Module",
            "LED_SMD": "LED_SMD",
            "Inductor_SMD": "Inductor_SMD",
            "Resistor_SMD": "Resistor_SMD",
            "Capacitor_SMD": "Capacitor_SMD",
            "Connector_JST": "Connector_JST",
            "Package_SO": "Package_SO",
            "Package_TO_SOT_SMD": "Package_TO_SOT_SMD",
            "TestPoint": "TestPoint",
        }
        fp_lib = LIB_MAP.get(lib_name, lib_name)
    # Find the .pretty directory
    kicad_fp_root = Path(r"C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints")
    pretty_dir = kicad_fp_root / f"{fp_lib}.pretty"
    if not pretty_dir.exists():
        print(f"  [WARN] Library dir not found: {pretty_dir}")
        return None
    # Use the static FootprintLoad (top-level function in pcbnew)
    try:
        fp = pcbnew.FootprintLoad(str(pretty_dir), fp_name)
        return fp
    except Exception as e:
        print(f"  [ERR] Failed to load {fp_spec}: {e}")
        return None


def main():
    if not SCH.exists():
        print(f"[ERR] Schematic not found: {SCH}")
        print("       Run build_schematic.py first")
        return 1
    if not PCB.exists():
        print(f"[ERR] PCB not found: {PCB}")
        print("       Run init_layout.py first")
        return 1

    # Parse schematic
    components = parse_schematic(SCH)
    print(f"[INFO] Parsed {len(components)} components from schematic")

    with_fp = sum(1 for c in components if c["footprint"])
    print(f"[INFO] {with_fp}/{len(components)} have footprints assigned")
    no_fp = [c for c in components if not c["footprint"]]
    if no_fp:
        print(f"  [WARN] No footprint: {', '.join(c['ref'] for c in no_fp[:10])}")

    # Load PCB
    board = pcbnew.LoadBoard(str(PCB))
    print(f"[INFO] Loaded {PCB.name}")

    # Check what's already on the board (idempotency)
    existing = {fp.GetReference() for fp in board.GetFootprints()}
    if existing:
        print(f"[INFO] Board already has {len(existing)} footprints; adding only missing ones")

    # Add each component
    added = 0
    failed = []
    for c in components:
        if c["ref"] in existing:
            continue
        if not c["footprint"]:
            failed.append(c["ref"])
            continue
        fp = load_footprint(board, c["footprint"], ref=c["ref"])
        if fp is None:
            failed.append(c["ref"])
            continue
        # Each FootprintLoad returns a shared reference; we need a fresh instance
        new_fp = pcbnew.FOOTPRINT(board)
        new_fp.CopyFrom(fp)
        # Set the reference (CopyFrom doesn't always copy it)
        new_fp.SetReference(c["ref"])
        if c["value"]:
            new_fp.SetValue(c["value"])
        # Place at origin (will be moved by place_components.py)
        new_fp.SetPosition(pcbnew.VECTOR2I(0, 0))
        board.Add(new_fp)
        added += 1

    print(f"[OK] Added {added} footprints to PCB")
    if failed:
        print(f"[WARN] Failed to add: {', '.join(failed)}")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"[OK] Saved {PCB.name}")
    print()
    print("Next: run place_components.py to position the components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
