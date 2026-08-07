"""
Quick solenoid drive test.

Drives the solenoid H-bridge (U5b) in 3 phases:
  0. idle (valve off)         - baseline readings
  1. valve ON, 1 second       - watch IPROPI + nFAULT
  2. valve OFF, 500ms settle  - recovery

Sets Solenoid Mode to Manual first so we can drive the valve switch
directly. Logs all relevant sensors.
"""
import asyncio
import aioesphomeapi

HOST = "wattplot-controller.local"
KEY  = "cz0STvY6M+0ob9ydfsi28MDAL9b5P8VsmXsnZv3t7BU="

# entity keys (stable across firmware)
SOL_MODE_KEY   = 3792266734  # Solenoid Mode (Off / Auto / Manual)
SOL_VALVE_KEY  = 4222604611  # Solenoid Valve (switch)
SOL_IPI_KEY    = 182416010   # Solenoid IPROPI Current
SOL_NFAULT_KEY = 3413365401  # Solenoid nFAULT
SOL_ALARM_KEY  = 1057942567  # Solenoid Fault Alarm
SOL_BUDGET_KEY = 10022656    # Solenoid Budget (s)
SOL_ONTIME_KEY = 1393952356  # Solenoid On Time (s)


async def main():
    api = aioesphomeapi.APIClient(HOST, 6053, noise_psk=KEY)
    await api.connect(login=True)
    print(f"Connected to {HOST}")

    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(1.0)

    def get(key, fmt=None):
        s = states.get(key)
        if s is None:
            return None
        if hasattr(s, "missing_state") and s.missing_state:
            return None
        v = s.state
        if fmt:
            return fmt(v)
        return v

    def sel(key):
        s = states.get(key)
        if s is None:
            return None
        return getattr(s, "state", None) or getattr(s, "current_option", lambda: "?")()

    def set_sel(key, option):
        api.select_command(key=key, state=option)

    def set_sw(key, on):
        api.switch_command(key=key, state=on)

    # Snapshot helper
    def snapshot(label):
        print(f"  [{label}]")
        print(f"    Solenoid Mode     = {sel(SOL_MODE_KEY)}")
        print(f"    Solenoid Valve    = {get(SOL_VALVE_KEY)}")
        print(f"    Solenoid IPROPI   = {get(SOL_IPI_KEY, lambda v: f'{v:.3f} A')}")
        print(f"    Solenoid nFAULT   = {get(SOL_NFAULT_KEY)}")
        print(f"    Solenoid Alarm    = {get(SOL_ALARM_KEY)}")
        print(f"    On Time (s)       = {get(SOL_ONTIME_KEY, lambda v: f'{v:.2f}')}")
        print(f"    Budget (s)        = {get(SOL_BUDGET_KEY, lambda v: f'{v:.1f}')}")
        print()

    # Phase 0: baseline
    print("\n=== Phase 0: idle (valve off) ===")
    snapshot("baseline")

    # Switch to Manual mode
    if sel(SOL_MODE_KEY) != "Manual":
        print("Setting Solenoid Mode to Manual ...")
        set_sel(SOL_MODE_KEY, "Manual")
        await asyncio.sleep(0.3)
        print(f"  Mode now: {sel(SOL_MODE_KEY)}\n")

    # Phase 1: valve on
    print("=== Phase 1: valve ON (1.0 s) ===")
    snapshot("before ON")
    set_sw(SOL_VALVE_KEY, True)
    t0 = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - t0 < 1.0:
        await asyncio.sleep(0.1)
        ipi = get(SOL_IPI_KEY)
        nf = get(SOL_NFAULT_KEY)
        al = get(SOL_ALARM_KEY)
        on = get(SOL_ONTIME_KEY)
        if ipi is not None:
            print(f"    t={asyncio.get_event_loop().time()-t0:4.2f}s  ipi={ipi:.3f} A  nF={nf}  alarm={al}  onTime={on:.2f}s")
    snapshot("during ON")

    # Phase 2: valve off
    print("=== Phase 2: valve OFF (0.5 s settle) ===")
    set_sw(SOL_VALVE_KEY, False)
    await asyncio.sleep(0.5)
    snapshot("after OFF")

    # Restore Solenoid Mode to Off (safe default)
    set_sel(SOL_MODE_KEY, "Off")
    await asyncio.sleep(0.3)
    print(f"Restored Solenoid Mode to: {sel(SOL_MODE_KEY)}")

    try:
        await api.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
