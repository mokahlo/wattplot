# Demo Script, Maker Faire Bay Area 2026

> **STALE — references the BMI160 IMU and a 90° "verticalize to dry the
> bed" pitch beat. The IMU is disabled in v3.2 and the 90° mode was
> retired (fails the wind calc).** Update the script before the booth.
> See `firmware/README.md` for what the controller actually does today.

Three tiers, matched to the visitor. The 30-second version is for the
casual walk-by, most of your visitors. The 5-minute version is for
the maker who wants to see the firmware. Read the room.

---

## 30-Second Hook (the casual walk-by)

> "Wattplot is a DIY solar planter that gives an **old panel a
> second life**. A twelve-year-old panel from a decommissioned
> rooftop is still good for shade and some power. You put it on a
> raised bed, add a hinge and a smart controller, and it tilts to
> follow the sun. This is the benchtop version, watch, "

**[ press the button ]**

> ": the panel tilts to follow the sun. The whole thing runs off a
> twelve-volt battery that the panel charges through a real MPPT
> charge controller. The smart controller decides when to tilt based
> on rain, wind, soil moisture, and the time of day. Everything you
> see is open source, scan the QR, the build guide is free."

**[ hand them a cut-list card ]**

> "Have a good faire."

**Time:** ~30 seconds. **Goal:** plant a seed. The QR is the ask.

---

## 2-Minute Pitch (the curious visitor)

> "Wattplot is what happens when you stop choosing between a garden
> bed and a solar panel, and when you give an old panel a second
> life instead of sending it to the landfill. The whole thing is
> sized to fit a salvage panel from a decommissioned rooftop: a
> twelve-year-old 250 watt panel, still good for 235 watts, in a
> planter you build from 8-foot lumber. Up to 8 by 5 feet, fits
> any panel, the bed resizes when you call a preset."

> "What it does is grow food and make power from the same square
> footage. A full-size build in Phoenix makes about 850 kilowatt-hours
> a year with a salvage panel, or 2,200 with a new bifacial. A
> hundred and twenty-four kilos of tomatoes a year. The trade-off
> is engineered: the panel tilts so the bed gets morning and
> evening sun, but the harsh midday is shaded, which actually
> helps the plants."

> "What's new is the *control*, a thirty-dollar ESP32 and a real
> hardware MPPT charge controller. The panel charges the battery
> through MPPT, the MPPT runs its own charge profile, the ESP32
> only reads the battery voltage. The smart controller, "

**[ press the button ]**

> ": is a PI loop on motor current. The IMU tells it the actual
> panel angle. The decision stack decides what angle to *want*:
> rain, wind, soil, time of day. The PI loop just keeps the motor
> from burning out under wind load."

> "The whole thing is parametric, change one number in the Python
> file, the 3D model and the sun sim and the wind sim all update.
> Open source, MIT, every drawing is in the repo. The mini is one
> ninety-three in parts. The full-size is fourteen hundred with a
> new panel, about eight hundred with a salvage."

**[ hand them a take-home card ]**

> "The repo's on the card. The upcycling guide is in the docs.
> If you build one, send me photos."

**Time:** ~2 minutes. **Goal:** the visitor understands the project
and remembers it tomorrow.

---

## 5-Minute Deep Dive (the maker who wants the firmware)

After the 2-minute pitch, but only if the visitor leans in:

> "OK, the firmware. It's ESPHome. Single YAML file in
> `firmware/wattplot.yaml`. The PI loop runs at one hertz, deadband
> is plus or minus two degrees, the current limit trips at two and
> a half amps, the DRV8871 trips at three-point-six, so you've
> got a one-point-one amp safety margin. The wind-fold logic is in
> the decision stack: if motor current exceeds a threshold for more
> than five seconds, fold to zero. If NWS says more than fifty
> miles an hour in the next hour, preemptively fold to fifteen
> degrees."

> "The rain capture is a fun one. If the soil's dry and NWS says
> rain, the controller holds the panel at fifteen degrees to
> maximize rain landing on the bed. If the soil's already wet, the
> controller verticalizes to ninety degrees to dry the bed out and
> prevent root rot."

> "Sun position is computed with pvlib. The decision stack is
> priority-ordered, user override beats safety beats weather beats
> soil beats time-of-day. The whole thing is sixty-odd lines of
> decision logic on top of the PI loop."

> "Calibration: the IMU has a zero-tilt offset you have to measure
> on the bench. The actuator's stroke gives you a tilt range
> empirically, the 100mm kickstand actuator hits its end-stop
> at about thirty-five degrees, which is fine because the
> full-size build's twenty-four-inch actuator hits ninety."

**[ point to the screen ]**

> "The dashboard is just a stand-alone HTML page. Reads the
> pre-computed sim for the demo, the live version talks to the
> ESP over WiFi. You can see the panel kWh, the DLI, the soil
> moisture, the wind, the battery. The kWh number updates as the
> panel moves. The DLI is a rollup of the morning and afternoon
> sun on the bed."

> "Want to build one? The hardest part is the bed. The half-lap
> corners need a router or a chisel. Everything else is a drill and
> a screwdriver. Take a card."

**Time:** ~5 minutes. **Goal:** the maker goes home and reads the repo.

---

## Asks to plant (every pitch)

Pick the one that fits:

- **"Scan the QR."** (primary ask, repo is the outcome)
- **"If you build one, send me photos."** (community growth)
- **"I'm here all weekend, come back tomorrow."** (return visits)
- **"Tell a teacher, this is a great classroom project."** (multiplier)

Do **not** ask for an email unless they offer. Do **not** push the
volunteer-to-help angle. People are at a faire to look, not to be
recruited.

---

## What NOT to say

- "It's not finished yet", say "this is the validation prototype, the
  full-size build is on the poster."
- "The smart controller is a work in progress", say "the controller
  has a PI loop on motor current and a priority-ordered decision
  stack, the firmware's in the repo."
- "It's complicated", never. Every part of the build is a board and
  a screw.
- "I don't know, that's a good question", say "good question, let me
  look that up tonight and post the answer in the repo." Then actually
  do it. This is how good projects get built.
- Long apologies for the unfinished state. Acknowledge, move on.

---

## Body language notes

- **Stand, don't sit.** Visitors are afraid to interrupt someone
  sitting. Standing says "I want to talk to you."
- **Look at the visitor, not the project.** The project is the
  prop. The visitor is the audience.
- **Smile at the kid before the parent.** Kids drive the parent's
  attention span. If the kid is engaged, the parent is too.
- **Move the panel while you talk.** Constant micro-motion is what
  catches the eye from across the aisle.
- **Have a piece of paper in your hand.** People trust someone who
  writes things down. Use the cut-list card.

---

## Booth etiquette (3 rules)

1. **One pitch per visitor.** If they're not into it, thank them and
   hand them a card. Don't follow.
2. **Don't pitch the person who's pitching you.** If someone is
   selling *their* project to you, listen. Trade cards.
3. **If the table is empty, look up.** A booth with no eye contact is
   a booth with no visitors. When the table is empty, you're allowed
   to look bored, but you're not allowed to *be* bored.

---

## Run-of-show (3 days)

| Day | Open | Talk | Lunch | Talk | Close |
|---|---|---|---|---|---|
| Fri | 10:00 | 10:00 – 12:30 | 12:30 – 1:30 | 1:30 – 5:00 | 5:00 – 5:30 |
| Sat | 10:00 | 10:00 – 12:30 | 12:30 – 1:30 | 1:30 – 5:00 | 5:00 – 5:30 |
| Sun | 10:00 | 10:00 – 12:30 | 12:30 – 1:30 | 1:30 – 4:00 | 4:00 – 4:30 (early close) |

Two operators minimum. Stagger lunch. Sunday is family day, more
kids, more questions, slower talk.
