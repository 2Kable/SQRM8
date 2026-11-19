#pragma once
// Board profiles. One firmware image runs on both boards: hal.cpp probes the I2C bus at boot (a TCA9554 at 0x20
// answers only on the 4B) and takes the expander or the direct-GPIO path from there (hal_board()).
//
// Waveshare ESP32-S3-Touch-LCD-4B (ESP32-S3R8 module, 8 MB OPI PSRAM, 16 MB flash, ST7701 480x480 RGB panel,
// GT911 touch). A TCA9554 expander @0x20 carries the panel's 3-wire SPI init bus, the panel reset and the touch
// reset/INT; backlight PWM on GPIO4 (AP3032, inverted); I2C on 47/48.
// Host link = the "USB-OTG" port (native USB-Serial-JTAG). The "USB TO UART" port is a CH343 on UART0 and is
// only used for flashing.
// Sources: 4B schematic + Waveshare BSP (waveshare/esp32_s3_touch_lcd_4b) + Arduino demo 06_LVGL_Arduino_v9.
// (The older ESP32-S3-Touch-LCD-4 V4 with its CH32V003 expander was supported until firmware 0.3.0.)
//
// sqrm8, the SQRM8 board, our own (hardware/BOARD.md, KiCad project hardware/pcb/sqrm8): ESP32-S3-WROOM-1-N16R8,
// same RGB/sync/I2C/USB/UART/BOOT pins and the same backlight pin as the 4B, no expander: the five pins the 4B map
// leaves free carry the panel's init bus, one reset line shared by the panel and the GT911, and the touch INT.
#include <stdint.h>

enum class Board : uint8_t { WS4B, SQRM8 };
Board board_kind();   // detected by hal_init (WS4B until then); the hello's board name: hal_board_name()

// Shared by both boards
#define BOARD_I2C_SDA 47
#define BOARD_I2C_SCL 48
#define BOARD_LCD_HSYNC 46
#define BOARD_LCD_VSYNC 3
#define BOARD_LCD_DE 17
#define BOARD_LCD_PCLK 9
// esp_lcd order: B0-4 G0-5 R0-4 (schematic nets B1-5 = IO40 41 42 2 1, G0-5 = IO21 8 18 45 38 39, R1-5 = IO10-14)
#define BOARD_LCD_DATA {40, 41, 42, 2, 1, 21, 8, 18, 45, 38, 39, 10, 11, 12, 13, 14}
#define BOARD_BL_PIN 4

// 4B: the TCA9554 pins
#define BOARD_4B_NAME "ESP32-S3-Touch-LCD-4B"
#define BOARD_EXPANDER_ADDR 0x20
#define BOARD_EXIO_LCD_CS 0
#define BOARD_EXIO_LCD_SDA 1
#define BOARD_EXIO_LCD_SCL 2
// EXIO3 = audio amp enable, EXIO4 = PWR key sense (input): both left alone
#define BOARD_EXIO_TP_RST 5
#define BOARD_EXIO_TP_INT 6
#define BOARD_EXIO_LCD_RST 7
// 4B backlight: PWM into the AP3032's FB node through an RC filter (a higher duty dims: inverted)
#define BOARD_4B_BL_HZ 5000

// sqrm8: direct GPIOs
#define BOARD_SQRM8_NAME "sqrm8"
#define BOARD_SQRM8_LCD_CS 5     // 10k pull-up: deselected until the firmware drives it
#define BOARD_SQRM8_LCD_SCL 6
#define BOARD_SQRM8_LCD_SDA 7    // the panel's SDA is bidirectional; the firmware only writes
#define BOARD_SQRM8_RST 15       // panel RESX and GT911 RST together; 10k pull-down holds both in reset at boot
#define BOARD_SQRM8_TP_INT 16    // GT911 INT; driven low through the reset release (address 0x5D), then an input
// sqrm8 backlight: GPIO4 drives the AP3032 CTRL pin itself (100k pull-down: off until the firmware runs).
// Duty = brightness, not inverted. 200 Hz, not the tens of kHz the AP3032 datasheet suggests: at 25 kHz the
// output capacitors carry the LEDs through the 40 us off-time and the brightness saturates above 8 % duty; 1 kHz
// dims over the whole range but whines at 40-80 %; 200 Hz does both (first P2 board, 2026-11-19, by eye and ear).
// Under BOARD_SQRM8_BL_MIN the on-time is too short to light the LEDs.
#define BOARD_SQRM8_BL_HZ 200
#define BOARD_SQRM8_BL_MIN 31    // lowest lit duty of 1024 (3 %)

// Panel orientation: 1 = the UI is drawn rotated by 180 degrees (the picture upright with the board's
// connectors on the side the user wants). Set per build with -DHAL_ROT180=0/1; this is the 4B's value.
#ifndef HAL_ROT180
#define HAL_ROT180 1
#endif
// The sqrm8 board sits the other way up behind its panel: its picture is turned half a turn from the 4B's.
#define BOARD_SQRM8_ROT180 (!HAL_ROT180)
