# Wattplot, Maker Faire FAQ

> **STALE — references the BMI160 IMU and entity names from the v2.4
> firmware (`panel_voltage_v`, `panel_current_a`, `poa_irradiance_w_m2`,
> `battery_v`, etc.). The IMU is disabled; entity names in v3.2 are
> human-friendly ("Panel V", "Panel Current", "POA Irradiance",
> "Battery Voltage").** Update before printing. See `docs/control.html`
> and `firmware/README.md` for the current entity list.

Anticipated questions, ranked by how often you'll get them. Read this
once before the faire. The answers are designed to be said out loud,
not just read.

---

## The top 8 (you'll get these 50+ times)

### 1. "How much does it cost to build?"

> The full-size 8×5 ft is about **$1,400** in parts with a new
> bifacial panel, or **~$800** with a salvage panel from a
> decommissioned rooftop. The mini on the table is $193. Both are
> in the build guide; the take-home card has the mini's cut list.
> See `docs/upcycling.md` for the salvage-panel path.

### 2. "How much electricity does it make?"

> In Phoenix, the full-size makes about **2,240 kWh/yr** at 35° tilt
> with a new 620 W bifacial, or **~850 kWh/yr** with a typical
> 12-year-old 235 W salvage panel. That's about $300/yr (new) or
> $115/yr (salvage) at Arizona rates. The mini on the table makes
> about 16 kWh/yr, enough to run the controller and the grow light
> and a small pump. The point of the mini is to validate the
> full-size; the point of the full-size is shade + some power, not
> net-zero.

### 3. "Does it actually grow food?"

> The full-size has been simulated to grow about a hundred and twenty
> eighty-four kilos of tomatoes a year. That's about a hundred
> and eighty-five pounds, from four plants,
> four plants. The trick is the tilt: morning and evening sun gets to
> the bed, midday is shaded, the soil doesn't cook. The mini on the
> table is a validation prototype, not a production garden, but the
> geometry, firmware, and MPPT are the same.

### 4. "Can I build one for my apartment?"

> Yes. The mini is designed for a balcony. The full-size is heavy:
> a thousand pounds of wet soil, so you need a place that takes the
> load. The mini's 18×14 bed weighs about thirty pounds wet and fits
> on most decks.

### 5. "Why not just put solar panels on the roof?"

> Three reasons. First, the agrivoltaic part: you grow food *and*
> make power from the same square footage. Second, plug-and-play
> solar laws in California, Utah, and Colorado let you skip the
> permit process for sub-800-watt systems. A balcony-mounted
> system is invisible from the street. Third, the panel is the
> *shade cloth* for the bed. Tomatoes in Phoenix do better with
> partial afternoon shade, and the panel provides it for free.

### 6. "Is it waterproof? What about rain?"

> The panel sheds rain onto the bed. The controller's IP65, the MPPT's
> IP67, the panel's IP68, the soil sensors are waterproof. The bed is
> open-bottomed, it drains into the native soil. The smart controller
> actually uses rain: when the soil's dry and rain's coming, it tilts
> the panel to maximize rain landing on the bed.

### 7. "What about wind? Won't it blow over?"

> The full-size is ballasted, a thousand pounds of wet soil holds it
> down. The frame is designed for a hundred-and-fifteen-mile-an-hour
> three-second gust at thirty-five degrees of tilt with a safety factor
> of two. The smart controller folds the panel flat in high wind. The
> mini is light enough to bring inside.

### 8. "Where do I start?"

> The repo's on the card. The build guide is step-by-step. The mini
> build is the easiest entry point, about three hours, one ninety-three
> in parts, all from Amazon and Home Depot.

---

## The "I know a thing" questions

### 9. "Why not bifacial_radiance for the sim?"

> It is the gold standard. Our shadow raycaster is a 2D
> approximation that uses the actual 3D panel geometry. It's a
> simplification, the 2D slice over-estimates winter DLI by about
> fifteen percent, under-estimates summer by about ten. The
> full simulation in `analysis/sun_simulator.py` uses pvlib for
> sun position and clear-sky modeling, which is the same library
> bifacial_radiance uses for its inputs.

### 10. "Why MPPT over PWM? Why not a simple solar charge controller?"

> MPPT extracts twenty to thirty percent more energy from the panel
> in cold and cloudy conditions. PWM is fine for trickle charging but
> the full-size panel is six hundred watts, PWM would throw away half
> the energy on a hot day. The mini uses a Sunapex 10A MPPT, the
> full-size uses a Victron SmartSolar 100/30 or an EPEver Tracer
> 4210AN. The ESP32 only reads the battery voltage; the MPPT does its
> own charge profile.

### 11. "What about a 3D-printed version?"

> The brackets in the build guide are 1×2 wood offcuts, printable
> in PETG, but the wood is cheaper, stiffer, and the right color for
> a planter. If you want a 3D-printed version, the FreeCAD source is
> in the repo. You can swap the wood parts for printable parts at
> parametric time.

### 12. "Can I use this for off-grid?"

> Yes. The full-size has a 12V 100Ah LiFePO4 battery. With a two
> thousand watt-hour battery and twenty-two hundred kilowatt-hours a
> year of generation, you can run a fridge and a few LED lights
> year-round, depending on your draw. The mini is too small to
> meaningfully off-grid anything except the controller and the grow
> light.

### 13. "What about a tracker? Why just tilt, not pan?"

> The full-size is a single-axis tilt, not a dual-axis tracker. The
> power gain from azimuth tracking is about eight percent in Phoenix,
> and the cost is a second actuator, a second IMU, and a lot more
> firmware. The bed, not the panel, is the priority. A single-axis
> tilt lets the morning and evening sun get to the bed, which a
> dual-axis tracker would block.

### 14. "Why is the panel wired to a Y-splitter, doesn't that hurt MPPT?"

> No, because the Y-splitter is *after* the panel, on the DC bus. The
> MPPT sees the panel; the microinverter sees the panel; they don't
> see each other. Both have their own MPPT (well, the microinverter
> has its own panel-side optimizer). The panel produces 50–100× more
> energy than the controller needs, so the Y-splitter doesn't
> starve either load.

### 15. "What's the decision stack? How does it prioritize?"

> It's priority-ordered. User override first, then hard current limit
> (failsafe to zero), then NWS rain forecast, then wind forecast, then
> soil state, then time-of-day. The PI loop on motor current is the
> safety layer underneath all of them. Full spec is in
> `docs/control_law.md`.

### 16. "Can it integrate with Home Assistant?"

> Yes, ESPHome has a native Home Assistant integration. The mini
> already exposes tilt, current, soil moisture, temperature, and
> battery voltage. The `firmware/wattplot.yaml` is a drop-in ESPHome
> config. If you're running HA, add the ESPHome integration and the
> entities show up automatically.

---

## The "my kid will love this" questions

### 17. "What age is this for?"

> The build itself is for an adult, drill, saw, basic wiring. The
> *concept* is great for a kid of any age. The panel tilts, the soil
> gets watered, the sun makes power. The dashboard on the screen
> shows real numbers changing. There's a "what should the panel do
> now" decision they can predict and then watch. A great classroom
> project.

### 18. "Is there a school curriculum?"

> Not yet. This is the kind of project that's perfect for a high
> school shop class or a college sustainability seminar. The build
> has mechanical, electrical, and software components, and the
> decisions are real. If you're a teacher, get in touch; I'd love to
> write one.

---

## The "I'm a builder" questions

### 19. "How long does it take to build?"

> The full-size is ten to fifteen hours over a weekend with lumber
> pre-cut. The mini is three to four hours. Both are in the build
> guide with step-by-step instructions and verification steps.

### 20. "What's the hardest part?"

> The bed half-lap corners. A router with a straight bit is the
> right tool. A circular saw and a chisel works too, just slower.
> Everything else is a drill and a screwdriver.

### 21. "Can I customize it?"

> Yes. `wattplot_params.py` is the single source of truth. Change
> the bed length, the panel wattage, the tilt range, the wind speed
> limit, the 3D model, the sun sim, the wind sim, and the
> engineering drawings all update in about ten seconds. Build
> guides are for the default config.

### 22. "What about hail? Snow? Hurricanes?"

> The smart controller folds the panel flat in wind. The bed is
> below the frame, so a folded panel protects the bed from hail.
> The bed itself is open-bottomed and the lumber is pressure-treated,
> so snow load is on the soil, not the wood. Hurricane winds are
> beyond the design limit, the structure is rated for a
> hundred-and-fifteen-mile-an-hour gust, which is the ASCE 7-22
> Phoenix Cat II 700-year event, not a Cat V hurricane.

---

## The "I'm a journalist" questions

### 23. "What's the bigger story here?"

> The story is that agrivoltaics is real, code-first, and DIY-able.
> Most agrivoltaic systems are commercial, a researcher at a
> university with a grant, a solar company with a product. This
> is one person, a Python file, and a Saturday. The same patterns
> (parametric 3D model, sun sim, wind sim, ESP32 controller) work
> for any raised-bed-with-solar project, not just this one.

### 24. "Where can I see one in operation?"

> Right here. The mini on the table is a validation prototype of
> the full-size. The full-size hasn't been built yet, the smart
> controller is the next step, then the PCB, then the first
> physical build. Follow the repo, the build photos will go up
> when there's a build to photograph.

---

## The "I want to help" questions

### 25. "Can I contribute to the project?"

> Yes. Issues, PRs, forks welcome. The codebase is small enough
> to read in an afternoon. The most-helpful contributions: build
> photos, calibration data from a real build, additional sensor
> drivers, a panel-mist cooling mode, the full-size build log.

### 26. "Are you on social media / a Discord / a forum?"

> The repo is the community. Open an issue, get an answer. The
> "I built one" thread in the discussions tab is the closest thing
> to a forum.

---

## Wildcards (you might not get these, but just in case)

### 26a. "What about old panels? Can I use one from my own rooftop?"

> Yes, that's the primary use case. A 12-year-old 250 W panel is
> still a 235 W panel after the standard 0.5%/year degradation. It's
> not cost-effective for grid-tie anymore (the inverter is the limit,
> not the panel), but it's perfect for shade + some power. Wattplot
> has five named panel presets and a general "bring your own" path.
> Measure the aluminum frame dimensions, call `apply_panel_preset()`,
> and the bed resizes. The cut list is derived from the bed, so the
> build scales with the panel. See `docs/upcycling.md` for the full
> guide.

### 26b. "What if my panel is bigger than 8×5 ft?"

> Two options. **Chain multiple planters in a row**, the structural
> design works for a row of identical planters sharing a common
> hinge axis. Or **scale the build up** with 10-ft or 12-ft lumber
> stock, which is more expensive but the same design pattern. The
> single-planter 8×5 cap is from 8-ft lumber stock; it's the
> cost-optimal, single-person-build size.

### 26c. "How do I tell if a salvage panel is still good?"

> Four checks: (1) the **glass** is intact, no cracks; (2) the
> **aluminum frame** is straight, no bent corners; (3) the
> **junction box** is sealed, no burn marks; (4) under full sun,
> the panel's **Voc** (open-circuit voltage) is within 5% of the
> nameplate, measured with a multimeter. A thermal camera is a plus
>, hot spots mean cell mismatch. Most decommissioned panels pass
> all four checks. Avoid cracked glass, delamination, or visible
> hot spots.

### 27. "What about vermicomposting? Aquaponics?"

> Aquaponics is a different project, the bed doesn't have a
> reservoir, the soil is the structure. Vermicomposting would
> work great in a Wattplot bed, the soil ecosystem is the same as
> any raised bed.

### 28. "What about a transparent panel? Wouldn't that grow more food?"

> Transparent bifacial panels exist, but they're expensive, less
> efficient, and the transparency varies across the cell. The
> partial-shade pattern in this design is actually better for
> tomatoes than full sun, full sun in Phoenix cooks the soil and
> stresses the plants.

### 29. "How do you keep the squirrels out?"

> Same as any raised bed, hardware cloth under the soil, a
> chicken-wire cage if the local squirrel population is serious.
> The Mini on the table is a non-issue.

### 30. "What about a community garden version?"

> Yes. The full-size is *exactly* the right scale for a community
> garden plot. The wifi telemetry makes it easy to monitor from a
> distance. The Home Assistant integration gives a community-garden
> manager a single dashboard for ten or twenty of them.

---

## When you don't know

> "Good question, let me look that up tonight and post the answer in
> the repo discussion. The repo's on the card, drop me a line."

**Then actually do it.** This is how open-source projects get good
documentation. Every "I don't know" at the faire is a free contribution
to the docs.
