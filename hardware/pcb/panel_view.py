#!/usr/bin/env python3
"""Draw the sqrm8 board where it sits on the back of the panel, for the mechanical review (stdlib + PIL only).

  python3 hardware/pcb/panel_view.py [--board sqrm8.kicad_pcb] [--out DIR]

Reads the board file (Edge.Cuts outline, footprint positions, F.CrtYd courtyards, pads, the antenna rule area) and writes
two pictures to DIR (default ~/.cache/kicad-tools/sqrm8/):
  * panel_view.png: the back of the device at 10 px/mm, upright (tail at the bottom): lens, panel, the folded tail and
    the touch sub-flex keep-out, the centre lines, then the board at its mounting position with its courtyards, holes,
    the FPC entry, the USB-C opening and a legend of the key heights;
  * panel_section.png: a side section along the vertical centre line with the stack heights (z drawn x2).

Panel frame: u = mm from the left lens edge seen from the back, v = mm up from the bottom lens edge. The board frame is
KiCad's (y down) with its tail edge (x = 0) at v = TAIL_EDGE_UP and board +x pointing up: u = LENS/2 + (y - H/2),
v = TAIL_EDGE_UP + x. That is a rotation (no mirror): the components face the viewer, board +y points right.
Numbers from ../PANEL.md and ../BOARD.md.
"""
import math, os, re, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 10                                  # px per mm
LENS = 84.2                             # cover lens, square
PANEL_W, PANEL_H = 74.66, 76.54         # LCD + backlight: 74.66 along the tail edge, centred on the lens across
PANEL_V0 = 2.56                         # panel bottom edge above the bottom lens edge (the lens overhang on the tail side)
ROOT_W, ROOT_FROM = 33.57, 19.12        # tail root width, from the panel's left corner seen from the FRONT (= right, back)
STRIP_W, TIP_UP = 20.5, 25.0            # contact strip width (centred); folded tip above the panel's bottom edge
TOUCH_KEEP = 15.0                       # touch sub-flex: nothing of ours below this, from the bottom lens edge
TAIL_EDGE_UP = 22.0                     # board tail edge above the bottom lens edge
J2_ENTRY_X, J2_INSERT = 1.1, 2.1        # J2 housing entry from the tail edge; FPC insertion to the stop
USB_OPEN = (8.94, 3.16)                 # USB-C body (shell opening), long side across the panel
KEY = ('J1', 'J2', 'U1', 'SW1', 'H1', 'H2', 'TP1', 'TP2', 'TP3', 'TP4', 'TP5')
BLOCKS = {'U2': 'U2', 'U3': 'U3', 'D1': 'D1', 'D2': 'D2', 'L1': 'L1'}   # small labels; the passives stay unlabelled
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def font(size, bold=False):
    p = FONT.replace('.ttf', '-Bold.ttf') if bold else FONT
    try: return ImageFont.truetype(p, size)
    except OSError: return ImageFont.load_default(size)


def block(t, i):
    """The balanced s-expression starting at t[i] == '('."""
    d = 0
    for j in range(i, len(t)):
        if t[j] == '(': d += 1
        elif t[j] == ')':
            d -= 1
            if d == 0: return t[i:j + 1]
    raise ValueError('unbalanced')


def rot(lx, ly, deg):
    """KiCad footprint rotation (y down, angle counter-clockwise on screen)."""
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    return lx * c + ly * s, -lx * s + ly * c


def read_board(path):
    """{'outline': [(x0, y0, x1, y1)], 'fps': {ref: {...}}, 'ant': [pts]} from a .kicad_pcb."""
    t = open(path).read()
    xs, ys = [], []
    for m in re.finditer(r'\(gr_(?:line|rect)\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)(?:(?!\(gr_).)*?\(layer "Edge\.Cuts"\)', t, re.S):
        xs += [float(m.group(1)), float(m.group(3))]; ys += [float(m.group(2)), float(m.group(4))]
    fps = {}
    for m in re.finditer(r'\n\t\(footprint "', t):
        b = block(t, m.start() + 2)
        ref = re.search(r'\(property "Reference" "([^"]*)"', b).group(1)
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', b)
        x, y, r = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        cy = []
        for g in re.finditer(r'\((?:fp_rect|fp_line)\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)(?:(?!\(fp_).)*?\(layer "F\.CrtYd"\)', b, re.S):
            cy += [(float(g.group(1)), float(g.group(2))), (float(g.group(3)), float(g.group(4)))]
        circ = []
        for g in re.finditer(r'\(fp_circle\s+\(center ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)(?:(?!\(fp_).)*?\(layer "F\.CrtYd"\)', b, re.S):
            cx, cyy, ex, ey = map(float, g.groups()); circ.append((cx, cyy, math.hypot(ex - cx, ey - cyy)))
        pads = []
        for g in re.finditer(r'\(pad "([^"]*)" (\w+) \w+\s+\(at ([-\d.]+) ([-\d.]+)(?: [-\d.]+)?\)\s+\(size ([-\d.]+) ([-\d.]+)\)(?:\s+\(drill (?:oval )?([-\d.]+))?', b):
            pads.append({'n': g.group(1), 'type': g.group(2), 'l': (float(g.group(3)), float(g.group(4))),
                         'drill': float(g.group(7)) if g.group(7) else 0.0})
        fps[ref] = {'at': (x, y, r), 'crt': cy, 'circ': circ, 'pads': pads}
    ant = None
    for m in re.finditer(r'\n\t\(zone\b', t):
        z = block(t, m.start() + 2)
        if '(name "U1 antenna keep-out")' in z:
            ant = [(float(a), float(b_)) for a, b_ in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', z)]
    return {'outline': (min(xs), min(ys), max(xs), max(ys)), 'fps': fps, 'ant': ant}


class View:
    """Panel mm -> pixels for the back view; board mm -> panel mm."""
    def __init__(self, bd, margin=(70, 70)):
        self.mx, self.my = margin
        x0, y0, x1, y1 = bd['outline']; self.W, self.H = x1 - x0, y1 - y0

    def px(self, u, v): return (self.mx + u * S, self.my + (LENS - v) * S)
    def panel(self, x, y): return (LENS / 2 + (y - self.H / 2), TAIL_EDGE_UP + x)
    def bpx(self, x, y): return self.px(*self.panel(x, y))


def hatch(dr, box, step, color, width=1, slope=1):
    """45-degree hatch inside a pixel box (x0, y0, x1, y1), rising (slope 1) or falling (slope -1) to the right."""
    x0, y0, x1, y1 = box; h = y1 - y0
    k = x0 - h
    while k < x1:
        a, b = ((k, y1), (k + h, y0)) if slope > 0 else ((k, y0), (k + h, y1))
        pts = [(a[0] + (b[0] - a[0]) * i / 400, a[1] + (b[1] - a[1]) * i / 400) for i in range(401)]
        pts = [q for q in pts if x0 <= q[0] <= x1]
        if len(pts) > 1: dr.line([pts[0], pts[-1]], fill=color, width=width)
        k += step


def dashed(dr, a, b, color, width=1, dash=10, gap=6):
    L = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L // (dash + gap)) + 1
    for i in range(n):
        t0 = i * (dash + gap) / L; t1 = min(1, (i * (dash + gap) + dash) / L)
        if t0 >= 1: break
        dr.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=color, width=width)


def arrow(dr, a, b, color, width=2, head=10):
    dr.line([a, b], fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        dr.line([b, (b[0] - head * math.cos(ang + s * 0.45), b[1] - head * math.sin(ang + s * 0.45))], fill=color, width=width)


def pad_panel(bd, v, ref, num):
    f = bd['fps'][ref]; x, y, r = f['at']
    for p in f['pads']:
        if p['n'] == num:
            dx, dy = rot(*p['l'], r); return v.panel(x + dx, y + dy)


def back_view(bd, out):
    v = View(bd)
    img = Image.new('RGB', (v.mx * 2 + int(LENS * S) + 560, v.my * 2 + int(LENS * S) + 40), 'white')
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); do = ImageDraw.Draw(ov)
    dr = ImageDraw.Draw(img)
    f12, f14, f16b, f20b = font(12), font(14), font(16, True), font(20, True)
    # lens, panel
    dr.rectangle([v.px(0, LENS), v.px(LENS, 0)], fill='#f2f2f2', outline='black', width=4)
    pu0 = (LENS - PANEL_W) / 2
    dr.rectangle([v.px(pu0, PANEL_V0 + PANEL_H), v.px(pu0 + PANEL_W, PANEL_V0)], fill='#d5dae1', outline='#555', width=2)
    dr.text(v.px(pu0 + 1, PANEL_V0 + PANEL_H - 1), 'panel %.2f x %.2f (back of the backlight)' % (PANEL_W, PANEL_H), fill='#444', font=f12)
    dr.text(v.px(1, LENS - 1), 'lens %.1f x %.1f, seen from the back (tail at the bottom)' % (LENS, LENS), fill='black', font=f12)
    # touch sub-flex keep-out
    tb = [*v.px(0, TOUCH_KEEP), *v.px(LENS, 0)]
    hatch(dr, (tb[0] + 3, tb[1], tb[2] - 3, tb[3] - 3), 14, '#eaa274', 1)
    dr.line([v.px(0, TOUCH_KEEP), v.px(LENS, TOUCH_KEEP)], fill='#d9772b', width=2)
    dr.text(v.px(1, TOUCH_KEEP + 2.0), 'touch sub-flex / tail fold: keep out below %.0f mm' % TOUCH_KEEP, fill='#b35a14', font=f12)
    # tail root (on the panel's bottom edge) and the folded strip
    pr = pu0 + PANEL_W
    r0, r1 = pr - ROOT_FROM - ROOT_W, pr - ROOT_FROM
    dr.rectangle([v.px(r0, PANEL_V0 + 1.5), v.px(r1, PANEL_V0)], outline='#1f4e9c', width=2)
    dr.text(v.px(r0, PANEL_V0 + 3.6), 'tail root %.2f, %.2f from the front-left corner' % (ROOT_W, ROOT_FROM), fill='#1f4e9c', font=f12)
    s0, s1 = LENS / 2 - STRIP_W / 2, LENS / 2 + STRIP_W / 2
    sb = [*v.px(s0, PANEL_V0 + TIP_UP), *v.px(s1, PANEL_V0)]
    dr.rectangle(sb, outline='#1f4e9c', width=2); hatch(dr, sb, 8, '#6f8fd0', 1, slope=-1)
    dr.text(v.px(s0 - 21.5, PANEL_V0 + 19.5), 'folded tail, %.1f wide, tip %.1f up\nfrom the panel edge (%.2f from the lens edge)' % (STRIP_W, TIP_UP, PANEL_V0 + TIP_UP), fill='#1f4e9c', font=f12)
    # pin 1 of the tail: the strip end on the root's 19.12 side (datasheet front view: pin 1 nearer that corner)
    p1u = s1 - 0.25
    dr.ellipse([v.px(p1u - 0.6, PANEL_V0 + TIP_UP - 2.4), v.px(p1u + 0.6, PANEL_V0 + TIP_UP - 3.6)], fill='#1f4e9c')
    # centre lines
    for a, b in ((v.px(LENS / 2, LENS), v.px(LENS / 2, 0)), (v.px(0, LENS / 2), v.px(LENS, LENS / 2))):
        dashed(dr, a, b, '#888', 1, 14, 6)
    dr.text(v.px(LENS / 2 + 0.5, LENS - 3), 'centre line', fill='#666', font=f12)
    dr.text(v.px(0.8, LENS / 2 + 2.2), 'mid-height %.1f' % (LENS / 2), fill='#666', font=f12)
    # board
    x0, y0, x1, y1 = bd['outline']
    do.polygon([v.bpx(x0, y0), v.bpx(x1, y0), v.bpx(x1, y1), v.bpx(x0, y1)], fill=(46, 125, 50, 70), outline=(27, 94, 32, 255))
    if bd['ant']:
        do.polygon([v.bpx(*p) for p in bd['ant']], fill=(220, 40, 40, 70))
    img.paste(ov, (0, 0), ov); dr = ImageDraw.Draw(img)
    dr.polygon([v.bpx(x0, y0), v.bpx(x1, y0), v.bpx(x1, y1), v.bpx(x0, y1)], outline='#1b5e20', width=3)
    if bd['ant']:
        a = [v.bpx(*p) for p in bd['ant']]
        bx = (min(p[0] for p in a), min(p[1] for p in a), max(p[0] for p in a), max(p[1] for p in a))
        hatch(dr, bx, 10, '#d32f2f', 1); dr.text((bx[0] + 4, bx[1] + 4), 'antenna keep-out\n(all layers)', fill='#b71c1c', font=f12)
    # courtyards and labels
    for ref, f in sorted(bd['fps'].items()):
        x, y, r = f['at']
        if f['crt']:
            lx = [p[0] for p in f['crt']]; ly = [p[1] for p in f['crt']]
            c = [rot(a, b, r) for a in (min(lx), max(lx)) for b in (min(ly), max(ly))]
            c = [c[0], c[1], c[3], c[2]]
            pts = [v.bpx(x + a, y + b) for a, b in c]
            dr.polygon(pts, outline='#0d47a1' if ref in KEY else '#5c6f80', width=2 if ref in KEY else 1)
        for cx, cy, rr in f['circ']:
            px, py = v.bpx(x + cx, y + cy); dr.ellipse([px - rr * S, py - rr * S, px + rr * S, py + rr * S], outline='#0d47a1', width=1)
        for p in f['pads']:
            if p['drill'] >= 2.0:      # the 2.2 mm locating holes
                dx, dy = rot(*p['l'], r); px, py = v.bpx(x + dx, y + dy); rr = p['drill'] / 2 * S
                dr.ellipse([px - rr, py - rr, px + rr, py + rr], fill='black')
        cu, cv = v.bpx(x, y)
        if ref in KEY:
            fnt = f20b if ref in ('J1', 'J2', 'U1') else (f14 if ref.startswith('TP') else f16b)
            tw = dr.textlength(ref, font=fnt)
            off = {'J1': (-tw / 2, -50), 'H1': (-tw / 2, -46), 'H2': (-tw / 2, 28), 'J2': (-tw / 2, 18)}.get(ref, (-tw / 2, -9))
            dr.text((cu + off[0], cv + off[1]), ref, fill='#0d47a1', font=fnt)
        elif ref in BLOCKS:
            dr.text((cu - dr.textlength(BLOCKS[ref], font=f12) / 2, cv - 7), BLOCKS[ref], fill='#33475b', font=f12)
    # USB-C flange and opening
    jx, jy, jr = bd['fps']['J1']['at']
    cu, cv = v.bpx(jx, jy)
    w, h = USB_OPEN[0] * S, USB_OPEN[1] * S          # rot 90 on the board: the long side runs across the panel (u)
    dr.rounded_rectangle([cu - w / 2, cv - h / 2, cu + w / 2, cv + h / 2], radius=h / 2, fill='#263238', outline='black', width=2)
    xr = v.bpx(bd['outline'][0], bd['outline'][3])[0]
    dr.line([(cu + w / 2, cv), (xr + 14, cv)], fill='#263238', width=1)
    dr.text((xr + 18, cv - 9), 'USB-C mouth %.2f x %.2f' % USB_OPEN, fill='#263238', font=f14)
    # FPC entry arrow and J2's pin 1
    eu, ev = v.panel(J2_ENTRY_X, bd['outline'][3] / 2)
    arrow(dr, v.px(eu, ev - 6.5), v.px(eu, ev), '#c62828', 3, 14)
    dr.text(v.px(eu + 0.8, ev - 4.2), 'FPC in (entry %.1f)' % (TAIL_EDGE_UP + J2_ENTRY_X), fill='#c62828', font=f14)
    pu, pv = pad_panel(bd, v, 'J2', '1')
    px, py = v.px(pu, pv); dr.ellipse([px - 6, py - 6, px + 6, py + 6], fill='#c62828')
    dr.text((px + 9, py - 22), 'J2 pin 1', fill='#c62828', font=f12)
    # legend
    lx, ly = v.mx * 2 + int(LENS * S) - 20, v.my
    W, H = v.W, v.H
    hh = {h: v.panel(*bd['fps'][h]['at'][:2]) for h in ('H1', 'H2')}
    u1 = v.panel(*bd['fps']['U1']['at'][:2])
    au = sorted(v.panel(*p) for p in bd['ant']) if bd['ant'] else []
    lines = [
        ('sqrm8 P3 on the back of the panel', f20b), ('(mm, from the bottom lens edge "up";', f14), (' across from the left lens edge seen from the back)', f14), ('', f14),
        ('board %.1f (up) x %.1f (across), 10 px/mm' % (W, H), f14),
        ('tail edge: %.1f up' % TAIL_EDGE_UP, f14),
        ('board top edge: %.1f up' % (TAIL_EDGE_UP + W), f14),
        ('across: %.1f .. %.1f (centred)' % (LENS / 2 - H / 2, LENS / 2 + H / 2), f14),
        ('J2 entry: %.1f up, strip on the centre line' % (TAIL_EDGE_UP + J2_ENTRY_X), f14),
        ('  FPC seated to %.1f up (tip flat at %.2f)' % (TAIL_EDGE_UP + J2_ENTRY_X + J2_INSERT, PANEL_V0 + TIP_UP), f14),
        ('J1 (USB-C) centre: %.1f up, on the centre line' % v.panel(*bd['fps']['J1']['at'][:2])[1], f14),
        ('H1: %.1f up, %.1f across (%.1f left of centre)' % (hh['H1'][1], hh['H1'][0], LENS / 2 - hh['H1'][0]), f14),
        ('H2: %.1f up, %.1f across (%.1f right of centre)' % (hh['H2'][1], hh['H2'][0], hh['H2'][0] - LENS / 2), f14),
        ('  2.2 mm holes for the shell bosses', f14),
        ('U1 centre: %.1f up, %.1f across' % (u1[1], u1[0]), f14),
    ]
    if au:
        us = [p[0] for p in au]; vs = [p[1] for p in au]
        lines.append(('antenna keep-out: %.1f..%.1f up, %.1f..%.1f across' % (min(vs), max(vs), min(us), max(us)), f14))
    lines += [('touch keep-out: below %.0f up (board starts at %.0f)' % (TOUCH_KEEP, TAIL_EDGE_UP), f14), ('', f14),
              ('blue dot: tail pin 1 (datasheet: root side)', f14), ('red dot: J2 pad 1 on the board', f14),
              ('PANEL.md says pin 1 is LEFT seen from the back:', f14), ('to be checked on the 4B before ordering', f14)]
    yy = ly
    for s, fnt in lines:
        dr.text((lx, yy), s, fill='black', font=fnt); yy += fnt.size + 7
    img.save(out); print('wrote', out)


def section_view(bd, out):
    """Side section along the vertical centre line: v to the right (up the panel), z down (towards the back), z x2."""
    SZ = 2 * S; mx, my = 60, 60
    W, H = bd['outline'][2] - bd['outline'][0], bd['outline'][3] - bd['outline'][1]
    zmax = 16.0
    img = Image.new('RGB', (mx * 2 + int(LENS * S) + 260, my + int(zmax * SZ) + 50), 'white'); dr = ImageDraw.Draw(img)
    f12, f14, f16b = font(12), font(14), font(16, True)
    P = lambda v, z: (mx + v * S, my + z * SZ)
    def rect(v0, v1, z0, z1, fill, outline='black'):
        dr.rectangle([P(v0, z0), P(v1, z1)], fill=fill, outline=outline, width=1)
    LENSZ, STACK, TAPE, PCB, MOD, USB = 1.08, 3.18, 1.2, 1.6, 3.2, 8.8
    zt, zp = STACK, STACK + TAPE; zb = zp + PCB
    b0, b1 = TAIL_EDGE_UP, TAIL_EDGE_UP + W
    rect(0, LENS, 0, LENSZ, '#90caf9')                                    # lens + touch sensor
    rect(PANEL_V0, PANEL_V0 + PANEL_H, LENSZ, STACK, '#b0bec5')          # LCD + backlight
    rect(b0, b1, zt, zp, '#fff59d')                                      # foam tape
    jx, jy, _ = bd['fps']['J1']['at']; j0, j1 = TAIL_EDGE_UP + jx - 2.5, TAIL_EDGE_UP + jx + 2.5
    rect(j0 - 0.3, j1 + 0.3, zt, zp, 'white', '#999')                    # tape window under the USB-C blades
    rect(b0, b1, zp, zb, '#2e7d32')                                      # PCB
    ux, uy, _ = bd['fps']['U1']['at']
    rect(TAIL_EDGE_UP + ux - 9.0, TAIL_EDGE_UP + ux + 9.0, zb, zb + MOD, '#78909c')          # module
    rect(TAIL_EDGE_UP + 0.85, TAIL_EDGE_UP + 6.0, zb, zb + 2.0, '#8d6e63')                  # J2 housing (~2 mm)
    rect(j0, j1, zb, zb + USB, '#546e7a')                                 # USB-C
    # shell: inner face 0.5 over the module, 2 mm wall, a boss round the port up to its mouth
    zin, zout = zb + MOD + 0.5, zb + MOD + 2.5
    dr.line([P(0, zin), P(j0 - 1.5, zin)], fill='#d97757', width=2); dr.line([P(j1 + 1.5, zin), P(LENS, zin)], fill='#d97757', width=2)
    dr.line([P(0, zout), P(j0 - 1.5, zout)], fill='#d97757', width=2); dr.line([P(j1 + 1.5, zout), P(LENS, zout)], fill='#d97757', width=2)
    for vv in (j0 - 1.5, j1 + 1.5): dr.line([P(vv, zin), P(vv, zb + USB)], fill='#d97757', width=2)
    for vv in (j0 - 0.1, j1 + 0.1): dr.line([P(vv, zb + 3.2), P(vv, zb + USB)], fill='#d97757', width=1)
    dr.line([P(j0 - 1.5, zb + USB), P(j0 - 0.1, zb + USB)], fill='#d97757', width=2); dr.line([P(j1 + 0.1, zb + USB), P(j1 + 1.5, zb + USB)], fill='#d97757', width=2)
    dr.text(P(1, zout + 0.3), 'back shell (0.5 clearance + 2 mm wall)', fill='#b5532f', font=f12)
    # the tail: U-turn round the panel's bottom edge, flat on the back, rise into J2's slot (~1.2 above the PCB)
    tail = [P(PANEL_V0 + 1.0, 1.4), P(PANEL_V0 - 0.6, 1.6), P(PANEL_V0 - 0.9, 2.4), P(PANEL_V0 - 0.6, 3.25), P(PANEL_V0 + 1.0, 3.33),
            P(16.0, 3.33), P(18.5, 3.7), P(20.5, 5.6), P(21.6, zb + 1.1), P(22.4, zb + 1.2), P(TAIL_EDGE_UP + J2_ENTRY_X + J2_INSERT, zb + 1.2)]
    rect(PANEL_V0 + 1.9, TOUCH_KEEP - 0.3, STACK + 0.15, STACK + 1.55, '#ffcc80', '#e65100')          # touch sub-flex parts
    dr.text(P(PANEL_V0 + 2.2, STACK + 1.65), 'touch sub-flex <= 1.4', fill='#e65100', font=f12)
    dr.line(tail, fill='#1f4e9c', width=3)
    dr.text(P(24.0, zb + 2.3), 'tail rises over the board edge into J2', fill='#1f4e9c', font=f12)
    # labels on the parts
    for txt, vv, zz in (('lens + touch', 30, 0.1), ('LCD + backlight', 30, LENSZ + 0.2), ('PCB', b1 - 6, zp + 0.1),
                        ('U1', TAIL_EDGE_UP + ux - 1, zb + 0.6), ('J2', TAIL_EDGE_UP + 2.2, zb + 0.3), ('USB-C', j0 + 0.4, zb + 3.0)):
        dr.text(P(vv, zz), txt, fill='white' if txt in ('PCB', 'U1', 'USB-C') else 'black', font=f12)
    # height scale
    hx = mx + int(LENS * S) + 30
    for z, txt in ((0, 'front of the lens 0'), (STACK, 'back of the panel %.2f' % STACK), (zp, 'tape 1.2 -> %.2f' % zp),
                   (zb, 'PCB 1.6 -> %.2f' % zb), (zb + MOD, 'module 3.2 -> %.2f' % (zb + MOD)), (zout, 'shell ~%.1f' % zout),
                   (zb + USB, 'USB-C 8.8 -> %.2f (mouth)' % (zb + USB))):
        y = P(0, z)[1]; dashed(dr, (mx, y), (hx - 5, y), '#bbb', 1, 4, 4); dr.text((hx, y - 8), txt, fill='black', font=f12)
    for vv, txt in ((0, '0'), (TOUCH_KEEP, '%.0f' % TOUCH_KEEP), (b0, '%.0f' % b0), (TAIL_EDGE_UP + jx, '%.1f' % (TAIL_EDGE_UP + jx)), (b1, '%.1f' % b1), (LENS, '%.1f' % LENS)):
        x = P(vv, 0)[0]; dr.line([(x, my - 8), (x, my - 2)], fill='black'); dr.text((x - 10, my - 26), txt, fill='black', font=f12)
    dr.text((mx, my + int(15.4 * SZ)), 'section on the vertical centre line, bottom of the device on the left; v (mm up the lens) to the right, '
            'z (towards the back) down, z drawn x2', fill='black', font=f14)
    img.save(out); print('wrote', out)


if __name__ == '__main__':
    a = sys.argv
    board = a[a.index('--board') + 1] if '--board' in a else os.path.join(HERE, 'sqrm8.kicad_pcb')
    out = a[a.index('--out') + 1] if '--out' in a else os.path.expanduser('~/.cache/kicad-tools/sqrm8')
    os.makedirs(out, exist_ok=True)
    bd = read_board(board)
    back_view(bd, os.path.join(out, 'panel_view.png'))
    section_view(bd, os.path.join(out, 'panel_section.png'))
