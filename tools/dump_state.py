"""
Wattplot full state dump.

Connects to the wattplot's native API and prints every exposed
entity's name, type, and current value. Organized into sections
(power, sensors, actuator, solenoid, calibration, diagnostics).

Usage:
    python tools/dump_state.py [host] [encryption_key]
"""
import asyncio
import aioesphomeapi

HOST = "wattplot-controller.local"
KEY  = "cz0STvY6M+0ob9ydfsi28MDAL9b5P8VsmXsnZv3t7BU="

# (section title, [entity names to show in that section])
SECTIONS = [
    ("DIAGNOSTICS", [
        "Uptime", "Free Memory", "MCU Temperature",
        "WiFi Signal", "Last Event", "Controller State",
    ]),
    ("POWER", [
        "Battery Voltage", "Panel V", "Panel Current", "Panel Power",
        "Energy Today", "Energy Total", "Battery SOC",
    ]),
    ("ACTUATOR", [
        "Panel Tilt", "Commanded Tilt (°)",
        "Motor IPROPI Current", "Motor Current",
        "Actuator Bus V", "Actuator nFAULT",
    ]),
    ("SOLENOID", [
        "Solenoid Mode", "Solenoid Valve",
        "Solenoid IPROPI Current", "Solenoid nFAULT",
        "Solenoid Fault Alarm", "Solenoid On Time (s)",
        "Solenoid Budget (s)", "Solenoid Max On-Time (s)",
    ]),
    ("SENSORS", [
        "Panel Temperature", "Soil Temperature", "Canopy Air Temperature",
        "Soil Moisture", "Soil Moisture (raw V)",
    ]),
    ("CALIBRATION", [
        "Calibration In Progress", "Last Calibration (s)",
        "Last MAX Endstop Current", "Last ZERO Endstop Current",
        "Endstop Current Threshold (A)",
    ]),
    ("H-BRIDGE", [
        "H-bridge IN1", "H-bridge IN2", "H-bridge EN",
    ]),
    ("LIGHT", [
        "Status LED",
    ]),
]


def render_value(s):
    """Format a SensorState / BinarySensorState / SwitchState / etc."""
    if s is None:
        return "(no data)"
    v = s.state
    if v is None or (isinstance(v, float) and v != v):
        return "NaN"
    if isinstance(v, bool):
        return "TRUE" if v else "false"
    if isinstance(v, float):
        if abs(v) >= 100:
            return f"{v:.0f}"
        if abs(v) >= 10:
            return f"{v:.1f}"
        return f"{v:.3f}"
    return str(v)


async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else HOST
    key  = sys.argv[2] if len(sys.argv) > 2 else KEY

    api = aioesphomeapi.APIClient(host, 6053, noise_psk=key)
    await api.connect(login=True)
    info = await api.device_info()
    print(f"=== Wattplot full state dump ===")
    print(f"  device:   {info.name}")
    print(f"  mac:      {info.mac_address}")
    print(f"  sw:       {info.esphome_version}")
    print(f"  host:     {host}")
    print()

    entities, _ = await api.list_entities_services()
    by_key = {e.key: getattr(e, "name", "") for e in entities}
    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(2.5)

    # Walk through sections
    for title, names in SECTIONS:
        print(f"--- {title} ---")
        for name in names:
            k = next((kk for kk, nm in by_key.items() if nm == name), None)
            if k is None:
                print(f"  {name:<28} (not exposed)")
                continue
            s = states.get(k)
            v = render_value(s)
            print(f"  {name:<28} = {v}")
        print()

    # Tally: also list any entities we DIDN'T cover, so we know what's exposed
    covered = set()
    for _, names in SECTIONS:
        covered.update(names)
    extras = sorted(set(by_key.values()) - covered)
    if extras:
        print(f"--- OTHER EXPOSED ENTITIES ({len(extras)}) ---")
        for n in extras:
            k = by_key.get(n)
            s = states.get(k) if k is not None else None
            v = render_value(s)
            print(f"  {n:<40} = {v}")
        print()

    try:
        await api.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    import sys
    asyncio.run(main())
