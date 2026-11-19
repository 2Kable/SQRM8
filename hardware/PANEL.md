# The panel

**EastRising ER-TFT040-3 with the capacitive touch option** (sold as ER-TFT040-3 + ER-TPC040-3): 4.0" IPS,
480x480, ST7701S controller, 3-wire SPI for registers plus 18-bit parallel RGB, capacitive touch on a GT911,
everything on one 40-pin 0.5 mm FPC. It is the same glass as the Waveshare ESP32-S3-Touch-LCD-4B, so the
firmware's init table, timings and touch driver apply unchanged. Any panel with the pinout below works.

| Item | Value |
|---|---|
| Active area / outline | 71.86 x 70.18 mm / 74.66 x 76.54 x 2.1 mm (panel), lens 84.2 x 84.2 mm, 3.18 mm total with touch |
| Brightness, contrast, viewing | 400 cd/m2, 800:1, 80 deg all sides |
| Logic supply | 2.5-3.3 V (3.3 V here), VIH 0.7 VDD |
| Backlight | 10 white LEDs as 2 strings of 5: 15 V typ / 16 V max at 40 mA total, 30 mA typ |
| Touch | GT911, I2C at 0x5D (INT low at reset) or 0x14, 3.3 V |
| Driven as | RGB565 at 12 MHz pixel clock, DB0 and DB12 driven with B5 and R5 (the top bit repeated, so full white is true white) |
| Cover lens | black printed border only |

## 40-pin FPC

| Pin | Signal | | Pin | Signal |
|---|---|---|---|---|
| 1 | LEDA | | 16 | DB0 (B0, to GND) |
| 2, 3 | LEDK | | 17-21 | DB1-DB5 (blue) |
| 4, 34, 40 | GND | | 22-27 | DB6-DB11 (green) |
| 5 | VDD | | 28 | DB12 (R0, to GND) |
| 6 | RESET | | 29-33 | DB13-DB17 (red) |
| 7, 8 | NC | | 35 | TP_INT |
| 9 / 10 / 11 | SPI SDA / SCK / CS | | 36 / 37 | TP_SDA / TP_SCL |
| 12 / 13 / 14 / 15 | PCLK / DE / VS / HS | | 38 | TP_RST |
| | | | 39 | TP_VCC |

## Mechanics of the tail

The tail leaves the BOTTOM edge of the upright screen (the datasheet's drawings are rotated 90 degrees; the
label reads upright with the tail at the bottom; confirmed on a Waveshare 4B, same glass). Its root is 33.57 mm
wide, starting 19.12 mm from the panel's left corner; the 20.5 mm contact strip is centred on the panel width.
The tail is 27 mm long and folds onto the back of the panel: measured on a 4B, the contact end then lies 25 mm
in from the panel's bottom edge (datasheet: 24 +- 0.5), i.e. about 27.5 mm from the bottom lens edge, with pin 1
at the RIGHT end seen from the back (left end seen from the front: the fold about the bottom edge keeps left and
right) and the contacts facing the panel (a dual-contact connector takes either face). The touch controller sits on a sub-flex near the fold, within about
15 mm of the bottom lens edge, up to 1.4 mm thick. The backlight's back is metal.
