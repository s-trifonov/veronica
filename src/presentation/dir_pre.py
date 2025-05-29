#import sys
from PyQt5 import QtCore, QtWidgets

from h2tools.tools_qt import qt_str
from h2tools.runtime import RT_Guard
from model.img_h import ImageHandler

#=================================
class DirImagesPresentation:

    #==========================
    def getIcon(self, icon_name):
        return self.mTopPre.getEnv().getUIApp().getIcon(icon_name)

    #=================================
    def __init__(self, top_pre):
        self.mTopPre = top_pre

        self.mTreeWidget = self.mTopPre.getEnv().getWidget("dir-image-tree")
        self.mTreeWidget._setupCurrentItemChange(self.onChangeSelection)

#        self.mTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#        self.mTreeWidget.customContextMenuRequested.connect(
#            self.openContextMenu)
#
#        self.mContextMenu = QtWidgets.QMenu(self.mTreeWidget)
#        self.mContextActions = {}
#        for ctrl_id, name in (
#                ("mark-to-learn", "img.mark-to-learn"),):
#            action = QtWidgets.QAction(qt_str(msg(name)), None)
#            self.mTopPre.getEnv().getUICtrl()._mapAction(action,
#                "dir-" + ctrl_id, "triggered")
#            self.mContextActions[ctrl_id] = action
#            self.mContextMenu.addAction(action)
#        self.mContextMenu.aboutToShow.connect(self._checkContextMenu)

        self.mRoundCombo = self.mTopPre.getEnv().getWidget("dir-round")

        self.mCurRoundH = None
        self.mCurRoundVal = ""
        self.mItemsMap = None
        self.resetState()

    def setDisabled(self, value):
        for widget in (self.mTreeWidget, self.mRoundCombo):
            widget.setDisabled(value)

    def resetState(self):
        prev_sel = self.getSelection(False)
        if prev_sel is not None:
            prev_sel = prev_sel.getViewId()
        self.mCurRoundVal = self.mRoundCombo.getValue()
        self.mCurRoundH = self.mTopPre.getProject().getRound(
            self.mCurRoundVal)
        self.mTreeWidget.clear()
        self.mItemsMap = {}
        for dir_h in self.mTopPre.getProject().iterTopDirList():
            self._fillDirItems(dir_h)
        if prev_sel is not None:
            self.selectItem(prev_sel)

    def getCurRound(self):
        return self.mCurRoundH

    def selectItem(self, view_id):
        item = self.mItemsMap.get(view_id)
        if item is None:
            return

        dir_h = item.data(0, QtCore.Qt.UserRole)
        if isinstance(dir_h, ImageHandler):
            dir_h = dir_h.getDir()
        while dir_h is not None:
            if dir_h.getViewId() not in self.mItemsMap:
                return
            self.mItemsMap[dir_h.getViewId()].setExpanded(True)
            dir_h = dir_h.getParent()

        self.mTreeWidget.setCurrentItem(item)
        self.mTreeWidget.scrollToItem(item)

    def update(self):
        if self.mRoundCombo.getValue() != self.mCurRoundVal:
            self.resetState()

    def getSelection(self, check_image = True):
        item = self.mTreeWidget.currentItem()
        if item is not None:
            obj = item.data(0, QtCore.Qt.UserRole)
            if check_image and not isinstance(obj, ImageHandler):
                return None
            return obj
        return None

    def onChangeSelection(self):
        obj = self.getSelection()
        if obj is not None:
            with RT_Guard():
                self.mTopPre.setCurImage(obj)

#    def openContextMenu(self, position):
#        if self.getSelection() is not None:
#            self.mContextMenu.exec_(self.mTreeWidget.mapToGlobal(position))
#
#    def _checkContextMenu(self):
#        it = self.getSelection()
#        self.mContextActions["mark-to-learn"].setDisabled(it is None)

    def userAction(self, act):
#        if act.isAction("mark-to-learn"):
#            print("Marked")
#            act.done()
#            return

        if act.isAction("check-round"):
            self.mTopPre.getEnv().needsUpdate()
            act.done()
            return

    def updateImage(self, image_h):
        if image_h.getViewId() in self.mItemsMap:
            self._updateImage(self.mItemsMap[image_h.getViewId()], image_h)

    #=================================
    def _makeTreeDirItem(self, parent, dir_h):
        item = QtWidgets.QTreeWidgetItem(parent)
        item.setData(0, QtCore.Qt.UserRole, dir_h)
        item.setText(0, qt_str(dir_h.getDirName()))
        item.setIcon(0, self.getIcon("folder.png"))
        item.setText(1, qt_str("-"))
        #item.setIcon(1, inv_pre.getItemStateIcon(sect))
        item.setFlags(item.flags() & (~QtCore.Qt.ItemIsSelectable))
        self.mItemsMap[dir_h.getViewId()] = item
        return item

    def _makeTreeImageItem(self, parent, image_h):
        item = QtWidgets.QTreeWidgetItem(parent)
        self._updateImage(item, image_h)
        self.mItemsMap[image_h.getViewId()] = item
        return item

    def _updateImage(self, item, image_h):
        item.setData(0, QtCore.Qt.UserRole, image_h)
        item.setText(0, qt_str(image_h.getName()))

        l_status = image_h.getDir().getSmpSupport().getImageStatus(image_h)
        if l_status is None:
            l_icon = "image.png"
        else:
            l_icon = "image_ok.png" if l_status else"image_proc.png"
        item.setIcon(0, self.getIcon(l_icon))

        info_data = image_h.getAnnotationData(
            self.mTopPre.getProject().getRound("info"))
        info_str = ""
        if info_data is not None:
            info_str = info_data.get("mark", "")
            if "quality" in info_data:
                info_str += "Q" + str(info_data["quality"])
        item.setText(1, qt_str(info_str))

        item.setBackground(0,
            QtCore.Qt.yellow if image_h.hasErrors() else QtCore.Qt.white)


    #=================================
    def _fillDirItems(self, dir_h, parent=None):
        if parent is not None:
            dir_item = self._makeTreeDirItem(parent, dir_h)
        else:
            dir_item = self.mTreeWidget
        items = []
        for subdir_h in dir_h.getDirectories():
            if not subdir_h.isEmpty(self.mCurRoundH):
                items.append(self._fillDirItems(subdir_h, dir_item))
        smp_support = dir_h.getSmpSupport()
        smp_support.resetState()
        if smp_support.sameRound(self.mCurRoundH):
            for image_h in smp_support.getImages():
                items.append(self._makeTreeImageItem(dir_item, image_h))
        else:
            for image_h in dir_h.getImages():
                if image_h.hasAnnotation(self.mCurRoundH):
                    items.append(self._makeTreeImageItem(dir_item, image_h))
        if parent is None:
            self.mTreeWidget.addTopLevelItems(items)
            return None
        return dir_item

