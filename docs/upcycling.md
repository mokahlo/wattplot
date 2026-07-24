# Wattplot, Panel Upcycling Guide

> A single Wattplot planter is **8 ft × 5 ft** (max). It fits any solar
> panel that fits in that envelope, new panels from the manufacturer,
> or **old panels rescued from decommissioned arrays** that would
> otherwise be landfilled.
>
> Most decommissioned panels are still functional. They've lost
> 8-15% of their nameplate output over 10-20 years, but they're not
> cost-effective for grid-tie anymore. They're perfect for **shade +
> food + some power** in a Wattplot.

## Why upcycle?

- **~10M tons** of solar panel waste globally by 2050 (IRENA 2016).
  Most of it is glass, aluminum, and silicon, recyclable, but
  recycling costs money and the infrastructure is sparse.
- A **second-life** use case (shade + some power) delays recycling
  by 10-20 years and recovers ~50-90% of the panel's original
  useful energy.
- Most panels are removed from service because the **inverter** or
  **racking** failed, not the panel itself. The cells are usually
  fine.
- A 12-year-old 250W panel is still a 235W panel. For a
  shade-and-power application, that's a free 235W.

## The 8×5 envelope

Wattplot's single-planter size is set by **lumber stocking length**:
8 ft is the longest common dimension at Home Depot, with zero waste
on the long rails. 5 ft is the wide cross-rail cut from one 8-ft
board (two cross-rails per board, 6" waste).

Panels can overhang the bed by **0.5" per side** (1" total in either
direction). The mid-clamps grip the aluminum frame, which sits on
the wood rails, overhang is fine and is how the LONGi Hi-MO X10
(97" panel, 96" bed) works.

Anything bigger → **chain multiple planters in a row**. Two 8×5
planters side by side is 8×10 ft, which fits two 60-cell panels
laid out as a 2×1 array.

## Common salvage panels (all fit)

These are the **named presets in `wattplot_params.py`**. Each one
has been validated to fit the 8×5 cap and produce a sensible bed
size:

| Preset | L × W (in) | New W | Age | Bifacial | Derated W | Bed L × W (in) |
|---|---|---|---|---|---|---|
| `longi_620W` | 97.0 × 44.6 | 620 W | 0 yr | yes | **620 W** | 96.0 × 44.6 |
| `residential_60cell` | 65.0 × 39.0 | 250 W | 12 yr | no | **235 W** | 65.0 × 39.0 |
| `residential_72cell` | 77.0 × 39.0 | 300 W | 8 yr | no | **288 W** | 77.0 × 39.0 |
| `commercial_96cell` | 65.0 × 41.0 | 400 W | 6 yr | no | **388 W** | 65.0 × 41.0 |
| `large_format_1m65` | 65.0 × 41.0 | 400 W | 4 yr | yes | **392 W** | 65.0 × 41.0 |

All five are tested in `wattplot_params.py`, calling
`apply_panel_preset(name)` swaps the panel + bed + derated wattage
in one call.

## How to use a custom (non-preset) panel

For a panel that's not in the preset list:

```python
import wattplot_params as P

# Measure your panel (with the aluminum frame, the clamps grip the frame)
P.PANEL['L_in'] = 66.5         # length, including frame
P.PANEL['W_in'] = 39.0         # width, including frame
P.PANEL['thickness_in'] = 1.6
P.PANEL['mass_lb'] = 40.0
P.PANEL['wattage'] = 245       # new nameplate (or your measured Voc/Imp)
P.PANEL['panel_age_years'] = 8 # 8 years old
P.PANEL['panel_bifacial'] = False
P.PANEL['panel_efficiency_pct'] = 17.0

# Then call the helper to resize the bed and derate the wattage
P.apply_panel_preset('longi_620W')  # arbitrary preset just to trigger the helper
# Or call the function inline if you didn't change a preset key:
# (See apply_panel_preset source for the derate + bed-resize logic)
```

The derate formula is **0.5% per year, floor 70%**, typical for
crystalline-silicon panels. Polycrystalline degrades slightly
faster (0.7%/yr). Adjust `panel_efficiency_pct` to match the panel.

## Lumber math (the cut list scales with the bed)

The cut list is **derived from the bed dimensions**, not hardcoded.
For a bed of `B_L × B_W` inches:

| Member | Length | Source |
|---|---|---|
| 2 × long rails | `B_L` | 2×6×8ft, no waste if `B_L = 96` |
| 2 × cross rails | `B_W` | 2×6×8ft, 2 per board (waste = 96 - 2·B_W) |
| 1 × diagonal brace | √(B_L² + B_W²) + 0" (square ends butt into rails) | 2×4×10ft for full-size, 2×4×8ft offcut for mini |
| 1 × continuous hinge pin | `B_L` (extends 1" each end) | ½" steel rod, `B_L` + 2" |
| Bed walls (4) | 2 × `B_L`, 2 × `B_W` | 2×12, depends on `B_L` and `B_W` |

If `B_L = 96"` and `B_W = 44.6"` (the LONGi 620W default), the cut
list is exactly what's in `bom.md` and the build guide.

If `B_L = 65"` and `B_W = 39"` (the 60-cell preset), the long rails
are 65" each (cut from 2×6×8ft, 31" waste per board) and the cross
rails are 39" (2 per board, 18" waste per board). The diagonal
brace is 76" (from 2×4×8ft, 20" waste).

## Structural check

The wind-load analysis (`analysis/wind_load.py`) takes the panel
dimensions and computes the wind force, moment, and safety factor
on the bed. For a smaller panel, the wind force is **lower** (the
wind force is proportional to the panel area), so the safety
factor goes **up**, a smaller, lighter panel is easier to support.

This means old/salvage panels are often **easier to validate** than
the 620W default. The wind analysis should pass at smaller panel
sizes with the same bed structure.

## MPPT sizing

| Panel | Imp | Recommended MPPT |
|---|---|---|
| LONGi 620W (new, full-size) | 17.5 A | Victron SmartSolar 100/30 or EPEver Tracer 4210AN |
| 60-cell salvage (235W) | 7.5 A | Sunapex 10A MPPT (or any 10A MPPT) |
| 72-cell salvage (288W) | 8.5 A | Sunapex 10A MPPT (or any 10A MPPT) |
| Commercial 96-cell (388W) | 11.0 A | Victron SmartSolar 100/20 (20A) or EPEver Tracer 2210AN |
| Large 1m65 (392W) | 11.0 A | Victron SmartSolar 100/20 (20A) or EPEver Tracer 2210AN |

A Sunapex 10A is fine for the 60-cell and 72-cell salvage cases
(7-8A peak). For the bigger panels, step up to a 20A or 30A MPPT.

## When a salvage panel is *not* a good fit

- **Cracked glass.** Water will get in and the cells will fail. Don't
  use these.
- **Delamination.** Bubbles or peeling on the front. The cells are
  degrading; useful life is short.
- **Hot spots.** If a thermal camera shows >20°C delta on the panel
  surface under sun, the cells are mismatched and the panel will
  continue to degrade. Don't use these.
- **No label / no specs.** A panel you can't identify may have
  different dimensions than expected. Measure it before designing
  the bed.

A good salvage panel has a clean label (Voc, Isc, Imp, Vmp, Pmax),
intact glass, intact aluminum frame, intact junction box, and
measures close to its nameplate Voc/Isc under full sun (use a
multimeter).

## Open question: bifacial upcycling

Most pre-2018 salvage panels are monofacial. Bifacial panels are
typically 2018+. If you're sourcing from a recent decommissioned
commercial array, you might find bifacial salvage, and the 10%
bifacial bonus is significant for a Wattplot's annual kWh.

If you have access to bifacial salvage, set `panel_bifacial=True`
in the preset. The function will set `bifacial_bonus = 0.10`.

## Summary

A 12-year-old 250W residential panel salvaged from a rooftop
decommissioning is a 235W panel in a Wattplot. Free shading, free
power for the controller and grow light, second-life delay on
recycling, 235 kWh/year in Phoenix. **The single most sustainable
way to add solar to a garden bed.**
