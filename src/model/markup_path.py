import abc
#from config.messenger import msg
from config.ver_cfg import Config

import tools.geom as geom
#=================================
class PathLogic:
    @abc.abstractmethod
    def getPathKind(self):
        assert False

    @abc.abstractmethod
    def isClosed(self):
        assert False

    @abc.abstractmethod
    def getMinPointCount(self):
        assert False

    @abc.abstractmethod
    def drawPoly(self, path_points):
        assert False

    @abc.abstractmethod
    def preBuildPath(self, pre_points):
        assert False

    def checkPosToModify(self, path_points, p0):
        return None

    def modifyPath(self, path_points, modify_info, pp):
        assert False

    def checkPosToInsert(self, path_points, p0):
        return None

    def insertToPath(self, path_points, insert_info, pp):
        assert False

    def checkPosToRemove(self, path_points, p0):
        return None

    def removeInPath(self, path_points, remove_info):
        assert False

#=================================
class LinePathLogic(PathLogic):
    def getPathKind(self):
        return "plain"

    def isClosed(self):
        return False

    def getMinPointCount(self):
        return 2

    def drawPoly(self, path_points):
        if len(path_points) < 2:
            return None
        return path_points[:2]

    def preBuildPath(self, pre_points):
        if len(pre_points) < 2:
            return True
        ret = pre_points[:2]
        if geom.dist(*ret) > Config.MIN_DIST:
            return ret
        return None

    def checkPosToModify(self, path_points, p0):
        for idx, pp in enumerate(path_points[:2]):
            if geom.dist(p0, pp) <= Config.MIN_DIST:
                return idx
        return None

    def modifyPath(self, path_points, modify_info, pp):
        assert modify_info in (0, 1)
        if geom.dist(path_points[1 - modify_info], pp) < Config.MIN_DIST:
            return None
        ret = path_points[:2]
        ret[modify_info] = pp
        return ret

#=================================
class PolyPathLogic(PathLogic):
    def __init__(self, closed_mode):
        self.mClosed = closed_mode

    def getPathKind(self):
        return "plain"

    def isClosed(self):
        return self.mClosed

    def getMinPointCount(self):
        return 3

    def drawPoly(self, path_points):
        if len(path_points) < 2:
            return None
        return path_points

    def preBuildPath(self, pre_points):
        if not geom.checkCorrectPath(pre_points, False, False):
            return None
        if len(pre_points) < 3:
            return True
        return pre_points

    def checkPosToModify(self, path_points, p0):
        for idx, pp in enumerate(path_points):
            if geom.dist(p0, pp) <= Config.MIN_DIST:
                return idx
        return None

    def modifyPath(self, path_points, modify_info, pp):
        assert 0 <= modify_info < len(path_points)
        ret = path_points[:]
        ret[modify_info] = pp
        if not geom.checkCorrectPath(ret, self.mClosed):
            return None
        return ret

    def checkPosToInsert(self, path_points, p0):
        if len(path_points) >= Config.MAX_PATH_POINTS:
            return None
        dist, cc = geom.locateDistToPoly(p0, path_points)
        if dist > Config.MIN_DIST:
            return
        if abs(cc - round(cc)) < Config.MIN_LOC:
            return None
        if round(cc + .5) != round(cc):
            return round(cc) + 1
        return round(cc)

    def insertToPath(self, path_points, insert_info, pp):
        assert 0 <= insert_info < len(path_points) - 1
        ret = path_points[:]
        ret.insert(insert_info + 1, pp)
        if not geom.checkCorrectPath(ret, self.mClosed):
            return None
        return ret

    def checkPosToRemove(self, path_points, p0):
        if len(path_points) <= 3:
            return None
        dist, cc = geom.locateDistToPoly(p0, path_points)
        if dist < Config.MIN_DIST and abs(cc - round(cc)) < Config.MIN_LOC:
            return round(cc)
        return None

    def removeInPath(self, path_points, remove_info):
        ret = path_points[:]
        del ret[remove_info]
        if not geom.checkCorrectPath(ret, self.mClosed):
            return None
        return ret

#=================================
class SplinePathLogic(PathLogic):
    def __init__(self, closed_mode):
        self.mClosed = closed_mode

    def getPathKind(self):
        return "spline"

    def isClosed(self):
        return self.mClosed

    def getMinPointCount(self):
        return 2

    def drawPoly(self, path_points):
        if len(path_points) < 2:
            return None
        ret = []
        if self.mClosed:
            assert len(path_points) % 3 == 0
        else:
            assert len(path_points) % 3 == 1
        for idx in range(0, len(path_points), 3):
            pp = path_points[idx:idx+4]
            if len(pp) == 1:
                break
            elif len(pp)< 4:
                pp.append(path_points[0])
            ret += geom.splinePoints(pp)
        del ret[-1]
        return ret

    SPLINE_C = .5 / .75

    def preBuildPath(self, pre_points):
        if len(pre_points) < 2:
            return True
        assert len(pre_points) == 2
        if not geom.checkCorrectPath(pre_points, False, False):
            return None
        if self.mClosed:
            dd0 = geom.delta(*pre_points)
            dd = (-dd0[1], dd0[0])
            return [
                pre_points[0],
                geom.addVecWithCoeff(pre_points[0], dd, self.SPLINE_C),
                geom.addVecWithCoeff(pre_points[1], dd, self.SPLINE_C),
                pre_points[1],
                geom.addVecWithCoeff(pre_points[1], dd, -self.SPLINE_C),
                geom.addVecWithCoeff(pre_points[0], dd, -self.SPLINE_C)]
        else:
            return [
                pre_points[0],
                geom.linePoint(*pre_points, .33),
                geom.linePoint(*pre_points, .66),
                pre_points[1]]

    def checkPosToModify(self, path_points, p0):
        for idx, pp in enumerate(path_points):
            if geom.dist(p0, pp) <= Config.MIN_DIST:
                return idx
        return None

    def modifyPath(self, path_points, modify_info, pp):
        assert 0 <= modify_info < len(path_points)
        ret = path_points[:]
        ret[modify_info] = pp
        if not geom.checkCorrectPath(ret, self.mClosed, False):
            return None
        return ret

    def checkPosToInsert(self, path_points, p0):
        if len(path_points) >= Config.MAX_PATH_POINTS:
            return None
        for idx in range(0, len(path_points), 3):
            pp = path_points[idx:idx+3]
            if len(pp) == 1:
                break
            elif len(pp) < 4:
                pp.append(path_points[0])
            spl_poly = geom.splinePoints(pp)
            dist, cc = geom.locateDistToPoly(p0, spl_poly)
            if (dist <= Config.MIN_DIST and
                    cc >= 1 and cc + 1 < len(spl_poly)):
                lseg = geom.dist(spl_poly[0], spl_poly[-1])
                cc = int(cc)
                dd = geom.delta(spl_poly[cc + 1], spl_poly[cc - 1])
                lchunk = geom.dist(dd, (0, 0))
                if lchunk < Config.TOO_SMALL:
                    continue
                cc = float(lseg) / lchunk
                return (idx, (cc * dd[0], cc* dd[1]))
        return None

    def insertToPath(self, path_points, insert_info, pp):
        idx, dd = insert_info
        assert 0 <= idx < len(path_points) - 2 and idx % 3 == 0
        ret = path_points[:]
        ret[idx+1:idx+1] = [geom.addVecWithCoeff(pp, dd, -.33),
            pp, geom.addVecWithCoeff(pp, dd, .33)]
        if not geom.checkCorrectPath(ret, self.mClosed):
            return None
        return ret

    def checkPosToRemove(self, path_points, p0):
        if len(path_points) <= (6 if self.mClosed else 4):
            return None
        for idx in range(0, len(path_points), 3):
            if geom.dist(p0, path_points[idx]) <= Config.MIN_DIST:
                return idx
        return None

    def removeInPath(self, path_points, remove_info):
        ret = path_points[:]
        if remove_info == 0:
            ret = path_points[2:]
            if self.mClosed:
                ret.append(ret[0])
                del ret[0]
        elif remove_info == len(path_points) - 1:
            assert not self.mClosed
            ret = ret[:-3]
        else:
            ret[remove_info - 1: remove_info + 2] = []
        if not geom.checkCorrectPath(ret, self.mClosed):
            return None
        return ret

#=================================
class MarkupPath:

    sTypeMap = {
        "vesicula": SplinePathLogic(True),
        "v-seg": SplinePathLogic(False),
        "v-joint": LinePathLogic(),
        "blot": SplinePathLogic(True),
        "dirt": PolyPathLogic(True)
    }

    def __init__(self, type, points = None):
        self.mType = type
        self.mPoints = points if points is not None else []
        self.mLogic = self.sTypeMap[self.mType]

    def getPoints(self):
        return self.mPoints

    def getType(self):
        return self.mType

    def isComplete(self):
        return len(self.mPoints) >= self.mLogic.getMinPointCount()

    def isClosed(self):
        return self.mLogic.isClosed()

    def canChangeType(self):
        return len(self.mPoints) <= 2

    def changeType(self, type):
        self.mType = type
        self.mLogic = self.sTypeMap(self.mType)

    def checkPrePoint(self, pp):
        pre_points = self.mPoints + [pp]
        pre_path = self.mLogic.preBuildPath(pre_points)
        return pre_path

    def addPrePoint(self, pp):
        self.mPoints.append(pp)
        if len(self.mPoints) >= self.mLogic.getMinPointCount():
            pre_path = self.mLogic.preBuildPath(self.mPoints)
            assert (isinstance(pre_path, list)
                and len(pre_path) >= len(self.mPoints))
            self.mPoints = pre_path

    def popPrePoint(self):
        if not self.isClosed() and len(self.mPoints) > 1:
            del self.mPoints[-1]
            return True
        return False

    def drawPoly(self, pre_path=None):
        if pre_path is not None:
            the_path = pre_path
        elif self.isComplete():
            the_path = self.mPoints
        else:
            the_path = self.mLogic.preBuildPath(self.mPoints)
        if the_path in (None, True):
            return None
        return self.mLogic.drawPoly(the_path)

    def checkPos(self, pp, mode):
        if mode == "insert":
            ret = self.mLogic.checkPosToInsert(self.mPoints, pp)
        elif mode == "remove":
            ret = self.mLogic.checkPosToRemove(self.mPoints, pp)
        else:
            ret = self.mLogic.checkPosToModify(self.mPoints, pp)
        if ret is not None:
            return (self, mode, ret)
        return None

    def _modifyPos(self, modify_info, pp):
        assert modify_info[0] is self
        _, mode, info = modify_info
        if mode == "insert":
            return self.mLogic.insertToPath(self.mPoints, info, pp)
        elif mode == "remove":
            return self.mLogic.removeInPath(self.mPoints, info)
        return self.mLogic.modifyPath(self.mPoints, info, pp)

    def viewModifyPos(self, modify_info, pp):
        points = self._modifyPos(modify_info, pp)
        if points is None:
            return None
        return self.mLogic.drawPoly(points)

    def keepModifyPos(self, modify_info, pp):
        points = self._modifyPos(modify_info, pp)
        assert points is not None
        if (len(self.mPoints) == len(points) and
                all(self.mPoints[i][j] == points[i][j]
                    for i in range(len(points))
                    for j in range(2))):
            return False
        self.mPoints = points
        return True