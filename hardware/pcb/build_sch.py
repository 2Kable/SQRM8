#!/usr/bin/env python3
"""Build sqrm8.kicad_sch (SQRM8 display board: ESP32-S3-WROOM-1 + 40-pin RGB panel FPC, USB-C powered)
and the project library sqrm8.kicad_sym. Spec: hardware/BOARD.md.

Run through the excalibur tools, used in place and read-only (see README.md):
  cd $KICAD_TOOLS/../.. && PYTHONDONTWRITEBYTECODE=1 tools/kicad/board.sh /path/to/hardware/pcb sch

The AP3032 boost and the panel FPC connector are drawn here (no KiCad library symbol fits) and go into
sqrm8.kicad_sym like every other symbol."""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get('KICAD_TOOLS', '/home/damien/projects/iot-hw-excalibur/tools/kicad'))
import schgen

g = schgen.Schematic('sqrm8', os.path.join(HERE, 'sqrm8.kicad_sch'), paper='A3',
                     title='SQRM8 display board', rev='P3', company='', date='2026-11-08')


# ---------------------------------------------------------------- custom symbols (KiCad tab layout: schgen parses them with regexes)
def _pin(typ, x, y, ang, name, num):
    e = '\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)'
    return ('\n\t\t\t(pin %s line\n\t\t\t\t(at %s %s %d)\n\t\t\t\t(length 2.54)\n\t\t\t\t(name "%s"%s\n\t\t\t\t)\n\t\t\t\t(number "%s"%s\n\t\t\t\t)\n\t\t\t)'
            % (typ, schgen._f(x), schgen._f(y), ang, name, e, num, e))


def _prop(name, val, x, y, hide):
    return ('\n\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)%s\n\t\t\t(effects\n\t\t\t\t(font\n'
            '\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)' % (name, val, schgen._f(x), schgen._f(y), '\n\t\t\t(hide yes)' if hide else ''))


def _symbol(name, ref, value, fp, ds, desc, kw, fpf, box, pins):
    """One single-unit symbol: box = (x0, y0, x1, y1) body rectangle, pins = [(type, x, y, angle, name, number)]."""
    s = '\n\t(symbol "%s"\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(duplicate_pin_numbers_are_jumpers no)' % name
    s += _prop('Reference', ref, box[0], box[1] + 1.27, False) + _prop('Value', value, box[2], box[1] + 1.27, False)
    s += _prop('Footprint', fp, 0, box[3] - 5.08, True) + _prop('Datasheet', ds, 0, 0, True) + _prop('Description', desc, 0, 0, True)
    s += _prop('ki_keywords', kw, 0, 0, True) + _prop('ki_fp_filters', fpf, 0, 0, True)
    s += ('\n\t\t(symbol "%s_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start %s %s)\n\t\t\t\t(end %s %s)\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n'
          '\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)\n\t\t)'
          % (name, schgen._f(box[0]), schgen._f(box[1]), schgen._f(box[2]), schgen._f(box[3])))
    s += '\n\t\t(symbol "%s_1_1"' % name
    for p in pins: s += _pin(*p)
    s += '\n\t\t)\n\t\t(embedded_fonts no)\n\t)'
    return s


def ap3032_symbol():
    """AP3032 datasheet Rev 1.2 p.2 (SOT-23-6 top view): 1 SW, 2 GND, 3 FB, 4 CTRL, 5 OV, 6 VIN."""
    pins = [('power_in', -10.16, 2.54, 0, 'VIN', '6'), ('input', -10.16, -2.54, 0, 'CTRL', '4'),
            ('passive', 10.16, 2.54, 180, 'SW', '1'), ('input', 10.16, 0, 180, 'OV', '5'), ('input', 10.16, -2.54, 180, 'FB', '3'),
            ('power_in', 0, -7.62, 90, 'GND', '2')]
    return _symbol('AP3032KTR-G1', 'U', 'AP3032KTR-G1', 'sqrm8:SOT-23-6', '~',
                   'White LED boost converter, 1 MHz, VIN 2.7-9 V, FB 200 mV, OVP 27 V, SOT-23-6', 'LED driver boost backlight',
                   'SOT?23*', (-7.62, 5.08, 7.62, -5.08), pins)


PANEL = ['LED_A', 'LED_K', 'LED_K', 'GND', 'VDD', 'RST', 'NC', 'NC', 'SDA', 'SCK', 'CS', 'PCLK', 'DE', 'VS', 'HS'] + \
        ['DB%d' % i for i in range(18)] + ['GND', 'TP_INT', 'TP_SDA', 'TP_SCL', 'TP_RST', 'TP_VCC', 'GND']


def panel_symbol():
    """40-pin FPC carrying the ER-TFT040-3 tail, pins named after the panel datasheet (pin n = panel pin n), S1 = anchor pads."""
    def typ(n): return 'power_in' if n in ('GND', 'VDD', 'TP_VCC') else 'no_connect' if n == 'NC' else 'passive'
    pins = [(typ(n), -10.16, 50.8 - 2.54 * i, 0, n, str(i + 1)) for i, n in enumerate(PANEL)]
    pins.append(('passive', 0, -53.34, 90, 'MP', 'S1'))     # anchor pads, named S1 in sqrm8.pretty
    return _symbol('ER-TFT040-3_FPC40', 'J', 'FPC-05FB-40PH20', 'sqrm8:FPC_0.5mm_40P_XUNPU_FPC-05FB-40PH20',
                   '~',
                   '40-pin 0.5 mm FPC, flip lock, dual contact, wired for the EastRising ER-TFT040-3 tail (RGB + 3-wire SPI + backlight + GT911)',
                   'FPC FFC LCD RGB ST7701 GT911', 'FPC*0.5mm*40P*', (-7.62, 53.34, 7.62, -50.8), pins)


CUSTOM = os.path.join(schgen.SYMDIR, 'sqrm8_custom.kicad_sym')        # virtual library, served from the SymLib cache
g.lib.cache[CUSTOM] = '(kicad_symbol_lib\n\t(version 20251024)' + ap3032_symbol() + panel_symbol() + '\n)\n'

# ---------------------------------------------------------------- passives
CAP = {'100n': ('C14663', 'C_0603_1608Metric'), '10u': ('C19702', 'C_0603_1608Metric'), '22u': ('C45783', 'C_0805_2012Metric'),
       '1u': ('C15849', 'C_0603_1608Metric'), '1u 50V': ('C28323', 'C_0805_2012Metric'),
       # VBUS caps rated 25 V: a 10 V X5R keeps ~40 % of its value at 5 V; no Basic 4.7 uF 25 V exists in 0603
       '4.7u 25V': ('C1779', 'C_0805_2012Metric'), '10u 25V': ('C15850', 'C_0805_2012Metric')}
RES = {'4.7k': 'C23162', '5.1k': 'C23186', '10k': 'C25804', '100k': 'C25803', '100R': 'C22775',
       '6.8R': 'C23214'}       # 6.8 R 1 %: no Basic part, same UNI-ROYAL series as the 5.1 R it replaces
G = 2.54


def grid(x, y): return (round(x / G) * G, round(y / G) * G)


def R(ref, val, pos, p1, p2, desc=''):
    """Vertical resistor: pin 1 on top."""
    g.add(ref, 'Device:R', grid(*pos), 0, value=val, footprint='sqrm8:R_0603_1608Metric', lcsc=RES[val], pins={'1': p1, '2': p2}, desc=desc)


def C(ref, val, pos, p1, p2, desc=''):
    """Vertical capacitor: pin 1 on top."""
    lc, fp = CAP[val]
    g.add(ref, 'Device:C', grid(*pos), 0, value=val, footprint='sqrm8:' + fp, lcsc=lc, pins={'1': p1, '2': p2}, desc=desc)


# no flag on +3V3: U2's VO is a power output already (a flag there is a power_out/power_out ERC error)
for i, net in enumerate(['VBUS', 'GND', 'LED_A']):
    g.add('#FLG%d' % (i + 1), 'power:PWR_FLAG', grid(155 + 20 * i, 190), 0, value='PWR_FLAG', pins={'1': net}, in_bom=False)

# ---------------------------------------------------------------- MCU: ESP32-S3-WROOM-1-N16R8 (pin map = firmware/src/core/board.h)
g.text('MCU: ESP32-S3-WROOM-1-N16R8', (15, 25), 2.5, True)
g.text('RGB565 panel bus as the Waveshare 4B; GPIO 35-37 = octal PSRAM, unconnected', (15, 30), 1.5)
g.text('no pull-ups on the strapping pins 45/46 (LCD_G3 / LCD_HS)', (15, 34), 1.5)
GPIO = {0: 'BOOT', 1: 'LCD_B5', 2: 'LCD_B4', 3: 'LCD_VS', 4: 'BL_PWM', 5: 'LCD_CS', 6: 'LCD_SCL', 7: 'LCD_SDA', 8: 'LCD_G1',
        9: 'LCD_PCLK', 10: 'LCD_R1', 11: 'LCD_R2', 12: 'LCD_R3', 13: 'LCD_R4', 14: 'LCD_R5', 15: 'LCD_RST', 16: 'TP_INT',
        17: 'LCD_DE', 18: 'LCD_G2', 21: 'LCD_G0', 35: 'NC', 36: 'NC', 37: 'NC', 38: 'LCD_G4', 39: 'LCD_G5', 40: 'LCD_B1',
        41: 'LCD_B2', 42: 'LCD_B3', 45: 'LCD_G3', 46: 'LCD_HS', 47: 'I2C_SDA', 48: 'I2C_SCL'}
BYNAME = {'GND': 'GND', '3V3': '+3V3', 'EN': 'EN', 'USB_D-': 'USB_N', 'USB_D+': 'USB_P', 'TXD0': 'TXD0', 'RXD0': 'RXD0'}
BYNAME.update({'IO%d' % k: v for k, v in GPIO.items()})
u1 = {num: BYNAME[name] for num, name, *_ in g.lib.pins('RF_Module', 'ESP32-S3-WROOM-1')}   # KeyError = unmapped module pin
g.add('U1', 'RF_Module:ESP32-S3-WROOM-1', grid(80, 95), 0, value='ESP32-S3-WROOM-1-N16R8', footprint='sqrm8:ESP32-S3-WROOM-1',
      lcsc='C2913202', mpn='ESP32-S3-WROOM-1-N16R8', desc='ESP32-S3 module, 16 MB flash, 8 MB octal PSRAM, PCB antenna (radio unused)', pins=u1)

g.text('3V3 decoupling, EN, BOOT', (15, 150), 2.0, True)
C('C1', '10u', (20, 165), '+3V3', 'GND', desc='3V3 bulk at U1 pin 2')
C('C2', '100n', (30, 165), '+3V3', 'GND', desc='3V3 at U1 pin 2')
R('R1', '10k', (45, 165), '+3V3', 'EN', desc='EN pull-up (RC reset with C3)')
C('C3', '1u', (55, 165), 'EN', 'GND', desc='EN delay: 10k x 1 uF, 3V3 settles before the chip starts')
R('R2', '10k', (70, 165), '+3V3', 'BOOT', desc='GPIO0 pull-up (the internal one suffices; belt and braces)')
g.add('SW1', 'Switch:SW_Push', grid(80, 170), 90, value='BOOT', footprint='sqrm8:SW_TS-1088', lcsc='C720477', mpn='TS-1088-AR02016',
      desc='BOOT: hold while plugging in for the ROM download mode', pins={'2': 'BOOT', '1': 'GND'})
g.text('I2C pull-ups (GT911)', (95, 150), 2.0, True)
R('R3', '4.7k', (100, 165), '+3V3', 'I2C_SDA', desc='I2C SDA pull-up')
R('R4', '4.7k', (110, 165), '+3V3', 'I2C_SCL', desc='I2C SCL pull-up')

g.text('Debug pads and mounting holes', (15, 200), 2.0, True)
for i, (ref, net) in enumerate([('TP1', 'TXD0'), ('TP2', 'RXD0'), ('TP3', 'GND'), ('TP4', '+3V3'), ('TP5', 'EN')]):
    g.add(ref, 'Connector:TestPoint', grid(20 + i * 14, 215), 0, value=net, footprint='sqrm8:TestPoint_Pad_1.5x1.5mm', in_bom=False,
          desc='EN pad: short to GND to reset' if net == 'EN' else 'debug pad (UART0 console, power)', pins={'1': net})
for i, ref in enumerate(['H1', 'H2']):
    g.add(ref, 'Mechanical:MountingHole', grid(100 + i * 20, 215), 0, value='2.2mm', footprint='sqrm8:MountingHole_2.2mm',
          in_bom=False, desc='2.2 mm hole for the assembly jig / case boss, near the USB-C', pins={})

# ---------------------------------------------------------------- USB-C, ESD, 3.3 V LDO
g.text('USB-C (device), CC, ESD', (150, 25), 2.5, True)
g.text('vertical receptacle, SMD signal pins, shell blades soldered through; shell to GND; no polyfuse', (150, 30), 1.5)
g.add('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', grid(175, 75), 0, value='TYPE-C-31-D-15', lcsc='C22464480',
      footprint='sqrm8:USB_C_Vertical_HRO_TYPE-C-31-D-15', mpn='TYPE-C-31-D-15', desc='USB-C 2.0 receptacle, vertical, soldered shell blades, 8.8 mm (UFP)',
      pins={'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND', 'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
            'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_P', 'B6': 'USB_P', 'A7': 'USB_N', 'B7': 'USB_N', 'A8': 'NC', 'B8': 'NC'})
R('R5', '5.1k', (215, 75), 'CC1', 'GND', desc='CC1 Rd pull-down (UFP, 5 V default power)')
R('R6', '5.1k', (225, 75), 'CC2', 'GND', desc='CC2 Rd pull-down (UFP, 5 V default power)')
g.add('D1', 'Power_Protection:USBLC6-2SC6', grid(255, 75), 0, value='USBLC6-2SC6', footprint='sqrm8:SOT-23-6', lcsc='C2687116',
      mpn='USBLC6-2SC6', desc='ESD on D+/D- and VBUS at J1', pins={'1': 'USB_P', '6': 'USB_P', '3': 'USB_N', '4': 'USB_N', '2': 'GND', '5': 'VBUS'})

g.text('3.3 V: AMS1117-3.3 from VBUS', (150, 120), 2.5, True)
g.text('~250 mA, 1.1 V dropout from 5 V; tab = VOUT', (150, 125), 1.5)
g.add('U2', 'Regulator_Linear:AMS1117-3.3', grid(190, 145), 0, value='AMS1117-3.3', footprint='sqrm8:SOT-223-3_TabPin2', lcsc='C6186',
      mpn='AMS1117-3.3', desc='3.3 V 1 A LDO', pins={'3': 'VBUS', '2': '+3V3', '1': 'GND'})
C('C4', '4.7u 25V', (160, 145), 'VBUS', 'GND', desc='U2 input (VBUS total ~15 uF nominal with C7)')
C('C5', '22u', (220, 145), '+3V3', 'GND', desc='U2 output (datasheet: 22 uF)')
C('C6', '100n', (230, 145), '+3V3', 'GND', desc='U2 output HF')
g.text('Power flags', (150, 180), 1.5)

# ---------------------------------------------------------------- backlight: AP3032 boost, Waveshare 4B topology, VIN from VBUS
g.text('Backlight: AP3032, PWM on CTRL (25 kHz), 29 mA; off at boot', (262, 120), 2.0, True)
g.text('I_LED = 200 mV / 6.8 R = 29 mA (2 strings x 5 LEDs, 15-16 V); FB straight on LED_K', (262, 125), 1.5)
g.text('BL_PWM (GPIO4) via 100 R into CTRL: duty = brightness (not inverted);', (262, 129), 1.5)
g.text('low < 0.7 ms keeps the AP3032 in standby, no soft-start per cycle', (262, 133), 1.5)
g.text('100k pull-down: off while GPIO4 floats (power-up, download mode)', (262, 137), 1.5)
g.add('U3', 'sqrm8_custom:AP3032KTR-G1', grid(300, 155), 0, value='AP3032KTR-G1', footprint='sqrm8:SOT-23-6', lcsc='C264086',
      mpn='AP3032KTR-G1', desc='WLED boost, 1 MHz, FB 200 mV, OVP 27 V',
      pins={'6': 'VBUS', '4': 'BL_EN', '1': 'BL_SW', '5': 'LED_A', '3': 'LED_K', '2': 'GND'})
C('C7', '10u 25V', (265, 180), 'VBUS', 'GND', desc='U3 VIN')
g.add('L1', 'Device:L', grid(280, 180), 0, value='10uH', footprint='sqrm8:L_SWPA3015S', lcsc='C45403', mpn='SWPA3015S100MT',
      desc='boost inductor 10 uH, 3x3x1.5 mm', pins={'1': 'VBUS', '2': 'BL_SW'})
g.add('D2', 'Diode:SS14', grid(300, 180), 0, value='SS14', footprint='sqrm8:D_SMA', lcsc='C2480', mpn='SS14',
      desc='boost rectifier, Schottky 40 V 1 A', pins={'2': 'BL_SW', '1': 'LED_A'})
C('C8', '1u 50V', (320, 180), 'LED_A', 'GND', desc='boost output (LED_A up to ~16 V, OVP 27 V)')
C('C9', '100n', (330, 180), 'LED_A', 'GND', desc='boost output HF (50 V part)')
R('R11', '100R', (275, 210), 'BL_PWM', 'BL_EN', desc='BL_PWM (GPIO4) into CTRL, 25 kHz PWM')
R('R7', '100k', (290, 210), 'BL_EN', 'GND', desc='CTRL pull-down: backlight off until GPIO4 drives it')
R('R8', '6.8R', (305, 210), 'LED_K', 'GND', desc='LED current sense 6.8 R 1 %: 29 mA')

# ---------------------------------------------------------------- panel FPC (ER-TFT040-3 pinout, datasheet p.6)
g.text('Panel: ER-TFT040-3 40-pin FPC', (322, 25), 2.5, True)
g.text('RGB565: DB1-5 = B1-5, DB6-11 = G0-5, DB13-17 = R1-5', (322, 30), 1.5)
g.text('DB0 = B5, DB12 = R5 (top bit repeated: true white)', (322, 34), 1.5)
g.text('LCD and touch resets shared (GPIO15)', (322, 38), 1.5)
COLOR = {16: 'LCD_B5', 28: 'LCD_R5'}
for i in range(17, 22): COLOR[i] = 'LCD_B%d' % (i - 16)
for i in range(22, 28): COLOR[i] = 'LCD_G%d' % (i - 22)
for i in range(29, 34): COLOR[i] = 'LCD_R%d' % (i - 28)
FIXED = {1: 'LED_A', 2: 'LED_K', 3: 'LED_K', 4: 'GND', 5: '+3V3', 6: 'LCD_RST', 7: 'NC', 8: 'NC', 9: 'LCD_SDA', 10: 'LCD_SCL',
         11: 'LCD_CS', 12: 'LCD_PCLK', 13: 'LCD_DE', 14: 'LCD_VS', 15: 'LCD_HS', 34: 'GND', 35: 'TP_INT', 36: 'I2C_SDA',
         37: 'I2C_SCL', 38: 'LCD_RST', 39: '+3V3', 40: 'GND'}
J2 = {str(k): v for k, v in {**FIXED, **COLOR}.items()}
J2['S1'] = 'GND'
g.add('J2', 'sqrm8_custom:ER-TFT040-3_FPC40', grid(395, 100), 0, value='FPC-05FB-40PH20', footprint='sqrm8:FPC_0.5mm_40P_XUNPU_FPC-05FB-40PH20',
      lcsc='C2856837', mpn='FPC-05FB-40PH20', desc='40-pin 0.5 mm FPC, flip lock, dual contact: ER-TFT040-3 tail', pins=J2)
g.text('VDD (pin 5) and TP_VCC (pin 39) decoupling', (340, 172), 1.5)
C('C12', '1u', (345, 185), '+3V3', 'GND', desc='panel VDD (J2 pin 5)')
C('C13', '100n', (355, 185), '+3V3', 'GND', desc='panel VDD (J2 pin 5)')
C('C14', '1u', (370, 185), '+3V3', 'GND', desc='touch TP_VCC (J2 pin 39)')
C('C15', '100n', (380, 185), '+3V3', 'GND', desc='touch TP_VCC (J2 pin 39)')
g.text('Panel control lines held until the firmware drives them', (340, 200), 1.5)
R('R9', '10k', (345, 220), 'LCD_RST', 'GND', desc='LCD_RST pull-down: panel and touch held in reset at boot')
R('R10', '10k', (355, 220), '+3V3', 'LCD_CS', desc='LCD_CS pull-up: init SPI deselected at boot')


# ---------------------------------------------------------------- field placement
def _fields_right(item, dx, ry, vy, ang):
    """Move Reference / Value of one placed symbol to its right, left-justified (schgen centres them on the pin axis)."""
    m = re.match(r'\t\(symbol\n\t\t\(lib_id "[^"]+"\)\n\t\t\(at ([-\d.]+) ([-\d.]+) \d+\)', item)
    x, y = float(m.group(1)), float(m.group(2))
    for name, oy in (('Reference', ry), ('Value', vy)):
        pat = r'(\(property "%s" "[^"]*"\n\t\t\t\(at )[-\d.]+ [-\d.]+ \d+\)((?:.|\n)*?\(size 1.27 1.27\)\n\t\t\t\t\))' % name
        item = re.sub(pat, lambda mm: '%s%s %s %d)%s\n\t\t\t\t(justify left)' % (mm.group(1), schgen._f(x + dx), schgen._f(y + oy), ang, mm.group(2)), item, 1)
    return item


TIDY = {'sqrm8:R': (2.54, -1.27, 1.27, 0), 'sqrm8:C': (2.54, -1.27, 1.27, 0), 'sqrm8:L': (2.54, -1.27, 1.27, 0),
        'sqrm8:TestPoint': (1.27, -3.81, -1.27, 0), 'sqrm8:SW_Push': (5.08, -1.27, 1.27, 90), 'sqrm8:PWR_FLAG': (1.27, -3.81, -1.27, 0),
        'sqrm8:USBLC6-2SC6': (3.81, -5.08, 6.35, 0), 'sqrm8:USB_C_Receptacle_USB2.0_16P': (7.62, -20.32, 25.4, 0)}
for i, it in enumerate(g.items):
    m = re.match(r'\t\(symbol\n\t\t\(lib_id "([^"]+)"', it)
    if m and m.group(1) in TIDY: g.items[i] = _fields_right(it, *TIDY[m.group(1)])

res = g.write()
print(res)
if res['single_use_labels']:
    sys.exit('single-use labels (typo?): %s' % res['single_use_labels'])
