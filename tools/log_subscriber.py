"""
Wattplot Log Subscriber — v2.5

Subscribes to MQTT topic `wattplot/log` (and `wattplot/#` for status
messages) and writes every line to a rotating log file on this PC.

Output: ./logs/wattplot.log (current)
        ./logs/wattplot.YYYY-MM-DD.log.N.gz (rotated, gzipped, kept 30 days)

Run on the same PC that's running your Mosquitto broker, or any PC
that can reach the broker on your home network.

Usage:
    pip install paho-mqtt
    python tools/log_subscriber.py                 # uses defaults
    python tools/log_subscriber.py --broker 192.168.1.10
    python tools/log_subscriber.py --broker localhost --no-auth
    python tools/log_subscriber.py --keep-days 7   # shorter retention

Press Ctrl-C to stop. Reconnects automatically on network drops.
"""
import argparse
import gzip
import logging
import os
import signal
import sys
import time
from datetime import datetime, date
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Missing dependency: paho-mqtt. Install with:  pip install paho-mqtt",
          file=sys.stderr)
    sys.exit(1)


# Defaults — override via CLI
DEFAULT_BROKER = "localhost"
DEFAULT_PORT = 1883
DEFAULT_USER = "wattplot"
DEFAULT_PASS = ""
DEFAULT_TOPIC = "wattplot/#"
DEFAULT_LOG_DIR = "logs"
DEFAULT_KEEP_DAYS = 30


class RotatingLog:
    """Writes log lines to a date-stamped file, rotates daily, gzips + cleans old."""

    def __init__(self, log_dir: Path, keep_days: int = 30):
        self.log_dir = log_dir
        self.keep_days = keep_days
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_date: date | None = None
        self.current_file = None
        self._open_for_today()

    def _open_for_today(self) -> None:
        today = date.today()
        if self.current_date == today:
            return
        # Rotate the old file
        if self.current_file is not None:
            self.current_file.close()
            self._gzip_yesterday()
        self.current_date = today
        path = self.log_dir / "wattplot.log"
        # Append if it already exists (same-day restart), else create
        self.current_file = open(path, "a", encoding="utf-8", buffering=1)
        self._write_line(f"--- log_subscriber started at {datetime.now().isoformat()} ---")

    def _gzip_yesterday(self) -> None:
        """Find the wattplot.log file (yesterday's), rename and gzip it."""
        # If the current file got rotated mid-day (e.g., by external tool),
        # we'd lose data; we only rotate once per day at midnight.
        # For simplicity, rotate on day-boundary.
        old = self.log_dir / "wattplot.log"
        if not old.exists():
            return
        ts = self.current_date.isoformat() if self.current_date else "unknown"
        # Move to a dated name, then gzip
        dated = self.log_dir / f"wattplot.{ts}.log"
        if dated.exists():
            # If dated file already exists, just leave wattplot.log in place
            return
        old.rename(dated)
        gz_path = dated.with_suffix(".log.gz")
        with open(dated, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
            f_out.writelines(f_in)
        dated.unlink()

    def _write_line(self, line: str) -> None:
        self._open_for_today()
        self.current_file.write(line + "\n")

    def write(self, topic: str, payload: str) -> None:
        # Strip null bytes (some MQTT brokers forward them)
        payload = payload.replace("\x00", "")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write_line(f"{ts}  [{topic}]  {payload}")

    def cleanup_old(self) -> None:
        """Delete gzipped logs older than keep_days."""
        cutoff = time.time() - self.keep_days * 86400
        for gz in self.log_dir.glob("wattplot.*.log.gz"):
            if gz.stat().st_mtime < cutoff:
                gz.unlink()
                print(f"[cleanup] deleted old log {gz.name}", file=sys.stderr)

    def close(self) -> None:
        if self.current_file:
            self.current_file.close()


def make_client(broker: str, port: int, user: str, pw: str,
                no_auth: bool, rot: RotatingLog) -> mqtt.Client:
    client = mqtt.Client(client_id="wattplot-log-subscriber",
                         clean_session=True)

    if not no_auth and user:
        client.username_pw_set(user, pw)

    # LWT for the subscriber itself (lets you see if it died)
    client.will_set("wattplot/log_subscriber/status", "offline",
                    qos=0, retain=True)

    def on_connect(c, userdata, flags, rc, _props=None):
        if rc == 0:
            print(f"[mqtt] connected to {broker}:{port}", file=sys.stderr)
            c.subscribe(DEFAULT_TOPIC, qos=0)
            print(f"[mqtt] subscribed to {DEFAULT_TOPIC}", file=sys.stderr)
            c.publish("wattplot/log_subscriber/status", "online", retain=True)
        else:
            print(f"[mqtt] connection failed: rc={rc}", file=sys.stderr)

    def on_message(c, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="replace").strip()
        except Exception as e:
            payload = f"<decode error: {e}>"
        rot.write(msg.topic, payload)

    def on_disconnect(c, userdata, rc, _props=None):
        if rc != 0:
            print(f"[mqtt] unexpected disconnect (rc={rc}), will auto-reconnect",
                  file=sys.stderr)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    # Auto-reconnect (built into paho)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    return client


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--broker", default=DEFAULT_BROKER,
                    help=f"MQTT broker host (default: {DEFAULT_BROKER})")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT,
                    help=f"MQTT broker port (default: {DEFAULT_PORT})")
    ap.add_argument("--user", default=DEFAULT_USER,
                    help=f"MQTT username (default: {DEFAULT_USER})")
    ap.add_argument("--password", default=DEFAULT_PASS,
                    help="MQTT password (default: empty)")
    ap.add_argument("--no-auth", action="store_true",
                    help="Connect without username/password (anonymous)")
    ap.add_argument("--log-dir", default=DEFAULT_LOG_DIR,
                    help=f"Directory for log files (default: {DEFAULT_LOG_DIR})")
    ap.add_argument("--keep-days", type=int, default=DEFAULT_KEEP_DAYS,
                    help=f"Days of rotated logs to keep (default: {DEFAULT_KEEP_DAYS})")
    ap.add_argument("--topic", default=DEFAULT_TOPIC,
                    help=f"MQTT topic to subscribe to (default: {DEFAULT_TOPIC})")
    args = ap.parse_args()

    # Make log dir relative to script's parent so the file lands in the
    # repo (./logs/), not in whatever cwd the user invoked from
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    log_dir = (repo_root / args.log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"[boot] Wattplot log subscriber", file=sys.stderr)
    print(f"[boot]   broker    = {args.broker}:{args.port}", file=sys.stderr)
    print(f"[boot]   user      = {args.user or '<none>'}", file=sys.stderr)
    print(f"[boot]   topic     = {args.topic}", file=sys.stderr)
    print(f"[boot]   log dir   = {log_dir}", file=sys.stderr)
    print(f"[boot]   keep days = {args.keep_days}", file=sys.stderr)

    rot = RotatingLog(log_dir, args.keep_days)
    client = make_client(args.broker, args.port, args.user, args.password,
                         args.no_auth, rot)

    # Handle Ctrl-C cleanly
    def shutdown(signum, frame):
        print("\n[shutdown] disconnecting...", file=sys.stderr)
        client.publish("wattplot/log_subscriber/status", "offline", retain=True)
        client.disconnect()
        rot.close()
        sys.exit(0)
    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # Daily cleanup of old logs (best-effort, runs once at boot)
    rot.cleanup_old()

    # Initial connect (blocking; auto-reconnects on failure)
    try:
        client.connect(args.broker, args.port, keepalive=60)
    except Exception as e:
        print(f"[fatal] initial connect failed: {e}", file=sys.stderr)
        return 1

    # loop_forever blocks; auto-reconnects on disconnect
    client.loop_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
