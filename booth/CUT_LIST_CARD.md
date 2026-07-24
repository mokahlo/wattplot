# Wattplot Mini, Cut List Card

> A 4×6 take-home card. Source is this markdown; render to a 4×6
> PDF for printing (Vistaprint, Moo, or your local print shop).
> Stack 500 of these for the booth.

---

# Wattplot Mini

**18" × 14" planter, 0–35° tilt, ~$193 in parts, ~3-4 hr build.**

github.com/mokahlo/wattplot

## Cut list (all 90° square cuts, no miter)

| Qty | Material | Length | Use |
|---|---|---|---|
| 2 | 1×4 PT DF | 18"     | Long bed walls |
| 2 | 1×4 PT DF | 12.5"   | Short bed walls |
| 2 | 1×2 PT DF | 18"     | Long frame rails |
| 2 | 1×2 PT DF | 12.5"   | Cross frame rails |
| 2 | 1×2 PT DF | 18"     | Skids |
| 1 | 2×4 PT DF | 21"     | Diagonal brace |
| 1 | 1×2 PT DF | 3"      | Kickstand bottom block |
| 1 | 1×2 PT DF | 3"      | Kickstand top bracket |

**From 1×4×8 ft (1 board):** 4 walls, 60" waste per board.
**From 1×2×8 ft (2 boards):** 4 rails + 2 skids, 60" waste per.
**From 2×4×8 ft (1 board, offcut):** 1 brace, 75" waste.

## Parts list

- 2 × 1.5" butt hinges (⅜" pin)
- 1 × ⅜" × 22" steel rod
- 4 × 1" mid-clamps (18mm channel)
- 1 × 100mm 12V linear actuator
- 1 × Sunapex 10A MPPT
- 1 × ECO-WORTHY 10W panel
- 1 × 12V 7Ah LiFePO4 battery
- 1 × ESP32-C3 dev board
- 1 × BMI160 IMU
- 1 × INA219
- 3 × DS18B20
- 1 × capacitive soil sensor
- 1 × 12V solenoid (NC) + relay
- 16 × #6 × 1.5" wood screws
-  8 × #6 × 1" wood screws
-  4 × M8 × 1.5" bolts
-  2 × ⅜" clevis pins

## Build order

1. Cut half-laps (1.5" × 0.375"), bed corners
2. Assemble bed box + skids
3. Frame rectangle + diagonal brace
4. Hinges on south wall + bed
5. Insert continuous hinge pin
6. Mount panel (4 mid-clamps)
7. Kickstand mounts + actuator
8. Wire panel → MPPT → battery
9. Wire controller (ESP32, IMU, INA219, sensors)
10. Flash ESPHome (`firmware/wattplot.yaml`)
11. Calibrate IMU
12. Add watering system
13. Fill + plant

**Total: ~3-4 hours. ~$193.**

---

*MIT-licensed, code-first, build-photos at github.com/mokahlo/wattplot/renders/build_photos*

**Mare Island · Sept 25-27 2026**
