#import sys
import abc
from PyQt5 import QtCore
#from config.messenger import msg

#=================================
class MouseEventListener:
    def __init__(self, view_port):
        self.mViewPort = view_port

    def getViewPort(self):
        return self.mViewPort

    #==========================
    def mapPos(self, event):
        return self.mViewPort.mapPos(event.pos())

    def shiftMode(self, event):
        return bool(event.modifiers() & QtCore.Qt.SHIFT)

    def ctrlMode(self, event):
        return bool(event.modifiers() & QtCore.Qt.CTRL)

    def buttonIsLeft(self, event):
        return event.button() == QtCore.Qt.LeftButton

    def buttonIsLeftOnly(self, event):
        return int(event.buttons()) == QtCore.Qt.LeftButton

    def noButtons(self, event):
        return int(event.buttons()) == 0

    #==========================
    def setHint(self, hint):
        self.mViewPort.getEnv().notifyStatus(hint, hint_mode=True)

    def setCursor(self, cursor):
        self.mViewPort.setCursor(cursor)

    #==========================
    def mouseMoveEvent(self, event):
        pass

    def mousePressEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass

    def leaveEvent(self, event):
        pass

    def enterEvent(self, event):
        pass

    def dragEnterEvent(self, event):
        pass

    def dragMoveEvent(self, event):
        pass

    def dragLeaveEvent(self, event):
        pass

    def modeEvent(self, event):
        pass

    def dropEvent(self, event):
        pass

#=================================
class MouseScenario_NewPath(MouseEventListener):
    def __init__(self, view_port, the_path):
        MouseEventListener.__init__(self, view_port)
        self.mPath = the_path

    def _setPath(self, the_path):
        self.mPath = the_path

    def getPath(self):
        return self.mPath

    #====================
    @abc.abstractmethod
    def onActivate(self):
        assert False

    @abc.abstractmethod
    def onDeactivate(self):
        assert False

    @abc.abstractmethod
    def onPathChange(self):
        assert False

    @abc.abstractmethod
    def viewPoly(self, view_poly):
        assert False

    #====================
    def activate(self):
        self.onActivate()
        self.setCursor(QtCore.Qt.CrossCursor)

    def deactivate(self):
        self.onDeactivate()

    def mouseMoveEvent(self, event):
        cursor = QtCore.Qt.ForbiddenCursor
        view_poly = None
        if self.noButtons(event):
            pos = self.mapPos(event)
            pre_path = self.mPath.checkPrePoint(pos)
            if pre_path is not None:
                view_poly = self.mPath.drawPoly(pre_path)
                cursor = QtCore.Qt.CrossCursor
        self.viewPoly(view_poly)
        self.setCursor(cursor)

    def mousePressEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        if self.buttonIsLeft(event) and self.noButtons(event):
            pos = self.mapPos(event)
            if self.mPath.checkPrePoint(pos):
                self.mPath.addPrePoint(pos)
                self.onPathChange()
        else:
            if self.mPath.popPrePoint():
                self.onPathChange()

#=================================
class MouseScenario_Generic(MouseEventListener):
    def __init__(self, view_port):
        MouseEventListener.__init__(self, view_port)
        self.mCurModInfo = None

    #====================
    @abc.abstractmethod
    def subScenario(self):
        assert False

    @abc.abstractmethod
    def onActivate(self):
        assert False

    @abc.abstractmethod
    def onDeactivate(self):
        assert False

    @abc.abstractmethod
    def locateCur(self, pp):
        assert False

    @abc.abstractmethod
    def setCurPath(self, idx, scroll_to=False):
        assert False

    @abc.abstractmethod
    def onTouchCurPath(self):
        assert False

    @abc.abstractmethod
    def onPathChange(self):
        assert False

    @abc.abstractmethod
    def viewPathPoly(self, view_poly):
        assert False

    def onClick(self, event):
        pass

    def onUnclick(self, event):
        pass

    def mouseBlocked(self):
        return False

    #====================
    def setCurMod(self, mod_info = None):
        self.mCurModInfo = mod_info
        if self.mCurModInfo is not None:
            assert self.mCurModInfo[0] is self.getCurPath()
            self.onTouchCurPath()

    #====================
    def activate(self):
        self.onActivate()
        self.setCursor(QtCore.Qt.ArrowCursor)

    def deactivate(self):
        self.setCurMod(None)
        self.onDeactivate()

    #====================
    sModeCursors = {
        "": QtCore.Qt.CrossCursor,
        "insert": QtCore.Qt.UpArrowCursor,
        "remove": QtCore.Qt.ClosedHandCursor
    }

    def _checkStartMod(self, pos, event):
        cur_path = self.getCurPath()
        if cur_path is None:
            return None
        if self.ctrlMode(event):
            if self.shiftMode(event):
                return None
            return cur_path.checkPos(pos, "remove")
        if self.shiftMode(event):
            return cur_path.checkPos(pos, "insert")
        return cur_path.checkPos(pos, "")

    def _drawCurMod(self, pos):
        if self.mCurModInfo is None:
            self.setCursor(QtCore.Qt.ArrowCursor)
            return
        cur_path, cur_mode, _ = self.mCurModInfo
        assert cur_path is self.getCurPath()
        path_poly = cur_path.viewModifyPos(self.mCurModInfo, pos)
        self.viewPathPoly(path_poly)
        if path_poly is None:
            self.setCursor(QtCore.Qt.ForbiddenCursor)
        else:
            self.setCursor(self.sModeCursors[cur_mode])

    #====================
    def mouseMoveEvent(self, event):
        if self.mouseBlocked():
            self.setCursor(QtCore.Qt.WhatsThisCursor)
            return
        if self.subScenario() is not None:
            self.subScenario().mouseMoveEvent(event)
            return
        pos = self.mapPos(event)
        if self.noButtons(event):
            mod_info = self._checkStartMod(pos, event)
            if mod_info is not None:
                self.setCursor(self.sModeCursors[mod_info[1]])
                return
            loc_idx = self.locateCur(pos)
            if loc_idx is not None and loc_idx != self.getCurPathIdx():
                self.setCursor(QtCore.Qt.PointingHandCursor)
        self._drawCurMod(pos)

    def mousePressEvent(self, event):
        self.onClick(event)
        if self.mouseBlocked():
            self.setCursor(QtCore.Qt.WhatsThisCursor)
            return
        if self.subScenario() is not None:
            self.subScenario().mousePressEvent(event)
            return
        pos = self.mapPos(event)
        if self.buttonIsLeft(event):
            mod_info = self._checkStartMod(pos, event)
            if mod_info is not None:
                self.setCurMod(mod_info)
                self.setCursor(self.sModeCursors[mod_info[1]])
                return
            loc_idx = self.locateCur(pos)
            if loc_idx is not None and loc_idx != self.getCurPathIdx():
                self.setCurPath(loc_idx)
                self.setCursor(QtCore.Qt.ArrowCursor)
                return
        elif self.mCurModInfo is not None:
            self.setCurMod(None)
            self.onTouchCurPath()
        self._drawCurMod(pos)

    def mouseReleaseEvent(self, event):
        self.onUnclick(event)
        if self.mouseBlocked():
            self.setCursor(QtCore.Qt.WhatsThisCursor)
            return
        if self.subScenario() is not None:
            self.subScenario().mouseReleaseEvent(event)
            return

        pos = self.mapPos(event)
        changed = False
        if self.buttonIsLeft(event):
            if self.mCurModInfo is not None:
                changed = self.mCurModInfo[0].keepModifyPos(
                    self.mCurModInfo, pos)
        self.setCurMod(None)
        self.onTouchCurPath()
        self.setCursor(QtCore.Qt.ArrowCursor)
        if changed:
            self.onPathChange()

#=================================
#=================================
