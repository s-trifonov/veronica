import abc
#from config.messenger import msg
from config.ver_cfg import Config
from .v_types import VType

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

    def getSignature(self):
        return "/".join([self.getPathKind(),
            ["open", "closed"][self.isClosed()]])

    def checkPosToModify(self, path_points, p0):
        return None

    def modifyPath(self, path_points, modify_info, pp):
        assert False

    def checkPosToInsert(self, path_points, p0):
        return None

    def insertToPath(self, path_points, insert_info):
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
        dist, cc = geom.locateDistToPoly(p0, path_points, self.mClosed)
        if dist > Config.MIN_DIST:
            return None
        return (int(cc), p0)

    def insertToPath(self, path_points, insert_info):
        idx, pp = insert_info
        assert 0 <= idx < len(path_points)
        ret = path_points[:]
        ret.insert(idx + 1, pp)
        if not geom.checkCorrectPath(ret, self.mClosed):
            return None
        return ret

    def checkPosToRemove(self, path_points, p0):
        if len(path_points) <= 3:
            return None
        dist, cc = geom.locateDistToPoly(p0, path_points, False)
        if dist <= Config.MIN_DIST:
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
        return geom.splineToPoly(path_points, self.mClosed)

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
        idx = modify_info
        assert self.mClosed == (len(path_points) % 3 == 0)
        if idx % 3 == 0:
            dd = geom.delta(path_points[idx], pp)
            idx_p = idx - 1
            if idx_p < 0 and self.mClosed:
               idx_p = len(path_points) - 1
            if idx_p >= 0:
                ret[idx_p] = geom.addVecWithCoeff(
                    ret[idx_p], dd, 1)
            idx_n = idx + 1
            if idx_n == len(path_points) and self.mClosed:
                idx_n = 0
            if idx_n < len(path_points):
                ret[idx_n] = geom.addVecWithCoeff(
                    ret[idx_n], dd, 1)
        ret[idx] = pp
        if not geom.checkCorrectPath(ret, self.mClosed, False):
            return None
        return ret

    def checkPosToInsert(self, path_points, p0):
        if len(path_points) >= Config.MAX_PATH_POINTS:
            return None
        for idx in range(0, len(path_points), 3):
            pp = path_points[idx:idx+4]
            if len(pp) == 1:
                assert not self.mClosed
                break
            elif len(pp) < 4:
                pp.append(path_points[0])
            spl_poly = geom.splinePoints(pp)
            dist, cc = geom.locateDistToPoly(p0, spl_poly, False)
            if dist > Config.MIN_DIAMETER:
                continue
            spl_idx = int(cc)
            if not ( 0 < spl_idx < len(spl_poly) - 1):
                continue
            seg = spl_poly[spl_idx - 1], spl_poly[spl_idx + 1]
            p_insert = geom.linePoint(*seg, cc - spl_idx)

            len_poly = float(geom.polyDiameter(spl_poly))
            if len_poly < Config.MIN_DIAMETER:
                continue
            d_chunk = geom.delta(*seg)
            len_chunk = geom.dist(d_chunk, (0, 0))
            if len_chunk < Config.TOO_SMALL:
                continue
            c_chunk = len_poly / len_chunk
            d_insert = [c_chunk * z for z in d_chunk]

            alpha = float(cc) / len(spl_poly)
            patch_seg = [
                geom.addVecWithCoeff(
                    pp[0], geom.delta(pp[0], pp[1]), alpha),
                geom.addVecWithCoeff(p_insert, d_insert, -.25),
                p_insert,
                geom.addVecWithCoeff(p_insert, d_insert, .25),
                geom.addVecWithCoeff(
                    pp[3], geom.delta(pp[3], pp[2]), 1 - alpha)]

            check_points = path_points[:]
            check_points[idx+1:idx+3] = patch_seg
            if not geom.checkCorrectPath(check_points, self.mClosed):
                return None
            return (idx, patch_seg)
        return None

    def insertToPath(self, path_points, insert_info):
        idx, patch_seg = insert_info
        assert 0 <= idx < len(path_points) - 2 and idx % 3 == 0
        ret = path_points[:]
        ret[idx+1:idx+3] = patch_seg
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
class MarkupPathCtrl:
    _sPMap = {
        "spline": SplinePathLogic,
        "poly": PolyPathLogic,
        "line": LinePathLogic}

    sTypeMap = None
    @classmethod
    def __checkTypeMap(cls):
        if cls.sTypeMap is None:
            cls.sTypeMap = {
                tp.getType(): cls._sPMap[tp.getGeomType()](tp.isClosed())
                for tp in VType.iterTypes()}

    def __init__(self, type, points = None):
        self.__checkTypeMap()
        self.mType = type
        self.mPoints = points if points is not None else []
        self.mLogic = self.sTypeMap[self.mType]

    def getPoints(self):
        return self.mPoints

    def getType(self):
        return self.mType

    def getInfo(self):
        return self.mType, self.mPoints

    def isComplete(self):
        return len(self.mPoints) >= self.mLogic.getMinPointCount()

    def isClosed(self):
        return self.mLogic.isClosed()

    def canChangeType(self, type = None):
        if len(self.mPoints) <= 2:
            return True
        return (type is not None and self.mLogic.getSignature() ==
            self.sTypeMap[type].getSignature())

    def getCompatibleTypes(self):
        ret = []
        sign = self.mLogic.getSignature()
        for type in VType.getList():
            if self.sTypeMap[type].getSignature() == sign:
                ret.append(type)
        return ret

    def changeType(self, type):
        if type == self.mType:
            return
        assert self.canChangeType(type)
        self.mType = type
        self.mLogic = self.sTypeMap[self.mType]

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
            return self.mLogic.insertToPath(self.mPoints, info)
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
