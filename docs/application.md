# Wattplot, Maker Faire Bay Area 2026, Application

> **STALE — references the BMI160 IMU ("closed-loop position feedback")
> and the 90° verticalize-for-rain tilt behavior.** The IMU is disabled
> in v3.2 and the 90° mode was retired (fails the wind calc). If you
> re-submit, soften those answers — see `firmware/README.md` and README
> §"Status & roadmap" for the current truth.

> **Curated responses for the Maker Faire Bay Area 2026 Call for Makers.**
> Copy each answer into the form. Notes below each field explain the
> choice.
>
> **Application URL:** https://makerfaire.com/bay-area (Call for Makers)
> **Show:** Sept 25–27, 2026 · Mare Island Naval Shipyard, Vallejo CA
> **Deadline:** typically early August, submit by end of week.

---

## Exhibitor Information

### Name (Required)
**Mohamad**

### Last Name (Required)
**Al-kahlout**

### Email (Required)
**mokahlou@gmail.com**

### Will this be your first time exhibiting at Maker Faire Bay Area?
**Yes**

### Your Location, City/District (Required)
**Phoenix**

### Country (Required)
**United States of America**

### State/Province (Required)
**Arizona**

---

## Project

### Project Name (Required)
> **Wattplot**
>
> *Note:* the form default text was "Watt Plot" (with a space). The
> brand is "Wattplot", one word, capital W, matching the repo
> (`github.com/mokahlo/wattplot`) and the README. Use the one-word
> form.

### Project Description (Required, public, on website)

> Wattplot gives a decommissioned solar panel a second life. An
> 8 ft × 5 ft raised bed with a hinged, ballast-mounted canopy
> holds an old rooftop panel, the same one that lost its
> inverter and was headed for the landfill, and uses it for
> shade, food, and some power. A $30 ESP32 smart controller tilts
> the panel to follow the sun, folds it flat for high winds,
> verticalizes it for rain, and shuts the motor off before it
> stalls. Fits any panel up to 97"×61", five validated presets
> from a 12-year-old 250 W residential salvage to a new 620 W
> bifacial. Open source (MIT), code-first, every drawing and
> every simulation in the repo.

*Rationale: ~280 chars, leads with the upcycling hook (the new
value prop), gives the dimensions and the technology, closes with
the open-source ask. No jargon. Accessible to a 12-year-old and
to a 60-year-old engineer.*

### What are your plans at Maker Faire? (Required, check all that apply)
- ☑ **Showcasing my project and sharing knowledge**
- ☑ **Creating a hands on activity to inspire others to make**

*Skip "Promoting a product or service," "Selling at Maker Faire,"
"Launching a product or service or crowdfunding campaign":
Wattplot is open source, not a product launch.*

### Project Website (Required)
**https://github.com/mokahlo/wattplot**

### Primary Project Photo (Required)

> **Use:** `renders/wattplot_v2_iso.png` (the iso view of the
> 8×4 full-size model at 35° tilt with tomato plants).
>
> **Specs check:** landscape, ≥900×600 px (the render is 1200×800
> at the source), 3:2 aspect ratio, no text overlay. The render
> is generated from the parametric FreeCAD model, so you have
> full rights.
>
> *Alternates if you want to swap:*
> - `wattplot_v2_mini_iso.png`, the benchtop version (18×14),
>   more relatable, "I can build this"
> - `wattplot_v2_flat_iso.png`, storm fold at 0°, the safety
>   story
> - `wattplot_v2_side_view_035.png`, engineering side view
>   (frame + actuator + hinge detail)
>
> **My pick: `wattplot_v2_iso.png`**, canonical, shows scale,
> the title is the project itself.

### Additional Project Photos (up to 5, 10 MB each, jpg/png/gif/webp)

Recommended order (strongest first):

1. **`wattplot_v2_iso.png`**, iso view, 35° tilt, full bed
2. **`wattplot_v2_mini_iso.png`**, benchtop mini (what's on
   the booth table)
3. **`wattplot_v2_flat_iso.png`**, storm fold at 0°
4. **`wattplot_v2_side_view_035.png`**, engineering side
   view with hinge + actuator detail
5. **`renders/booth_preview/booth_viewer_preview.png`** OR
   **`renders/booth_preview/booth_sim_dashboard_preview.png`**:
   shows the booth itself (3D viewer or sim dashboard)

*If you don't have the booth preview yet, substitute
`wattplot_v2_pcb_schematic.png` (PCB block diagram) for
slot 5.*

### Social Media Links (one full URL per line)
*Optional. If you have a YouTube build video, this is the place
for it.*

```
https://github.com/mokahlo/wattplot
```

### Project Video (optional)
*If you record a 30-second build-time-lapse (the booth
materials have a TODO for this), link the unlisted YouTube
URL here. Maker Faire features videos on the website.*

### Primary Category (Required)
**Alternative Energy**

### Additional Categories (up to 4)
- ☑ **Open Source**, MIT license, code-first
- ☑ **Sustainability & Nature**, agrivoltaic, food+energy from
  one footprint, **panel upcycling / second-life use**
- ☑ **Electronics**, ESP32 + MPPT + IMU + sensors
- ☑ **Education**, great classroom build (high school shop,
  college sustainability)

*If you want to swap one for something more "Maker Faire":*
- **Home**, backyard/balcony use case
- **Wood and Metal Working**, the build is all-wood + off-shelf
  hardware, with a continuous-hinge rod.
- **Microcontrollers**, ESP32 + ESPHome

---

## Maker Information

### Who would you like listed as the maker(s) of the project?
**Just Myself**

### Your Website
**https://github.com/mokahlo/wattplot**

### Your Photo (Required, square, ≥500 px)
*Needs a headshot of you. Take with a phone against a plain
background, crop to square.*

*Tips for the shot:*
- Plain wall behind you
- Daylight or a softbox, no harsh shadows
- Crop to 1:1 (square)
- 500×500 minimum, 1000×1000 better
- Look at the camera, slight smile, no sunglasses
- Maker Faire wants to put a face to the project

### Maker Bio (Required, public, on website)

> Mohamad is a maker in Phoenix, Arizona. Wattplot started as a
> backyard experiment to grow tomatoes in a small space and ended
> as a code-first agrivoltaic system, a parametric 3D model, an
> annual sun simulator, an ASCE 7-22 wind load analysis, an ESP32
> PI controller on motor current, and a Home Assistant dashboard,
> all in one open repo. The project pivoted in 2026 toward
> upcycling decommissioned rooftop panels, a single Wattplot
> planter fits any panel up to 8×5 ft, with five validated
> presets from 12-year-old 250 W residential salvage to new 620
> W bifacial. He builds it to learn; he shares it so others can
> build it too. First time exhibiting at Maker Faire Bay Area.

---

## Exhibit Logistics

### Space Size Request (Required)
**Standard Full Booth (10' x 10')**

### Do you need Tables and Chairs? (Required)
**Yes please**

### Number of Tables (Required)
**1**

### Number of Chairs (Required)
**2**

### Do you have a hands-on activity for attendees? (Required)
**Yes**

### Please describe your hands-on activity (Required)

> Visitors press a button on the booth table to tilt the panel
> between three modes: storm fold (0°), mid (15°), and
> power (35°, the structural max). The Mini v2.4 on the table responds in real
> time. Kids see the engineering, a PI loop on motor current,
> an IMU for closed-loop position feedback, a priority-ordered
> decision stack. Adults see the agrivoltaic loop, sun → MPPT
> → battery → tilt, all under $200 in parts.

### Location (Required)
**Either**

*If you have a preference: outdoor is better for a solar demo
(the sun lamp is for indoor backup). The Mini v2.4 has its
own 12V 7Ah battery, so it works either way. Pick "Either" if
you want the producers to choose based on layout.*

### Noise
**Normal - does not interfere with normal conversation**

### Does your exhibit require power? (Required)
**Yes**

*The Mini v2.4 has its own battery, but you'll want power for
the 24" live-sim dashboard monitor and the laptop running the
3D viewer. Standard 120V outlet, ~200W draw.*

### Does your exhibit use or disrupt radio frequencies?
**No**

*ESP32 is WiFi + BLE, these are license-free ISM bands, not
"disruptive." But the form only gives Yes/No, and you can
leave it No. The booth's WiFi comes from the venue.*

### Will you be giving away, selling, or sampling food?
**No**

*You're not handing out food, but you might mention tomatoes
grown in the bed. That's information, not food. "No" is
correct.*

### Do you have any additional special requests?
**No**

### Availability, Are you able to exhibit for the entire event? (Required)
**Yes**

> Friday 9/25 through Sunday 9/27

### Mobile Phone Number (Required)
**+1 6235653273**

---

## Safety

### Does your exhibit contain fire, chemicals, or dangerous materials? (Required)
**No**

*12V only. No propane, no welders, no open flames. The Mini's
solenoid is a 12V DC valve on tap water, not a hazmat.*

### Do you have an interactive exhibit including using tools, riding, climbing? (Required)
**Yes**

*The "interactive" here is the press-the-button-to-tilt-the-panel
demo. Visitors touch a momentary pushbutton; the panel tilts in
response. No tools, no climbing, no riding. The "Yes" is honest
because the form is asking about any interactive element.*

### Will your exhibit produce any waste? (Required)
**Yes**

*The Mini runs clean, but visitors will leave coffee cups and
take-home cards. "Yes" is honest (the form is about the whole
booth). Bring a small trash bag. The booth's net waste is
minimal, paper cards and plastic cups, both recyclable.*

---

## Optional Information

### Upload additional supporting documents
*Optional. If you have a 1-page project PDF, drop it here.
The README.md + one-pager in this repo are sufficient.*

### Is there anything else you want to tell us? (Optional, use this!)

> Wattplot's primary use case is **upcycling decommissioned
> solar panels that would otherwise be landfilled**. ~10M tons
> of panel waste globally by 2050 (IRENA). Most panels are
> removed because the racking or inverter failed, not the
> cells. A 12-year-old 250 W panel is still a 235 W panel:
> perfect for shade + some power, and you delay recycling by
> 10-20 years.
>
> The build is parametric: `wattplot_params.py` is the single
> source of truth for the 3D model, the annual sun simulator,
> the ASCE 7-22 wind analysis, and the engineering drawings.
> Change one number and the whole pipeline updates in ~10
> seconds.
>
> Five panel presets are validated: `longi_620W` (new
> bifacial), `residential_60cell` (12-yr-old salvage,
> 235 W derated), `residential_72cell` (8-yr-old, 288 W),
> `commercial_96cell` (6-yr-old, 388 W), and `large_format_1m65`
> (4-yr-old bifacial, 392 W). A custom-panel API is one
> function call: `apply_panel_preset(name)`.
>
> The Mini v2.4 on the booth table is a working validation
> prototype: real 10W panel, real MPPT, real actuator, real
> sensors, real soil. The firmware is the same ESPHome YAML
> that runs the full-size build. Every drawing, every
> simulation, every line of code is in the public repo under
> MIT license.

### Terms and Conditions
☑ **I accept the Terms and Conditions.**

---

## Pre-submit checklist

Before you click SUBMIT:

- [ ] Project name = "Wattplot" (one word, not "Watt Plot")
- [ ] Project description = the curated text above
- [ ] Plans: "Showcasing" + "Hands-on activity" only
- [ ] Primary photo: `wattplot_v2_iso.png` (or your pick)
- [ ] 4 additional categories: Open Source, Sustainability &
      Nature, Electronics, Education
- [ ] Maker bio = the curated text above
- [ ] Your photo: square, ≥500 px, plain background, your face
- [ ] Space: Standard Full Booth (10'×10')
- [ ] Tables: 1, Chairs: 2
- [ ] Hands-on activity: the curated description
- [ ] Location: Either
- [ ] Power: Yes
- [ ] Phone: +1 6235653273
- [ ] Interactive: Yes (the press-the-button demo)
- [ ] Waste: Yes (honest)
- [ ] Anything else: the upcycling block above
- [ ] T&C: accepted

## After you submit

- Make Community typically responds within 2-4 weeks
- They may ask for clarification, additional photos, or a video
- Once accepted, you'll get a Maker Toolkit with booth layout,
  load-in schedule, wifi info, and rules
- The full booth package (`booth/`) is already prepared:
  poster, one-pager, cut-list cards, demo script, FAQ, 3D
  viewer, sim dashboard

## If you get rejected

- Re-apply for the next regional Faire (San Diego, Phoenix,
  others, Make Community has a calendar)
- The booth materials in `booth/` are reusable for any
  Maker Faire or science fair / community event
- Worst case: a 5×10 tabletop at a local maker meetup is a
  great dry run before the next BA Faire
