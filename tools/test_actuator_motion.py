"""
Actuator motion + endstop test (live, with battery connected).

Drives the actuator extend and then retract. Samples IPROPI every
~100 ms through each direction. Auto-stops early on a current spike
that signals an endstop hit (peak above ENDSTOP_A for at least
SPIKE_MIN_MS consecutive samples). Reports baseline current, peak
current, time-to-spike, and a per-phase timeline.

Safety:
- The DRV8871's internal current limit is ~1.15 A typical. If we see
  IPROPI > 1.5 A sustained (i.e. > 3.0 A in motor current), we abort
  and turn the H-bridge off.
- Watch nFAULT — if it asserts, we abort immediately.

Usage:
    python test_actuator_motion.py [host] [encryption_key]
"""
import asyncio
import math
import sys
import time

import aioesphomeapi


HOST_DEFAULT = "wattplot-controller.local"
ENDSTOP_A = 0.80            # firmware's endstop_current_threshold
HARD_ABORT_A = 1.50         # anything above this, kill the H-bridge
PHASE_MAX_S = 7.0           # hard timeout per direction
SAMPLE_INTERVAL_S = 0.10
SPIKE_MIN_MS = 200          # need this many ms above ENDSTOP_A to count


async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else HOST_DEFAULT
    noise_psk = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Connecting to {host}:6053 ...")
    api = aioesphomeapi.APIClient(host, 6053, noise_psk=noise_psk)
    await api.connect(login=True)
    info = await api.device_info()
    print(f"Device: {info.name}  (MAC: {info.mac_address})\n")

    entities, _ = await api.list_entities_services()
    by_key = {e.key: getattr(e, "name", "") for e in entities}
    in1_key = next(k for k, n in by_key.items() if n == "H-bridge IN1")
    in2_key = next(k for k, n in by_key.items() if n == "H-bridge IN2")
    en_key = next(k for k, n in by_key.items() if n == "H-bridge EN")
    nFAULT_key = next(k for k, n in by_key.items() if n == "Actuator nFAULT")
    ipi_key = next(k for k, n in by_key.items() if n == "Motor IPROPI Current")
    bus_v_key = next(k for k, n in by_key.items() if n == "Actuator Bus V")

    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(1.0)  # let initial states arrive

    def ipi():
        s = states.get(ipi_key)
        return float(s.state) if s is not None and not getattr(s, "missing_state", False) else float("nan")

    def bus_v():
        s = states.get(bus_v_key)
        return float(s.state) if s is not None and not getattr(s, "missing_state", False) else float("nan")

    def nfl():
        s = states.get(nFAULT_key)
        return bool(s.state) if s is not None else None

    # Baseline
    print(f"  baseline   IPROPI = {ipi():.3f} A   nFAULT = {nfl()}   busV = {bus_v():.2f} V")
    print()

    async def run_phase(label, drive, max_s):
        """drive: callable() that turns on the H-bridge in one direction.
        Returns (peak_A, samples, hit_endstop_bool)."""
        print(f"=== {label} ===")
        peak = 0.0
        samples = []
        spike_started = None
        hit = False
        aborted = False
        t0 = time.monotonic()
        drive(True)
        try:
            while True:
                t = time.monotonic() - t0
                if t > max_s:
                    print(f"  timeout at {t:.2f} s, no endstop hit")
                    break
                await asyncio.sleep(SAMPLE_INTERVAL_S)
                v = ipi()
                bv = bus_v()
                nf = nfl()
                if not math.isfinite(v):
                    continue
                peak = max(peak, v)
                samples.append((t, v, bv, nf))
                tag = ""
                if v > HARD_ABORT_A:
                    tag = "  ** HARD ABORT (>1.5 A) **"
                    aborted = True
                if v >= ENDSTOP_A:
                    if spike_started is None:
                        spike_started = t
                    elif (t - spike_started) * 1000 >= SPIKE_MIN_MS:
                        tag = "  ** ENDSTOP HIT **"
                        hit = True
                else:
                    spike_started = None
                print(f"  t={t:5.2f}s  IPROPI={v:6.3f} A   busV={bv:5.2f} V   nFAULT={nf}{tag}")
                if aborted or hit:
                    break
                if nf is False:
                    print("  ** nFAULT ASSERTED — aborting **")
                    break
        finally:
            drive(False)
            # brief settle
            await asyncio.sleep(0.3)
            v_idle = ipi()
            print(f"  settled   IPROPI = {v_idle:.3f} A   nFAULT = {nfl()}")
            print()
        return peak, samples, hit or aborted

    # Make sure EN is on
    en_state = states.get(en_key)
    if en_state is not None and en_state.state is False:
        print("Enabling H-bridge EN ...")
        api.switch_command(key=en_key, state=True)
        await asyncio.sleep(0.2)

    # Extend
    def drive_extend(on):
        if on:
            api.switch_command(key=in2_key, state=False)
            api.switch_command(key=in1_key, state=True)
        else:
            api.switch_command(key=in1_key, state=False)

    peak_ext, samp_ext, hit_ext = await run_phase("EXTEND (IN1=ON)", drive_extend, PHASE_MAX_S)

    # pause
    await asyncio.sleep(1.0)

    # Retract
    def drive_retract(on):
        if on:
            api.switch_command(key=in1_key, state=False)
            api.switch_command(key=in2_key, state=True)
        else:
            api.switch_command(key=in2_key, state=False)

    peak_ret, samp_ret, hit_ret = await run_phase("RETRACT (IN2=ON)", drive_retract, PHASE_MAX_S)

    # Final idle
    await asyncio.sleep(0.5)
    print("=== Final idle ===")
    print(f"  IPROPI = {ipi():.3f} A   nFAULT = {nfl()}   busV = {bus_v():.2f} V")

    print()
    print("====== summary ======")
    print(f"  EXTEND    peak = {peak_ext:6.3f} A   endstop hit: {hit_ext}   samples: {len(samp_ext)}")
    print(f"  RETRACT   peak = {peak_ret:6.3f} A   endstop hit: {hit_ret}   samples: {len(samp_ret)}")

    if samp_ext:
        # find time to first sustained spike
        t0 = samp_ext[0][0]
        spike_started = None
        for t, v, *_ in samp_ext:
            if v >= ENDSTOP_A:
                if spike_started is None:
                    spike_started = t
                elif (t - spike_started) * 1000 >= SPIKE_MIN_MS:
                    print(f"  EXTEND    time-to-endstop = {spike_started - t0:.2f} s")
                    break
            else:
                spike_started = None
    if samp_ret:
        t0 = samp_ret[0][0]
        spike_started = None
        for t, v, *_ in samp_ret:
            if v >= ENDSTOP_A:
                if spike_started is None:
                    spike_started = t
                elif (t - spike_started) * 1000 >= SPIKE_MIN_MS:
                    print(f"  RETRACT   time-to-endstop = {spike_started - t0:.2f} s")
                    break
            else:
                spike_started = None

    try:
        api.unsubscribe_states()
    except Exception:
        pass
    try:
        await api.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
