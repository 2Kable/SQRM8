#!/usr/bin/env python3
"""Route sqrm8 (file based, no KiCad): writes routes.json (read by build_pcb.py) and rebuilds the board.
Engine and stage description: excalibur tools/kicad/route_engine.py (used in place, read-only); this file holds only the
board's planes, widths and stitching settings.

Usage: PYTHONDONTWRITEBYTECODE=1 $KICAD_TOOLS/kicad-py hardware/pcb/route_board.py [--reset] [--manual-only] [--no-router]
   or: tools/kicad/board.sh <repo>/hardware/pcb route [--reset] [--manual-only] [--no-router]
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.environ.get('KICAD_TOOLS', '/home/damien/projects/iot-hw-excalibur/tools/kicad')
sys.path.insert(0, TOOLS); sys.path.insert(0, HERE)   # board dir first
import route_engine as E
import build_pcb
from shapely.geometry import Polygon

ANT = Polygon(build_pcb.rect(build_pcb.ANT))
VBUS = Polygon(build_pcb.VBUS_POUR).difference(ANT)
CFG = E.Config(
    board=os.path.join(HERE, 'sqrm8.kicad_pcb'), build=build_pcb,
    planes={'GND': None, 'VBUS': VBUS, '+3V3': Polygon(build_pcb.V33_POUR).difference(VBUS.buffer(0.25)).difference(ANT)},   # None = In1 everywhere
    power_w={'GND': 0.3, 'VBUS': 0.4, '+3V3': 0.3, 'LED_A': 0.3, 'BL_SW': 0.5, 'LED_K': 0.3},
    plane_via_nets=('GND', '+3V3', 'VBUS'),
    plane_via_skip=(),
    stitch_pair_nets=('USB_P', 'USB_N'),
    stitch_body_clip=(-1, -1, 0.01, build_pcb.H + 1),   # the default clips the fence at y = 30 (excalibur's 22 mm boards)
    edge_clearance=build_pcb.EDGE,                      # V-cut panel: copper >= 1 mm from every edge
    stitch_ring_inset=build_pcb.EDGE + 0.4,             # fence vias (0.45) fully 1 mm in
    stitch_fence_cut=-1.0,                              # no tab root on this board: fence all the way round
)

if __name__ == '__main__':
    E.main(CFG, sys.argv)
