# Wattplot Mini v2.1 — Bill of Materials

Benchtop design-validation prototype. **40"×22" bed, 100W bifacial
panel, 4" kickstand linear actuator** — large enough to fit a real
off-the-shelf bifacial panel, small enough to sit on a workbench.

Build before committing to the full-size build to validate:
- Real 100W bifacial gain (rear-side albedo)
- 4" kickstand actuator geometry (compression, low-side mount, 0-35° tilt)
- 2x2 frame structural behavior
- Same firmware / sensors / MPPT / wiring as the full-size

**Total cost: ~$220-280. Total build time: ~4-5 hours.**

Same design rules as the full-size build (`bom.md`):
1. **No miter cuts** — every cut is a 90° square cut.
2. **All hardware off the shelf** — Home Depot, Amazon, McMaster.
3. **Simple, common dimensions** — all from 8ft stock, 1x4 / 2x2 / 2x4 PT DF.

---

## Tilt range: 0-35° (kickstand-limited)

The kickstand actuator geometry limits the panel to **0-35° tilt** (not
the full 0-90°). This is by design — the Phoenix sun sim shows 35° is
the **power-optimal static tilt** (1,539 kWh/yr at 35° on the full-size;
on the mini, 35° gives 159.36 kWh/yr vs 170.95 at 0° and 106.84 at 90°).
A 35° tilt captures ~93% of the maximum summer yield, which is good
enough for the mini's purpose (validating the system, not maximizing
production).

The full-size Wattplot keeps its 24" stroke linear actuator for full
0-90° range. The mini doesn't need that.

---

## Lumber (PT Douglas Fir)

### Bed walls (1x4 PT DF, actual 0.75" × 3.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 1x4 | 40" | Long walls (N and S), half-lap corners | 1x4x8ft, 56" waste per board |
| 2 | 1x4 | 20.5" | Short walls (E and W), half-lap corners | 1x4x8ft, 4 short walls from 1 board (82" used, 14" waste) |

**Lumber for bed walls: 3 boards, ~6 bf**

### Frame rails (2x2 PT DF, actual 1.5" × 1.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 2x2 | 40" | Long rails (E and W sides of panel) | 2x2x8ft, 56" waste per board |
| 2 | 2x2 | 19" | Cross rails (N and S ends of panel) | 2x2x8ft, 4 cross rails from 1 board (76" used, 20" waste) |

**Lumber for frame rails: 3 boards, ~6 bf**

### Diagonal brace (2x4 PT DF, actual 1.5" × 3.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 1 | 2x4 | 42" | Diagonal brace, square ends butt into long rails | 2x4x8ft, 54" waste |

**Lumber for brace: 1 board offcut, ~2 bf**

### Bed skids (2x2 PT DF, actual 1.5" × 1.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 2x2 | 40" | Long skids, under the long walls | 2x2x8ft, 56" waste per board |

**Lumber for skids: 1 board, 2 bf** (2 skids from 1 board, 80" used, 16" waste)

### Kickstand actuator mount (2x2 PT DF, actual 1.5" × 1.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 1 | 2x2 | 4" | Bottom mount block, on bed's south wall | 2x2 offcut (any 2x2 scrap) |
| 1 | 2x2 | 4" | Top mount bracket, hanging below panel | 2x2 offcut (any 2x2 scrap) |

**Lumber for kickstand mount: offcuts, ~0 bf** (use scraps from the rails/skids)

### Total lumber

| Material | Boards | Cost |
|---|---|---|
| 1x4x8ft (3 boards) | 3 | ~$15 |
| 2x2x8ft (4 boards) | 4 | ~$20 |
| 2x4x8ft (1 board for brace) | 1 | ~$7 |
| **Total lumber** | **8 boards** | **~$42** |

---

## Hardware (all off the shelf)

### Hinges + continuous hinge pin
| Qty | Item | Source | Cost |
|---|---|---|---|
| 2 | 4" butt hinge, ½" pin (galvanized) | Home Depot | ~$5 ea = **$10** |
| 1 | ½" × 44" steel rod (continuous hinge pin) | Home Depot | **$6** |

### Panel + mounting
| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | Newpowa 100W 12V Bifacial solar panel, 38.58" × 20.87" × 1.18" | Amazon | **$90** |
| 6 | 2" aluminum mid-clamps, 35mm channel, M8 bolt | Amazon | ~$3 ea = **$18** |

### Kickstand actuator + clevis pins
| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | 4" stroke 12V linear actuator, 75 lbf (ECO-WORTHY or similar) | Amazon | **$18** |
| 2 | ½" × 3" clevis pins + cotter pins | Hardware store | **$3** |

### Fasteners
| Qty | Item | Use |
|---|---|---|
| 24 | #8 × 2" deck screws (HDG) | Bed half-lap corners, frame corners |
| 8 | #6 × 1.5" wood screws | Diagonal brace to frame |
| 6 | M8 × 1.5" stainless bolts + EPDM washers | Mid-clamps to rails |
| 8 | 5/16" × 3" lag bolts (HDG) | Hinges to bed wall and frame rail |
| 8 | #8 × 2" deck screws | Kickstand mount blocks (4 per block) |
| 2 | ½" × 3" clevis pins + cotter pins | Actuator clevis to mount blocks |

**Total fasteners: ~$15**

### Electronics (same as full-size, minus PCB)

| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | ESP32-WROOM-32E dev board | Mouser | **$5** |
| 1 | DPS5005 MPPT controller | Amazon | **$25** |
| 1 | BMI160 IMU breakout | Mouser | **$2** |
| 1 | INA219 current sensor breakout | Mouser | **$2** |
| 1 | DS18B20 temperature sensor (waterproof) | Amazon | **$3** |
| 1 | Capacitive soil moisture sensor | Amazon | **$3** |
| 1 | 12V 20Ah LiFePO4 battery (with BMS) | Amazon | **$80** |
| 1 | Breadboard or perfboard (for prototyping) | Amazon | **$5** |
| ~30 | Jumper wires (M-F, M-M, F-F) | Amazon | **$3** |
| 1 | USB-C cable (for ESP32 programming) | Amazon | **$3** |

**Total electronics: ~$130**

(Optional: use the full-size PCB from `docs/pcb_design.md` for $5 + $15
shipping from JLCPCB. Replaces the breadboard + jumper wires above.)

---

## Cost summary

| Category | Cost |
|---|---|
| Lumber (8 boards + scraps) | $42 |
| Hinges + pin | $16 |
| Panel + clamps | $108 |
| Kickstand actuator + pins | $21 |
| Fasteners | $15 |
| Electronics (ESP32 + DPS5005 + sensors + battery) | $130 |
| **Total** | **~$330** |

(The full-size build is ~$1,400; the mini is ~24% of that, with most of
the cost in the panel + battery which are sized for the mini but use
the same form factor as the full-size.)

**Mini v2.0 (24" actuator) was ~$400; Mini v2.1 (4" kickstand) saves ~$70
on the actuator.**

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
- 5/16" drill bit (for lag bolts)
- M8 hex driver (for mid-clamp bolts)
- Tape measure, square, level
- Wire stripper
- Multimeter
- Soldering iron (for the perfboard, if not using a breadboard)

---

## Sizing note (read this!)

The 100W panel (38.58" × 20.87") is **larger than the frame's interior**
(40 − 2×1.5 = 37" × 22 − 2×1.5 = 19"). The panel sits on top of the
frame rails and overhangs the frame interior by ~0.79" on the long sides
and ~0.94" on the short sides. This is the same overhang pattern as the
full-size build (the full-size 97" × 44.6" panel also overhangs the
93" × 41.6" frame interior).

The mid-clamps grip the panel frame at the rail positions, so the panel
is held firmly even though it extends past the rails. **Do not** try to
make the panel fit inside the frame interior — it won't, and the
mid-clamps need the panel to be on top of the rails, not tucked inside.
