# Booth Runbook — Maker Faire Bay Area 2026

Operational runbook for the booth. Read this before the faire. Print
the recovery checklist at the bottom and keep it in the toolkit.

## Pre-faire (T-7 days)

- [ ] **Cloudflare Access policy applied.** See
      `docs/_internal/remote-access.md` §8. Until this is on, the
      `/api/switch` and `/api/button` POSTs are reachable by anyone
      on the internet.
- [ ] **Wattplot on the bench, calibrated, plugged in.** Run
      `python tools/calibrate_watch.py` once. The endstop current
      threshold should land in 0.85 - 1.0 A; the actuator should
      retract to 0° on release.
- [ ] **Live control panel reachable from github.io.** Open
      <https://wattplot.org/control.html> on the booth
      laptop. Verify the panel shows the live chip (not the stale
      banner) and that pressing Calibrate doesn't 500.
- [ ] **Sim dashboard renders.** Open the local
      `docs/sim.html` (or run `jekyll serve` if the laptop is
      offline). The sim should show a 24-hour preview curve.
- [ ] **Demo script printed.** Bring 4 copies of the 30-second,
      2-minute, and 5-minute scripts (`docs/demo_script.md`).
- [ ] **Cut-list cards printed.** 50 of
      `booth/CUT_LIST_CARD.md`, 8.5 × 11. Most visitors want a
      "what would I build at Home Depot" takeaway.
- [ ] **Inventory check.** See `booth/PARTS_STATUS.md` for what
      you own vs. what to buy the morning of.

## Pre-faire (T-1 day)

- [ ] **Battery charged.** 12 V 100 Ah LiFePO4 at 100 % SOC.
      Voltage at the controller's GPIO7 ADC should read 13.2 - 13.4 V
      (Sunapex in absorption at full charge).
- [ ] **Log subscriber running.** `python tools/log_subscriber.py
      --broker localhost` (Mosquitto local) or wherever the broker
      is. The log file is your post-mortem tool if anything goes
      wrong at the booth.
- [ ] **Test the auto-fold path.** With the controller in Normal
      mode, manually command tilt to 35°, then short the panel
      INA219 (simulate motor stall). The controller should fold
      within 1-2 s. Recover by setting Controller State back to
      Normal.
- [ ] **Backups.** A USB stick with `docs/`, `firmware/`, and a
      recent `wattplot.log.gz` in case the laptop dies.

## Faire day

### 8:30 AM — setup

- [ ] **Power on.** Battery first, then panel INA219, then
      controller.
- [ ] **Verify the panel responds.** `python tools/dump_state.py`
      should show `Controller State = Normal`, `Battery Voltage >
      12.5 V`, `WiFi Signal > -70 dBm`.
- [ ] **Open the panel in a browser.** Click each of: solenoid
      ON/OFF, Calibrate, "Water Now". Confirm the actuators
      respond.
- [ ] **Stale banner test.** Briefly disconnect the chip's USB
      power, watch the panel show the stale banner within 5 s.
      Reconnect, watch it clear within 5 s.

### 9 AM - 6 PM — open

- **Tabletop posture:** chip is exposed, panel is up, a tablet
  or laptop shows the dashboard. Don't leave the controller
  unattended -- if a kid pulls a wire, the IPROPI endstop is the
  only safety net, and the IPROPI is a software safety net.
- **Demo path:** see `docs/demo_script.md`. Three tiers, pick
  based on visitor interest. Most are 30-second.
- **Handouts:** cut-list cards (50 max). If a visitor is going
  to build, point them at github.com/mokahlo/wattplot and the
  README's "Bring your own panel" path.
- **Trades.** "Have you done a solar project?" is the open
  question for makers. Most useful signal.

### 6 PM — teardown

- [ ] **Power down in reverse order.** Panel INA119 first,
      battery last. Don't leave the battery connected to a
      discharged panel overnight (it'll over-discharge and
      damage the cells; the Sunapex has low-voltage cutoff but
      it's still better to disconnect).
- [ ] **Pull the log file.** `tools/log_subscriber.py` will have
      rotated to a daily gz. Copy it to your backup USB.
- [ ] **Note what went wrong.** Anything that surprised you
      (sensor fell off, panel tilted unexpectedly, etc.) goes
      in a post-mortem commit.

## Recovery — when things go wrong

The Wattplot has one job at the booth: **show the live data**.
Everything else is bonus. Recovery priority:

### Recovery 1 — "panel is frozen / shows stale banner"

Cause: link down, watchdog will reconnect within 30 s. Just wait.

If still stale after 60 s:
1. `python tools/show_state.py` — does the chip respond at all?
2. If yes: refresh the browser tab. The `setSolenoidMode('Auto')`
   on the panel sometimes resets after a Cloudflare blip.
3. If no: check the chip (LEDs, USB power).
4. Last resort: `python tools/calibrate_watch.py` to force a
   state transition.

### Recovery 2 — "actuator won't fold"

This is the dangerous one. If the actuator is stuck driving
toward 90° with the firmware reporting `Controller State =
Normal`, kill the H-bridge by:
1. Unplug the actuator lead from the PCB (J5 / U5a). The
   mechanical stops will hold the panel.
2. Verify the panel is at a safe angle (ideally 0° / stowed).
3. Plug back in. The IPROPI endstop should re-detect on the next
   100 ms tick and the controller will re-enter Folding.

DO NOT try to override the firmware in this state. The
firmware's `n_safe + 0.3` hard fold IS the safety net — if it's
not folding, something deeper is wrong (firmware hung, watch the
log).

### Recovery 3 — "live panel unreachable from github.io"

Cause: Cloudflare Access session expired, or cloudflared
service died, or DNS hiccup.

1. Check the booth laptop can reach the wattplot directly:
   `python tools/show_state.py`
2. If that works, the issue is Cloudflare-edge-side. Try a
   different browser (Firefox / Safari / private window) to
   rule out a stuck session.
3. Last resort: show the panel via `localhost:8765/control.html`
   on the booth laptop. Stand up a sign "Booth laptop only".

### Recovery 4 — "Mosquitto died"

The control panel works without MQTT — the log streaming just
stops. Not a booth-killer.

1. Restart Mosquitto.
2. `python tools/log_subscriber.py` reconnects automatically.

### Recovery 5 — "the wind picks up"

If the booth is outdoors and winds exceed ~25 mph, manually
fold the panel to 0° via the panel UI. The auto-fold will
trigger if `i_safe` is set right; otherwise manual is safer
than betting on the controller.

## What NOT to do at the booth

- **Don't touch the YAML header comment without rebooting the
  chip.** The chip won't pick up the YAML change until you
  flash.
- **Don't run `esphome compile wattplot.yaml` on the booth
  laptop.** It pulls 200 MB of PlatformIO toolchain and takes
  ~10 minutes. Do this at home.
- **Don't change Cloudflare Access policy from the booth
  laptop.** If something goes wrong, you can't undo it remotely
  from a different network.
- **Don't post the booth's Wi-Fi SSID/password on Twitter.**
  Use a guest network if available.

## Post-faire (T+7 days)

- [ ] **Post-mortem commit** if anything broke. The most useful
      signals are:
      - chip wedged mid-day? → check `docs/_internal/esp32-s3.md`
        for the recovery procedure, file an issue
      - panel tilted under unexpected wind? → recalibrate
        endstop current threshold
      - public visitors confused by a term? → add to
        `docs/glossary.md`
      - control panel UI confusing? → screenshot, propose UX
        fix in a `feat:` PR
- [ ] **Trademark response.** Andrew Welch has the existing
      wattplot.com. If the coexistence request landed, no action.
      Otherwise follow `docs/_internal/RENAME_PLAN.md`.