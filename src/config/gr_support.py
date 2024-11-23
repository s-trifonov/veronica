from PyQt5 import QtCore, QtGui,  QtWidgets
from config.messenger import msg
from h2tools.tools_qt import qt_str

from PyQt5.QtGui import QPen, QBrush, QColor
#=================================
class GraphicsSupport:

    @staticmethod
    def _makePixmapMessage(text, text_color, max_x, max_y, p_x, p_y, angle):
        scene = QtWidgets.QGraphicsScene()
        rect = QtWidgets.QGraphicsRectItem(0, 0, max_x, max_y)
        rect.setBrush(QBrush(QtCore.Qt.white))
        rect.setPen(QPen(QtCore.Qt.white))
        scene.addItem(rect)
        txt_item = QtWidgets.QGraphicsSimpleTextItem()
        txt_item.setText(qt_str(text))
        txt_item.setPos(p_x, p_y)
        txt_item.setBrush(text_color)
        sans_font = QtGui.QFont("Helvetica [Cronyx]", 40, QtGui.QFont.Bold)
        txt_item.setFont(sans_font)
        txt_item.setRotation(angle)
        scene.addItem(txt_item)

        img = QtGui.QImage(max_x + 20, max_y + 20, QtGui.QImage.Format_RGB16)
        painter = QtGui.QPainter(img)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        scene.render(painter)
        del painter
        return QtGui.QPixmap(img).copy(10,  10,  max_x - 20,  max_y - 20)

    sPixmapNotFound = None

    @classmethod
    def getPixmapNotFound(cls):
        if cls.sPixmapNotFound is None:
            cls.sPixmapNotFound = cls._makePixmapMessage(
                msg("img.not.found"),
                QColor(255, 220, 220), 490, 280, 40, 70, -10)
        return cls.sPixmapNotFound

    sPixmapNotAvail = None

    @classmethod
    def getPixmapNotAvailable(cls):
        if cls.sPixmapNotAvail is None:
            cls.sPixmapNotAvail = cls._makePixmapMessage(
                msg("img.not.avail"),
                QColor(220, 220, 255), 490, 280, 40, 70, -10)
        return cls.sPixmapNotAvail

    @classmethod
    def createLine(cls, scene, decor_key, parent = None):
        line = QtWidgets.QGraphicsLineItem(parent)
        if line.scene() is not None:
            scene.addItem(line)
        line.hide()
        pen, brush = cls.getDecorInfo(decor_key)
        if pen is not None:
            line.setPen(pen)
        if brush is not None:
            line.setBrush(brush)
        return line

    sTypeColor = {
        "vesicula":  QtCore.Qt.darkBlue,
        "v-seg":     QtCore.Qt.darkMagenta,
        "barrier":   QtCore.Qt.cyan,
        "blot":      QtCore.Qt.darkCyan,
        "dirt":      QtCore.Qt.black
    }

    sTypeWidth = {
        "vesicula":  4,
        "v-seg":     3,
        "barrier":   4,
        "blot":      2,
        "dirt":      2
    }

    sStdPens = {
        None: QPen(QtCore.Qt.white, 1,
            style = QtCore.Qt.NoPen),
        "_current": QPen(QtCore.Qt.red, 3),
        "_bound": QPen(QtCore.Qt.yellow, 3),
        "_active_bound": QPen(QtCore.Qt.yellow, 5, QtCore.Qt.DashLine),
    }

    sNoBrush = QBrush(QtCore.Qt.NoBrush)
    sStdBrushes = {
        "blot": QBrush(QtCore.Qt.cyan, QtCore.Qt.CrossPattern),
        "dirt": QBrush(QtCore.Qt.blue, QtCore.Qt.Dense5Pattern),
        "_active": QBrush(QtCore.Qt.red),
        "_transparent": QBrush(QtCore.Qt.transparent)
    }

    for tp, color in sTypeColor.items():
        sStdPens[tp] = QPen(color, sTypeWidth[tp])
        sStdBrushes["mark." + tp] = QBrush(color)

    @classmethod
    def stdPen(cls, decor_key):
        if decor_key not in cls.sStdPens:
            if decor_key:
                print("Bad decor pen key:", decor_key)
            return cls.sStdPens[None]
        return cls.sStdPens.get(decor_key)

    @classmethod
    def stdBrush(cls, decor_key):
        return cls.sStdBrushes.get(decor_key, cls.sNoBrush)

    MARK_R = 12
    MARK_D = 2 * MARK_R

    @classmethod
    def readyPointMark(cls, point_item, x, y, vtype):
        point_item.hide()
        point_item.setRect(x - cls.MARK_R, y - cls.MARK_R,
            cls.MARK_D, cls.MARK_D)
        point_item.setPen(cls.stdPen("_bound"))
        #point_item.setBrush(cls.stdBrush("mark." + vtype))
        point_item.setBrush(cls.stdBrush("_active"))

    @classmethod
    def readyPolygon(cls, poly_item, points, vtype, is_closed, is_current):
        poly_item.hide()
        pp_seq = [QtCore.QPointF(x, y) for x, y in points]
        if is_closed:
            pp_seq.append(pp_seq[0])
        paint_path = QtGui.QPainterPath()
        paint_path.addPolygon(QtGui.QPolygonF(pp_seq))
        poly_item.setPath(paint_path)
        poly_item.setPen(cls.stdPen("_current" if is_current else vtype))
        poly_item.setBrush(cls.stdBrush(vtype
            if is_closed else "_transparent"))

    @classmethod
    def readyPatchMarkup(cls, markup_group, markup_points):
        if markup_points is None:
            return False
        cls.clearGroup(markup_group)
        p1, p2 = markup_points
        line = QtWidgets.QGraphicsLineItem(p1[0], p1[1], p2[0], p2[1])
        line.setPen(cls.stdPen("_current"))
        markup_group.addToGroup(line)
        return True

    @classmethod
    def readyPatchPoly(cls, patch_group, points):
        cls.clearGroup(patch_group)
        pp_seq = [QtCore.QPointF(x, y) for x, y in points]
        paint_path = QtGui.QPainterPath()
        paint_path.addPolygon(QtGui.QPolygonF(pp_seq[1:]))
        patch_item = QtWidgets.QGraphicsPathItem()
        patch_item.setPath(paint_path)
        patch_item.setPen(cls.stdPen("_bound"))
        patch_item.setBrush(cls.stdBrush("_transparent"))
        patch_group.addToGroup(patch_item)
        p_line = QtWidgets.QGraphicsLineItem(
            points[0][0], points[0][1],
            points[1][0], points[1][1])
        p_line.setPen(cls.stdPen("_active_bound"))
        patch_group.addToGroup(p_line)
        patch_group.show()

    @classmethod
    def readyDebugSegments(cls, debug_group, segments):
        cls.clearGroup(debug_group)
        for points in segments:
            pp_seq = [QtCore.QPointF(x, y) for x, y in points]
            paint_path = QtGui.QPainterPath()
            paint_path.addPolygon(QtGui.QPolygonF(pp_seq))
            p_item = QtWidgets.QGraphicsPathItem()
            p_item.setPath(paint_path)
            p_item.setPen(cls.stdPen("_current"))
            p_item.setBrush(cls.stdBrush("_transparent"))
            debug_group.addToGroup(p_item)
        debug_group.show()

    @classmethod
    def clearGroup(cls, group):
        for it in group.childItems():
            group.removeFromGroup(it)

    @classmethod
    def makePatchPixmap(cls, pixmap, cropper):
        x0, y0 = cropper.mapToGlobal([0, 0])
        if cropper.getAngle() == 0:
            return pixmap.copy(x0, y0,
                cropper.getSize(), cropper.getSize())
        p_poly = cropper.getPoly(False)
        x1 = min(pp[0] for pp in p_poly)
        x2 = max(pp[0] for pp in p_poly)
        y1 = min(pp[1] for pp in p_poly)
        y2 = max(pp[1] for pp in p_poly)
        local_pixmap = pixmap.copy(
            x1 - 1, y1 - 1, x2 - x1 + 2, y2 - y1 + 2)

        mm = QtGui.QTransform();
        mm.rotate(-cropper.getAngle());
        rotated_pixmap = local_pixmap.transformed(mm,
            QtCore.Qt.SmoothTransformation);
        return rotated_pixmap.copy(
            round((rotated_pixmap.width() - cropper.getSize())/2),
            round((rotated_pixmap.height() - cropper.getSize())/2),
            cropper.getSize(), cropper.getSize())

#=================================
