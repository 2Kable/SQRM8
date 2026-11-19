#!/usr/bin/env python3
"""Build sqrm8.pretty: copies of the KiCad stock footprints used by the board, plus the footprints drawn here.

Stock copies (STOCK) are verbatim, except the ESP32-S3-WROOM-1 thermal-via drills (PATCH) and that three are saved under a shorter project name (the schematic uses these
names): L_SWPA3015S = Inductor_SMD:L_Sunlord_SWPA3015S (pads 0.8 x 2.7, gap 1.5 = Sunlord a/b/c 1.5/0.8/2.7),
SW_TS-1088 = Button_Switch_SMD:SW_SPST_TS-1088-xR020 (made from the XUNPU TS-1088-AR02016 drawing, C720477: pads 1.05 x 2.0
at +-2.225), MountingHole_2.2mm = MountingHole:MountingHole_2.2mm_M2. Only the footprint name and the Value change.

Drawn here, from the manufacturers' datasheets:
  * USB_C_Vertical_SHOUHAN_LTH6.8: SHOU HAN TYPE-C 16P LTH6.8 (LCSC C5187468), vertical USB 2.0 receptacle, from the
    "recommended P.C.B. layout" of its datasheet (rev A 2021-07-19), checked against the EasyEDA
    footprint USB-C-SMD_TYPE-C-16P-LTH6.8: 16 signal pads 0.30 x 0.87, x = +-2.75 and +-0.25..1.25 at 0.5 pitch, rows at
    y = -+0.865 (A row at -y, A1 at -x, as the maker's top view); 4 shell legs in plated slots (+-2.40, +-2.15), all "SH"
    (the shield pin of the stock symbol, as pcb-flash);
    2 non-plated peg holes at (+-3.75, 0). Pad names = Connector:USB_C_Receptacle_USB2.0_16P. Origin = pattern centre
    (= EasyEDA origin, so JLC needs no dx/dy).
  * FPC_0.5mm_40P_XUNPU_FPC-05FB-40PH20: XUNPU FPC-05FB-40PH20 (LCSC C2856837), 40 pins 0.5 mm, back flip lock, dual
    contact, H 2.0, from the XUNPU FPC-05FB-NPH20 drawing (rev A) checked against the EasyEDA footprint: signal pads 0.30 x
    1.20 at y = -1.625, anchor pads 2.00 x 1.80 at (+-11.30, +1.625) named "S1"
    (the schematic's J2 symbol has an S1 pin for them); pin 1 at +x (the maker's "A" end), the
    housing (23.5 x 4.9) towards +y and the FPC entering from +y (the edge opposite the solder tails, F.Fab arrow).
    Origin = centre between the two pad rows (= EasyEDA origin).

  * USB_C_Vertical_HRO_TYPE-C-31-D-09 (C7463258, all legs through-hole) and USB_C_Vertical_HRO_TYPE-C-31-D-15 (C22464480,
    16 SMD pads + 4 shell blades in plated slots with paste + 2 pegs, the board's J1): see their .md files. The D-15 slots
    (1.10 x 0.55) and peg holes (Ø0.80) deviate from the drawing (1.20 x 0.45, Ø0.90) to meet sqrm8.kicad_pro; its slot pads
    overlap the GND corner pads as in the drawing, so SH must be on GND.

3D models: the stock copies keep their ${KICAD10_3DMODEL_DIR} models; the two drawn footprints point at
${KIPRJMOD}/sqrm8.3dshapes/, EasyEDA STEPs of the exact LCSC part (tools/kicad/model3d.py easyeda) fitted with
model3d.py fit and checked in renders (MODELS below).

Run (stdlib only): python3 hardware/pcb/build_lib.py   (build_pcb.py may call build() itself)
"""
import glob
import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = 'sqrm8'
PRETTY = os.path.join(HERE, NAME + '.pretty')
FPDIR = sorted(glob.glob('/var/lib/flatpak/runtime/org.kicad.KiCad.Library.Footprints/x86_64/stable/*/files/footprints'))[0]

# project name -> (stock library, stock name)
STOCK = {
    'ESP32-S3-WROOM-1': ('RF_Module', 'ESP32-S3-WROOM-1'),
    'SOT-223-3_TabPin2': ('Package_TO_SOT_SMD', 'SOT-223-3_TabPin2'),
    'SOT-23-6': ('Package_TO_SOT_SMD', 'SOT-23-6'),
    'D_SMA': ('Diode_SMD', 'D_SMA'),
    'C_0603_1608Metric': ('Capacitor_SMD', 'C_0603_1608Metric'),
    'C_0805_2012Metric': ('Capacitor_SMD', 'C_0805_2012Metric'),
    'R_0603_1608Metric': ('Resistor_SMD', 'R_0603_1608Metric'),
    'TestPoint_Pad_1.5x1.5mm': ('TestPoint', 'TestPoint_Pad_1.5x1.5mm'),
    'MountingHole_2.2mm': ('MountingHole', 'MountingHole_2.2mm_M2'),
    'L_SWPA3015S': ('Inductor_SMD', 'L_Sunlord_SWPA3015S'),
    'SW_TS-1088': ('Button_Switch_SMD', 'SW_SPST_TS-1088-xR020'),
}

# project name -> [(regex, replacement, expected count)] applied to the stock copy: the only deviations from stock.
# ESP32-S3-WROOM-1:
#  * the 12 thermal vias in the exposed pad (pad 41) are drilled 0.2 mm in the stock footprint, below the board's 0.3 mm
#    minimum hole (sqrm8.kicad_pro, JLC's no-surcharge drill); 0.3 in the same 0.6 mm pads (ring 0.15);
#  * the stock rule area (no copper, no footprints) is Espressif's 48 x 21 mm free-air clearance beyond the antenna end, with
#    a courtyard around it: on a 40 mm board that covers the whole top band. Both shrink to the module: the rule area to the
#    18 x 6 mm antenna end of the body (-9..9 x -12.75..-6.75), the courtyard to the body (-9.75..9.75 x -13.15..13.45).
#    The board adds its own antenna keep-out to the edges (build_pcb).
_CRT_LINE = r'\n\t\(fp_line\n(?:(?!\n\t\)).)*?\(layer "F\.CrtYd"\)(?:(?!\n\t\)).)*\n\t\)'
_ESP_CRT = ('\n\t(fp_rect\n\t\t(start -9.75 -13.15)\n\t\t(end 9.75 13.45)\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type solid)\n'
            '\t\t)\n\t\t(fill no)\n\t\t(layer "F.CrtYd")\n\t\t(uuid "5a1c0de0-e5b3-4d2a-9c3e-000000000001")\n\t)')
PATCH = {
    'ESP32-S3-WROOM-1': [
        (r'(\(size 0\.6 0\.6\)\n\t\t\(drill )0\.2\)', r'\g<1>0.3)', 12),
        (r'\(xy -24 -6\.75\) \(xy 24 -6\.75\) \(xy 24 -27\.75\) \(xy -24 -27\.75\)',
         '(xy -9 -6.75) (xy 9 -6.75) (xy 9 -12.75) (xy -9 -12.75)', 1),
        ('(?s)' + _CRT_LINE + r'(?=\n\t\(fp_line\n(?:(?!\n\t\)).)*?\(layer "F\.CrtYd"\))', '', 7),   # all but the last
        ('(?s)' + _CRT_LINE, lambda m: _ESP_CRT, 1),                                       # the last -> body rect
    ],
}

USB = 'USB_C_Vertical_SHOUHAN_LTH6.8'
FPC = 'FPC_0.5mm_40P_XUNPU_FPC-05FB-40PH20'
HRO = 'USB_C_Vertical_HRO_TYPE-C-31-D-09'
HRO15 = 'USB_C_Vertical_HRO_TYPE-C-31-D-15'

# footprint name -> (model path, offset, scale, rotate); replaces the footprint's own (model ...) blocks.
# Fitted with `model3d.py fit ... --render` and checked in the renders (rotation 0 = the EasyEDA footprint's frame, which
# is ours). fit seats the lowest point on z = 0 and centres on F.Fab; both are overridden here:
#   USB: the STEP's SMD tails are at z -3.6, the shell legs (0.95) and pegs (0.40) go through the board, so z = 3.6 puts
#        the tails on the copper; XY 0 (the model is centred). The model is 6.5 mm tall, the part 6.80.
#   HRO: the STEP is 8.40 tall (6.50 body + 1.90 legs), body bottom at z -3.85: z = 3.85 seats it, legs through the board.
#   HRO15: no EasyEDA model for the D-15; the clone HX-TYPE-C-16P-180-LT-H9.3 (C49261568, same pads, pegs, blades and
#        flange) stands in. Its SMD tails are at z -0.52 and its pattern centre at y +0.05: z = 0.52 puts the tails on the
#        copper (blades 2.05 and pegs 0.55 below), y 0.05 centres it. It is 9.8 mm tall above the board, the D-15 8.8.
#        Measured in the board STL: tails at z 0.00, flange bottom +0.05, so the seating is right. `model3d.py check`
#        takes the lowest point of the whole model (the blade tips, -2.05) and has only a global --ztol, so it reports
#        J1 MISPLACED: the one expected finding (`check --refs J1 --ztol 2.1` passes).
#   FPC: the STEP is 5.40 deep (housing 4.90 + tails); aligned on its anchor tabs (STEP y 2.45..4.05 -> pads at +1.625).
SHAPES = '${KIPRJMOD}/' + NAME + '.3dshapes/'
MODELS = {
    USB: (SHAPES + USB + '.step', (0, 0, 3.6), (1, 1, 1), (0, 0, 0)),
    FPC: (SHAPES + FPC + '.step', (0, 1.625, 0), (1, 1, 1), (0, 0, 0)),
    HRO: (SHAPES + HRO + '.step', (0, 0, 3.85), (1, 1, 1), (0, 0, 0)),
    HRO15: (SHAPES + HRO15 + '.step', (0, 0.05, 0.52), (1, 1, 1), (0, 0, 0)),
}


def _f(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return s if s not in ('-0', '') else '0'


def _u(): return str(uuid.uuid4())


def _model(name):
    path, off, sc, rot = MODELS[name]
    xyz = lambda v: '\t\t\t(xyz %s %s %s)\n' % tuple(_f(c) for c in v)
    return ('\t(model "%s"\n\t\t(offset\n%s\t\t)\n\t\t(scale\n%s\t\t)\n\t\t(rotate\n%s\t\t)\n\t)\n'
            % (path, xyz(off), xyz(sc), xyz(rot)))


def _set_model(name, s):
    """Footprint text with its (model ...) blocks replaced by MODELS[name] (inserted before the closing paren)."""
    if name not in MODELS:
        return s
    s = re.sub(r'\t\(model "(?:[^"\\]|\\.)*"\n(?:\t\t.*\n)*\t\)\n', '', s)
    assert s.rstrip().endswith(')'), name
    return s.rstrip()[:-1] + _model(name) + ')\n'


def _rename(s, old, new):
    """Stock footprint text saved under a project name: the footprint name and the Value property change, nothing else."""
    if old == new:
        return s
    s, n1 = re.subn(r'^\(footprint "%s"' % re.escape(old), '(footprint "%s"' % new, s, count=1)
    s, n2 = re.subn(r'\(property "Value" "%s"' % re.escape(old), '(property "Value" "%s"' % new, s, count=1)
    assert n1 == 1 and n2 == 1, old
    return s


def _font(size=1.0, th=0.15):
    return '(effects\n\t\t\t(font\n\t\t\t\t(size %s %s)\n\t\t\t\t(thickness %s)\n\t\t\t)\n\t\t)' % (_f(size), _f(size), _f(th))


def _prop(name, val, x, y, layer, hide=False):
    return ('\t(property "%s" "%s"\n\t\t(at %s %s 0)\n\t\t(layer "%s")\n%s\t\t(uuid "%s")\n\t\t%s\n\t)\n'
            % (name, val, _f(x), _f(y), layer, '\t\t(hide yes)\n' if hide else '', _u(), _font()))


def _line(a, b, layer, w):
    return ('\t(fp_line\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n'
            '\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n' % (_f(a[0]), _f(a[1]), _f(b[0]), _f(b[1]), _f(w), layer, _u()))


def _poly(pts, layer, w, closed=False):
    """Open polyline as fp_lines (closed=True joins the last point to the first)."""
    pts = list(pts) + ([pts[0]] if closed else [])
    return ''.join(_line(a, b, layer, w) for a, b in zip(pts, pts[1:]))


def _rect(a, b, layer, w):
    return ('\t(fp_rect\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n'
            '\t\t(fill no)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n' % (_f(a[0]), _f(a[1]), _f(b[0]), _f(b[1]), _f(w), layer, _u()))


def _dot(x, y, r, layer):
    """Filled circle (silk pin-1 dot)."""
    return ('\t(fp_circle\n\t\t(center %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type solid)\n\t\t)\n'
            '\t\t(fill yes)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n' % (_f(x), _f(y), _f(x + r), _f(y), layer, _u()))


def _text(txt, x, y, layer, size=0.6, th=0.09):
    return ('\t(fp_text user "%s"\n\t\t(at %s %s 0)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t\t%s\n\t)\n'
            % (txt, _f(x), _f(y), layer, _u(), _font(size, th)))


def _head(name, descr, tags, attr, ref_y, val_y):
    return ('(footprint "%s"\n\t(version 20260206)\n\t(generator "pcbnew")\n\t(generator_version "10.0")\n\t(layer "F.Cu")\n'
            '\t(descr "%s")\n\t(tags "%s")\n' % (name, descr, tags)
            + _prop('Reference', 'REF**', 0, ref_y, 'F.SilkS') + _prop('Value', name, 0, val_y, 'F.Fab')
            + _prop('Datasheet', '', 0, 0, 'F.Fab', True) + _prop('Description', '', 0, 0, 'F.Fab', True)
            + '\t(attr %s)\n\t(duplicate_pad_numbers_are_jumpers no)\n' % attr)


def _smd(num, x, y, w, h):
    return ('\t(pad "%s" smd rect\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n\t\t(uuid "%s")\n\t)\n'
            % (num, _f(x), _f(y), _f(w), _f(h), _u()))


# ---------------------------------------------------------------- SHOU HAN TYPE-C 16P LTH6.8 (vertical)
USB_SIG = (0.30, 0.87)                       # signal pad w x h
USB_ROW = 0.865                              # row centre, |y|: pad spans 0.43..1.30 from the centre line
USB_XS = (-2.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 2.75)
USB_A = ('A1', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A12')        # -y row, left to right
USB_B = ('B12', 'B9', 'B8', 'B7', 'B6', 'B5', 'B4', 'B1')        # +y row, left to right (B1 = A1 turned 180 deg)
USB_SHELL = (2.40, 2.15)                     # shell slot centres (+-x, +-y): 4.80 x 4.30
USB_SHELL_PAD = (1.50, 1.10)                 # datasheet 1.35 x 1.10; x widened for the 1.0 mm slot's annular ring
USB_SHELL_SLOT = (1.00, 0.60)                # datasheet 0.85 x 0.60; 1.0 long as EasyEDA (JLC drills shorter slots as holes)
USB_PEG = (3.75, 0.60)                       # peg holes (+-x, 0), drill: datasheet 0.52 for a 0.40 +-0.05 peg; 0.60 = EasyEDA
USB_BODY = (8.94, 3.16)                      # housing footprint on the board, centred


def usb_c():
    name = USB
    s = _head(name, 'SHOU HAN TYPE-C 16P LTH6.8 vertical USB 2.0 Type-C receptacle, 6.8 mm above the board, '
              '16 SMD signal pins, 4 shell legs in plated slots, 2 pegs (LCSC C5187468); '
              'land pattern from the SHOU HAN drawing rev A 2021-07-19, checked against EasyEDA USB-C-SMD_TYPE-C-16P-LTH6.8',
              'USB C Type-C receptacle USB2.0 vertical SHOU HAN LTH6.8 C5187468', 'smd', -3.7, 3.7)
    bx, by = USB_BODY[0] / 2, USB_BODY[1] / 2
    # fab: housing with the A1 corner chamfered, A1 label
    c = 0.8
    s += _poly([(-bx + c, -by), (bx, -by), (bx, by), (-bx, by), (-bx, -by + c)], 'F.Fab', 0.1, closed=True)
    s += _text('A1', -bx + 0.75, 0, 'F.Fab', 0.5, 0.08)
    s += _text('${REFERENCE}', 0.6, 0, 'F.Fab', 0.6, 0.09)
    # silk: housing outline 0.11 outside the body, broken around the shell pads; pin-A1 dot left of A1
    w, o = 0.12, 0.11
    sx_in = USB_SHELL[0] - USB_SHELL_PAD[0] / 2 - 0.3            # stop 0.3 short of the inner shell-pad edge
    sx_out = USB_SHELL[0] + USB_SHELL_PAD[0] / 2 + 0.25          # resume 0.25 past the outer one
    for sy in (-1, 1):
        y = sy * (by + o)
        s += _line((-sx_in, y), (sx_in, y), 'F.SilkS', w)
        s += _line((-sx_out, y), (-(bx + o), y), 'F.SilkS', w) + _line((sx_out, y), (bx + o, y), 'F.SilkS', w)
    for sx in (-1, 1):
        s += _line((sx * (bx + o), -(by + o)), (sx * (bx + o), by + o), 'F.SilkS', w)
    s += _dot(-3.35, -USB_ROW, 0.15, 'F.SilkS')
    # courtyard: body and shell pads, + 0.25
    cx = max(bx, USB_PEG[0] + USB_PEG[1] / 2, USB_SHELL[0] + USB_SHELL_PAD[0] / 2) + 0.25
    cy = max(by, USB_SHELL[1] + USB_SHELL_PAD[1] / 2) + 0.25
    s += _rect((-cx, -cy), (cx, cy), 'F.CrtYd', 0.05)
    for row, names in ((-USB_ROW, USB_A), (USB_ROW, USB_B)):
        for x, n in zip(USB_XS, names):
            s += _smd(n, x, row, *USB_SIG)
    for sx in (-1, 1):
        for sy in (-1, 1):
            s += ('\t(pad "SH" thru_hole oval\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(drill oval %s %s)\n'
                  '\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t\t(uuid "%s")\n\t)\n'
                  % (_f(sx * USB_SHELL[0]), _f(sy * USB_SHELL[1]), _f(USB_SHELL_PAD[0]), _f(USB_SHELL_PAD[1]),
                     _f(USB_SHELL_SLOT[0]), _f(USB_SHELL_SLOT[1]), _u()))
    for sx in (-1, 1):
        s += ('\t(pad "" np_thru_hole circle\n\t\t(at %s 0)\n\t\t(size %s %s)\n\t\t(drill %s)\n\t\t(layers "*.Cu" "*.Mask")\n'
              '\t\t(uuid "%s")\n\t)\n' % (_f(sx * USB_PEG[0]), _f(USB_PEG[1]), _f(USB_PEG[1]), _f(USB_PEG[1]), _u()))
    s += '\t(embedded_fonts no)\n)\n'
    return name, s


# ---------------------------------------------------------------- HRO TYPE-C-31-D-09 (vertical, all legs through-hole)
HRO_XS = (-3.85, -2.75, -1.65, -0.55, 0.55, 1.65, 2.75, 3.85)  # 8 holes per row at 1.10 pitch (7.70 span)
HRO_ROW = 0.675                              # rows 1.35 apart: A at -y, B at +y (same names left to right as USB_A/USB_B)
HRO_SIG = (0.80, 0.50)                       # signal pad, drill (datasheet hole 0.50, EasyEDA pad 0.80)
HRO_SHELL = (2.50, 2.15)                     # shell leg centres (+-x, +-y): 5.00 x 4.30
HRO_SHELL_PAD = (1.80, 1.00)                 # EasyEDA pad around the slot
HRO_SHELL_SLOT = (1.37, 0.60)                # EasyEDA slot, long axis along x (datasheet: Ø1.30 round holes)
HRO_BODY = (8.94, 3.16)


def hro_c31():
    name = HRO
    s = _head(name, 'HRO TYPE-C-31-D-09 vertical USB 2.0 Type-C receptacle, 6.5 mm above the board, 16 signal pins and '
              '4 shell legs all through-hole (legs 1.9 mm), LCSC C7463258; land pattern from the HRO drawing rev A 2021-05-18 '
              'with the EasyEDA USB-C-TH_TYPE-C-31-D-09 shell slots (1.37 x 0.60) instead of the drawn Ø1.30 holes',
              'USB C Type-C receptacle USB2.0 vertical through-hole HRO TYPE-C-31-D-09 C7463258', 'through_hole', -3.6, 3.6)
    bx, by = HRO_BODY[0] / 2, HRO_BODY[1] / 2
    c = 0.8
    s += _poly([(-bx + c, -by), (bx, -by), (bx, by), (-bx, by), (-bx, -by + c)], 'F.Fab', 0.1, closed=True)
    s += _text('A1', -bx + 0.75, 0, 'F.Fab', 0.5, 0.08)
    s += _text('${REFERENCE}', 0.6, 0, 'F.Fab', 0.6, 0.09)
    # silk: housing outline 0.11 outside the body, broken around the shell pads; pin-A1 dot outside the A1 corner
    w, o = 0.12, 0.11
    sx_in = HRO_SHELL[0] - HRO_SHELL_PAD[0] / 2 - 0.3
    sx_out = HRO_SHELL[0] + HRO_SHELL_PAD[0] / 2 + 0.25
    for sy in (-1, 1):
        y = sy * (by + o)
        s += _line((-sx_in, y), (sx_in, y), 'F.SilkS', w)
        s += _line((-sx_out, y), (-(bx + o), y), 'F.SilkS', w) + _line((sx_out, y), (bx + o, y), 'F.SilkS', w)
    for sx in (-1, 1):
        s += _line((sx * (bx + o), -(by + o)), (sx * (bx + o), by + o), 'F.SilkS', w)
    s += _dot(-4.1, -2.25, 0.15, 'F.SilkS')
    cx = max(bx, HRO_XS[-1] + HRO_SIG[0] / 2, HRO_SHELL[0] + HRO_SHELL_PAD[0] / 2) + 0.25
    cy = max(by, HRO_SHELL[1] + HRO_SHELL_PAD[1] / 2) + 0.25
    s += _rect((-cx, -cy), (cx, cy), 'F.CrtYd', 0.05)
    for row, names in ((-HRO_ROW, USB_A), (HRO_ROW, USB_B)):
        for x, n in zip(HRO_XS, names):
            s += ('\t(pad "%s" thru_hole %s\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(drill %s)\n\t\t(layers "*.Cu" "*.Mask")\n'
                  '\t\t(remove_unused_layers no)\n\t\t(uuid "%s")\n\t)\n'
                  % (n, 'rect' if n == 'A1' else 'circle', _f(x), _f(row), _f(HRO_SIG[0]), _f(HRO_SIG[0]), _f(HRO_SIG[1]), _u()))
    for sx in (-1, 1):
        for sy in (-1, 1):
            s += ('\t(pad "SH" thru_hole oval\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(drill oval %s %s)\n'
                  '\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t\t(uuid "%s")\n\t)\n'
                  % (_f(sx * HRO_SHELL[0]), _f(sy * HRO_SHELL[1]), _f(HRO_SHELL_PAD[0]), _f(HRO_SHELL_PAD[1]),
                     _f(HRO_SHELL_SLOT[0]), _f(HRO_SHELL_SLOT[1]), _u()))
    s += '\t(embedded_fonts no)\n)\n'
    return name, s


# ---------------------------------------------------------------- HRO TYPE-C-31-D-15 (vertical, hybrid: SMD + soldered blades)
D15_XS = (-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5)        # 8 SMD pads per row at 1.00 pitch
D15_ROW = 1.365                              # row centres: pads 1.59 long with a 1.14 gap (4.32 overall), A at -y
D15_SIG = (0.50, 1.59)                       # signal pad w x h
D15_SHELL = (4.225, 1.43)                    # blade centres (+-x, +-y): 8.45 x 2.86
D15_SHELL_SLOT = (1.10, 0.55)                # drawing 1.20 x 0.45 for a 0.90 +-0.05 x 0.30 blade. 0.55 wide: JLC's plated-slot minimum
                                             # (0.50) + paste room. 1.10 long, not 1.20: with the 0.075 ring the rules ask at the
                                             # tips, a 1.20 slot puts the pad copper 0.04 from the peg hole (rule 0.15)
D15_SHELL_PAD = (1.25, 1.05)                 # roundrect: ring 0.075 at the slot tips, 0.25 at the sides; 0.16 from the peg hole
D15_SHELL_PASTE = 0.05                       # paste margin: 1.35 x 1.15 aperture on the slot pads (pin-in-paste)
D15_PEGS = ((-5.41, -1.50), (5.41, 1.50))    # unplated locating pegs Ø0.70, diagonal (A1 corner and B1 corner)
D15_PEG_D = 0.80                             # drawing Ø0.90; 0.80 (0.05 play per side) keeps the slot pad 0.16 from it
D15_FLANGE = (12.0, 5.0)                     # moulded flange the part sits on, centred
D15_BODY = (8.94, 3.16)                      # shell above the flange


def hro_d15():
    name = HRO15
    s = _head(name, 'HRO TYPE-C-31-D-15 vertical USB 2.0 Type-C receptacle, 8.8 mm above the board, 16 SMD signal pads, '
              '4 shell blades soldered in plated slots (pin-in-paste, paste on the slot pads), 2 unplated pegs, 12 x 5 mm flange '
              '(LCSC C22464480); land pattern from the HRO drawing rev A 2023-10-27, same pads as EasyEDA HC-TYPE-C-16P-LT01A and '
              'HX-TYPE-C-16P-180-LT-H9.3',
              'USB C Type-C receptacle USB2.0 vertical HRO TYPE-C-31-D-15 C22464480', 'smd', -3.95, 3.6)
    fx, fy = D15_FLANGE[0] / 2, D15_FLANGE[1] / 2
    bx, by = D15_BODY[0] / 2, D15_BODY[1] / 2
    c = 0.5
    # fab: flange (A1 corner chamfered), shell outline, A1 label
    s += _poly([(-fx + c, -fy), (fx, -fy), (fx, fy), (-fx, fy), (-fx, -fy + c)], 'F.Fab', 0.1, closed=True)
    s += _rect((-bx, -by), (bx, by), 'F.Fab', 0.1)
    s += _text('A1', -3.5, -fy + 0.45, 'F.Fab', 0.4, 0.06)
    s += _text('${REFERENCE}', 0, 0, 'F.Fab', 0.6, 0.09)
    # silk: flange outline 0.11 outside, pin-A1 dot above A1 outside the flange
    o, w = 0.11, 0.12
    s += _poly([(-(fx + o), -(fy + o)), (fx + o, -(fy + o)), (fx + o, fy + o), (-(fx + o), fy + o)], 'F.SilkS', w, closed=True)
    s += _dot(D15_XS[0], -(fy + o) - 0.4, 0.15, 'F.SilkS')
    s += _rect((-(fx + 0.25), -(fy + 0.25)), (fx + 0.25, fy + 0.25), 'F.CrtYd', 0.05)
    for row, names in ((-D15_ROW, USB_A), (D15_ROW, USB_B)):
        for x, n in zip(D15_XS, names):
            s += _smd(n, x, row, *D15_SIG)
    for sx in (-1, 1):
        for sy in (-1, 1):
            s += ('\t(pad "SH" thru_hole roundrect\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(drill oval %s %s)\n'
                  '\t\t(layers "*.Cu" "*.Mask" "F.Paste")\n\t\t(remove_unused_layers no)\n\t\t(roundrect_rratio 0.25)\n'
                  '\t\t(solder_paste_margin %s)\n\t\t(uuid "%s")\n\t)\n'
                  % (_f(sx * D15_SHELL[0]), _f(sy * D15_SHELL[1]), _f(D15_SHELL_PAD[0]), _f(D15_SHELL_PAD[1]),
                     _f(D15_SHELL_SLOT[0]), _f(D15_SHELL_SLOT[1]), _f(D15_SHELL_PASTE), _u()))
    for x, y in D15_PEGS:
        s += ('\t(pad "" np_thru_hole circle\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(drill %s)\n\t\t(layers "*.Cu" "*.Mask")\n'
              '\t\t(uuid "%s")\n\t)\n' % (_f(x), _f(y), _f(D15_PEG_D), _f(D15_PEG_D), _f(D15_PEG_D), _u()))
    s += '\t(embedded_fonts no)\n)\n'
    return name, s


# ---------------------------------------------------------------- XUNPU FPC-05FB-40PH20
FPC_N, FPC_P = 40, 0.5
FPC_SIG = (0.30, 1.20)                       # signal pad w x h
FPC_SIG_Y = -1.625                           # signal row; anchors 3.25 behind it (datasheet "3.25")
FPC_MP = (2.00, 1.80)                        # anchor pad
FPC_MP_X = ((FPC_N - 1) * FPC_P + 3.1) / 2   # 11.30: "(pin-1)*0.5+3.1" between anchor centres
FPC_MP_Y = FPC_SIG_Y + 3.25                  # 1.625
FPC_BODY = (-((FPC_N - 1) * FPC_P + 4.0) / 2, FPC_SIG_Y + 0.20,     # housing "(pin-1)*0.5+4.00" x 4.90, its tail
            ((FPC_N - 1) * FPC_P + 4.0) / 2, FPC_SIG_Y + 0.20 + 4.90)  # edge 0.20 behind the pad centre line


def fpc40():
    name = FPC
    s = _head(name, 'XUNPU FPC-05FB-40PH20, 40 pins, 0.5 mm pitch FPC connector, back flip lock, dual contact, H 2.0 mm, '
              'FPC 0.3 mm, FPC entering from +y (opposite the solder tails), pin 1 at +x; land pattern from the XUNPU drawing '
              'FPC-05FB-NPH20 rev A, checked against EasyEDA FPC-SMD_40P-P0.50_XUNPU_FPC-05FB-40PH20 (LCSC C2856837)',
              'connector FPC FFC XUNPU FPC-05FB 0.5mm flip lock dual contact C2856837', 'smd', -3.4, 4.7)
    x0, y0, x1, y1 = FPC_BODY
    p1 = (FPC_N - 1) * FPC_P / 2                                  # pin 1 x (+9.75)
    # fab: housing, lid hinge line on the tail side, pin-1 triangle, entry edge (double line) and arrow
    s += _rect((x0, y0), (x1, y1), 'F.Fab', 0.1)
    s += _line((x0, y0 + 1.0), (x1, y0 + 1.0), 'F.Fab', 0.1)
    s += _poly([(p1 - 0.5, y0), (p1, y0 + 0.6), (p1 + 0.5, y0)], 'F.Fab', 0.1)
    s += _text('1', p1, y0 + 1.5, 'F.Fab', 0.6, 0.09)
    s += _line((x0 + 0.3, y1 - 0.25), (x1 - 0.3, y1 - 0.25), 'F.Fab', 0.1)
    ay = y1 - 0.4
    s += _line((0, ay), (0, ay - 1.6), 'F.Fab', 0.1) + _poly([(-0.4, ay - 1.2), (0, ay - 1.6), (0.4, ay - 1.2)], 'F.Fab', 0.1)
    s += _text('FPC in', -2.2, ay - 0.8, 'F.Fab', 0.6, 0.09)
    s += _text('${REFERENCE}', 4.5, ay - 0.8, 'F.Fab', 0.8, 0.12)
    # silk: housing corners clear of the pads by >= 0.25, pin-1 dot above pad 1
    w, o = 0.12, 0.1
    xa = x1 + o
    sig_top = FPC_SIG_Y - FPC_SIG[1] / 2
    mp_top, mp_bot = FPC_MP_Y - FPC_MP[1] / 2, FPC_MP_Y + FPC_MP[1] / 2
    for sx in (-1, 1):
        s += _poly([(sx * (p1 + 0.6), y0 - o), (sx * xa, y0 - o), (sx * xa, mp_top - 0.27)], 'F.SilkS', w)
        s += _line((sx * xa, mp_bot + 0.27), (sx * xa, y1 + o), 'F.SilkS', w)
    s += _line((-xa, y1 + o), (xa, y1 + o), 'F.SilkS', w)
    s += _dot(p1 + 0.25, sig_top - 0.45, 0.15, 'F.SilkS')
    # courtyard
    s += _rect((-(FPC_MP_X + FPC_MP[0] / 2) - 0.25, sig_top - 0.25), ((FPC_MP_X + FPC_MP[0] / 2) + 0.25, y1 + 0.25), 'F.CrtYd', 0.05)
    for i in range(FPC_N):
        s += _smd(str(i + 1), p1 - i * FPC_P, FPC_SIG_Y, *FPC_SIG)
    for sx in (-1, 1):
        s += _smd('S1', sx * FPC_MP_X, FPC_MP_Y, *FPC_MP)
    s += '\t(embedded_fonts no)\n)\n'
    return name, s


def build():
    os.makedirs(PRETTY, exist_ok=True)
    for name, (lib, stock) in STOCK.items():
        src = os.path.join(FPDIR, lib + '.pretty', stock + '.kicad_mod')
        s = _rename(open(src).read(), stock, name)
        for rx, rep, n in PATCH.get(name, ()):
            s, k = re.subn(rx, rep, s)
            assert k == n, (name, rx, k)
        open(os.path.join(PRETTY, name + '.kicad_mod'), 'w').write(_set_model(name, s))
    for fn in (usb_c, hro_c31, hro_d15, fpc40):
        name, s = fn()
        open(os.path.join(PRETTY, name + '.kicad_mod'), 'w').write(_set_model(name, s))
    return sorted(os.listdir(PRETTY))


if __name__ == '__main__':
    print('\n'.join(build()))
