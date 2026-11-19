# Bring-up of the first SQRM8 boards (P2, 2026-11-07)

Bench procedure for the first 12 SQRM8 boards (revision P2, delivered assembled as two V-cut panels of 2 x 3) and 12
ER-TFT040-3 panels with the capacitive touch option. The P2 boards were ordered before the rename to SQRM8
(2026-11-08) and carry the old silkscreen text, `CLAUDIUS` / `MAXIMUS` / `cmax P2`; P3 gets `SQRM8 P3`. Follow the
steps in order for each board and fill one row of the results table (step 7) per board. Board design: `BOARD.md`;
panel: `PANEL.md`; case: `CASE.md`.

Bench kit: a multimeter, a USB-C cable (plus a USB-A to C cable for step 5), a USB meter or a current-limited 5 V
supply with a USB-C power breakout, a loupe or microscope, calipers, a Waveshare ESP32-S3-Touch-LCD-4B as the
reference board, and a checkout of this repository on branch `hardware`.

Figures marked **(est.)** are derived from datasheets or the design, not measured; replace them with the
measured values once the first boards are through.

## Conventions

- Board positions are in mm in the KiCad top view (component side): origin at the corner where the J2 edge meets
  the edge with the board name, x along the 48.5 mm side away from J2, y along the 42 mm side. The J2 edge (x = 0)
  is the tail edge; the long edge at y = 42 carries L1, D2, C4 and the debug pad row.
- On the panel, seen from the back with the device upright (tail at the bottom): a board point (x, y) is
  22 + x mm up from the bottom lens edge and y - 21 mm right of the vertical centre line. J1 sits at the lens
  centre; J2's pin-1 end is on the right.
- Serials 1-12: panel A positions 1-6 = serials 1-6, panel B = 7-12. Write the serial on U1's shield can with a fine
  marker after separation.

## Before you start

- **Firmware**: the sqrm8 board profile (`hal.cpp` board detection, GPIO 5/6/7/15/16, CTRL backlight) exists only on
  branch `hardware`. Released apps and firmware up to 0.7.2 have none: they report a 4B, never initialise the panel
  and drive the backlight inverted at 5 kHz. Build and flash from the checkout only, and record the commit
  (`git rev-parse --short HEAD`). The checkout says `FW_VERSION "0.8.0"`, the version of the rename release, which
  is not out yet: the string alone does not tell a checkout build from a release.
- **Quit the packaged desktop app** for the whole session (tray menu, Quit): it would offer its own firmware to a
  board that sends no hello. Use the daemon from the checkout (step 5).
- **One ESP32-S3 board on USB at a time.** `tools/dev.py` and PlatformIO take the first Espressif (303a) port; with
  the 4B plugged in too, they may flash or measure the wrong board. Pin the upload with
  `PLATFORMIO_UPLOAD_PORT=/dev/ttyACM0` if both must stay connected.
- **Never connect or disconnect the panel tail with power applied**, and never with C8 charged (step 3.6).
- **No pull-ups on GPIO45 (LCD_G3) or GPIO46 (LCD_HS)**: they are strapping pins (VDD_SPI voltage, download mode).
  No logic-analyser inputs with pull-ups or probe fixtures on those nets.
- ESD: wrist strap, and handle the panel by its edges; keep the lens film on until step 6.

### Probe points

| Net | Where (board mm) | Notes |
|---|---|---|
| EN / 3V3 / GND / RX / TX | TP5 / TP4 / TP3 / TP2 / TP1, the pad row at y 39.75, x 35.1-45.3, silk `EN 3V3 GND RX TX` | RX = RXD0 (GPIO44), TX = TXD0 (GPIO43); no VBUS pad |
| VBUS | C7 (4.3, 35.5) or C4 (16.9, 39.2), the other pad is GND | U2 pin 3 is VBUS too |
| BOOT (GPIO0) | SW1 (42.5, 33.0), silk `BOOT`; R2 (37.0, 33.0) is its 10k pull-up | pressed = GND |
| LED_A (boost output) | C8 (12.9, 35.6) or C9 (15.45, 35.3) | up to the 27 V OVP with no panel |
| LED_K / sense | across R8 6.8 ohm (12.6, 31.2) | V(R8) = LED current x 6.8 |
| BL_EN (AP3032 CTRL) | across R7 100k (12.6, 33.0) to GND | BL_PWM (GPIO4) reaches it through R11 100 ohm (15.6, 32.75) |
| LCD_RST (GPIO15, panel RESX and GT911 RST) | across R9 10k (15.6, 10.9) to GND | 10k pull-down |
| LCD_CS (GPIO5) | R10 10k (12.6, 29.6), pad to GND | 10k pull-up |
| I2C_SDA / I2C_SCL (GPIO47 / 48) | R3 (12.6, 9.3) / R4 (12.6, 10.9), 4.7k pull-ups | GT911 only on this bus |

Never probe J2's 0.5 mm pads: a slipped probe shorts LED_A to its neighbours.

## 1. Incoming inspection

### 1.1 The two PCB panels, before separation

1. Photograph each panel, both sides, with a ruler in frame.
2. V-cuts: continuous and even on both axes, the same depth from both faces, no copper or fibre exposed along the
   cut (copper stops 1.0 mm from every edge), no delamination at the rails.
3. Look along each board's y = 42 edge: C4 (4.7 uF 0805) lies perpendicular to that cut, its pads 1.35 mm from
   it, the high-strain orientation for MLCC cracks. Inspect it before and after separation.

### 1.2 Separation

Separate along the score with a V-cut separator, or with flat pliers gripping the board right next to the cut,
never by flexing the whole panel. Snap the y = 42 edges (C4, L1, D2) with the least bending of all.

### 1.3 Each board (loupe, x10-x20)

| Item | Check |
|---|---|
| C4 | no hairline crack at either termination (flex cracks run at about 45 degrees from the end cap), no chipped corner; same for L1 and D2 on the same edge |
| J1 (USB-C) | the 12 x 5 mm flange sits flat on the board all round (no light under one side, gap <= 0.1 mm), the body upright; 16 signal pads wetted, no bridges; the 4 shell blades through their plated slots with a fillet on the top pad and on the bottom of each slot; both pegs in their holes. The slots are 1.10 x 0.55 mm for 0.90 x 0.30 mm blades: a blade that bound shows as a tilted flange and a starved or missing fillet |
| J1 blades | protrusion below the bottom face, with calipers (depth from the bottom face to the tip including solder). Drawing: 0.55 mm nominal, 0.30-0.96 mm over the blade and board tolerances, plus the fillet. Record the largest of the four |
| J2 (FPC) | 40 pads at 0.5 mm: no bridges, none open; both anchor pads soldered; the back-flip latch opens and closes freely, housing not deformed by reflow, no solder or flux in the slot. Pin 1 (silk dot) is the end next to C12/C13, R8 and R10 (y 30.75); pin 40 the end next to R3/R4 and R9 (y 11.25). The latch is rated for 20 cycles: open it only to check it once |
| U1 (module) | flat, all castellations wetted on both long sides and the bottom end, antenna end at the y = 0 edge in the corner away from J2 (keep-out x 28-48.5, y 0-8.5: no copper, nothing placed). Bottom side under the exposed pad: no solder bumps through its 12 vias (a bump there presses on the panel); file the assembler's X-ray of the pad if supplied |
| Polarised parts | not all placement rotations were confirmed before assembly: D1 (USBLC6) pin 1 mark as on the silk, U2 (AMS1117) tab towards C5/C6 (+x), U3 (AP3032) pin 1 mark, D2 (SS14) cathode bar towards C8 (+x, away from L1), SW1 square on its pads; no 0603/0805 part turned 90 degrees |
| Silk | `cmax P2` under the board name `CLAUDIUS` / `MAXIMUS` (P2 predates the rename) |

Photographs per board (keep them with the private records in `work/`, not in the repo: the silk carries the fab's
order number): top and bottom with a ruler; C4 both ends; J1 from four sides plus the bottom fillets; J2's pad row
and latch; U1's castellations on both sides; the bottom under U1; anything rejected. Name them
`sqrm8-P2-<serial>-<view>.jpg`.

### 1.4 The 12 panels

- Lens: no chips at the corners, no scratches under the film; touch sub-flex and its hot-bar joint (within 15 mm of
  the tail-side lens edge) undamaged.
- Tail: not creased, stiffener intact, contacts clean. Thickness at the contacts 0.30 +- 0.05 mm (panel drawing)
  against the connector's 0.30 +- 0.02: a thick tail makes the latch stiff, a thin one lowers contact force.
- Record the panel's label or lot number against the board serial it gets.

### 1.5 Unpowered measurements

| Measurement | Expected | A fault reads |
|---|---|---|
| VBUS-GND resistance (red on VBUS at C7) | climbs past several kilohms as the caps charge (est.) | < 10 ohm and steady: short (C4 or C7 cracked, D1 rotated) |
| VBUS-GND, probes reversed | a diode-like low reading is normal (USBLC6 and IC body diodes) | |
| 3V3-GND resistance (TP4-TP3) | climbs past about 1 kilohm (est.) | < 10 ohm: short on the rail (module, C1/C5) |
| LED_A-GND (C8) | open or climbing | low: C8/C9 or a shorted boost output |
| LCD_RST-GND (across R9) | about 10 kilohm (R9) | ~0: short; open: R9 missing |
| EN-GND (TP5-TP3) | climbs (C3 1 uF behind R1 10k to 3V3) | ~0: short |
| VBUS-GND capacitance, if the meter has the range | 14-18 uF (est.): C4 4.7 + C7 10 uF nominal, plus up to ~1.1 uF of C8/C9 seen through D2 at the meter's test voltage | 10-12 uF: C4 open (cracked or missing) |

## 2. Power-up without the panel

### 2.1 Setup

USB meter inline in the host cable, or a current-limited supply at 5.0 V into a USB-C power breakout (there is no
VBUS pad). First power-up of each board: limit 100 mA. Without firmware the module is blank (the ROM loops on
"invalid header") or carries a factory test image; either way GPIO4 floats and R7 holds the backlight boost off.

### 2.2 Expected values

| Quantity | Where | Expected |
|---|---|---|
| VBUS | C7 or C4 | supply minus cable drop; >= 4.75 V from a good host port |
| 3V3 | TP4-TP3 | 3.27-3.33 V (AMS1117-3.3, 1 % initial); 3.20-3.40 V over temperature |
| EN | TP5-TP3 | = 3V3 (R1 10k, C3 1 uF: high about 10 ms after 3V3) |
| BOOT | SW1 / R2 | = 3V3; 0 V while pressed |
| LED_A | C8 | VBUS minus D2's forward drop, about 0.2-0.4 V below VBUS (est.): the boost is off, VBUS reaches LED_A through L1 and D2. About 0 V means D2 is reversed or open |
| BL_EN (CTRL) | across R7 | 0 V |
| LCD_RST | across R9 | 0 V (held in reset) |
| LCD_CS | R10, LCD_CS pad | = 3V3 |
| I2C_SDA, I2C_SCL | R3, R4 | = 3V3 |

Expected VBUS currents (all est.: no SQRM8 board has been measured yet):

| State | Current | Derived from |
|---|---|---|
| Blank module or ROM download mode, no panel | 25-50 mA | ESP32-S3 on its reset clock with the USB-Serial-JTAG up, AMS1117 quiescent 5-11 mA, AP3032 shutdown 50 uA |
| Firmware running, no panel (step 3.6), boost enabled into no load | 70-110 mA | module at 240 MHz dual core with the PSRAM scan-out running (60-100 mA), AMS1117 quiescent, AP3032 quiescent 3-5 mA |
| Same, backlight 0 (`bl 0`) | 3-5 mA less | the AP3032 quiescent current: without the panel the boost has nothing to drive |
| Firmware + panel, backlight 0 | 85-150 mA | + panel logic and GT911 (15-40 mA) |
| Firmware + panel, backlight 100 | 190-270 mA | + 29.4 mA in two strings of 5 LEDs at about 15 V, through the boost at 75-82 % efficiency from 5 V: +105-120 mA |

Reference: measure the 4B on the same meter with the same build in the same states (step 3 onwards) and enter it
as the `4B` row of the results table. At equal settings the SQRM8 board should draw less (est.): the 4B adds a PMIC, the
audio codec, the CH343 and the expander, and runs its LEDs at about 42 mA at 100 %.

A short looks like this: the supply sits at its current limit with VBUS collapsing to under 1 V, or the USB meter
shows the port switching off and on (the host's over-current protection; Linux logs `over-current` in `dmesg`),
and one part gets hot within seconds (U2, D1, C4, L1, D2: touch-test them). 3V3 near 0 V with VBUS normal and U2
hot is a short on the 3.3 V rail. Unplug at once.

After one minute at the 2.2 state, U2 is at most lukewarm.

### 2.3 Brown-out threshold (one or two boards, supply only, after step 3)

The firmware resets the chip when 3V3 falls under about 2.84 V (`CONFIG_ESP_BROWNOUT_DET_LVL_SEL_4`, both boards).
3V3 comes from VBUS through the AMS1117 (dropout about 1.0-1.1 V at this load; regulation is only specified from
4.8 V in). With the firmware running, lower VBUS in 0.1 V steps from 5.0 V and record:

- the VBUS at which 3V3 drops below 3.20 V (dropout onset; about 4.3-4.5 V, est.);
- the VBUS at which the board resets (3V3 at about 2.84 V; VBUS about 3.9-4.0 V, est.): the UI restarts, and a
  UART console on TP1 prints `BOD: Brownout detector was triggered` and the ROM reports reset reason `rst:0xf`.

## 3. First flash

### 3.1 Host

```bash
git -C <repo> switch hardware && git -C <repo> rev-parse --short HEAD
host/.venv/bin/pip install -e host platformio            # once, from the repo root
```

Quit the packaged app; check that nothing holds the port (`lsof /dev/ttyACM*` empty). Only the board under test
on USB.

### 3.2 Download mode

Hold BOOT (SW1) while plugging the USB-C cable into J1 (the board's native USB, the ESP32-S3's USB-Serial-JTAG),
then release it. Checks: `lsusb` lists `303a:1001` (Espressif USB JTAG/serial debug unit), `/dev/ttyACM0`
appears, the current is in the 25-50 mA band (est.), LED_A stays at VBUS minus the diode drop (boost off).
A blank module also enters the loader without BOOT (esptool resets it through the USB-Serial-JTAG); holding BOOT
here also proves SW1.

Record the board's MAC: esptool prints `MAC:` while flashing with `dev.py`, or
`udevadm info -q property -n /dev/ttyACM0 | grep ID_SERIAL_SHORT` (the USB serial number is the MAC).

### 3.3 Flash

One image runs on the 4B and on the SQRM8 board; the board is detected at boot, so there is no board-specific build.

Developer path (PlatformIO upload, prints esptool's output):

```bash
DEV_NAME=bench host/.venv/bin/python tools/dev.py flash
```

The desktop flasher path (what users will run), from a bundle of the same build:

```bash
host/.venv/bin/python tools/fw_bundle.py --board 4b --out /tmp/sqrm8-fw    # bundle "4b" serves sqrm8 (flasher.BUNDLES)
cd host && SQRM8_FIRMWARE_DIR=/tmp/sqrm8-fw .venv/bin/python -m companion flash --board sqrm8 --port /dev/ttyACM0 --erase
```

It ends with `flashed sqrm8 fw 0.8.0 via /dev/ttyACM0 in <n>s` and `link port: /dev/ttyACM0`. `--erase` gives the
settings store a clean start; use it on the first flash of each board. Flash the 4B with the same build once, as
the reference for everything below.

### 3.4 Board detection

`hal.cpp` logs nothing about the detection (the console is UART0 at `CONFIG_LOG_DEFAULT_LEVEL_WARN`); the result is
in the hello on the native port. `board_init` probes I2C 0x20 three times: a TCA9554 answering is a 4B, none is
sqrm8.

```bash
DEV_NAME=bench host/.venv/bin/python tools/dev.py monitor --seconds 5
```

Must print (the firmware sends it without spaces, `dev.py` re-prints it with them):

```
{"t": "hello", "fw": "0.8.0", "board": "sqrm8", "w": 480, "h": 480, "caps": ["part", "screen"], "screen": "home"}
```

| Result | Meaning |
|---|---|
| `"board": "sqrm8"` | pass |
| `"board": "ESP32-S3-Touch-LCD-4B"` | the image is a release build without the sqrm8 profile (main, up to 0.7.2), not the `hardware` build: nothing on an SQRM8 board answers at 0x20 |
| no hello | the firmware does not run: read the UART console, reflash with `--erase` |

The 4B with the same build reports `"board": "ESP32-S3-Touch-LCD-4B"`.

### 3.5 UART console (optional)

A 3.3 V USB-UART adapter on TP1 (TX), TP2 (RX), TP3 (GND), 115200 8N1. At power-up the ROM prints its banner and a
`rst:` / `boot:` line (download mode: `boot:0x0 (DOWNLOAD(USB/UART0))`, `waiting for download`). The bootloader logs
only errors and the application only warnings and errors, so a healthy boot is quiet after the banner. Panics and
the brown-out message appear here and nowhere else.

### 3.6 Running without the panel

With the firmware running and no panel: the current is in the 70-110 mA band (est.); the firmware enables the
backlight at boot, so the boost runs into no load and LED_A sits at the AP3032's OVP clamp, about 27 V (measure at
C8). `dev.py perf --screen home --seconds 10 --nodemo` answers with `lcd_frames` advancing, `lcd_underruns` 0 and
`"touch_ic":"?"` (no GT911 without the panel).

**Before connecting a panel**: C8/C9 can stay charged near 27 V after the USB cable is removed, and would discharge
into the LEDs when the tail goes in. Unplug, measure LED_A at C8, and if it is above about 5 V discharge it with a
1 kilohm resistor across C8 for a second.

## 4. Panel connection

### 4.1 Position

Lens face down on a clean soft cloth. Put the board in its final place on the panel back, standing on the 1.2 mm
foam tape with the liner still on (or a 1.2 mm spacer), so the tail sees its final geometry: the J2 edge 22 mm up
from the bottom lens edge, J1 at the lens centre (42.1 mm from the bottom and side lens edges). USB unplugged,
C8 discharged.

### 4.2 Tail insertion

1. Fold the tail from the panel's bottom edge onto the back, as the panel maker folds it. Its contacts then face the
   panel; J2 is dual contact, so the face does not matter.
2. Pin 1 (LEDA) arrives at the right end seen from the back, which is J2's pin-1 end (next to C12/C13, R8). Check
   against the tail's marking: a mirrored tail puts panel GND (pin 40) on LED_A.
3. Open the back-flip latch (it lifts on the side away from the entry), slide the tail in square (20.5 mm tail in a
   20.6 mm slot: a skew over about 6 degrees binds) to the stop, 2.1 mm deep; about 1.4 mm of the 3.5 mm exposed
   contacts stay visible at the entry (est.). Close the latch. A gentle tug must not move the tail.
4. First board only: note the slack, and whether the tail humps or springs back. `BOARD.md` leaves the 22 mm figure
   to a sample check (+-0.5 mm); record the position that gives about 1 mm of slack for the jig (step 6).

### 4.3 Power-up with the panel

Current limit 500 mA. Plug in and watch the screen: it stays dark until the UI appears, with no white or garbage
flash (R9 holds the panel and the GT911 in reset, R7 holds the backlight off until the firmware drives them).
A flash at plug-in means R7 or R9 is missing or GPIO4/GPIO15 is driven early.

The firmware's sequence (`hal.cpp` `init_sqrm8`, `panel_init`): LCD_CS/SCL/SDA (GPIO 5/6/7) high, TP_INT (GPIO16) low,
LCD_RST (GPIO15) low for 20 ms, then high; TP_INT held low 60 ms more (GT911 address 0x5D), then released as an
input; 60 ms later the touch probe (0x5D, then 0x14) and the ST7701S init over the bit-banged 3-wire bus (software
reset, 120 ms, the init table), then the RGB scan-out at 12 MHz pixel clock, then the backlight (LEDC on GPIO4,
200 Hz, 10 bit, duty = brightness; 100 % on at the end of `hal_init`, then the saved setting, 80 % by default).
With a scope on R9 and on the TP_INT net this is visible; with a multimeter only the end state is.

Current at the default 80 %: between the two "panel" rows of the table in 2.2.

### 4.4 Shared reset line

| Condition | LCD_RST (across R9) | Screen |
|---|---|---|
| Firmware running | 3V3 | UI |
| BOOT held at plug-in (download mode) | 0 V | dark, backlight off |

Never re-pulse GPIO15 to recover the touch alone: it resets the panel too. Diagnosis:

| Picture | Touch (`touch_ic`) | Look at |
|---|---|---|
| no | yes (`911`) | init bus (GPIO 5/6/7, R10), RGB lines, panel VDD (J2 pin 5, C12/C13) |
| yes | no (`?`) | I2C (R3/R4, GPIO47/48), TP_INT (GPIO16), TP_VCC (J2 pin 39, C14/C15) |
| no | no | the tail (seating, pin 1 end), LCD_RST stuck low, 3V3 |

### 4.5 Backlight

Set the level with `DEV_NAME=bench host/.venv/bin/python tools/dev.py send '{"t":"cmd","bl":N}'` and measure DC
across R8 (the meter averages the 200 Hz PWM). The auto-dim lowers the level after 180 s without touch or activity:
touch the screen or send again.

| `bl` | CTRL duty | V(R8) expected | LED current |
|---|---|---|---|
| 100 | constantly high | 0.200 V (AP3032 feedback 0.188-0.212 V) | 29.4 mA (27.4-31.5 mA with R8 at 1 %) |
| 80 (default) | 80 % | about 0.16 V (est., linear dimming) | about 23.5 mA (est.) |
| 50 | 50 % | about 0.10 V (est.) | |
| 12 (dim level) | 12 %, 0.6 ms high per 5 ms | about 24 mV (est.) | |
| 6 (night idle level) | 6 %, 0.3 ms high | about 12 mV (est.) | |
| 3, 2, 1 | 3 %, 0.15 ms high (the firmware raises 1 and 2 to it) | lit on the first board, value not measured | |
| 0 | off | 0 V | 0 |

At 100 % also: LED_A at C8 = the string voltage plus 0.2 V, about 14.5-16 V (est.; the panel gives 15 V typical,
16 V max at 40 mA); BL_EN across R7 = 3V3, and duty x 3V3 on average below 100 %.

The firmware first dimmed at 25 kHz as the AP3032 datasheet suggests; the first board (2026-11-19) changed only up
to 8 % duty there, and whined at 40-80 % at 1 kHz, hence 200 Hz (`BOARD.md`). Record whether V(R8) steps down
evenly through 80, 50, 12, 6 and 3, whether the brightness jumps between 80 and 100 (under 0.7 ms low time, above
about 86 %, the AP3032 stays in standby instead of restarting), and any whine or visible flicker. Next to the 4B at the same setting the SQRM8
board is dimmer by about a quarter (est.: 29 against about 42 mA).

### 4.6 Picture

A test image with colour bars and one ramp per channel (a dead or shorted data line shows as a ramp whose steps
repeat or jump at 1/2, 1/4, 1/8... of its width):

```bash
host/.venv/bin/python - <<'EOF'
from PIL import Image, ImageDraw
im = Image.new('RGB', (480, 480)); d = ImageDraw.Draw(im)
bars = [(255, 255, 255), (255, 255, 0), (0, 255, 255), (0, 255, 0), (255, 0, 255), (255, 0, 0), (0, 0, 255), (0, 0, 0)]
for i, c in enumerate(bars): d.rectangle((i * 60, 0, i * 60 + 59, 119), fill=c)
for x in range(480):
    v = x * 255 // 479
    for k, c in enumerate([(v, 0, 0), (0, v, 0), (0, 0, v)]): d.line((x, 120 + 120 * k, x, 239 + 120 * k), fill=c)
im.save('/tmp/sqrm8-bars.png')
EOF
DEV_NAME=bench host/.venv/bin/python tools/dev.py show /tmp/sqrm8-bars.png --seconds 30
```

Pass: the white bar top left with the picture upright and the tail edge at the top; bar colours as on the 4B
showing the same image (red and blue not swapped); white is neutral (DB0 and DB12 repeat B5 and R5); the three
ramps smooth and monotonic, red and blue in 32 steps, green in 64. Since 2026-11-19 the firmware turns the sqrm8
picture half a turn from the 4B's (`BOARD_SQRM8_ROT180` in `board.h`), so the tail edge is at the top of the
picture; an upside-down picture with correct colours is that setting, not the board.

Then a screenshot of the home screen:

```bash
DEV_NAME=bench host/.venv/bin/python tools/dev.py shot /tmp/sqrm8-<serial>-home.png --screen home --calm --settle 4
```

The shot reads the framebuffer, so it proves rendering and a 460 KB transfer over the link, not the panel: compare
the PNG with what the panel shows.

### 4.7 Scan-out (`docs/PERF.md` probe)

```bash
DEV_NAME=bench host/.venv/bin/python tools/dev.py perf --screen home --seconds 120 --nodemo
DEV_NAME=bench host/.venv/bin/python tools/dev.py perf --screen home --seconds 120
DEV_NAME=bench host/.venv/bin/python tools/dev.py perf --screen home --seconds 60 --cycle
```

Pass: `lcd_underruns` 0 in every window, `lcd_n10` and `vs_n10` 0; `fps`, `frame_ms_avg`, `cpu_pct` and `heap_int`
within run-to-run scatter of the 4B running the same build and the same commands (same module family, PSRAM and
scan-out). Record the first window's numbers in the table.

### 4.8 Touch (GT911)

From the same perf output: `"touch_ic":"911"` (the product id register read back: the GT911 answered, at 0x5D or
0x14; the reset sequence makes it 0x5D, the address itself is not reported), `touch_rate_ms` from the controller's
configuration, `touch_errors` 0. Run a `perf --nodemo --seconds 20` while tapping: `touch_presses` counts up,
`touch_scan_hz` is above 0 while a finger is down and 0 at rest, `touch_glitches` stays near 0. In the UI: taps land
under the finger in all four corners (touch follows the same rotation as the picture), swipes move between tiles.

## 5. USB link

From the checkout, with the packaged app still quit:

```bash
cd host && .venv/bin/python -m companion run -v          # or: .venv/bin/python -m companion app --no-setup -v
cd host && .venv/bin/python -m companion status          # in a second terminal
cd host && .venv/bin/python -m companion detect
```

| Check | Expected |
|---|---|
| daemon log | `device hello fw=0.8.0` after connecting |
| `status` | `device         : connected on /dev/ttyACM0  fw=0.8.0  board=sqrm8  hello <n>s ago` |
| `detect` | the port as `native 303a:1001`, marked `[SQRM8 fw 0.8.0]` |
| screen | the real sessions and plan limits; tapping Focus raises the session's terminal |
| replug x5 | the daemon re-sends the full state after each (no stale screen) |
| USB-C to C cable from a USB-C host port, both plug orientations | link up both ways: checks J1's A and B signal rows and both CC pull-downs (R5, R6; a C source gives no VBUS without them) |
| USB-A to C cable | link up |
| bus-powered hub | link up, no reset of the other devices on the hub at plug-in (VBUS capacitance), no brown-out at backlight 100 |
| 10 min with real sessions | no reconnects in the daemon log |

## 6. Mechanical

1. Outline per board with calipers: 48.5 x 42.0 mm (V-cut tolerance about +-0.4 mm, est.). The board spans 22.0 to
   70.5 mm up from the bottom lens edge and 21.1 to 63.1 mm from the side lens edges, inside the panel's back.
2. J1 blade protrusion (from 1.3): it must stay inside the tape window without reaching the panel back once the
   foam is pressed; with 1.2 mm foam, reject above 0.9 mm (est.) and trim the blade instead.
3. Foam tape, 1.2 mm, cut to the outline, with one window under J1's four blades and their fillets: the blades sit at
   x 20.1 +- 1.43, y 21.0 +- 4.225, so a 5 x 11 mm window centred on (20.1, 21.0), long side along y; punch H1/H2
   (x 20.1, y 11.5 and 30.5) too if the jig's pins pass through. The window is symmetric about y = 21, so it is in
   the same place seen from either face.
4. Jig: datums are the lens edges and H1/H2, never the V-cut edges. Targets: J1's centre on the lens centre, the J2
   edge 22.0 mm up from the bottom lens edge (or the figure from 4.2.4). Nothing of ours in the first 15 mm above
   the bottom lens edge (tail fold, touch sub-flex).
5. Press with the lens face down on a flat soft support, through a pad relieved for J1, U1 and J2, never on parts.
6. Fold and insert the tail as in 4.2 (the latch is reachable with the board glued); repeat 4.3 and 4.6.
7. Case, once printed (`CASE.md`): J1's body (8.94 x 3.16 mm) through its hole with 0.1-0.15 mm per side; the
   bosses on H1/H2; the BOOT pin hole over SW1, 64.5 mm up from the bottom lens edge and 12 mm right of the centre
   line seen from the back; at least 0.5 mm over the module; the board's top edge at 70.5 mm up clears the pocket.
   Measure the J1 mouth height above the lens front (nominal 3.18 + 1.2 + 1.6 + 8.8 = 14.78 mm; the foam
   compresses) for the boss length.

## 7. Results

Electrical and function, one row per board (P = pass, F = fail; currents in mA, voltages in V):

| Serial | MAC | Commit | 1.3 insp. | C4 | J1 seat | J1 protr. mm | 1.5 R/C ok | VBUS-GND uF | I blank | VBUS | 3V3 | EN | LED_A off | Flash | hello board | I fw, no panel | LED_A on | Panel OK | V(R8) @100 | I @0 | I @100 | lowest lit bl | Whine | Bars | underruns 120 s quiet / demo / cycle | fps / cpu % | touch_ic | Link (5) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4B | | | - | - | - | - | - | - | - | | | - | - | | | | - | | - | | | | | | | | | | reference |
| 1 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 2 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 3 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 4 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 5 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 6 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 7 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 8 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 9 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 10 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 11 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| 12 | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |

Mechanical, one row per board:

| Serial | Panel lot | Outline mm | Tail slack mm | Tape window OK | Jig: J1 to lens centre mm | Flat after pressing | Case fit | J1 mouth height mm | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | |
| 2 | | | | | | | | | |
| 3 | | | | | | | | | |
| 4 | | | | | | | | | |
| 5 | | | | | | | | | |
| 6 | | | | | | | | | |
| 7 | | | | | | | | | |
| 8 | | | | | | | | | |
| 9 | | | | | | | | | |
| 10 | | | | | | | | | |
| 11 | | | | | | | | | |
| 12 | | | | | | | | | |

Brown-out (2.3), one or two boards: serial, VBUS at 3V3 < 3.20 V, VBUS at reset.

## Known risks of P2

Accepted for this batch, and what each looks like at the bench:

| Risk | Symptom |
|---|---|
| C4 perpendicular to the y = 42 V-cut, 1.35 mm from it | cracked open: VBUS capacitance 10-12 uF instead of 14-18 (1.5), the LDO's input less decoupled; cracked short: VBUS-GND short, host over-current, C4 hot; a partial crack leaks and gets worse over weeks |
| J1 blades (0.90 x 0.30) in 1.10 x 0.55 mm slots, pegs 0.70 in 0.80 mm holes; pin-in-paste fills only part of each slot | a blade that bound: tilted flange, open or bridged signal pads (no enumeration, power only, a link in one plug orientation only, or a link that drops when the cable is moved); thin fillets: the connector loosens under cable force |
| U1's exposed pad has 12 x 0.3 mm vias (filling and capping requested from the fab) | open vias wick solder: bumps under U1 on the bottom side (pressure on the panel), voids in the X-ray; the pad is one of only three module grounds |
| VBUS capacitance 14.7 uF nominal, about 10-11 uF effective at 5 V, near the 10 uF USB attach limit | other devices on a weak or bus-powered hub reset at plug-in; a host reports an over-current at attach |
| AMS1117: regulation specified only from 4.8 V in, 1.1 V dropout | 3V3 follows VBUS on long cables and weak hubs; brown-out resets around VBUS 3.9-4.0 V (est.) |
| AMS1117 output all ceramic (its datasheet asks for 22 uF tantalum for stability) | ringing or oscillation on 3V3 on a scope; random resets under load steps |
| AMS1117 heat on a board glued to the panel | a warm spot or mura on the picture over U2 after an hour at backlight 100 |
| No polyfuse; VBUS reaches LED_A through L1 and D2 with no switch in the path | a short on LED_A (damaged tail, mirrored tail) draws the host's over-current limit through SS14 and L1: current limit only with the panel in, D2 or L1 hot |
| Boost output charged to the 27 V OVP when the firmware runs without a panel | hot insertion into a charged C8: one LED string damaged, uneven or dim backlight at a normal V(R8) |
| PWM dimming on CTRL (200 Hz since the first board: 25 kHz saturated above 8 % duty) | flicker, a brightness step above about 86 %, the night (6 %) or dim (12 %) level out of line with the others; audible whine |
| Placement rotations not all confirmed (J1 had no library footprint at the assembler) | D1 rotated: VBUS-GND short at plug-in; U3 rotated: no backlight, U3 hot; D2 reversed: LED_A near 0 V with the boost off |
| Small parts 1.35-2.0 mm from the V-cuts (C4, L1, D2 and others) | cracked or lifted parts along the edges after separation |
| Tail reach set from one 4B measurement (+-0.5 mm) | the tail does not reach the stop, or humps and springs out before the latch closes |
| Console on UART0 pads only | a crash loop shows nothing on USB: a UART adapter on TP1/TP2 is the only way to read the panic |

## P3 candidates

- Rotate C4 parallel to the V-cut and move it at least 2.5 mm in (the assembler's preference for every part).
- J1: the drawing's 1.20 mm slots and 0.90 mm peg holes with a footprint-local clearance exception, and paste
  overprint for the blades, if the first batch shows binding or thin fillets.
- U1 exposed pad: move the vias out of the paste area (perimeter) or make filled and capped vias part of the fab
  specification.
- A low-dropout LDO or a small buck for 3V3 (dropout, all-ceramic stability, heat), and C1 at U1's 3V3 pin to 22 uF.
- VBUS: effective capacitance at or below 10 uF, or a soft start; a polyfuse or eFuse; a VBUS TVS (the 4B has one).
- Test pads for VBUS and LED_K.
- USB: 0 ohm footprints on D+/D- near U1; the USBLC6 closer to J1.
- EN: a discharge diode across R1 for fast replugs.
- Firmware: a minimum CTRL duty or another PWM frequency if the low end or the whine fails 4.5; interrupt-driven
  touch on GPIO16 (TP_INT, still polled); a release with the sqrm8 profile (planned: 0.8.0).
