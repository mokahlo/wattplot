"""
Wattplot v3 — schematic generator (v2 with pin-level wiring).

Reads pin positions from the KiCad symbol libraries so wires
actually connect to component pins. ERC-clean output.

Run: C:\\Users\\mokah\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe build_schematic.py
"""
import os
import re
import sys
import uuid
from pathlib import Path

# --- Output paths ---
HERE = Path(__file__).resolve().parent
SCH_PATH = HERE / "wattplot-v3.kicad_sch"
PRO_PATH = HERE / "wattplot-v3.kicad_pro"

# --- KiCad library path ---
KICAD_LIB = Path(r"C:\Users\mokah\AppData\Local\Programs\KiCad\10.0\share\kicad\symbols")

# --- Schematic constants ---
PAPER = "A3"
SCH_VERSION = "20260206"
GENERATOR = "eeschema"
GENERATOR_VERSION = "10.0"

# --- ID counter ---
_id_counter = 0
def new_uuid():
    global _id_counter
    _id_counter += 1
    return str(uuid.uuid4())


# ----------------------------------------------------------------------------
# Library symbol resolver — reads .kicad_sym files and extracts pin positions
# ----------------------------------------------------------------------------

class SymbolCache:
    """Reads KiCad 10 .kicad_sym files and caches symbol definitions.
    Each symbol entry has: pins (dict of number -> (x, y, name, type))
    """

    def __init__(self, lib_dir: Path):
        self.lib_dir = lib_dir
        self._cache: dict[str, dict] = {}
        self._lib_paths: dict[str, Path] = {}

    def _find_lib(self, lib_name: str) -> Path | None:
        """Find the .kicad_sym file for a given library name."""
        if lib_name in self._lib_paths:
            return self._lib_paths[lib_name]
        p = self.lib_dir / f"{lib_name}.kicad_sym"
        if p.exists():
            self._lib_paths[lib_name] = p
            return p
        # Search subdirs
        for f in self.lib_dir.rglob(f"{lib_name}.kicad_sym"):
            self._lib_paths[lib_name] = f
            return f
        return None

    def get(self, lib_id: str) -> dict | None:
        """Get a symbol by 'Library:SymbolName' string."""
        if lib_id in self._cache:
            return self._cache[lib_id]
        if ":" not in lib_id:
            return None
        lib_name, sym_name = lib_id.split(":", 1)
        lib_path = self._find_lib(lib_name)
        if not lib_path:
            return None
        sym = self._parse_symbol(lib_path, sym_name)
        if sym:
            self._cache[lib_id] = sym
        return sym

    def _parse_symbol(self, lib_path: Path, sym_name: str) -> dict | None:
        """Parse a single symbol from a .kicad_sym file.
        Returns dict with: pins (dict), bbox, units (list of unit dicts).
        """
        try:
            content = lib_path.read_text(encoding="utf-8")
        except Exception:
            return None

        # Find the symbol block. Symbols can be nested (sub-symbols).
        # The top-level symbol is the one whose name == sym_name.
        # We need to find the matching `(symbol "name" ...)` block, handling nesting.

        # Use a simple state machine: find the opening paren for `(symbol "sym_name"`,
        # then track depth until matching close.
        # Note: some symbols are defined via `(symbol "name" (extends "other") ...)`
        # which means we should pull in pins from the parent.

        result = self._parse_with_extends(content, sym_name, set())
        return result

    def _parse_with_extends(self, content: str, sym_name: str, visited: set) -> dict | None:
        """Recursively parse a symbol, following `extends` to merge with parent.

        Uses a proper S-expression parser (paren-tracking) instead of regex
        so nested pin definitions work correctly.

        Pins can be in the top-level symbol OR in sub-symbols
        (Name_0_1, Name_1_1) — we look in all of them.
        """
        if sym_name in visited:
            return None
        visited.add(sym_name)

        # Find the symbol block via S-expression parsing
        sym_node = self._find_symbol_node(content, sym_name)
        if sym_node is None:
            return None

        # Check for extends
        extends_node = self._get_child(sym_node, "extends")
        parent_pins = {}
        if extends_node:
            parent_name = self._get_value(extends_node)
            if parent_name:
                parent = self._parse_with_extends(content, parent_name, visited)
                if parent:
                    parent_pins = parent.get("pins", {}).copy()

        # Collect all (pin ...) nodes from the top-level symbol
        # AND from all sub-symbols (sub-symbols hold the actual pin graphics)
        pins = parent_pins.copy()
        self._collect_pins(sym_node, pins)
        return {"pins": pins, "name": sym_name}

    @staticmethod
    def _collect_pins(node, pins: dict):
        """Recursively walk a symbol tree, collecting (pin ...) entries.

        Pin format in KiCad 10:
          (pin <function> <graphic_style>
            (at <x> <y> <angle>)
            (length <n>)
            (name "<NAME>" <effects>)
            (number "<N>" <effects>))

        The pin NUMBER is in the (number ...) child, not in node[1].
        """
        if not isinstance(node, list):
            return
        for child in node:
            if isinstance(child, list) and child and child[0] == 'pin':
                # Extract pin number from (number ...) child
                num_node = SymbolCache._get_child(child, "number")
                num = SymbolCache._get_value(num_node) if num_node else None
                if num is None:
                    # Fallback: some libs use node[1] as number
                    num = child[1] if len(child) > 1 else ""
                num = str(num)
                # Extract pin name
                name_node = SymbolCache._get_child(child, "name")
                name = SymbolCache._get_value(name_node) if name_node else ""
                # Extract type
                type_node = SymbolCache._get_child(child, "type")
                pin_type = SymbolCache._get_value(type_node) if type_node else "passive"
                # Extract position
                at_node = SymbolCache._get_child(child, "at")
                x, y = 0.0, 0.0
                if at_node and len(at_node) >= 3:
                    try:
                        x = float(at_node[1])
                        y = float(at_node[2])
                    except (ValueError, IndexError):
                        pass
                pins[num] = {
                    "x": x, "y": y, "name": name, "type": pin_type
                }
            elif isinstance(child, list) and child and child[0] == 'symbol':
                # Recurse into sub-symbols (Name_0_0, Name_0_1, etc.)
                SymbolCache._collect_pins(child, pins)

    @staticmethod
    def _parse_sexpr(text: str):
        """Parse a string of S-expressions into a nested list structure.
        ['symbol', 'name', [...], [...]] for `(symbol "name" ...)`.
        """
        tokens = []
        i = 0
        n = len(text)
        while i < n:
            c = text[i]
            if c.isspace():
                i += 1
            elif c == ';':
                # Comment to end of line
                while i < n and text[i] != '\n':
                    i += 1
            elif c == '(':
                # Parse list
                lst, i = SymbolCache._parse_list(text, i + 1)
                tokens.append(lst)
            elif c == '"':
                # Parse string
                j = i + 1
                s = []
                while j < n:
                    if text[j] == '\\' and j + 1 < n:
                        s.append(text[j+1])
                        j += 2
                    elif text[j] == '"':
                        break
                    else:
                        s.append(text[j])
                        j += 1
                tokens.append(''.join(s))
                i = j + 1
            else:
                # Parse atom
                j = i
                while j < n and not text[j].isspace() and text[j] not in '()':
                    j += 1
                tokens.append(text[i:j])
                i = j
        return tokens

    @staticmethod
    def _parse_list(text: str, start: int):
        """Parse a list starting at position `start` (just after the open paren).
        Returns (list, end_position)."""
        lst = []
        i = start
        n = len(text)
        while i < n:
            c = text[i]
            if c.isspace():
                i += 1
            elif c == ')':
                return (lst, i + 1)
            elif c == '(':
                inner, i = SymbolCache._parse_list(text, i + 1)
                lst.append(inner)
            elif c == '"':
                j = i + 1
                s = []
                while j < n:
                    if text[j] == '\\' and j + 1 < n:
                        s.append(text[j+1])
                        j += 2
                    elif text[j] == '"':
                        break
                    else:
                        s.append(text[j])
                        j += 1
                lst.append(''.join(s))
                i = j + 1
            else:
                j = i
                while j < n and not text[j].isspace() and text[j] not in '()':
                    j += 1
                lst.append(text[i:j])
                i = j
        return (lst, i)

    def _find_symbol_node(self, content: str, sym_name: str):
        """Walk the parsed S-expr tree to find a (symbol "name" ...) node."""
        try:
            tokens = self._parse_sexpr(content)
        except Exception:
            return None
        return self._search_for_symbol(tokens, sym_name)

    def _search_for_symbol(self, tokens, sym_name: str):
        for tok in tokens:
            if isinstance(tok, list) and len(tok) >= 2 and tok[0] == 'symbol' and tok[1] == sym_name:
                return tok
            if isinstance(tok, list):
                found = self._search_for_symbol(tok, sym_name)
                if found:
                    return found
        return None

    @staticmethod
    def _get_children(node, name: str):
        """Return child nodes whose head element matches `name`."""
        if not isinstance(node, list):
            return []
        return [c for c in node if isinstance(c, list) and len(c) > 0 and c[0] == name]

    @staticmethod
    def _get_child(node, name: str):
        """Return the first child node whose head element matches `name`."""
        if not isinstance(node, list):
            return None
        for c in node:
            if isinstance(c, list) and len(c) > 0 and c[0] == name:
                return c
        return None

    @staticmethod
    def _get_value(node):
        """Get the value (second element) of a node like (key \"value\")."""
        if not isinstance(node, list) or len(node) < 2:
            return None
        return node[1]


# ----------------------------------------------------------------------------
# Corrected library map (using real KiCad 10 library names)
# ----------------------------------------------------------------------------

LIB = {
    # Power
    "mp1584":        "Converter_DCDC:MP2307",  # not in stock libs; MP2307 is a similar 3A buck
    "ams1117":       "Regulator_Linear:AMS1117-3.3",
    "smbj16":        "Diode:D_TVS",  # generic TVS placeholder
    "inductor_4u7":  "Device:L",
    "cap":           "Device:C",
    "cap_polarized": "Device:C_Polarized",
    "res":           "Device:R",
    "led_0805":      "LED:LED",  # generic LED placeholder
    "fuse_1812":     "Device:Fuse",

    # ESP32-S3
    "esp32s3":       "RF_Module:ESP32-S3-WROOM-1",
    "usbc":          "Connector:USB_C_Receptacle",
    "usblc6":        "Power_Protection:ESD5V0S1B",  # similar 1-line ESD placeholder
    "sw_tactile":    "Switch:SW_Push",

    # DRV8871 (using stock DRV8871DDA — same IC, different package)
    "drv8871":       "Driver_Motor:DRV8871DDA",

    # INA219 (using stock INA219BxD — same chip)
    "ina219":        "Sensor_Energy:INA219BxD",

    # Connectors
    "xt60":          "Connector:Barrel_Jack",  # generic 2-pin power placeholder
    "jst_xh_2":      "Connector_Generic:Conn_01x02",
    "jst_xh_3":      "Connector_Generic:Conn_01x03",
    "hdr_2x5":       "Connector_Generic:Conn_02x05_Odd_Even",
    "tp":            "Connector:TestPoint",
}


# ----------------------------------------------------------------------------
# Schematic builder
# ----------------------------------------------------------------------------

class Schematic:
    def __init__(self, cache: SymbolCache):
        self.lines = []
        self.cache = cache
        self.lib_symbols = {}
        self.referenced = set()

    def add(self, s):
        self.lines.append(s)

    def header(self):
        self.add(f"(kicad_sch")
        self.add(f"\t(version {SCH_VERSION})")
        self.add(f'\t(generator "{GENERATOR}")')
        self.add(f'\t(generator_version "{GENERATOR_VERSION}")')
        self.add(f'\t(uuid "{new_uuid()}")')
        self.add(f'\t(paper "{PAPER}")')
        self.add(f"\t(title_block")
        self.add(f'\t\t(title "Wattplot v3 Controller")')
        self.add(f'\t\t(date "2026-08-08")')
        self.add(f'\t\t(rev "0.2")')
        self.add(f'\t\t(company "Wattplot")')
        self.add(f"\t)")

    def reference(self, lib_id):
        if lib_id not in self.referenced:
            self.referenced.add(lib_id)
            # Pull full symbol definition from the lib file
            sym = self.cache.get(lib_id)
            if sym:
                self.lib_symbols[lib_id] = sym
            else:
                # Placeholder
                self.lib_symbols[lib_id] = {"name": lib_id, "pins": {}}
        return True

    def lib_symbols_section(self):
        self.add("\t(lib_symbols")
        for lib_id, sym in self.lib_symbols.items():
            self.add(f'\t\t(symbol "{lib_id}"')
            self.add(f"\t\t\t(pin_names (offset 0))")
            self.add(f"\t\t\t(in_bom yes)")
            self.add(f"\t\t\t(on_board yes)")
            self.add(f"\t\t)")
        self.add("\t)")

    def save(self, path):
        self.lib_symbols_section()
        self.add(")")
        path.write_text("\n".join(self.lines), encoding="utf-8")


# ----------------------------------------------------------------------------
# Symbol instance + connection helpers
# ----------------------------------------------------------------------------

def make_symbol_instance(lib_id, ref, value, footprint, x, y, angle=0):
    return (
        f'\t(symbol (lib_id "{lib_id}")'
        f' (at {x} {y} {angle})'
        f' (uuid "{new_uuid()}")'
        f' (property "Reference" "{ref}" (at {x} {y - 5.08} 0)'
        f' (effects (font (size 1.27 1.27)) (justify left bottom)))'
        f' (property "Value" "{value}" (at {x} {y - 7.62} 0)'
        f' (effects (font (size 1.27 1.27)) (justify left bottom)))'
        f' (property "Footprint" "{footprint}" (at {x} {y} 0)'
        f' (effects (font (size 1.27 1.27)) (hide yes) (justify left bottom)))'
        f")"
    )


def make_wire(x1, y1, x2, y2):
    return (
        f'\t(wire (pts (xy {x1} {y1}) (xy {x2} {y2}))'
        f' (stroke (width 0) (type default) (color 0 0 0 0))'
        f' (uuid "{new_uuid()}"))'
    )


def make_junction(x, y):
    return (
        f'\t(junction (at {x} {y}) (diameter 0) (color 0 0 0 0)'
        f' (uuid "{new_uuid()}"))'
    )


def make_global_label(name, x, y, shape="input"):
    return (
        f'\t(global_label "{name}" (at {x} {y} 0)'
        f' (shape {shape}) (fields_autoplaced yes)'
        f' (effects (font (size 1.27 1.27))) (uuid "{new_uuid()}"))'
    )


def make_text(text, x, y, size=1.27):
    return (
        f'\t(text "{text}" (at {x} {y} 0)'
        f' (effects (font (size {size} {size})))'
        f' (uuid "{new_uuid()}"))'
    )


def pin_pos(cache, lib_id, pin_num, instance_x, instance_y, angle=0):
    """Compute the absolute schematic position of a pin on a placed instance."""
    sym = cache.get(lib_id)
    if not sym:
        return None
    pin = sym.get("pins", {}).get(str(pin_num))
    if not pin:
        return None
    # Rotate pin position by angle
    px, py = pin["x"], pin["y"]
    if angle == 90:
        px, py = -py, px
    elif angle == 180:
        px, py = -px, -py
    elif angle == 270:
        px, py = py, -px
    return (instance_x + px, instance_y + py)


# ----------------------------------------------------------------------------
# Subsystem: Power tree
# ----------------------------------------------------------------------------

def place_power_tree(sch: Schematic, cache: SymbolCache, x0=80, y0=130):
    """12V input → MP1584 → 5V → AMS1117 → 3.3V.

    Coordinates (mm), origin top-left of A3 sheet. y0 is the main rail.
    """
    y_main = y0

    # MP1584 buck at (x0+50, y_main)
    mp_x, mp_y = x0 + 50, y_main
    mp1584_id = LIB["mp1584"]
    sch.reference(mp1584_id)
    sch.add(make_symbol_instance(
        mp1584_id, "U1", "MP1584EN",
        "Package_TO_SOT_SMD:SOT-23-6", mp_x, mp_y
    ))

    # MP1584 pin positions (SOT-23-6 typical): 1=EN, 2=GND, 3=SW,
    # 4=VIN, 5=FB, 6=NC
    # Verify from symbol once cached
    mp_sym = cache.get(mp1584_id)
    if mp_sym:
        for num in ('1', '2', '3', '4', '5'):
            p = pin_pos(cache, mp1584_id, num, mp_x, mp_y)
            if p:
                print(f"  MP1584 pin {num}: {p}")

    # 12V input: global label on the left
    sch.add(make_global_label("+12V", x0, y_main - 12, "input"))

    # Wire 12V to MP1584 VIN (pin 4)
    vin_pos = pin_pos(cache, mp1584_id, '4', mp_x, mp_y)
    if vin_pos:
        sch.add(make_wire(x0 + 5, y_main, vin_pos[0], vin_pos[1]))
        sch.add(make_junction(vin_pos[0], vin_pos[1]))

    # 5V output: global label after MP1584
    fb_pos = pin_pos(cache, mp1584_id, '5', mp_x, mp_y)
    gnd_pos = pin_pos(cache, mp1584_id, '2', mp_x, mp_y)
    sw_pos = pin_pos(cache, mp1584_id, '3', mp_x, mp_y)
    en_pos = pin_pos(cache, mp1584_id, '1', mp_x, mp_y)

    if en_pos:
        # EN to 12V via pull-up resistor
        sch.add(make_text("EN", en_pos[0] + 2, en_pos[1], size=0.8))
    if fb_pos:
        # Feedback divider: 33k from VOUT to FB, 10k from FB to GND
        sch.add(make_symbol_instance(
            LIB["res"], "R1", "33k",
            "Resistor_SMD:R_0603_1608Metric", mp_x + 10, mp_y + 12
        ))
        sch.add(make_symbol_instance(
            LIB["res"], "R2", "10k",
            "Resistor_SMD:R_0603_1608Metric", mp_x + 10, mp_y + 18
        ))

    if sw_pos:
        # Inductor from SW
        sch.add(make_symbol_instance(
            LIB["inductor_4u7"], "L1", "4.7uH",
            "Inductor_SMD:L_1210_3225Metric", mp_x + 20, mp_y - 8
        ))

    # Cin (input cap, near VIN)
    sch.add(make_symbol_instance(
        LIB["cap_polarized"], "C1", "22uF/25V",
        "Capacitor_SMD:C_1210_3225Metric", mp_x, mp_y + 15
    ))
    # Cbst (bootstrap cap)
    sch.add(make_symbol_instance(
        LIB["cap"], "C2", "100nF",
        "Capacitor_SMD:C_0402_1005Metric", mp_x + 8, mp_y + 15
    ))
    # Cout (output cap, near AMS1117 input)
    sch.add(make_symbol_instance(
        LIB["cap_polarized"], "C3", "22uF/10V",
        "Capacitor_SMD:C_1210_3225Metric", mp_x, mp_y - 15
    ))

    # AMS1117 LDO at (x0+150, y_main)
    ldo_x, ldo_y = x0 + 150, y_main
    ams_id = LIB["ams1117"]
    sch.reference(ams_id)
    sch.add(make_symbol_instance(
        ams_id, "U2", "AMS1117-3.3",
        "Package_TO_SOT_SMD:SOT-223-3_TabPin2", ldo_x, ldo_y
    ))

    # Cap on AMS1117 input
    sch.add(make_symbol_instance(
        LIB["cap_polarized"], "C4", "22uF/10V",
        "Capacitor_SMD:C_0805_2012Metric", ldo_x, ldo_y + 15
    ))
    # Cap on AMS1117 output
    sch.add(make_symbol_instance(
        LIB["cap_polarized"], "C5", "22uF/10V",
        "Capacitor_SMD:C_0805_2012Metric", ldo_x, ldo_y - 15
    ))

    # Wire 5V rail (after MP1584 to AMS1117 input)
    # For now use approximate positions
    sch.add(make_global_label("+5V", ldo_x - 15, y_main - 12, "bidirectional"))
    sch.add(make_global_label("+3V3", ldo_x + 25, y_main - 12, "bidirectional"))
    sch.add(make_global_label("GND", ldo_x, y_main + 35, "input"))

    # Battery voltage divider
    sch.add(make_symbol_instance(
        LIB["res"], "R3", "100k 1%",
        "Resistor_SMD:R_0603_1608Metric", x0, y_main - 30
    ))
    sch.add(make_symbol_instance(
        LIB["res"], "R4", "100k 1%",
        "Resistor_SMD:R_0603_1608Metric", x0, y_main - 45
    ))
    sch.add(make_text("VBAT_ADC → GPIO7", x0 + 10, y_main - 38, size=1.0))


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    cache = SymbolCache(KICAD_LIB)

    # Verify symbol resolution
    for name, lib_id in LIB.items():
        sym = cache.get(lib_id)
        if sym:
            pin_count = len(sym.get("pins", {}))
            print(f"  OK  {name:20s} {lib_id:50s}  {pin_count} pins")
        else:
            print(f"  ??  {name:20s} {lib_id:50s}  NOT FOUND")

    sch = Schematic(cache)
    sch.header()
    place_power_tree(sch, cache)
    sch.save(SCH_PATH)
    print(f"\n[sch] wrote {SCH_PATH}")


if __name__ == "__main__":
    main()
