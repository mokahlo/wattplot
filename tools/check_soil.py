"""Check soil moisture sensor readings."""
import asyncio
import aioesphomeapi

HOST = "wattplot-controller.local"
KEY  = "cz0STvY6M+0ob9ydfsi28MDAL9b5P8VsmXsnZv3t7BU="


async def main():
    api = aioesphomeapi.APIClient(HOST, 6053, noise_psk=KEY)
    await api.connect(login=True)
    entities, _ = await api.list_entities_services()
    by_key = {e.key: getattr(e, "name", "") for e in entities}
    raw_key = next((k for k, n in by_key.items() if n == "Soil Moisture (raw V)"), None)
    pct_key = next((k for k, n in by_key.items() if n == "Soil Moisture"), None)

    print(f"  Soil Moisture (raw V) key: {raw_key}")
    print(f"  Soil Moisture        key: {pct_key}")

    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(2.5)

    raw = states.get(raw_key)
    pct = states.get(pct_key)

    if raw:
        print(f"\n  Raw state object: {type(raw).__name__}")
        print(f"  Raw state: {raw.state}")
        print(f"  Raw missing_state: {getattr(raw, 'missing_state', None)}")
    else:
        print("\n  Raw state: (no data)")

    if pct:
        print(f"  Pct state: {pct.state}")

    # Take 3 samples over 1.5 s to see the live readings
    print("\n--- 3 samples (raw V / pct) ---")
    for _ in range(3):
        await asyncio.sleep(0.5)
        r = states.get(raw_key)
        p = states.get(pct_key)
        rv = r.state if r else None
        pv = p.state if p else None
        miss = getattr(r, "missing_state", None) if r else None
        print(f"  raw={rv}  missing={miss}  pct={pv}")

    try:
        await api.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
