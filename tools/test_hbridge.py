"""
Actuator H-bridge logic test.

Drives H-bridge IN1/IN2 in 4 phases (idle, fwd, rev, idle), each 300ms,
and logs the state of all relevant sensors before/during/after.

NO motor is connected. With battery disconnected, VM=0V at the DRV8871,
so even with IN1/IN2 driven, no current flows and no motion happens.
This is a logic-level test only — it confirms the firmware can drive
the GPIOs and the DRV8871 chip is responding on its logic inputs.

Usage:
    python test_hbridge.py [host] [encryption_key]
"""
import asyncio
import sys

import aioesphomeapi


# Tunables
PHASE_MS = 300
HOST_DEFAULT = "wattplot-controller.local"


async def wait_states(api, ms):
    """Sleep while states stream in."""
    await asyncio.sleep(ms / 1000.0)


async def snapshot(states, keys, label):
    print(f"  [{label}]")
    for k, n in keys:
        v = states.get(k)
        if v is None:
            print(f"    {n:<28} (no data)")
            continue
        s = v.state
        if isinstance(s, float):
            print(f"    {n:<28} = {s:.3f}")
        else:
            print(f"    {n:<28} = {s}")


async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else HOST_DEFAULT
    noise_psk = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Connecting to {host}:6053 ...")
    api = aioesphomeapi.APIClient(host, 6053, noise_psk=noise_psk)
    await api.connect(login=True)

    info = await api.device_info()
    print(f"Device: {info.name}  (MAC: {info.mac_address})")

    # Build key->name map
    entities, _ = await api.list_entities_services()
    by_key = {e.key: getattr(e, "name", "") for e in entities}

    # Resolve the switch keys we need
    in1_key = next(k for k, n in by_key.items() if n == "H-bridge IN1")
    in2_key = next(k for k, n in by_key.items() if n == "H-bridge IN2")
    en_key = next(k for k, n in by_key.items() if n == "H-bridge EN")
    print(f"  H-bridge IN1 key: {in1_key}")
    print(f"  H-bridge IN2 key: {in2_key}")
    print(f"  H-bridge EN  key: {en_key}")

    # Start state subscription
    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(1.0)  # let initial states arrive

    # Make sure H-bridge EN is on so the IN1/IN2 bits actually take effect
    # (the DRV8871 datasheet says EN tied high, but ESPHome still exposes the
    #  switch — turn it ON to be safe).
    if states.get(en_key) is not None and states[en_key].state is False:
        print("\nEnabling H-bridge EN ...")
        api.switch_command(key=en_key, state=True)
        await wait_states(api, 200)

    # Keys we want to show in the snapshot
    snapshot_keys = [
        (in1_key, "H-bridge IN1"),
        (in2_key, "H-bridge IN2"),
        (en_key, "H-bridge EN"),
        (1853948805, "Actuator nFAULT"),
        (3413365401, "Solenoid nFAULT"),
        (587565470, "Motor IPROPI Current"),
        (182416010, "Solenoid IPROPI Current"),
        (1531162880, "Actuator Bus V"),
        (1965930050, "Motor Current (INA219)"),
    ]

    print("\n=== Phase 0: idle ===")
    await snapshot(states, snapshot_keys, "before")
    await wait_states(api, 200)

    print("\n=== Phase 1: IN1=HIGH, IN2=LOW (forward direction) ===")
    api.switch_command(key=in2_key, state=False)
    api.switch_command(key=in1_key, state=True)
    await wait_states(api, PHASE_MS)
    await snapshot(states, snapshot_keys, "during fwd")

    print("\n=== Phase 2: IN1=LOW, IN2=HIGH (reverse direction) ===")
    api.switch_command(key=in1_key, state=False)
    api.switch_command(key=in2_key, state=True)
    await wait_states(api, PHASE_MS)
    await snapshot(states, snapshot_keys, "during rev")

    print("\n=== Phase 3: coast (IN1=LOW, IN2=LOW) ===")
    api.switch_command(key=in2_key, state=False)
    await wait_states(api, PHASE_MS)
    await snapshot(states, snapshot_keys, "after")

    # Force a fresh read so the final values are settled
    await wait_states(api, 200)
    print("\n=== Final settled ===")
    await snapshot(states, snapshot_keys, "settled")

    try:
        api.unsubscribe_states()
    except Exception:
        pass
    try:
        await api.disconnect()
    except Exception:
        pass
    print("\nDone. Battery still disconnected — no motor current should have flowed.")


if __name__ == "__main__":
    asyncio.run(main())
