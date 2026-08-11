"""
Quick demo: set the wattplot to Normal mode and command a tilt.
Verifies the manual control path works through the API.
"""
import asyncio
import aioesphomeapi

from _secrets import get_api_key

HOST = "wattplot-controller.local"
KEY  = get_api_key()


async def main():
    api = aioesphomeapi.APIClient(HOST, 6053, noise_psk=KEY)
    await api.connect(login=True)
    entities, _ = await api.list_entities_services()
    by_key = {e.key: getattr(e, "name", "") for e in entities}
    state_key = next(k for k, n in by_key.items() if n == "Controller State")
    tilt_key  = next(k for k, n in by_key.items() if n == "Commanded Tilt (\u00b0)")

    states = {}

    def on_state(s):
        states[s.key] = s

    api.subscribe_states(on_state)
    await asyncio.sleep(1.0)

    cs = states.get(state_key)
    ct = states.get(tilt_key)
    cur_state = getattr(cs, "state", None) or getattr(cs, "current_option", lambda: "?")()
    cur_tilt = ct.state if ct else "?"
    print(f"  current state:  {cur_state}")
    print(f"  current tilt:   {cur_tilt} deg")

    print("\nSetting state to Normal ...")
    api.select_command(key=state_key, state="Normal")
    await asyncio.sleep(0.5)
    cs = states.get(state_key)
    print(f"  state now:      {getattr(cs, 'state', None) or getattr(cs, 'current_option', lambda: '?')()}")

    print("Setting commanded tilt to 20 deg ...")
    api.number_command(key=tilt_key, state=20.0)
    await asyncio.sleep(0.5)
    ct = states.get(tilt_key)
    print(f"  tilt now:       {ct.state if ct else '?'} deg")

    print("\nThe 1 Hz control loop should start driving the actuator in <= 1 s.")
    print("Watch 'Motor IPROPI Current' on the web UI to see the motor spin up.")
    try:
        await api.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
