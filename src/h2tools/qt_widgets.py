import sys
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets, Qsci, QtGui
from .tools_qt import qt_str, updateStyle
from .runtime import RT_Guard
from .utils import getExceptionValue
from .ui_oplist import UI_OpList
#===================================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.mKey_F    = None
        self.mClose_F  = None

    def getRegion(self):
        size = self.size()
        pos = self.pos()
        reg = [size.width(), size.height(), pos.x(), pos.y()]
        return reg

    def setRegion(self, width, height, left, top):
        self.resize(width, height)
        self.move(left, top)

    def setListeners(self, key_f, close_f = None):
        self.mKey_F    = key_f
        self.mClose_F  = close_f

    def keyPressEvent(self, evt):
        if self.mKey_F is not None:
            self.mKey_F(evt)
        return QtWidgets.QMainWindow.keyPressEvent(self, evt)

    def closeEvent(self, evt):
        if self.mClose_F:
            self.mClose_F()
        return QtWidgets.QMainWindow.closeEvent(self, evt)


class Dialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self, None)
        self.mStoredPos = None

    def getRegion(self):
        size = self.size()
        pos = self.pos()
        reg = [size.width(), size.height(), pos.x(), pos.y()]
        return reg

    def setRegion(self, width, height, left, top):
        self.resize(width, height)
        self.move(left, top)

#===================================
class ComboBoxWithValues(QtWidgets.QComboBox):
    def __init__(self, parent, items = None,
            supports_wrong_value = False,
            to_hide = None):
        QtWidgets.QComboBox.__init__(self, parent)
        self.mSupportsWrong = supports_wrong_value
        self.mWrongValue = None
        if items is not None:
            self.mDataToHide = None
            self.setupItems(items, to_hide = to_hide)

    def setupItems(self, items, cur_value = None, to_hide = None):
        self.clear()
        if self.mWrongValue:
            self.setProperty("sclass", "")
            updateStyle(self)
        self.mWrongValue = None
        self.mValues = []
        for idx, item in enumerate(items):
            if isinstance(item, str):
                text, image, value = item, None, item
            else:
                text, image, value = item
            if image is None:
                self.addItem(text, userData = value)
            else:
                self.addItem(image, text, userData = value)
            self.mValues.append(value)
            if value == to_hide:
                self.mDataToHide = [text, image, value, idx, False]
        self.mOpList = UI_OpList(self.mValues)
        self.setDisabled(len(self.mValues) < 2)
        if cur_value is not None:
            self.setValue(cur_value, True)

    def setEnabledItems(self, enabled_values, cur_value = None):
        count_good = 0
        for idx, value in enumerate(self.mValues):
            # hack on Qt5 level: disable/enable items in combo box
            if value in enabled_values:
                self.setItemData(idx, 33, QtCore.Qt.UserRole - 1)
                count_good += 1
                if value == cur_value:
                    self.setCurrentIndex(idx)
            else:
                self.setItemData(idx, 0, QtCore.Qt.UserRole - 1)
        self.setDisabled(count_good < 2)

    def makeAllEnabled(self):
        self.setEnabledItems(self.mValues, self.getValue())

    def setValue(self, value, needs_update_style = False):
        set_value = False
        value = str(value)
        if self.mSupportsWrong:
            if value == self.mWrongValue:
                return
            if self.mWrongValue is not None:
                self.removeItem(len(self.mValues))
                self.mWrongValue = None
                needs_update_style = True
            if value not in self.mValues:
                self.mWrongValue = value
                self.addItem(value, userData = value)
                needs_update_style = True
                self.setCurrentIndex(len(self.mValues))
                set_value = True
        if not set_value and value in self.mValues:
            self.setCurrentIndex(self.mValues.index(value))
        if needs_update_style:
            self.setProperty("sclass",
                "wrong_value" if self.mWrongValue else "")
            updateStyle(self)
            self.setDisabled(len(self.mValues) < 2 and not self.mWrongValue)

    def getValue(self):
        idx = self.currentIndex()
        if 0 <= idx < len(self.mValues):
            return self.mValues[idx]
        return self.mWrongValue

    def checkWrongValue(self):
        if self.mWrongValue and self.currentIndex() < len(self.mValues):
            self.removeItem(len(self.mValues))
            self.mWrongValue = None
            self.setProperty("sclass", "")
            updateStyle(self)
            self.setDisabled(len(self.mValues) < 2)

    def checkHiddenValue(self, val, set_visible):
        assert val == self.mDataToHide[2]
        if set_visible == self.mDataToHide[-1]:
            return
        if set_visible:
            text, image, value, idx, viz = self.mDataToHide
            assert not viz
            if image is None:
                self.insertItem(idx, text, userData = value)
            else:
                self.insertItem(idx, image, text, userData = value)
            self.mDataToHide[-1] = True
            self.mValues.insert(idx, value)
        else:
            cur_idx = self.currentIndex()
            idx = self.mDataToHide[-2]
            self.removeItem(idx)
            self.mDataToHide[-1] = False
            del self.mValues[idx]
            if cur_idx == idx:
                self.setValue(self.mValues[0])

    def removeValue(self, value):
        reselect = (self.mValues[self.currentIndex()] == value)
        self.removeItem(self.mValues.index(value))
        self.mValues.remove(value)
        self.mOpList = UI_OpList(self.mValues)
        if reselect:
            self.setCurrentIndex(0)

    def userAction(self, act):
        if self.currentIndex() is None:
            return False
        cur_name = self.mValues[self.currentIndex()]
        val = self.mOpList.relocate(cur_name, act, True)
        if val is None:
            return False
        if val:
            self.setValue(val)
        return True

    def sibbling(self, delta):
        val = self.mOpList.sibbling(self.currentIndex(), delta)
        if val is not None:
            self.setValue(val)
            return True
        return False

    def clearActiveSelection(self):
        if len(self.mValues) < 2:
            self.setDisabled(False)
        self.setCurrentIndex(-1)

#===================================
class ListWidget(QtWidgets.QListWidget):
    def __init__(self, parent, items = None,
            supports_wrong_value = False):
        QtWidgets.QListWidget.__init__(self, parent)
        self.mSupportsWrong = supports_wrong_value
        self.mWrongValue = None
        if items is not None:
            self.setupItems(items)

    def setupItems(self, items, cur_value = None):
        self.clear()
        self.mValues = []
        for idx, item in enumerate(items):
            if isinstance(item, str):
                text, image = item, None
            else:
                text, image = item[:2]
            if image is None:
                self.addItem(text)
            else:
                self.addItem(
                    QtWidgets.QListWidgetItem(image, text))
            self.mValues.append(text)
        self.setDisabled(len(self.mValues) < 2)
        if cur_value is None and len(self.mValues) > 0:
            cur_value = self.mValues[0]
        if cur_value is not None:
            self.setValue(cur_value, True)

    def setValue(self, value, needs_update_style = False):
        set_value = False
        value = str(value)
        if self.mSupportsWrong:
            if value == self.mWrongValue:
                return
            if self.mWrongValue is not None:
                self.remove(self.item(len(self.mValues)))
                self.mWrongValue = None
                needs_update_style = True
            if value not in self.mValues:
                self.mWrongValue = value
                self.addItem(value)
                needs_update_style = True
                self.setCurrentIndex(len(self.mValues))
                set_value = True
        if not set_value and value in self.mValues:
            self.setCurrentRow(self.mValues.index(value))
        if needs_update_style:
            self.setProperty("sclass",
                "wrong_value" if self.mWrongValue else "")
            updateStyle(self)
            self.setDisabled(len(self.mValues) < 2 and not self.mWrongValue)

    def getValue(self):
        idx = self.currentRow()
        if 0 <= idx < len(self.mValues):
            return self.mValues[idx]
        return self.mWrongValue

    def removeValue(self, value):
        reselect = (self.mValues[self.currentRow()] == value)
        self.remove(self.item(self.mValues.index(value)))
        self.mValues.remove(value)
        if reselect:
            self.setCurrentRow(0)

    def checkWrongValue(self):
        if self.mWrongValue and self.currentRow() < len(self.mValues):
            self.remove(self.item(len(self.mValues)))
            self.mWrongValue = None
            self.setProperty("sclass", "")
            updateStyle(self)
            self.setDisabled(len(self.mValues) < 2)

    def clearActiveSelection(self):
        if len(self.mValues) < 2:
            self.setDisabled(False)
        self.setCurrentRow(-1)

#===================================
class ComboLineWithMemory(QtWidgets.QComboBox):
    def __init__(self, parent, mem_length = 30):
        QtWidgets.QComboBox.__init__(self, parent)
        self.mMemLength = mem_length
        self.setEditable(True)
        self.clearEditText()
        self.mMemState = []

    def getMemState(self):
        return self.mMemState

    def setMemState(self, mem_state):
        assert isinstance(mem_state, list)
        self.mMemState = mem_state[:]
        self._setup()

    def _setup(self):
        QtWidgets.QComboBox.clear(self)
        for variant in self.mMemState:
            self.addItem(variant)

    def rememberVariant(self, variant = True):
        if variant is True:
            variant = self.lineEdit().text()
        if len(self.mMemState) > 0 and variant == self.mMemState[0]:
            return
        if variant in self.mMemState:
            del self.mMemState[self.mMemState.index(variant)]
        self.mMemState.insert(0, variant)
        if len(self.mMemState) > self.mMemLength:
            self.mMemState = self.mMemState[:self.mMemLength]
        self._setup()

    def getValue(self):
        return self.lineEdit().text()

    def clear(self):
        self.lineEdit().setText("")

    def setText(self, txt):
        self.lineEdit().setText(qt_str(txt))

    def setBadMode(self, bad_mode):
        self.setProperty("sclass",
            "wrong_value" if bad_mode else "")
        updateStyle(self)

#===================================
# Keep in mind term conflict: TabBox, TabWidget -> QTabWidget, QWidget
#===================================
class TabBox(QtWidgets.QTabWidget):
    def __init__(self, parent):
        QtWidgets.QTabWidget.__init__(self, parent)
        self.mTabIdxStack = None
        self.mHoldState = False
        self.mChangingCtrl = None

    def getCurrentController(self):
        tab = self.currentWidget()
        if tab is not None:
            return tab.getController()
        return None

    def getHoldState(self):
        return self.mHoldState or self.mChangingCtrl

    def getChangingController(self):
        return self.mChangingCtrl

    def getCurWidgetName(self):
        tab = self.currentWidget()
        if tab is not None:
            return tab.objectName()
        return None

    def pushCurWidget(self):
        if self.mTabIdxStack is None:
            self.mTabIdxStack = [idx for idx in range(self.count())]
        self.pushWidget(self.currentWidget().objectName())

    def pushWidget(self, object_name):
        if self.mTabIdxStack is None:
            self.pushCurWidget()
        for j, idx in enumerate(self.mTabIdxStack):
            if self.widget(idx).objectName() == object_name:
                if j == 0:
                    return
                del self.mTabIdxStack[j]
                self.mTabIdxStack.insert(0, idx)
                return
        assert False

    def widgetOrder(self, controller_0, controller_1):
        if self.mTabIdxStack is None:
            self.pushCurWidget()
        j, j0, j1 = -1, -1, -1
        while j < len(self.mTabIdxStack) - 1:
            j += 1
            ctrl = self.widget(self.mTabIdxStack[j]).getController()
            if ctrl == controller_0:
                assert j0 < 0
                j0 = j
            if ctrl == controller_1:
                assert j1 < 0
                j1 = j
        assert j0 >= 0 and j1 >= 0
        if j1 != j0 + 1:
            idx = self.mTabIdxStack[max(j0, j1)]
            del self.mTabIdxStack[max(j0, j1)]
            if j0 < j1:
                self.mTabIdxStack.insert(j0 + 1, idx)
            else:
                self.mTabIdxStack.insert(j1, idx)

    def setCurWidget(self, object_name):
        for idx in range(self.count()):
            if self.widget(idx).objectName() == object_name:
                self.widget(idx).setCurrent()
                return

    def getControllers(self):
        for idx in range(self.count()):
            ctrl = self.widget(idx).getController()
            if ctrl is not None:
                yield ctrl

    def holdCurrentState(self):
        assert not self.mHoldState
        self.mHoldState = True

    def setupCurrentState(self, keep_current = False):
        assert self.mHoldState
        if self.mTabIdxStack is None:
            self.pushCurWidget()
        cur_w = self.currentWidget() if keep_current else None
        idx_cur = None
        for idx in self.mTabIdxStack:
            w = self.widget(idx)
            if w.mHoldDisable is None:
                w.mHoldDisable = not w.isEnabled()
            if not w.mHoldDisable and (idx_cur is None or w is cur_w):
                idx_cur = idx
        if idx_cur is not None:
            w = self.widget(idx_cur)
            w.setDisabled(False)
            self.setTabEnabled(idx_cur, True)
            if not w.isCurrent():
                w.setCurrent()
        for idx in self.mTabIdxStack:
            w = self.widget(idx)
            if idx is not idx_cur:
                w.setDisabled(w.mHoldDisable)
                self.setTabEnabled(idx, not w.mHoldDisable)
            w.mHoldDisable = None
        self.mHoldState = False

    def setChangingController(self, ctrl):
        self.mChangingCtrl = ctrl
        for idx in range(self.count()):
            w = self.widget(idx)
            ctrl = w.getController()
            if ctrl is None or ctrl.isReadOnly() or ctrl is self.mChangingCtrl:
                continue
            if self.mChangingCtrl is not None:
                w.mHoldDisable = not self.isTabEnabled(idx)
                self.setTabEnabled(idx, False)
            else:
                if w.mHoldDisable is not None:
                    self.setTabEnabled(idx, not w.mHoldDisable)
                    w.mHoldDisable = None

    def setupEmptyControllers(self, ctrl_f):
        for idx in range(self.count()):
            w = self.widget(idx)
            if w.getController() is None:
                ctrl_f(w.objectName())

    def userAction(self, act, name_preffix = None):
        cur_name = None
        names, lost = [], []
        for idx in range(self.count()):
            w = self.widget(idx)
            if not w.isEnabled():
                lost.append(w.objectName())
                continue
            if w.isCurrent():
                cur_name = w.objectName()
            names.append(w.objectName())
        op_list = UI_OpList(names)
        name = op_list.relocate(cur_name, act, False)
        if name is not None:
            self.setCurWidget(name)
            return True
        if name_preffix is not None:
            if not act.isGroup(name_preffix):
                return False
        name = op_list.selectName(cur_name, act, '-')
        if name is not None:
            if name:
                self.setCurWidget(name)
                self.pushWidget(name)
            return True
        for nm in lost:
            if nm.endswith(act.getOpName()):
                act.failed()
                break
        return False

#===================================
class TabWidget(QtWidgets.QWidget):
    sColorChanging = QtGui.QColor(255, 0, 64)

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.mTabBox = parent
        self.mTabIdx    = None
        self.mController = None
        self.mHoldDisable = None
        self.mTabColorDefault = None

    def activate(self):
        self.mTabIdx = self.mTabBox.addTab(self, qt_str(""))
        self.mTabColorDefault = self.mTabBox.tabBar().tabTextColor(
            self.mTabIdx)

    def setController(self, controller):
        assert self.mController is None
        self.mController = controller

    def getTabBox(self):
        return self.mTabBox

    def getTabBar(self):
        return self.mTabBox.tabBar()

    def getController(self):
        return self.mController

    def setContentDisabled(self, value):
        QtWidgets.QWidget.setDisabled(self, value)

    def setDisabled(self, value):
        if self.mTabBox.getHoldState():
            self.mHoldDisable = value
        else:
            self.mTabBox.setTabEnabled(self.mTabIdx, not value)

    def setText(self, value):
        self.mTabBox.setTabText(self.mTabIdx, value)

    def setToolTip(self, value):
        self.mTabBox.setTabToolTip(self.mTabIdx, value)

    def setIcon(self, value):
        self.mTabBox.setTabIcon(self.mTabIdx, value)

    def setCurrent(self):
        if self.isEnabled():
            self.mTabBox.setCurrentIndex(self.mTabIdx)

    def isCurrent(self):
        return self.mTabBox.currentIndex() == self.mTabIdx

    def getTabIndex(self):
        return self.mTabIdx

    def getChangingMode(self):
        return self.mTabBox.getChangingController() is self.mController

    def setChangingMode(self, value):
        if not value:
            if self.mTabBox.getChangingController() is not self.mController:
                return False
            self.mTabBox.setChangingController(None)
            self.mTabBox.tabBar().setTabTextColor(
                self.mTabIdx, self.mTabColorDefault)
            return True
        if self.mTabBox.getChangingController() is self.mController:
            return False
        if self.mTabBox.getChangingController() is not None:
            return False
        self.mTabBox.setChangingController(self.mController)
        self.mTabBox.tabBar().setTabTextColor(
            self.mTabIdx, self.sColorChanging)
        return True

#===================================
class ProgressBar(QtWidgets.QProgressBar):
    def __init__(self, parent):
        QtWidgets.QProgressBar.__init__(self, parent)
        self.mProgressState = None
        self.setMinimum(0)
        self.setMaximum(100)
        self.setInactive()

    def setInactive(self):
        if self.mProgressState is False:
            return
        self.setDisabled(True)
        self.setFormat("--")
        self.setValue(99)
        self.reset()
        self.mProgressState = "inactive"

    def setUndetermined(self):
        self.setProgressState("undet")

    def setProgressState(self, value):
        if value == self.mProgressState:
            return
        self.reset()
        if value == "undet":
            self.setFormat("*")
            self.setValue(50)
            self.setDisabled(True)
        else:
            self.setFormat("%p")
            self.setValue(value)
            self.setDisabled(False)
        self.mProgressState = value

#===================================
class TreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent):
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.mDrop_F = None
        self.mOnCurrentChangeF = None

    def _initColSizes(self, col_sizes):
        try:
            for idx, size in enumerate(col_sizes):
                self.header().setSectionResizeMode(
                    QtWidgets.QHeaderView.Interactive)
                self.header().resizeSection(idx, size)
        except Exception:
            print("Failed to set persistent tree column sizes:",
                file = sys.stderr)
            getExceptionValue()

    def _setupCurrentItemChange(self, func):
        self.mOnCurrentChangeF = func

    def currentChanged(self, cur, prev):
        QtWidgets.QTreeWidget.currentChanged(self, cur, prev)
        if self.mOnCurrentChangeF is not None:
            self.mOnCurrentChangeF()

    def setDropF(self, drop_f):
        self.mDrop_F = drop_f

    def dropEvent(self, event):
        if event.source() == self:
            QtWidgets.QAbstractItemView.dropEvent(self, event)

    def dropMimeData(self, parent, index, data, action):
        return self.mDrop_F(parent, index, data, action)

    def getColSizesInfo(self):
        return [self.header().sectionSize(idx)
            for idx in range(self.model().columnCount())]

#===================================
class TableView(QtWidgets.QTableView):
    def __init__(self, parent):
        QtWidgets.QTableView.__init__(self, parent)
        self.mOnCurrentChangeF   = None
        self.mOnSelectionChangeF = None
        self.mMousePressF        = None

    def _initColSizes(self, col_sizes):
        try:
            for idx, size in enumerate(col_sizes):
                self.setColumnWidth(idx, size)
        except Exception:
            print("Failed to set persistent table column sizes:",
                file = sys.stderr)
            getExceptionValue()

    def _setMousePressFunc(self, mouse_press_func):
        self.mMousePressF = mouse_press_func

    def _setupCurrentItemChange(self, func):
        self.mOnCurrentChangeF = func

    def _setupSelectionChange(self, func):
        self.mOnSelectionChangeF = func

    def currentChanged(self, cur, prev):
        QtWidgets.QTableView.currentChanged(self, cur, prev)
        if self.mOnCurrentChangeF is not None:
            self.mOnCurrentChangeF()

    def selectionChanged(self, selected, deselected):
        QtWidgets.QTableView.selectionChanged(self, selected, deselected)
        if self.mOnSelectionChangeF is not None and selected is not None:
            self.mOnSelectionChangeF()

    def getColSizesInfo(self):
        return [self.columnWidth(idx)
            for idx in range(self.model().columnCount() - 1)]

    def clearModel(self):
        if self.model().rowCount() > 0:
            self.model().removeRows(0, self.model().rowCount())

    def scrollToCurrent(self):
        item = self.curremtItem()
        if item is not None:
            self.scrollTo(self.model().indexFromItem(item))

    def scrollToLine(self, idx):
        self.scrollTo(self.model().index(idx, 0))

    def mousePressEvent(self, event):
        if self.mMousePressF:
            return self.mMousePressF(event)
        return QtWidgets.QTableView.mousePressEvent(self, event)

#===================================
class PlainTextEdit(QtWidgets.QPlainTextEdit):
    def __init__(self, parent):
        QtWidgets.QPlainTextEdit.__init__(self, parent)

    def text(self):
        return self.toPlainText()

    def setText(self, txt):
        self.setPlainText(txt)

#===================================
class ToolButtonMenu(QtWidgets.QToolButton):
    def __init__(self, parent):
        QtWidgets.QToolButton.__init__(self, parent)
        self.mMenu = QtWidgets.QMenu(self)
        self.setMenu(self.mMenu)
        self.mActions = []
        self.mCtrls   = []
        self.setDisabled(True)
        self.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.mMenu.aboutToShow.connect(self.correctMenuPosition)
        self.mMenu.setLayoutDirection(QtCore.Qt.RightToLeft)

    def correctMenuPosition(self):
        point        = self.rect().topLeft()
        global_point = self.mapToGlobal(point)
        self.mMenu.move(global_point
            - QtCore.QPoint(self.mMenu.width() - 1200, -200))

    def regActionOn(self, ctrl, message, act_f):
        if ctrl in self.mCtrls:
            return
        action = QtWidgets.QAction(message, self.mMenu)
        self.mMenu.addAction(action)
        action.triggered.connect(act_f)
        self.mCtrls.append(ctrl)
        self.mActions.append(action)
        self.setDisabled(False)

    def regActionOff(self, ctrl):
        if ctrl not in self.mCtrls:
            return
        idx = self.mCtrls.index(ctrl)
        action = self.mActions[idx]
        action.setParent(None)
        del self.mActions[idx]
        del self.mCtrls[idx]
        del action
        self.setDisabled(len(self.mCtrls) == 0)

#===================================
class Splitter(QtWidgets.QSplitter):
    def __init__(self, parent):
        QtWidgets.QSplitter.__init__(self, parent)
        self.mCareHidden = None
        self.mSplitSizes = None
        self.splitterMoved.connect(self.onSplitChange)

    def setup(self, care_hidden):
        self.mCareHidden = care_hidden
        for idx in range(self.count()):
            self.setCollapsible(idx, False)

    @QtCore.pyqtSlot(int, int)
    def onSplitChange(self, s1, s2):
        if self.mCareHidden and any(self.widget(idx).isHidden()
                for idx in range(self.count())):
            return
        self.mSplitSizes = self.sizes()[:]

    def setSplitSizes(self, size_seq):
        self.mSplitSizes = size_seq
        self.setSizes(size_seq)

    def getSplitSizes(self):
        if self.mSplitSizes is None:
            self.mSplitSizes = self.sizes()[:]
        return self.mSplitSizes

#===================================
def getWheelDelta(event):
    ret = _getWheelDelta(event)
    return ret

def _getWheelDelta(event):
    num_pixels = event.pixelDelta()
    if not num_pixels.isNull():
        return num_pixels.y() if num_pixels.y() != 0 else num_pixels.x()
    num_degrees = event.angleDelta()
    return num_degrees.y() if num_degrees.y() != 0 else num_degrees.x()

#===================================
class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent):
        QtWidgets.QGraphicsView.__init__(self, parent)
        self.mMouseEventListener = None
        self.mNoWheel            = False
        self.mWheelZoomF         = None

    def setMouseEventListener(self, listener):
        self.mMouseEventListener = listener

    def mouseMoveEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.mouseMoveEvent(event)
        return QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.mousePressEvent(event)
        return QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.mouseReleaseEvent(event)
        return QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

    def leaveEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.leaveEvent(event)
        return QtWidgets.QGraphicsView.leaveEvent(self, event)

    def enterEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.enterEvent(event)
        return QtWidgets.QGraphicsView.enterEvent(self, event)

    def dragEnterEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.dragEnterEvent(event)
        return QtWidgets.QGraphicsView.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.dragLeaveEvent(event)
        return QtWidgets.QGraphicsView.dragLeaveEvent(self, event)

    def dragMoveEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.dragMoveEvent(event)
        return QtWidgets.QGraphicsView.dragMoveEvent(self, event)

    def dropEvent(self, event):
        if self.mMouseEventListener:
            self.mMouseEventListener.dropEvent(event)
        return QtWidgets.QGraphicsView.dropEvent(self, event)

    def setNoWheel(self):
        self.mNoWheel = True

    def _setWheelZoomFunc(self, zoom_func):
        self.mWheelZoomF = zoom_func

    def wheelEvent(self, event):
        if self.mNoWheel:
            return None
        if self.mWheelZoomF and bool(event.modifiers() & QtCore.Qt.CTRL):
            self.mWheelZoomF(getWheelDelta(event), event.pos())
            return event.accept()
        return QtWidgets.QGraphicsView.wheelEvent(self, event)

#===================================
class Label(QtWidgets.QLabel):
    def __init__(self, parent):
        QtWidgets.QLabel.__init__(self, parent)
        self.mMousePressF        = None

    def _setMousePressFunc(self, mouse_press_func):
        self.mMousePressF = mouse_press_func

    def mousePressEvent(self, event):
        if self.mMousePressF:
            return self.mMousePressF(event)
        return QtWidgets.QLabel.mousePressEvent(self, event)

#===================================
class Widget(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.mMousePressF        = None

    def _setMousePressFunc(self, mouse_press_func):
        self.mMousePressF = mouse_press_func

    def mousePressEvent(self, event):
        if self.mMousePressF:
            return self.mMousePressF(event)
        return QtWidgets.QWidget.mousePressEvent(self, event)

#===================================
class WebPage(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, parent, name):
        QtWebEngineWidgets.QWebEnginePage.__init__(self, parent)
        self.mName = name

    def javaScriptAlert(self, security_origin, msg):
        print("JSAlert(%s): %s" % (self.mName, msg), file = sys.stderr)

    def javaScriptConsoleMessage(self,
            level, message, line_no, source_id):
        if (line_no is not None or source_id is not None):
            comp_data = '|' + str(source_id) + ':' + str(line_no)
        else:
            comp_data = ""
        print("JSConsole(%s%s): %s" % (self.mName, comp_data, message),
            file = sys.stderr)

#===================================
class WebView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent, name):
        QtWebEngineWidgets.QWebEngineView.__init__(self, parent)
        page = WebPage(self, name)
        self.setPage(page)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)

    def getZoomState(self):
        return int(self.zoomFactor() * 100)

    def setZoomState(self, zoom_state):
        self.mZoomState = max(25, min(500, zoom_state))
        self.setZoomFactor(zoom_state * .01)

#===================================
class Scintilla(Qsci.QsciScintilla):
    def __init__(self, parent):
        Qsci.QsciScintilla.__init__(self, parent)
        self.mWheelZoomF  = None
        self.mZoomState   = 0

    def setAutoZoom(self):
        self.mWheelZoomF = self.changeZoom

    def _setWheelZoomFunc(self, zoom_func):
        self.mWheelZoomF = zoom_func

    def getZoomState(self):
        return self.mZoomState

    def changeZoom(self, par):
        zoom_state = self.mZoomState
        if par > 0.:
            zoom_state += 1
        elif par < 0.:
            zoom_state -= 1
        else:
            return
        with RT_Guard():
            self.setZoomState(zoom_state)

    def setZoomState(self, zoom_state):
        self.mZoomState = min(20, max(-9, zoom_state))
        self.zoomTo(self.mZoomState)

    def wheelEvent(self, event):
        if self.mWheelZoomF and bool(event.modifiers() & QtCore.Qt.CTRL):
            self.mWheelZoomF(getWheelDelta(event))
            return event.accept()
        return Qsci.QsciScintilla.wheelEvent(self, event)

#===================================
