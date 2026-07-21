"""
Wattplot v2 — Custom PCB block diagram.
Uses schemdraw's Ic element for block boxes.
"""

import os
import schemdraw
import schemdraw.elements as elm


def block(d, x, y, w, h, title, sub="", ref=""):
    """Add a labeled rectangular block centered at (x, y) using Ic."""
    d.here = (x, y)
    d.push()
    # Ic with no pins, just a rectangle
    d += elm.Ic(size=(w, h), pins=[])
    d.pop()
    # Add labels
    d += elm.Label().at((x, y + h/2 - 0.3)).label(title, fontsize=10, halign='center')
    if sub:
        d += elm.Label().at((x, y - 0.2)).label(sub, fontsize=7, halign='center', color='gray')
    if ref:
        d += elm.Label().at((x - w/2 + 0.15, y + h/2 - 0.15)).label(ref, fontsize=7, color='red')


def main():
    with schemdraw.Drawing(show=False) as d:
        d.config(unit=2.0, fontsize=10)

        # Title
        d += elm.Label().at((0, 9.5)).label('Wattplot Controller v1 — Custom PCB Block Diagram',
                                            fontsize=12, halign='center')
        d += elm.Label().at((0, 9.0)).label('80×60mm 2-layer · 12V input · ESP32-WROOM-32E · DRV8871 H-bridge',
                                            fontsize=8, halign='center', color='gray')

        # === Power input (left) ===
        d += elm.Battery().at((-8, 6)).right().label('12V\nbattery', loc='left')
        d += elm.Line().right().length(1.0)
        d += elm.Dot()
        d += elm.Label().at((-7.0, 6.4)).label('12V rail', color='red', fontsize=8)

        d += elm.Battery().at((-8, 3)).right().label('20W\nsolar', loc='left')
        d += elm.Line().right().length(1.0)
        d += elm.Line().up().length(2.0).at((-7, 3.5))
        d += elm.Dot()
        d += elm.Label().at((-7.5, 4.5)).label('MPPT\nctrl', loc='left', fontsize=7, color='gray')

        # === 12V → 5V buck ===
        block(d, -4.5, 6, 1.6, 1.4, 'MP1584', '12V→5V buck', 'U2')
        d += elm.Line().at((-3.7, 6)).right().length(0.8)
        d += elm.Dot()
        d += elm.Label().at((-2.7, 6.4)).label('5V rail', color='red', fontsize=8)

        # === 5V → 3.3V LDO ===
        block(d, -1.5, 6, 1.6, 1.4, 'AMS1117', '5V→3.3V LDO', 'U3')
        d += elm.Line().at((-0.7, 6)).right().length(0.8)
        d += elm.Dot()
        d += elm.Label().at((0.2, 6.4)).label('3V3 rail', color='red', fontsize=8)

        # === ESP32 (center) ===
        block(d, 0, 3, 3.0, 1.6, 'ESP32-WROOM-32E', 'WiFi · MCU · USB-C', 'U1')

        # Power rail down to ESP32
        d += elm.Line().at((0.5, 5.3)).down().toy((0.5, 3.8))
        d += elm.Label().at((0.7, 4.5)).label('3V3', color='red', fontsize=7)

        # === USB-C (above ESP32) ===
        block(d, 0, 5.5, 1.4, 0.8, 'USB-C', 'program', 'J1')
        d += elm.Line().at((0, 5.1)).down().toy((0, 3.8))

        # === Anemometer input (left of ESP32) ===
        block(d, -4.5, 3, 1.6, 0.8, 'Cup anem.', 'pulse out', 'EXT1')
        d += elm.Line().at((-3.7, 3)).right().toy((-3.3, 3))
        d += elm.Line().down().toy((-3.3, 2.5))
        block(d, -3.3, 2.3, 0.6, 0.6, 'ST', '', 'U4')
        d += elm.Line().at((-3.0, 2.3)).right().toy((-1.7, 2.3))
        d += elm.Line().up().toy((-1.7, 2.5))
        d += elm.Dot()
        d += elm.Label().at((-2.5, 1.8)).label('GPIO34', color='blue', fontsize=7)

        # === H-bridge (right of ESP32) ===
        block(d, 3.0, 3, 1.6, 1.4, 'DRV8871', 'H-bridge', 'U5')
        d += elm.Line().at((1.5, 3)).right().toy((2.2, 3))
        d += elm.Dot()
        d += elm.Label().at((1.7, 3.3)).label('IN1, IN2', color='blue', fontsize=7)

        # 12V to H-bridge
        d += elm.Line().at((3.0, 3.7)).up().toy((3.0, 5.3))
        d += elm.Line().at((3.0, 5.3)).left().tox((-2.0, 5.3))
        d += elm.Label().at((0.5, 5.5)).label('12V motor', color='red', fontsize=7)

        # === Linear actuator ===
        block(d, 5.5, 3, 1.8, 1.4, 'Linear actuator', '12V, 4-12" stroke', 'MOT1')
        d += elm.Line().at((3.8, 3)).right().toy((4.6, 3))
        d += elm.Dot()
        d += elm.Label().at((4.0, 3.3)).label('OUT1, OUT2', color='red', fontsize=7)
        d += elm.Label().at((5.5, 2.0)).label('→ panel tilt', fontsize=7, halign='center', color='gray')

        # === Limit switches (below ESP32) ===
        block(d, -1, 1.2, 2.4, 0.8, 'Limit switches', '0° + 90° NO roller', 'J2')
        d += elm.Line().at((0, 2.2)).down().toy((0, 1.6))
        d += elm.Label().at((0.4, 1.8)).label('GPIO32, 35', color='blue', fontsize=7)

        # === Optional sensors ===
        block(d, 3, 1.2, 2.4, 0.8, 'BME280 + ADXL345', 'env + tilt', 'U6')
        d += elm.Line().at((1.0, 2.2)).down().toy((1.0, 1.6))
        d += elm.Label().at((1.4, 1.8)).label('I²C', color='green', fontsize=7)

        # === Status LED ===
        d += elm.LED().at((-3, 0.8)).right().label('WS2812B\nGPIO25', loc='bottom', fontsize=7, color='gray')

        # === Bottom annotations ===
        d += elm.Label().at((0, -0.3)).label('Power: 12V → MP1584 → 5V → AMS1117 → 3V3 → ESP32',
                                            fontsize=8, halign='center', color='gray')
        d += elm.Label().at((0, -0.8)).label('Signal: anemometer → Schmitt → ESP32 → DRV8871 → actuator',
                                            fontsize=8, halign='center', color='gray')
        d += elm.Label().at((0, -1.3)).label('Safety: limit switches → ESP32 → H-bridge EN (cuts power on end-stop)',
                                            fontsize=8, halign='center', color='gray')
        d += elm.Label().at((0, -2.0)).label('BOM @ 1k ≈ $15-22/board · 5 assembled ≈ $100 @ JLCPCB · ~1 wk turnaround',
                                            fontsize=8, halign='center', color='gray')
        d += elm.Label().at((0, -2.5)).label('Schematic: SKiDL (Python) → netlist → KiCad layout',
                                            fontsize=8, halign='center', color='gray')
        d += elm.Label().at((0, -3.2)).label('Enclosure: IP65 ABS, 120×80×50mm, 4× M3 mount',
                                            fontsize=8, halign='center', color='gray')

        out = os.path.join(os.path.dirname(__file__), "..", "renders", "wattplot_v2_pcb_schematic.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        d.save(out)
        print(f"[schem] wrote {out}")


if __name__ == "__main__":
    main()
