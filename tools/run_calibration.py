"""
Trigger the actuator_calibrate script via the OTA-over-ESPHome button
and watch progress: 'Calibration In Progress' flips True, then back
to False at the end. Polls the new 'Last MAX Endstop Current' and
'Last ZERO Endstop Current' sensors as they fill in.
"""
import asyncio
import sys

import aioesphomeapi

from _secrets import get_api_key


HOST = "wattplot-controller.local"
KEY = get_api_key()

CAL_BTN_KEY     = 3817736166  # Calibrate Actuator
CAL_RUNNING_KEY = 2872278387  # Calibration In Progress (binary)
CAL_AGE_KEY     = 2252638468  # Last Calibration (s)
CAL_MAX_KEY     = 516998126   # Last MAX Endstop Current (A)
CAL_ZERO_KEY    = 1314387666  # Last ZERO Endstop Current (A)


async def main():
    api = aioesphomeapi.APIClient(HOST, 6053, noise_psk=KEY)
    await api.connect(login=True)
    info = await api.device_info()
    print(f"Device: {info.name}  (MAC: {info.mac_address})  sw: {info.esphome_version}\n")

    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(1.0)

    def get(key):
        s = states.get(key)
        if s is None:
            return None
        v = s.state
        if hasattr(s, "missing_state") and s.missing_state:
            return None
        return v

    def fmt(key, label, unit=""):
        v = get(key)
        if v is None:
            return f"{label:<30} (no data)"
        if isinstance(v, bool):
            return f"{label:<30} = {v}"
        if isinstance(v, float):
            return f"{label:<30} = {v:.3f}{unit}"
        return f"{label:<30} = {v}{unit}"

    print("=== before calibration ===")
    print(fmt(CAL_RUNNING_KEY, "Calibration In Progress"))
    print(fmt(CAL_AGE_KEY, "Last Calibration (s)", "s"))
    print(fmt(CAL_MAX_KEY, "Last MAX Endstop Current", " A"))
    print(fmt(CAL_ZERO_KEY, "Last ZERO Endstop Current", " A"))
    print()

    print(f"Pressing 'Calibrate Actuator' button at t=0 ...")
    api.button_command(key=CAL_BTN_KEY)

    import time
    t0 = time.monotonic()
    last_age = None
    while True:
        t = time.monotonic() - t0
        running = get(CAL_RUNNING_KEY)
        age = get(CAL_AGE_KEY)
        if t > 60:
            print(f"  t={t:5.1f}s  TIMEOUT (>60s), aborting wait")
            break
        if running is False and t > 1.0:
            # Just transitioned to false → calibration finished
            print(f"  t={t:5.1f}s  Calibration finished, settling for 1s ...")
            await asyncio.sleep(1.0)
            break
        if t % 1 < 0.15:
            print(f"  t={t:5.1f}s  running={running}  age={age}s")
        await asyncio.sleep(0.1)

    print()
    print("=== after calibration ===")
    print(fmt(CAL_RUNNING_KEY, "Calibration In Progress"))
    print(fmt(CAL_AGE_KEY, "Last Calibration (s)", "s"))
    print(fmt(CAL_MAX_KEY, "Last MAX Endstop Current", " A"))
    print(fmt(CAL_ZERO_KEY, "Last ZERO Endstop Current", " A"))

    max_a = get(CAL_MAX_KEY)
    zero_a = get(CAL_ZERO_KEY)
    if isinstance(max_a, (int, float)) and isinstance(zero_a, (int, float)):
        if max_a > 0 and zero_a > 0:
            delta = abs(max_a - zero_a)
            print(f"\n  asymmetry: |MAX − ZERO| = {delta:.3f} A")
            if delta > 0.30:
                print("  ⚠ large asymmetry — one endstop is significantly stiffer than the other")
            elif delta > 0.10:
                print("  moderate asymmetry — normal for a real actuator")
            else:
                print("  ✓ symmetric — both endstops feel about the same")

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
