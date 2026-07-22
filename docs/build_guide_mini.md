# Wattplot Mini v1 — Build Guide

1/5-scale, fully functional design-validation prototype. Sits on a
workbench or window sill. Build it before committing to the full-size
build to validate the geometry, the hinge mechanism, the actuator
travel, the sensor placement, and the controller logic.

**Build time:** ~3-4 hours
**Build cost:** ~$100-130 (lumber + hardware + 10W panel + small battery)

---

## Phase 0: Order parts (Day 0, ~30 min)

### Lumber (all PT DF)
- 3 × 1x4x8ft (bed walls: 2 long + 1 short-wall source, 2 short walls per board)
- 1 × 1x2x8ft (frame rails: 4 rails from 1 board with 32" waste)
- 1 × 2x2x8ft (skids: 2 skids from 1 board, with 77" waste)
- 1 × 2x2x24" or 1x2x24" (diagonal brace — can be a cut-off from the skids board)

If pre-cut at the lumber yard:
- 2 × 1x4 @ 19" (long walls)
- 2 × 1x4 @ 8.5" (short walls, 2 per board)
- 4 × 1x2 @ 19" (long rails)
- 4 × 1x2 @ 8.5" (cross rails, 2 per board)
- 2 × 2x2 @ 19" (skids)
- 1 × 1x2 or 2x2 @ 20" (diagonal brace)

### Hardware
- 2 × 1.5" butt hinges, ⅜" pin (Home Depot, ~$3 ea)
- 1 × ⅜" × 24" steel rod (Home Depot, ~$3) — continuous hinge pin
- 1 × 10W 12V mono solar panel, 17.32" × 8.46" (Newpowa, Amazon, ~$25)
- 1 × 1" stroke 12V micro linear actuator, 25 lbf (Amazon, ~$15)
- 4 × 1" aluminum mid-clamps for 18mm panel frame channel (Amazon, ~$2 ea = $8)
- 8 × #6 × 1.5" wood screws (for frame joints, ~$3)
- 4 × ⅛" × 1" wood screws (for cleats, ~$1)
- 2 × ⅛" × 2" cotter pins (for clevis pin, ~$1)
- 1 × 12V 5Ah LiFePO4 battery (Amazon, ~$50)

### Electronics (same as full-size)
- 1 × ESP32-WROOM-32 dev board (Mouser, ~$5)
- 1 × DPS5005 MPPT controller (Amazon, ~$25)
- 1 × BMI160 IMU breakout (Mouser, ~$2)
- 1 × INA219 current sensor breakout (Mouser, ~$2)
- 1 × DS18B20 temperature sensor (Amazon, ~$3)
- 1 × capacitive soil moisture sensor (Amazon, ~$3)
- Jumper wires, breadboard, perfboard for prototyping (~$10)
- (Optional: use the full-size PCB, ~$5 for 5pcs from JLCPCB)

**Total: ~$110-130.**

---

## Phase 1: Bed (Day 1, ~1 hour)

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

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" screws, square

For a small bed, just use wood screws (no need for carriage bolts at this
size). Pre-drill and screw each corner.

**Process:**
1. Lay out the 4 walls on a flat surface.
2. Bring the corners together. The half-lap notches interlock.
3. Pre-drill 2 holes per corner (one near the top, one near the bottom).
4. Drive #6 × 1.5" wood screws through the corners.

**Verification:** bed box is 19" × 10" outside, square (measure diagonally).

### 1.3 Attach the skids

**Tools:** drill, ⅛" pilot bit, screws

**Process:**
1. Flip the bed upside down.
2. Place two 2x2x19" skids under the bed, aligned with the long walls.
3. Pre-drill and screw through the skids into the bed walls.

**Verification:** skids are flush with the bed ends and square.

---

## Phase 2: Frame (Day 1, ~1 hour)

### 2.1 Assemble the frame rectangle

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" screws, square

**Process:**
1. Lay the 4 frame rails (2 long + 2 cross) on a flat surface.
2. The cross rails fit between the long rails. Butt joints (no miter).
3. Pre-drill 2 holes per corner (through the cross rail into the long
   rail end).
4. Drive #6 × 1.5" screws.

**Verification:** frame is square, 19" × 10" outside, 17.5" × 8.5" inside.

### 2.2 Add the diagonal brace

**Tools:** drill, ⅛" pilot bit, screws, measuring tape

**Process:**
1. The 1x2x20" diagonal brace runs corner to corner inside the frame.
2. Position the brace so its ends butt into the inside faces of the
   long rails (square ends, no miter).
3. Pre-drill 2 holes per end (through the brace into the long rail
   inside face).
4. Drive screws.

**Verification:** brace is at the diagonal angle (~28°), both ends screwed.

### 2.3 Install hinges on the bed's south wall

**Tools:** drill, 5/64" pilot bit, screws (the small butt hinges come
with their own screws), measuring tape

**Process:**
1. Lay the frame on top of the bed, with the frame's south rail
   resting on the bed's south wall.
2. Position the 2 hinges evenly along the south rail: spacing ~13",
   centered (3" margin on each end of the 19" rail).
3. Mark the hinge positions on both the frame's south rail and the
   bed's south wall.
4. Pre-drill 4 holes per hinge (2 per leaf), 5/64" bit.
5. Attach the wall leaf to the bed's south wall.
6. Attach the frame leaf to the frame's south rail.
7. The frame should now hinge freely.

**Verification:** frame hinges smoothly between 0° and 90° tilt. The ⅜"
hinge pin holes in both hinges are aligned (the continuous pin passes
through both).

### 2.4 Insert the continuous hinge pin

**Tools:** mallet (rubber), ⅜" drill bit (if pin is too tight)

**Process:**
1. Thread the ⅜" × 24" steel rod through both hinges, starting from
   one end.
2. Tap gently with a rubber mallet to seat the pin fully.
3. The pin should extend ~1" past the last hinge on each end.

**Verification:** pin is fully seated. Frame hinges smoothly with the pin in place.

---

## Phase 3: Panel (Day 1, ~15 min)

### 3.1 Lift the panel onto the frame

**Tools:** hands (10W panel is only ~2.5 lb)

**Process:**
1. Place the 10W panel inside the frame, centered.
2. The panel frame (aluminum) should sit on top of the wood frame.

**Verification:** panel is centered, frame interior clearances are even on
all sides (~0.04" on the long sides, 0.18" on the short sides).

### 3.2 Clamp the panel to the frame

**Tools:** drill, M8 hex driver, 1" mid-clamps

**Process:**
1. Place 2 mid-clamps per long rail (4 total), at positions ±9.5" from
   the panel center.
2. Tighten the M8 bolts to clamp the panel frame to the wood rails.
3. Torque to ~5 Nm (snug, not crushing).

**Verification:** panel is firmly attached. Try to wiggle it — should
not move.

### 3.3 Install the actuator

**Tools:** drill, ⅛" pilot bit, screws, ⅛" cotter pin

**Process:**
1. The actuator is between the bed's north wall and the frame's north
   rail.
2. Mount the wall-side clevis block (1x2, 3" long) on top of the bed's
   north wall, near the bed's center.
3. Mount the frame-side clevis block on the inside face of the frame's
   north rail, near the bed's center.
4. The actuator's body is on the frame-side, the rod extends toward
   the wall.
5. Pin the actuator to the wall block with a ⅜" pin (a ⅛" cotter pin
   works in a pinch).
6. Pin the actuator's rod end to the frame block.

**Verification:** actuator is mounted, rod can extend and retract. Frame
can be tilted by hand from 0° to 90°.

---

## Phase 4: Sensors and Wiring (Day 1, ~1 hour)

### 4.1 Install the IMU on the frame

Follow the same principle as the full-size build (see
`docs/sensor_placement.md` § 1): mount the BMI160 breakout on the
underside of the frame's north rail, centered, with the X axis along
the bed's long axis.

**Tools:** drill, #4 wood screws, foam adhesive pad

### 4.2 Install the limit switches

For the mini, the limit switches are optional (the IMU is reliable
enough for a validation prototype). If you add them:
- 0° switch on the bed's south wall, just below the hinge axis
- 90° switch on the bed's north wall, near the actuator mount

### 4.3 Install the soil sensors

If using the bed for plants:
- DS18B20: 3" deep in soil, 6" from south wall
- Soil moisture: 2" deep in soil, 9" from south wall

### 4.4 Mount the PCB (or breadboard)

For the mini, you can use a breadboard or perfboard for the ESP32
circuit instead of the full-size PCB. Mount the breadboard on the
bed's east short wall, near the battery.

**Tools:** #4 wood screws, double-sided tape (alternative)

### 4.5 Wire the PCB/breadboard

Follow `docs/wiring.md` (the same wiring works for the mini, just with
shorter cables).

**Tools:** jumper wires, wire stripper, multimeter

### 4.6 Continuity check

Before applying power, verify:
- [ ] No shorts between 12V and GND
- [ ] No shorts between 3V3 and GND
- [ ] No shorts between 5V and GND
- [ ] All sensors connected and addressed correctly

---

## Phase 5: Battery and First Power-On (Day 1, ~30 min)

### 5.1 Connect the battery

**Tools:** multimeter, 1A fuse

For the mini, use a 1A fuse (the actuator stall is much lower than
full-size).

**Process:**
1. Place the 12V 5Ah LiFePO4 battery next to the bed.
2. Connect the battery negative to the breadboard's ground bus.
3. Connect the battery positive through a 1A fuse, then to the 12V
   rail on the breadboard.
4. **Do not install the fuse yet.**

### 5.2 Install the fuse and power on

**Process:**
1. Connect the laptop via USB to the ESP32.
2. Install the fuse.
3. The ESP32 should boot. The status LED should light up.
4. Flash the firmware: `esphome run firmware/wattplot.yaml`.

### 5.3 Verify boot

**Process:**
1. Open the serial monitor (115200 baud).
2. Look for ESPHome boot messages. Verify:
   - "Wattplot Controller" branding
   - IMU detected
   - DPS5005 detected
   - State: FOLDING (safe default)

### 5.4 Test each sensor

For each sensor, verify it's reading sensible values (see
`docs/test_checklist.md` Phase A for the full list).

---

## Phase 6: Solar Panel and MPPT (Day 1-2, ~30 min)

### 6.1 Connect the solar panel

**Tools:** MC4 crimper, wire stripper

**Process:**
1. The 10W panel has MC4 connectors on the back. Use MC4-to-wire
   adapters (or crimp your own).
2. Run the panel wires (positive + negative) from the panel to the
   breadboard.
3. Connect the panel input to the DPS5005 input.
4. Connect the DPS5005 output to the 12V battery (through a 1A fuse).

### 6.2 Test the MPPT

**Process:**
1. With the panel in sun, the DPS5005 should output ~14.4V to the
   battery.
2. Verify the ESP32 can read and adjust the DPS5005 setpoint via
   UART.
3. The battery voltage should rise slowly during the day.

---

## Phase 7: Soil and Planting (Day 2, ~15 min)

### 7.1 Fill the bed with soil

**Process:**
1. Fill the bed with 3.5" of soil (interior 17.5" × 8.5" × 3.5" = 0.3
   cu ft, ~1.5 gallons).
2. Use a potting mix (not native soil — too heavy for a small planter).

### 7.2 Plant a small herb or flower

**Process:**
1. Plant 1-2 small herbs (basil, parsley) or 1 small flower.
2. Use a starter fertilizer.

---

## Phase 8: Test and Validate (Day 2, ongoing)

### 8.1 Bench test (1 week)

Run the mini on your workbench for a week. Monitor:
- State machine transitions (NORMAL, BEDSUN, FOLDING)
- IMU accuracy (does the firmware tilt to the right angle?)
- MPPT efficiency (panel power → battery power)
- DLI computation (is the bed DLI sensible for plants?)
- WiFi connectivity (does HA see the device?)

### 8.2 What to learn from the mini

After a week, you'll know:
- Whether the hinge geometry is right (does the frame bind?)
- Whether the actuator has enough travel (does it reach 90°?)
- Whether the IMU is accurate enough (or needs filtering)
- Whether the MPPT loop converges (or oscillates)
- Whether the state machine behaves as expected

If the mini works for a week, the full-size build will work too.
Apply any tuning you discovered (Kp, Ki, deadband, target_current)
to the full-size firmware.

---

## Final build checklist

- [ ] Bed is level, square, and full of soil
- [ ] Frame hinges smoothly from 0° to 90°
- [ ] Hinge pin is fully seated
- [ ] Panel is firmly clamped to the frame
- [ ] Actuator is mounted and pinned
- [ ] IMU is reading tilt correctly
- [ ] Battery is connected and charging
- [ ] Solar panel is producing power
- [ ] ESP32 is online in Home Assistant
- [ ] State machine transitions are working
- [ ] MPPT is converging

**Mini complete. Apply learnings to the full-size build.**
