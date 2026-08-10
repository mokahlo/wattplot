# Mini v2.4, Parts Status & Build Tracker

**Target:** Working Mini v2.4, fully assembled, on the booth table.
Faire: **Sept 25–27, 2026** (47 days from 2026-08-09).

> **Status as of 2026-08-09 (W3 of 9):** Mini v2.4 build is on the
> bench. Calibrating IMU and running closed-loop tilt tests. Original
> electronics list (below) is kept as a record of what shipped. **The
> controller row was updated to ESP32-S3 in W3** — the v3.2 ESPHome
> firmware dropped C3 support, so anything you build fresh needs the
> S3 DevKitC-1. PCB v3 (a custom carrier that replaces the Sunapex
> + breadboard) is in development, targeting post-faire. The Mini
> stays on the discrete-component path because it's the booth demo
> and it has to work *now*.

## On hand / confirmed ordered (per `docs/build_guide_mini.md`)

- [x] 12V 7Ah LiFePO4 battery (with BMS) — installed
- [x] 100mm (3.94") stroke 12V linear actuator, 70N — installed
- [x] ESP32-S3 DevKitC-1 (N16R8) — installed (sub for the original C3)
- [x] ECO-WORTHY 10W 12V solar panel, 13.3" × 8.1" — installed

## Order this week, electronics (Amazon + Mouser, ~3-5 day shipping)

> **As of 2026-08-09:** all items below were received in W1–W2 and
> are installed in the bench build, with the following substitutions
> relative to the original order:
>
> - **ESP32-S3 DevKitC-1** in place of the planned ESP32-C3 (W3
>   sub — required by the v3.2 ESPHome firmware)
> - **DRV8871 H-bridge carrier** in place of the 5V relay (W3
>   sub — required for direction-controlled actuator; relay was
>   single-direction and the v3 firmware uses both polarities
>   for current-based homing)

| Qty | Item | Source | ~Cost | Why | Status |
|---|---|---|---|---|---|
| 1 | **Sunapex 10A MPPT** charge controller, IP67, LiFePO4-aware | Amazon | $25 | Replaces the CN3791 (incompatible with 12V LiFePO4) | installed |
| 1 | BMI160 IMU breakout | Mouser | $2 | Tilt feedback (closed loop) | installed |
| 1 | INA219 current sensor breakout | Mouser | $2 | Battery / panel current | installed |
| 3 | DS18B20 waterproof temperature sensor (5-pack) | Amazon | $11 | Panel, soil, battery temp | installed |
| 1 | Capacitive soil moisture sensor V1.2 (5-pack) | Amazon | $9 | Soil water content | installed |
| 1 | Breadboard or perfboard | Amazon | $5 | Wiring | installed (W3 → replaced by PCB v3 prototype once available) |
| 1 | USB-C cable | Amazon | $3 | ESP32 programming | installed |
| 1 | 12V DC normally-closed solenoid valve, 1/4" barb | Amazon | $10 | Watering system | installed |
| 1 | ~~1-channel 5V relay module~~ → **DRV8871 H-bridge carrier** | Amazon | $5 | ESP32 → solenoid (bidirectional for current homing) | installed (W3 sub) |
| 1 | Pressure regulator 5-30 PSI, 1/4" NPT | Amazon | $10 | Safe drip pressure | installed |
| 10 ft | 1/4" vinyl tubing (food-safe) | Amazon | $8 | Drip line | installed |
| 1 | Pressure-compensating drip emitter, 2 GPH | Amazon | $5 | Dripper | installed |
| 2 | 1/4" tubing barb fittings | Amazon | $3 | Solenoid connections | installed |
| 1 | 1/4" cold-water tee, brass | Home Depot | $3 | Tap-line tee | installed |
| 4 | Zip ties | Home Depot | $2 | Tubing | installed |
| ~30 | Jumper wires (M-F, M-M, F-F) | Amazon | $3 | Prototyping | installed |
| 1 | 1.5" butt hinges w/ ⅜" pin (2-pack) | Home Depot | $6 | Frame to bed hinge | installed |
| 1 | ⅜" × 22" steel rod (continuous hinge pin) | Home Depot | $3 | Hinge pin | installed |
| 4 | 1" aluminum mid-clamps for 18mm panel channel | Amazon | $8 | Panel mounting | installed |
| 2 | ⅜" clevis pins + cotter pins | Hardware | $2 | Actuator mount | installed |

**Electronics + watering + hardware subtotal: ~$124**

## Order this week, lumber (Home Depot, ~1-2 day pickup)

| Qty | Size | Use |
|---|---|---|
| 1 | 1x4x8 ft PT DF | Bed walls (2 long + 2 short) |
| 2 | 1x2x8 ft PT DF | Frame rails (1 board) + skids + kickstand blocks (1 board) |
| 1 | 2x4x8 ft PT DF | Diagonal brace (cut a 21" piece) |

**Lumber subtotal: ~$19**

## Order this week, fasteners (Home Depot, ~$8)

- 16 × #6 × 1.5" wood screws (HDG), bed + frame
- 8 × #6 × 1" wood screws, diagonal brace + kickstand blocks
- 4 × M8 × 1.5" stainless bolts + EPDM washers, mid-clamps
- 8 × 5/64" × 1" wood screws, hinge leaves (often come with hinges)

## Grand total to order this week

**~$151** (plus tax, plus shipping)

## Order timing (historical — for the W1 order)

| Today (Jul 23) | Action | Actual |
|---|---|---|
| Tonight | Walk the list above. Cross off what you already have. | done |
| Tomorrow | Place the Amazon + Mouser orders. | done (W1) |
| Tomorrow | Drive to Home Depot for lumber + brass tee + hinges. | done (W1) |
| Sat/Sun | All parts in hand. Begin build. | done (W2 weekend) |
| By end of W2 (Aug 5) | Mini v2.4 assembled, on the table, talking to the laptop. | done (Aug 4) |

## Current phase (W3, 2026-08-09)

- **Build:** assembled, on the bench, talking to the laptop.
- **Tuning:** calibrating IMU, verifying closed-loop tilt against
  the 0–35° range, validating the soil-moisture dry/wet trigger
  thresholds against `docs/test_checklist.md` Phase A.
- **Risk:** the bench MPPT (Sunapex) is a known-good part; the
  DRV8871 swap (W3) needs a current-limit sanity check before
  the 70N actuator is connected for the first time in-circuit.
- **Booth collateral:** cards and poster (W4). One-pager, FAQ,
  demo script in `docs/` are up to date.

## Build sequence (full guide in `docs/build_guide_mini.md`)

1. **Phase 1: Bed**, 1 hour. Cut half-laps, assemble, attach skids.
2. **Phase 2: Frame**, 1 hour. Rectangle + diagonal brace + hinges.
3. **Phase 3: Panel**, 10 min. Mid-clamps.
4. **Phase 4: Kickstand actuator mount**, 20 min. Bottom + top blocks + clevis pins.
5. **Phase 5: Wire the panel**, 30 min. MC4 → Sunapex → battery. Verify MPPT lights up.
6. **Phase 6: Wire the controller**, 1.5 hours. ESP32 + IMU + INA219 + DS18B20 + soil sensor + relay.
7. **Phase 7: Flash ESPHome**, 30 min. Use `firmware/wattplot.yaml` (see notes below).
8. **Phase 8: Watering system**, 1 hour. Tap → tee → regulator → solenoid → drip emitter.
9. **Phase 9: Fill + plant**, 30 min. Potting mix + 4 seedlings.
10. **Phase 10: Calibrate + test**, 1 hour. Tilt range, current limits, soil dry/wet trigger.

**Total: ~7-8 hours, one weekend.**

## Firmware note

The Mini uses the same `firmware/wattplot.yaml` v3.2 as the full-size
(ESP32-S3-DevKitC-1, GPIO6/7/10/12/16, DRV8871 for the actuator +
solenoid). Verify the pin map against `docs/pinmap.html` before
wiring — the v2.x C3-era pinouts are stale and won't compile. The
Mini's actuator is much lighter (70N vs 330 lbf full-size) and the
IMU offset will be different. The `control_law.md` constants
(I_safe, deadband) need to be re-tuned for the smaller actuator.

A separate `firmware/wattplot_mini.yaml` is on the to-do list for
after the booth if we have time.

## What NOT to do

- **Do not 3D-print any of the brackets.** They are designed to be
  1×2 wood offcuts. The build guide says so. The build cost is $19 of
  lumber, not $80 of PETG.
- **Do not use a different MPPT.** The Sunapex is the spec. Other MPPTs
  in this size class either don't speak LiFePO4 or are PWM (not MPPT).
  Read `bom_mini.md` §"Critical note" before substituting.
- **Do not skip the ½-lap corners on the bed.** Butt joints will
  rack. The 1.5" wide × 0.375" deep notch is the whole reason the
  bed is square.

## Risk register

| Risk | Mitigation |
|---|---|
| Sunapex out of stock | Solperk HC-SM10A is the documented backup (~$35). Same form factor. |
| ECO-WORTHY 10W panel is backordered | Any 10-20W 12V panel works. The build is sized for 13.3"×8.1"; bigger is fine, just changes the mid-clamp count. |
| Lumber yard only has cedar | Cedar is fine for a raised bed, same dimensions, costs ~30% more. Don't use untreated pine. |
| Solenoid leaks on first run | Use a normally-closed (NC) valve, it fails safe (off) when de-energized. |
| ESP32 won't program | Try a different USB-C cable (many are charge-only). Check the driver. Try ESPHome Web Flasher if `esphome run` won't talk. |
| Tilt range is too small | The 100mm actuator gives 0-35°. The full-size gives 0-90°. 0-35° is enough for the demo. |
