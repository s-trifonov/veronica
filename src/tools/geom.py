import math

from config.ver_cfg import Config

#=================================
def dist(p0, p1):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    return math.sqrt(dx*dx + dy*dy)

#=================================
def linePoint(p0, p1, c):
    return (c * p1[0] + (1 - c) * p0[0],
        c * p1[1] + (1 - c) * p0[1])

#=================================
def delta(p0, p1):
    return (p1[0] - p0[0], p1[1] - p0[1])

#=================================
def smult(p0, p1):
    return (p0[0] * p1[0]) + (p0[1] * p1[1])

#=================================
def locateDistToLine(pp, pl1, pl2):
    m1 = smult(delta(pl1, pp), delta(pl1, pl2))
    if m1 <= Config.TOO_SMALL:
        return dist(pp, pl1), 0

    m2 = smult(delta(pl2, pp), delta(pl2, pl1))
    if m2 <= Config.TOO_SMALL:
        return dist(pp, pl1), 1

    c = float(m1) / (m1 + m2)
    return dist(pp, linePoint(pl1, pl2, c)), c

#=================================
def distToLine(pp, pl1, pl2):
    return locateDistToLine(pp, pl1, pl2)[0]

#=================================
def locateDistToPoly(pp, poly):
    variants = []
    for idx, pl2 in enumerate(poly[1:]):
        pl1 = poly[idx]
        dd, cc = locateDistToLine(pp, pl1, pl2)
        variants.append((dd, cc + idx))
    return min(variants)

#=================================
def checkCorrectPath(points, closed_mode, check_self_intersect=True):
    for idx, pl1 in enumerate(points):
        for pl2 in points[idx + 1:]:
            if dist(pl1, pl2) < Config.MIN_DIST:
                return False
    #TRF: add check self intersection
    return True

#=================================
def addVecWithCoeff(pp, dd, c):
    return ((pp[0] + c * dd[0]), (pp[1] + c * dd[1]))

#=================================
def splinePoint(points, c):
    u, v = c, 1-c
    u2 = u * u
    v2 = v * v
    cc = [v * v2, 3 * v2 * u, 3 * v * u2, u2 * u]
    return [sum(cc[j] * points[j][i] for j in range(4))
        for i in range(2)]

def splinePoints(points):
    assert len(points) == 4
    ll = sum(dist(points[i + 1], points[i]) for i in range(3))
    count = round((ll + Config.SPLINE_VIS_SEG)/Config.SPLINE_VIS_SEG)
    dt = 1./count
    return [splinePoint(points, i * dt) for i in range(0, count + 1)]
