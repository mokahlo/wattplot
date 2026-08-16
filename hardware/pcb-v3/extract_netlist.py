#!/usr/bin/env python3
"""
extract_netlist.py — Parse the schematic S-expr and emit a KiCad-format
netlist file. Works around the empty-lib_symbols issue: kicad-cli's
netlist export produces an empty list because the lib_symbols section
is empty, but the components ARE in the schematic file as (symbol ...)
blocks with (property "Reference" "R1") and (property "Footprint" "...").
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent
SCH = ROOT / "wattplot-v3.kicad_sch"
OUT = ROOT / "exports" / "wattplot-v3.net"


def extract_blocks(s, head):
    """Yield (start, end, body) for each top-level (head ...) block."""
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
                    yield (start, i + 1, s[start:i + 1])
                    break
            i += 1


def find_property(body, key):
    """Find (property "key" "value" ...) in an s-expr body."""
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


def main():
    text = SCH.read_text(encoding="utf-8")
    print(f"[INFO] Read {len(text):,} bytes from {SCH.name}")

    components = []
    for _, _, body in extract_blocks(text, "symbol"):
        lib_id = find_kv(body, "lib_id")
        # Skip sub-symbols (instances like unit A, power symbols)
        # Heuristic: only keep symbols with a Reference property
        ref = find_property(body, "Reference")
        if not ref or ref.startswith('"'):
            continue
        value = find_property(body, "Value")
        fp = find_property(body, "Footprint")
        if ref:
            components.append({
                "ref": ref, "value": value, "footprint": fp, "lib_id": lib_id,
            })

    print(f"[INFO] Found {len(components)} components (top-level symbols)")

    # Emit netlist (component list only; nets require wire/pin tracing)
    lines = [
        '(export',
        '  (version "E")',
        '  (design',
        f'    (source "{SCH.name}")',
        '    (date "2026-08-16")',
        '    (tool "extract_netlist.py")',
        '  )',
        '  (components',
    ]
    for c in components:
        lines.append(f'    (comp (ref "{c["ref"]}")')
        if c["value"]:
            lines.append(f'      (value "{c["value"]}")')
        if c["footprint"]:
            lines.append(f'      (footprint "{c["footprint"]}")')
        lines.append('    )')
    lines.append('  )')
    lines.append('  (nets)')
    lines.append(')')
    lines.append('')

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {OUT.relative_to(ROOT)}")

    with_fp = sum(1 for c in components if c["footprint"])
    print(f"     {with_fp}/{len(components)} have footprints")

    no_fp = [c for c in components if not c["footprint"]]
    if no_fp:
        refs = ", ".join(c["ref"] for c in no_fp[:15])
        print(f"     Without footprint: {refs}")
        if len(no_fp) > 15:
            print(f"     ... and {len(no_fp) - 15} more")

    # Footprint prefix distribution
    fp_prefixes = {}
    for c in components:
        if c["footprint"]:
            prefix = c["footprint"].split(":")[0] if ":" in c["footprint"] else c["footprint"].split("_")[0]
            fp_prefixes[prefix] = fp_prefixes.get(prefix, 0) + 1
    if fp_prefixes:
        print()
        print("     Footprint prefixes:")
        for k, v in sorted(fp_prefixes.items(), key=lambda x: -x[1]):
            print(f"       {k}: {v}")


if __name__ == "__main__":
    main()
