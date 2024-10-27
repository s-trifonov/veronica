from PyQt5 import QtCore, QtGui,  QtWidgets
#from h2tools.runtime import RT_Guard
from config.gr_support import GraphicsSupport
from config.ver_cfg import Config
#=================================
class ImagePresentation:
    def __init__(self, top_pre):
        self.mTopPre = top_pre

        self.mGrView = self.mTopPre.getEnv().getWidget("the-image")
        self.mGrView.setMouseTracking(True)
        self.mGrView._setWheelZoomFunc(self.mTopPre._imgZoomChange)

        self.mScene = QtWidgets.QGraphicsScene()
        self.mScene.setSceneRect(0, 0,
            Config.DEFAULT_IMAGE_WIDTH, Config.DEFAULT_IMAGE_HEIGHT)

        self.mGrView.setScene(self.mScene)
        self.mGrView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.mGrView.setBackgroundBrush(QtCore.Qt.lightGray)
        self.mGrView.setCacheMode(QtWidgets.QGraphicsView.CacheNone)
        self.mGrView.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)

        self.mNotFoundItem = QtWidgets.QGraphicsRectItem(0, 0,
            Config.DEFAULT_IMAGE_WIDTH, Config.DEFAULT_IMAGE_WIDTH)
        self.mNotFoundItem.setBrush(QtGui.QBrush
            (GraphicsSupport.getPixmapNotAvailable()))
        self.mNotFoundItem.hide()
        self.mScene.addItem(self.mNotFoundItem)

        self.mImgItem = QtWidgets.QGraphicsPixmapItem(
            GraphicsSupport.getPixmapNotFound())
        self.mImgItem.setPos(0, 0)
        self.mImgItem.setOffset(0, 0)
        self.mImgItem.hide()
        self.mImgItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.mScene.addItem(self.mImgItem)

        self.mPolygonItems = []
        self.mPolygonUsageCount = 0
        self.mPolygonGroup = QtWidgets.QGraphicsItemGroup()
        self.mScene.addItem(self.mPolygonGroup)

        self.mPointGroup = QtWidgets.QGraphicsItemGroup()
        self.mPointUsageCount = 0
        self.mPointItems = []
        self.mScene.addItem(self.mPointGroup)

        self.mMarkupCtrl = None

        self.mCurImageH  = None
        self.mCurScale   = None
        self.mCurOpacity = None
        self.mStarted    = False
        self.mCurPixmapH = None
        self.checkZoom()
        self.checkOpacity()

    #==========================
    def resetState(self):
        self.mCurImageH = self.mTopPre.getCurImage()
        pixmap_h = self.mTopPre.getImagePixmapHandler(self.mCurImageH)
        if self.mCurPixmapH is pixmap_h:
            return
        self.mCurPixmapH = pixmap_h
        self.runMarkupCtrl(None)
        if self.mCurPixmapH in (None, False):
            self.mImgItem.hide()
            self.mScene.setSceneRect(-Config.VIS_DELTA, -Config.VIS_DELTA,
                Config.DEFAULT_IMAGE_WIDTH + 2 * Config.VIS_DELTA,
                Config.DEFAULT_IMAGE_HEIGHT + 2 * Config.VIS_DELTA)
            self.mNotFoundItem.show()
        else:
            self.mNotFoundItem.hide()
            self.mImgItem.setPixmap(self.mCurPixmapH.getPixmap())
            h, w = self.mCurPixmapH.getSize()
            self.mImgItem.setPos(0, 0)
            self.mImgItem.setOffset(0, 0)
            self.mScene.setSceneRect(-Config.VIS_DELTA, -Config.VIS_DELTA,
                w + 2 * Config.VIS_DELTA, h + 2 * Config.VIS_DELTA)
            self.mImgItem.show()
        if not self.mStarted:
            scroll_bar = self.mGrView.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.minimum())
            self.mStarted = True

    def checkSelection(self):
        self.updateViewBoxes()
        self.checkZoom()

    def update(self):
        if (self.mCurImageH is not self.mTopPre.getCurImage()):
            self.resetState()

    def getEnv(self):
        return self.mTopPre.getEnv()

    #==========================
    def setCursor(self, cursor):
        if cursor is None:
            self.mGrView.unsetCursor()
        else:
            self.mGrView.setCursor(cursor)

    def checkZoom(self, screen_pos = None):
        zoom = self.mTopPre.getCurZoom()
        if zoom == self.mCurScale:
            return
        self.mCurScale = zoom

#        ??
#        pos0 = (self.mGrView.mapToScene(screen_pos)
#            if screen_pos is not None else None)

        self.mGrView.setTransform(QtGui.QTransform())
        dd = self.mCurScale / 100.
        self.mGrView.scale(dd, dd)

#        if screen_pos is not None:
#            pos1 = self.mGrView.mapToScene(screen_pos)
#            dx, dy = pos1.x() - pos0.x(), pos1.y() - pos0.y()
#            print(f"pos0={pos0}, pos1={pos1}, d={dx}, {dy}")
#            self.mGrView.translate(100*dx, 100*dy)


    def checkOpacity(self):
        opacity = self.mTopPre.getCurOpacity()
        if opacity == self.mCurOpacity:
            return
        dd = opacity / 100.
        self.mImgItem.setOpacity(dd)

    #==========================
    def mapPos(self, pos):
        p = self.mGrView.mapToScene(pos)
        return (int(p.x()), int(p.y()))

    #==========================
    def scrollToPoints(self, p1, p2):
        self.mGrView.ensureVisible(
            QtCore.QRectF(min(p1[0], p2[0]), min(p1[1], p2[1]),
                abs(p2[0] - p1[0]), abs(p2[1] - p1[1])),
            Config.MIN_DIST, Config.MIN_DIST)

    #==========================
    # Markup manipulations
    #==========================
    def runMarkupCtrl(self, ctrl):
        if self.mMarkupCtrl is ctrl and ctrl is not None:
            return
        if self.mMarkupCtrl is not None:
            self.mMarkupCtrl.deactivate()
        self.mMarkupCtrl = ctrl
        if self.mMarkupCtrl is not None:
            self._clearPoints()
            self._clearPolygons()
            self.mMarkupCtrl.activate()
        self.showMarkup(self.mMarkupCtrl is not None)
        self.mGrView.setMouseEventListener(self.mMarkupCtrl)

    def showMarkup(self, value=True):
        if value:
            self.mPolygonGroup.show()
            self.mPointGroup.show()
        else:
            self.mPolygonGroup.hide()
            self.mPointGroup.hide()

    def getMarkupCtrl(self):
        return self.mMarkupCtrl

    def _setPoints(self, points, vtype):
        while len(points) > len(self.mPointItems):
            point_item = QtWidgets.QGraphicsEllipseItem()
            point_item.hide()
            self.mPointGroup.addToGroup(point_item)
            self.mPointItems.append(point_item)
        self.mPointUsageCount = 0
        for pp in points:
            x, y = pp
            point_item = self.mPointItems[self.mPointUsageCount]
            GraphicsSupport.readyPointMark(point_item, x, y, vtype)
            point_item.show()
            self.mPointUsageCount += 1
        for idx in range(self.mPointUsageCount, len(self.mPointItems)):
            self.mPointItems[idx].hide()

    #==========================
    def _clearPoints(self):
        self._setPoints([], None)

    #==========================
    def _clearPolygons(self):
        for idx in range(self.mPolygonUsageCount):
            self.mPolygonItems[idx].hide()
        self.mPointUsageCount = 0

    def _reservePolygon(self):
        if len(self.mPolygonItems) == self.mPolygonUsageCount:
            poly_item = QtWidgets.QGraphicsPolygonItem()
            poly_item.hide()
            self.mPolygonItems.append(poly_item)
            self.mPolygonGroup.addToGroup(poly_item)
        ret = self.mPolygonItems[self.mPolygonUsageCount]
        self.mPolygonUsageCount += 1
        return ret

    def _freePolygon(self, poly_item):
        assert self.mPolygonUsageCount > 0
        if self.mPolygonItems[self.mPolygonUsageCount - 1] is poly_item:
            self.mPolygonUsageCount -= 1
        poly_item.hide()

    #==========================
    #==========================
    def userAction(self, act):
        if act.isAction("check-zoom"):
            self.checkZoom()
            act.done()
            return

        if act.isAction("check-opacity"):
            self.checkOpacity()
            act.done()
            return
