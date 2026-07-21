# Wattplot v2 — Build Guide

Step-by-step assembly of the entire apparatus. Follow the order below.
Each step lists the **time**, **tools**, **parts**, and **verification**.

**Total build time:** ~10-15 hours over a weekend (with lumber pre-cut).

**Total cost:** ~$1,400 (per the BOM at `bom.md`).

---

## Phase 0: Pre-build (Day 0, ~1 hour)

### 0.1 Order lumber

From the BOM at `bom.md`:
- 6 × 2x12x8ft PT DF (bed walls, 4 long + 2 short)
- 2 × 2x6x8ft PT DF (long rails)
- 2 × 2x6x8ft PT DF (cross rails)
- 1 × 2x4x10ft PT DF (diagonal brace)
- 2 × 4x4x8ft PT DF (skids)

If your lumber yard offers FSC-certified DF, request it (small premium).
FSC chain-of-custody: ask for the certificate.

**Tip:** many yards will cut to length for free or a small fee. Have
them cut:
- 4 × 2x12 @ 96" (long walls, no cut needed from 8ft)
- 4 × 2x12 @ 44.6" (short walls, 2 per board from 8ft)
- 2 × 2x6 @ 96" (long rails, no cut)
- 4 × 2x6 @ 42" (cross rails, 2 per board)
- 1 × 2x4 @ 102" (diagonal brace, cut from 10ft)
- 2 × 4x4 @ 96" (skids, no cut)

If they don't pre-cut, you'll need a circular saw or miter saw. None
of the cuts are mitered (90° only). A standard circular saw is enough.

### 0.2 Order hardware

- 4 × galvanized butt hinges 4"×4" leaf, ½" pin (Home Depot)
- 1 × ½" × 72" steel rod (Home Depot, in the steel rod section)
- 6 × aluminum mid-clamps 35mm channel (IronRidge / Unirac)
- 1 × ECO-WORTHY 12V 4" stroke 330 lbf linear actuator (Amazon)
- 1 × ½" × 3" clevis pin (McMaster)
- 8 × 3/8" × 4" carriage bolts HDG + washers + nuts (Home Depot)
- 8 × 5/16" × 3" lag bolts HDG (Home Depot)
- 24 × ¼" × 3" deck screws HDG Torx T-25 (Home Depot, 1 lb box)
- 1 lb box × 3" exterior deck screws (general)

### 0.3 Order the panel + electrical

- 1 × 620 W bifacial panel (LONGi Hi-MO X10 or similar)
- 1 × 12V 100Ah LiFePO4 battery (LiTime or similar)
- 1 × DPS5005 programmable buck converter (Amazon, $25)
- 1 × 12V LED grow light (20-30W, full spectrum)
- 1 × ESP32-WROOM-32E dev board (or use the PCB from `docs/pcb_design.md`)

### 0.4 Order the PCB (optional but recommended)

Send the design from `docs/pcb_design.md` to JLCPCB (5 pieces for $5+shipping).
While you wait (1-2 weeks), continue with the mechanical build.

---

## Phase 1: Bed (Day 1, ~3 hours)

### 1.1 Cut the wall half-lap notches

Each bed wall has a 3" wide × 0.75" deep notch at each end (the
half-lap joint). Cut the notches with a circular saw + chisel, or with
a router + straight bit.

**Tools:** circular saw, chisel, mallet, square

**Process:**
1. Mark the notch location on the wall (3" from each end, 0.75" deep).
2. Make multiple passes with the circular saw at the notch depth
   (don't try to cut 0.75" deep in one pass).
3. Clean out the waste with a chisel.
4. Test-fit two walls at a corner. They should sit flush with no gap.

**Verification:** the two walls meet at a 90° corner with the outer
faces flush. No daylight between them.

### 1.2 Assemble the bed box

**Tools:** drill, ⅜" bit, 9/16" wrench, square, level

**Process:**
1. Lay out the 4 walls on a flat surface (a driveway or garage floor).
2. Bring the corners together. The half-lap notches interlock.
3. Drill two ⅜" holes through each corner joint (one near the top,
   one near the bottom).
4. Drive 3/8" × 4" carriage bolts through the holes. Add washer + nut
   on the inside. Tighten with a 9/16" wrench.
5. Check the bed for square: measure diagonally both ways. Should be
   equal (~105" each).

**Verification:** bed box is 96" × 44.6" outside, walls are
plumb (vertical), corners are square.

### 1.3 Attach the skids

**Tools:** drill, ¼" bit, impact driver, square

**Process:**
1. Flip the bed upside down.
2. Place two 4x4x8ft skids under the bed, aligned with the long
   walls. The skids extend 0" past the bed ends (flush).
3. Pre-drill 4 holes per skid (2 per end), ¼" pilot bit, through the
   skid and into the bed wall.
4. Drive ¼" × 3" deck screws through the skid into the wall.

**Verification:** skids are flush with the bed ends and square to the
bed. The bed sits flat on the skids.

### 1.4 Place the bed at the site

**Tools:** level, shovel (if site prep needed)

**Process:**
1. Move the bed to its final location. The bed is heavy (~150 lb empty,
   ~2000 lb with soil). Get help.
2. Level the bed in both directions (use shims under the skids if
   needed).
3. The bed should slope slightly toward the south (1-2% grade) for
   drainage. Adjust shims.

**Verification:** bed is level (or slightly tilted south), skids are
fully supported, no wobble.

---

## Phase 2: Frame (Day 1, ~2 hours)

### 2.1 Assemble the frame rectangle

**Tools:** drill, ¼" bit, impact driver, square, measuring tape

**Process:**
1. Lay the 4 frame rails (2 long + 2 cross) on a flat surface.
2. The cross rails fit between the long rails. Butt joints at the
   corners (no miter).
3. Pre-drill 2 holes per corner (through the cross rail into the long
   rail end), ¼" pilot bit.
4. Drive ¼" × 3" deck screws.
5. The frame interior should be 93" × 42" (PANEL_L - 2*RAIL_T) ×
   (CROSS_RAIL_L).
6. The frame exterior should be 96" × 45.6".

**Verification:** frame is square (measure diagonally), 96" × 45.6"
outside, 93" × 42" inside.

### 2.2 Add the diagonal brace

**Tools:** drill, ¼" bit, impact driver, measuring tape

**Process:**
1. The 2x4x102" diagonal brace runs corner to corner inside the frame.
2. Position the brace so its ends butt into the inside faces of the
   long rails.
3. The brace is at the height of the rails (sits on the bottom inside
   face of the long rails, or just above).
4. Pre-drill 2 holes per end (through the brace into the long rail
   inside face), ¼" pilot bit.
5. Drive ¼" × 3" deck screws.

**Verification:** brace is at the correct diagonal angle (~24°), both
ends are screwed to the long rails. Frame is now rigid (no racking).

### 2.3 Install hinges on the bed's south wall

**Tools:** drill, 5/16" bit, impact driver with socket, measuring tape

**Process:**
1. Lay the frame on top of the bed, with the frame's south rail
   resting on the bed's south wall.
2. Position the 4 hinges evenly along the south rail: spacing 22",
   centered, 4" margin on each end of the 96" wall.
3. Mark the hinge positions on both the frame's south rail and the
   bed's south wall.
4. Pre-drill 4 holes per hinge (2 per leaf), 5/16" bit for the lag
   bolts.
5. Attach the wall leaf of each hinge to the bed's south wall with
   5/16" × 3" lag bolts.
6. Attach the frame leaf of each hinge to the frame's south rail
   with 5/16" × 3" lag bolts.
7. The frame should now hinge freely on the south wall.

**Verification:** frame hinges smoothly between 0° and 90° tilt. No
binding. The ½" hinge pin holes in all 4 hinges are aligned (the
continuous pin will pass through all 4).

### 2.4 Insert the continuous hinge pin

**Tools:** mallet (rubber), ½" drill bit (if pin is too tight)

**Process:**
1. Thread the ½" × 72" steel rod through all 4 hinges, starting from
   one end.
2. Tap gently with a rubber mallet to seat the pin fully.
3. The pin should extend ~1" past the last hinge on each end.

**Verification:** pin is fully seated. The frame hinges smoothly with
the pin in place.

---

## Phase 3: Panel (Day 2, ~1 hour)

### 3.1 Lift the panel onto the frame

**Tools:** helper(s), ladder if needed

**Process:**
1. The 620 W bifacial panel weighs ~65 lb. Get help.
2. With the frame flat (0°), place the panel inside the frame, centered.
3. The panel frame (aluminum) should sit on top of the wood frame.

**Verification:** panel is centered, frame interior clearances are
even on all sides.

### 3.2 Clamp the panel to the frame

**Tools:** drill, 5/16" hex driver, M8 wrench, ladder if needed

**Process:**
1. Place 2 mid-clamps per long rail (4 total), at positions ±24" from
   the panel center (4 evenly spaced clamps along the 96" rail).
2. Place 1 mid-clamp per cross rail (2 total), at the panel center
   (each side of the panel, where the cross rail meets the panel).
3. Tighten the M8 bolts to clamp the panel frame to the wood rails.
4. Torque to ~10 Nm (snug, not crushing).

**Verification:** panel is firmly attached. Try to wiggle it — should
not move.

### 3.3 Install the actuator

**Tools:** drill, ½" bit, 9/16" wrench, 2× helpers

**Process:**
1. The actuator is between the bed's north wall and the frame's north
   rail.
2. Mount the wall-side clevis block (2x6 PT, 6" long) on top of the
   bed's north wall, near the bed's center.
3. Mount the frame-side clevis block on the inside face of the frame's
   north rail, near the bed's center.
4. The actuator's body is on the frame-side, the rod extends toward
   the wall.
5. Pin the actuator to the wall block with the ½" × 3" clevis pin.
6. Pin the actuator's rod end to the frame block with another clevis
   pin (or use the same pin if the actuator has both ends pinned).

**Verification:** actuator is mounted, rod can extend and retract. Frame
can be tilted by hand from 0° to 90°.

---

## Phase 4: Sensors and Wiring (Day 2, ~3 hours)

### 4.1 Install the IMU on the frame

Follow `docs/sensor_placement.md` § 1.

**Tools:** drill, #4 wood screws, small Phillips, foam adhesive pad

**Process:**
1. Mount the BMI160 breakout board on the **underside** of the frame's
   north rail, centered.
2. Use 2× #4 wood screws through the breakout's mounting holes.
3. Add a small foam adhesive pad between the breakout and the wood to
   dampen vibration.
4. Run the 4-wire I2C cable along the north rail to the cable carrier.

### 4.2 Install the limit switches

Follow `docs/sensor_placement.md` § 6.

**Tools:** drill, small wood screws

**Process:**
1. Mount the **0° switch** on a small wood block on the bed's south
   wall, just below the hinge axis. The roller faces the frame's
   south rail.
2. Mount the **90° switch** on a small wood block on the bed's north
   wall, near the actuator mount. The roller faces the frame's north
   rail.
3. Test by tilting the frame by hand:
   - At 0° (flat), the 0° switch should be pressed.
   - At 90° (vertical), the 90° switch should be pressed.
4. Run the 3-wire cable (signal, signal, GND) from the switches to the
   PCB.

### 4.3 Install the soil sensors

Follow `docs/sensor_placement.md` § 3-4.

**Tools:** shovel, drill (for grommet holes), screwdriver

**Process:**
1. Drill a ½" hole in the bed's south wall, 12" from the east end
   (for the soil cables).
2. Insert a rubber grommet in the hole.
3. Push the DS18B20 probe into the soil to 6" depth, 12" from the
   south wall, 24" from the east end.
4. Push the soil moisture sensor into the soil to 4" depth, 18" from
   the south wall, 24" from the east end.
5. Run the cables through the grommet, up the south wall, into the
   cable carrier, to the PCB.

### 4.4 Mount the PCB enclosure

**Tools:** drill, #10 wood screws, level

**Process:**
1. Mount the PCB enclosure on the bed's east short wall, at table
   height (~30" above ground).
2. The enclosure should be accessible for service (not buried in
   foliage).
3. Use 4× #10 wood screws through the enclosure's mounting feet into
   the bed wall.
4. Verify the enclosure is level (for any internal status displays).

### 4.5 Wire the PCB to all components

Follow `docs/wiring.md`.

**Tools:** wire stripper, JST-XH crimper, screwdriver, multimeter

**Process:** connect each cable as described in the wiring table.
**Do not install the battery fuse yet.**

### 4.6 Continuity check

**Tools:** multimeter

Before applying power, verify:
- [ ] No shorts between 12V and GND (multimeter continuity)
- [ ] No shorts between 3V3 and GND
- [ ] No shorts between 5V and GND
- [ ] Each limit switch closes when pressed (0 Ω when activated)
- [ ] All JST-XH connectors are fully seated
- [ ] No bare wire exposed at any connector

---

## Phase 5: Battery and First Power-On (Day 2, ~1 hour)

### 5.1 Connect the battery

**Tools:** multimeter, 5A fuse

**Process:**
1. Place the 12V LiFePO4 battery on the ground next to the bed (or
   in a small battery box).
2. Connect the battery negative to the PCB enclosure's ground bus.
3. Connect the battery positive through a 5A in-line fuse, then to
   the PCB's J1+ terminal.
4. **Do not install the fuse yet.** Leave the fuse holder empty.

### 5.2 Install the fuse and power on

**Tools:** USB cable, laptop

**Process:**
1. With the laptop connected via USB-C to the PCB's J3, install the
   fuse.
2. The ESP32 should boot. The status LED should light up (any color
   means power is on).
3. Open the Arduino IDE or ESPHome flasher. Verify the ESP32 is
   detected.
4. Flash the firmware: `esphome run firmware/wattplot.yaml`.

### 5.3 Verify boot

**Tools:** serial monitor

**Process:**
1. Open the serial monitor (115200 baud).
2. Look for ESPHome boot messages. Should see:
   - "Wattplot Controller" branding
   - "BMI160" detected
   - "INA219" detected
   - "DS18B20" detected
   - "DPS5005" detected (if connected)
   - State: FOLDING (safe default)

### 5.4 Test each sensor

**Tools:** serial monitor, web browser (Home Assistant)

For each sensor, verify it's reading sensible values:
- [ ] IMU: tilt = ~0° when frame is flat, ~35° when tilted
- [ ] INA219: current = ~0 A when actuator is stationary
- [ ] DS18B20: temp = ~70-80°F in Phoenix afternoon
- [ ] Soil moisture: ~30-60% depending on soil wetness
- [ ] Battery voltage: ~12.0-13.5 V (LiFePO4 range)
- [ ] Limit switches: HIGH when open, LOW when pressed
- [ ] DPS5005: responds to UART commands

---

## Phase 6: Soil and Planting (Day 2-3, ~1 hour)

### 6.1 Fill the bed with soil

**Tools:** wheelbarrow, shovel, rake

**Process:**
1. Fill the bed with 11.25" of soil (1 cubic yard = 27 cu ft, bed
   interior is 93" × 41.6" × 11.25" = 30.1 cu ft = 1.1 cu yd).
2. Use a 50/50 mix of native soil and compost. Or just compost.
3. Wet the soil to settle it.

### 6.2 Plant tomatoes

**Tools:** trowel, tomato seedlings, fertilizer

**Process:**
1. Plant 4 tomato seedlings, one in each quadrant of the bed
   (16" from each wall, evenly spaced).
2. Use a 6-24-24 starter fertilizer at planting.
3. Install drip irrigation (optional but recommended for consistent
   watering).

### 6.3 Install the grow light (if used)

**Tools:** drill, screws, 12V LED fixture

**Process:**
1. Bolt the grow light fixture to the top of the frame's east and
   west cross rails.
2. Run the 12V switched wire from PCB J5 to the light, through the
   cable carrier.
3. Test by toggling the grow light from Home Assistant.

---

## Phase 7: Final Wiring and Validation (Day 3, ~1 hour)

### 7.1 Connect the solar panel

**Tools:** MC4 crimper, wire stripper

**Process:**
1. Mount the 620W bifacial panel on the frame (already done in
   Phase 3).
2. Run the MC4 cables from the panel's junction box down through the
   cable carrier to the PCB enclosure.
3. Splice the panel leads: one leg to the microinverter (240 VAC), one
   leg to the DPS5005 input (for MPPT battery charging).
4. The microinverter is its own certified box — install per its
   instructions.

### 7.2 Validate the state machine

**Tools:** serial monitor, web UI

**Process:**
1. With everything connected, the firmware should be in FOLDING state
   (safe default).
2. Verify the state transitions:
   - Send a command to go to NORMAL → frame tilts to 35° via the
     actuator, IMU reads 35°, INA219 reads 0 A.
   - Send a command to go to BEDSUN → frame tilts to 90° (vertical).
   - Send a command to go back to FOLDING → frame tilts to 0° (flat).
3. Check the decision stack:
   - Disconnect WiFi → state should still update (offline mode).
   - Mock a high-wind NWS forecast → state should go to FOLDING.
   - Disconnect the IMU → watchdog should trigger, state should go to
     FOLDING.

### 7.3 Test the MPPT

**Tools:** multimeter

**Process:**
1. With the panel exposed to sun, the DPS5005 should be outputting
   ~14.4V to the battery.
2. The battery voltage should rise slowly during the day.
3. Verify the ESP32 can read and adjust the DPS5005 setpoint via
   UART (use the web UI to change the setpoint, see the change on
   the multimeter).

### 7.4 Test the DLI grow light

**Tools:** serial monitor, web UI

**Process:**
1. With the panel in NORMAL state, check the DLI reading (mol/m²/day).
2. If DLI is below target, the grow light should come on.
3. Verify the light turns on (visually) and the timer limits to 16
   hours on / 8 hours off.

---

## Phase 8: Documentation (Day 3, ~30 min)

### 8.1 Take build photos

Follow the **photo template** in the README (Build section).

### 8.2 Log the build

In `docs/build_log.md` (create it), write:
- Date and time of each phase
- Any deviations from this guide
- Any issues encountered
- Photos (with captions)

### 8.3 Update the README

In the main README, add the build photos to the "Build photos" section.

---

## Build checklist (final, before considering the build "done")

- [ ] Bed is level, square, and full of soil
- [ ] Frame hinges smoothly from 0° to 90°
- [ ] Hinge pin is fully seated
- [ ] Panel is firmly clamped to the frame
- [ ] Actuator is mounted and pinned
- [ ] IMU is reading tilt correctly
- [ ] Limit switches trigger at 0° and 90°
- [ ] Soil sensors are reading
- [ ] Battery is connected and charging
- [ ] Solar panel is producing power (DPS5005 output is 14.4V)
- [ ] Microinverter is grid-tied (240 VAC out)
- [ ] ESP32 is online in Home Assistant
- [ ] State machine transitions are working
- [ ] DLI grow light is operating correctly
- [ ] All grommets are sealed
- [ ] Conformal coating is applied to the PCB (optional but recommended)

**Build complete.** Enjoy the tomatoes and the kWh.
