# Wattplot Mini v2.2 — Bill of Materials

Benchtop design-validation prototype. **18"×14" bed, ECO-WORTHY 10W
panel, 100mm kickstand linear actuator** — sized to match the parts
already ordered for this build.

Build before committing to the full-size build to validate:
- Real solar charging (10W panel → MPPT → battery)
- 100mm kickstand actuator geometry (compression, low-side mount, 0-35°)
- 1x2 frame structural behavior
- Same firmware / sensors / MPPT / wiring as the full-size

**Total cost: ~$130-170. Total build time: ~3-4 hours.**

Same design rules as the full-size build (`bom.md`):
1. **No miter cuts** — every cut is a 90° square cut.
2. **All hardware off the shelf** — Home Depot, Amazon, McMaster.
3. **Simple, common dimensions** — all from 8ft stock, 1x2 / 1x4 / 2x4 PT DF.

---

## Tilt range: 0-35° (kickstand-limited)

The kickstand actuator geometry limits the panel to **0-35° tilt** (not
the full 0-90°). For a 10W trickle-charger panel, this is fine — the
panel produces 17 kWh/yr at 0° flat or 15.9 kWh/yr at 35° (the
power-optimal tilt for Phoenix in summer). 0-35° covers the full useful
range for a small panel.

The full-size Wattplot keeps its 24" stroke linear actuator for full
0-90° range (snow shedding, high-wind survival, max winter DLI). The
mini doesn't need that.

---

## Lumber (PT Douglas Fir)

### Bed walls (1x4 PT DF, actual 0.75" × 3.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 1x4 | 18" | Long walls (N and S), half-lap corners | 1x4x8ft, 60" waste per board |
| 2 | 1x4 | 12.5" | Short walls (E and W), half-lap corners | 1x4x8ft, 4 short walls from 1 board (25" used, 71" waste) |

**Lumber for bed walls: 1 board, ~3 bf** (both long walls + 2 short walls from 1x4x8ft)

### Frame rails (1x2 PT DF, actual 0.75" × 1.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 1x2 | 18" | Long rails (E and W sides of panel) | 1x2x8ft, 60" waste per board |
| 2 | 1x2 | 12.5" | Cross rails (N and S ends of panel) | 1x2x8ft, 4 cross rails from 1 board (25" used, 71" waste) |

**Lumber for frame rails: 1 board, ~2 bf** (4 rails from 1x2x8ft, fits all on one board)

### Diagonal brace (2x4 PT DF, actual 1.5" × 3.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 1 | 2x4 | 21" | Diagonal brace, square ends butt into long rails | 2x4x8ft, 75" waste |

**Lumber for brace: 1 board offcut, ~2 bf** (or 2x4 scrap from another project)

### Bed skids (1x2 PT DF, actual 0.75" × 0.75")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 1x2 | 18" | Long skids, under the long walls | 1x2x8ft, 60" waste per board (cut 2 from 1 board) |

**Lumber for skids: 1 board, 1 bf** (2 skids from 1x2x8ft)

### Kickstand actuator mount (1x2 PT DF, scraps)
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 1 | 1x2 | 3" | Bottom mount block, on bed's south wall | 1x2 offcut |
| 1 | 1x2 | 3" | Top mount bracket, hanging below panel | 1x2 offcut |

**Lumber for kickstand mount: offcuts, ~0 bf** (use scraps from the rails/skids boards)

### Total lumber

| Material | Boards | Cost |
|---|---|---|
| 1x4x8ft (1 board) | 1 | ~$5 |
| 1x2x8ft (2 boards: 1 for frame, 1 for skids) | 2 | ~$7 |
| 2x4x8ft (1 board offcut for brace) | 1 | ~$7 |
| **Total lumber** | **4 boards** | **~$19** |

---

## Hardware (all off the shelf)

### Hinges + continuous hinge pin
| Qty | Item | Source | Cost |
|---|---|---|---|
| 2 | 1.5" butt hinge, ⅜" pin (galvanized) | Home Depot | ~$3 ea = **$6** |
| 1 | ⅜" × 22" steel rod (continuous hinge pin) | Home Depot | **$3** |

### Panel + mounting
| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | ECO-WORTHY 10W 12V solar panel, 13.3" × 8.1" × 0.7" (1.88 lb) | Amazon | **$25** (already ordered) |
| 4 | 1" aluminum mid-clamps, 18mm channel, M8 bolt | Amazon | ~$2 ea = **$8** |

### Kickstand actuator + clevis pins
| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | 100mm (3.94") stroke 12V linear actuator, 70N (15.7 lbf) | Amazon | **$15** (already ordered) |
| 2 | ⅜" clevis pins + cotter pins | Hardware store | **$2** |

### Fasteners
| Qty | Item | Use |
|---|---|---|
| 16 | #6 × 1.5" wood screws (HDG) | Bed half-lap corners, frame corners |
| 8 | #6 × 1" wood screws | Diagonal brace to frame |
| 4 | M8 × 1.5" stainless bolts + EPDM washers | Mid-clamps to rails |
| 8 | 5/64" × 1" wood screws | Hinge leaves to bed wall and frame rail |
| 4 | #6 × 1.5" wood screws | Kickstand mount blocks |
| 2 | ⅜" × 3" clevis pins + cotter pins | Actuator clevis to mount blocks |

**Total fasteners: ~$8**

### Electronics (same as full-size, minus PCB)

| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | DPS5005 MPPT controller (NOTE: CN3791 you ordered is INCOMPATIBLE with 12V LiFePO4) | Amazon | **$25** (need to order) |
| 1 | ESP32-C3 PRO Mini dev board (or any ESP32) | Mouser | **$5** (already ordered) |
| 1 | BMI160 IMU breakout | Mouser | **$2** |
| 1 | INA219 current sensor breakout | Mouser | **$2** |
| 3 | DS18B20 waterproof temperature sensors (panel, soil, battery) | Amazon | **$11** (5-pack) |
| 1 | Capacitive soil moisture sensor V1.2 (5-pack for spares) | Amazon | **$9** |
| 1 | 12V 7Ah LiFePO4 battery (with BMS) | Amazon | **$25** (already ordered) |
| 1 | Breadboard or perfboard (for prototyping) | Amazon | **$5** |
| ~30 | Jumper wires (M-F, M-M, F-F) | Amazon | **$3** |
| 1 | USB-C cable (for ESP32 programming) | Amazon | **$3** |

**Total electronics: ~$61 new + $50 already ordered = $111**

### Watering system (v2.3 — smart planter)

| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | 12V peristaltic pump (food-safe, ~0.5 L/min) | Amazon | **$15-20** |
| 1 | 1-channel 5V relay module (low-level trigger, for ESP32) | Amazon | **$3-5** |
| 1 | 5-gallon bucket with lid (reservoir, 18.9 L) | Home Depot | **$5** |
| 10 ft | 1/4" vinyl tubing (food-safe, for drip line) | Amazon | **$8** |
| 1 | Pressure-compensating drip emitter (2 GPH) | Amazon | **$5** (5-pack) |
| 2 | 1/4" tubing barb fittings (for pump inlet/outlet) | Amazon | **$3** |
| 4 | Zip ties (for securing tubing) | Home Depot | **$2** |

**Total watering system: ~$41-48**

---

## Cost summary

| Category | New | Already have | Total |
|---|---|---|---|
| Lumber (4 boards) | $19 | — | $19 |
| Hinges + pin | $9 | — | $9 |
| Panel + clamps | $33 | — | $33 |
| Kickstand actuator + pins | $17 | already ordered | $17 |
| Fasteners | $8 | — | $8 |
| Electronics (DPS5005, sensors, breadboard) | $61 | $50 (battery + ESP32) | $111 |
| Watering system (pump + reservoir + drip) | $45 | — | $45 |
| **Total** | **$192** | **$50** | **~$242** |

**v2.3 adds ~$45 (watering system) on top of v2.2 — full smart planter.**

(The full-size build is ~$1,400; the mini v2.3 is ~17% of that.)

---

## Critical note: CN3791 swap

The **HiLetgo CN3791 MPPT** in the parts list is **not compatible** with
the 12V LiFePO4 battery. The CN3791 is a 12V solar → **1S LiPo (3.7V)**
charger, not a 12V → 12V charger.

**Replace with a DPS5005** ($25, Amazon, "DPS5005 programmable buck
converter"). Same UART control, same MPPT loop in the firmware.

---

## What you DON'T need

- ❌ Welder (it's all screwed)
- ❌ Concrete / rebar / post anchors
- ❌ Steel angle iron / Unistrut
- ❌ Miter saw (all cuts are 90° square cuts)
- ❌ Custom-fabricated metal parts
- ❌ Permit (this is a small benchtop prototype)

---

## Tools needed

- Circular saw (or have the lumber yard pre-cut)
- Drill / impact driver
- ⅛" drill bit (for wood screws)
- 5/64" drill bit (for hinge screws)
- M8 hex driver (for mid-clamp bolts)
- Tape measure, square, level
- Wire stripper
- Multimeter
- Soldering iron (for the perfboard, if not using a breadboard)
