# ESP32-S3 cheat sheet

Everything we need to know about the ESP32-S3-DevKitC-1-N16R8 we're using,
the USB-Serial/JTAG peripheral, the boot flow, strapping pins, the
auto-reset circuit (or lack thereof), and the esptool options that
actually work on this board. Kept under `_internal/` so it doesn't get
served on the public site.

---

## 1. The board

- **Module:** ESP32-S3-DevKitC-1-N16R8 (Espressif official)
- **Chip:** ESP32-S3 (QFN56, revision v0.2)
- **Flash:** 16 MB (Octal SPI)
- **PSRAM:** 8 MB (AP_3v3 vendor, 85°C rated)
- **WiFi:** 2.4 GHz 802.11 b/g/n
- **Bluetooth:** 5 (LE)
- **CPU:** Dual-core Xtensa LX7 @ 240 MHz, plus LP core
- **Crystal:** 40 MHz
- **USB:** Native USB-Serial/JTAG (no bridge chip, no CP2102N)
- **Buttons:** BOOT (GPIO0), RST (EN / CHIP_PU)
- **LED:** Onboard LED on GPIO48 (active LOW on some DevKitC-1 variants)
- **MAC address (this unit):** e0:72:a1:fd:1e:c0

The board uses the chip's **native USB-Serial/JTAG peripheral** for both
USB communication and JTAG. There is **no separate USB-to-serial bridge
chip** (no CP2102N, no CH340). This matters for auto-reset — see §6.

---

## 2. Strapping pins

The ESP32-S3 has **four strapping pins**, sampled at reset to determine
boot behavior:

| Pin | Default | Effect |
|---|---|---|
| **GPIO0** | Internal pullup (~45 kΩ) | LOW = ROM serial bootloader (download mode), HIGH = boot from flash |
| **GPIO3** | — | JTAG signal source |
| **GPIO45** | Internal pullup | VDD_SPI voltage (LOW = 1.8V, HIGH = 3.3V) |
| **GPIO46** | Internal pulldown | ROM boot mode (must be LOW for download mode) |

**Boot mode truth table (for the SPI/Joint Download modes):**

| GPIO0 | GPIO46 | Mode |
|---|---|---|
| HIGH (or floating) | any | SPI Boot (run from flash) — normal operation |
| LOW | LOW | Joint Download Boot (ROM serial bootloader) |
| LOW | HIGH | Invalid / won't boot |

The good news: **GPIO0 has an internal pullup**. If nothing is pulling
it LOW, it defaults HIGH and the chip boots from flash. So a stuck BOOT
button is the most common cause of being "stuck in download mode."

---

## 3. The reset and boot flow

### 3.1 Power-on / EN rising edge

1. CHIP_PU (EN) rises. The chip is enabled.
2. Strapping pins (GPIO0, GPIO3, GPIO45, GPIO46) are sampled.
3. The ROM bootloader starts. It decides:
   - **SPI Boot** (default): read the app from flash at 0x10000
   - **Joint Download Boot**: wait for esptool on UART0 or USB-JTAG

### 3.2 The "boot button trick"

To force the chip into download mode:

1. **Press and hold BOOT** (pulls GPIO0 LOW)
2. **Press and release RST** (toggles CHIP_PU, chip resets)
3. **Release BOOT** (after a short delay, ~100 ms is enough)

The chip samples GPIO0 LOW on the CHIP_PU rising edge, enters Joint
Download Boot, and waits for esptool.

### 3.3 What `Hard resetting via RTS pin` actually does (esptool default)

Toggles the **RTS line of a USB-to-serial bridge chip** (CP2102N, FTDI,
CH340). On those boards, RTS is wired (via a transistor) to CHIP_PU, so
toggling RTS = pulsing CHIP_PU = resetting the chip.

**The DevKitC-1 has no such bridge chip.** Its USB goes directly to the
chip's native USB-Serial/JTAG peripheral. There is no RTS line. So
esptool's "Hard resetting via RTS pin" on this board is a **no-op** —
it does nothing, the chip stays in whatever state it was in.

This is the most common reason people get "stuck in download mode" with
the DevKitC-1 after a flash. The flash succeeds, the chip tries to
boot, but the implicit RTS reset that esptool does at the end of
write_flash doesn't reset anything.

### 3.4 What actually resets the chip on this board

Three real options:

1. **Press the RST button manually.** Most reliable. The chip resets
   cleanly, GPIO0 is sampled (with BOOT released, it reads HIGH), the
   chip boots the new firmware.

2. **Use esptool's `--after watchdog-reset`.** Triggers the chip's
   internal watchdog timer to do a hard reset. Works on USB-Serial/JTAG
   boards where RTS isn't wired. **This is the fix for the DevKitC-1
   "stuck in download mode" problem.**

3. **Power-cycle the chip.** Unplug USB, wait 10+ seconds (to discharge
   the brownout capacitor), plug back in. Cleanest state.

---

## 4. eFuse settings we care about

Read with `espefuse --chip esp32s3 --port COM## summary`. Key
fuses for our situation:

| Fuse | Value | Meaning |
|---|---|---|
| `DIS_FORCE_DOWNLOAD` | 0 (default) | Chip CAN be forced into download mode. If set to 1, download mode is permanently disabled — DO NOT set this. |
| `DIS_DOWNLOAD_MODE` | 0 (default) | UART/USB download mode is enabled. |
| `DIS_USB_SERIAL_JTAG` | 0 (default) | USB-Serial/JTAG peripheral is enabled. |
| `DIS_USB_SERIAL_JTAG_DOWNLOAD_MODE` | 0 (default) | USB download mode (via USB-Serial/JTAG) is enabled. |
| `DIS_USB_OTG` | 0 (default) | USB-OTG peripheral is enabled (separate from USB-Serial/JTAG). |
| `USB_PHY_SEL` | 0 (default) | Internal PHY to USB Device, external PHY to USB OTG. |
| `SOFT_DIS_JTAG` | 0 (default) | JTAG via USB is enabled. |
| `DIS_PAD_JTAG` | 0 (default) | JTAG via pads is enabled. |
| `DIS_APP_CPU` | 0 (default) | Both cores available. |
| `DIS_ICACHE` / `DIS_DCACHE` | 0 (default) | Caches enabled. |
| `FLASH_TYPE` | 0 (4-line) | Default for our module. |
| `PSRAM_CAP` | 1 (8 MB) | Matches the N16R8 module spec. |

**What we observed on this chip (eFuse summary from earlier today):**

```
DIS_FORCE_DOWNLOAD = False
DIS_DOWNLOAD_MODE = False
DIS_USB_SERIAL_JTAG = False
USB_PHY_SEL = internal PHY to USB Device
FLASH_TYPE = 4 data lines
PSRAM_CAP = 8M
```

All defaults, nothing custom. The chip is in factory state for the
N16R8 module.

---

## 5. Flash memory layout

The factory bin we build contains:

```
Offset    Size         Content
0x0000    32 KB        Second-stage bootloader
0x8000    4 KB         Partition table
0x9000    16 KB        NVS (Non-Volatile Storage, for HA pairing, etc.)
0xE000    8 KB        OTA data partition
0x10000   ~1.2 MB      Application (ESPHome firmware)
```

A "factory bin" (`firmware.factory.bin`) is the whole thing concatenated
starting at offset 0x0. A regular `firmware.bin` is just the app at
0x10000.

The factory bin is what you flash when the chip is in a clean state.
The OTA bin is what gets pushed via the network once the chip is
running ESPHome.

---

## 6. esptool options that matter

```
esptool --chip esp32s3 --port COM## [options] command
```

### `--before` (what to do before talking to the chip)

| Option | Effect |
|---|---|
| `default-reset` | Toggle DTR/RTS to enter download mode. **Default. Does nothing useful on DevKitC-1 because no DTR/RTS are wired.** |
| `usb-reset` | USB-JTAG-specific reset sequence. **Esptool auto-detects USB-Serial/JTAG and uses this when appropriate.** |
| `no-reset` | Skip reset. Use when the chip is already in download mode (e.g., you manually did the BOOT procedure and esptool is connecting to an already-downloading chip). |
| `no-reset-no-sync` | Skip reset and skip sync. Use only if the chip is already running and you want to upload a new stub quickly. |

### `--after` (what to do when the operation completes)

| Option | Effect |
|---|---|
| `hard-reset` | Toggle RTS to reset. **Default. Does nothing useful on DevKitC-1.** This is why we got stuck. |
| `soft-reset` | Software reset via the stub. Resets the chip's CPU, leaves USB intact. **This works on DevKitC-1.** |
| `watchdog-reset` | Internal watchdog reset. **The recommended fix for DevKitC-1 "stuck in download mode" problem.** |
| `no-reset` | Leave the chip in download mode. Use when you want to flash multiple files in one session. |
| `no-reset-stub` | Leave the stub bootloader running. Use for advanced debugging. |

### Putting it together

For the DevKitC-1, the safe flash command is:

```powershell
& "C:\Program Files\PyManager\python.exe" -m esptool --chip esp32s3 --port COM## --before usb-reset --after watchdog-reset --baud 460800 write_flash 0x0 firmware\.esphome\build\wattplot-controller\build\firmware.factory.bin
```

If the chip is already in download mode and esptool detects the USB-JTAG,
it will use the right reset automatically — the `--before usb-reset` and
`--after watchdog-reset` are belt-and-suspenders.

---

## 7. The current state (as of last flash)

After two flash attempts (both with hash-verified writes), the chip is
showing as:

- **COM18** (PID 303A:1001) — "OK" status — the ROM bootloader
- **COM17** (PID 303A:4001) — "Unknown" status — should be the normal
  USB-Serial/JTAG mode, but the driver isn't fully loaded

Neither device is doing anything useful. The flash is verified correct
(readback matched the source bin byte-for-byte). The chip just isn't
transitioning out of download mode because:

1. esptool's "Hard resetting via RTS pin" is a no-op on this board
2. The flash doesn't include any code to do its own reset
3. The chip stays in ROM bootloader mode until something forces a reset

The fix is the `--after watchdog-reset` flag (or a manual RST press).

---

## 8. Recovery procedure (the one that should work)

### Step 1: Verify the chip is in download mode

```powershell
& "C:\Program Files\PyManager\python.exe" -m esptool --chip esp32s3 --port COM18 chip-id
```

If you get `Chip is ESP32-S3` plus a MAC address, the chip is in
download mode. If you get `Failed to connect`, do the BOOT procedure
(hold BOOT, press RST, release BOOT) and retry.

### Step 2: Reflash with the right `--after` flag

The current firmware in flash is probably fine — the factory bin
verified. But to be safe, reflash with the correct reset option:

```powershell
& "C:\Program Files\PyManager\python.exe" -m esptool --chip esp32s3 --port COM18 --before no-reset --after watchdog-reset --baud 460800 write_flash 0x0 firmware\.esphome\build\wattplot-controller\build\firmware.factory.bin
```

- `--before no-reset` because the chip is already in download mode
- `--after watchdog-reset` so esptool triggers the chip's internal
  watchdog to do a real reset, instead of trying to toggle RTS
- `--baud 460800` for faster transfer

After this completes, the chip should reboot on its own, enumerate
as the normal USB-Serial/JTAG device (PID 4001), and start the new
firmware.

### Step 3: If the chip still doesn't come up

1. **Press the RST button manually** (no BOOT). The chip should boot
   from flash.
2. **If the LED doesn't come on within 5 seconds** after the RST press,
   press and hold **BOOT** (without RST) for 3 seconds, then release.
   The chip should reset to download mode.
3. **If the chip is still silent after a power cycle**, the most likely
   cause is a hardware issue: BOOT button stuck LOW, damaged GPIO0,
   damaged USB peripheral. Check with a multimeter: GPIO0 should
   measure ~3.3V when the BOOT button is not pressed.

### Step 4: Confirm the firmware is running

```powershell
& "C:\Program Files\PyManager\python.exe" -m esphome logs firmware\wattplot.yaml --device COM17
```

You should see the ESPHome banner, WiFi connect messages, and the
controller state machine starting up. If you see the homing sequence
start (actuator moving to 0°), the firmware is fully alive.

---

## 9. Why the previous flash attempts failed to boot

Timeline:
1. **First flash (COM18, hash verified):** Used default `--after hard-reset`,
   which is a no-op on this board. Chip stayed in download mode.
2. **Erase + reflash (COM18, hash verified):** Same problem. The chip
   is fine, the flash is fine, but the reset isn't happening.
3. **Manual RST press + esptool reset:** Didn't transition the chip
   out of download mode, possibly because Windows was caching the
   USB device state, or because the chip's USB peripheral is in a
   stuck state.

The **only** remaining question: is the factory bin in flash actually
valid, or is something corrupt in the chip's flash memory? The readback
showed the bytes match, so the bin is correct. The chip should boot
it.

---

## 10. Quick reference card

| Question | Answer |
|---|---|
| What chip is this? | ESP32-S3-DevKitC-1-N16R8 |
| Flash size? | 16 MB Octal SPI |
| PSRAM size? | 8 MB |
| Where is the BOOT button? | GPIO0, near USB-C connector |
| Where is the RST button? | EN / CHIP_PU, near pin headers |
| What pins are strapping? | GPIO0, GPIO3, GPIO45, GPIO46 |
| What puts the chip in download mode? | GPIO0 LOW + GPIO46 LOW at reset |
| What pins are USB? | GPIO19 (D-), GPIO20 (D+) — **never use as GPIO** |
| What VID/PID does the bootloader show? | 303A:1001 (COM18 on this PC) |
| What VID/PID does the normal firmware show? | 303A:4001 (COM17 on this PC) |
| Does esptool's `--after hard-reset` work? | **No.** Use `--after watchdog-reset` instead. |
| Does the DevKitC-1 have a USB-to-serial bridge? | No. Native USB-Serial/JTAG only. |
| What's the watchdog reset? | The chip's internal watchdog timer fires, forcing a hard reset. Available via `--after watchdog-reset`. |
| Where's the firmware bin? | `firmware/.esphome/build/wattplot-controller/build/firmware.factory.bin` (1,278,384 bytes) |
| What's the safe flash command? | `esptool --chip esp32s3 --port COM## --before no-reset --after watchdog-reset write_flash 0x0 <factory.bin>` |

---

## 11. Common pitfalls (so we don't repeat them)

1. **Don't rely on `--after hard-reset` on DevKitC-1.** It does nothing
   on the native USB-Serial/JTAG peripheral. Use `watchdog-reset`.

2. **Don't hold BOOT throughout the flash process.** The chip enters
   download mode on the rising edge of CHIP_PU. Once esptool is talking
   to the chip, you can release BOOT. If you keep holding it, the chip
   will stay in download mode after the flash.

3. **Don't use a USB hub.** The DevKitC-1's USB peripheral can be
   finicky through unpowered hubs. Plug directly into the PC.

4. **If the LED never comes on, check the BOOT button.** With a
   multimeter, GPIO0 should be HIGH (3.3V) when the button is not
   pressed. If it's stuck LOW, the chip will always enter download mode.

5. **Windows may cache the COM port.** If COM17 was "Unknown" after a
   flash, try `pnputil /scan-devices` or unplug/replug the USB cable
   to force a re-enumeration.

6. **Driver issues.** The ESP32-S3 USB-Serial/JTAG driver is built into
   Windows 10/11. If COM17 shows as "Unknown," check Device Manager
   for an unrecognized device and update the driver.

7. **Don't flash while serial monitor is open.** Close any PuTTY,
   Tera Term, Arduino Serial Monitor, or VSCode Serial Monitor first.
   Opening the serial port holds DTR/RTS in a state that can prevent
   the chip from booting.

8. **The factory bin is for first-time flash.** Once the chip has been
   flashed once, you can use the OTA bin (`firmware.ota.bin`) over
   the network. The factory bin re-flashes the bootloader, partition
   table, and NVS — which can wipe saved WiFi credentials and HA
   pairings.
