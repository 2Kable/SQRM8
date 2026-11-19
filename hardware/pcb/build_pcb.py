#!/usr/bin/env python3
"""Build sqrm8.kicad_pcb (SQRM8 display board P3) from sqrm8.net with excalibur's pcbgen (file based, no KiCad):
outline, explicit placement, zones, silkscreen, and the copper of routes.json (written by route_board.py).

Board frame (mm, KiCad coordinates, y down): origin (0, 0) at the top-left corner, W x H, square corners (the panel is
separated by V-cuts on both axes: copper, bodies and silk >= 1 mm from every edge, connectors and the module >= 2.5 mm where
the outline allows, JLC's assembly rule near a V-cut). The board is glued on the back of the panel with the components facing
away from it and mounted rotated: the LEFT edge (x = 0, the tail edge) is the device's bottom, 22 mm up from the bottom lens
edge, board +x points up the panel and board y runs across it, y = H/2 on the panel's vertical centre line. Layout:
  * J2 (panel FPC) along the left edge, FPC entry facing -x (housing 1.1 mm, its entry silk 1.0 mm from the edge), contact
    strip centred on y = H/2, pin 1 at the +y end; a 2.5 mm channel right of its pads stays free for three via columns.
  * J1 (vertical USB-C) on the centre line at mid-height of the panel (x = 42.1 - 22 = 20.1), flange's 12 mm side along y;
    H1/H2 (shell bosses) at the same x, y = H/2 -/+ 9.5. The bus crosses this band under J1 on B.Cu and through the gaps
    between J1 and the holes; nothing else sits between J2 and J1.
  * U1 (ESP32-S3-WROOM-1) above it (x 28-46), long axis along y, GPIO column (pins 1-14) facing -x, bottom row facing +y,
    antenna end at the top (y = 0) edge 2.5 mm in, entirely on the board: the ANT keep-out (antenna region extended to the
    top and right edges) bans copper on all four layers. A 4.4 mm channel between J1 and U1 holds D1 on the USB pair (J1 ->
    D1 -> pins 13/14), R6 on CC2, and the fan-out vias of the left column; C1/C2 (3V3 pin) and C3/R1 (EN) above it.
    The module cannot sit at the x = W edge with its GPIO column facing -x (the antenna is at the end of the long axis), and
    18 mm of module plus J1 at x 20.1 need W 48.5, not 40.
  * Bottom band (y > 33): the AP3032 block under J2's LED pins (L1 - D2 along the edge, U3 over the switch node, C8 between
    D2's cathode and U3's GND), the AMS1117 below H2 with its tab towards C5/C6, then BOOT and the debug pad row bottom right.
  * J2's ends: C12/C13 (pin 5) and the CS/LED_K/CTRL resistors below the strip, C14/C15 (pin 39), the I2C pull-ups and the
    RST pull-down above it.

Run:  PYTHONDONTWRITEBYTECODE=1 $KICAD_TOOLS/kicad-py hardware/pcb/build_pcb.py [--no-routes]
"""
import sys, os, json, math, re
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.environ.get('KICAD_TOOLS', '/home/damien/projects/iot-hw-excalibur/tools/kicad')
sys.path.insert(0, TOOLS); sys.path.insert(0, HERE)   # board dir first
import pcbgen

NAME = 'sqrm8'
W, H = 48.5, 42.0          # board width (x, up the panel) and height (y, across), square corners (V-cut panel)
L = W                      # route_engine's name for the board length (stitching fence)
EDGE = 1.0                 # copper, bodies and silk to every edge (V-cuts on both axes)
VCUT_PART = 2.5            # JLC's preferred part distance from a V-cut: J2's housing ends, U1, J1
STRIP_Y = H / 2            # centre of the panel tail's contact strip = the panel's vertical centre line
# Panel frame (BOARD.md): lens 84.2 mm, the board's tail edge 22 mm up from the bottom lens edge.
LENS, TAIL_EDGE_UP = 84.2, 22.0

# J2 rotation: the FPC entry is the footprint's +y edge and pin 1 sits at local +x (the "A" end). 270 turns the entry to -x
# (the left edge, where the tail comes in) and puts pin 1 at the +y (bottom) end, pin 40 at the top: the panel's pin order
# (pin 1 at the bottom of the strip). 90 would turn the entry to +x (pin 1 at the top), i.e. the tail would come from the right.
J2_ROT = 270
J2_SILK_IN = 3.575         # entry-side silk line (local y), 0.1 mm beyond the housing (local y 3.475)
J2_X = EDGE + J2_SILK_IN   # footprint origin: silk 1.0 mm, housing 1.1 mm from the left edge
# J1: mid-height of the panel (42.1 mm up = board x 20.1) on the centre line; rot 90 lays the 12 x 5 flange's long side along
# y (the port opening 8.94 x 3.16 runs across the panel). H1/H2 flank it on the same x: hole edge 9.3 mm in from the edges.
J1_X, J1_Y, J1_ROT = LENS / 2 - TAIL_EDGE_UP, H / 2, 90
H_DY = 9.5
# U1: long axis along y, antenna end at the top edge, body VCUT_PART from the top and right edges, GPIO column facing J1/J2.
U1_X, U1_Y = W - VCUT_PART - 9.0, VCUT_PART + 12.75
# Antenna keep-out (Espressif): the module's antenna region (body local y -12.75 .. -6.75, full body width), extended to the
# top and right board edges. No copper on any layer, no pour.
ANT = (U1_X - 9.0, 0.0, W, U1_Y - 6.75)

# ---------------------------------------------------------------- placement: ref -> (x, y, rot[, 'B'])
P = {
    'J2': (J2_X, STRIP_Y, J2_ROT),
    'J1': (J1_X, J1_Y, J1_ROT),
    'H1': (J1_X, J1_Y - H_DY, 0), 'H2': (J1_X, J1_Y + H_DY, 0),
    'U1': (U1_X, U1_Y, 0),
    # channel J1 | U1: C2 (100n) pad 1 level with the 3V3 pin, C1 above it, C3/R1 for EN above; they double as the 3V3-GND
    # pair at the ribbon's U1 end. D1 on the pair, USB_N row level with pin 13; R6 on CC2 (B5, J1's right row).
    'C2': (25.6, 11.26, 180), 'C1': (25.6, 9.7, 180), 'C3': (25.6, 8.1, 180), 'R1': (25.6, 6.5, 180),
    'D1': (25.05, 25.85, 180), 'R6': (24.4, 20.6, 0),
    # left of J1: R5 on CC1 (A5, J1's left row); the bus passes under it on B.Cu
    'R5': (16.3, 23.2, 270),
    # J2 top end: pin 39 (TP_VCC) decoupling within 3 mm, I2C pull-ups and the RST pull-down beside it
    'C15': (9.6, 10.9, 0), 'C14': (9.6, 9.3, 0), 'R4': (12.6, 10.9, 0), 'R3': (12.6, 9.3, 0), 'R9': (15.6, 10.9, 0),
    # J2 bottom end: pin 5 (VDD) decoupling within 3 mm, the CS pull-up, LED_K sense, CTRL pull-down and BL_PWM series R
    'C13': (9.6, 29.6, 0), 'C12': (9.6, 31.2, 0), 'R10': (12.6, 29.6, 0), 'R8': (12.6, 31.2, 0),
    'R7': (12.6, 33.0, 0), 'R11': (15.6, 32.75, 0),
    # AP3032 boost along the bottom edge under J2's LED pins: L1 (VBUS -> SW), D2 anode on the SW node, U3 (rot 90: SW, GND,
    # FB on its lower row) over the node, C8 between D2's cathode and U3's GND, C7 on VBUS between L1 and U3's VIN
    'L1': (4.5, 39.25, 0), 'D2': (10.0, 39.25, 180), 'U3': (9.0, 35.45, 90), 'C8': (12.9, 35.6, 180),
    'C7': (4.3, 35.5, 90), 'C9': (15.45, 35.3, 90),
    # AMS1117 below H2: VIN towards the VBUS island (C4), the tab towards C5/C6 and a +3V3 F.Cu area with tab vias
    'U2': (22.6, 37.2, 0), 'C4': (16.9, 39.2, 90), 'C5': (29.2, 37.2, 90), 'C6': (31.1, 37.2, 90),
    # BOOT button and its pull-up bottom right, away from J1 (8.8 mm tall): a pin hole in the shell reaches it
    'SW1': (42.5, 33.0, 180), 'R2': (37.0, 33.0, 0),
}
# debug pads: a row along the bottom edge, 2.54 pitch (TX/RX come down the right edge from U1's right column), labels above
TP_ROW = [('TP5', 'EN'), ('TP4', '3V3'), ('TP3', 'GND'), ('TP2', 'RX'), ('TP1', 'TX')]
TP_P, TP_Y, TP_X0 = 2.54, H - EDGE - 1.25, 35.09
def tp_x(i): return TP_X0 + i * TP_P
for i, (tp, _) in enumerate(TP_ROW): P[tp] = (tp_x(i), TP_Y, 0)

# In2: +3V3 everywhere (priority 1) except a VBUS island (priority 2) in the bottom band under U2's input, C4 and the AP3032
# block (U2's tab and C5/C6 stay on +3V3 for the tab vias). In2 is the reference of the B.Cu bus under J1 and the module, so
# VBUS leaves J1 on F.Cu (two trunks, x 15.3 and x 22.65) and only meets In2 at the island: no split under the bus.
V33_POUR = [(-1, -1), (W + 1, -1), (W + 1, H + 1), (-1, H + 1)]
VBUS_POUR = [(-1, 33.0), (23.2, 33.0), (23.2, H + 1), (-1, H + 1)]
# F.Cu +3V3 area round U2's tab and the output caps (heat spreader, tab vias into In2)
TAB_POUR = [(24.2, 34.7), (32.3, 34.7), (32.3, 39.7), (24.2, 39.7)]
HOLE_KEEP = 1.1 + 0.5      # hole radius + 0.5 mm annular room: no copper, no pour

TX1 = dict(size=1.0, thickness=0.15, width=0.8)
SILK = []
for i, (tp, name) in enumerate(TP_ROW):
    SILK.append((name, (tp_x(i), TP_Y - 1.95), dict(TX1, width=0.6)))
# board name in the free top band left of the antenna keep-out, JLC's order-number placeholder under it
SILK += [('SQRM8', (13.0, 3.5), TX1), ('P3', (13.0, 4.8), TX1),
         ('JLCJLCJLCJLC', (13.0, 6.6), dict(TX1, width=0.7)), ('BOOT', (42.5, 30.0), dict(TX1, width=0.6))]
SHOW_REFS = {'U1': (U1_X, 22.0, 0), 'J1': (J1_X - 3.6, J1_Y, 90)}
STITCH_KEEPOUT = [ANT, (6.0, 0.0, 21.0, 7.6), (32.0, 36.6, W, H)]   # no fence vias under the texts / the debug pad labels


# ---------------------------------------------------------------- geometry helpers
def outline_segments():
    """Closed Edge.Cuts contour: a plain W x H rectangle, square corners (the panel separates by V-cuts on both axes)."""
    c = [(0, 0), (W, 0), (W, H), (0, H)]
    return [('line', c[i], c[(i + 1) % 4]) for i in range(4)]


def body_polygon():
    from shapely.geometry import box
    return box(0, 0, W, H)


def _rot(lx, ly, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    return lx * c + ly * s, -lx * s + ly * c


_FP = {}
def _fp_pads(ref):
    """[(number, lx, ly)] of a part's footprint (local coordinates), cached."""
    if ref not in _FP:
        comps, _ = pcbgen.parse_netlist(os.path.join(HERE, NAME + '.net'))
        lib, name = comps[ref]['footprint'].split(':', 1)
        t = open(os.path.join(HERE, lib + '.pretty', name + '.kicad_mod')).read()
        _FP[ref] = [(m.group(1), float(m.group(2)), float(m.group(3)))
                    for m in re.finditer(r'\(pad "([^"]*)" \w+ \w+\s+\(at ([-\d.]+) ([-\d.]+)', t)]
    return _FP[ref]


def pad(ref, num, i=0):
    """Board position of pad `num` of `ref` (i-th pad of that number), from the placement table: routes_manual uses it so
    the hand copper follows the parts."""
    x, y, rot = P[ref][:3]
    hits = [(lx, ly) for n, lx, ly in _fp_pads(ref) if n == num]
    lx, ly = hits[i]
    dx, dy = _rot(lx, ly, rot)
    return (round(x + dx, 4), round(y + dy, 4))


def courtyards(b):
    """{ref: (x0, y0, x1, y1)} board courtyard boxes. U1 uses its body courtyard (the stock footprint's courtyard also draws
    Espressif's 24 mm-wide antenna clearance, which the board implements as the ANT keep-out instead)."""
    out = {}
    for ref, v in P.items():
        x, y, rot = v[:3]
        cy = pcbgen.courtyard(b.fp_text(b.comps[ref]['footprint']))
        if ref == 'U1': cy = (-9.75, -13.15, 9.75, 13.45)
        r = pcbgen.rot_rect(cy, rot)
        out[ref] = (x + r[0], y + r[1], x + r[2], y + r[3])
    return out


def circle(c, r, n=24):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def add_keepout(b, pts, name):
    """Rule area on all four copper layers: no tracks, no vias, no pour (pcbgen's keepout only forbids pour)."""
    b.add_zone('', ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'], pts, priority=0, name=name, keepout=True)
    z = b.zones[-1]
    b.zones[-1] = z.replace('(tracks allowed)', '(tracks not_allowed)').replace('(vias allowed)', '(vias not_allowed)')


def rect(r):
    return [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]


# ---------------------------------------------------------------- post-processing (as pcb-flash)
def fix_refs(path):
    """Hide the Reference text of every footprint not in SHOW_REFS, move the shown ones to SHOW_REFS (board coordinates)."""
    t = open(path).read(); out = []; pos = 0
    for m in re.finditer(r'\n\t\(footprint "', t):
        blk = pcbgen.extract_block(t, m.start() + 2)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
        fx, fy, fr = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        pm = re.search(r'\(property "Reference" "[^"]*"\n\t\t\t\(at [^)]*\)', blk)
        nb = blk
        if ref in SHOW_REFS:
            x, y, r = SHOW_REFS[ref]; dx, dy = x - fx, y - fy
            a = math.radians(fr); lx = dx * math.cos(a) - dy * math.sin(a); ly = dx * math.sin(a) + dy * math.cos(a)
            nb = nb.replace(pm.group(0), re.sub(r'\(at [^)]*\)', '(at %s %s %s)' % (pcbgen._f(lx), pcbgen._f(ly), pcbgen._f(r)), pm.group(0)), 1)
        else:
            i = nb.index('(property "Reference"'); blk2 = pcbgen.extract_block(nb, i)
            if '(hide yes)' not in blk2: nb = nb.replace(blk2, blk2.replace('\n\t\t\t(layer', '\n\t\t\t(hide yes)\n\t\t\t(layer', 1), 1)
        out.append(t[pos:m.start() + 2] + nb); pos = m.start() + 2 + len(blk)
    out.append(t[pos:]); open(path, 'w').write(''.join(out))


def fix_descriptions(path):
    """Copy each symbol's description (netlist (comp (description ...))) into the footprint's Description property."""
    net = open(os.path.join(HERE, NAME + '.net')).read()
    desc = {}
    for m in re.finditer(r'\(comp\s', net):
        cb = pcbgen.extract_block(net, m.start())
        ref = re.search(r'\(ref "([^"]*)"\)', cb).group(1)
        dm = re.search(r'\n\t\t\t\(description "((?:[^"\\]|\\.)*)"\)', cb)
        if dm: desc[ref] = dm.group(1)
    t = open(path).read(); out = []; pos = 0
    for m in re.finditer(r'\n\t\(footprint "', t):
        blk = pcbgen.extract_block(t, m.start() + 2)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        if ref in desc: blk = blk.replace('(property "Description" ""', '(property "Description" "%s"' % desc[ref], 1)
        out.append(t[pos:m.start() + 2] + blk); pos = m.start() + 2 + len(pcbgen.extract_block(t, m.start() + 2))
    out.append(t[pos:]); open(path, 'w').write(''.join(out))


SOLID_PADS = {'U2': '(size 2 3.8)',  # ref -> the pad's size clause: the SOT-223 tab (pad 2, the large one)
              'J1': '(size 0.5 1.59)'}  # J1's signal row: A1 is boxed in by A4 and the USB_P track (one spoke only); only
                                        # its GND pads (A1/A12/B1/B12) meet the GND pour, the others are other nets


def solid_pads(path, which):
    """Give the named pads a solid zone connection (zone_connect 2) whatever the zone's relief setting: the heat paths."""
    t = open(path).read(); out = []; pos = 0
    for m in re.finditer(r'\n\t\(footprint "', t):
        blk = pcbgen.extract_block(t, m.start() + 2)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        nb = blk
        if ref in which:
            for pm in re.finditer(r'\(pad "', blk):
                pb = pcbgen.extract_block(blk, pm.start())
                if which[ref] in pb and '(zone_connect' not in pb:
                    nb = nb.replace(pb, pb[:-1].rstrip() + '\n\t\t\t(zone_connect 2)\n\t\t)', 1)
        out.append(t[pos:m.start() + 2] + nb); pos = m.start() + 2 + len(blk)
    out.append(t[pos:]); open(path, 'w').write(''.join(out))


def set_origin():
    """Fab origin (aux_axis_origin) = the board's lower-left corner; rewritten in the template when H changes."""
    p = os.path.join(HERE, 'template.kicad_pcb'); t = open(p).read()
    n = re.sub(r'\(aux_axis_origin [-\d.]+ [-\d.]+\)', '(aux_axis_origin 0 %s)' % pcbgen._f(H), t)
    if n != t: open(p, 'w').write(n)


def build(with_routes=True, out=os.path.join(HERE, NAME + '.kicad_pcb')):
    if J2_ROT not in (90, 270): raise ValueError('J2_ROT must be 90 or 270')
    set_origin()
    b = pcbgen.Board(template=os.path.join(HERE, 'template.kicad_pcb'), netlist=os.path.join(HERE, NAME + '.net'), proj_dir=HERE,
                     sheetfile=NAME + '.kicad_sch', libname=NAME)
    missing = [r for r in b.comps if r not in P]
    print('UNPLACED:', ' '.join(sorted(missing)))
    for ref, v in P.items():
        b.place(ref, (v[0], v[1]), v[2], side=v[3] if len(v) > 3 else 'F')
    for seg in outline_segments(): b.outline_line(seg[1], seg[2])
    # ---- zones. In1 GND; In2 +3V3 with a VBUS island; F/B GND fills; a +3V3 area on F round U2's tab. Thermal reliefs on
    # every pour-connected pad (two-pad parts with one end solid in a pour tombstone); U1's exposed pad (zone_connect 2 in
    # its footprint) and U2's tab (solid_pads below) stay solid for heat.
    full = [(-1, -1), (W + 1, -1), (W + 1, H + 1), (-1, H + 1)]
    b.add_zone('GND', ['In1.Cu'], full, priority=0, name='GND plane')
    b.add_zone('+3V3', ['In2.Cu'], V33_POUR, priority=1, name='+3V3 pour')
    b.add_zone('VBUS', ['In2.Cu'], VBUS_POUR, priority=2, name='VBUS island')
    b.add_zone('GND', ['F.Cu'], full, priority=0, name='GND F')
    b.add_zone('GND', ['B.Cu'], full, priority=0, name='GND B')
    b.add_zone('+3V3', ['F.Cu'], TAB_POUR, priority=1, name='U2 tab +3V3')
    for i, z in enumerate(b.zones):
        b.zones[i] = z.replace('(thermal_gap 0.5)', '(thermal_gap 0.3)').replace('(thermal_bridge_width 0.5)', '(thermal_bridge_width 0.4)')
    add_keepout(b, rect(ANT), 'U1 antenna keep-out')
    for ref in ('H1', 'H2'): add_keepout(b, circle(P[ref][:2], HOLE_KEEP), ref + ' keep-out')
    for t in SILK: b.add_text(*t[:2], **t[2])
    if with_routes:
        rp = os.path.join(HERE, 'routes.json')
        if os.path.exists(rp):
            R = json.load(open(rp))
            for t in R.get('tracks', []): b.add_track(t['net'], t['layer'], tuple(t['start']), tuple(t['end']), t['w'])
            for v in R.get('vias', []): b.add_via(v['net'], tuple(v['pos']), v.get('dia', 0.45), v.get('drill', 0.3))
            print('routes:', len(R.get('tracks', [])), 'tracks', len(R.get('vias', [])), 'vias')
    res = b.write(out); fix_refs(out); fix_descriptions(out); solid_pads(out, SOLID_PADS)
    return b, res


if __name__ == '__main__':
    print(build('--no-routes' not in sys.argv)[1])
