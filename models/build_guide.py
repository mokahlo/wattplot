"""
Build guide generator — produces a phase-by-phase build markdown
from the current panel + bed + cut list + hardware spec.

The output mirrors the structure of the static `docs/build_guide.md` but
with all measurements filled in from the params. So if you swap a
panel preset (or call bring_your_own_panel.py with custom specs), the
guide adjusts automatically.

Usage:
    from models.build_guide import generate_build_guide, write_build_guide

    # After applying a panel preset:
    md = generate_build_guide(panel_name="residential_60cell")
    write_build_guide(md, "docs/build_residential_60cell.md")
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import wattplot_params as P
from models.cut_list import derive_cut_list
from models.hardware_spec import derive_hardware_spec


def _h(minutes):
    """Format minutes as '~Xh' or '~Xm'."""
    if minutes >= 60:
        h = minutes / 60.0
        return f"~{h:.1f} hr"
    return f"~{minutes} min"


def generate_build_guide(panel_name="custom", output_to_file=None):
    """Generate a build guide markdown for the current panel + bed state.

    Reads from wattplot_params (P.PANEL, P.BED), so the caller should
    have applied the desired panel preset first.

    Args:
        panel_name: a label for this build (e.g., "residential_60cell" or
                    "my_salvage_panel"). Used in the title and the output
                    filename.
        output_to_file: optional path to write the markdown. If None,
                        returns the string only.

    Returns:
        the markdown string
    """
    panel_L = P.PANEL["L_in"]
    panel_W = P.PANEL["W_in"]
    panel_thk = P.PANEL.get("thickness_in", 1.4)
    panel_mass = P.PANEL.get("mass_lb", 50)
    panel_W_current = int(P.PANEL["wattage"])  # possibly derated
    panel_W_nameplate = int(P.PANEL.get("wattage_nameplate", panel_W_current))
    panel_age = P.PANEL.get("panel_age_years", 0)
    panel_bifacial = P.PANEL.get("panel_bifacial", False)
    bed_L = P.BED["outer_L_in"]
    bed_W = P.BED["outer_W_in"]
    bed_L_ft = bed_L / 12.0
    bed_W_ft = bed_W / 12.0

    # Derive cut list and hardware spec
    cuts = derive_cut_list(bed_L_in=bed_L, bed_W_in=bed_W)
    hardware = derive_hardware_spec(
        bed_L_in=bed_L, bed_W_in=bed_W,
        panel_L_in=panel_L, panel_W_in=panel_W,
        panel_thk_in=panel_thk, panel_mass_lb=panel_mass,
        actuator_stroke_in=4.0,
    )

    # Time estimates (scale with bed dimensions)
    is_mini = bed_L < 30
    hinge_count = hardware["hinges"]["count"]
    n_clamps = hardware["mid_clamps"]["count"]
    hinge_pin_L = hardware["hinge_pin"]["length_in"]
    short_wall_L = bed_W - 1.5 - 1.5     # bed_W - 2*T (wall thickness)
    cross_rail_L = bed_W - 1.5 - 1.5    # bed_W - 2*T (rail thickness)

    time_phase1 = 90 + 10 * (bed_L_ft * bed_W_ft) / 8.0  # bed: 90 min base, scales
    time_phase2 = 45 + 5 * bed_L_ft                     # frame
    time_phase3 = 10 * hinge_count                       # hinges
    time_phase4 = 1 * n_clamps + 5                      # panel + clamps
    time_phase5 = 20                                      # actuator
    time_phase6 = 30                                      # panel wiring
    time_phase7 = 60                                      # controller wiring
    time_phase8 = 30                                      # flash
    time_phase9 = 60                                      # calibrate
    time_phase0 = 60                                      # order parts
    total_min = sum([time_phase0, time_phase1, time_phase2,
                     time_phase3, time_phase4, time_phase5,
                     time_phase6, time_phase7, time_phase8,
                     time_phase9])

    # ---- Build the markdown ----
    md = []
    md.append(f"# Wattplot Build Guide: {panel_name}")
    md.append("")
    md.append(f"Step-by-step assembly of the entire apparatus. Follow the "
              f"order below. Each step lists the **time**, **tools**, "
              f"**parts**, and **verification**.")
    md.append("")
    md.append("**Total build time:** " + _h(total_min) + " over a weekend "
              "(with lumber pre-cut).")
    md.append("")
    md.append("**Specifications for this build:**")
    md.append(f"- Panel: {panel_L}\" × {panel_W}\" × {panel_thk}\" "
              f"({panel_L/12:.2f} × {panel_W/12:.2f} ft), {panel_mass} lb")
    if panel_W_nameplate != panel_W_current:
        md.append(f"- Wattage: {panel_W_current} W "
                  f"(nameplate {panel_W_nameplate} W, "
                  f"derated after {panel_age} yr, "
                  f"{'bifacial' if panel_bifacial else 'monofacial'})")
    else:
        md.append(f"- Wattage: {panel_W_current} W "
                  f"({panel_age} yr old, "
                  f"{'bifacial' if panel_bifacial else 'monofacial'})")
    md.append(f"- Bed: {bed_L}\" × {bed_W}\" "
              f"({bed_L_ft:.2f} × {bed_W_ft:.2f} ft), 12\" deep walls, bottomless")
    md.append("")

    # ---- Phase 0: Pre-build ----
    md.append("## Phase 0: Pre-build (Day 0, " + _h(time_phase0) + ")")
    md.append("")
    md.append("### 0.1 Lumber (from the cut list)")
    md.append("")
    md.append("| Nominal | Qty | Length | Use |")
    md.append("|---|---|---|---|")
    for c in cuts["cuts"]:
        md.append(f"| {c.nominal} | {c.qty} | {c.length_in:.1f}\" "
                  f"({c.length_in/12:.2f} ft) | {c.use} |")
    md.append("")
    if cuts["boards_8ft"]:
        md.append("**Source from 8-ft stock:** " +
                  ", ".join(f"{c}× {n}" for n, c in cuts["boards_8ft"].items()))
    if cuts["boards_10ft"]:
        md.append("**Source from 10-ft stock:** " +
                  ", ".join(f"{c}× {n}" for n, c in cuts["boards_10ft"].items()))
    md.append("")
    md.append("**Tip:** many yards will cut to length for free or a small fee. "
              "Have them cut each piece on the list above. None of the cuts are "
              "mitered (90° square cut only).")
    md.append("")
    md.append("### 0.2 Hardware")
    md.append("")
    md.append(f"- {hardware['hinges']['count']} × {hardware['hinges']['spec']}")
    md.append(f"- 1 × {hardware['hinge_pin']['spec']}")
    md.append(f"- {hardware['mid_clamps']['count']} × {hardware['mid_clamps']['spec']}")
    md.append(f"- {hardware['carriage_bolts']['count']} × {hardware['carriage_bolts']['spec']}")
    md.append(f"- {hardware['lag_bolts']['count']} × {hardware['lag_bolts']['spec']}")
    md.append(f"- {hardware['deck_screws']['total']} × {hardware['deck_screws']['spec']}")
    md.append(f"- 1 × {hardware['actuator']['spec']}")
    md.append("")
    md.append("### 0.3 Panel + electrical")
    md.append("")
    if panel_age > 0:
        md.append(f"- 1 × **{panel_W_nameplate} W nameplate "
                  f"({panel_W_current} W after derate) salvage panel** (you provide)")
        md.append("  - Verify under full sun: Voc within 5% of nameplate (multimeter)")
        md.append("  - Glass intact, no cracks or delamination")
        md.append("  - Aluminum frame straight, junction box sealed")
    else:
        md.append(f"- 1 × **{panel_W_current} W new panel** (from manufacturer)")
    md.append("- 1 × MPPT charge controller (sized to your panel, see `bring_your_own_panel.py`)")
    md.append("- 1 × 12V 100Ah LiFePO4 battery (LiTime or similar)")
    md.append("- 1 × Microinverter (Enphase IQ7+ or APsystems DS3)")
    md.append("- 1 × ESP32-WROOM-32E dev board (or use the PCB from `docs/pcb_design.md`)")
    md.append("")

    # ---- Phase 1: Bed ----
    md.append(f"## Phase 1: Bed (Day 1, {_h(int(time_phase1))})")
    md.append("")
    md.append("### 1.1 Cut the wall half-lap notches")
    md.append("")
    md.append(f"Each bed wall has a 3\" wide × 0.75\" deep notch at each end.")
    md.append("")
    md.append("**Tools:** circular saw, chisel, mallet, square")
    md.append("")
    md.append("**Process:**")
    md.append("1. Mark the notch location on each wall (3\" from each end, 0.75\" deep).")
    md.append("2. Make multiple passes with the circular saw at the notch depth.")
    md.append("3. Clean out the waste with a chisel.")
    md.append("4. Test-fit two walls at a corner.")
    md.append("")
    md.append("**Verification:** the two walls meet at a 90° corner with no daylight.")
    md.append("")
    md.append("### 1.2 Assemble the bed box")
    md.append("")
    md.append("**Tools:** drill, ⅛\" pilot bit, #6 × 1.5\" wood screws, square")
    md.append("")
    md.append("**Process:**")
    md.append(f"1. Lay out the 4 walls on a flat surface. "
              f"Long walls are {bed_L:.1f}\" ({bed_L_ft:.2f} ft). "
              f"Short walls are {short_wall_L:.1f}\" ({short_wall_L/12:.2f} ft).")
    md.append("2. Bring the corners together. The half-lap notches interlock.")
    md.append("3. Pre-drill 2 holes per corner (one near the top, one near the bottom).")
    md.append("4. Drive #6 × 1.5\" wood screws through the corners.")
    md.append("")
    md.append(f"**Verification:** bed box is {bed_L:.1f}\" × {bed_W:.1f}\" outside, "
              f"square (measure diagonally, both should be the same).")
    md.append("")
    md.append("### 1.3 Attach the skids")
    md.append("")
    md.append("**Tools:** drill, ⅛\" pilot bit, #6 × 1.5\" screws")
    md.append("")
    md.append("**Process:**")
    md.append("1. Flip the bed upside down.")
    md.append(f"2. Place two 4x4×{bed_L:.1f}\" skids under the bed, aligned with the long walls.")
    md.append("3. Pre-drill and screw through the skids into the bed walls.")
    md.append("4. Use 2-3 screws per skid.")
    md.append("")
    md.append("**Verification:** skids are flush with the bed ends, square, "
              "and the whole bed sits level on the ground.")
    md.append("")

    # ---- Phase 2: Frame ----
    md.append(f"## Phase 2: Frame (Day 1, {_h(int(time_phase2))})")
    md.append("")
    md.append("### 2.1 Assemble the frame rectangle")
    md.append("")
    md.append("**Tools:** drill, ⅛\" pilot bit, #6 × 1.5\" wood screws, square")
    md.append("")
    md.append("**Process:**")
    md.append(f"1. Lay the 4 frame rails on a flat surface. Long rails are {bed_L:.1f}\" "
              f"({bed_L_ft:.2f} ft). Cross rails are {cross_rail_L:.1f}\" ({cross_rail_L/12:.2f} ft).")
    md.append("2. The cross rails fit between the long rails. Butt joints (no miter).")
    md.append("3. Pre-drill 2 holes per corner. Drive #6 × 1.5\" wood screws.")
    md.append("")
    md.append(f"**Verification:** frame is {bed_L:.1f}\" × {bed_W:.1f}\" outside, square.")
    md.append("")
    md.append("### 2.2 Add the diagonal brace")
    md.append("")
    diag_L = math.sqrt(bed_L**2 + bed_W**2)
    md.append("**Tools:** drill, ⅛\" pilot bit, #6 × 1\" screws, measuring tape")
    md.append("")
    md.append("**Process:**")
    md.append(f"1. The 2x4×{diag_L:.1f}\" diagonal brace runs corner to corner inside the frame.")
    md.append("2. Position the brace so its ends butt into the inside faces of the long rails.")
    md.append("3. Pre-drill 2 holes per end. Drive #6 × 1\" screws (4 total).")
    md.append("")
    md.append("**Verification:** brace is at the diagonal angle, both ends screwed.")
    md.append("")

    # ---- Phase 3: Hinges ----
    md.append(f"## Phase 3: Hinges (Day 1, {_h(int(time_phase3))})")
    md.append("")
    md.append("### 3.1 Install hinges on the bed's south wall")
    md.append("")
    md.append("**Tools:** drill, 5/64\" bit, hinge screws (included with hinges), tape measure")
    md.append("")
    md.append("**Process:**")
    md.append("1. Lay the frame on top of the bed, with the frame's south rail resting on the bed's south wall.")
    hinge_spacing = (bed_L - 8) / max(1, hinge_count - 1) if hinge_count > 1 else 0
    md.append(f"2. Position the {hinge_count} hinges evenly along the south rail. "
              f"Spacing: {hinge_spacing:.1f}\" center-to-center, with 4\" margin on each end.")
    md.append("3. Mark the hinge positions on both the frame's south rail and the bed's south wall.")
    md.append("4. Pre-drill 4 holes per hinge (2 per leaf), 5/64\" bit.")
    md.append("5. Attach the wall leaf to the bed's south wall.")
    md.append("6. Attach the frame leaf to the frame's south rail.")
    md.append("")
    md.append("**Verification:** frame hinges freely between 0° and ~90° tilt.")
    md.append("")
    md.append("### 3.2 Insert the continuous hinge pin")
    md.append("")
    md.append("**Tools:** mallet (rubber)")
    md.append("")
    md.append("**Process:**")
    md.append(f"1. Thread the ½\" × {hinge_pin_L:.1f}\" steel rod through all hinges, "
              "starting from one end.")
    md.append("2. Tap gently with a rubber mallet to seat the pin fully.")
    md.append("3. The pin should extend ~1\" past the last hinge on each end.")
    md.append("")
    md.append("**Verification:** pin is fully seated. Frame hinges smoothly with the pin in place.")
    md.append("")

    # ---- Phase 4: Panel ----
    md.append(f"## Phase 4: Panel (Day 1, {_h(int(time_phase4))})")
    md.append("")
    md.append("### 4.1 Place the panel on the frame")
    md.append("")
    md.append(f"**Tools:** hands (the panel weighs {panel_mass} lb).")
    md.append("")
    md.append("**Process:**")
    md.append("1. With the frame flat on the bed, place the panel on top of the frame, centered.")
    md.append("2. The panel should rest on the wood rails with even margin on all four sides.")
    md.append("")
    md.append("**Verification:** panel is centered, no overhang on the long rails.")
    md.append("")
    md.append("### 4.2 Clamp the panel to the frame")
    md.append("")
    md.append("**Tools:** drill, M8 hex driver, mid-clamps")
    md.append("")
    md.append("**Process:**")
    md.append(f"1. Place {hardware['mid_clamps']['long_rail']} mid-clamps on each long rail "
              f"({hardware['mid_clamps']['long_rail'] * 2} total, "
              f"evenly spaced along the panel frame).")
    md.append(f"2. Place {hardware['mid_clamps']['cross_rail']} mid-clamps on each cross rail.")
    md.append("3. Tighten the M8 bolts to clamp the panel frame to the wood rails.")
    md.append(f"4. Torque to ~3 Nm (snug, not crushing).")
    md.append("")
    md.append("**Verification:** panel is firmly attached. Try to wiggle it: should not move.")
    md.append("")

    # ---- Phase 5: Actuator ----
    md.append(f"## Phase 5: Actuator Mount (Day 1, {_h(time_phase5)})")
    md.append("")
    md.append("### 5.1 Mount the bottom block on the bed's north wall")
    md.append("")
    md.append("**Tools:** drill, ⅛\" pilot bit, #6 × 1.5\" wood screws")
    md.append("")
    md.append("**Process:**")
    md.append("1. Cut a 3\" length of 2x6 (offcut from any 2x6 scrap).")
    md.append("2. Mount the block on the outer face of the bed's north wall, at the bottom.")
    md.append("3. Centered along the bed length.")
    md.append("4. Pre-drill 2 holes and drive #6 × 1.5\" screws.")
    md.append("")
    md.append("### 5.2 Mount the top bracket on the panel's underside")
    md.append("")
    md.append("1. Cut a 3\" length of 2x6 (offcut).")
    md.append("2. Mount on the **underside** of the panel, 2\" north of the panel's south edge.")
    md.append("3. The bracket should sit just below the panel's underside, flush with the panel's south frame edge.")
    md.append("4. Pre-drill and drive #6 × 1.5\" wood screws through the bracket into the panel frame.")
    md.append("")
    md.append("### 5.3 Connect the actuator")
    md.append("")
    md.append("1. Use ⅜\" clevis pins to attach the actuator to both mount blocks.")
    md.append("2. Test manually: the panel should now move from 0° to ~90° (or your actuator's stroke limit).")
    md.append("")

    # ---- Phase 6: Wire panel to MPPT ----
    md.append(f"## Phase 6: Wire the panel to MPPT (Day 2, {_h(time_phase6)})")
    md.append("")
    md.append("### 6.1 MC4 connectors")
    md.append("")
    md.append("**Tools:** MC4 crimper, wire stripper, multimeter")
    md.append("")
    md.append("**Process:**")
    md.append("1. Crimp MC4 connectors on the panel's PV+ and PV- leads.")
    md.append("2. Plug into the MPPT's PV input (MC4 or SAE adapter, depending on the MPPT).")
    md.append("3. **Verify polarity**: red → +PV, black → -PV. Reverse polarity kills MPPT.")
    md.append("")
    md.append("### 6.2 MPPT to battery")
    md.append("")
    md.append("1. Connect MPPT battery output to the 12V LiFePO4 battery (via ring terminals or Anderson).")
    md.append("2. Set the MPPT's battery chemistry to LiFePO4 (MODE button on Sunapex).")
    md.append("3. The MPPT status LED should turn on (green = charging or float).")
    md.append("")
    md.append("**Verification:** under sun, panel Voc on multimeter matches nameplate ±5%. "
              "Battery voltage rises over the next hour.")
    md.append("")

    # ---- Phase 7: Wire controller ----
    md.append(f"## Phase 7: Wire the controller (Day 2, {_h(time_phase7)})")
    md.append("")
    md.append("### 7.1 ESP32 + sensors")
    md.append("")
    md.append("**Tools:** soldering iron (or perfboard), wire stripper, multimeter")
    md.append("")
    md.append("**Pins (from `firmware/wattplot.yaml`):**")
    md.append("")
    md.append("| GPIO | Function |")
    md.append("|---|---|")
    md.append("| 4 | DS18B20 1-Wire data |")
    md.append("| 5 | Watering solenoid |")
    md.append("| 16, 17, 18 | H-bridge IN1, IN2, EN |")
    md.append("| 19 | Grow light relay |")
    md.append("| 21, 22 | I2C SDA, SCL |")
    md.append("| 25 | WS2812B status LED |")
    md.append("| 32 | Soil moisture ADC |")
    md.append("| 33 | Battery voltage ADC |")
    md.append("| 34, 35 | Limit switches (0° and 90°) |")
    md.append("")
    md.append("### 7.2 Power")
    md.append("")
    md.append("1. Connect the DRV8871 H-bridge to the 12V battery (via a 5A fuse).")
    md.append("2. Connect the ESP32's VIN to a 5V buck converter on the 12V rail.")
    md.append("3. Verify all grounds are common.")
    md.append("")
    md.append("### 7.3 IMU + INA219 + DS18B20")
    md.append("")
    md.append("1. Mount the BMI160 on the panel (under the north rail). I2C address 0x68.")
    md.append("2. Mount the INA219 in series with the actuator (high side). I2C address 0x40.")
    md.append("3. Mount the DS18B20 in the bed soil.")
    md.append("4. All sensors share the I2C bus: SDA (GPIO 21), SCL (GPIO 22), 3.3V, GND.")
    md.append("")
    md.append("**Verification:** ESPHome logs show all sensors reporting values.")
    md.append("")

    # ---- Phase 8: Flash ----
    md.append(f"## Phase 8: Flash ESPHome (Day 2, {_h(time_phase8)})")
    md.append("")
    md.append("### 8.1 First flash over USB")
    md.append("")
    md.append("```bash")
    md.append("# Install ESPHome (if not already)")
    md.append("pip install esphome")
    md.append("")
    md.append("# Flash the firmware")
    md.append("esphome run firmware/wattplot.yaml")
    md.append("```")
    md.append("")
    md.append("### 8.2 WiFi + Home Assistant (optional)")
    md.append("")
    md.append("1. Set WiFi credentials in `firmware/secrets.yaml`.")
    md.append("2. Re-flash. ESP32 connects to WiFi and exposes all entities to Home Assistant.")
    md.append("3. Add the ESPHome integration in HA. Entities appear automatically.")
    md.append("")

    # ---- Phase 9: Calibrate ----
    md.append(f"## Phase 9: Calibrate + test (Day 2, {_h(time_phase9)})")
    md.append("")
    md.append("### 9.1 IMU zero-tilt offset")
    md.append("")
    md.append("1. With the panel flat (0°), read the BMI160's pitch value via ESPHome log.")
    md.append("2. That reading is your zero-tilt offset. Subtract it in the firmware.")
    md.append("3. Re-flash.")
    md.append("")
    md.append("### 9.2 Motor current calibration")
    md.append("")
    md.append("1. Manually drive the panel to 35°. Read the INA219 current (idle, no wind).")
    md.append("2. Set that as the `target_current_A` in `firmware/wattplot.yaml`.")
    md.append("3. Set `I_safe_A` just above the stall current (typically 2.5A for DRV8871).")
    md.append("")
    md.append("### 9.3 Limit switches")
    md.append("")
    md.append("1. Drive the panel to 0° (limit switch 0). Adjust switch position so it trips cleanly.")
    md.append("2. Drive to 90° (limit switch 1). Same.")
    md.append("3. Verify the firmware auto-stops at both limits.")
    md.append("")
    md.append("### 9.4 End-to-end test")
    md.append("")
    md.append("1. Open Home Assistant. Verify all sensors reporting.")
    md.append("2. Trigger a manual tilt from HA. Verify panel moves.")
    md.append("3. Press the user-override button. Verify it overrides the decision stack.")
    md.append("4. Leave it running for 24 hours. Check logs for any errors.")
    md.append("")

    # ---- Closing ----
    md.append("---")
    md.append("")
    md.append("**Total time:** " + _h(total_min) + " (with pre-cut lumber and a clean workspace).")
    md.append("")
    md.append("**Total cost:** see `python bring_your_own_panel.py` for an itemized estimate.")
    md.append("")
    md.append("**Next:** see `docs/test_checklist.md` for per-component and per-system tests.")
    md.append("")

    md_text = "\n".join(md)

    if output_to_file:
        write_build_guide(md_text, output_to_file)

    return md_text


def write_build_guide(md_text, path):
    """Write a build guide markdown to a file. Creates parent dirs if needed."""
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"Wrote build guide: {full} ({len(md_text)} bytes)")


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    # Test with the LONGi default
    print("=" * 70)
    print("Generating build guide for LONGi 620W (default)...")
    print("=" * 70)
    md = generate_build_guide(panel_name="longi_620W")
    print(md[:3000])
    print(f"\n... ({len(md)} total chars)\n")
