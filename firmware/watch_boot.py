"""
Open COM16, send a USB-CDC chip reset, then capture ~20s of boot logs.
Uses errors=replace on stdout to handle Unicode chars (DEBUG logs include ⁄).
"""
import io
import sys
import time

import serial

PORT = "COM16"
BAUD = 115200
WATCH_SECONDS = 80

# Force UTF-8 on stdout to handle Unicode chars (cp1252 on Windows console
# can't print ⁄ etc).
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001, S110
    pass

def main():
    s = serial.Serial(PORT, BAUD, timeout=0.3)
    print(f"[watch] opened {PORT} @ {BAUD}", flush=True)
    s.dtr = False
    s.rts = True
    time.sleep(0.1)
    s.dtr = True
    s.rts = False
    time.sleep(0.5)
    s.reset_input_buffer()
    print("[watch] reset issued, capturing...", flush=True)
    deadline = time.time() + WATCH_SECONDS
    total = 0
    while time.time() < deadline:
        chunk = s.read(4096)
        if chunk:
            total += len(chunk)
            sys.stdout.write(chunk.decode("utf-8", errors="replace"))
            sys.stdout.flush()
    s.close()
    print(f"\n[watch] done. total bytes: {total}", flush=True)

if __name__ == "__main__":
    main()
