# Case

Two printed parts, a bezel frame and a back shell, around the panel with the board glued on its back.

## Dimensions to respect (see `BOARD.md`, stack)

| Layer | mm | Total |
|---|---|---|
| Lens + touch + LCD | 3.18 | 3.18 |
| Foam tape 1.2 mm, windows under the USB-C blades | 1.2 | 4.38 |
| PCB | 1.6 | 5.98 |
| ESP32-S3 module | 3.2 | 9.18 |
| Back shell over the module (0.5 clearance + 2 mm wall) | | ~11.7 |
| USB-C, 8.8 mm above the PCB | | 14.8: a boss in the shell around the port, mouth flush with its outer face |

- The lens is 84.2 x 84.2 mm with a black printed border; the bezel frames it.
- The USB-C passes through a close-fitting hole (body 8.94 x 3.16 mm plus 0.1-0.15 mm per side for FDM; its 12 x 5 mm flange sits on the board); two
  bosses on the board's 2.2 mm holes next to the port clamp the board so cable loads go into the shell.
- Keep the first 15 mm above the bottom lens edge free behind the panel: the tail fold and the touch
  controller's sub-flex live there. The USB-C exits on the centre line at mid-height; a pin hole in the shell
  reaches the BOOT button.
- Walls 2 mm or an opaque filament: translucent PLA lets the backlight glow through.

## Colour

The device colour is the UI's accent, Claude orange `#D97757` (`firmware/src/ui/theme.h`), a muted orange
between filament "orange" and "terracotta" families: Pantone 2433 C or RAL 2012 are the nearest references for
a supplier. Common PLA oranges are more saturated and yellower, terracottas darker; print a swatch and judge it
in daylight next to the screen. A matte charcoal bezel around the black lens with an orange shell is the
fallback when no spool matches.
