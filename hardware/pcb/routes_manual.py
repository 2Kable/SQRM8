"""Hand-written copper for sqrm8 P2/P3 (consumed by route_board.py): the design intent for every signal net; the router only adds
plane vias, leftovers and stitching. TRACKS: (net, layer, width, [points]) polylines, 45-degree geometry; VIAS: (net, (x, y)),
0.45/0.3 mm, tented. Pad positions come from build_pcb.pad() (placement table + footprint), so the copper follows the parts.
Board frame of build_pcb.py (origin top-left, y down).

Layers: F.Cu parts, In1.Cu solid GND, In2.Cu +3V3 (VBUS only as an island in the bottom band), B.Cu the panel bus. In2 under
the B.Cu bus is one unbroken +3V3 pour: nothing but vias touches In2 here.

Structure:
  * J2 (panel FPC): every bus pin drops to B.Cu through a via in one of three columns (pin number mod 3, 0.95 mm apart, so the
    antipads on In1/In2 do not merge into a slot). LCD_CS/SCL/SDA and the first LCD_RST pin stay on F.Cu (the "init fan").
  * Init fan (F.Cu): J2 pins 11/10/9/6 north along x 10-10.9, east over J1's top (between H1 and J1's peg), down into U1
    pins 5-8 from the west. LCD_CS reaches its pull-up R10 by a short B.Cu hop under the fan.
  * B.Cu ribbon, in J2 order: the north group (LCD_RST from pin 38, I2C_SCL, I2C_SDA, TP_INT) across J1's top; the south block
    (R5-R1, G5-G0, HS, VS, DE, PCLK) under J1 between its shell pads, then fanned to 0.46 mm in the channel and run under the
    module, each line ending in a via with a short F.Cu stub to its pad (bottom row from above, left/right column sideways).
  * B1-B5 (J2 pins 17-21) go west under J2, north along the edge, east along the top band and under the module's top edge,
    down to vias left of their right-column pads. J2 pins 16 (B5) and 28 (R5) join pins 21 and 33 by F.Cu hooks under the
    housing.
  * USB: P joins A6-B6 by a diagonal in J1's row gap and leaves down the gap, hops under J1's bottom on B.Cu and enters D1
    pin 6 from below; N joins A7-B7 by a B.Cu crossover and enters D1 pin 4 from above; D1's pins 4-3 and 6-1 are linked
    under its body (KiCad has no internal link), pins 3/1 go on to U1 pins 13/14. VBUS reaches D1 pin 5 from the west.
  * EN and BL_PWM leave U1 pins 3/4 eastwards on F.Cu under the module (the only free side), cross the bottom row on B.Cu
    through gaps between the stubs, and run to TP5 / R11 on B.Cu below the module.
"""
import build_pcb as bp
F, B = 'F.Cu', 'B.Cu'
HS, SIG, PWR, SWN = 0.15, 0.15, 0.3, 0.5
TRACKS, VIAS = [], []
REQUESTS = []


CH = 0.25                                               # 45-degree cut of every right-angle corner


def chamfer(pts, c=CH):
    """Replace the interior right-angle corners of a polyline by 45-degree cuts (nested bus corners keep their pitch)."""
    out = [pts[0]]
    for a, q, b in zip(pts, pts[1:], pts[2:]):
        u, w = (q[0] - a[0], q[1] - a[1]), (b[0] - q[0], b[1] - q[1])
        lu, lw = (u[0] ** 2 + u[1] ** 2) ** 0.5, (w[0] ** 2 + w[1] ** 2) ** 0.5
        if abs(u[0] * w[0] + u[1] * w[1]) < 1e-6 * lu * lw:
            k = min(c, 0.45 * lu, 0.45 * lw)
            out += [(q[0] - u[0] / lu * k, q[1] - u[1] / lu * k), (q[0] + w[0] / lw * k, q[1] + w[1] / lw * k)]
        else:
            out.append(q)
    return out + [pts[-1]]


def t(net, layer, w, *pts):
    pts = [tuple(round(c, 4) for c in q) for q in pts]
    pts = [q for i, q in enumerate(pts) if i == 0 or q != pts[i - 1]]      # no zero-length segments
    if len(pts) > 2: pts = [tuple(round(c, 4) for c in q) for q in chamfer(pts)]
    TRACKS.append((net, layer, w, pts))
def v(net, *pos): VIAS.append((net, tuple(round(c, 4) for c in pos)))
def p(ref, num, i=0): return bp.pad(ref, num, i)
def j2(n): return p('J2', str(n))
def u1(n): return p('U1', str(n))


# ================================================================== J2: via columns, hooks, power pins, top-end parts
COLS = (7.3, 8.25, 9.2)                                 # pin n -> column n % 3: neighbours 1.07 mm apart, antipads separate
def jvia(n): return (COLS[n % 3], j2(n)[1])
def drop(net, n):
    """F.Cu stub from J2 pin n to its column via; returns the via."""
    q = jvia(n); t(net, F, SIG, j2(n), q); v(net, *q); return q

drop('GND', 34)
HOOK = 5.25                                             # under the housing, 0.35 mm west of the pad ends
for net, a, b in (('LCD_B5', 16, 21), ('LCD_R5', 28, 33)):
    t(net, F, SIG, j2(a), (HOOK, j2(a)[1]), (HOOK, j2(b)[1]), j2(b))
for n in (4, 40):                                       # GND pins: via west of the pad, under the housing
    t('GND', F, 0.2, j2(n), (5.1, j2(n)[1])); v('GND', 5.1, j2(n)[1])
# pin 39 (TP_VCC): column via + C15/C14; C15/C14 GND and the I2C pull-up supply get their own vias below the B1-B5 band
V39 = drop('+3V3', 39)
C15V, C15G, C14V, C14G = p('C15', '1'), p('C15', '2'), p('C14', '1'), p('C14', '2')
t('+3V3', F, 0.25, V39, (C15V[0] - 0.675, C15V[1]), C15V, C14V)
t('GND', F, 0.25, C14G, C15G, (C15G[0], 11.75)); v('GND', C15G[0], 11.75)
R3V, R4V = p('R3', '1'), p('R4', '1')
t('+3V3', F, 0.25, R3V, R4V, (R4V[0], 11.75)); v('+3V3', R4V[0], 11.75)
R9R, R9G = p('R9', '1'), p('R9', '2')
t('GND', F, 0.25, R9G, (R9G[0], 11.75)); v('GND', R9G[0], 11.75)
RST_R9 = (R9R[0], j2(38)[1])                            # R9 (RST pull-down) lands on the pin-38 RST lane by a via
t('LCD_RST', F, SIG, R9R, RST_R9); v('LCD_RST', *RST_R9)
# I2C pull-ups from the column vias of pins 37 / 36 (F.Cu, north of the init fan)
SCLV, SDAV = jvia(37), jvia(36)
R4S, R3S = p('R4', '2'), p('R3', '2')
t('I2C_SCL', F, SIG, SCLV, (R4S[0], SCLV[1]), R4S)
SDX = 14.1                                              # between R4/R3 and R9
t('I2C_SDA', F, SIG, SDAV, (SDX, SDAV[1]), (SDX, R3S[1]), R3S)

# ================================================================== init fan (F.Cu): CS / SCL / SDA / RST -> U1 pins 5-8
# (net, J2 pin, U1 pin, vertical x, top-band y, x where the 45-degree drop to the pin row starts)
INIT = [('LCD_CS', 11, 5, 10.0, 13.6, 22.95), ('LCD_SCL', 10, 6, 10.3, 13.9, 22.8),
        ('LCD_SDA', 9, 7, 10.6, 14.2, 22.65), ('LCD_RST', 6, 8, 10.9, 14.5, 22.5)]
for net, n, pin, x, y, xd in INIT:
    a, e = j2(n), u1(pin)
    t(net, F, SIG, a, (x, a[1]), (x, y), (xd, y), (xd + (e[1] - y), e[1]), e)
# LCD_CS pull-up R10 sits south of the fan: a B.Cu hop from the CS line under SCL/SDA/RST
CSV1 = (9.55, j2(11)[1]); R10C = p('R10', '2'); CSV2 = (R10C[0], 28.6)
v('LCD_CS', *CSV1); v('LCD_CS', *CSV2)
t('LCD_CS', B, SIG, CSV1, (CSV1[0] + (CSV2[1] - CSV1[1]), CSV2[1]), CSV2)
t('LCD_CS', F, SIG, CSV2, R10C)

# ================================================================== B.Cu ribbon: J2 -> J1 -> channel -> under U1
XS = 10.5                                               # J2 side: lanes leave the columns, then converge to J1's pitch
XE = 28.9                                               # channel: every south-block lane is on its module lane from here
# north group: (net, J2 pin, y over J1's top, y under the module, x where the channel drop starts)
NORTH = [('LCD_RST', 38, 13.45, 14.25, 23.95), ('I2C_SCL', 37, 13.75, 14.75, 23.8),
         ('I2C_SDA', 36, 14.05, 15.05, 23.65), ('TP_INT', 35, 14.35, 15.35, 23.5)]
XN = 15.0                                               # north group: converge east of R9's via
NEND = {}
for net, n, yj, ym, xd in NORTH:
    q = drop(net, n)
    NEND[net] = [q, (XN, q[1]), (XN + (yj - q[1]), yj), (xd, yj), (xd + (ym - yj), ym)]
# LCD_RST (pin 38): via left of U1 pin 8, F.Cu down into the pad (east side; the init fan's RST enters from the west)
RSTV = (29.7, 14.25)
t('LCD_RST', B, SIG, *NEND['LCD_RST'], RSTV); v('LCD_RST', *RSTV)
e = u1(8); t('LCD_RST', F, SIG, RSTV, (RSTV[0], e[1] - 0.48), (RSTV[0] - 0.48, e[1]), e)
# I2C: under the module above the exposed pad, to vias over their bottom-row pads, F.Cu straight down
# (I2C_SDA's via drops 0.45 below its lane: I2C_SCL runs on past it to pin 25)
for net, pin, dy in (('I2C_SCL', 25, 0.0), ('I2C_SDA', 24, 0.45)):
    e = u1(pin); a = NEND[net][-1]; q = (e[0], a[1] + dy)
    t(net, B, SIG, *NEND[net], (q[0] - dy, a[1]), q); v(net, *q); t(net, F, SIG, q, e)
# TP_INT: drops 0.2 to its via so that I2C_SDA keeps 0.5 mm, F.Cu down east of the RST stub into pin 9
TPV = (30.4, 15.55); a = NEND['TP_INT'][-1]
t('TP_INT', B, SIG, *NEND['TP_INT'], (TPV[0] - (TPV[1] - a[1]), a[1]), TPV); v('TP_INT', *TPV)
e = u1(9); t('TP_INT', F, SIG, TPV, (TPV[0], e[1] - 0.55), (TPV[0] - 0.55, e[1]), e)

# south block: (net, J2 pin), in J2 order; J1 y: 11 lanes north of the USB_N crossover, 4 south of it
SOUTH = [('LCD_R5', 33), ('LCD_R4', 32), ('LCD_R3', 31), ('LCD_R2', 30), ('LCD_R1', 29), ('LCD_G5', 27), ('LCD_G4', 26),
         ('LCD_G3', 25), ('LCD_G2', 24), ('LCD_G1', 23), ('LCD_G0', 22), ('LCD_HS', 15), ('LCD_VS', 14), ('LCD_DE', 13),
         ('LCD_PCLK', 12)]
YM0, PM = 19.75, 0.46                                   # module lanes: R5 just below the exposed pad's vias, 0.46 pitch
SEND = {}
for k, (net, n) in enumerate(SOUTH):
    q = drop(net, n)
    yj = 17.95 + 0.3 * k if k < 11 else 22.0 + 0.3 * (k - 11)
    ym = YM0 + PM * k
    d = abs(yj - q[1])
    SEND[net] = [q, (XS, q[1]), (XS + d, yj), (XE - (ym - yj), yj), (XE, ym)]
def bottom(net, pin):
    """Lane to a via above its bottom-row pad, F.Cu stub straight down."""
    e = u1(pin); q = (e[0], SEND[net][-1][1]); t(net, B, SIG, *SEND[net], q); v(net, *q); t(net, F, SIG, q, e)
for net, pin in (('LCD_R5', 22), ('LCD_R4', 21), ('LCD_R3', 20), ('LCD_R2', 19), ('LCD_R1', 18), ('LCD_G0', 23),
                 ('LCD_VS', 15), ('LCD_PCLK', 17)):
    bottom(net, pin)
# lane-end vias are kept >= 1.13 mm apart so their In1/In2 antipads (0.85) never merge into a slot under the bus
HSV = (31.75, SEND['LCD_HS'][-1][1]); e = u1(16)        # east of DE's climb, stub down then onto the pad
t('LCD_HS', B, SIG, *SEND['LCD_HS'], HSV); v('LCD_HS', *HSV)
t('LCD_HS', F, SIG, HSV, (HSV[0], 26.5), (e[0], 26.5 + (HSV[0] - e[0])), e)
# right column G5 / G4 (vias east of I2C_SCL's stub), G3 (bottom row, via dropped below G4's)
G5V = (43.3, SEND['LCD_G5'][-1][1]); e = u1(32)
t('LCD_G5', B, SIG, *SEND['LCD_G5'], G5V); v('LCD_G5', *G5V)
t('LCD_G5', F, SIG, G5V, (G5V[0], e[1] + 0.45), (G5V[0] + 0.45, e[1]), e)
G4V = (44.4, SEND['LCD_G4'][-1][1]); e = u1(31)
t('LCD_G4', B, SIG, *SEND['LCD_G4'], G4V); v('LCD_G4', *G4V)
t('LCD_G4', F, SIG, G4V, (G4V[0], e[1]), e)
e = u1(26); a = SEND['LCD_G3'][-1]; G3V = (e[0], 23.7)
t('LCD_G3', B, SIG, *SEND['LCD_G3'], (G3V[0] - (G3V[1] - a[1]), a[1]), G3V); v('LCD_G3', *G3V); t('LCD_G3', F, SIG, G3V, e)
# left column G2 / G1 / DE: vias just east of the pads; DE's stub climbs past the bottom-left vias
G2V = (29.45, SEND['LCD_G2'][-1][1]); e = u1(11)
t('LCD_G2', B, SIG, *SEND['LCD_G2'], G2V); v('LCD_G2', *G2V)
t('LCD_G2', F, SIG, G2V, (G2V[0] - (G2V[1] - e[1]), e[1]), e)
G1V = (30.5, SEND['LCD_G1'][-1][1]); e = u1(12)
t('LCD_G1', B, SIG, *SEND['LCD_G1'], G1V); v('LCD_G1', *G1V)
t('LCD_G1', F, SIG, G1V, (e[0] + 0.35, G1V[1]))
DEV = (31.05, SEND['LCD_DE'][-1][1]); e = u1(10)
t('LCD_DE', B, SIG, *SEND['LCD_DE'], DEV); v('LCD_DE', *DEV)
t('LCD_DE', F, SIG, DEV, (DEV[0], e[1] + 0.48), (DEV[0] - 0.48, e[1]), e)

# ================================================================== B1-B5: west under J2, top band, down to the right column
# (net, J2 pin, west x, top-band y, U1 pin, right x)
GRP = [('LCD_B1', 17, 2.4, 8.3, 33, 44.6), ('LCD_B2', 18, 2.75, 8.6, 34, 44.14), ('LCD_B3', 19, 3.1, 8.9, 35, 43.68),
       ('LCD_B4', 20, 3.45, 9.2, 38, 43.22), ('LCD_B5', 21, 3.8, 9.5, 39, 42.76)]
BX0, BDY = 26.6, 1.15                                   # top band -> under-module band (clear of the antenna corner)
for i, (net, n, wx, ty, pin, rx) in enumerate(GRP):
    q = drop(net, n); e = u1(pin); r = (rx, e[1])
    x0 = BX0 - 0.13 * i                                 # 67.5-degree stagger keeps 0.3 mm pitch on the diagonal
    t(net, B, SIG, q, (wx, q[1]), (wx, ty), (x0, ty), (x0 + BDY, ty + BDY), (rx, ty + BDY), r)
    v(net, *r); t(net, F, SIG, r, e)

# ================================================================== USB, CC, VBUS at J1 / D1
JA4, JA5, JA6, JA7, JA9 = (p('J1', n) for n in ('A4', 'A5', 'A6', 'A7', 'A9'))
JB4, JB5, JB6, JB7, JB9 = (p('J1', n) for n in ('B4', 'B5', 'B6', 'B7', 'B9'))
DP1, DG2, DN3, DN4, DV5, DP6 = (p('D1', str(i)) for i in range(1, 7))
# USB_P: A6-B6 diagonal in the row gap, down the gap, B.Cu under J1's bottom, up into D1 pin 6, link 6-1, on to U1 pin 14
PX = 20.1
t('USB_P', F, HS, JA6, (PX - 0.5, JA6[1]), (PX + 0.5, JB6[1]), JB6)
PV1, PV2 = (PX, 26.95), (DP6[0], 27.6625)
t('USB_P', F, HS, (PX, JA6[1] - 0.5), PV1); v('USB_P', *PV1)
t('USB_P', B, HS, PV1, (PX + 0.35, 27.3), (PV2[0] - 0.3625, 27.3), PV2); v('USB_P', *PV2)
t('USB_P', F, HS, PV2, DP6, DP1, (27.2, DP1[1]), (27.2 + (DP1[1] - u1(14)[1]), u1(14)[1]), u1(14))
# USB_N: A7 west to a via, B.Cu crossover under J1, via east of B7, down into D1 pin 4, link 4-3, on to U1 pin 13
NV1, NV2 = (17.35, JA6[1]), (22.85, JB7[1])
t('USB_N', F, HS, JA7, (NV1[0] + 0.25, JA7[1]), (NV1[0], JA7[1] + 0.25), NV1); v('USB_N', *NV1)
t('USB_N', B, HS, NV1, NV2); v('USB_N', *NV2)
t('USB_N', F, HS, JB7, NV2, (DN4[0], NV2[1] + (DN4[0] - NV2[0])), DN4, DN3,
  (27.18, DN3[1]), (27.18 + (u1(13)[1] - DN3[1]), u1(13)[1]), u1(13))
DGV = (27.05, DG2[1]); t('GND', F, 0.25, DG2, DGV); v('GND', *DGV)
# CC pull-downs
R5C, R5G, R6C, R6G = p('R5', '1'), p('R5', '2'), p('R6', '1'), p('R6', '2')
t('CC1', F, SIG, JA5, (R5C[0], JA5[1]))
t('CC2', F, SIG, JB5, (R6C[0] - (R6C[1] - JB5[1]), JB5[1]), R6C)
t('GND', F, 0.25, R5G, (R5G[0], 24.95)); v('GND', R5G[0], 24.95)
t('GND', F, 0.25, R6G, (R6G[0], 21.475)); v('GND', R6G[0], 21.475)     # between the bus's two groups
# VBUS: A9-B4 across the row gap; A9 and A4 west to a trunk at x 15.3 (A4 between R5's pads), down to the In2 island;
# B9 east and down x 22.65 past D1 pin 5 to the island. In2 under J1 stays +3V3.
TX_ = 15.3
t('VBUS', F, 0.4, JA9, JB4)
t('VBUS', F, 0.4, JA9, (TX_, JA9[1]), (TX_, 28.0), (17.3, 30.0), (17.3, 34.5)); v('VBUS', 17.3, 34.5)   # 1.17 from BL_EN's via
t('VBUS', F, 0.25, JA4, (17.6, JA4[1]), (17.26, 23.16), (TX_, 23.16))
VX = 22.65
t('VBUS', F, 0.4, JB9, (VX, JB9[1]), (VX, 33.6)); v('VBUS', VX, 33.6)
t('VBUS', F, 0.3, (VX, DV5[1]), DV5)

# ================================================================== U1 supply, EN, BL_PWM, GND pins
C1V, C2V, C3E, R1E, R1V = p('C1', '1'), p('C2', '1'), p('C3', '1'), p('R1', '2'), p('R1', '1')
t('+3V3', F, PWR, u1(2), C2V, C1V); t('+3V3', F, PWR, C2V, (C2V[0], 12.15)); v('+3V3', C2V[0], 12.15)
t('GND', F, 0.25, p('C3', '2'), p('C1', '2'), p('C2', '2'), (p('C2', '2')[0], 12.15)); v('GND', p('C2', '2')[0], 12.15)
t('+3V3', F, 0.25, R1V, (27.2, R1V[1])); v('+3V3', 27.2, R1V[1])
g = u1(1); t('GND', F, PWR, g, (29.0, g[1]), (29.75, g[1] + 0.75), (29.75, 11.9)); v('GND', 29.75, 11.9)
g = u1(40); t('GND', F, PWR, g, (47.0, g[1])); v('GND', 47.0, g[1])
# EN: R1 / C3 -> B.Cu under the antenna-side corner -> U1 pin 3's line; pin 3 east under the module, B.Cu under the bottom
# row through the R5/G0 gap, to TP5
ENV1, ENV2, ENX = (27.25, C3E[1]), (30.4, 8.95), 39.54
t('EN', F, SIG, R1E, C3E, ENV1); v('EN', *ENV1)
t('EN', B, SIG, ENV1, (ENV1[0] + (ENV2[1] - ENV1[1]), ENV2[1]), ENV2); v('EN', *ENV2)
t('EN', F, SIG, ENV2, (ENV2[0], u1(3)[1]))
ENV3, ENV4, TP5 = (ENX, 26.6), (36.2, 37.4), p('TP5', '1')
t('EN', F, SIG, u1(3), (ENX, u1(3)[1]), ENV3); v('EN', *ENV3)
t('EN', B, SIG, ENV3, (ENX, ENV4[1] - (ENX - ENV4[0])), ENV4); v('EN', *ENV4)
t('EN', F, SIG, ENV4, (TP5[0], ENV4[1] + (ENV4[0] - TP5[0])), TP5)
# BL_PWM: pin 4 east under the module, down through the PCLK/R1 gap, B.Cu west under J1's bottom (north of H2), F.Cu to R11
BPX, R11P = 33.19, p('R11', '1')
BPV1, BPV2 = (BPX, 25.2), (14.6, 28.4)                 # BPV1 1.18 mm from PCLK's via: separate antipads
t('BL_PWM', F, SIG, u1(4), (29.2, u1(4)[1]), (29.5, u1(4)[1] - 0.3), (BPX, u1(4)[1] - 0.3), BPV1); v('BL_PWM', *BPV1)
t('BL_PWM', B, SIG, BPV1, (BPX, 27.4), (BPX - (BPV2[1] - 27.4), BPV2[1]), BPV2); v('BL_PWM', *BPV2)
t('BL_PWM', F, SIG, BPV2, (BPV2[0], R11P[1]))

# ================================================================== UART pads, BOOT
TP1, TP2 = p('TP1', '1'), p('TP2', '1')
TXX, RXX = 47.3, 46.85
t('TXD0', F, SIG, u1(37), (TXX, u1(37)[1]), (TXX, TP1[1] - (TXX - TP1[0])), TP1)
t('RXD0', F, SIG, u1(36), (RXX, u1(36)[1]), (RXX, TP2[1] - (RXX - TP2[0])), TP2)
sw2, r2b, b27 = p('SW1', '2'), p('R2', '2'), u1(27)
t('BOOT', F, SIG, b27, (b27[0], 29.5), (b27[0] - 1.0, 30.5), (sw2[0] + 0.5, 30.5), (sw2[0], 31.0), sw2, r2b)
v('+3V3', *p('TP4', '1')); v('GND', *p('TP3', '1'))   # test pads: plane vias in the pads

# ================================================================== U2 (AMS1117): output to the tab, tab vias, caps, input
vo, tab, vin = p('U2', '2'), p('U2', '2', 1), p('U2', '3')
t('+3V3', F, 0.5, vo, tab)
TVX, TVY = 27.3, (35.7, 36.9, 38.1, 39.3)               # tab strap with four vias into the In2 +3V3 pour
t('+3V3', F, 0.5, tab, (TVX, tab[1])); t('+3V3', F, 0.5, (TVX, TVY[0]), (TVX, TVY[-1]))
for y in TVY: v('+3V3', TVX, y)
C5o, C6o = p('C5', '1'), p('C6', '1')
t('+3V3', F, 0.4, (TVX, C5o[1]), C5o, (C6o[0], C5o[1]))
C4v = p('C4', '1'); t('VBUS', F, 0.4, vin, (18.1, vin[1]), (C4v[0] + 0.55, C4v[1]), C4v)

# ================================================================== AP3032 boost: SW node, loop, LED_A / LED_K / BL_EN
L1V, L1S, D2K, D2A = p('L1', '1'), p('L1', '2'), p('D2', '1'), p('D2', '2')
U3 = {i: p('U3', str(i)) for i in range(1, 7)}
C7V, C7G, C8A, C8G, C9A, C9G = p('C7', '1'), p('C7', '2'), p('C8', '1'), p('C8', '2'), p('C9', '1'), p('C9', '2')
t('BL_SW', F, SWN, L1S, D2A)
t('BL_SW', F, SWN, (U3[1][0], D2A[1]), U3[1])            # anode straight up into SW: the node stays 3 mm long
t('VBUS', F, 0.4, L1V, (L1V[0], 37.4), (C7V[0], C7V[1]), (5.6, C7V[1]), (5.6, U3[6][1]), U3[6])
for pad_, via in ((U3[2], (U3[2][0], 37.7)), (C8G, (C8G[0], 36.95)), (C7G, (C7G[0], 33.6)), (C9G, (16.35, C9G[1]))):
    t('GND', F, PWR, pad_, via); v('GND', *via)
# LED_K: J2 pins 2/3 between C13 and C12, R8 (sense), down west of R7/C8 into U3 FB from below
k2, k3, R8K = j2(2), j2(3), p('R8', '1')
KX, KY = 11.1, 30.4
t('LED_K', F, 0.2, k3, (7.05, k3[1]), (7.05, k2[1]))
t('LED_K', F, 0.2, k2, (7.25, k2[1]), (7.4, KY), (KX, KY))                 # split at the R8 branch: a real junction
t('LED_K', F, 0.2, (KX, KY), (KX, 37.65), (U3[3][0], 37.65), U3[3])
t('LED_K', F, 0.2, (KX, KY), (R8K[0], KY), R8K)
# LED_A: J2 pin 1 -> U3 OV from above; B.Cu hop under U3 / D2 to D2's cathode, C8 and C9
a1 = j2(1); LAX = 7.1; LAV1, LAV2 = (LAX, 33.3), (14.0, 37.7)
t('LED_A', F, 0.25, a1, (a1[0] + 0.6, a1[1]), (LAX, a1[1] + 0.3), LAV1); v('LED_A', *LAV1)
t('LED_A', F, 0.25, (LAX, 32.7), (8.55, 32.7), (U3[5][0], 33.15), U3[5])
t('LED_A', B, 0.25, LAV1, (LAX, 38.6), (13.1, 38.6), LAV2); v('LED_A', *LAV2)
t('LED_A', F, 0.3, LAV2, (C8A[0], LAV2[1] - 0.15), C8A, (14.85, C8A[1]), (C9A[0] - 0.125, C9A[1]), C9A)
t('LED_A', F, 0.3, LAV2, (13.4, 38.3), (D2K[0] + 0.45, D2K[1]), D2K)
# BL_EN (CTRL): U3 pin 4 -> B.Cu east under R7 / C8 -> R7 (pull-down) and R11 (series from BL_PWM)
R7E, R11E = p('R7', '1'), p('R11', '2')
EV1, EV2, EV3 = (U3[4][0], 33.1), (R7E[0], 34.05), (R11E[0], 33.725)
t('BL_EN', F, SIG, U3[4], EV1); v('BL_EN', *EV1)
t('BL_EN', B, SIG, EV1, (EV1[0] + (EV2[1] - EV1[1]), EV2[1]), (EV3[0] - (EV2[1] - EV3[1]), EV2[1]), EV3)
v('BL_EN', *EV2); v('BL_EN', *EV3)
t('BL_EN', F, SIG, EV2, R7E); t('BL_EN', F, SIG, EV3, R11E)
# sense / pull-down GND, local decoupling of the panel supply pins
R8G, R7G = p('R8', '2'), p('R7', '2')
t('GND', F, 0.25, R7G, R8G, (14.05, R8G[1])); v('GND', 14.05, R8G[1])
C13V, C13G, C12V, C12G = p('C13', '1'), p('C13', '2'), p('C12', '1'), p('C12', '2')
t('GND', F, 0.25, C13G, (C13G[0], 28.75)); v('GND', C13G[0], 28.75)
t('GND', F, 0.25, C12G, (C12G[0], 32.15)); v('GND', C12G[0], 32.15)
v5 = j2(5); V5V = (7.6, v5[1])
t('+3V3', F, 0.25, v5, V5V, (C13V[0] - 0.375, C13V[1]), C13V); v('+3V3', *V5V)
t('+3V3', F, 0.25, C12V, (C12V[0], 32.15)); v('+3V3', C12V[0], 32.15)

# ================================================================== plane vias the engine's 1.4 mm search cannot place
for net, pad_, via in (('GND', p('C4', '2'), (15.8, 38.25)), ('VBUS', p('C4', '1'), (15.8, 40.15)),
                       ('GND', p('C5', '2'), (29.2, 35.2)), ('GND', p('C6', '2'), (31.1, 35.4)),
                       ('GND', p('J2', 'S1', 0), (1.6, p('J2', 'S1', 0)[1])), ('GND', p('J2', 'S1', 1), (1.6, p('J2', 'S1', 1)[1])),
                       ('GND', p('SW1', '1'), (45.85, 33.0)), ('GND', p('U2', '1'), (21.1, 34.9)),
                       ('VBUS', p('L1', '1'), (2.2, p('L1', '1')[1])), ('+3V3', p('R2', '1'), (35.3, 33.0)),
                       ('+3V3', p('R10', '1'), (11.775, 28.75))):
    t(net, F, 0.3 if net != '+3V3' else 0.25, pad_, via); v(net, *via)
