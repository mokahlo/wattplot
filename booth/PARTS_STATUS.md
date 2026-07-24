# Mini v2.4, Parts Status & Order-Now List

**Target:** Working Mini v2.4, fully assembled, on the booth table by
**Aug 5** (week 2). The faire is Sept 25, 64 days from project start,
and the build is the critical path.

> **Status as of 2026-07-23:** Some parts ordered, more to go. Items
> below are split into "on hand / confirmed ordered" and "order this
> week." Confirm against your own records before ordering.

## On hand / confirmed ordered (per `docs/build_guide_mini.md`)

These were the original order list. **Verify you actually have them.**

- [ ] 12V 7Ah LiFePO4 battery (with BMS)
- [ ] 100mm (3.94") stroke 12V linear actuator, 70N
- [ ] ESP32-C3 PRO Mini dev board (or any ESP32)
- [ ] ECO-WORTHY 10W 12V solar panel, 13.3" × 8.1"

## Order this week, electronics (Amazon + Mouser, ~3-5 day shipping)

| Qty | Item | Source | ~Cost | Why |
|---|---|---|---|---|
| 1 | **Sunapex 10A MPPT** charge controller, IP67, LiFePO4-aware | Amazon | $25 | Replaces the CN3791 (incompatible with 12V LiFePO4) |
| 1 | BMI160 IMU breakout | Mouser | $2 | Tilt feedback (closed loop) |
| 1 | INA219 current sensor breakout | Mouser | $2 | Battery / panel current |
| 3 | DS18B20 waterproof temperature sensor (5-pack) | Amazon | $11 | Panel, soil, battery temp |
| 1 | Capacitive soil moisture sensor V1.2 (5-pack) | Amazon | $9 | Soil water content |
| 1 | Breadboard or perfboard | Amazon | $5 | Wiring |
| 1 | USB-C cable | Amazon | $3 | ESP32 programming |
| 1 | 12V DC normally-closed solenoid valve, 1/4" barb | Amazon | $10 | Watering system |
| 1 | 1-channel 5V relay module, low-level trigger | Amazon | $4 | ESP32 → solenoid |
| 1 | Pressure regulator 5-30 PSI, 1/4" NPT | Amazon | $10 | Safe drip pressure |
| 10 ft | 1/4" vinyl tubing (food-safe) | Amazon | $8 | Drip line |
| 1 | Pressure-compensating drip emitter, 2 GPH | Amazon | $5 | Dripper |
| 2 | 1/4" tubing barb fittings | Amazon | $3 | Solenoid connections |
| 1 | 1/4" cold-water tee, brass | Home Depot | $3 | Tap-line tee |
| 4 | Zip ties | Home Depot | $2 | Tubing |
| ~30 | Jumper wires (M-F, M-M, F-F) | Amazon | $3 | Prototyping |
| 1 | 1.5" butt hinges w/ ⅜" pin (2-pack) | Home Depot | $6 | Frame to bed hinge |
| 1 | ⅜" × 22" steel rod (continuous hinge pin) | Home Depot | $3 | Hinge pin |
| 4 | 1" aluminum mid-clamps for 18mm panel channel | Amazon | $8 | Panel mounting |
| 2 | ⅜" clevis pins + cotter pins | Hardware | $2 | Actuator mount |

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

## Order timing

| Today (Jul 23) | Action |
|---|---|
| Tonight | Walk the list above. Cross off what you already have. |
| Tomorrow | Place the Amazon + Mouser orders. |
| Tomorrow | Drive to Home Depot for lumber + brass tee + hinges. |
| Sat/Sun | All parts in hand. Begin build. |
| By end of W2 (Aug 5) | Mini v2.4 assembled, on the table, talking to the laptop. |

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

The Mini uses the same `firmware/wattplot.yaml` as the full-size, but
verify the pin map. The Mini's actuator is much lighter (70N vs 330 lbf
full-size) and the IMU offset will be different. The `control_law.md`
constants (I_safe, deadband) need to be re-tuned.

A separate `firmware/wattplot_mini.yaml` is on the to-do list for after
the booth if we have time.

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
