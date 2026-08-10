# Wattplot Mini v2.4 — Physical Build Guide

> **This guide covers the physical build only — Phases 1–4 below
> (bed, frame, panel, kickstand).** The Mini's *electronics* moved on
> with the v3.2 firmware (ESP32-C3 → ESP32-S3, 5V relay → DRV8871
> H-bridge, GPIO retuned). The electronics steps that used to live in
> this file are now in the canonical references listed at the end.
>
> **Why the split:** the physical assembly hasn't changed in three
> revs; the wiring has. Keeping them in one file meant every firmware
> bump had to also update this build guide. Easier to keep the wood
> separate from the wires.

Benchtop design-validation prototype. **18"×14" bed, ECO-WORTHY
10W panel, 100mm kickstand linear actuator**.

**Tilt range:** 0–35° (limited by the kickstand geometry; matches the
power-optimal range per the Phoenix sun sim).

**Build time:** ~3–4 hours (physical only — add ~2 hours for
electronics per the canonical references at the end).

**Build cost (physical only):** ~$42 (lumber + hinges + clamps +
fasteners). Add ~$151 for the electronics — see
[`booth/PARTS_STATUS.md`](../booth/PARTS_STATUS.md) for the full,
up-to-date order list.

**Lumber (all PT DF, all from 8 ft stock):**

- 1 × 1×4×8 ft (bed walls: 2 long + 2 short, all from 1 board)
- 2 × 1×2×8 ft (1 for frame rails, 1 for skids + kickstand mount blocks)
- 1 × 2×4×8 ft (diagonal brace offcut)

**Fasteners:** 16 × #6 × 1.5" wood screws, 8 × #6 × 1" screws,
4 × M8 × 1.5" stainless bolts, 8 × 5/64" × 1" hinge screws,
2 × ⅜" clevis pins. (Full list in [`booth/PARTS_STATUS.md`](../booth/PARTS_STATUS.md).)

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

## Electronics (v3.2 firmware)

The physical build is done. For the controller, sensors, and wiring,
use these canonical references — the wiring chapter in this doc used
to live here, but the firmware has moved on (ESP32-C3 → ESP32-S3, 5V
relay → DRV8871 H-bridge, GPIO retuned) and the wiring has to move
with it.

| Reference | What's in it |
|---|---|
| [`docs/schematic.html`](schematic.html) | Rev B (2026-08-03). 14 sections, 5 V/3.3 V power tree, dual H-bridge. The single source of truth for the controller schematic. |
| [`docs/pinmap.html`](pinmap.html) | Visual diff between the schematic and the firmware. Every wire, every pin, on the ESP32-S3-DevKitC-1. |
| [`docs/wiring.md`](wiring.md) | Cable lengths, AWG, JST pinouts, pre-power checklist. |
| [`docs/sensor_placement.md`](sensor_placement.md) | DS18B20 + capacitive soil + BMI160 placement. Full-size build's guidance applies to the Mini too. |
| [`firmware/README.md`](../firmware/README.md) | Flash + log-stream + MQTT quick-start. The Mini and the full-size use the same firmware. |
| [`firmware/wattplot.yaml`](../firmware/wattplot.yaml) | The YAML itself. The v3.2 revision history is in the header comment. |
| [`booth/PARTS_STATUS.md`](../booth/PARTS_STATUS.md) | The current parts list (W3 2026-08-09), with status of each item. The Mini's electronics list is the source of truth here, not in this build guide. |

### Mini-specific gotchas (read these)

- **Solenoid driver:** the v3.2 firmware uses a **DRV8871 H-bridge**
  (not the 5V relay in the original v2.4 design). The Mini bench
  build has both for transition; the PCB v3 will only have the
  DRV8871.
- **Pin map:** the Mini uses the same ESP32-S3-DevKitC-1 as the
  full-size, so the GPIO map is identical. The Mini's actuator is
  just lighter (70 N vs 330 lbf) — the same control law, the same
  current limit constants.
- **Calibration:** the IMU offset is different (the Mini's panel is
  smaller and tilts less). Re-run the IMU calibration on the Mini's
  panel after mounting; don't carry over the full-size's values.
- **Pre-power checklist:** the [pre-power checklist](pre_build_checklist.md)
  applies. Verify no shorts before applying 12 V.
