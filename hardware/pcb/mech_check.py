#!/usr/bin/env python3
"""sqrm8 placement checker (run by `board.sh <dir> check`, or alone), adapted from excalibur's pcb-level-rigid / pcb-flash.

  PYTHONDONTWRITEBYTECODE=1 $KICAD_TOOLS/kicad-py hardware/pcb/mech_check.py [--png [OUT.png]] [--zoom X0,Y0,X1,Y1] [--routes]

Checks on the build_pcb.P placement table (courtyard bounding boxes, board frame, origin top-left, y down):
  * no two courtyards overlap (H1/H2 as their stock r 2.45 circles); every courtyard >= EDGE (1 mm, V-cut panel) from the
    edges; U1 by its pads and antenna-end silk (pads 0.5 mm past the body); no part inside the antenna keep-out (ANT);
  * JLC's 2.5 mm part-to-V-cut preference (VCUT_PART) for U1's body, J1's courtyard and J2's housing ends;
  * J2: FPC entry edge (local +y) facing -x, housing within 1.1 mm of the left edge and its entry silk >= EDGE; strip
    centre (pins 20/21) at y = H/2 (the panel's centre line); pin 1 at the +y end; no part in the via channel (VIA_CHANNEL
    mm right of its pads, over the bus pins 6-38);
  * J1 on the centre line at mid-height of the panel (x = 42.1 - TAIL_EDGE_UP), flange's long side along y; H1/H2 at J1's x,
    y = H/2 -/+ H_DY, hole edge >= HOLE_EDGE from every edge;
  * U1: GPIO column (pins 1-14) facing -x, antenna region inside ANT and ANT reaching the board edge(s) past it;
  * NEAR: pad-to-pad (copper edge) distances of the decoupling, ESD, CC and boost-loop parts;
  * every part on the top side (the board is glued flat on the panel).
--png draws courtyards and pads (coloured by net, net names on request) of the last built board to
~/.cache/kicad-tools/sqrm8/placement.png (antenna keep-out in red, the 1 mm edge band dashed, In2 VBUS island red dotted,
U2's F.Cu +3V3 area orange dotted, hole keep-outs red dashed).
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.environ.get('KICAD_TOOLS', '/home/damien/projects/iot-hw-excalibur/tools/kicad')
sys.path.insert(0, TOOLS); sys.path.insert(0, HERE)

NAME = 'sqrm8'
EDGE = 1.0                 # courtyards (here = bodies + 0.25, or the body itself for SW1/D2/U2) to every board edge
J1_MARGIN = 0.0            # other courtyards may touch J1's
HOLE_EDGE = 1.5            # H1/H2 hole edge to every board edge (they locate the board on the shell bosses)
VIA_CHANNEL = 2.5          # free of parts right of J2's pad row (three via columns >= 0.95 mm apart)
# (ref, pad, ref, pad, max copper-edge distance mm): the brief's proximity rules
NEAR = [('C2', '1', 'U1', '2', 2.5), ('C1', '1', 'U1', '2', 4.0), ('C3', '1', 'U1', '3', 6.0), ('R1', '2', 'U1', '3', 7.0),
        ('C12', '1', 'J2', '5', 3.0), ('C13', '1', 'J2', '5', 3.0), ('C14', '1', 'J2', '39', 3.0), ('C15', '1', 'J2', '39', 3.0),
        ('D1', '4', 'J1', 'B7', 5.0), ('D1', '6', 'J1', 'B6', 6.0),   # USB_P's D1 pads sit 1.9 mm lower (U1 pins 13/14 order)
        ('D1', '3', 'U1', '13', 2.5), ('D1', '1', 'U1', '14', 2.5),
        ('R5', '1', 'J1', 'A5', 3.0), ('R6', '1', 'J1', 'B5', 3.0),
        ('U3', '1', 'L1', '2', 3.0), ('U3', '1', 'D2', '2', 3.0), ('D2', '1', 'C8', '1', 4.0), ('C8', '2', 'U3', '2', 3.5),
        ('C7', '1', 'U3', '6', 4.0), ('C4', '1', 'U2', '3', 2.5), ('C5', '1', 'U2', '2', 4.0), ('R2', '2', 'SW1', '2', 3.0)]
OUT = os.path.expanduser('~/.cache/kicad-tools/%s' % NAME)


def board():
    import pcbgen
    return pcbgen.Board(os.path.join(HERE, 'template.kicad_pcb'), os.path.join(HERE, NAME + '.net'), HERE, NAME + '.kicad_sch', libname=NAME)


def shapes(bp, b):
    from shapely.geometry import box, Point
    out = {}
    for ref, r in bp.courtyards(b).items():
        if ref.startswith('H'):
            x, y = bp.P[ref][:2]; out[ref] = Point(x, y).buffer((r[2] - r[0]) / 2, 32)   # stock M2 courtyard, r 2.45
        else:
            out[ref] = box(*r)
    return out


_PADS = {}
def pad_boxes(bp, ref, num):
    """Board copper boxes of pad `num` of `ref` (axis-aligned: every rotation here is a multiple of 90)."""
    import re
    from shapely.geometry import box
    if ref not in _PADS:
        import pcbgen
        comps, _ = pcbgen.parse_netlist(os.path.join(HERE, NAME + '.net'))
        lib, name = comps[ref]['footprint'].split(':', 1)
        txt = open(os.path.join(HERE, lib + '.pretty', name + '.kicad_mod')).read()
        _PADS[ref] = [(m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4) or 0), float(m.group(5)), float(m.group(6)))
                      for m in re.finditer(r'\(pad "([^"]*)" \w+ \w+\s+\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s+\(size ([-\d.]+) ([-\d.]+)\)', txt)]
    x, y, rot = bp.P[ref][:3]; out = []
    for n, lx, ly, a, sx, sy in _PADS[ref]:
        if n != num: continue
        dx, dy = bp._rot(lx, ly, rot)
        if round((a + rot) / 90) % 2: sx, sy = sy, sx
        out.append(box(x + dx - sx / 2, y + dy - sy / 2, x + dx + sx / 2, y + dy + sy / 2))
    return out


def near(bp, a, pa, b, pb):
    return min(g.distance(h) for g in pad_boxes(bp, a, pa) for h in pad_boxes(bp, b, pb))


def check(bp):
    from shapely.geometry import box
    b = board(); sh = shapes(bp, b); errs = []
    W, H = bp.W, bp.H
    inner = box(EDGE, EDGE, W - EDGE, H - EDGE)
    ant = box(*bp.ANT)
    for ref, g in sh.items():
        side = bp.P[ref][3] if len(bp.P[ref]) > 3 else 'F'
        if side != 'F': errs.append('%s on the bottom side' % ref)
        if ref == 'U1':
            # body (+-9 x +-12.75) inside, pads (0.5 mm past the body sideways) and silk (antenna end) >= EDGE from the edges
            x, y = bp.P['U1'][:2]
            if not inner.contains(box(x - 9.5, y - 12.9, x + 9.5, y + 13.25)): errs.append('U1 pads/silk closer than %.1f mm to an edge' % EDGE)
            continue
        if ref == 'J2': continue                                          # checked below (entry side)
        if ref.startswith('H'):
            x, y = bp.P[ref][:2]
            if not box(1.1 + EDGE, 1.1 + EDGE, W - 1.1 - EDGE, H - 1.1 - EDGE).contains(box(x, y, x, y)): errs.append('%s hole edge closer than %.1f mm to an edge' % (ref, EDGE))
        elif not inner.contains(g):
            errs.append('%s courtyard %s closer than %.1f mm to an edge' % (ref, tuple(round(v, 2) for v in g.bounds), EDGE))
        if ref != 'U1' and g.intersection(ant).area > 1e-4: errs.append('%s inside the antenna keep-out' % ref)
    refs = sorted(sh)
    for i, a in enumerate(refs):
        for c in refs[i + 1:]:
            if sh[a].intersection(sh[c]).area > 1e-4:
                errs.append('courtyard overlap %s / %s (%.2f mm2)' % (a, c, sh[a].intersection(sh[c]).area))
    j1 = sh['J1'].buffer(J1_MARGIN, join_style=2) if J1_MARGIN else sh['J1']
    for ref, g in sh.items():
        if ref != 'J1' and j1.intersection(g).area > 1e-4:
            errs.append('%s within %.1f mm of J1 courtyard' % (ref, J1_MARGIN))
    # J2: entry edge (housing local y = +3.475, silk +3.575) facing -x, housing within 1.1 mm of the left edge, silk >= EDGE
    x, y, rot = bp.P['J2'][:3]
    ex, ey = bp._rot(0, 3.475, rot)
    if not (abs(ey) < 1e-6 and ex < 0): errs.append('J2 entry does not face -x (J2_ROT %s)' % rot)
    entry_x = x + ex; silk_x = x + bp._rot(0, 3.575, rot)[0]
    if not (0 <= entry_x <= 1.1 + 1e-6): errs.append('J2 housing at x %.3f, not within 1.1 mm of the left edge' % entry_x)
    if silk_x < EDGE - 1e-6: errs.append('J2 entry silk at x %.3f, closer than %.1f mm to the left edge' % (silk_x, EDGE))
    jx0, jy0, jx1, jy1 = sh['J2'].bounds
    if jy0 < EDGE or jy1 > H - EDGE: errs.append('J2 ends closer than %.1f mm to the top/bottom edge' % EDGE)
    mid = (bp.pad('J2', '20')[1] + bp.pad('J2', '21')[1]) / 2
    if abs(mid - bp.STRIP_Y) > 1e-6: errs.append('J2 strip centre at y %.3f, not %.3f' % (mid, bp.STRIP_Y))
    if bp.pad('J2', '1')[1] < bp.pad('J2', '40')[1]: errs.append('J2 pin 1 is not at the +y (bottom) end')
    # U1 entirely inside, antenna end at the top edge
    if bp.ANT[1] > 0 or bp.ANT[2] < W: errs.append('antenna keep-out does not reach the top and right edges')
    # JLC's part-to-V-cut preference
    x, y = bp.P['U1'][:2]
    vin = box(bp.VCUT_PART, bp.VCUT_PART, W - bp.VCUT_PART, H - bp.VCUT_PART)
    if not vin.contains(box(x - 9.0, y - 12.75, x + 9.0, y + 12.75)): errs.append('U1 body closer than %.1f mm to an edge' % bp.VCUT_PART)
    if not vin.contains(sh['J1']): errs.append('J1 courtyard closer than %.1f mm to an edge' % bp.VCUT_PART)
    if jy0 < bp.VCUT_PART or jy1 > H - bp.VCUT_PART: errs.append('J2 housing ends closer than %.1f mm to the top/bottom edge' % bp.VCUT_PART)
    # J2's via channel: no courtyard right of the pad row over the bus pins
    px = max(g.bounds[2] for g in pad_boxes(bp, 'J2', '20'))
    ch = box(px, bp.pad('J2', '38')[1] - 0.25, px + VIA_CHANNEL, bp.pad('J2', '6')[1] + 0.25)
    for ref, g in sh.items():
        if ref != 'J2' and g.intersection(ch).area > 1e-4: errs.append('%s in the via channel right of J2' % ref)
    # U1: GPIO column facing -x; antenna region (body local y -12.75..-6.75) inside ANT, ANT out to the edge past it
    if bp.pad('U1', '1')[0] >= x or bp.pad('U1', '14')[0] >= x: errs.append('U1 GPIO column (pins 1-14) does not face -x')
    r = bp._rot(0, -1, bp.P['U1'][2])
    c = [bp._rot(lx, ly, bp.P['U1'][2]) for lx in (-9.0, 9.0) for ly in (-12.75, -6.75)]
    areg = box(x + min(p[0] for p in c), y + min(p[1] for p in c), x + max(p[0] for p in c), y + max(p[1] for p in c))
    ant = box(*bp.ANT)
    if ant.intersection(areg).area < areg.area - 1e-4: errs.append('antenna region not inside the keep-out')
    reach = {(1, 0): bp.ANT[2] >= W, (-1, 0): bp.ANT[0] <= 0, (0, 1): bp.ANT[3] >= H, (0, -1): bp.ANT[1] <= 0}
    if not reach[(round(r[0]), round(r[1]))]: errs.append('antenna keep-out does not reach the edge past the antenna end')
    # J1 on the centre line at mid-height of the panel, 12 mm side along y; the holes on its x, -/+ H_DY
    jx, jy = bp.P['J1'][:2]
    if abs(jx - (bp.LENS / 2 - bp.TAIL_EDGE_UP)) > 1e-6: errs.append('J1 at x %.3f, not %.2f (panel mid-height)' % (jx, bp.LENS / 2 - bp.TAIL_EDGE_UP))
    if abs(jy - H / 2) > 1e-6: errs.append('J1 at y %.3f, not on the centre line y = %.2f' % (jy, H / 2))
    b0 = sh['J1'].bounds
    if not (b0[3] - b0[1] > b0[2] - b0[0]): errs.append('J1 flange long side not along y')
    for h, s in (('H1', -1), ('H2', 1)):
        hx, hy = bp.P[h][:2]
        if abs(hx - jx) > 1e-6 or abs(hy - (H / 2 + s * bp.H_DY)) > 1e-6: errs.append('%s at (%.2f, %.2f), not (%.2f, %.2f)' % (h, hx, hy, jx, H / 2 + s * bp.H_DY))
        if min(hx, hy, W - hx, H - hy) - 1.1 < HOLE_EDGE - 1e-6: errs.append('%s hole edge closer than %.1f mm to an edge' % (h, HOLE_EDGE))
    if bp.TAIL_EDGE_UP < 15.0: errs.append('board tail edge inside the 15 mm touch-flex keep-out')
    for a, pa, b_, pb, lim in NEAR:
        d = near(bp, a, pa, b_, pb)
        if d > lim + 1e-6: errs.append('%s.%s to %s.%s %.2f mm (> %.1f)' % (a, pa, b_, pb, d, lim))
    return errs, sh


def png(bp, sh, out, zoom=None, routes=False, labels=True):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    import board_file_dump
    from route_engine import pad_shapes
    d = board_file_dump.dump(os.path.join(HERE, NAME + '.kicad_pcb'))
    x0, y0, x1, y1 = zoom or (-1, -1, bp.W + 1, bp.H + 1)
    fig, ax = plt.subplots(figsize=(16, 16 * (y1 - y0) / (x1 - x0)))
    ax.add_patch(plt.Polygon(list(bp.body_polygon().exterior.coords), fill=False, ec='#ff0', lw=1.2))
    ax.add_patch(plt.Polygon(list(bp.body_polygon().buffer(-EDGE, join_style=2).exterior.coords), fill=False, ec='#880', lw=0.6, ls='--'))
    a = bp.ANT; ax.add_patch(Rectangle((a[0], a[1]), a[2] - a[0], a[3] - a[1], fc='#f00', alpha=0.15, ec='#f00'))
    ax.add_patch(plt.Polygon(bp.VBUS_POUR, fill=False, ec='#d33', lw=0.8, ls=':'))          # In2 VBUS island
    ax.add_patch(plt.Polygon(bp.TAB_POUR, fill=False, ec='#f90', lw=0.8, ls=':'))           # F.Cu +3V3 at U2's tab
    for h in ('H1', 'H2'): ax.add_patch(Circle(bp.P[h][:2], bp.HOLE_KEEP, fill=False, ec='#f00', lw=0.6, ls='--'))
    col = {'GND': '#2a7', 'VBUS': '#d33', '+3V3': '#f90', 'LED_A': '#c3f', 'BL_SW': '#f3c'}
    if routes:
        for t in d['tracks']:
            c = {'F.Cu': '#c33', 'B.Cu': '#36f'}.get(t['layer'], '#999')
            ax.plot([t['start'][0], t['end'][0]], [t['start'][1], t['end'][1]], color=c, lw=t['w'] * 16 / (x1 - x0) * 72, alpha=0.6, solid_capstyle='round')
        for v in d['vias']: ax.add_patch(Circle(v['pos'], v['dia'] / 2, fc='#bbb', ec='k', lw=0.3))
    for f in d['footprints']:
        for p in f['pads']:
            for lay, g in pad_shapes(p):
                if lay != 'F.Cu': continue
                xs, ys = g.exterior.xy
                net = p['net'] or ''
                c = col.get(net, '#ccc' if net and not net.startswith('unconnected') else '#555')
                if net.startswith('USB'): c = '#0cf'
                ax.fill(xs, ys, color=c, alpha=0.85, lw=0)
                if labels and zoom and net and not net.startswith('unconnected'):
                    ax.text(p['pos'][0], p['pos'][1], net.replace('LCD_', ''), fontsize=5, ha='center', va='center', color='k', rotation=0)
            if p['type'] == 4:
                ax.add_patch(Circle(p['pos'], p['copper'][0]['size'][0] / 2 if p['copper'] else 0.3, fc='k', ec='w', lw=0.3))
    for ref, g in sh.items():
        xs, ys = g.exterior.xy; ax.plot(xs, ys, lw=0.6, color='#0ff')
        c = g.centroid; ax.text(c.x, c.y, ref, ha='center', va='center', fontsize=7, color='w')
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal'); ax.grid(lw=0.2, alpha=0.4)
    ax.set_xticks([i for i in range(int(x0), int(x1) + 1)]); ax.set_yticks([i for i in range(int(y0), int(y1) + 1)])
    ax.tick_params(labelsize=6); ax.set_facecolor('#111')
    fig.savefig(out, dpi=130, bbox_inches='tight'); plt.close(fig); print('wrote', out)


if __name__ == '__main__':
    if not os.path.exists(os.path.join(HERE, 'build_pcb.py')):
        print('mech_check: no build_pcb.py yet (no placement), nothing to check'); sys.exit(0)
    import build_pcb
    errs, sh = check(build_pcb)
    if '--png' in sys.argv:
        i = sys.argv.index('--png')
        out = sys.argv[i + 1] if len(sys.argv) > i + 1 and not sys.argv[i + 1].startswith('--') else os.path.join(OUT, 'placement.png')
        zoom = None
        if '--zoom' in sys.argv: zoom = [float(v) for v in sys.argv[sys.argv.index('--zoom') + 1].split(',')]
        os.makedirs(os.path.dirname(out), exist_ok=True); png(build_pcb, sh, out, zoom, routes='--routes' in sys.argv)
    for e in errs: print('MECH:', e)
    print('mech_check: %d issue(s)' % len(errs))
    sys.exit(1 if errs else 0)
