# Wattplot Mini v2.4 — Build Guide

Benchtop design-validation prototype. **18"×14" bed, ECO-WORTHY
10W panel, 100mm kickstand linear actuator** — sized to match the
parts you already ordered.

**Tilt range: 0-35°** (limited by the kickstand geometry; matches the
power-optimal range per the Phoenix sun sim).

**Build time:** ~3-4 hours
**Build cost:** ~$193 (new parts: DPS5005 MPPT, sensors, lumber, hardware,
solenoid watering). Already have: $50 (battery, ESP32, actuator, panel).

---

## Phase 0: Order parts (Day 0, ~30 min)

### Already ordered (Saturday)
- 1 × 12V 7Ah LiFePO4 battery (BMS built-in)
- 1 × 100mm (3.94") stroke 12V linear actuator, 70N (15.7 lbf)
- 1 × ESP32-C3 PRO Mini dev board
- 1 × ECO-WORTHY 10W 12V solar panel (13.3" × 8.1" × 0.7", 1.88 lb)

### Still need to order (one-stop)
- **1 × DPS5005 programmable buck converter** (~$25, Amazon) — **REPLACES
  the HiLetgo CN3791** you ordered (CN3791 is for 1S LiPo, not 12V
  LiFePO4 — incompatible with the battery you have)
- 2 × 1.5" butt hinges with ⅜" pin (~$3 ea, Home Depot)
- 1 × ⅜" × 22" steel rod (continuous hinge pin, ~$3, Home Depot)
- 4 × 1" aluminum mid-clamps for 18mm panel frame channel (~$2 ea, Amazon)
- 1 × BMI160 IMU breakout (~$2, Mouser)
- 1 × INA219 current sensor breakout (~$2, Mouser)
- 1 × DS18B20 waterproof temp sensor (~$3, Amazon)
- 1 × Capacitive soil moisture sensor (~$3, Amazon)
- 1 × Breadboard or perfboard + jumper wires (~$8, Amazon)
- 1 × USB-C cable (~$3, Amazon)
- Fasteners: 16 × #6 × 1.5" wood screws, 8 × #6 × 1" screws, 4 × M8 × 1.5"
  stainless bolts, 8 × 5/64" × 1" hinge screws, 2 × ⅜" clevis pins

### Lumber (all PT DF, all from 8ft stock)
- 1 × 1x4x8ft (bed walls: 2 long + 2 short, all from 1 board)
- 2 × 1x2x8ft (1 for frame rails, 1 for skids + kickstand mount blocks)
- 1 × 2x4x8ft (diagonal brace offcut)

If pre-cut at the lumber yard:
- 2 × 1x4 @ 18" (long walls)
- 2 × 1x4 @ 12.5" (short walls)
- 2 × 1x2 @ 18" (long rails)
- 2 × 1x2 @ 12.5" (cross rails)
- 2 × 1x2 @ 18" (skids)
- 2 × 1x2 @ 3" (kickstand mount blocks)
- 1 × 2x4 @ 21" (diagonal brace)

**Total lumber cost: ~$19**

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

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" wood screws, square

The bed is small (18"×14"), so the joints don't need to be as beefy as
the full-size. Use #6 × 1.5" wood screws (instead of #8 × 2" for the
bigger builds).

**Process:**
1. Lay out the 4 walls on a flat surface.
2. Bring the corners together. The half-lap notches interlock.
3. Pre-drill 2 holes per corner (one near the top, one near the bottom).
4. Drive #6 × 1.5" wood screws through the corners.

**Verification:** bed box is 18" × 14" outside, square (measure
diagonally — both diagonals should be the same length).

### 1.3 Attach the skids

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" screws

**Process:**
1. Flip the bed upside down.
2. Place two 1x2x18" skids under the bed, aligned with the long walls.
3. Pre-drill and screw through the skids into the bed walls.
4. Use 2-3 screws per skid.

**Verification:** skids are flush with the bed ends, square, and the
whole bed sits level on the ground.

---

## Phase 2: Frame (Day 1, ~1 hour)

### 2.1 Assemble the frame rectangle

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" wood screws, square

**Process:**
1. Lay the 4 frame rails (2 long + 2 cross) on a flat surface.
2. The cross rails fit between the long rails. Butt joints (no miter).
3. Pre-drill 2 holes per corner (through the cross rail into the long
   rail end). Use 2 screws per corner.
4. Drive #6 × 1.5" wood screws.

**Verification:** frame is square, 18" × 14" outside, 16.5" × 12.5"
inside.

### 2.2 Add the diagonal brace

**Tools:** drill, ⅛" pilot bit, #6 × 1" screws, measuring tape

**Process:**
1. The 2x4x21" diagonal brace runs corner to corner inside the frame.
2. Position the brace so its ends butt into the inside faces of the
   long rails (square ends, no miter).
3. Pre-drill 2 holes per end (through the brace into the long rail
   inside face).
4. Drive #6 × 1" screws (4 screws total, 2 per end).

**Verification:** brace is at the diagonal angle (~37°), both ends screwed.

### 2.3 Install hinges on the bed's south wall

**Tools:** drill, 5/64" bit (for hinge screws), screws (the small butt
hinges come with their own screws), measuring tape

**Process:**
1. Lay the frame on top of the bed, with the frame's south rail
   resting on the bed's south wall.
2. Position the 2 hinges evenly along the south rail: spacing 13",
   centered (2.5" margin on each end of the 18" rail).
3. Mark the hinge positions on both the frame's south rail and the
   bed's south wall.
4. Pre-drill 4 holes per hinge (2 per leaf), 5/64" bit.
5. Attach the wall leaf to the bed's south wall.
6. Attach the frame leaf to the frame's south rail.
7. The frame should now hinge freely.

**Verification:** frame hinges smoothly between 0° and ~35° tilt. The
⅜" hinge pin holes in both hinges are aligned (the continuous pin
passes through both).

### 2.4 Insert the continuous hinge pin

**Tools:** mallet (rubber), ⅜" drill bit (if pin is too tight)

**Process:**
1. Thread the ⅜" × 22" steel rod through both hinges, starting from
   one end.
2. Tap gently with a rubber mallet to seat the pin fully.
3. The pin should extend ~1" past the last hinge on each end.

**Verification:** pin is fully seated. Frame hinges smoothly with the pin
in place.

---

## Phase 3: Panel (Day 1, ~10 min)

### 3.1 Sizing note (important!)

The 10W panel (13.3" × 8.1") is **smaller** than the frame's interior
(16.5" × 12.5"). The panel sits inside the frame interior with margin
on all four sides:
- Long sides: 1.6" margin per side
- Short sides: 2.2" margin per side

The mid-clamps grip the panel frame at the rail positions, holding the
panel firmly. This is the inverse of the v2.1 design (where the panel
overhung the frame) — for the small 10W panel, it fits comfortably
inside the frame.

### 3.2 Lift the panel onto the frame

**Tools:** hands (10W panel is only 1.88 lb)

**Process:**
1. With the frame flat on the bed, place the 10W panel on top of the
   frame, centered.
2. The panel's aluminum frame should rest on the wood rails.

**Verification:** panel is centered, with even margin on all four sides.

### 3.3 Clamp the panel to the frame

**Tools:** drill, M8 hex driver, 1" mid-clamps

**Process:**
1. Place 2 mid-clamps per long rail (4 total), at positions ±4" from
   the panel center.
2. Tighten the M8 bolts to clamp the panel frame to the wood rails.
3. Torque to ~3 Nm (snug, not crushing — the small panel frame is
   fragile).

**Verification:** panel is firmly attached. Try to wiggle it — should
not move.

### 3.4 Install the kickstand TOP mount bracket

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" wood screws

**Process:**
1. Cut a 3" length of 1x2 (offcut from any 1x2 scrap).
2. Position the bracket on the **underside** of the panel, **2 inches
   north of the south edge** of the panel.
3. The bracket should be flush with the panel's south frame edge (in z
   direction), and sit just below the panel's underside (panel underside
   is at y=4.75, bracket top is at y=4.75, bracket bottom is at y=4.0).
4. **Attach the bracket to the panel's aluminum frame**, not the bed.
   The bracket moves WITH the panel as the panel tilts.
5. Pre-drill 2 holes through the bracket's top face into the panel
   frame's channel.
6. Drive #6 × 1.5" wood screws.

**Verification:** the bracket hangs from the panel's underside, 2"
north of the south edge. The bracket moves up/down as you manually
tilt the panel.

---

## Phase 4: Kickstand Actuator Mount (Day 1, ~20 min)

### 4.1 Mount the bottom block on the bed's south wall

**Tools:** drill, ⅛" pilot bit, #6 × 1.5" wood screws

**Process:**
1. Cut a 3" length of 1x2 (offcut from any 1x2 scrap).
2. Mount the block on the **outer face** of the bed's south wall, at
   the **bottom** (resting on the ground or on the skid).
3. Position: y=0 to 0.75 (ground to top of skid), z=+7 to +7.75
   (outer face of south wall + 1x2 extending out), x=-1.5 to +1.5
   (centered along bed length).
4. Pre-drill 2 holes and drive #6 × 1.5" screws through the block into
   the bed's south wall.

**Verification:** block is firmly attached to the bed's south wall, low.

### 4.2 Insert the bottom pin

**Tools:** ⅜" clevis pin, rubber mallet

**Process:**
1. The bottom pin is a ⅜" × 3.5" steel pin that goes through the
   bottom block, perpendicular to the actuator's axis (i.e., along the
   X axis, parallel to the bed length).
2. Drill a ⅜" hole through the block (centered, 0.375" above the
   block's bottom and 0.75" outside the wall's outer face).
3. Insert the pin through the hole. The pin should extend ~0.25" past
   each side of the block.

**Verification:** pin is in place, sticking out both sides of the block.

### 4.3 Mount the kickstand actuator between the pins

**Tools:** ⅜" clevis pin + cotter pin, rubber mallet

**Process:**
1. The 100mm (3.94") stroke 12V 70N (15.7 lbf) linear actuator has a
   ⅜" clevis pin hole on each end (body side and rod side).
2. Pin the body-side clevis to the **bottom pin** (on the bed's south
   wall, low position).
3. Pin the rod-side clevis to the **top pin** (on the panel's underside
   bracket).
4. Use cotter pins to keep the clevis pins from sliding out.

**Geometry check:** at 0° panel tilt, the actuator is at its **collapsed**
length (~5" between pin centers). When the panel tilts up, the top
pin moves up and inward, and the actuator **extends** by ~0.7" to
reach the 35° tilt position.

**Verification:** actuator is pinned at both ends. Manually extend and
retract the rod — the panel should tilt up and down. Test the range:
- At fully retracted rod, panel should be flat (0°)
- At fully extended rod, panel should be at ~35° tilt

If the panel binds before reaching 35°, the actuator's top bracket
may need to be repositioned. If the actuator doesn't have enough stroke,
you've hit the geometry limit.

---

## Phase 5: Sensors and Wiring (Day 1, ~45 min)

### 5.1 Install the IMU on the frame

Follow the same principle as the full-size build (see
`docs/sensor_placement.md` § 1): mount the BMI160 breakout on the
underside of the frame's north rail, centered, with the X axis along
the bed's long axis.

**Tools:** drill, #4 wood screws, foam adhesive pad

### 5.2 Install the soil sensors

If using the bed for plants:
- DS18B20: 3" deep in soil, 6" from south wall
- Soil moisture: 2" deep in soil, 9" from south wall

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

## Phase 6: Battery and First Power-On (Day 1, ~20 min)

### 6.1 Connect the battery

**Tools:** multimeter, 3A fuse

For the mini (small 10W panel), use a 3A fuse (the actuator stall
current is well below this).

**Process:**
1. Place the 12V 7Ah LiFePO4 battery next to the bed.
2. Connect the battery negative to the breadboard's ground bus.
3. Connect the battery positive through a 3A fuse, then to the 12V
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

### 6.4 Configure max tilt

The firmware should be configured to cap tilt at **35°** (the
kickstand's mechanical limit). Set this in the ESPHome `globals`:
```yaml
globals:
  - id: max_tilt_deg
    type: float
    initial_value: '35.0'
```

### 6.5 Test each sensor

For each sensor, verify it's reading sensible values (see
`docs/test_checklist.md` Phase A for the full list).

---

## Phase 7: Solar Panel and MPPT (Day 1-2, ~20 min)

### 7.1 Connect the solar panel

**Tools:** MC4 crimper, wire stripper

**Process:**
1. The 10W panel has MC4 connectors on the back. Use MC4-to-wire
   adapters (or crimp your own).
2. Run the panel wires (positive + negative) from the panel to the
   breadboard.
3. Connect the panel input to the DPS5005 input.
4. Connect the DPS5005 output to the 12V battery (through a 3A fuse).

### 7.2 Test the MPPT

**Process:**
1. With the panel in sun, the DPS5005 should output ~14.4V to the
   battery.
2. Verify the ESP32 can read and adjust the DPS5005 setpoint via
   UART.
3. The battery voltage should rise slowly during the day.
4. Expected power: 8-9W peak at noon in full sun (after 15% derate).

---

## Phase 8: Soil and Planting (Day 2, ~10 min)

### 8.1 Fill the bed with soil

**Process:**
1. Fill the bed with 4" of soil (interior 16.5" × 12.5" × 4" = 0.48
   cu ft, ~3.5 gallons).
2. Use a potting mix (not native soil — too heavy for a small planter).

### 8.2 Plant something

**Process:**
1. Plant 1 small herb (basil, parsley) or a small flower.
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
- Actuator travel (does the kickstand reach 0° and 35°?)

### 9.2 What to learn from the mini

After a week, you'll know:
- Whether the kickstand geometry is right (does the panel bind?)
- Whether the 100mm actuator has enough travel (does it reach 35°?)
- Whether the IMU is accurate enough (or needs filtering)
- Whether the MPPT loop converges (or oscillates)
- Whether the state machine behaves as expected
- Whether the 10W panel produces expected power (~8-9W peak)
- Whether the DPS5005 charges the 7Ah battery correctly
- Whether the system runs unattended for a week without issues

If the mini works for a week, the full-size build will work too.
Apply any tuning you discovered (Kp, Ki, deadband, target_current)
to the full-size firmware.

---

## Phase 10: Watering System (solenoid on tap) (Day 2, ~45 min)

The mini v2.4 is a **smart planter**: it reads soil moisture + temps,
decides when to water, and energizes a 12V solenoid to drip-feed the
bed from your house's cold water tap. No pump, no reservoir, no
refilling. The full design spec is in `docs/watering.md`.

### 10.1 Tee into the cold water supply

**Tools:** adjustable wrench, tube cutter (or hacksaw), Teflon tape

**Process:**
1. Pick your tie-in point. The easiest options are:
   - **Outdoor hose bib** (e.g. on a patio wall): screw a 1/4" barb
     adapter directly into the faucet spout
   - **Under-sink cold water line**: cut the 3/8" or 1/2" copper
     pipe, install a 1/4" tee, restore flow
2. **Shut off the water first.** Open the closest faucet to drain
   residual pressure.
3. Cut the pipe (or unscrew the hose bib spout if going that route).
4. Wrap the tee threads with 2-3 layers of Teflon tape, install the
   tee, hand-tighten, then snug with the wrench (don't over-torque
   on plastic fittings).
5. Restore water pressure and check for leaks. Wait 5 minutes, check
   again.
6. Attach a 1/4" barb to the tee's 1/4" outlet.

**Verification:** no leaks at the tee after 5 min under pressure.

### 10.2 Run the supply line to the bed

**Tools:** scissors, 1/4" tubing cutter (or sharp knife)

**Process:**
1. Cut a length of 1/4" vinyl tubing (typically 5-20 ft depending on
   the run from tee to bed).
2. Push one end onto the tee's 1/4" barb.
3. Route the tubing from the tee to the bed (along the wall, across
   the floor, up to the workbench level). Use zip ties every 2-3 ft
   to keep it tidy.
4. (Optional) Install a 5-30 PSI pressure regulator in the line, set
   to ~15 PSI for the drip emitter. Not strictly required if your
   emitter is rated for full house pressure (40-80 PSI), but it gives
   you a more consistent flow rate.
5. Leave the other end of the supply line at the bed, ready to
   connect to the solenoid inlet.

**Verification:** briefly open the upstream valve (or unscrew the
supply tubing from where the solenoid will go) and confirm water
flows. Reconnect and leave the system pressurized but the solenoid
closed.

### 10.3 Mount the solenoid

**Tools:** screwdriver, drill, zip ties (or screws)

**Process:**
1. Mount the 12V DC normally-closed solenoid valve on the bed's east
   short wall, at ~6" height (above any potential splash zone).
   Zip-tie it to the bed's frame, or screw it to a small block of
   1x2 first and then screw the block to the bed wall.
2. The solenoid has a flow direction arrow — make sure INLET faces
   the supply tubing, OUTLET faces the drip line.
3. Connect the supply tubing to the solenoid INLET.
4. Cut ~3-4 ft of 1/4" tubing, connect to the solenoid OUTLET, run
   it to the bed's soil surface.
5. Attach a pressure-compensating drip emitter (2 GPH) to the other
   end, insert the emitter 1" deep into the soil near the plant.

**Verification:** with the solenoid DE-energized (no relay trigger),
no water should flow (NC = normally closed). With the relay on
manually, water should drip from the emitter at ~2 mL/sec.

### 10.4 Wire the relay and solenoid

**Tools:** wire stripper, small screwdriver (for relay terminals)

**Process:**
1. Mount the 1-channel relay module on the bed's east short wall,
   near the breadboard.
2. Connect:
   - **Battery 12V+** → relay COM terminal
   - **Relay NO (normally open)** → solenoid + (red wire)
   - **Solenoid - (black wire)** → battery 12V- (GND bus)
   - **Relay VCC** → ESP32 5V (or 3.3V, depending on relay module)
   - **Relay GND** → ESP32 GND
   - **Relay IN** → ESP32 GPIO 5
3. Test: in Home Assistant, toggle `switch.watering_solenoid` ON
   for 10 seconds. Solenoid should click open, water should flow,
   then auto-stop at the 30-second watchdog.

**Important:** if the solenoid wires are reversed, no harm done
(it's a DC coil, not polarized), but the flow direction arrow on
the body MUST be correct — reversed flow will leak through the
diaphragm when closed.

### 10.5 Install the temperature + soil moisture sensors

**Tools:** wire stripper, small screwdriver, thermal tape (or zip ties)

**Process (DS18B20 sensors, all on the same 1-Wire bus on GPIO 10):**
1. **Panel temp:** attach a DS18B20 to the back of the panel with
   thermal tape. Route the wire along the panel edge to the bed's
   hinge area, then to the breadboard.
2. **Soil temp:** bury a DS18B20 2" deep in the soil (next to the
   soil moisture sensor).
3. **Battery temp:** tape a DS18B20 to the side of the battery with
   Kapton tape (handles the heat).
4. All 3 sensors share VCC (3.3V), GND, and the data line (GPIO 10)
   with a single 4.7kΩ pullup resistor.
5. **Soil moisture:** Insert the Stemedu V1.2 capacitive sensor 2"
   deep into the bed soil, near the center. Connect: VCC → 3.3V,
   GND → GND, AOUT → ESP32 GPIO 4 (ADC).

**Verification:** in Home Assistant, verify all 4 sensors show
reasonable values (panel ~20-40°C, soil ~15-30°C, battery ~15-30°C,
moisture 30-60%).

### 10.6 Verify energy + SOC + POA monitoring

**Process:**
1. The INA219 (panel V/I), DPS5005 (battery V), and BMI160 (tilt)
   are already wired from Phase 5. Verify these entities in HA:
   - `sensor.panel_voltage_v` (should read ~17-21V in sun)
   - `sensor.panel_current_a` (should read 0-0.58A in sun)
   - `sensor.panel_power_w` (V × I, should peak ~8-10W in full sun)
   - `sensor.battery_v` (should read ~12-13.6V)
   - `sensor.battery_soc_pct` (should follow the LiFePO4 curve)
   - `sensor.current_tilt_deg` (should match panel angle)
   - `sensor.poa_irradiance_w_m2` (should peak ~900-1000 W/m²
     at solar noon on a clear day)
   - `sensor.panel_efficiency_pct` (should be 12-18% on a good day)
   - `sensor.energy_today_kwh` (should accumulate ~30-50 Wh/day
     in good sun, = 0.03-0.05 kWh/day)
   - `sensor.energy_total_kwh` (lifetime counter)
2. If `poa_irradiance_w_m2` reads 0 or wildly off, check the
   latitude/longitude in the firmware config (should be 33.45,
   -112.07 for Phoenix) and the time sync (NTP or manual).
3. If `panel_efficiency_pct` reads >20%, the panel area calculation
   is wrong — double check `panel_L_in × panel_W_in` in
   `wattplot_params.py`.

### 10.7 Test the watering automation

**Process:**
1. In Home Assistant, verify these entities exist:
   - `sensor.soil_moisture_pct`
   - `sensor.panel_temp_c` / `sensor.soil_temp_c` / `sensor.battery_temp_c`
   - `sensor.battery_v` / `sensor.battery_soc_pct`
   - `sensor.poa_irradiance_w_m2`
   - `sensor.energy_today_kwh`
   - `switch.watering_solenoid` (manual toggle)
   - `switch.watering_automation` (auto mode)
2. Force a watering event: in HA, set `sensor.soil_moisture_pct` to
   25 (below the 30% threshold), wait 15 seconds. The solenoid
   should click open for 50 seconds (~100 mL water).
3. Verify `sensor.water_ml_today` increments by ~100 mL.
4. Verify `sensor.watering_events_today` increments by 1.
5. Test safety blocks:
   - Set `sensor.panel_temp_c` to 50°C → watering is blocked
   - Set `sensor.battery_v` to 11.0V → watering is blocked
   - Set `sensor.battery_soc_pct` to 15 → watering is blocked
   - At night (`panel_power_w` < 0.5W) → watering is blocked

---

## Final build checklist

- [ ] Bed is level, square, and full of soil
- [ ] Frame hinges smoothly from 0° to ~35° tilt
- [ ] Hinge pin is fully seated
- [ ] Panel is firmly clamped to the frame (4 mid-clamps)
- [ ] Top kickstand bracket is mounted on panel's underside, 2" north of south edge
- [ ] Bottom kickstand block is mounted on bed's south wall, low position
- [ ] Kickstand actuator is pinned at both ends
- [ ] Panel reaches 0° when actuator is fully retracted
- [ ] Panel reaches ~35° when actuator is fully extended
- [ ] IMU is reading tilt correctly
- [ ] Battery is connected and charging via MPPT
- [ ] Solar panel is producing 8-9W peak in full sun
- [ ] ESP32 is online in Home Assistant
- [ ] State machine transitions are working
- [ ] MPPT is converging
- [ ] Firmware has `max_tilt_deg = 35.0` configured
- [ ] **Solenoid is mounted, tee is in the cold water line, drip emitter is in soil**
- [ ] **Solenoid wiring through relay is correct (test in HA, click on/off)**
- [ ] **3 DS18B20 sensors are reading (panel, soil, battery)**
- [ ] **Soil moisture sensor is reading 30-60%**
- [ ] **INA219 reads panel V×I; panel_power_w peaks at 8-10W in full sun**
- [ ] **battery_soc_pct follows the LiFePO4 curve**
- [ ] **poa_irradiance_w_m2 peaks at ~900-1000 W/m² at solar noon**
- [ ] **panel_efficiency_pct is 12-18%**
- [ ] **energy_today_kwh accumulates ~0.03-0.05 kWh/day**
- [ ] **Auto-watering fires when soil drops below 30%**
- [ ] **Safety blocks work (high temp, low battery, low SOC, nighttime)**

**Mini v2.4 complete. A real smart planter with full energy telemetry.
Apply learnings to the full-size build.**
