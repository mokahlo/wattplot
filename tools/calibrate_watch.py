"""
Run the actuator calibration while logging IPROPI current at 100ms.
Lets us see exactly what the firmware sees during the calibration —
helpful for debugging the threshold and the endstop detection.
"""
import asyncio
import sys
import time

import aioesphomeapi


HOST = "wattplot-controller.local"
KEY = "cz0STvY6M+0ob9ydfsi28MDAL9b5P8VsmXsnZv3t7BU="

CAL_BTN_KEY       = 3817736166   # Calibrate Actuator
CAL_RUNNING_KEY   = 2872278387   # Calibration In Progress
CAL_MAX_KEY       = 516998126    # Last MAX Endstop Current
CAL_ZERO_KEY      = 1314387666   # Last ZERO Endstop Current
THRESH_KEY        = 2893581024   # Endstop Current Threshold
IPI_KEY           = 587565470    # Motor IPROPI Current
IN1_KEY           = 970142872    # H-bridge IN1
IN2_KEY           = 970142875    # H-bridge IN2
NFAULT_KEY        = 1853948805   # Actuator nFAULT


async def main():
    api = aioesphomeapi.APIClient(HOST, 6053, noise_psk=KEY)
    await api.connect(login=True)

    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(1.0)

    print("=== current state ===")
    print(f"  threshold        = {states.get(THRESH_KEY).state if states.get(THRESH_KEY) else '?'} A")
    print(f"  IN1              = {states.get(IN1_KEY).state if states.get(IN1_KEY) else '?'}")
    print(f"  IN2              = {states.get(IN2_KEY).state if states.get(IN2_KEY) else '?'}")
    print(f"  last MAX current = {states.get(CAL_MAX_KEY).state if states.get(CAL_MAX_KEY) else '?'} A")
    print(f"  last ZERO current= {states.get(CAL_ZERO_KEY).state if states.get(CAL_ZERO_KEY) else '?'} A")
    print()

    # Optional threshold override (default: leave the chip's setting alone)
    forced = None
    if len(sys.argv) > 1:
        try:
            forced = float(sys.argv[1])
        except ValueError:
            pass
    if forced is not None:
        print(f"Setting endstop threshold to {forced} A (overriding current)...")
        api.number_command(key=THRESH_KEY, state=forced)
        await asyncio.sleep(0.5)
        print(f"  new threshold    = {states.get(THRESH_KEY).state} A\n")
    else:
        print(f"Using current threshold ({states.get(THRESH_KEY).state} A).\n")

    print("=== before calibration ===")
    print(f"  running = {states.get(CAL_RUNNING_KEY).state}")
    print(f"  ipi     = {states.get(IPI_KEY).state:.3f} A")
    print()

    print("Triggering calibration ...")
    t0 = time.monotonic()
    api.button_command(key=CAL_BTN_KEY)

    peak_ipi = 0.0
    spike_above_thresh_ms = 0
    last_print = t0
    while True:
        t = time.monotonic() - t0
        if t > 60:
            print("  timeout, aborting")
            break
        running = states.get(CAL_RUNNING_KEY)
        ipi = states.get(IPI_KEY)
        in1 = states.get(IN1_KEY)
        in2 = states.get(IN2_KEY)
        nfl = states.get(NFAULT_KEY)
        if ipi is not None and ipi.state is not None:
            v = float(ipi.state)
            if v == v:  # not nan
                peak_ipi = max(peak_ipi, v)
                thresh = float(states.get(THRESH_KEY).state)
                if v > thresh:
                    spike_above_thresh_ms += 100
        # print every 200 ms
        if t - (last_print - t0) > 0.2:
            last_print = time.monotonic()
            ipi_v = float(ipi.state) if ipi and ipi.state is not None and ipi.state == ipi.state else float('nan')
            in1_v = in1.state if in1 and in1.state is not None else None
            in2_v = in2.state if in2 and in2.state is not None else None
            nfl_v = nfl.state if nfl and nfl.state is not None else None
            run_v = running.state if running and running.state is not None else None
            print(f"  t={t:5.1f}s  ipi={ipi_v:5.2f}A  IN1={in1_v}  IN2={in2_v}  nF={nfl_v}  run={run_v}")
        if running is not None and running.state is False and t > 1.5:
            print(f"  t={t:5.1f}s  calibration finished, settling 1s")
            await asyncio.sleep(1.0)
            break
        await asyncio.sleep(0.1)

    print()
    print("=== after calibration ===")
    print(f"  peak IPROPI during run: {peak_ipi:.2f} A")
    print(f"  ms above threshold:    {spike_above_thresh_ms}")
    print(f"  last MAX current = {states.get(CAL_MAX_KEY).state} A")
    print(f"  last ZERO current= {states.get(CAL_ZERO_KEY).state} A")
    print(f"  ipi now          = {states.get(IPI_KEY).state} A")

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
