# Wattplot Mini v2 — Build Guide

Benchtop design-validation prototype. **40"×22" bed, 100W bifacial
panel, 24" stroke linear actuator** — large enough to fit a real
off-the-shelf bifacial panel and reach true 90° tilt, small enough
to sit on a workbench.

**Build time:** ~4-5 hours
**Build cost:** ~$220-280 (lumber + 100W panel + 24" actuator + battery)

---

## Phase 0: Order parts (Day 0, ~30 min)

### Lumber (all PT DF)
- 3 × 1x4x8ft (bed walls: 2 long + 1 short-wall source)
- 4 × 2x2x8ft (2 for long rails, 1 for cross rails, 1 for skids, 1 extra)
- 1 × 2x4x8ft (diagonal brace)

If pre-cut at the lumber yard:
- 2 × 1x4 @ 40" (long walls)
- 2 × 1x4 @ 20.5" (short walls, 4 per board)
- 2 × 2x2 @ 40" (long rails, 1 per board)
- 2 × 2x2 @ 19" (cross rails, 4 per board)
- 2 × 2x2 @ 40" (skids, 1 per board)
- 1 × 2x4 @ 42" (diagonal brace, offcut from 8ft)

### Hardware
- 2 × 4" butt hinges, ½" pin (Home Depot, ~$5 ea)
- 1 × ½" × 44" steel rod (Home Depot, ~$6) — continuous hinge pin
- 1 × 100W 12V bifacial solar panel, 38.58" × 20.87" × 1.18" (Newpowa, Amazon, ~$90)
- 1 × 24" stroke 12V linear actuator, 330 lbf (ECO-WORTHY or WindyNation, Amazon, ~$90)
- 6 × 2" aluminum mid-clamps for 35mm panel frame channel (Amazon, ~$3 ea = $18)
- 24 × #8 × 2" deck screws (HDG, ~$5)
- 8 × #6 × 1.5" wood screws (for diagonal brace, ~$2)
- 8 × 5/16" × 3" lag bolts (HDG, for hinges, ~$5)
- 2 × ½" × 3" clevis pins + cotter pins (for actuator, ~$3)
- 1 × 12V 20Ah LiFePO4 battery (Amazon, ~$80)

### Electronics (same as full-size)
- 1 × ESP32-WROOM-32 dev board (Mouser, ~$5)
- 1 × DPS5005 MPPT controller (Amazon, ~$25)
- 1 × BMI160 IMU breakout (Mouser, ~$2)
- 1 × INA219 current sensor breakout (Mouser, ~$2)
- 1 × DS18B20 temperature sensor (Amazon, ~$3)
- 1 × capacitive soil moisture sensor (Amazon, ~$3)
- Jumper wires, breadboard, perfboard for prototyping (~$10)
- (Optional: use the full-size PCB, ~$5 for 5pcs from JLCPCB)

**Total: ~$220-280.**

---

## Phase 1: Bed (Day 1, ~1.5 hours)

### 1.1 Cut the half-lap notches

Each bed wall has a 1.5" wide × 0.375" deep notch at each end.

**Tools:** circular saw, chisel, mallet, square

**Process:**
1. Mark the notch location on each wall (1.5" from each end, 0.375" deep).
2. Make multiple passes with the circular saw at the notch depth
   (don't try to cut 0.375" deep in one pass).
3. Clean out the waste with a chisel.
4. Test-fit two walls at a corner.

**Verification:** the two walls meet at a 90° corner with no daylight.

### 1.2 Assemble the bed box

**Tools:** drill, ⅛" pilot bit, #8 × 2" deck screws, square

For v2 (bigger than v1), use #8 × 2" deck screws (instead of #6 × 1.5")
at each corner for stronger joints (the bed is bigger and the soil load
is heavier).

**Process:**
1. Lay out the 4 walls on a flat surface.
2. Bring the corners together. The half-lap notches interlock.
3. Pre-drill 2 holes per corner (one near the top, one near the bottom).
4. Drive #8 × 2" deck screws through the corners.

**Verification:** bed box is 40" × 22" outside, square (measure
diagonally — both diagonals should be the same length).

### 1.3 Attach the skids

**Tools:** drill, ⅛" pilot bit, #8 × 2" screws

**Process:**
1. Flip the bed upside down.
2. Place two 2x2x40" skids under the bed, aligned with the long walls.
3. Pre-drill and screw through the skids into the bed walls.
4. Use 4 screws per skid (every ~10").

**Verification:** skids are flush with the bed ends, square, and the
whole bed sits level on the ground.

---

## Phase 2: Frame (Day 1, ~1.5 hours)

### 2.1 Assemble the frame rectangle

**Tools:** drill, ⅛" pilot bit, #8 × 2" deck screws, square

**Process:**
1. Lay the 4 frame rails (2 long + 2 cross) on a flat surface.
2. The cross rails fit between the long rails. Butt joints (no miter).
3. Pre-drill 2 holes per corner (through the cross rail into the long
   rail end). Use 2 screws per corner.
4. Drive #8 × 2" deck screws.

**Verification:** frame is square, 40" × 22" outside, 37" × 19" inside.

### 2.2 Add the diagonal brace

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" screws, measuring tape

**Process:**
1. The 2x4x42" diagonal brace runs corner to corner inside the frame.
2. Position the brace so its ends butt into the inside faces of the
   long rails (square ends, no miter).
3. Pre-drill 2 holes per end (through the brace into the long rail
   inside face).
4. Drive #6 × 1.5" screws (4 screws total, 2 per end).

**Verification:** brace is at the diagonal angle (~27°), both ends screwed.

### 2.3 Install hinges on the bed's south wall

**Tools:** drill, 5/16" bit (for lag bolts), ½" bit (for hinge knuckles),
lag bolts (5/16" × 3" HDG), measuring tape

**Process:**
1. Lay the frame on top of the bed, with the frame's south rail
   resting on the bed's south wall.
2. Position the 2 hinges evenly along the south rail: spacing ~26",
   centered (7" margin on each end of the 40" rail).
3. Mark the hinge positions on both the frame's south rail and the
   bed's south wall.
4. Pre-drill 4 holes per hinge (2 per leaf), 5/16" bit.
5. Attach the wall leaf to the bed's south wall with 5/16" × 3" lag bolts.
6. Attach the frame leaf to the frame's south rail with 5/16" × 3" lag bolts.
7. The frame should now hinge freely.

**Verification:** frame hinges smoothly between 0° and ~90° tilt. The
½" hinge pin holes in both hinges are aligned (the continuous pin passes
through both).

### 2.4 Insert the continuous hinge pin

**Tools:** mallet (rubber), ½" drill bit (if pin is too tight)

**Process:**
1. Thread the ½" × 44" steel rod through both hinges, starting from
   one end.
2. Tap gently with a rubber mallet to seat the pin fully.
3. The pin should extend ~1" past the last hinge on each end.

**Verification:** pin is fully seated. Frame hinges smoothly with the pin
in place. You should be able to manually tilt the frame from 0° to
nearly 90° (the actuator will be the limiting factor for full 90° travel).

---

## Phase 3: Panel (Day 1, ~15 min)

### 3.1 Sizing note (important!)

The 100W panel (38.58" × 20.87") is **larger** than the frame's interior
(37" × 19"). The panel sits ON TOP of the frame rails and overhangs the
frame interior by ~0.79" on the long sides and ~0.94" on the short sides.

The mid-clamps grip the panel frame at the rail positions, holding the
panel firmly. This is the same pattern as the full-size build.

### 3.2 Lift the panel onto the frame

**Tools:** two people (100W panel is ~15 lb)

**Process:**
1. With the frame flat on the bed, place the 100W panel on top of the
   frame, centered.
2. The panel's aluminum frame should rest on the wood rails.

**Verification:** panel is centered, with the overhang roughly equal on
all four sides (0.79" long, 0.94" short).

### 3.3 Clamp the panel to the frame

**Tools:** drill, M8 hex driver, 2" mid-clamps

**Process:**
1. Place 2 mid-clamps per long rail (4 total), at positions ±9" from
   the panel center.
2. Place 1 mid-clamp per cross rail (2 total), centered.
3. Tighten the M8 bolts to clamp the panel frame to the wood rails.
4. Torque to ~5 Nm (snug, not crushing the wood).

**Verification:** panel is firmly attached. Try to wiggle it — should
not move.

---

## Phase 4: Actuator Mount (Day 1, ~30 min)

### 4.1 Mount the wall block on the bed's north wall

**Tools:** drill, ⅛" pilot bit, #8 × 2" deck screws

**Process:**
1. Take a 2x2x4" block (cut from leftover 2x2 scrap).
2. Mount it on top of the bed's north wall, at the outer face (z=-22),
   centered along X.
3. Pre-drill 2 holes and drive #8 × 2" screws down through the block
   into the wall.

### 4.2 Mount the clevis on the frame's north rail

**Tools:** drill, ⅛" pilot bit, #8 × 2" deck screws

**Process:**
1. Take another 2x2x4" block.
2. Mount it on top of the frame's north rail, at the outer face,
   centered along X.
3. Pre-drill and screw into the rail.

### 4.3 Mount the actuator between the blocks

**Tools:** ½" clevis pin, cotter pin, mallet

**Process:**
1. The 24" stroke actuator has a ½" pin on each end (body side and
   rod side).
2. Pin the body-side clevis to the wall block (on the bed).
3. Pin the rod-side clevis to the clevis block (on the frame).
4. Use cotter pins to keep the clevis pins from sliding out.

**Verification:** actuator is pinned at both ends. Manually extend and
retract the rod — the frame should tilt up and down.

**NOTE on geometry:** the 24" stroke actuator is sized for ~85-90° tilt
with this geometry. If the frame binds before reaching 90°, the actuator
may need a longer bracket extension. See the `actuator_mount.py` source
in the model for the geometric analysis.

---

## Phase 5: Sensors and Wiring (Day 1, ~1 hour)

### 5.1 Install the IMU on the frame

Follow the same principle as the full-size build (see
`docs/sensor_placement.md` § 1): mount the BMI160 breakout on the
underside of the frame's north rail, centered, with the X axis along
the bed's long axis.

**Tools:** drill, #4 wood screws, foam adhesive pad

### 5.2 Install the soil sensors

If using the bed for plants:
- DS18B20: 3" deep in soil, 12" from south wall
- Soil moisture: 2" deep in soil, 18" from south wall

### 5.3 Mount the breadboard

For the mini, you can use a breadboard or perfboard for the ESP32
circuit instead of the full-size PCB. Mount the breadboard on the
bed's east short wall, near the battery.

**Tools:** #4 wood screws, double-sided tape (alternative)

### 5.4 Wire the breadboard

Follow `docs/wiring.md` (the same wiring works for the mini, just with
shorter cables).

**Tools:** jumper wires, wire stripper, multimeter

### 5.5 Continuity check

Before applying power, verify:
- [ ] No shorts between 12V and GND
- [ ] No shorts between 3V3 and GND
- [ ] No shorts between 5V and GND
- [ ] All sensors connected and addressed correctly

---

## Phase 6: Battery and First Power-On (Day 1, ~30 min)

### 6.1 Connect the battery

**Tools:** multimeter, 5A fuse

For v2, use a 5A fuse (the 24" stroke actuator can pull more current
than the v1 mini's 1A).

**Process:**
1. Place the 12V 20Ah LiFePO4 battery next to the bed.
2. Connect the battery negative to the breadboard's ground bus.
3. Connect the battery positive through a 5A fuse, then to the 12V
   rail on the breadboard.
4. **Do not install the fuse yet.**

### 6.2 Install the fuse and power on

**Process:**
1. Connect the laptop via USB to the ESP32.
2. Install the fuse.
3. The ESP32 should boot. The status LED should light up.
4. Flash the firmware: `esphome run firmware/wattplot.yaml`.

### 6.3 Verify boot

**Process:**
1. Open the serial monitor (115200 baud).
2. Look for ESPHome boot messages. Verify:
   - "Wattplot Controller" branding
   - IMU detected
   - DPS5005 detected
   - State: FOLDING (safe default)

### 6.4 Test each sensor

For each sensor, verify it's reading sensible values (see
`docs/test_checklist.md` Phase A for the full list).

---

## Phase 7: Solar Panel and MPPT (Day 1-2, ~30 min)

### 7.1 Connect the solar panel

**Tools:** MC4 crimper, wire stripper

**Process:**
1. The 100W panel has MC4 connectors on the back. Use MC4-to-wire
   adapters (or crimp your own).
2. Run the panel wires (positive + negative) from the panel to the
   breadboard.
3. Connect the panel input to the DPS5005 input.
4. Connect the DPS5005 output to the 12V battery (through a 5A fuse).

### 7.2 Test the MPPT

**Process:**
1. With the panel in sun, the DPS5005 should output ~14.4V to the
   battery.
2. Verify the ESP32 can read and adjust the DPS5005 setpoint via
   UART.
3. The battery voltage should rise slowly during the day.
4. Expected power: 80-90W peak at noon in full sun (after 15% derate).

---

## Phase 8: Soil and Planting (Day 2, ~15 min)

### 8.1 Fill the bed with soil

**Process:**
1. Fill the bed with 3.5" of soil (interior 38.5" × 20.5" × 3.5" =
   1.0 cu ft, ~7.5 gallons).
2. Use a potting mix (not native soil — too heavy for a small planter).

### 8.2 Plant something

**Process:**
1. Plant 1-2 small herbs (basil, parsley) or a small flower.
2. Use a starter fertilizer.

---

## Phase 9: Test and Validate (Day 2, ongoing)

### 9.1 Bench test (1 week)

Run the mini on your workbench for a week. Monitor:
- State machine transitions (NORMAL, BEDSUN, FOLDING)
- IMU accuracy (does the firmware tilt to the right angle?)
- MPPT efficiency (panel power → battery power)
- DLI computation (is the bed DLI sensible for plants?)
- WiFi connectivity (does HA see the device?)
- Actuator travel (does it reach 0° and 90°?)

### 9.2 What to learn from the mini

After a week, you'll know:
- Whether the hinge geometry is right (does the frame bind?)
- Whether the 24" actuator has enough travel (does it reach 90°?)
- Whether the IMU is accurate enough (or needs filtering)
- Whether the MPPT loop converges (or oscillates)
- Whether the state machine behaves as expected
- Whether the 100W panel produces expected power (~80-90W peak)
- Whether the bifacial gain is real (compare front vs rear illumination)

If the mini works for a week, the full-size build will work too.
Apply any tuning you discovered (Kp, Ki, deadband, target_current)
to the full-size firmware.

---

## Final build checklist

- [ ] Bed is level, square, and full of soil
- [ ] Frame hinges smoothly from 0° to ~90° tilt
- [ ] Hinge pin (½" × 44") is fully seated
- [ ] Panel is firmly clamped to the frame (6 mid-clamps)
- [ ] Actuator is mounted and pinned at both ends
- [ ] IMU is reading tilt correctly
- [ ] Battery is connected and charging via MPPT
- [ ] Solar panel is producing 80-90W peak in full sun
- [ ] ESP32 is online in Home Assistant
- [ ] State machine transitions are working
- [ ] MPPT is converging

**Mini complete. Apply learnings to the full-size build.**
