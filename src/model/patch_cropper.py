import math
from config.ver_cfg import Config
import tools.geom as geom
from .cropper import Cropper

#=================================
class PatchCropper(Cropper):
    sLocCenter = [Config.PATCH_HALF_SIZE, Config.PATCH_HALF_SIZE]
    sBounds = (Config.PATCH_SIZE, Config.PATCH_SIZE)
    sMinBoundDist = int(Config.PATCH_HALF_SIZE * math.sqrt(2)) + 1

    def __init__(self, center, angle):
        Cropper.__init__(self, center, angle, self.sBounds, self.sLocCenter)
        self.mCenter = center

    @classmethod
    def checkIfCenterCorrect(cls, width, height, point):
        return (
            point[0] - cls.sMinBoundDist >= 0 and
            point[0] + cls.sMinBoundDist < width and
            point[1] - cls.sMinBoundDist >= 0 and
            point[1] + cls.sMinBoundDist < height)

    @classmethod
    def fullCorrectRegion(cls, width, height):
        return (cls.sMinBoundDist, cls.sMinBoundDist,
            width - 2 * cls.sMinBoundDist,
            height - 2 * cls.sMinBoundDist)

    def getCenter(self):
        return self.mCenter

    def getParams(self):
        return f"{self.mCenter}/{self.mAngle}"

    def toJSon(self):
        return {
            "loc-center": list(self.mCenter),
            "loc-angle": self.mAngle
        }

    #=================================
    def _pointNearBoundary(self, pp):
        for dim in (0, 1):
            if (abs(pp[dim]) <= Config.PATCH_MIN_DIST or
                    abs(pp[dim] - Config.PATCH_SIZE) <=
                    Config.PATCH_MIN_DIST):
                return True
        return False

    ## use local points
    def adaptChunk(self, points):
        bounds = [[
            min(pp[dim] for pp in points),
            max(pp[dim] for pp in points)]
            for dim in (0, 1)]
        small_count = 0
        for dim in (0, 1):
            if bounds[1-dim][0] + Config.PATCH_MIN_DIST < bounds[1-dim][1]:
                continue
            small_count += 1
            if bounds[dim][0] - Config.PATCH_MIN_DIST <= 0:
                return None
            if bounds[dim][1] + Config.PATCH_MIN_DIST >= Config.PATCH_SIZE:
                return None
        if small_count > 1:
            return None
        ret = [points[0], points[-1]]
        if geom.length(*geom.delta(*ret)) < Config.PATCH_MIN_DIST:
            return None
        if (all(self._pointNearBoundary(pp) for pp in ret)):
            return ret
        return None

    #=================================
    sDimCritSeq = [
        (1, lambda p: p[0]),
        (1, lambda p: Config.PATCH_SIZE - p[0]),
        (0, lambda p: p[1]),
        (0, lambda p: Config.PATCH_SIZE - p[1])]

    #=================================
    def cutCurve(self, points, closed):
        assert len(points) > 2
        if closed and points[-1] != points[0]:
            points = points[:] + [points[0]]
        res = [self.mapPointsToLocal(points)]
        for _, crit in self.sDimCritSeq:
            res1 = []
            for points in res:
                res1 += self._cutPoly(points, crit, False)
            if len(res1) == 0:
                return None
            res[:] = res1
            if closed:
                self.__joinCircled(res)
        return res

    #=================================
    def cropArea(self, points):
        assert len(points) > 2
        if points[-1] != points[0]:
            points = points[:] + [points[0]]
        result = [self.mapPointsToLocal(points)]
        for dim_join, crit in self.sDimCritSeq:
            self._cutArea(result, crit, dim_join)
            if len(result) == 0:
                return result
        #geom.setDebugSegments(self.mapPointsToGlobal(points)
        #    for points in result)
        return result

    #=================================
    def measureArea(self, segments):
        res = sum(geom.area(points) for points in segments)
        return abs(res) / Config.PATCH_SIZE / Config.PATCH_SIZE / 2

    #=================================
    sDimCritBoundsSeq = [
        (1, 0, lambda p: Config.PATCH_MIN_DIST - p[0]),
        (1, 1, lambda p: p[0] + Config.PATCH_MIN_DIST - Config.PATCH_SIZE),
        (0, 0, lambda p: Config.PATCH_MIN_DIST - p[1]),
        (0, 1, lambda p: p[1] + Config.PATCH_MIN_DIST - Config.PATCH_SIZE)]

    #=================================
    def boundsOfArea(self, segments):
        ret = []
        for dim_join, q_upper, crit in self.sDimCritBoundsSeq:
            seq = segments[:]
            self._cutArea(seq, crit, dim_join)
            for points in seq:
                pp1 = [0, 0]
                pp1[1 - dim_join] = q_upper * Config.PATCH_SIZE
                pp2 = pp1[:]
                pp1[dim_join] = min(p[dim_join] for p in points)
                pp2[dim_join] = max(p[dim_join] for p in points)
                ret.append([pp1, pp2])
        return ret

    #=================================
    def boundsOfPoly(self, segments):
        ret = []
        for dim_join, q_upper, crit in self.sDimCritBoundsSeq:
            seq = []
            for points in segments:
                seq += self._cutPoly(points, crit, False)
            zz = q_upper * Config.PATCH_SIZE
            for ch in seq:
                pp0, pp1 = list(ch[0]), list(ch[-1])
                if abs(pp0[1 - dim_join] - zz) > 1:
                    pp0, pp1 = pp1, pp0
                if (min(pp0[dim_join], pp1[dim_join]) <=
                        Config.PATCH_LONG_CROSS):
                    continue
                if (max(pp0[dim_join], pp1[dim_join]) >=
                        Config.PATCH_SIZE - Config.PATCH_LONG_CROSS):
                    continue
                if (abs(pp0[1 - dim_join] - zz) >=
                        Config.PATCH_TOO_SHORT_CROSS or
                        abs(pp0[dim_join] - pp1[dim_join]) >=
                        Config.PATCH_LONG_CROSS):
                    pp0[1 - dim_join] = zz
                    ret.append([pp0, 1000])
                    continue
                pp0[1 - dim_join] = zz
                dd = geom.delta(pp0, pp1)
                if geom.length(*dd) <= Config.PATCH_TOO_SHORT_CROSS:
                    ret.append([pp0, -1000])
                    continue
                base = [0, 0]
                base[1 - dim_join] = -1 if q_upper else 1
                c0, c1 = geom.mapOrtho(base, dd)
                assert  c0 > 0 and abs(c1) < 10 * c0
                ret.append([pp0, (1 - 2 * dim_join) * c1 / c0])
        return ret

    #=================================
    @classmethod
    def __signSeg(cls, points, dim_join):
        return points[-1][dim_join] > points[0][dim_join]

    @classmethod
    def __closeSeg(cls, points):
        if points[0] == points[-1]:
            return points
        return points[:] + [points[0]]

    @classmethod
    def __joinCircled(cls, segments):
        if len(segments) > 1 and segments[0][0] == segments[-1][-1]:
            segments[0] = segments[-1] + segments[0][1:]
            del segments[-1]
            return True
        return False

    #=================================
    @classmethod
    def _cutArea(cls, segments, criterium, dim_join):
        result = []
        for points in segments:
            res = cls._cutPoly(points, criterium, True)
            result += cls._cutAreaRes(res, dim_join)
        segments[:] = result

    @classmethod
    def _cutAreaRes(cls, segments, dim_join):
        if len(segments) < 2:
            return [cls.__closeSeg(points) for points in segments]
        sign_next = cls.__signSeg(segments[-1], dim_join)
        for idx in range(len(segments) - 1):
            sign = cls.__signSeg(segments[idx], dim_join)
            if sign == sign_next:
                segments[idx] += segments[idx+1]
                del segments[idx+1]
            sign_next = sign
        assert 1 <= len(segments) <= 2, "Too complex area markup!"
        return [cls.__closeSeg(points) for points in segments]

    #=================================
    @classmethod
    def _cutPoly(cls, points, criterium, closed):
        res = []
        cr0 = criterium(points[0])
        if cr0 >= 0:
            res.append([points[0]])
        idx = 1

        while idx < len(points):
            cr = criterium(points[idx])
            if cr >= 0:
                if cr0 < 0:
                    dcr = cr - cr0
                    if dcr > Config.TOO_SMALL:
                        res.append([geom.linePoint(points[idx-1],
                            points[idx], -cr0 / dcr)])
                    else:
                        res.append([])
                res[-1].append(points[idx])
            elif cr0 >= 0:
                dcr = cr0 - cr
                if dcr > Config.TOO_SMALL:
                    res[-1].append(geom.linePoint(points[idx-1],
                        points[idx], cr0 / dcr))
                elif len(res[-1]) < 2:
                    del res[-1]

            idx += 1
            cr0 = cr

        if closed:
            cls.__joinCircled(res)

        assert all(len(seg) > 1 for seg in res)
        return res

    #=================================
    sP0 = [0, 0]
    def selectLine(self, lines):
        sheet = [(geom.distToLine(self.sP0, *line), idx)
            for idx, line in enumerate(lines)]
        return sorted(sheet)[0][1]
