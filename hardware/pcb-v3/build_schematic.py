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
    "mp1584":        "Regulator_Switching:MP1470",  # MP1470 is a similar 2A/16V sync buck in stock libs; we use as placeholder for MP1584EN
    "ams1117":       "Regulator_Linear:AMS1117-3.3",  # extends AP1117-15; pin positions come from there
    "smbj16":        "Power_Protection:TVS1800DRV",  # closest 16V-ish TVS in stock lib; sub for SMBJ16A
    "inductor_4u7":  "Device:L",
    "cap":           "Device:C",
    "cap_polarized": "Device:C_Polarized",
    "res":           "Device:R",
    "led_0805":      "Device:LED",  # generic LED in Device lib (LED lib has only specific part numbers)
    "fuse_1812":     "Device:Fuse",

    # ESP32-S3
    "esp32s3":       "RF_Module:ESP32-S3-WROOM-1",
    "usbc":          "Connector:USB_C_Receptacle",
    "usblc6":        "Power_Protection:USBLC6-2P6",  # correct substitute for USBLC6-2
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
        """Emit an EMPTY lib_symbols section. KiCad will resolve every
        `lib_id` from the user's installed libraries at open time.

        We deliberately do NOT embed a stub. The script used to emit a
        minimal stub (`(symbol "lib:id" (pin_names (offset 0)) (in_bom yes)
        (on_board yes))`) which KiCad's ERC then compared against the
        full library copy and flagged as a mismatch — and worse, used the
        stub's missing pin positions to compute "wire not connected"
        errors when our `pin_pos` (which reads the full library)
        disagreed by sub-millimeter amounts.

        The downside is that this schematic is no longer self-contained
        (you need the libraries installed to open it). For an open-source
        board, that's the right tradeoff: the user is using KiCad, they
        have the libs.
        """
        self.add("\t(lib_symbols")
        self.add("\t)")
        # (Alternatively, for full portability, we'd embed the entire raw
        # S-expression of each symbol here. That's future work; for now
        # we rely on the KiCad 10 standard library being present.)

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
        f' (shape {shape})'
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
    """12V input → MP1470 (buck placeholder) → 5V → AMS1117 → 3.3V.

    MP1470 pinout (substituted for MP1584EN — same SOT-23-6 footprint,
    similar 6-pin sync buck):
      1=GND, 2=SW, 3=IN, 4=FB, 5=EN, 6=BST

    AMS1117-3.3 pinout (extends AP1117-15):
      1=GND, 2=VO, 3=VI
    """
    y_main = y0
    mp_id = LIB["mp1584"]   # actually MP1470; see LIB dict
    ams_id = LIB["ams1117"]
    res_id = LIB["res"]
    cap_id = LIB["cap_polarized"]
    l_id   = LIB["inductor_4u7"]

    # ------------------------------------------------------------------
    # Component placement
    # ------------------------------------------------------------------

    # MP1470 (U1) at (x0+50, y_main)
    mp_x, mp_y = x0 + 50, y_main          # (130, 130)
    sch.reference(mp_id)
    sch.add(make_symbol_instance(
        mp_id, "U1", "MP1584EN",
        "Package_TO_SOT_SMD:SOT-23-6", mp_x, mp_y
    ))

    # AMS1117 (U2) at (x0+150, y_main)
    ams_x, ams_y = x0 + 150, y_main       # (230, 130)
    sch.reference(ams_id)
    sch.add(make_symbol_instance(
        ams_id, "U2", "AMS1117-3.3",
        "Package_TO_SOT_SMD:SOT-223-3_TabPin2", ams_x, ams_y
    ))

    # C1: 12V input cap (between +12V rail and GND)
    c1_x, c1_y = mp_x - 5, mp_y + 18      # (125, 148)
    sch.reference(cap_id)
    sch.add(make_symbol_instance(
        cap_id, "C1", "22uF/25V",
        "Capacitor_SMD:C_1210_3225Metric", c1_x, c1_y
    ))

    # C2: bootstrap cap (between SW and BST) — placed just below MP1470
    c2_x, c2_y = mp_x + 8, mp_y + 8       # (138, 138)
    sch.reference(cap_id)
    sch.add(make_symbol_instance(
        cap_id, "C2", "100nF",
        "Capacitor_SMD:C_0402_1005Metric", c2_x, c2_y
    ))

    # C3: 5V output cap (between +5V rail and GND, near L1)
    c3_x, c3_y = mp_x + 30, mp_y + 15     # (160, 145)
    sch.reference(cap_id)
    sch.add(make_symbol_instance(
        cap_id, "C3", "22uF/10V",
        "Capacitor_SMD:C_1210_3225Metric", c3_x, c3_y
    ))

    # C4: AMS1117 input cap (between +5V rail and GND)
    c4_x, c4_y = ams_x - 8, ams_y + 15    # (222, 145)
    sch.reference(cap_id)
    sch.add(make_symbol_instance(
        cap_id, "C4", "22uF/10V",
        "Capacitor_SMD:C_0805_2012Metric", c4_x, c4_y
    ))

    # C5: AMS1117 output cap (between +3V3 rail and GND)
    c5_x, c5_y = ams_x + 8, ams_y - 15    # (238, 115)
    sch.reference(cap_id)
    sch.add(make_symbol_instance(
        cap_id, "C5", "22uF/10V",
        "Capacitor_SMD:C_0805_2012Metric", c5_x, c5_y
    ))

    # L1: output inductor (between MP1470 SW and +5V rail)
    l1_x, l1_y = mp_x + 20, mp_y          # (150, 130)
    sch.reference(l_id)
    sch.add(make_symbol_instance(
        l_id, "L1", "4.7uH",
        "Inductor_SMD:L_1210_3225Metric", l1_x, l1_y
    ))

    # R1: 33k feedback (top of divider, from +5V to FB)
    r1_x, r1_y = mp_x + 35, mp_y - 8      # (165, 122)
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R1", "33k",
        "Resistor_SMD:R_0603_1608Metric", r1_x, r1_y
    ))

    # R2: 10k feedback (bottom of divider, from FB to GND)
    r2_x, r2_y = mp_x + 35, mp_y - 18     # (165, 112)
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R2", "10k",
        "Resistor_SMD:R_0603_1608Metric", r2_x, r2_y
    ))

    # R3: 100k battery divider (top, from VBAT to VBAT_ADC)
    r3_x, r3_y = x0, y_main - 30          # (80, 100)
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R3", "100k 1%",
        "Resistor_SMD:R_0603_1608Metric", r3_x, r3_y
    ))

    # R4: 100k battery divider (bottom, from VBAT_ADC to GND)
    r4_x, r4_y = x0, y_main - 45          # (80, 85)
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R4", "100k 1%",
        "Resistor_SMD:R_0603_1608Metric", r4_x, r4_y
    ))

    # Test point for VBAT_ADC (taps the middle of the divider)
    sch.reference(LIB["tp"])
    sch.add(make_symbol_instance(
        LIB["tp"], "TP1", "VBAT_ADC",
        "TestPoint:TestPoint_Pad_D1.0mm", x0 + 12, y_main - 37
    ))

    # ------------------------------------------------------------------
    # Resolve pin positions
    # ------------------------------------------------------------------

    def pp(lib, num, x, y):
        """Shorthand for pin_pos with a missing-pin fallback."""
        p = pin_pos(cache, lib, num, x, y)
        if p is None:
            raise RuntimeError(f"no pin {num} on {lib}")
        return p

    # MP1470: 1=GND, 2=SW, 3=IN, 4=FB, 5=EN, 6=BST
    mp_gnd = pp(mp_id, '1', mp_x, mp_y)
    mp_sw  = pp(mp_id, '2', mp_x, mp_y)
    mp_in  = pp(mp_id, '3', mp_x, mp_y)
    mp_fb  = pp(mp_id, '4', mp_x, mp_y)
    mp_en  = pp(mp_id, '5', mp_x, mp_y)
    mp_bst = pp(mp_id, '6', mp_x, mp_y)

    # AMS1117-3.3 (via AP1117-15): 1=GND, 2=VO, 3=VI
    ams_gnd = pp(ams_id, '1', ams_x, ams_y)
    ams_vo  = pp(ams_id, '2', ams_x, ams_y)
    ams_vi  = pp(ams_id, '3', ams_x, ams_y)

    # Caps: pin 1 = + (top), pin 2 = - (bottom)
    c1_pos, c1_neg = pp(cap_id, '1', c1_x, c1_y), pp(cap_id, '2', c1_x, c1_y)
    c2_pos, c2_neg = pp(cap_id, '1', c2_x, c2_y), pp(cap_id, '2', c2_x, c2_y)
    c3_pos, c3_neg = pp(cap_id, '1', c3_x, c3_y), pp(cap_id, '2', c3_x, c3_y)
    c4_pos, c4_neg = pp(cap_id, '1', c4_x, c4_y), pp(cap_id, '2', c4_x, c4_y)
    c5_pos, c5_neg = pp(cap_id, '1', c5_x, c5_y), pp(cap_id, '2', c5_x, c5_y)

    # Inductor: pin 1 = top, pin 2 = bottom
    l1_top, l1_bot = pp(l_id, '1', l1_x, l1_y), pp(l_id, '2', l1_x, l1_y)

    # Resistors: pin 1 = top, pin 2 = bottom
    r1_top, r1_bot = pp(res_id, '1', r1_x, r1_y), pp(res_id, '2', r1_x, r1_y)
    r2_top, r2_bot = pp(res_id, '1', r2_x, r2_y), pp(res_id, '2', r2_x, r2_y)
    r3_top, r3_bot = pp(res_id, '1', r3_x, r3_y), pp(res_id, '2', r3_x, r3_y)
    r4_top, r4_bot = pp(res_id, '1', r4_x, r4_y), pp(res_id, '2', r4_x, r4_y)

    # ------------------------------------------------------------------
    # Net labels — placed AT each power pin
    # ------------------------------------------------------------------
    # Multiple same-named global labels = same net (KiCad convention).
    # With the lib_symbols section now empty (see Schematic.lib_symbols_section),
    # KiCad's ERC reads pin positions from the installed libraries, which
    # match the coordinates we computed via pin_pos(). Labels placed exactly
    # at a pin position connect cleanly.

    def label_at_pin(net, pin_xy, shape="bidirectional"):
        x, y = pin_xy
        sch.add(make_global_label(net, x, y, shape))

    # +12V net: MP1470 IN, C1+, MP1470 EN (EN is tied to +12V via pull-up)
    label_at_pin("+12V", mp_in)
    label_at_pin("+12V", c1_pos)
    label_at_pin("+12V", mp_en)

    # GND net: every ground pin
    label_at_pin("GND", mp_gnd)
    label_at_pin("GND", ams_gnd)
    label_at_pin("GND", c1_neg)
    label_at_pin("GND", c3_neg)
    label_at_pin("GND", c4_neg)
    label_at_pin("GND", c5_neg)
    label_at_pin("GND", r2_bot)
    label_at_pin("GND", r4_bot)

    # +5V net: MP1470 SW, AMS1117 VI, C3+, C4+, R1 top
    label_at_pin("+5V", mp_sw)
    label_at_pin("+5V", ams_vi)
    label_at_pin("+5V", c3_pos)
    label_at_pin("+5V", c4_pos)
    label_at_pin("+5V", r1_top)

    # +3V3 net: AMS1117 VO, C5+
    label_at_pin("+3V3", ams_vo)
    label_at_pin("+3V3", c5_pos)

    # FB net: MP1470 FB, R1 bot, R2 top
    label_at_pin("FB", mp_fb)
    label_at_pin("FB", r1_bot)
    label_at_pin("FB", r2_top)

    # VBAT net: R3 top (battery +)
    label_at_pin("VBAT", r3_top)

    # VBAT_ADC net (mid-divider): R3 bot, R4 top, TP1
    label_at_pin("VBAT_ADC", r3_bot)
    label_at_pin("VBAT_ADC", r4_top)
    label_at_pin("VBAT_ADC", (x0 + 12, y_main - 37))

    # ------------------------------------------------------------------
    # Wires — only for components bridging two named nets
    # ------------------------------------------------------------------

    def w(x1, y1, x2, y2):
        sch.add(make_wire(x1, y1, x2, y2))

    # L1 inductor: between MP1470 SW (+5V) and the rest of the +5V net
    w(mp_sw[0], mp_sw[1], l1_top[0], l1_top[1])                  # SW → L1 top
    w(l1_bot[0], l1_bot[1], c3_pos[0], l1_bot[1])                # L1 bot → C3+ col
    sch.add(make_junction(l1_bot[0], l1_bot[1]))                  # tee so +5V label at C3+ sees it

    # C2 bootstrap cap: between MP1470 SW and BST
    # C2 pin 1 (top) → BST, C2 pin 2 (bottom) → SW
    w(c2_pos[0], c2_pos[1], c2_pos[0], mp_bst[1])                # up to BST y
    w(c2_pos[0], mp_bst[1], mp_bst[0], mp_bst[1])                # right to BST pin
    sch.add(make_junction(mp_bst[0], mp_bst[1]))
    w(c2_neg[0], c2_neg[1], c2_neg[0], mp_sw[1])                 # up to SW y
    w(c2_neg[0], mp_sw[1], mp_sw[0], mp_sw[1])                   # right to SW pin
    sch.add(make_junction(mp_sw[0], mp_sw[1]))

    # Annotation
    sch.add(make_text("→ GPIO7 (ADC)", x0 + 20, y_main - 37 - 2, size=1.0))


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
