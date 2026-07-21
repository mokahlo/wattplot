# Wattplot Controller v1 — PCB Design Specification

The custom PCB for the Wattplot v2 smart-folding controller. This document is
the complete specification: schematic, netlist, BOM, board layout, and
assembly notes. Hand it to KiCad / EasyEDA / JLCPCB's free DFM service to
produce the actual board.

**Source of truth:** `firmware/wattplot.yaml` defines the pin map. The PCB
matches it 1:1.

---

## 1. Block diagram

```
                              ┌──────────────────────────────────────┐
                              │  Wattplot Controller v1 (50×70 mm)  │
                              │                                      │
   12V LiFePO4  ──────────────►│ J1 (XT60) ──► 12V rail            │
                              │                  │                  │
                              │            ┌─────▼─────┐            │
                              │            │  12V→5V    │  buck      │
                              │            │  (MP1584)  │  switching │
                              │            └─────┬─────┘            │
                              │                  │                  │
                              │            ┌─────▼─────┐            │
                              │            │  5V→3.3V  │  LDO       │
                              │            │  (AMS1117)│            │
                              │            └─────┬─────┘            │
                              │                  │                  │
   ESP32-WROOM-32E ◄─────────┤ 3V3 rail          │                  │
   (USB-C, WiFi/BT ant.)    │                  │                  │
                              │   ┌──────────────┼──────────────┐   │
                              │   │              │              │   │
                              │   ▼              ▼              ▼   │
                              │ GPIO16/17/18   GPIO21/22      GPIO26/27│
                              │   │              │              │   │
                              │ ┌─▼──┐    ┌─────▼─────┐  ┌─────▼─────┐│
                              │ │DRV │    │ I2C bus   │  │ UART2      ││
                              │ │8871│    │ (3V3)     │  │ (3V3)      ││
                              │ │    │    │  BMI160   │  │  DPS5005   ││
                              │ └─┬──┘    │  INA219   │  │  MPPT ctrl ││
                              │   │       │  ext hdr  │  └───────────┘│
                              │   │       └───────────┘                │
                              │   │                                     │
                              │   ▼                                     │
                              │  Linear actuator (4" stroke)          │
                              │                                      │
   Battery V sense ──────────►│ GPIO33 (10k/10k divider)             │
   Soil moisture ────────────►│ GPIO32 (capacitive, 0-3V)            │
   DS18B20 ──────────────────►│ GPIO4  (4.7k pullup to 3V3)          │
   WS2812B status LED ───────►│ GPIO25                              │
   Limit switch 0° ──────────►│ GPIO34 (external 10k pullup)        │
   Limit switch 90° ─────────►│ GPIO35 (external 10k pullup)        │
   Grow light relay ─────────►│ GPIO19 (low-side switch, 12V)       │
                              │                                      │
                              │ J2 (4-pin) ext I2C + 3V3 + GND        │
                              └──────────────────────────────────────┘
```

---

## 2. Power tree

Three rails, derived from a 12 V LiFePO4 battery:

| Rail | Source | Max current | Used by |
|---|---|---|---|
| **12 V** | J1 (XT60 from battery) | 5 A (fuse) | Grow light relay, DPS5005 input, DRV8871 motor supply |
| **5 V** | MP1584EN buck from 12 V | 3 A | (reserved; USB-C 5V also feeds here for programming) |
| **3.3 V** | AMS1117-3.3 LDO from 5 V | 1 A (peak ~800 mA) | ESP32, BMI160, INA219, DS18B20, DPS5005 logic, WS2812B |

**Battery fuse:** 5 A resettable PTC on the 12 V input (DRV8871 is rated 3.6 A
continuous; 5 A gives headroom for stall currents).

**Reverse polarity protection:** P-MOSFET on the 12 V input (e.g., AO3401A).

**Power flow on startup:**
1. Battery → 12 V rail (through fuse + reverse-polarity protection)
2. 12 V → 5 V (MP1584)
3. 5 V → 3.3 V (AMS1117)
4. ESP32 boots from 3.3 V
5. ESPHome starts, queries IMU/DPS5005/INA219 over I2C/UART, reads sensors
6. State machine boots in `FOLDING` (safe default) per firmware

---

## 3. Component BOM (PCB-level)

| Designator | Part | Package | Source | Qty | ~$ ea |
|---|---|---|---|---|---|
| U1 | ESP32-WROOM-32E (16 MB flash) | module | Mouser / Espressif | 1 | 3.50 |
| U2 | MP1584EN buck regulator (12V→5V, 3A) | SOIC-8 | TI / LCSC | 1 | 0.40 |
| U3 | AMS1117-3.3 LDO (5V→3V3, 1A) | SOT-223 | TI / LCSC | 1 | 0.10 |
| U4 | DRV8871 H-bridge motor driver | WSON-8 | TI / LCSC | 1 | 1.80 |
| U5 | BMI160 IMU (I2C, 0x68) | LGA-14 | Bosch / Mouser | 1 | 2.00 |
| U6 | INA219 current/power sensor (I2C, 0x40) | SOIC-8 | TI / LCSC | 1 | 1.20 |
| U7 | AO3401A P-MOSFET (reverse polarity) | SOT-23 | LCSC | 1 | 0.05 |
| Q1 | BC847 NPN (grow light relay driver) | SOT-23 | LCSC | 1 | 0.02 |
| K1 | SRD-12VDC-SL-C relay (or SSR-25DA, 12V coil) | through-hole | TME / LCSC | 1 | 0.80 |
| F1 | 5 A resettable PTC fuse (Bourns MF-R050) | radial | LCSC | 1 | 0.20 |
| L1 | 22 µH 3A inductor (for MP1584) | SMD 4×4 mm | Coilcraft / LCSC | 1 | 0.30 |
| L2 | 10 µH (for DRV8871 output filter, optional) | SMD | LCSC | 1 | 0.20 |
| C_bulk | 100 µF 25 V aluminum polymer (12 V rail) | SMD 6.3×5.4 mm | Panasonic | 2 | 0.40 |
| C_5V | 22 µF 10 V ceramic (5 V rail) | SMD 0805 | Murata | 2 | 0.10 |
| C_3V3 | 10 µF 10 V ceramic (3.3 V rail) | SMD 0805 | Murata | 2 | 0.10 |
| C_bypass | 100 nF 16 V ceramic (each IC) | SMD 0402 | Murata | 12 | 0.01 |
| D1 | SS34 Schottky (reverse polarity clamp) | SMA | ON Semi | 1 | 0.10 |
| D2 | 1N4148 (flyback for relay) | SOD-123 | ON Semi | 1 | 0.02 |
| LED1 | WS2812B (status) | 5050 | Worldsemi | 1 | 0.40 |
| J1 | XT60 connector (12 V battery) | through-hole | Amass | 1 | 0.80 |
| J2 | 4-pin JST-XH (I2C breakout: 3V3, GND, SDA, SCL) | through-hole | JST | 1 | 0.20 |
| J3 | USB-C receptacle (USB 2.0, 16-pin) | SMD | GCT | 1 | 0.50 |
| J4 | 4-pin JST-XH (DPS5005 UART: 3V3, GND, TX, RX) | through-hole | JST | 1 | 0.20 |
| J5 | 3-pin JST-XH (grow light: 12V, GND, switched) | through-hole | JST | 1 | 0.15 |
| J6 | 2-pin JST-XH (actuator: motor A, motor B) | through-hole | JST | 1 | 0.15 |
| J7 | 3-pin JST-XH (limit switches 0° + 90° + GND) | through-hole | JST | 1 | 0.15 |
| J8 | 3-pin JST-XH (DS18B20: data, 3V3, GND) | through-hole | JST | 1 | 0.15 |
| J9 | 2-pin JST-XH (soil moisture: signal, GND) | through-hole | JSC | 1 | 0.15 |
| J10 | 2-pin JST-XH (battery sense: divided, GND) | through-hole | JST | 1 | 0.15 |
| SW1 | Tactile switch (BOOT) | SMD 6×6 | C&K | 1 | 0.10 |
| SW2 | Tactile switch (RESET) | SMD 6×6 | C&K | 1 | 0.10 |

**PCB-level BOM total: 1 × PCB ($5, JLCPCB 5pcs) + ~$30 in components × 1 = $35 per board**

---

## 4. ESP32 pin map (matches firmware/wattplot.yaml)

| GPIO | Function | Connector | Notes |
|---|---|---|---|
| 4 | DS18B20 data (1-Wire) | J8 | 4.7 kΩ pullup to 3V3 on PCB |
| 16 | DRV8871 IN1 | U4 | H-bridge direction 1 |
| 17 | DRV8871 IN2 | U4 | H-bridge direction 2 |
| 18 | DRV8871 EN | U4 | H-bridge enable (PWM-able) |
| 19 | Q1 base (grow light relay) | J5 via K1 | Low-side NPN switch |
| 21 | I2C SDA | I2C bus (J2, U5, U6) | 4.7 kΩ pullup to 3V3 on PCB |
| 22 | I2C SCL | I2C bus (J2, U5, U6) | 4.7 kΩ pullup to 3V3 on PCB |
| 25 | WS2812B data | LED1 | 100 Ω series resistor |
| 26 | UART2 TX → DPS5005 RX | J4 | 3.3 V logic, level already matched |
| 27 | UART2 RX ← DPS5005 TX | J4 | |
| 32 | Soil moisture ADC1_CH4 | J9 | 0–3.3 V input |
| 33 | Battery voltage ADC1_CH5 | J10 | Divided 10k/10k from 12V |
| 34 | Limit switch 0° | J7 | Input only; external 10k pullup |
| 35 | Limit switch 90° | J7 | Input only; external 10k pullup |
| EN | RESET button (SW2) | — | Standard ESP32 reset |
| GPIO0 | BOOT button (SW1) | — | For USB flashing |

**Avoided pins (strapping / ADC2 / flash):** GPIO 0, 2, 5, 12, 15 are
strapping pins. GPIO 6–11 are flash pins. ADC2 is unusable when WiFi is
on, so we use ADC1_CH4 (GPIO32) and ADC1_CH5 (GPIO33) for analog.

---

## 5. Netlist (signal-level)

```
NET_12V = J1.p1, F1.in, U2.VIN, K1.coil+, J5.pin1
NET_GND = J1.p2, F1.out, U2.GND, U3.GND, U4.GND, U5.GND, U6.GND,
         U7.S, Q1.E, K1.coil-, all J*.pin(GND), all C_bypass.GND

NET_5V  = U2.VOUT, U3.VIN, U4.VM (motor supply, optional)
NET_3V3 = U3.VOUT, U1.3V3, U5.VDD, U6.VDD, R_pullup_I2C.top,
         R_pullup_DQ.top, LED1.VDD, J2.pin1, J4.pin1, J8.pin2

NET_SDA = U1.GPIO21, U5.SDA, U6.SDA, J2.pin3
NET_SCL = U1.GPIO22, U5.SCL, U6.SCL, J2.pin4

NET_MOTOR_A = U4.OUT1, J6.pin1
NET_MOTOR_B = U4.OUT2, J6.pin2
NET_IN1     = U1.GPIO16, U4.IN1
NET_IN2     = U1.GPIO17, U4.IN2
NET_EN      = U1.GPIO18, U4.EN

NET_DQ       = U1.GPIO4,  J8.pin1
NET_DQ_PU    = R_pullup_DQ.bot   (4.7 kΩ to 3V3)
NET_DQ_PD    = none (1-Wire is open-drain)

NET_UART_TX  = U1.GPIO26, J4.pin3    # ESP32 TX → DPS5005 RX
NET_UART_RX  = U1.GPIO27, J4.pin4    # DPS5005 TX → ESP32 RX

NET_SOIL     = U1.GPIO32, J9.pin1
NET_BAT_DIV  = U1.GPIO33, J10.pin1

NET_LIM_0    = U1.GPIO34, J7.pin1    # external 10k pullup to 3V3
NET_LIM_90   = U1.GPIO35, J7.pin2    # external 10k pullup to 3V3

NET_LED      = U1.GPIO25, R_LED (100 Ω) → LED1.DIN

NET_LIGHT_CTRL = U1.GPIO19, R_base (4.7 kΩ) → Q1.B
NET_LIGHT_OUT  = Q1.C → K1.coil+ (K1.coil- to GND)
                  K1.NO → J5.pin1 (12V out)
                  K1.COM → J5.pin1 (12V in, looped)
                  J5.pin2 = switched 12V → grow light fixture
```

Note: limit switch pullups are EXTERNAL (10 kΩ on the wires going to the
hinge area). The PCB only carries the signal traces.

---

## 6. Board layout

**Outline:** 50 mm × 70 mm, 2-layer FR4, 1 oz copper, 0.2 mm trace/space
(JLCPCB's standard 4-layer would be tighter, but 2-layer is enough at this
complexity).

**Component placement (top view, looking down at the board):**

```
  ┌─────────────────────────────────────────────┐  ← JLCPCB fiducials
  │  J1 (XT60)                                  │     on each corner
  │   ↓                                         │
  │  [F1] [U7] [D1]  12V INPUT                  │
  │              ↓                              │
  │         [C_bulk] [U2 MP1584] [L1] [C_5V]   │
  │              ↓                              │
  │         [U3 AMS1117] [C_3V3]                │
  │              ↓                              │
  │  ┌──────┐  USB-C (J3)  BOOT  RESET         │  ← Antenna keepout
  │  │ U1   │  J3       SW1  SW2                │     (no copper, no
  │  │ESP32 │                                   │     ground plane, no
  │  └──────┘                                   │     traces under
  │   │ │   │   │                               │     antenna region)
  │  GPIO distribution to:                      │
  │   ├── I2C bus [U5 BMI160] [U6 INA219]       │
  │   ├── GPIO25 → LED1                         │
  │   ├── GPIO4  → J8 (DS18B20)                 │
  │   ├── GPIO19 → Q1 → K1 → J5 (light)         │
  │   ├── GPIO32 → J9 (soil)                    │
  │   ├── GPIO33 → J10 (battery sense)          │
  │   ├── GPIO26/27 → J4 (DPS5005 UART)         │
  │   ├── GPIO16/17/18 → U4 DRV8871 → J6        │
  │   └── GPIO34/35 → J7 (limits)               │
  │                                             │
  │  Connectors along right edge:               │
  │  [J2 I2C]  [J4 DPS]  [J5 light]  [J6 motor]│
  │  [J7 lim]  [J8 temp] [J9 soil]  [J10 bat]  │
  └─────────────────────────────────────────────┘
```

**Critical rules:**
- **ESP32 antenna keepout:** 10 mm × 15 mm rectangle at the top edge of the
  PCB, no copper, no components, no ground plane. The PCB antenna needs
  this region to be clear.
- **High-current traces:** 12 V from XT60 to F1 to U2 to motor (J6) should
  be wide (≥ 1 mm, 1 oz copper = ~3 A). The 12 V rail carries up to 5 A
  briefly during actuator stall.
- **Analog traces (GPIO32, GPIO33):** Keep away from switching traces
  (MP1584 switch node, DRV8871 outputs). Add a ground guard on both sides.
- **I2C pullups:** 4.7 kΩ to 3V3 on SDA and SCL, near the ESP32.
- **Decoupling:** 100 nF + 10 µF within 5 mm of each IC's power pin.
- **Mounting holes:** M3 at each corner (4 mm from edges).

**Cost:** JLCPCB 5-piece prototype run: $5 (5 boards) + $15 shipping = $20.

---

## 7. Assembly notes

**Order of assembly (top side first):**

1. **Power section (low side):** U7, F1, D1, C_bulk, U2 (MP1584), L1, C_5V,
   U3 (AMS1117), C_3V3. Test with 12 V input: verify 5 V and 3.3 V rails
   before proceeding.
2. **ESP32 + USB-C:** J3, U1, SW1, SW2, R_pullups, decoupling. Test: connect
   USB, flash a blink sketch, verify the ESP32 boots and WiFi connects.
3. **I2C devices:** U5 (BMI160), U6 (INA219), J2. Test: run an I2C scanner,
   verify both devices respond.
4. **UART (DPS5005):** J4. Test: connect DPS5005, send `*IDN?` over UART,
   verify response.
5. **Motor driver:** U4 (DRV8871), J6. Test: bench-test with a spare
   actuator or a small DC motor. Verify IN1/IN2/EN control direction and
   speed.
6. **Relay + grow light:** Q1, D2, K1, J5. Test: toggle GPIO19, hear the
   relay click, verify 12 V at J5.
7. **Sensors:** J8 (DS18B20), J9 (soil), J10 (battery), J7 (limits). Test
   each individually.
8. **Status LED:** LED1 + R_LED. Test: blink test from ESPHome.

**Final assembly:**

- Mount the PCB in a waterproof ABS enclosure (e.g., Polycase WC-22F,
  4.7"×2.6"×1.4", IP65). Cut a hole for the USB-C and XT60.
- Conformal-coat the PCB (MG Chemicals 422B silicone) for humidity
  resistance — optional but recommended for outdoor Phoenix use.
- Mount the enclosure on the bed's east or west short wall, near the
  battery. Or external to the bed, on a post.

---

## 8. Test points

- **TP1:** 12 V rail (after F1)
- **TP2:** 5 V rail
- **TP3:** 3.3 V rail
- **TP4:** GPIO33 (battery sense divided voltage, should be ~5.0 V at 12 V battery)

Each test point is a 1 mm pad for easy probing.

---

## 9. What this PCB is NOT

- ❌ **Not a high-power MPPT.** The DPS5005 is the MPPT path; it handles
  up to 50 V / 5 A. The PCB only carries the UART control lines.
- ❌ **Not a microinverter interface.** The microinverter (Enphase IQ7+ or
  APsystems DS3) is its own certified box; the PCB doesn't touch it.
- ❌ **Not a solar charger.** The PCB monitors and controls; the actual
  battery charging is the DPS5005's job.
- ❌ **Not a power supply.** 12 V comes from the battery; 5 V and 3.3 V are
  derived for the ESP32 and sensors. The PCB does NOT generate 12 V.

---

## 10. Open questions for v2

- Add a small OLED display (SSD1306) for local status without Home Assistant?
- Add a CAN bus header for future expansion (e.g., multiple panels)?
- Add a hardware watchdog timer (TPL5010) to reset the ESP32 on hang?
- Move to a 4-layer board for better EMI/grounding?

These are not in v1. v1 is the minimum viable controller.
