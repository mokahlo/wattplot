"""
Quick state dump for the wattplot ESPHome device.

Connects via the native API (port 6053), lists all entities and their
current values, and prints them. Read-only — does not write anything.

Usage:
    python check_wattplot_state.py [host] [encryption_key]

Default host: wattplot-controller.local
"""
import asyncio
import sys

import aioesphomeapi


async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "wattplot-controller.local"
    noise_psk = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Connecting to {host}:6053 ...")
    api = aioesphomeapi.APIClient(host, 6053, noise_psk=noise_psk)
    await api.connect(login=True)
    info = await api.device_info()
    print(f"\nDevice:  {info.name}  (model: {info.model}, sw: {info.esphome_version})")
    print(f"  MAC:   {info.mac_address}")
    print(f"  Board: {getattr(info, 'board', '?')}")

    # List entities by type
    entities, _ = await api.list_entities_services()
    print(f"\nEntities ({len(entities)} total):")

    sensors = []
    binary_sensors = []
    switches = []
    others = []
    for e in entities:
        key = getattr(e, "key", "") or ""
        name = getattr(e, "name", "") or ""
        if e.__class__.__name__ == "SensorInfo":
            sensors.append((key, name))
        elif e.__class__.__name__ == "BinarySensorInfo":
            binary_sensors.append((key, name))
        elif e.__class__.__name__ == "SwitchInfo":
            switches.append((key, name))
        else:
            others.append((e.__class__.__name__, key, name))

    print(f"\nSensors ({len(sensors)}):")
    for k, n in sensors:
        print(f"  {k:<35} {n}")
    print(f"\nBinary sensors ({len(binary_sensors)}):")
    for k, n in binary_sensors:
        print(f"  {k:<35} {n}")
    print(f"\nSwitches ({len(switches)}):")
    for k, n in switches:
        print(f"  {k:<35} {n}")
    if others:
        print(f"\nOthers ({len(others)}):")
        for cls, k, n in others:
            print(f"  [{cls}]  {k:<30} {n}")

    # Subscribe to all states for 3 seconds
    print("\n--- current states (3s subscription) ---")
    state_by_key = {}

    def on_state(state):
        state_by_key[state.key] = state

    api.subscribe_states(on_state)
    try:
        await asyncio.sleep(3.0)
    finally:
        try:
            api.unsubscribe_states()
        except Exception:
            pass
    try:
        await api.disconnect()
    except Exception:
        pass

    if not state_by_key:
        print("  (no states received — check if device is alive)")
        return

    for k, n in sensors:
        s = state_by_key.get(k)
        if s is None:
            print(f"  {k:<35} (no data)")
            continue
        v = getattr(s, "state", "?")
        miss = " missing" if getattr(s, "missing_state", False) else ""
        print(f"  {k:<35} = {v}{miss}")
    for k, n in binary_sensors:
        s = state_by_key.get(k)
        if s is None:
            print(f"  {k:<35} (no data)")
            continue
        v = getattr(s, "state", "?")
        print(f"  {k:<35} = {v}")
    for k, n in switches:
        s = state_by_key.get(k)
        if s is None:
            print(f"  {k:<35} (no data)")
            continue
        v = getattr(s, "state", "?")
        print(f"  {k:<35} = {v}")


if __name__ == "__main__":
    asyncio.run(main())
