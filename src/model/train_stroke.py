from random import Random
from config.ver_cfg import Config
import tools.geom as geom
from .v_types import VType

#=================================
class TrainStrokePack:
    def __init__(self, env, img_h, width, height, markup_seq, seed = 179):
        self.mImgH = img_h
        self.mMarkupSeq = markup_seq
        self.mRH = Random(seed)

        bound_dist = Config.STROKE_WIDTH * 2
        self.mCorrectRegion = (bound_dist, bound_dist,
            width - bound_dist, height - bound_dist)

        strokes = []
        env.startProgress(Config.TRAIN_PACK_SIZE)
        for _ in range(Config.TRAIN_PACK_SIZE):
            strokes.append(self._makeOne())
            env.stepProgress()
        env.endProgress()

        self.mResult = {
            "seed": seed,
            "total": len(strokes),
            "strokes": strokes
        }

    def getResult(self):
        return self.mResult

    def _makeOne(self):
        x1, y1, x2, y2 = self.mCorrectRegion
        while (True):
            pp1 = (self.mRH.randint(int(x1), int(x2)),
                self.mRH.randint(int(y1), int(y2)))
            pp2 = (self.mRH.randint(int(x1), int(x2)),
                self.mRH.randint(int(y1), int(y2)))
            if geom.length(*geom.delta(pp1, pp2)) > 64:
                return self._analyzeStroke(pp1, pp2)

    def _analyzeStroke(self, pp1, pp2):
        if pp1[0] > pp2[0]:
            pp1, pp2 = pp2, pp1
        dd = geom.delta(pp1, pp2)
        ll = geom.length(*dd)
        aa, bb = dd[1] / ll, -dd[0] / ll
        cc = aa * pp1[0] + bb * pp1[1]
        criterium = lambda pp: aa * pp[0] + bb * pp[1] - cc

        z1, z2 = -bb, aa
        z0 = z1 * pp1[0] + z2 * pp1[1]
        map_z = lambda pp: z1 * pp[0] + z2 * pp[1] - z0
        assert abs(map_z(pp1)) < 1E-5
        assert abs(map_z(pp2) - ll) < 1E-5

        selection = []
        for ptype, points in self.mMarkupSeq:
            tp_descr = VType.getTypeDescr(ptype)
            if tp_descr.isAreaType():
                #TRF: not now
                continue
            if tp_descr.getGeomType() == "spline":
                points = geom.splineToPoly(points, tp_descr.isClosed())
            selection += self._locateIntersections(points,
                criterium, map_z, ll, tp_descr.getReducedType())
        selection.sort()
        return {
            "points": [list(pp1), list(pp2)],
            "intersections": selection}

    def _locateIntersections(self, points, criterium, map_z, ll, rtype):
        res = []
        cr_prev = criterium(points[0])
        idx = 0
        while idx < len(points):
            cr = criterium(points[idx])
            if cr * cr_prev <= 0:
                zz, tt = self._evalIntersection(cr_prev, cr,
                    map_z(points[idx-1]), map_z(points[idx]))
                if 0 <= zz <= ll:
                    res.append([int(zz), tt, rtype])
            cr_prev = cr
            idx += 1
        return res

    @staticmethod
    def _evalIntersection(c0, c1, z0, z1):
        assert c0 * c1 <= 0
        dc = abs(c1 - c0)
        dz = z1 - z0
        v0 = abs(c0) / (dc + 1E-5)
        zz = z0 * v0 + z1 * (1 - v0)
        if abs(dz) < 10 * dc:
            tt = dz / dc
        else:
            tt = 1000 if dz > 0 else -1000
        if c0 < 0:
            tt = -tt
        return (zz, tt)
#=================================
