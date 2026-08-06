"""Check the three DS18B20 temperature sensors on the wattplot."""
import asyncio
import aioesphomeapi

HOST = "wattplot-controller.local"
KEY  = "cz0STvY6M+0ob9ydfsi28MDAL9b5P8VsmXsnZv3t7BU="


async def main():
    api = aioesphomeapi.APIClient(HOST, 6053, noise_psk=KEY)
    await api.connect(login=True)
    entities, _ = await api.list_entities_services()
    by_key = {e.key: getattr(e, "name", "") for e in entities}
    wanted = {
        "Panel Temperature":       next((k for k, n in by_key.items() if n == "Panel Temperature"), None),
        "Soil Temperature":        next((k for k, n in by_key.items() if n == "Soil Temperature"), None),
        "Canopy Air Temperature":  next((k for k, n in by_key.items() if n == "Canopy Air Temperature"), None),
    }

    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    print("Polling for 4 seconds (DS18B20 takes ~1 s to convert)...")
    await asyncio.sleep(4.0)

    print()
    for label, key in wanted.items():
        s = states.get(key)
        if s is None:
            print(f"  {label:<28} (no data)")
            continue
        v = s.state
        if v is None or (isinstance(v, float) and v != v):  # NaN check
            print(f"  {label:<28} = NaN  (sensor not on bus)")
        elif isinstance(v, float):
            print(f"  {label:<28} = {v:.2f} \u00b0C")
        else:
            print(f"  {label:<28} = {v}")

    try:
        await api.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
