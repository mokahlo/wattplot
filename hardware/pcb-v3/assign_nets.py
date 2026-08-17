#!/usr/bin/env python3
"""
assign_nets.py — Parse the schematic and assign nets to footprint pads.

The schematic uses global labels at pin positions (no wires), so the
algorithm is simple: for each global label, find the symbol pin at the
same (x, y) position and assign the pad with the matching number to
the labeled net.

After this, prep_pcb.py will find the GND/+3V3/+5V nets and add the
copper pours.

This replaces the GUI F8 (Update PCB from Schematic) step.

  & 'C:/Users/mokah/AppData/Local/Programs/KiCad/10.0/bin/python.exe' ^
    'C:/dev/wattplot/hardware/pcb-v3/assign_nets.py'
"""

import re
from pathlib import Path
import pcbnew

ROOT = Path(__file__).parent
SCH = ROOT / "wattplot-v3.kicad_sch"
PCB = ROOT / "wattplot-v3.kicad_pcb"


def extract_blocks(s, head):
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
    m = re.search(rf'\(property\s+"{re.escape(key)}"\s+"([^"]+)"', body)
    return m.group(1) if m else ""


def find_pins(body):
    """Yield (pin_name, x, y, angle) for each pin in a symbol block.
    KiCad 10 pin format: (pin "name" (uuid "...") (at X Y ANGLE) (...type...))
    """
    for pin_block in extract_blocks(body, "pin"):
        m = re.search(r'\(pin\s+"([^"]+)"', pin_block)
        name = m.group(1) if m else ""
        m = re.search(r'\(at\s+([\-\d.]+)\s+([\-\d.]+)\s+([\-\d.]+)\)', pin_block)
        if m:
            x, y, angle = float(m.group(1)), float(m.group(2)), float(m.group(3))
            yield (name, x, y, angle)


def main():
    if not SCH.exists():
        print(f"[ERR] Schematic not found: {SCH}")
        return 1
    if not PCB.exists():
        print(f"[ERR] PCB not found: {PCB}")
        return 1

    text = SCH.read_text(encoding="utf-8")
    board = pcbnew.LoadBoard(str(PCB))
    print(f"[INFO] Loaded {SCH.name} and {PCB.name}")

    # Step 1: Build a map of all global labels in the schematic.
    labels = []
    for body in extract_blocks(text, "global_label"):
        m = re.search(r'\(global_label\s+"([^"]+)"', body)
        if not m:
            continue
        name = m.group(1)
        m = re.search(r'\(at\s+([\-\d.]+)\s+([\-\d.]+)\s+([\-\d.]+)\)', body)
        if m:
            x, y = float(m.group(1)), float(m.group(2))
            labels.append((name, x, y))

    print(f"[INFO] Found {len(labels)} global labels in schematic")
    from collections import Counter
    by_name = Counter(n for n, _, _ in labels)
    print(f"[INFO] Unique nets: {len(by_name)}")
    for n, c in by_name.most_common(10):
        print(f"   {n}: {c} pins")

    # Step 2: Build a map of (ref, pin_name) -> (x, y) for every pin
    pin_positions = []
    for body in extract_blocks(text, "symbol"):
        ref = find_property(body, "Reference")
        if not ref or ref.startswith('"#'):
            continue
        for pin_name, x, y, angle in find_pins(body):
            pin_positions.append((ref, pin_name, x, y))

    print(f"[INFO] Found {len(pin_positions)} pins in schematic")

    # Step 3: For each global label, find the pin at the same (x, y)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    print(f"[INFO] Found {len(fps)} footprints on board")

    def get_or_create_net(name):
        net = board.FindNet(name)
        if net is None or net.GetNet() == 0:
            net = pcbnew.NETINFO_ITEM(board, name)
            board.Add(net)
        return net

    assigned = 0
    skipped = 0
    for net_name, lx, ly in labels:
        matched = None
        for ref, pin_name, px, py in pin_positions:
            if abs(px - lx) < 0.1 and abs(py - ly) < 0.1:
                matched = (ref, pin_name)
                break
        if matched is None:
            skipped += 1
            continue
        ref, pin_name = matched
        if ref not in fps:
            skipped += 1
            continue
        fp = fps[ref]
        for pad in fp.Pads():
            if pad.GetPadName() == pin_name or pad.GetNumber() == pin_name:
                net = get_or_create_net(net_name)
                pad.SetNet(net)
                assigned += 1
                break

    print()
    print(f"[OK] Assigned nets to {assigned} pads ({skipped} labels unmatched)")

    pcbnew.SaveBoard(str(PCB), board)
    print(f"[OK] Saved {PCB.name}")

    nets = set()
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n:
                nets.add(n)
    print(f"[INFO] Total unique nets on board: {len(nets)}")
    print()
    print("Next: re-run prep_pcb.py to add copper pours + manufacturing files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
