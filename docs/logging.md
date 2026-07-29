# Wattplot Logging — v2.5

## Overview

The Wattplot firmware streams **all ESPHome log lines to a rotating
text file on your PC** over MQTT. This gives you a persistent, greppable
history of everything the controller has done — waterings, fold events,
MPPT decisions, errors — without needing Home Assistant or a cloud
service.

The pipeline is:

```
ESP32 (firmware)  ──MQTT──>  Mosquitto broker  ──MQTT──>  log_subscriber.py  ──write──>  logs/wattplot.log
```

- **ESP32** publishes every log line (DEBUG, INFO, WARN, ERROR) to MQTT
  topic `wattplot/log`
- **Mosquitto** is a tiny local MQTT broker (free, runs on Windows/Mac/Linux)
- **log_subscriber.py** is a small Python script that subscribes and writes
  each line to a daily-rotated, gzipped log file in `./logs/`

**No internet, no cloud, no HA required.** All traffic stays on your home
LAN.

---

## Setup (one time, ~10 minutes)

### 1. Install Mosquitto (MQTT broker)

**Windows:**
```powershell
# Easiest: download the Mosquitto installer from
# https://mosquitto.org/download/
# Install with default options. Note the install path.

# Or via winget (if you have it):
winget install mosquitto
```

**Mac:**
```bash
brew install mosquitto
brew services start mosquitto
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install mosquitto
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Default port: `1883`. Default config: allows anonymous connections on
localhost only. If you want password protection (recommended for any
non-localhost setup), see the Mosquitto docs.

**Quick smoke test** (in one terminal, subscribe):
```bash
mosquitto_sub -h localhost -p 1883 -t "wattplot/#" -v
```

In another terminal, publish a test message:
```bash
mosquitto_pub -h localhost -p 1883 -t "wattplot/test" -m "hello"
```

If you see `wattplot/test hello` in the first terminal, Mosquitto works.

### 2. Create a Wattplot MQTT user (recommended)

```bash
# Stop the broker
sudo systemctl stop mosquitto   # Linux
# or kill the Windows service via Services panel

# Edit the password file (create if it doesn't exist)
sudo nano /etc/mosquitto/passwd
# Add one line:  wattplot:YOUR_CHOSEN_PASSWORD

# Hash the password file
sudo mosquitto_passwd -U /etc/mosquitto/passwd

# Restart
sudo systemctl start mosquitto
```

For Windows, the Mosquitto docs have a different procedure but the
principle is the same: create a password file, set `password_file` in
`mosquitto.conf`, restart the service.

### 3. Configure ESPHome secrets

Edit `firmware/secrets.yaml` (copy from `secrets.yaml.example` if you
haven't yet) and add:

```yaml
mqtt_broker: "192.168.1.10"       # IP of the PC running Mosquitto
                                   # (use 127.0.0.1 if same PC as ESPHome)
mqtt_username: "wattplot"
mqtt_password: "YOUR_CHOSEN_PASSWORD"
```

If you're using anonymous (no auth), just set:
```yaml
mqtt_broker: "192.168.1.10"
mqtt_username: ""
mqtt_password: ""
```

And in the firmware YAML, comment out the `username`/`password` lines in
the `mqtt:` block, or set them to empty.

### 4. Flash the firmware

```bash
cd firmware
esphome run wattplot.yaml
```

If you only want to verify the MQTT config compiles without flashing:
```bash
esphome config wattplot.yaml
```

### 5. Install the log subscriber dependencies

```bash
pip install -r requirements.txt
# or just:
pip install paho-mqtt>=2.0
```

### 6. Start the log subscriber

```bash
# From the repo root:
python tools/log_subscriber.py --broker 192.168.1.10 --user wattplot --password YOUR_PASSWORD

# Or anonymous:
python tools/log_subscriber.py --broker 192.168.1.10 --no-auth
```

You should see:
```
[boot] Wattplot log subscriber
[boot]   broker    = 192.168.1.10:1883
[boot]   user      = wattplot
[boot]   topic     = wattplot/#
[boot]   log dir   = C:\dev\wattplot\logs
[boot]   keep days = 30
[mqtt] connected to 192.168.1.10:1883
[mqtt] subscribed to wattplot/#
```

When the ESP32 boots, you'll start seeing log lines like:
```
2026-07-29 09:00:00  [wattplot/log]  [09:00:00][D][wifi:373]: WiFi Connected...
2026-07-29 09:00:00  [wattplot/log]  [09:00:00][I][app:029]: Running through callback...
2026-07-29 09:00:05  [wattplot/log]  [09:00:05][I][mppt:42]: MPPT step: V=17.2V, I=0.42A, P=7.2W
2026-07-29 09:00:10  [wattplot/log]  [09:00:10][D][imu:218]: ax=0.12 ay=0.98 az=0.05, tilt=2.3°
```

**Run as a background service** (so it survives reboot):

**Windows** (Task Scheduler):
1. Open Task Scheduler → "Create Task"
2. General tab: name "Wattplot Log Subscriber", check "Run whether user
   is logged in or not"
3. Triggers: "At system startup"
4. Actions: Start a program = `python`, arguments = `tools\log_subscriber.py
   --broker 192.168.1.10 --user wattplot --password YOUR_PASSWORD`
   (with "Start in" set to the repo path)

**Mac/Linux** (systemd):
```ini
# /etc/systemd/system/wattplot-log.service
[Unit]
Description=Wattplot MQTT log subscriber
After=network.target

[Service]
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/wattplot
ExecStart=/usr/bin/python3 tools/log_subscriber.py --broker 192.168.1.10 --user wattplot --password YOUR_PASSWORD
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now wattplot-log.service
```

---

## Log file format

`logs/wattplot.log` is plain text, one line per MQTT message:

```
2026-07-29 09:00:00  [wattplot/log]  [09:00:00][D][wifi:373]: WiFi Connected...
2026-07-29 09:00:00  [wattplot/log]  [09:00:00][I][app:029]: Running through callback...
2026-07-29 09:00:05  [wattplot/log]  [09:00:05][I][mppt:42]: MPPT step: V=17.2V, I=0.42A, P=7.2W
2026-07-29 09:00:10  [wattplot/log]  [09:00:10][I][watering:87]: Watered: moisture=27%, events_today=1
2026-07-29 09:00:30  [wattplot/log]  [09:00:30][W][solenoid:102]: Safety watchdog killed solenoid after 30s
2026-07-29 09:01:00  [wattplot/log]  [wattplot/status]  online
2026-07-29 09:01:00  [wattplot/log]  [wattplot/log_subscriber/status]  online
```

The first column is the wall-clock time on the PC (subscriber side).
The `[wattplot/log]` topic is the ESP32's logger output. The
`[wattplot/status]` topic is the LWT (last will) — `online` when ESP32
boots, `offline` if it disconnects unexpectedly (great for catching
WiFi drops).

### Log level tags

ESPHome uses standard log levels:

| Tag | When to expect |
|---|---|
| `[D]` DEBUG | Verbose; every sensor read, every I2C transaction. Useful when debugging but very chatty. |
| `[I]` INFO | Normal operation; MPPT steps, watering events, state transitions. Default level. |
| `[W]` WARN | Something off but recoverable; sensor read failed, retry happening. |
| `[E]` ERROR | Failed operation; usually followed by the device going into safe mode. |

To reduce log volume, change `logger.level` in the firmware to `INFO`
(default) or `WARN` (quiet). The MQTT log level is set separately under
`logger.logs.mqtt.log.level`.

---

## Useful greps

```bash
# All watering events
grep "Watered:" logs/wattplot.log

# All safety interventions (the interesting ones)
grep -E "WARN|ERROR" logs/wattplot.log

# All MPPT activity
grep "MPPT step" logs/wattplot.log

# When did the panel last fold?
grep -E "Folding|Locked" logs/wattplot.log | tail -20

# WiFi disconnections
grep "wattplot/status" logs/wattplot.log

# All sensor values at a specific time (e.g., 9:00 AM today)
grep "2026-07-29 09:00:" logs/wattplot.log
```

---

## File rotation

`log_subscriber.py` rotates the log file at midnight each day:

- **Current day:** `logs/wattplot.log` (always the active file, append)
- **Yesterday:** `logs/wattplot.2026-07-28.log` (briefly, then gzipped)
- **Older:** `logs/wattplot.2026-07-27.log.gz` (gzipped to save space)
- **Default retention:** 30 days (configurable with `--keep-days N`)

At 1 INFO line per second from a busy ESP32, a single day is ~5 MB
plaintext, ~1 MB gzipped. 30 days = ~30 MB. Fits on any PC.

---

## Troubleshooting

**"Connection refused" when subscriber starts**
- Mosquitto isn't running, or is on a different port. Check with
  `mosquitto_pub -h YOUR_BROKER -p 1883 -t test -m "hi"`.

**No log lines appearing, but ESP32 is online**
- ESPHome's MQTT log level is set higher than the log lines you want
  to see. Set `logger.logs.mqtt.log.level: DEBUG` in the firmware.
- Wrong MQTT topic — the ESP32 is publishing to `wattplot/log` (the
  default), and the subscriber is listening on `wattplot/#` (catches
  everything). If you changed `topic_prefix` in the firmware, update
  the subscriber's `--topic` arg.

**"Authentication failed"**
- The username/password in the firmware secrets don't match Mosquitto's
  password file. Reset with `mosquitto_passwd` and update both.

**Logs are too verbose / filling disk**
- Set `logger.level: INFO` (drops DEBUG lines) or `WARN` (only warnings
  and errors). Drop `--keep-days 7` on the subscriber for shorter
  retention.

**I want to grep across all old logs at once**
```bash
zcat logs/wattplot.*.log.gz | grep "MPPT step" | less
```

**Subscriber died / no logs since Tuesday**
- Check the LWT: `mosquitto_sub -h localhost -t "wattplot/log_subscriber/status"`
  should show `online`. If it shows `offline`, the subscriber process
  crashed or was killed; restart it.

---

## What gets logged by default

The firmware uses `ESP_LOGI`, `ESP_LOGW`, `ESP_LOGE`, `ESP_LOGD` in the
following places (in v2.4/v2.5):

| Component | What's logged | Level |
|---|---|---|
| `mppt` | Each MPPT step (V, I, P, setpoint change) | INFO |
| `watering` | Watering events, safety blocks fired | INFO |
| `solenoid` | Solenoid on/off, watchdog kills | INFO / WARN |
| `controller` | State transitions (Normal→Folding→Locked) | INFO |
| `imu` | Tilt reading (DEBUG only, chatty) | DEBUG |
| `wifi` | WiFi connect/disconnect | INFO |
| `api` | Home Assistant API client connect | INFO |
| `mqtt` | MQTT connect/disconnect | INFO |

The full ESPHome startup banner (component init, GPIO assignments, etc.)
is also logged at INFO.

To get even more detail, set `logger.level: VERY_VERBOSE` in the
firmware (this includes ESPHome's internal debug output, ~10x more
chatter).

---

## Disabling MQTT logging

If you want to turn it off without removing the firmware config:

**Option A** — comment out the `mqtt:` block in `wattplot.yaml` and
reflash. This stops the ESP32 from publishing logs over MQTT.

**Option B** — set `logger.logs.mqtt.log.level: NONE` in the firmware.
This keeps the MQTT connection alive (useful for HA integration) but
stops forwarding log lines to the topic.

**Option C** — just stop the subscriber script. The ESP32 still
publishes; you just stop writing them to disk.

---

## Related docs

- `docs/watering.md` — what the watering state machine logs
- `docs/control_law.md` — what the controller state machine logs
- `firmware/wattplot.yaml` — the firmware config (lines 73-92: logger
  + mqtt sections)
- `tools/log_subscriber.py` — the subscriber source
