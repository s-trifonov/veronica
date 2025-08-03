import math

from config.ver_cfg import Config

#=================================
def dist(p0, p1):
    return length(p1[0] - p0[0], p1[1] - p0[1])

#=================================
def length(dx, dy):
    return math.sqrt(dx*dx + dy*dy)

#=================================
def norm(dx, dy):
    return dx*dx + dy*dy

#=================================
def linePoint(p0, p1, c):
    return (c * p1[0] + (1 - c) * p0[0],
        c * p1[1] + (1 - c) * p0[1])

#=================================
def shiftPoint(p0, dd, sign=1):
    return [p0[j] + sign * dd[j] for j in (0, 1)]

#=================================
def delta(p0, p1):
    return (p1[0] - p0[0], p1[1] - p0[1])

#=================================
def smult(p0, p1):
    return (p0[0] * p1[0]) + (p0[1] * p1[1])

#=================================
def xmult(p0, p1):
    return (p0[0] * p1[1]) - (p0[1] * p1[0])

#=================================
def locateDistToLine(pp, pl1, pl2):
    dp = delta(pl1, pl2)
    m1 = smult(delta(pl1, pp), dp)
    if m1 <= Config.TOO_SMALL:
        return dist(pp, pl1), 0

    m2 = - smult(delta(pl2, pp), dp)
    if m2 <= Config.TOO_SMALL:
        return dist(pp, pl2), 1

    c = float(m1) / (m1 + m2)
    return dist(pp, linePoint(pl1, pl2, c)), c

def distToLine(pp, pl1, pl2):
    return locateDistToLine(pp, pl1, pl2)[0]

#=================================
def locateDistToPoly(pp, poly, is_closed):
    variants = []
    idx_last = len(poly) - 1
    for idx, pl1 in enumerate(poly):
        if idx == idx_last:
            if not is_closed:
                break
            pl2 = poly[0]
        else:
            pl2 = poly[idx + 1]
        dd, cc = locateDistToLine(pp, pl1, pl2)
        if cc + Config.TOO_SMALL >= 1.:
            cc = 1 - Config.TOO_SMALL
        variants.append((dd, cc + idx))
    return min(variants)

def distToPoly(pp, poly, is_closed=False):
    return locateDistToPoly(pp, poly, is_closed)[0]

#=================================
def polyDiameter(poly):
    if len(poly) < 2:
        return 0
    return max(max(dist(poly[i], poly[j]) for i in range(j))
        for j in range(1, len(poly)))

#=================================
def polyCenter(poly):
    ret = []
    for j in (0, 1):
        min_z = min(pp[j] for pp in poly)
        max_z = max(pp[j] for pp in poly)
        ret.append(int((min_z + max_z)/2))
    return ret

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

#=================================
def splineToPoly(path_points, closed):
    assert len(path_points) > 2
    ret = []
    if closed:
        assert len(path_points) % 3 == 0
    else:
        assert len(path_points) % 3 == 1
    for idx in range(0, len(path_points), 3):
        pp = path_points[idx:idx+4]
        if len(pp) == 1:
            break
        elif len(pp)< 4:
            pp.append(path_points[0])
        ret += splinePoints(pp)
    if closed:
        del ret[-1]
    return ret

#=================================
def splitOrtho(base_vec, vec):
    l0 = length(*base_vec)
    norm_base = [base_vec[0]/l0, base_vec[1]/l0]
    mm = smult(norm_base, vec)
    vec1 = [norm_base[0] * mm, norm_base[1] * mm]
    return vec1, delta(vec1, vec)

#=================================
def mapOrtho(base_vec, vec):
    l0 = length(*base_vec)
    base_ortho = [base_vec[1], -base_vec[0]]
    return (smult(base_vec, vec)/l0, smult(base_ortho, vec)/l0)

#=================================
def lineFormula(p0, p1):
    vec = delta(p0, p1)
    l0 = length(*vec)
    if l0 < Config.PATCH_MIN_DIST:
        return None
    normal = [vec[1]/l0, -vec[0]/l0]
    if normal[0] < 0:
        normal = [-v for v in normal]
    return [normal[0], normal[1], -smult(normal, p0)]

#=================================
def mapPoint(mm, pp):
    return [
        round(mm[0][0] * pp[0] + mm[0][1] * pp[1] + mm[0][2]),
        round(mm[1][0] * pp[0] + mm[1][1] * pp[1] + mm[1][2])]


#=================================
def area(points):
    res = 0
    d1 = delta(points[0], points[1])
    for idx in range(2, len(points)):
        dd = delta(points[0], points[idx])
        res += xmult(d1, dd)
        d1 = dd
    return res / 2

#=================================
def polyEffectiveDiameter(poly):
    if len(poly) < 2:
        return 0
    p_area = abs(area(poly))
    return 2 * math.sqrt(p_area/3.14)

#=================================
sDEBUG_SEGMENTS = None
def _clearDebug():
    global sDEBUG_SEGMENTS
    sDEBUG_SEGMENTS = None

def setDebugSegments(segments):
    global sDEBUG_SEGMENTS
    sDEBUG_SEGMENTS = [points[:] for points in segments]
