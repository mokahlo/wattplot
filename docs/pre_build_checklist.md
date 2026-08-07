# Pre-build lumber quality checklist

Before you cut any wood, walk through this checklist with the
lumber you've bought. The wind and post-bending analyses assume
**clear, sound lumber** — knots, slope-of-grain, decay, and
wane reduce strength significantly. The NDS values the wind calc
references are for Select Structural grade; most lumber-yard
"construction grade" 4x4 is actually #2 or worse.

If you find any of these issues on the lumber you've bought,
**return it** to the lumber yard and pick different boards. Do not
"work around" it by moving the cut to a different location — the
structural path is well-defined and bad wood on that path means a
real-world failure mode.

## Check every board you plan to use

- [ ] **No knots larger than 1" in the bottom 12" of the four
      4x4 corner posts.** The base of the post carries the
      bending moment (see `analysis/post_bending.py`). A knot at
      that location reduces the cross-section's effective area and
      breaks the SF > 1.5 target.
- [ ] **No knots larger than 1/3 of the board face** anywhere
      along the post or rail length. Smaller knots (>1" but <1/3
      of the face) are acceptable at mid-height where the moment
      is lower.
- [ ] **No through-checks or splits.** A crack running through
      the board face means the fibers are already separated; the
      bending moment will open it further. Tap the board on the
      ground — a dull thud indicates internal decay; a clear
      ring is sound.
- [ ] **No wane (missing wood) on the load-bearing edges.** A
      4x4 with a rounded corner at the bottom is fine for
      appearance but not for a column under a 6 ft lever arm.
- [ ] **No twist > 1/4" over the length of the board.** Check
      by laying it on a flat surface. Twist compounds as the
      frame goes together; > 1/4" twist at the lumber yard is
      > 1" twist in the assembled frame.
- [ ] **No cup > 1/8" over the width.** Cup is OK in the bed skin
      boards (the cleats hold them flat) but not in the rails.
- [ ] **Moisture content < 19%** (KD-19 or kiln-dried). PT
      lumber is usually wetter at delivery. If it's > 19%, let
      it acclimate in the build area for a week or sticker-stack
      it before installing. Wet PT will shrink and open joints
      as it dries.
- [ ] **Stamp check** — the grade stamp should be legible
      ("S-P-F", "Douglas Fir", "Hem-Fir", etc.). If you can't
      read it, the lumber yard can't certify the grade.

## Pressure-treated (PT) specific

- [ ] **Use UC3B or UC4A rated for ground contact.** UC2
      ("above ground") is wrong for the bed cleats and skids.
      The lumber yard should have a tag or stamp. If unsure,
      ask.
- [ ] **Modern ACQ or copper azole treatment, not CCA.** CCA
      (chromated copper arsenate) is banned for residential use
      since 2003 in the US. ACQ is the modern equivalent and
      is what you'll get from Home Depot / Lowe's.
- [ ] **No "checker" surface treatment failures.** PT should
      have a uniform greenish tint and the incising pattern
      should be consistent. Misshapen checker pattern = the
      treatment didn't penetrate uniformly.

## Cedar specific (for the skin boards)

- [ ] **Heartwood > sapwood.** Cedar's rot resistance is in
      the heartwood. Sapwood (the lighter outer ring) will rot
      within 3-5 years when buried. Look for boards with
      mostly heartwood (the darker, aromatic inner wood).
- [ ] **No wane on the face.** Wane on a 1x6 skin board means
      less wood holding the cleat. The cleats are at most
      24" o.c., so any board with wane in the middle 12" of
      its face is unusable.
- [ ] **No "skip" (planer misses).** Cedar is often rough-sawn
      at the lumber yard. Skip is cosmetic for the garden bed
      but matters where the cleat screws bite into the skin.

## Stainless / hot-dip galvanized hardware check

- [ ] **Screws are #10 or larger, ACQ-compatible.** ACQ eats
      plain zinc-coated screws in 6-12 months. Use Simpson
      Strong-Tie Outdoor Accents or equivalent. Box of 1 lb is
      ~$8.
- [ ] **Bolts are hot-dip galvanized or stainless.** The hinge
      bolts, actuator mount, and panel clamps carry significant
      load. Don't use electro-galvanized (zinc-flash) bolts in
      ACQ-treated lumber — they corrode.
- [ ] **No mixing of galvanized and stainless.** Galvanic
      corrosion between dissimilar metals is real; if you use
      stainless bolts in a galvanized bracket, the bracket
      corrodes faster. Pick one metal and stay with it.

## Site prep

- [ ] **Bed footprint level within 1" over 8 ft.** Use a 4 ft
      level + straight edge. The 35° tilt assumption in the
      wind calc is for a level bed; a > 1" tilt in one
      direction adds a moment the calc didn't budget for.
- [ ] **No overhead wires or trees within 10 ft of the
      actuator's max extension.** At 35° tilt the panel + post
      top is ~7.5 ft up. A windstorm that drops a branch on the
      panel will destroy the actuator AND the panel.
- [ ] **Southern exposure, no shade between 10 AM and 4 PM
      year-round.** Use the SunAP (iPhone) or Sun Surveyor (any
      phone) to verify before you commit to the bed location.

## Don't

- [ ] Don't use boards with heart-rot even if it's "small" —
      it grows.
- [ ] Don't use lumber marked "stud grade" for the structural
      members (posts, rails). Stud grade is graded for
      non-structural use; it's not the same as #2 structural.
- [ ] Don't assume "new from lumber yard" = "dry". Most PT is
      wet at delivery; budget for a week of drying time.
- [ ] Don't substitute 2x4 for 4x4 posts — the moment of
      inertia is 8x different (I = bh³/12; 3.5³ vs 1.5³ = 12.7
      ratio). The post-bending analysis assumes 4x4.

## When in doubt

Post-bending analysis (`analysis/post_bending.py`) says the
4×4 fails at 35° unbraced. The two remedies are:
- **Upsize to 6×6** (SF 2.53 with the same loads)
- **Add lateral bracing** (square-cut gusset plates or off-the-shelf
  structural angle brackets)

If your lumber is borderline (knots at the base, lower-grade
stamp), pick one of those remedies. The wind calc is a first-pass
model with a 2.0 SF target; the PE review recommended in the
README is the right move if you have any doubt about the lumber
quality.