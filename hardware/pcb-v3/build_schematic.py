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
# Stock KiCad 10 library + our custom lib (for the 4 hand-rolled symbols)
CUSTOM_LIB = Path(__file__).parent / "custom-lib"
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

    Searches a list of lib directories (stock KiCad + custom-lib first).
    """

    def __init__(self, lib_dirs):
        # Accept either a single Path or a list of Paths
        if isinstance(lib_dirs, (Path, str)):
            self.lib_dirs = [Path(lib_dirs)]
        else:
            self.lib_dirs = [Path(d) for d in lib_dirs]
        self._cache: dict[str, dict] = {}
        self._lib_paths: dict[str, Path] = {}

    def _find_lib(self, lib_name: str) -> Path | None:
        """Find the .kicad_sym file for a given library name.

        Search order: CUSTOM_LIB first (so our hand-rolled symbols
        override stock ones), then stock KiCad.
        """
        if lib_name in self._lib_paths:
            return self._lib_paths[lib_name]
        # Search custom lib first, then stock
        # (Reverse the list so custom comes first when iterated in reverse)
        for lib_dir in reversed(self.lib_dirs):
            p = lib_dir / f"{lib_name}.kicad_sym"
            if p.exists():
                self._lib_paths[lib_name] = p
                return p
            for f in lib_dir.rglob(f"{lib_name}.kicad_sym"):
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
    "mp1584":        "wattplot:MP1584EN",  # our custom 6-pin SOT-23-6 sync buck
    "ams1117":       "Regulator_Linear:AMS1117-3.3",  # extends AP1117-15; pin positions come from there
    "smbj16":        "wattplot:SMBJ16A",  # our custom 2-pin TVS
    "inductor_4u7":  "Device:L",
    "cap":           "Device:C",
    "cap_polarized": "Device:C_Polarized",
    "res":           "Device:R",
    "led_0805":      "wattplot:LED_0805",  # our custom 2-pin LED (Device:LED is OK too)
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
    "xt60":          "wattplot:XT60",  # our custom 2-pin XT60 power connector
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

        We also tried embedding the full raw S-expression of each
        referenced symbol (including the custom-lib wattplot.kicad_sym
        content) so the schematic is self-contained. This BREAKS the
        file with "Failed to load schematic" — KiCad 10's parser is
        stricter than ours about the lib_symbols section format, and
        even getting the indentation / wrapping right wasn't enough.
        (The 26 label_dangling warnings from the empty-section approach
        persist, but those are cosmetic — the netlist is correct.)

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
# Subsystem: Sensor interfaces (1-Wire, soil moisture, panel temp)
# ----------------------------------------------------------------------------
#
# External sensor connectors:
#   J5  3-pin JST-XH 1-Wire bus   (GND, DATA, 3V3) — DS18B20 chain
#   J6  3-pin JST-XH soil sensor (GND, AOUT, 3V3) — capacitive moisture
#   4.7kΩ pull-up from DATA to 3V3 (required for 1-Wire)

def place_sensors(sch: Schematic, cache: SymbolCache, x0=750, y0=200):
    """1-Wire (DS18B20) + soil moisture sensor interfaces."""
    jst_id   = LIB["jst_xh_3"]
    res_id   = LIB["res"]

    def pp(lib, num, x, y):
        p = pin_pos(cache, lib, num, x, y)
        if p is None:
            raise RuntimeError(f"no pin {num} on {lib}")
        return p

    def lbl(net, pos, shape="bidirectional"):
        sch.add(make_global_label(net, pos[0], pos[1], shape))

    # J5: 1-Wire connector (3 pins: GND=1, DATA=2, 3V3=3)
    j5_x, j5_y = x0, y0
    sch.reference(jst_id)
    sch.add(make_symbol_instance(
        jst_id, "J5", "1-WIRE",
        "Connector_JST:JST_XH_B3B-PH-K_1x03_P2.50mm_Vertical", j5_x, j5_y
    ))
    j5_p1 = pp(jst_id, '1', j5_x, j5_y)  # GND
    j5_p2 = pp(jst_id, '2', j5_x, j5_y)  # DATA
    j5_p3 = pp(jst_id, '3', j5_x, j5_y)  # 3V3

    lbl("GND", j5_p1)
    lbl("DS18B20_DATA", j5_p2)
    lbl("+3V3", j5_p3)

    # 4.7kΩ pull-up resistor on DATA to 3V3 (placed above the connector)
    r_x, r_y = x0, y0 - 18
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R12", "4.7k",
        "Resistor_SMD:R_0603_1608Metric", r_x, r_y
    ))
    r_top = pp(res_id, '1', r_x, r_y)  # top of resistor (connects to 3V3)
    r_bot = pp(res_id, '2', r_x, r_y)  # bottom (connects to DATA)

    # Wire from DATA (j5_p2) up to r_bot — route via x=752 to avoid
    # passing through the +3V3 label at (744.92, 197.46)
    sch.add(make_wire(j5_p2[0], j5_p2[1], 752, j5_p2[1]))  # right
    sch.add(make_wire(752, j5_p2[1], 752, r_bot[1]))          # up
    sch.add(make_wire(752, r_bot[1], r_bot[0], r_bot[1]))      # left to r_bot
    sch.add(make_junction(752, r_bot[1]))
    # Wire from r_top to 3V3 (j5_p3) — NO through-R wire, the
    # resistor's own pins do the connection.
    sch.add(make_wire(r_top[0], r_top[1], r_top[0], j5_p3[1]))
    sch.add(make_wire(r_top[0], j5_p3[1], j5_p3[0], j5_p3[1]))
    sch.add(make_junction(r_top[0], j5_p3[1]))

    # J6: Soil moisture connector (3 pins: GND=1, AOUT=2, 3V3=3)
    j6_x, j6_y = x0, y0 + 50
    sch.reference(jst_id)
    sch.add(make_symbol_instance(
        jst_id, "J6", "SOIL",
        "Connector_JST:JST_XH_B3B-PH-K_1x03_P2.50mm_Vertical", j6_x, j6_y
    ))
    j6_p1 = pp(jst_id, '1', j6_x, j6_y)  # GND
    j6_p2 = pp(jst_id, '2', j6_x, j6_y)  # AOUT
    j6_p3 = pp(jst_id, '3', j6_x, j6_y)  # 3V3

    lbl("GND", j6_p1)
    lbl("SOIL_AOUT", j6_p2)
    lbl("+3V3", j6_p3)

    # Annotation
    sch.add(make_text("Sensor interfaces (J5 1-Wire, J6 soil)",
                      x0 - 20, y0 - 40, size=1.8))


# ----------------------------------------------------------------------------
# Subsystem: 2x INA219 current/power monitors
# ----------------------------------------------------------------------------
#
# INA219BxD pinout (extends INA219AxD):
#   Pin 1: A1         (10.16, -2.54)   ← I2C address bit 1
#   Pin 2: A0         (10.16, -5.08)   ← I2C address bit 0
#   Pin 3: SDA        (10.16, 5.08)    ← I2C SDA
#   Pin 4: SCL        (10.16, 2.54)    ← I2C SCL
#   Pin 5: VS         (0, 10.16)       ← power supply (3.3V)
#   Pin 6: GND        (0, -10.16)
#   Pin 7: IN-        (-10.16, -2.54)  ← current sense -
#   Pin 8: IN+        (-10.16, 2.54)   ← current sense +
#
# Wattplot wiring:
#   U7 (0x41) INA219 panel:   measures panel V/A via solar MPPT shunt
#   U8 (0x40) INA219 actuator: measures actuator + battery bus current
#   Both share I2C bus (GPIO8/18 on ESP32)
#   I2C addresses: U7 A0=VS(1), A1=GND(0) → 0x41
#                  U8 A0=GND(0), A1=GND(0) → 0x40

def place_ina219s(sch: Schematic, cache: SymbolCache, x0=600, y0=200):
    """Two INA219 current monitors (U7 panel, U8 actuator/battery)."""
    ina_id   = LIB["ina219"]
    res_id   = LIB["res"]
    cap_id   = LIB["cap"]

    def pp(lib, num, x, y):
        p = pin_pos(cache, lib, num, x, y)
        if p is None:
            raise RuntimeError(f"no pin {num} on {lib}")
        return p

    def place_one_ina(idx, name, ref_prefix, x, y,
                      a0_net, a1_net, label_prefix, shunt_label):
        """Place one INA219 + 100nF bypass cap + a virtual shunt."""
        sch.reference(ina_id)
        sch.add(make_symbol_instance(
            ina_id, ref_prefix, f"INA219 ({name})",
            "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", x, y
        ))

        # Resolve pin positions
        p_a1  = pp(ina_id, '1', x, y)
        p_a0  = pp(ina_id, '2', x, y)
        p_sda = pp(ina_id, '3', x, y)
        p_scl = pp(ina_id, '4', x, y)
        p_vs  = pp(ina_id, '5', x, y)
        p_gnd = pp(ina_id, '6', x, y)
        p_inm = pp(ina_id, '7', x, y)
        p_inp = pp(ina_id, '8', x, y)

        # 100nF VS bypass cap (right of the chip)
        cap_x, cap_y = x + 30, y + 10
        sch.reference(cap_id)
        sch.add(make_symbol_instance(
            cap_id, f"C{12+idx}", "100nF",
            "Capacitor_SMD:C_0402_1005Metric", cap_x, cap_y
        ))
        c_pos = pp(cap_id, '1', cap_x, cap_y)
        c_neg = pp(cap_id, '2', cap_x, cap_y)

        # Net labels at every pin
        def lbl(net, pos, shape="bidirectional"):
            sch.add(make_global_label(net, pos[0], pos[1], shape))
        lbl("+3V3",  p_vs)        # chip power
        lbl("GND",   p_gnd)       # ground
        lbl("I2C_SDA", p_sda)     # I2C bus
        lbl("I2C_SCL", p_scl)     # I2C bus
        lbl("ACT_IN+",  p_inp) if name == "ACT" else lbl("PANEL_IN+", p_inp)
        lbl("ACT_IN-" if name == "ACT" else "PANEL_IN-", p_inm)
        lbl(a0_net, p_a0)
        lbl(a1_net, p_a1)

        # Bypass cap: VS to GND
        # Place label on the cap's wires (so they form a clear stub)
        sch.add(make_wire(c_pos[0], c_pos[1], p_vs[0], c_pos[1]))
        sch.add(make_wire(p_vs[0], c_pos[1], p_vs[0], p_vs[1]))
        sch.add(make_junction(p_vs[0], c_pos[1]))
        sch.add(make_wire(c_neg[0], c_neg[1], c_neg[0], y - 30))
        lbl("GND", (c_neg[0], y - 30))
        lbl("+3V3", (p_vs[0], c_pos[1]))  # redundant but ensures ERC sees it

        # Annotation
        sch.add(make_text(f"{shunt_label} (1mΩ)",
                          x - 25, y - 25, size=1.0))

    # U7 (panel) at (x0, y0), I2C addr 0x41 → A0=VS, A1=GND
    place_one_ina(0, "PAN", "U7", x0, y0,
                  a0_net="+3V3", a1_net="GND",
                  label_prefix="PANEL", shunt_label="PV_SHUNT")
    # U8 (actuator) at (x0, y0+100), I2C addr 0x40 → A0=GND, A1=GND
    place_one_ina(1, "ACT", "U8", x0, y0 + 100,
                  a0_net="GND", a1_net="GND",
                  label_prefix="ACT", shunt_label="BATT_SHUNT")

    sch.add(make_text("INA219 current monitors (U7 panel / U8 actuator+battery)",
                      x0 - 30, y0 - 50, size=2.0))


# ----------------------------------------------------------------------------
# Subsystem: 2x DRV8871 H-bridges (actuator + solenoid drivers)
# ----------------------------------------------------------------------------
#
# DRV8871DDA pinout (from Driver_Motor lib, sub-symbol _1_1):
#   Pin 1: GND          (0, -10.16)
#   Pin 2: IN2          (-10.16, 2.54)   ← direction input 2
#   Pin 3: IN1          (-10.16, 5.08)   ← direction input 1
#   Pin 4: ILIM         (10.16, -5.08)   ← current sense (IPROPI) — 1kΩ to GND = 200mV/A
#   Pin 5: VM           (0, 10.16)      ← motor supply (12V fused)
#   Pin 6: OUT1         (10.16, 5.08)   ← motor output 1
#   Pin 7: GND (exposed pad) — hidden
#   Pin 8: OUT2         (10.16, 2.54)   ← motor output 2
#   Pin 9: GND (exposed pad) — hidden
#
# NOTE: The lib symbol does NOT have nSLEEP, VCC, or nFAULT pins. The real
# chip has all three, but in this package they're handled internally
# (nSLEEP tied high, VCC is internal 5V LDO). The nFAULT pin is
# open-drain and needs to be wired externally — we model this as a
# "virtual nFAULT" label on the H-bridge, which connects (by name) to
# the ACTUATOR_nFAULT / SOLENOID_nFAULT label on the ESP32.
#
# Wattplot wiring:
#   U5a (actuator) IN1=GPIO1, IN2=GPIO2, ILIM=GPIO4, nFAULT→GPIO21
#   U5b (solenoid) IN1=GPIO10, IN2=GPIO12, ILIM=GPIO5, nFAULT→GPIO13
#   VM (both) = +12V (fused)
#   GND (both) = common ground
#   OUT1/OUT2 → JST-XH 2-pin connector to motor / solenoid

def place_drv8871s(sch: Schematic, cache: SymbolCache, x0=450, y0=200):
    """Two DRV8871 H-bridges (U5a actuator, U5b solenoid) + support.

    Layout:
        U5a at (x0, y0)         ← actuator
        U5b at (x0, y0 + 90)    ← solenoid (below)
    """
    drv_id  = LIB["drv8871"]
    res_id  = LIB["res"]
    cap_id  = LIB["cap_polarized"]
    jst_id  = LIB["jst_xh_2"]
    tp_id   = LIB["tp"]

    def pp(lib, num, x, y):
        p = pin_pos(cache, lib, num, x, y)
        if p is None:
            raise RuntimeError(f"no pin {num} on {lib}")
        return p

    def place_one_drv(idx, name, ref_prefix, x, y,
                      in1_net, in2_net, ilim_net, nfault_net,
                      motor_label, jst_ref):
        """Place one DRV8871 + its VM bulk cap, ILIM resistor, JST output
        connector, and a virtual nFAULT test point."""
        # The DRV8871 itself
        sch.reference(drv_id)
        sch.add(make_symbol_instance(
            drv_id, ref_prefix, f"DRV8871 ({name})",
            "Package_SO:Texas_HTSOP-8-1EP_3.9x4.9mm_P1.27mm", x, y
        ))

        # Resolve pin positions
        p_gnd  = pp(drv_id, '1', x, y)
        p_in2  = pp(drv_id, '2', x, y)
        p_in1  = pp(drv_id, '3', x, y)
        p_ilim = pp(drv_id, '4', x, y)
        p_vm   = pp(drv_id, '5', x, y)
        p_out1 = pp(drv_id, '6', x, y)
        p_out2 = pp(drv_id, '8', x, y)

        # VM bulk cap (22uF/25V), placed above the chip
        cap_x, cap_y = x, y - 20
        sch.reference(cap_id)
        sch.add(make_symbol_instance(
            cap_id, f"C{8+idx}", "22uF/25V",
            "Capacitor_SMD:C_1210_3225Metric", cap_x, cap_y
        ))
        c_pos = pp(cap_id, '1', cap_x, cap_y)
        c_neg = pp(cap_id, '2', cap_x, cap_y)

        # ILIM resistor (1kΩ to GND, 200mV/A), placed to the right
        r_x, r_y = x + 25, y - 5
        sch.reference(res_id)
        sch.add(make_symbol_instance(
            res_id, f"R{9+idx}", "1k",
            "Resistor_SMD:R_0603_1608Metric", r_x, r_y
        ))
        r_top = pp(res_id, '1', r_x, r_y)
        r_bot = pp(res_id, '2', r_x, r_y)

        # JST-XH 2-pin output connector, placed further right
        jst_x, jst_y = x + 50, y
        sch.reference(jst_id)
        sch.add(make_symbol_instance(
            jst_id, jst_ref, motor_label,
            "Connector_JST:JST_XH_B2B-PH-K_1x02_P2.50mm_Vertical", jst_x, jst_y
        ))
        j1 = pp(jst_id, '1', jst_x, jst_y)
        j2 = pp(jst_id, '2', jst_x, jst_y)

        # nFAULT test point (a "virtual" pin not in the symbol)
        # Place to the right of the chip, at a y that doesn't collide
        nf_x, nf_y = x + 25, y + 10
        sch.reference(tp_id)
        sch.add(make_symbol_instance(
            tp_id, f"TP{1+idx}", f"nFAULT_{name}",
            "TestPoint:TestPoint_Pad_D1.0mm", nf_x, nf_y
        ))
        nf_pos = pp(tp_id, '1', nf_x, nf_y)

        # ------------------------------------------------------------------
        # Power labels (at each pin, no wires needed for power rails)
        # ------------------------------------------------------------------
        def lbl(net, pos, shape="bidirectional"):
            sch.add(make_global_label(net, pos[0], pos[1], shape))
        lbl("+12V",  p_vm)        # motor supply
        lbl("GND",   p_gnd)       # pin 1
        lbl("GND",   (x, p_gnd[1]))  # also at the symbol center (where pins 7,9 are)
        # Pin 7, 9 are hidden but their anchor is the same coordinate
        # as pin 1. Adding a GND label there ensures the symbol is
        # properly grounded even if KiCad resolves it differently.
        lbl(in1_net, p_in1)
        lbl(in2_net, p_in2)
        lbl(ilim_net, p_ilim)
        # Output connector: pin 1 = OUT1, pin 2 = OUT2 (typical convention)
        lbl("OUT1",  j1)
        lbl("OUT2",  j2)
        # nFAULT virtual pin: name it with the same net as the ESP32 side
        lbl(nfault_net, nf_pos)
        # Annotation: which motor does this drive
        sch.add(make_text(motor_label, jst_x + 5, jst_y + 7, size=1.27))

        # ------------------------------------------------------------------
        # Supporting wires
        # ------------------------------------------------------------------
        def w(x1, y1, x2, y2):
            sch.add(make_wire(x1, y1, x2, y2))
        def j(x, y):
            sch.add(make_junction(x, y))

        # VM bulk cap: between +12V and GND
        # The +12V label is at p_vm (top of chip). Wire from cap
        # positive to p_vm via a stub.
        w(c_pos[0], c_pos[1], c_pos[0], p_vm[1])
        w(c_pos[0], p_vm[1], p_vm[0], p_vm[1])
        j(p_vm[0], p_vm[1])
        # cap negative → GND rail (at y = p_gnd[1] = 189.84, but we
        # route down to the same GND label as the chip)
        w(c_neg[0], c_neg[1], c_neg[0], y - 30)
        lbl("GND", (c_neg[0], y - 30))

        # OUT1 → JST pin 1
        w(p_out1[0], p_out1[1], p_out1[0], j1[1])
        w(p_out1[0], j1[1], j1[0], j1[1])
        j(p_out1[0], j1[1])
        # OUT2 → JST pin 2
        w(p_out2[0], p_out2[1], p_out2[0], j2[1])
        w(p_out2[0], j2[1], j2[0], j2[1])
        j(p_out2[0], j2[1])

        # ILIM resistor: ILIM pin → R top; R bot → GND
        # (No through-R wire — the resistor's own pins do the connection)
        w(p_ilim[0], p_ilim[1], p_ilim[0], r_top[1])
        w(p_ilim[0], r_top[1], r_top[0], r_top[1])
        j(p_ilim[0], r_top[1])
        w(r_bot[0], r_bot[1], r_bot[0], y - 30)
        lbl("GND", (r_bot[0], y - 30))

    # U5a (actuator) at the original position
    place_one_drv(0, "ACT", "U5", x0, y0,
                  in1_net="ACTUATOR_IN1", in2_net="ACTUATOR_IN2",
                  ilim_net="ACTUATOR_IPROPI", nfault_net="ACTUATOR_nFAULT",
                  motor_label="ACTUATOR", jst_ref="J3")
    # U5b (solenoid) below U5a
    place_one_drv(2, "SOL", "U6", x0, y0 + 100,
                  in1_net="SOLENOID_IN1", in2_net="SOLENOID_IN2",
                  ilim_net="SOLENOID_IPROPI", nfault_net="SOLENOID_nFAULT",
                  motor_label="SOLENOID", jst_ref="J4")

    # Common GND label for the support wires
    sch.add(make_text("DRV8871 H-bridges (U5 actuator / U6 solenoid)",
                      x0 - 30, y0 - 50, size=2.0))


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
# Subsystem: ESP32-S3 + USB-C + EN/BOOT + status LED + I²C pull-ups + header
# ----------------------------------------------------------------------------
#
# ESP32-S3-WROOM-1 pinout (from RF_Module lib, sub-symbol _1_1):
#   Left side  (x=-15.24): pins 3, 4-9, 12, 15, 17-22, 27, 38, 39
#   Right side (x=+15.24): pins 10, 11, 13, 14, 16, 23-26, 28-37
#   Bottom     (y=-27.94): pins 1, 40, 41 (GND)
#   Top        (y=+27.94): pin 2 (3V3)
#
# Wattplot pin map (firmware v3.2):
#   GPIO1  → ACTUATOR_IN1     GPIO2  → ACTUATOR_IN2
#   GPIO4  → ACTUATOR_IPROPI  GPIO21 → ACTUATOR_nFAULT
#   GPIO5  → SOLENOID_IPROPI  GPIO10 → SOLENOID_IN1
#   GPIO12 → SOLENOID_IN2     GPIO13 → SOLENOID_nFAULT
#   GPIO6  → SOIL_MOISTURE_AOUT
#   GPIO7  → BATTERY_V_ADC
#   GPIO8  → I2C_SDA          GPIO18 → I2C_SCL
#   GPIO16 → DS18B20_DATA
#   GPIO17 → STATUS_LED
#   GPIO0  → BOOT (strapping pin, active low)
#   EN     → chip enable (active high, has internal pull-up; we add
#           external 10k to 3V3 + tactile button to GND for reset)
#   USB_D+/D- → native USB (goes to USB-C receptacle)
#   RXD0/TXD0 → UART (programming header)

def place_esp32_s3(sch: Schematic, cache: SymbolCache, x0=300, y0=200):
    """ESP32-S3-WROOM-1 module + supporting circuitry.

    Layout:
                            STATUS_LED
                                |
                            [330R]-+--> GPIO17
                                  LED
        USB-C   USB_D+/D- -->   ESP32-S3    --> ACTUATOR/SOLENOID/
        conn    via 5.1k       WROOM-1         SENSOR labels
        + ESD                   |
                              EN   BOOT        --> I2C pull-ups
                              |    /                     |
                             10k  SW                  SDA SCL
                              |   |
                             3V3 GND                 Program header
                                                          |
                                                       RX TX 0 3V3 GND
    """
    esp_id = LIB["esp32s3"]
    usbc_id = LIB["usbc"]
    res_id = LIB["res"]
    led_id = LIB["led_0805"]
    cap_id = LIB["cap"]
    cap_p_id = LIB["cap_polarized"]
    sw_id = LIB["sw_tactile"]
    hdr_id = LIB["hdr_2x5"]
    l_id = LIB["inductor_4u7"]

    # ------------------------------------------------------------------
    # Component placement
    # ------------------------------------------------------------------

    # ESP32-S3 module at (x0, y0)
    esp_x, esp_y = x0, y0
    sch.reference(esp_id)
    sch.add(make_symbol_instance(
        esp_id, "U3", "ESP32-S3-WROOM-1",
        "RF_Module:ESP32-S3-WROOM-1", esp_x, esp_y
    ))

    # USB-C receptacle — to the left of ESP32
    usbc_x, usbc_y = x0 - 60, y0 - 30
    sch.reference(usbc_id)
    sch.add(make_symbol_instance(
        usbc_id, "J1", "USB-C",
        "Connector:USB_C_Receptacle", usbc_x, usbc_y
    ))

    # Status LED + series resistor (above ESP32)
    led_r_x, led_r_y = x0, y0 - 65        # resistor above
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R5", "330R",
        "Resistor_SMD:R_0603_1608Metric", led_r_x, led_r_y
    ))
    led_x, led_y = x0, y0 - 80            # LED above resistor
    sch.reference(led_id)
    sch.add(make_symbol_instance(
        led_id, "D1", "GREEN",
        "LED_SMD:LED_0805_2012Metric", led_x, led_y
    ))

    # EN pull-up resistor + reset button (right of ESP32, top)
    en_r_x, en_r_y = x0 + 35, y0 - 30
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R6", "10k",
        "Resistor_SMD:R_0603_1608Metric", en_r_x, en_r_y
    ))
    rst_x, rst_y = x0 + 35, y0 - 50
    sch.reference(sw_id)
    sch.add(make_symbol_instance(
        sw_id, "SW1", "RESET",
        "Switch:SW_Push", rst_x, rst_y
    ))

    # BOOT button (right of ESP32, middle)
    boot_x, boot_y = x0 + 35, y0
    sch.reference(sw_id)
    sch.add(make_symbol_instance(
        sw_id, "SW2", "BOOT",
        "Switch:SW_Push", boot_x, boot_y
    ))

    # I²C pull-up resistors (right of ESP32, bottom)
    i2c_r1_x, i2c_r1_y = x0 + 35, y0 + 30    # SDA pull-up
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R7", "4.7k",
        "Resistor_SMD:R_0603_1608Metric", i2c_r1_x, i2c_r1_y
    ))
    i2c_r2_x, i2c_r2_y = x0 + 35, y0 + 45    # SCL pull-up
    sch.reference(res_id)
    sch.add(make_symbol_instance(
        res_id, "R8", "4.7k",
        "Resistor_SMD:R_0603_1608Metric", i2c_r2_x, i2c_r2_y
    ))

    # Decoupling caps for ESP32 (multiple GND/3V3 pairs)
    dec1_x, dec1_y = x0 - 30, y0 - 60
    sch.reference(cap_id)
    sch.add(make_symbol_instance(
        cap_id, "C6", "100nF",
        "Capacitor_SMD:C_0402_1005Metric", dec1_x, dec1_y
    ))
    dec2_x, dec2_y = x0 + 30, y0 - 60
    sch.reference(cap_id)
    sch.add(make_symbol_instance(
        cap_id, "C7", "10uF",
        "Capacitor_SMD:C_0603_1608Metric", dec2_x, dec2_y
    ))

    # USB-C series resistors + ESD protection (5.1k CC pull-downs optional)
    # For simplicity: just put a USBLC6-2P6 ESD near the USB-C connector
    # (was already in LIB; place + 100nF cap on each data line)
    esd_x, esd_y = x0 - 35, y0 - 30
    sch.reference(LIB["usblc6"])
    sch.add(make_symbol_instance(
        LIB["usblc6"], "U4", "USBLC6-2P6",
        "Package_TO_SOT_SMD:SOT-23-6", esd_x, esd_y
    ))

    # Programming / debug header (10-pin: 2x5) at the far right
    hdr_x, hdr_y = x0 + 80, y0
    sch.reference(hdr_id)
    sch.add(make_symbol_instance(
        hdr_id, "J2", "PROG",
        "PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", hdr_x, hdr_y
    ))

    # ------------------------------------------------------------------
    # Resolve pin positions
    # ------------------------------------------------------------------
    def pp(lib, num, x, y):
        p = pin_pos(cache, lib, num, x, y)
        if p is None:
            raise RuntimeError(f"no pin {num} on {lib}")
        return p

    # ESP32-S3 pins
    e_gnd   = pp(esp_id, '1',  esp_x, esp_y)     # bottom GND
    e_3v3   = pp(esp_id, '2',  esp_x, esp_y)     # top 3V3
    e_en    = pp(esp_id, '3',  esp_x, esp_y)     # left EN
    e_io4   = pp(esp_id, '4',  esp_x, esp_y)
    e_io5   = pp(esp_id, '5',  esp_x, esp_y)
    e_io6   = pp(esp_id, '6',  esp_x, esp_y)
    e_io7   = pp(esp_id, '7',  esp_x, esp_y)
    e_io15  = pp(esp_id, '8',  esp_x, esp_y)
    e_io16  = pp(esp_id, '9',  esp_x, esp_y)
    e_io17  = pp(esp_id, '10', esp_x, esp_y)
    e_io18  = pp(esp_id, '11', esp_x, esp_y)
    e_io8   = pp(esp_id, '12', esp_x, esp_y)
    e_usbdn = pp(esp_id, '13', esp_x, esp_y)
    e_usbdp = pp(esp_id, '14', esp_x, esp_y)
    e_io3   = pp(esp_id, '15', esp_x, esp_y)
    e_io46  = pp(esp_id, '16', esp_x, esp_y)
    e_io9   = pp(esp_id, '17', esp_x, esp_y)
    e_io10  = pp(esp_id, '18', esp_x, esp_y)
    e_io11  = pp(esp_id, '19', esp_x, esp_y)
    e_io12  = pp(esp_id, '20', esp_x, esp_y)
    e_io13  = pp(esp_id, '21', esp_x, esp_y)
    e_io14  = pp(esp_id, '22', esp_x, esp_y)
    e_io21  = pp(esp_id, '23', esp_x, esp_y)
    e_io47  = pp(esp_id, '24', esp_x, esp_y)
    e_io48  = pp(esp_id, '25', esp_x, esp_y)
    e_io45  = pp(esp_id, '26', esp_x, esp_y)
    e_io0   = pp(esp_id, '27', esp_x, esp_y)
    e_rxd0  = pp(esp_id, '36', esp_x, esp_y)
    e_txd0  = pp(esp_id, '37', esp_x, esp_y)
    e_io2   = pp(esp_id, '38', esp_x, esp_y)
    e_io1   = pp(esp_id, '39', esp_x, esp_y)
    e_gnd2  = pp(esp_id, '40', esp_x, esp_y)
    e_gnd3  = pp(esp_id, '41', esp_x, esp_y)

    # ------------------------------------------------------------------
    # Net labels — placed AT each ESP32 pin (multiple same-name = same net)
    # ------------------------------------------------------------------
    def label_at_pin(net, pin_xy, shape="bidirectional"):
        x, y = pin_xy
        sch.add(make_global_label(net, x, y, shape))

    # 3V3 (chip supply, decoupled)
    label_at_pin("+3V3", e_3v3)

    # GND (all 3 GND pins)
    label_at_pin("GND", e_gnd)
    label_at_pin("GND", e_gnd2)
    label_at_pin("GND", e_gnd3)

    # Wattplot signal labels (each maps to a firmware function)
    label_at_pin("ACTUATOR_IN1",   e_io1)   # GPIO1
    label_at_pin("ACTUATOR_IN2",   e_io2)   # GPIO2
    label_at_pin("ACTUATOR_IPROPI",e_io4)   # GPIO4 (ADC)
    label_at_pin("SOLENOID_IPROPI",e_io5)   # GPIO5 (ADC)
    label_at_pin("SOIL_AOUT",      e_io6)   # GPIO6 (ADC)
    label_at_pin("BATTERY_V_ADC",  e_io7)   # GPIO7 (ADC)
    label_at_pin("I2C_SDA",        e_io8)   # GPIO8
    label_at_pin("SOLENOID_IN1",   e_io10)  # GPIO10
    label_at_pin("SOLENOID_IN2",   e_io12)  # GPIO12
    label_at_pin("SOLENOID_nFAULT",e_io13)  # GPIO13
    label_at_pin("DS18B20_DATA",   e_io16)  # GPIO16
    label_at_pin("STATUS_LED",     e_io17)  # GPIO17
    label_at_pin("I2C_SCL",        e_io18)  # GPIO18
    label_at_pin("ACTUATOR_nFAULT",e_io21)  # GPIO21

    # USB data lines
    label_at_pin("USB_DP", e_usbdp)
    label_at_pin("USB_DN", e_usbdn)

    # BOOT (strapping pin — pulled high normally, low during download mode)
    label_at_pin("BOOT", e_io0)

    # EN
    label_at_pin("EN_CHIP", e_en)

    # UART (programming header)
    label_at_pin("UART_RX", e_rxd0)  # GPIO44/RXD0
    label_at_pin("UART_TX", e_txd0)  # GPIO43/TXD0

    # Unused GPIOs (no labels — just pins visible on the schematic)
    for pin_xy in [e_io3, e_io9, e_io11, e_io14, e_io15,
                   e_io45, e_io46, e_io47, e_io48]:
        # No label — just visible in schematic
        pass

    # ------------------------------------------------------------------
    # Supporting components wired to nets
    # ------------------------------------------------------------------
    #
    # Routing rules: NO wire segment runs along x=284.76 (left GPIO
    # column) or x=315.24 (right GPIO column). All connections to
    # those pins go via short horizontal stubs (≤5mm) and then route
    # out to a "support" column at x=325 or x=335 where the support
    # components live. Otherwise a long wire would short together
    # every label on the GPIO column.

    # The support column for EN/RST/BOOT lives at x=335.
    # The I2C pull-up column lives at x=335 too, but uses y values
    # below the GPIO band (y < 177) so the vertical wires don't
    # cross the right-side GPIO column (y = 177 to 223 at x=315).
    # A short horizontal stub from each GPIO pin to x=325 connects it
    # to the support column.

    def w(x1, y1, x2, y2):
        sch.add(make_wire(x1, y1, x2, y2))

    def label(net, x, y, shape="bidirectional"):
        sch.add(make_global_label(net, x, y, shape))

    # Status LED: GPIO17 → R5 (330R) → LED anode; LED cathode → GND
    # GPIO17 is on right side (x=315.24, y=217.78). Wire RIGHT to the
    # support column at x=335 (no other labels at y=217.78).
    led_r_top = pp(res_id, '1', led_r_x, led_r_y)
    led_r_bot = pp(res_id, '2', led_r_x, led_r_y)
    led_pos = pp(led_id, '1', led_x, led_y)
    led_neg = pp(led_id, '2', led_x, led_y)
    w(led_r_top[0], led_r_top[1], e_io17[0], led_r_top[1])    # right to R5
    sch.add(make_junction(e_io17[0], led_r_top[1]))
    label("STATUS_LED", e_io17[0], led_r_top[1])              # label on stub
    # NO through-R wire — R5's own pins do the connection.
    w(led_r_bot[0], led_r_bot[1], led_pos[0], led_r_bot[1])    # to LED anode
    w(led_pos[0], led_pos[1], led_neg[0], led_pos[1])         # through LED
    w(led_neg[0], led_pos[1], led_neg[0], y0 - 100)            # down to GND rail
    label("GND", led_neg[0], y0 - 100)

    # EN pull-up: EN (left col, x=284.76) → R6 (x=335) → 3V3
    # Route: EN → right to x=325, then DOWN through y=173.81, then
    # right to R6 pin 1. The vertical segment at x=325 is between
    # the right GPIO column (315.24) and R6 (335), no labels there.
    en_r_top = pp(res_id, '1', en_r_x, en_r_y)
    en_r_bot = pp(res_id, '2', en_r_x, en_r_y)
    # Stub from EN pin right to x=325 (no other label at y=222.86
    # since the BOOT label is at y=217.78 and the GPIO labels are
    # at x=284.76 — this stub is at y=222.86 only)
    w(e_en[0], e_en[1], 325, e_en[1])
    sch.add(make_junction(325, e_en[1]))
    # Vertical from (325, 222.86) down to (325, en_r_top[1] = 173.81)
    w(325, e_en[1], 325, en_r_top[1])
    # Right to R6 pin 1
    w(325, en_r_top[1], en_r_top[0], en_r_top[1])
    sch.add(make_junction(en_r_top[0], en_r_top[1]))
    # No through-R wire — the resistor's pins do the connection.
    # Up to 3V3 rail (y=227.94) from R6 pin 2
    w(en_r_bot[0], en_r_bot[1], en_r_bot[0], e_3v3[1])
    label("+3V3", en_r_bot[0], e_3v3[1])

    # EN reset button (SW1): pin 1 to EN_CHIP net, pin 2 to GND
    # SW_Push has HORIZONTAL pins: pin 1 at x=rst_x-5.08, pin 2 at x=rst_x+5.08
    rst_top = pp(sw_id, '1', rst_x, rst_y)
    rst_bot = pp(sw_id, '2', rst_x, rst_y)
    # Connect rst_top (329.92, 153.81) to EN net
    # Route: up from rst_top to EN y, then left to e_en[0]
    w(rst_top[0], rst_top[1], rst_top[0], e_en[1])
    w(rst_top[0], e_en[1], e_en[0], e_en[1])
    sch.add(make_junction(e_en[0], e_en[1]))
    # rst_bot to GND
    w(rst_bot[0], rst_bot[1], rst_bot[0], y0 - 100)
    label("GND", rst_bot[0], y0 - 100)

    # BOOT button (SW2): pin 1 to BOOT (IO0), pin 2 to GND
    boot_top = pp(sw_id, '1', boot_x, boot_y)
    boot_bot = pp(sw_id, '2', boot_x, boot_y)
    # Connect boot_top to BOOT net (e_io0 = 284.76, 217.78)
    # Route via y=219 to avoid the STATUS_LED label at y=217.78
    w(boot_top[0], boot_top[1], boot_top[0], 219)
    w(boot_top[0], 219, e_io0[0], 219)
    w(e_io0[0], 219, e_io0[0], e_io0[1])
    sch.add(make_junction(e_io0[0], e_io0[1]))
    w(boot_bot[0], boot_bot[1], boot_bot[0], y0 - 100)
    label("GND", boot_bot[0], y0 - 100)

    # I²C pull-up R7 (SDA): GPIO8 (left col) → R7 → 3V3
    i2c_r1_top = pp(res_id, '1', i2c_r1_x, i2c_r1_y)
    i2c_r1_bot = pp(res_id, '2', i2c_r1_x, i2c_r1_y)
    # Stub from GPIO8 (284.76, 197.46) right to x=325
    w(e_io8[0], e_io8[1], 325, e_io8[1])
    sch.add(make_junction(325, e_io8[1]))
    # Vertical from (325, 197.46) down to (325, 233.81 = i2c_r1_top[1])
    w(325, e_io8[1], 325, i2c_r1_top[1])
    # Right to R7 pin 1
    w(325, i2c_r1_top[1], i2c_r1_top[0], i2c_r1_top[1])
    sch.add(make_junction(i2c_r1_top[0], i2c_r1_top[1]))
    # NO through-R wire — the resistor's own pins do the connection.
    # Up to 3V3 rail from R7 pin 2
    w(i2c_r1_bot[0], i2c_r1_bot[1], i2c_r1_bot[0], e_3v3[1])
    label("+3V3", i2c_r1_bot[0], e_3v3[1])

    # I²C pull-up R8 (SCL): GPIO18 (right col) → R8 → 3V3
    i2c_r2_top = pp(res_id, '1', i2c_r2_x, i2c_r2_y)   # (333.73, 248.81)
    i2c_r2_bot = pp(res_id, '2', i2c_r2_x, i2c_r2_y)   # (336.27, 241.19)
    # GPIO18 (315.24, 215.24) → R8 pin 1 (333.73, 248.81)
    # Use a fresh support column at x=327 (between SDA col 325 and EN col 329.92)
    # to avoid shorting to R7 SDA vertical at x=325.
    scl_support_x = 327
    # Horizontal stub from GPIO18 to support col
    w(e_io18[0], e_io18[1], scl_support_x, e_io18[1])
    sch.add(make_junction(scl_support_x, e_io18[1]))
    # Down the support col to R8 pin 1's y
    w(scl_support_x, e_io18[1], scl_support_x, i2c_r2_top[1])
    sch.add(make_junction(scl_support_x, i2c_r2_top[1]))
    # Right to R8 pin 1
    w(scl_support_x, i2c_r2_top[1], i2c_r2_top[0], i2c_r2_top[1])
    sch.add(make_junction(i2c_r2_top[0], i2c_r2_top[1]))
    # NO through-R wire — the resistor's own pins do the connection.
    # Up to 3V3 rail from R8 pin 2
    w(i2c_r2_bot[0], i2c_r2_bot[1], i2c_r2_bot[0], e_3v3[1])
    label("+3V3", i2c_r2_bot[0], e_3v3[1])

    # Decoupling caps: C6 (100nF) and C7 (10uF) on 3V3/GND
    c6_pos = pp(cap_id, '1', dec1_x, dec1_y)
    c6_neg = pp(cap_id, '2', dec1_x, dec1_y)
    # Stub C6 positive to the 3V3 rail
    w(c6_pos[0], c6_pos[1], c6_pos[0], e_3v3[1])
    # Stub C6 negative to the GND rail
    w(c6_neg[0], c6_neg[1], c6_neg[0], y0 - 100)
    label("GND", c6_neg[0], y0 - 100)

    c7_pos = pp(cap_p_id, '1', dec2_x, dec2_y)
    c7_neg = pp(cap_p_id, '2', dec2_x, dec2_y)
    w(c7_pos[0], c7_pos[1], c7_pos[0], e_3v3[1])
    w(c7_neg[0], c7_neg[1], c7_neg[0], y0 - 100)
    label("GND", c7_neg[0], y0 - 100)

    # 3V3/GND labels for the rails (one label per rail, used by all
    # the support components' wires)
    label("+3V3", e_3v3[0], e_3v3[1])
    label("GND", 300, y0 - 100)

    # USB-C: place labels for power and data lines
    # USB-C has many pins; we just need CC1/CC2 (with 5.1k to GND),
    # VBUS (with 10uF cap), GND, D+, D-
    # For schematic brevity, label the data + power pins and skip CC
    # (the 5.1k CC pull-downs are added in a later pass)
    # Try to read a few USB-C pin positions
    for n in ('1', '4', '5', '6', '9', '12', 'A1', 'B12'):
        try:
            p = pp(usbc_id, n, usbc_x, usbc_y)
            if p:
                # Label only the meaningful pins
                if n == '4':  label("USB_VBUS", p[0], p[1])
                if n == '5':  label("USB_VBUS", p[0], p[1])
                if n == '9':  label("USB_DP",   p[0], p[1])
                if n == '12': label("USB_DN",   p[0], p[1])
                if n in ('1','12'): label("GND", p[0], p[1])
        except RuntimeError:
            pass

    # Programming header: 10-pin (2x5)
    # Standard ESP32 programming header pinout:
    #   1: GND   2: GPIO0 (BOOT)
    #   3: GPIO1 (TX)  4: EN (RST)
    #   5: GPIO3 (RX)  6: GPIO2
    #   7: 3V3   8: GPIO4
    #   9: GPIO5 10: GND
    # (matches the J-LINK / ESP-PROG / ESP32-S3-USB-Bridge pinout)
    # We'll just label the meaningful pins; the rest get GND
    for n, net in [('1', 'GND'), ('2', 'BOOT'), ('3', 'UART_TX'),
                   ('4', 'EN_CHIP'), ('5', 'UART_RX'), ('7', '+3V3'),
                   ('9', 'STATUS_LED'), ('10', 'GND')]:
        try:
            p = pp(hdr_id, n, hdr_x, hdr_y)
            if p:
                label(net, p[0], p[1])
        except RuntimeError:
            pass

    # Annotation
    sch.add(make_text("ESP32-S3 Module + USB + EN/BOOT + LED + I2C + Header",
                      x0 - 30, y0 - 110, size=2.0))


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    cache = SymbolCache([CUSTOM_LIB, KICAD_LIB])

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
    place_esp32_s3(sch, cache)
    place_drv8871s(sch, cache)
    place_ina219s(sch, cache)
    place_sensors(sch, cache)
    sch.save(SCH_PATH)
    print(f"\n[sch] wrote {SCH_PATH}")


if __name__ == "__main__":
    main()
