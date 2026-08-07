# Wattplot Build Guide: large_format_1m65

> **STALE — auto-generated from the same template as `build_guide.md`
> (which is itself stale).** The panel-preset-specific geometry (Phase 0
> lumber cut list, Phase 1 bed dimensions) is correct for the large-format
> 1.65 m² preset; the **electronics phases** (Phase 7 onward) reference
> the v2.4 architecture that no longer exists. See `firmware/README.md`
> and `docs/pinmap.html` for the current truth. Tracked in
> [ROADMAP.md](../ROADMAP.md).

Step-by-step assembly of the entire apparatus. Follow the order below. Each step lists the **time**, **tools**, **parts**, and **verification**.

**Total build time:** ~7.9 hr over a weekend (with lumber pre-cut).

**Specifications for this build:**
- Panel: 65.0" × 41.0" × 1.4" (5.42 × 3.42 ft), 41.0 lb
- Wattage: 392 W (nameplate 400 W, derated after 4 yr, bifacial)
- Bed: 65.0" × 41.0" (5.42 × 3.42 ft), 12" deep walls, bottomless

## Phase 0: Pre-build (Day 0, ~1.0 hr)

### 0.1 Lumber (from the cut list)

| Nominal | Qty | Length | Use |
|---|---|---|---|
| 1x6 | 10 | 65.0" (5.42 ft) | long wall skin (N/S), 4 courses |
| 1x6 | 10 | 39.5" (3.29 ft) | short wall skin (W/E), 4 courses |
| 2x4 | 16 | 27.5" (2.29 ft) | wall cleat (vertical, <=24" o.c.) |
| 2x6 | 2 | 65.0" (5.42 ft) | wall cap, hinge + strut walls |
| 2x6 | 2 | 65.0" (5.42 ft) | long frame rail |
| 2x6 | 2 | 38.0" (3.17 ft) | cross frame rail |
| 2x4 | 1 | 76.9" (6.40 ft) | diagonal brace |
| 4x4 | 2 | 65.0" (5.42 ft) | long skid |

**Source from 8-ft stock:** 15× 1x6, 7× 2x4, 5× 2x6, 2× 4x4

**Tip:** many yards will cut to length for free or a small fee. Have them cut each piece on the list above. None of the cuts are mitered (90° square cut only).

### 0.2 Hardware

- 2 × galvanized butt hinge, 4.0"×4.0" leaf, 0.5" pin, HDG
- 1 × ½" × 67.0" steel rod (continuous, through all hinges)
- 6 × aluminum mid-clamps, 35mm channel, M8 SS bolt + EPDM washer
- 8 × 3/8" × 4" carriage bolt HDG + washer + hex nut (bed corner joints)
- 8 × 5/16" × 3" lag bolt HDG (hinge leaf to bed wall)
- 18 × ¼" × 3" deck screw HDG Torx T-25
- 1 × 12V linear actuator, 4.0" stroke, IP65

### 0.3 Panel + electrical

- 1 × **400 W nameplate (392 W after derate) salvage panel** (you provide)
  - Verify under full sun: Voc within 5% of nameplate (multimeter)
  - Glass intact, no cracks or delamination
  - Aluminum frame straight, junction box sealed
- 1 × MPPT charge controller (sized to your panel, see `bring_your_own_panel.py`)
- 1 × 12V 100Ah LiFePO4 battery (LiTime or similar)
- 1 × Microinverter (Enphase IQ7+ or APsystems DS3)
- 1 × ESP32-WROOM-32E dev board (or use the PCB from `docs/pcb_design.md`)

## Phase 1: Bed (Day 1, ~1.9 hr)

### 1.1 Cut the wall half-lap notches

Each bed wall has a 3" wide × 0.75" deep notch at each end.

**Tools:** circular saw, chisel, mallet, square

**Process:**
1. Mark the notch location on each wall (3" from each end, 0.75" deep).
2. Make multiple passes with the circular saw at the notch depth.
3. Clean out the waste with a chisel.
4. Test-fit two walls at a corner.

**Verification:** the two walls meet at a 90° corner with no daylight.

### 1.2 Assemble the bed box

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" wood screws, square

**Process:**
1. Lay out the 4 walls on a flat surface. Long walls are 65.0" (5.42 ft). Short walls are 38.0" (3.17 ft).
2. Bring the corners together. The half-lap notches interlock.
3. Pre-drill 2 holes per corner (one near the top, one near the bottom).
4. Drive #6 × 1.5" wood screws through the corners.

**Verification:** bed box is 65.0" × 41.0" outside, square (measure diagonally, both should be the same).

### 1.3 Attach the skids

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" screws

**Process:**
1. Flip the bed upside down.
2. Place two 4x4×65.0" skids under the bed, aligned with the long walls.
3. Pre-drill and screw through the skids into the bed walls.
4. Use 2-3 screws per skid.

**Verification:** skids are flush with the bed ends, square, and the whole bed sits level on the ground.

## Phase 2: Frame (Day 1, ~1.2 hr)

### 2.1 Assemble the frame rectangle

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" wood screws, square

**Process:**
1. Lay the 4 frame rails on a flat surface. Long rails are 65.0" (5.42 ft). Cross rails are 38.0" (3.17 ft).
2. The cross rails fit between the long rails. Butt joints (no miter).
3. Pre-drill 2 holes per corner. Drive #6 × 1.5" wood screws.

**Verification:** frame is 65.0" × 41.0" outside, square.

### 2.2 Add the diagonal brace

**Tools:** drill, ⅛" pilot bit, #6 × 1" screws, measuring tape

**Process:**
1. The 2x4×76.9" diagonal brace runs corner to corner inside the frame.
2. Position the brace so its ends butt into the inside faces of the long rails.
3. Pre-drill 2 holes per end. Drive #6 × 1" screws (4 total).

**Verification:** brace is at the diagonal angle, both ends screwed.

## Phase 3: Hinges (Day 1, ~20 min)

### 3.1 Install hinges on the bed's south wall

**Tools:** drill, 5/64" bit, hinge screws (included with hinges), tape measure

**Process:**
1. Lay the frame on top of the bed, with the frame's south rail resting on the bed's south wall.
2. Position the 2 hinges evenly along the south rail. Spacing: 57.0" center-to-center, with 4" margin on each end.
3. Mark the hinge positions on both the frame's south rail and the bed's south wall.
4. Pre-drill 4 holes per hinge (2 per leaf), 5/64" bit.
5. Attach the wall leaf to the bed's south wall.
6. Attach the frame leaf to the frame's south rail.

**Verification:** frame hinges freely between 0° and ~90° tilt.

### 3.2 Insert the continuous hinge pin

**Tools:** mallet (rubber)

**Process:**
1. Thread the ½" × 67.0" steel rod through all hinges, starting from one end.
2. Tap gently with a rubber mallet to seat the pin fully.
3. The pin should extend ~1" past the last hinge on each end.

**Verification:** pin is fully seated. Frame hinges smoothly with the pin in place.

## Phase 4: Panel (Day 1, ~11 min)

### 4.1 Place the panel on the frame

**Tools:** hands (the panel weighs 41.0 lb).

**Process:**
1. With the frame flat on the bed, place the panel on top of the frame, centered.
2. The panel should rest on the wood rails with even margin on all four sides.

**Verification:** panel is centered, no overhang on the long rails.

### 4.2 Clamp the panel to the frame

**Tools:** drill, M8 hex driver, mid-clamps

**Process:**
1. Place 4 mid-clamps on each long rail (8 total, evenly spaced along the panel frame).
2. Place 2 mid-clamps on each cross rail.
3. Tighten the M8 bolts to clamp the panel frame to the wood rails.
4. Torque to ~3 Nm (snug, not crushing).

**Verification:** panel is firmly attached. Try to wiggle it: should not move.

## Phase 5: Actuator Mount (Day 1, ~20 min)

### 5.1 Mount the bottom block on the bed's north wall

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" wood screws

**Process:**
1. Cut a 3" length of 2x6 (offcut from any 2x6 scrap).
2. Mount the block on the outer face of the bed's north wall, at the bottom.
3. Centered along the bed length.
4. Pre-drill 2 holes and drive #6 × 1.5" screws.

### 5.2 Mount the top bracket on the panel's underside

1. Cut a 3" length of 2x6 (offcut).
2. Mount on the **underside** of the panel, 2" north of the panel's south edge.
3. The bracket should sit just below the panel's underside, flush with the panel's south frame edge.
4. Pre-drill and drive #6 × 1.5" wood screws through the bracket into the panel frame.

### 5.3 Connect the actuator

1. Use ⅜" clevis pins to attach the actuator to both mount blocks.
2. Test manually: the panel should now move from 0° to ~90° (or your actuator's stroke limit).

## Phase 6: Wire the panel to MPPT (Day 2, ~30 min)

### 6.1 MC4 connectors

**Tools:** MC4 crimper, wire stripper, multimeter

**Process:**
1. Crimp MC4 connectors on the panel's PV+ and PV- leads.
2. Plug into the MPPT's PV input (MC4 or SAE adapter, depending on the MPPT).
3. **Verify polarity**: red → +PV, black → -PV. Reverse polarity kills MPPT.

### 6.2 MPPT to battery

1. Connect MPPT battery output to the 12V LiFePO4 battery (via ring terminals or Anderson).
2. Set the MPPT's battery chemistry to LiFePO4 (MODE button on Sunapex).
3. The MPPT status LED should turn on (green = charging or float).

**Verification:** under sun, panel Voc on multimeter matches nameplate ±5%. Battery voltage rises over the next hour.

## Phase 7: Wire the controller (Day 2, ~1.0 hr)

### 7.1 ESP32 + sensors

**Tools:** soldering iron (or perfboard), wire stripper, multimeter

**Pins (from `firmware/wattplot.yaml`):**

| GPIO | Function |
|---|---|
| 4 | DS18B20 1-Wire data |
| 5 | Watering solenoid |
| 16, 17, 18 | H-bridge IN1, IN2, EN |
| 19 | Grow light relay |
| 21, 22 | I2C SDA, SCL |
| 25 | WS2812B status LED |
| 32 | Soil moisture ADC |
| 33 | Battery voltage ADC |
| 34, 35 | Limit switches (0° and 90°) |

### 7.2 Power

1. Connect the DRV8871 H-bridge to the 12V battery (via a 5A fuse).
2. Connect the ESP32's VIN to a 5V buck converter on the 12V rail.
3. Verify all grounds are common.

### 7.3 IMU + INA219 + DS18B20

1. Mount the BMI160 on the panel (under the north rail). I2C address 0x68.
2. Mount the INA219 in series with the actuator (high side). I2C address 0x40.
3. Mount the DS18B20 in the bed soil.
4. All sensors share the I2C bus: SDA (GPIO 21), SCL (GPIO 22), 3.3V, GND.

**Verification:** ESPHome logs show all sensors reporting values.

## Phase 8: Flash ESPHome (Day 2, ~30 min)

### 8.1 First flash over USB

```bash
# Install ESPHome (if not already)
pip install esphome

# Flash the firmware
esphome run firmware/wattplot.yaml
```

### 8.2 WiFi + Home Assistant (optional)

1. Set WiFi credentials in `firmware/secrets.yaml`.
2. Re-flash. ESP32 connects to WiFi and exposes all entities to Home Assistant.
3. Add the ESPHome integration in HA. Entities appear automatically.

## Phase 9: Calibrate + test (Day 2, ~1.0 hr)

### 9.1 IMU zero-tilt offset

1. With the panel flat (0°), read the BMI160's pitch value via ESPHome log.
2. That reading is your zero-tilt offset. Subtract it in the firmware.
3. Re-flash.

### 9.2 Motor current calibration

1. Manually drive the panel to 35°. Read the INA219 current (idle, no wind).
2. Set that as the `target_current_A` in `firmware/wattplot.yaml`.
3. Set `I_safe_A` just above the stall current (typically 2.5A for DRV8871).

### 9.3 Limit switches

1. Drive the panel to 0° (limit switch 0). Adjust switch position so it trips cleanly.
2. Drive to 90° (limit switch 1). Same.
3. Verify the firmware auto-stops at both limits.

### 9.4 End-to-end test

1. Open Home Assistant. Verify all sensors reporting.
2. Trigger a manual tilt from HA. Verify panel moves.
3. Press the user-override button. Verify it overrides the decision stack.
4. Leave it running for 24 hours. Check logs for any errors.

---

**Total time:** ~7.9 hr (with pre-cut lumber and a clean workspace).

**Total cost:** see `python bring_your_own_panel.py` for an itemized estimate.

**Next:** see `docs/test_checklist.md` for per-component and per-system tests.
