# SQRM8 hardware

The open design of the SQRM8 device: a 4" 480x480 touch panel on a small ESP32-S3 board, USB-C at the back, in a
printed case. Everything the firmware needs is here, so you can build your own; the assembled device from us costs
less than a one-off build once the panel, the boards and the time are counted.

| Path | What |
|---|---|
| `PANEL.md` | the display: reference, interface, pinout, mechanical data |
| `BOARD.md` | the board design: blocks, pin map, position on the panel, stack |
| `CASE.md` | the case: dimensions to respect, colour target, printing notes |
| `BRINGUP.md` | the bench procedure for the first boards: inspection, power-up, first flash, panel, USB link, mechanics, results table, known risks |
| `pcb/` | the KiCad 10 project (`sqrm8.kicad_pro`, schematic, board, footprints, 3D models) and the scripts that generate it |
| `../docs/CUSTOMIZING.md` | adapting the firmware to your own board, panel or taste |

The board is generated from Python (`pcb/build_*.py`) with a private KiCad toolchain; the committed KiCad files
are complete and open in KiCad 10 without it. Order files for a specific fab are not published.

Built on the Waveshare ESP32-S3-Touch-LCD-4B pin map, so one firmware image runs on either board: it detects
the board at boot (`firmware/src/core/hal.cpp`, profiles in `board.h`).
