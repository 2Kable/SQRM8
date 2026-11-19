# Board spec (2026-11-06)

The minimum board that runs the firmware as it is, glued on the back of the panel (`PANEL.md`), single-sided
SMT with one hand-soldered connector. The KiCad project is in `pcb/`.

## Blocks and parts (LCSC codes as in the schematic)

| Block | Part | LCSC | Notes |
|---|---|---|---|
| MCU | ESP32-S3-WROOM-1-N16R8 | C2913202 | 16 MB flash, 8 MB octal PSRAM, 3.3 V. Fully inside the outline (the board is panelised with V-cuts), with Espressif's copper keep-out on all layers under the antenna, so the radio stays usable |
| 3.3 V | AMS1117-3.3 SOT-223 + 4.7 uF/25 V 0805 in (C1779) / 22 uF out | C6186 | ~250 mA load; the 1.1 V dropout from 5 V is fine. VBUS caps are 25 V parts (a 10 V X5R keeps ~40 % at 5 V): 4.7 + 10 uF, ~15 uF nominal |
| Backlight | AP3032KTR-G1 + 10 uH (C45403) + SS14 (C2480) + 1 uF/50 V (C28323) + 100 nF + 10 uF/25 V 0805 in (C15850) | C264086 | input from VBUS (5 V); FB straight on LED_K, 6.8 ohm 1 % sense (C23214, Extended: no Basic 6.8 ohm) = 29 mA; GPIO4 PWM into CTRL via 100 ohm, 100k pull-down: off while GPIO4 floats (boot, download mode) |
| USB | vertical HRO TYPE-C-31-D-15 (SMD signal pins, four 2.2 mm shell blades soldered through the board, 12 x 5 mm flange, 8.8 mm tall) + 2 x 5.1k CC pull-downs + USBLC6-2SC6 | C22464480, C2687116 | D+/D- to GPIO 19/20; shell to GND; no polyfuse. Reflowed with the rest of the board (pin-in-paste on the blade slots); the unplug force goes through the soldered blades, not the signal pads. Same land pattern as Hong Cheng LT02A and hanxia 180 LT H9.3/H10 (second sources); the all-THT HRO D-09 and the SHOU HAN LTH6.8 footprints stay in the library |
| Panel | 40-pin 0.5 mm FPC, flip lock, dual contact | C2856837 | on the board's tail edge (left seen from the back), entry facing the panel's bottom edge; 1 uF + 100 nF on VCC and on TP_VCC; DB0 = B5 and DB12 = R5 (top bit repeated: true white); 10k pull-down on LCD_RST and 10k pull-up on LCD_CS hold the panel until the firmware drives them |
| Buttons | BOOT tactile 4 x 3 mm (C720477), EN 10k + 1 uF | | no reset button: EN test pad (TP5) |
| Debug | pads for TXD0 / RXD0 (GPIO 43/44), GND, 3V3, EN | | |
| Mechanics | 1.6 mm 4-layer (kept: the USB-C shell blades protrude 0.55 mm nominal, up to 0.96 mm, below a 1.6 mm board), two 2.2 mm holes for the jig / case bosses near the USB-C; the adhesive gets a cut-out under the USB-C legs | | |

## Pin map (ESP32-S3-WROOM-1), identical to `firmware/src/core/board.h` plus the expander replaced

| Function | GPIO | Panel pin |
|---|---|---|
| PCLK / DE / VS / HS | 9 / 17 / 3 / 46 | 12 / 13 / 14 / 15 |
| B1-B5 | 40 41 42 2 1 | 17-21 |
| G0-G5 | 21 8 18 45 38 39 | 22-27 |
| R1-R5 | 10 11 12 13 14 | 29-33 |
| DB0, DB12 (= B5, R5) | 1, 14 | 16, 28 |
| LCD_CS / LCD_SCL / LCD_SDA (3-wire init SPI) | 5 / 6 / 7 | 11 / 10 / 9 |
| RST (LCD and touch, shared) | 15 | 6 and 38 |
| TP_INT | 16 | 35 |
| I2C SDA / SCL (+4.7k pull-ups) | 47 / 48 | 36 / 37 |
| Backlight PWM | 4 | (AP3032 CTRL) |
| USB D- / D+ | 19 / 20 | |
| UART0 TX / RX | 43 / 44 | pads |
| BOOT | 0 | button to GND |

Only five GPIOs are free after the 4B map (5, 6, 7, 15, 16), so the panel and touch resets share one line;
the firmware drives TP_INT low during the reset pulse so the GT911 answers at 0x5D. GPIO 35-37 belong to the
PSRAM and stay unconnected. No pull-ups on 45 and 46 (strapping).

## Position on the panel (lens 84.2 x 84.2 mm; geometry confirmed on a 4B, same glass)

- The tail leaves the bottom edge of the upright screen; folded, its contact end lies 25 mm up from the
  panel's bottom edge (about 27.5 mm from the bottom lens edge), the 20.5 mm strip centred on the panel width,
  pin 1 at the right end seen from the back (P2 ordered on the drawing; checked against the 4B at bring-up). The FPC only has to enter the connector 2.1 mm past its entry edge.
- Board frame (KiCad top view, y down): the tail edge is the board's LEFT edge (x = 0) with J2 along it, entry
  facing -x, and the strip axis is y. The board is mounted rotated 90 degrees so that edge is at the bottom of the
  device. Board y = 18 (strip centre) is the panel's vertical centre line; the connector entry (board x 1.1) sits
  23 mm up from the bottom lens edge, so the board's tail edge is 22 mm up (the rise onto the PCB costs 1-2 mm of
  tail; a sample check sets the final figure +-0.5 mm; the jig references the lens edges).
- The USB-C is on the centre line (board y = 21) at mid-height of the panel (board x 20.1, i.e. 42.1 mm up
  from the bottom lens edge), cable straight back; the two 2.2 mm holes flank it on the centre line's sides for
  the shell bosses (locating only: no screw access once glued).
- The touch sub-flex occupies the first 15 mm above the bottom lens edge: nothing of ours there.
- Outline 48.5 x 42 mm (P2: x up the panel, 22 to 70.5 mm; y across, centred), plain rectangle with square corners so a panel separates entirely by V-cuts; copper,
  parts and silk at least 1 mm from every edge; the FPC and USB connectors and the module as far from the
  V-cut edges as the outline allows.
- Silkscreen name: the P2 boards already ordered carry the pre-rename text `CLAUDIUS` / `MAXIMUS` / `cmax P2`;
  P3 gets `SQRM8 P3`.

## Stack (components towards the back shell)

| Layer | mm | Total |
|---|---|---|
| Lens + touch + LCD | 3.18 | 3.18 |
| foam tape 1.2 mm (windows under the USB-C blades) | 1.2 | 4.38 |
| PCB | 1.6 | 5.98 |
| ESP32-S3-WROOM-1 | 3.2 | 9.18 |
| back shell (0.5 clearance + 2 mm wall) | | ~11.7 |
| USB-C 8.8 mm above the PCB | | 14.8: the back shell gets a boss around the port, mouth flush with its outer face |

## Firmware changes implied (done on branch `hardware`, not yet run on an SQRM8 board)

- One image for both boards: `hal.cpp` `board_init` probes I2C 0x20 (3 tries); a TCA9554 ACK = 4B, none = sqrm8
  (`board_kind()`). The hello reports `"board":"sqrm8"`; the app maps it to the same firmware bundle as the 4B
  (`flasher.BUNDLES`) and no longer assumes a 4B for a device that sends no hello.
- `board.h`: `BOARD_SQRM8_LCD_CS/SCL/SDA` 5/6/7, `BOARD_SQRM8_RST` 15, `BOARD_SQRM8_TP_INT` 16, `BOARD_SQRM8_BL_HZ`.
- Init bus: the same 9-bit bit-bang on GPIOs, 2 us per edge (~250 kHz), write-only, CS high when idle.
- Reset: CS/SCL/SDA high, INT low, RST low 20 ms, RST high, INT low 60 ms more, INT to input (no pull), 60 ms
  more, then the panel init; the GT911 address probe (0x5D, then 0x14) stays. Touch is still polled (TODO for an
  INT-driven read on GPIO16). Never re-pulse GPIO15 for the touch alone: it resets the panel too.
- Backlight: LEDC on GPIO4 drives CTRL at 200 Hz, 10 bit, duty = brightness (not inverted), 0 = off and 0 at
  boot; 1 and 2 % are raised to 3 % duty, the lowest that lights the panel. The 4B keeps its inverted FB injection
  at 5 kHz. The AP3032 datasheet suggests > 25 kHz, but on the first P2 board (2026-11-19, by eye and ear) 25 kHz
  dimmed only up to 8 % duty and was flat above (the output capacitors carry the LEDs through the 40 us off-time),
  and 1 kHz dimmed over the whole range but whined at 40-80 %; 200 Hz dims over the whole range without whine.
  Above about 86 % the low phase drops under 0.7 ms and the AP3032 holds standby instead of soft-starting: a step
  in brightness there is possible, not checked. 100 % = CTRL constantly high = the full R_sense current; there is
  no firmware cap. P3 candidate: dim through FB as the 4B does.
- Orientation: the sqrm8 picture is turned half a turn from the 4B's (`BOARD_SQRM8_ROT180` in `board.h`, chosen at
  boot with the board; framebuffer, touch and the screenshot header follow it).
- Brown-out reset raised to 2.84 V (`CONFIG_ESP_BROWNOUT_DET_LVL_SEL_4`) for both boards.
- `st7701_init.h`: diff against EastRising's init zip once downloaded; expected identical.

## Build flow

`pcb/` is generated from Python (`build_sch.py` schematic, `build_lib.py` footprints, `build_pcb.py` placement
and zones, `route_board.py` routing) with a private KiCad toolchain; see `pcb/README.md`. The committed KiCad
files are the result and open in KiCad 10 on their own.
