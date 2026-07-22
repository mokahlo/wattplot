# Wattplot Mini v1 — Bill of Materials

1/5-scale, fully functional design-validation prototype. Sits on a
workbench or window sill. Build before committing to the full-size
build to validate the geometry, the hinge mechanism, the actuator
travel, the sensor placement, and the controller logic.

**Total cost: ~$100-130. Total build time: ~3-4 hours.**

Same design rules as the full-size build (`bom.md`):
1. **No miter cuts** — every cut is a 90° square cut.
2. **All hardware off the shelf** — Home Depot, Amazon, McMaster.
3. **Simple, common dimensions** — all from 8ft stock, 1x2 / 1x4 / 2x2 PT DF.

---

## Lumber (PT Douglas Fir)

### Bed walls (1x4 PT DF, actual 0.75" × 3.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 1x4 | 19" | Long walls (N and S sides), half-lap corners | 1x4x8ft, 77" waste per board |
| 1 | 1x4 | 8.5" + 8.5" = 17" | Short walls (E and W ends) | 1x4x8ft, 79" waste |

**Lumber for bed walls: 3 boards, ~6 bf**

### Frame rails (1x2 PT DF, actual 0.75" × 1.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 1x2 | 19" | Long rails (E and W sides) | 1x2x8ft, 77" waste |
| 1 | 1x2 | 8.5" + 8.5" = 17" | Cross rails (N and S ends) | 1x2x8ft, 79" waste |

**Lumber for frame rails: 2 boards (1 long + 1 cross source), ~3 bf**

Wait — long rails and cross rails from the same 1x2x8ft board? 4 rails
of 19" = 76" total, leaving 20" of waste. That's 1 board. Plus 4 rails
of 8.5" = 34" total, that's < 1 board. So:

- 1 board: 4 × 19" long rails (76" used, 20" waste)
- 1 board: 2 × 8.5" + 2 × 8.5" = 4 cross rails from 1 board (34" used, 62" waste)

Total 1x2 boards: 2 (1 for long rails, 1 for cross rails). Or 1 board
for the 4 cross rails (4 × 8.5" = 34", which fits in one 96" board with
62" waste).

**Lumber for frame rails: 3 boards, ~5 bf**

### Diagonal brace (1x2 or 2x2, 20" long)
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 1 | 1x2 (or 2x2) | 20" | Diagonal brace | Offcut from any 1x2 / 2x2 board |

### Bed skids (2x2 PT DF, actual 1.5" × 1.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 2x2 | 19" | Long skids, under the long walls | 2x2x8ft, 77" waste per board |

**Lumber for skids: 1 board, 2 bf** (2 skids from 1 board, 38" used, 58"
waste)

### Total lumber

| Material | Boards | Cost |
|---|---|---|
| 1x4x8ft (3 boards) | 3 | ~$15 |
| 1x2x8ft (3 boards) | 3 | ~$10 |
| 2x2x8ft (1 board) | 1 | ~$5 |
| 1x2 offcut (diagonal) | 0 | $0 |
| **Total lumber** | **7 boards** | **~$30** |

---

## Hardware (all off the shelf)

### Hinges + continuous hinge pin
| Qty | Item | Source | Cost |
|---|---|---|---|
| 2 | 1.5" butt hinge, ⅜" pin (galvanized) | Home Depot | ~$3 ea = **$6** |
| 1 | ⅜" × 24" steel rod (continuous hinge pin) | Home Depot | **$3** |

### Panel + mounting
| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | Newpowa 10W 12V Mono solar panel, 17.32" × 8.46" × 0.71" | Amazon | **$25** |
| 4 | 1" aluminum mid-clamps, 18mm channel, M8 bolt | Amazon | ~$2 ea = **$8** |

### Actuator + clevis
| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | 1" stroke 12V micro linear actuator, 25 lbf | Amazon | **$15** |
| 2 | ⅜" cotter pins (for clevis) | Hardware store | **$1** |

### Fasteners
| Qty | Item | Use |
|---|---|---|
| 16 | #6 × 1.5" wood screws | Frame joints, half-lap corners |
| 8 | ⅛" × 1" wood screws | Cleats, bracket mounting |
| 1 | 1A in-line fuse (PTC resettable) | Battery protection |

**Total fasteners: ~$5**

### Electronics (same as full-size, minus PCB)

| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | ESP32-WROOM-32E dev board | Mouser | **$5** |
| 1 | DPS5005 MPPT controller | Amazon | **$25** |
| 1 | BMI160 IMU breakout | Mouser | **$2** |
| 1 | INA219 current sensor breakout | Mouser | **$2** |
| 1 | DS18B20 temperature sensor (waterproof) | Amazon | **$3** |
| 1 | Capacitive soil moisture sensor | Amazon | **$3** |
| 1 | 12V 5Ah LiFePO4 battery (with BMS) | Amazon | **$50** |
| 1 | Breadboard or perfboard (for prototyping) | Amazon | **$5** |
| ~30 | Jumper wires (M-F, M-M, F-F) | Amazon | **$3** |
| 1 | USB-C cable (for ESP32 programming) | Amazon | **$3** |

**Total electronics: ~$100**

(Optional: use the full-size PCB from `docs/pcb_design.md` for $5 + $15
shipping from JLCPCB. Replaces the breadboard + jumper wires above.)

---

## Cost summary

| Category | Cost |
|---|---|
| Lumber (7 boards) | $30 |
| Hinges + pin | $9 |
| Panel + clamps | $33 |
| Actuator + clevis | $16 |
| Fasteners | $5 |
| Electronics (ESP32 + DPS5005 + sensors + battery) | $100 |
| **Total** | **~$190** |

(The full-size build is ~$1,400; the mini is ~14% of that, with most of
the cost in the electronics which are identical between mini and full-size.)

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
- Tape measure, square, level
- Wire stripper
- Multimeter
- Soldering iron (for the perfboard, if not using a breadboard)
