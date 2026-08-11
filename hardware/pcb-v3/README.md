# Wattplot v3 — Custom PCB

**Status:** design in progress (KiCad 10.0, installing)
**Goal:** integrate every wattplot subsystem onto one 2-layer board.
No breakout boards. ~$30-50 in PCBs + assembly for 5 boards at JLCPCB.
**Replaces:** v1 block diagram in `analysis/pcb_schematic.py` (which
was ESP32-WROOM-32E based and didn't include the INA219s, DS18B20s,
or the 2nd DRV8871 that the current wattplot actually uses).

---

## What this board does

The wattplot v3 controller board is a single PCB that hosts:

1. **Power tree** — 12V (battery / MPPT) → MP1584 → 5V → AMS1117 → 3.3V
2. **ESP32-S3** — bare WROOM-1 module (not the DevKitC-1), with USB-C,
   ESD, USB-UART bridge, boot/reset buttons
3. **2× DRV8871** — actuator H-bridge (U5a) and solenoid H-bridge (U5b),
   current sensing via IPROPI, no physical limit switches
4. **2× INA219** — actuator bus current + panel V/A (energy monitor)
5. **Sensor interfaces** — 1-Wire connector (3× DS18B20 daisy chain),
   soil moisture probe connector, all on the same I²C / GPIO bus
6. **Status LED** — single LED on GPIO17 (compat pin from v1)

External (NOT on the PCB):
- MPPT (Sunapex 10A) — own enclosure
- 12V LiFePO4 battery — own enclosure
- Solar panel
- Linear actuator — mechanical
- Solenoid valve — mechanical
- DS18B20 temp probes (3×) — wired to PCB via 3-pin JST-XH
- Capacitive soil moisture probe — wired to PCB via 3-pin JST-XH

---

## Pin map (matches the current `firmware/wattplot.yaml`)

| Function | GPIO | Pin | Notes |
|---|---|---|---|
| Actuator H-bridge IN1 | GPIO1 | U5a | |
| Actuator H-bridge IN2 | GPIO2 | U5a | |
| Actuator IPROPI | GPIO4 | U5a | ADC1_CH3, current sense |
| Solenoid H-bridge IN1 | GPIO10 | U5b | |
| Solenoid H-bridge IN2 | GPIO12 | U5b | |
| Solenoid nFAULT | GPIO13 | U5b | input, 10k pull-up |
| Solenoid IPROPI | GPIO5 | U5b | ADC1_CH4, jam detect |
| Actuator nFAULT | GPIO21 | U5a | input, 10k pull-up |
| DS18B20 (1-Wire DQ) | GPIO16 | one-wire | 4.7k pull-up to 3.3V |
| Soil moisture AOUT | GPIO6 | ADC1_CH6 | |
| Battery V divider | GPIO7 | ADC1_CH6 | 100k+100k divider, midpoint to GPIO7 |
| I²C SDA | GPIO8 | I²C | 4.7k pull-up to 3.3V, shared by 2× INA219 |
| I²C SCL | GPIO18 | I²C | 4.7k pull-up to 3.3V |
| Status LED | GPIO17 | LED | 1k series, compat pin from v1 |
| USB D+ | GPIO20 | native USB | (not used, native USB on S3) |
| USB D- | GPIO19 | native USB | |
| (H-bridge EN) | GPIO11 | compat | reserved, no connection |
| Boot button | GPIO0 | BOOT | pulled up, tactile switch to GND |
| Reset button | EN | RST | pulled up, tactile switch to GND |

---

## Subsystem reference designs

### Power tree
- 12V input from MPPT LOAD via fuse (3A resettable PTC) + TVS (SMBJ 16V)
- MP1584EN buck, 12V→5V @ 3A peak (TI recommended circuit)
  - L = 4.7µH shielded, ≥ 3A saturation
  - Cin = 22µF/25V (SMD 1210)
  - Cbst = 100nF (SMD 0402)
  - Cout = 22µF/10V (SMD 1210)
  - Feedback resistors for 5V out: Rtop=33k, Rbot=10k (per MP1584 datasheet)
- AMS1117-3.3 LDO, 5V→3.3V
  - Cin = 10µF/10V (SMD 0805)
  - Cout = 22µF/10V (SMD 0805)
- Decoupling: 100nF/10V (SMD 0402) on every IC's power pin
- Battery voltage divider: 100kΩ + 100kΩ (both 1% 0402), midpoint to GPIO7

### ESP32-S3 module
- ESP32-S3-WROOM-1-N16R8 (Espressif) — 16MB flash, 8MB PSRAM
- Native USB (no UART bridge needed for programming)
- USB-C connector (16-pin SMD)
- USBLC6-2 (SOT-23-6) ESD on CC1, CC2, D+, D-
- 5.1kΩ pull-down on CC1 and CC2 (signals 3A / 1.5A current advertisement)
- 100nF caps on USB data lines (per USB spec)
- 10µF caps on USB VBUS
- Boot button: tactile switch, GPIO0 to GND (active low)
- Reset button: tactile switch, EN to GND (active low)
- 10kΩ pull-up on EN
- Status LED on GPIO17, 1k series, 0805

### 2× DRV8871 (U5a + U5b)
- DRV8871PWPR (TSSOP-28) — TI
- nSLEEP tied directly to 3.3V (always enabled)
- nFAULT: 10kΩ pull-up to 3.3V, output to ESP32 GPIO
- IPROPI: 1kΩ to GND (200mV/A conversion), output to ESP32 ADC
- VM (pin 1): 12V from MPPT, fused (3A PTC)
- VM bulk cap: 100µF/35V electrolytic + 100nF/50V ceramic, per DRV8871
- VCC (pin 3): 3.3V, decoupled with 100nF + 1µF
- BST (pin 28): 1µF to OUT1, charge pump cap
- OUT1, OUT2: to motor connector (JST-XH 2-pin for actuator, JST-XH 2-pin for solenoid)
- GND: pin 2, also exposed to power ground

### 2× INA219 (I²C current sensors)
- INA219AIDR (SOIC-8) — TI
- 0.1Ω shunt (2512 SMD, 1W) — one per INA219, in series with the rail
  - U5a INA219: measures 12V bus current to the actuator H-bridge VM
  - U6b INA219: measures panel V/A (for energy monitor)
- I²C addresses: 0x40 (U5a), 0x41 (U6b) — already used in firmware
- SDA/SCL: 4.7kΩ pull-up to 3.3V (one pair shared)
- Decoupling: 100nF + 1µF near each chip
- VIN+ to ESP32 3.3V (logic supply), VIN- floating or GND (we use VIN+ as supply)

### 1-Wire connector (DS18B20 daisy chain)
- 3-pin JST-XH connector (3.3V, DQ, GND)
- 4.7kΩ pull-up from DQ to 3.3V (on PCB, not in probes)
- DQ to GPIO16
- Up to 3 DS18B20 sensors in parallel (firmware has 2 wired so far, +1 spare)

### Soil moisture connector
- 3-pin JST-XH connector (3.3V, AOUT, GND)
- AOUT to GPIO6
- 100nF cap on AOUT to GND (noise filter)

### Connectors
- **J1 — Battery / 12V input**: XT60 (through-hole)
- **J2 — Solar / MPPT output**: MC4 or JST-XH 2-pin (input to PCB, parallel with battery)
- **J3 — Actuator motor**: JST-XH 2-pin (DRV8871 OUT1, OUT2)
- **J4 — Solenoid valve**: JST-XH 2-pin (DRV8871 OUT1, OUT2)
- **J5 — 1-Wire sensor chain**: JST-XH 3-pin (3.3V, DQ, GND)
- **J6 — Soil moisture**: JST-XH 3-pin (3.3V, AOUT, GND)
- **J7 — USB-C**: 16-pin SMD USB-C
- **J8 — Expansion header**: 2×5 pin 0.1" header (I²C, 3.3V, GND, 2× GPIO)
- **J9 — Solar bypass** (optional, not in v3): MC4 passthrough

### Test points
- TP1: +12V (after fuse)
- TP2: +5V
- TP3: +3.3V
- TP4: GND (×2, near opposite corners)
- TP5: VBAT (battery voltage, before fuse)

### Mounting
- 4× M3 mounting holes, 3.2mm pad, near corners

---

## Form factor

- **Target size:** 80×60mm, 2-layer, 1.6mm FR4 (matches v1 spec)
- **Mounting:** 4× M3 corners, 3.2mm pad
- **Connector placement:** all external connectors on the same edge
  (long edge, opposite from the ESP32 antenna) for clean wiring

---

## JLCPCB SMT component list (preliminary)

**Basic library (free):**
- ESP32-S3-WROOM-1-N16R8 (C2913203)
- AMS1117-3.3 (C6186)
- MP1584EN (C16581)
- INA219AIDR (C9459)
- 0402 resistors (1% 100k, 10k, 4.7k, 1k, 5.1k, 22)
- 0402 caps (100nF/10V)
- 0805 caps (10µF, 22µF)
- 1210 caps (22µF/25V)
- SOT-23-6 (USBLC6-2 or similar)
- Status LED (0805)
- Tactile switches
- 2512 resistor (0.1Ω 1W)

**Extended library ($3 setup per part):**
- DRV8871PWPR (TSSOP-28) — confirm availability
- SMBJ16A TVS (DO-214AA) — confirm
- MF-SMDF050 fuse (1812) — confirm
- JST-XH connectors — confirm (might be extended)
- USB-C connector (16-pin SMD) — confirm

(Will verify in JLCPCB's parts library once schematic is in KiCad.)

---

## Open questions

- [ ] Should the USB-C connector be 16-pin (with all sideband) or 6-pin
      (just power + data, smaller)? For this design, 16-pin is
      cleaner (no need for separate 5.1k pull-downs on the CC lines
      externally), but takes more PCB space.
- [ ] Reverse polarity protection on the 12V input: TVS only, or
      TVS + P-MOSFET ideal-diode? The TVS handles transients; a
      P-MOSFET ideal-diode handles sustained reverse. For a
      battery-powered device where reverse polarity is unlikely
      (battery has fixed polarity), TVS is enough. Skipping the
      P-MOSFET for v3.
- [ ] Should we add an SD card slot for data logging? The firmware
      has MQTT log streaming but no on-board logging. Out of scope
      for v3.
- [ ] Battery management: the BMS is in the battery, not on the PCB.
      PCB only has the fuse + TVS.

---

## Implementation order (todo)

See the master todo list — this doc is the schematic spec / source of
truth, but the actual capture happens in KiCad once the install
finishes.

1. Wait for KiCad 10.0 install
2. Open KiCad, create new project `wattplot-v3.kicad_pro` under
   `hardware/pcb-v3/`
3. Capture schematic sheet 1: Power tree (12V input → 5V → 3.3V)
4. Capture schematic sheet 2: ESP32-S3 module + USB-C + boot logic
5. Capture schematic sheet 3: 2× DRV8871 H-bridges
6. Capture schematic sheet 4: 2× INA219 + I²C bus
7. Capture schematic sheet 5: Sensor interfaces (1-Wire, soil moisture)
8. Capture schematic sheet 6: Connectors + test points
9. Annotate, ERC, generate netlist
10. Place components on PCB
11. Route power (12V, 5V, 3.3V) with wide traces
12. Route signal
13. Pour ground plane
14. DRC
15. Generate Gerbers, BOM, CPL
16. Upload to JLCPCB

---

## Changelog

- 2026-08-08: Initial spec. Maps v1 block diagram + current firmware
  v3.2 onto a single board. 80×60mm 2-layer, JLCPCB SMT.
