"""Show the current controller/actuator state."""
import asyncio
import aioesphomeapi

from _secrets import get_api_key

HOST = "wattplot-controller.local"
KEY  = get_api_key()

LABELS = [
    "Controller State",
    "Commanded Tilt (\u00b0)",
    "Panel Tilt",
    "Motor IPROPI Current",
    "Calibration In Progress",
    "Last Calibration (s)",
    "Last MAX Endstop Current",
    "Last ZERO Endstop Current",
]


async def main():
    api = aioesphomeapi.APIClient(HOST, 6053, noise_psk=KEY)
    await api.connect(login=True)
    entities, _ = await api.list_entities_services()
    by_key = {e.key: getattr(e, "name", "") for e in entities}
    wanted = {n: next((k for k, nm in by_key.items() if nm == n), None) for n in LABELS}

    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(1.5)

    for label in LABELS:
        key = wanted[label]
        s = states.get(key)
        if s is None:
            print(f"  {label:<28} (no data)")
            continue
        v = s.state
        if hasattr(s, "missing_state") and s.missing_state:
            print(f"  {label:<28} (missing)")
        elif isinstance(v, bool):
            print(f"  {label:<28} = {v}")
        elif isinstance(v, float):
            print(f"  {label:<28} = {v:.3f}")
        else:
            print(f"  {label:<28} = {v}")

    try:
        await api.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())

