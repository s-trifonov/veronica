import sys
from PyQt5 import QtCore, QtWidgets,  QtGui

from config.messenger import msg
from config.ver_cfg import Config
from config.qss import DefaultStyleCfg
from .tools_qt import qt_str
from .xmltrace import TracedXMLNode
from .xmlutils import (simpleLoadXML, isNode,
    nodeNoAttrs, nodeIsPure, nodeIsJustContainer)

import h2tools.qt_conv as qt_conv
import h2tools.qt_widgets as qt_widgets

#===================================
class UI_XultActivator:
    @staticmethod
    def _toIntSeq(txt, separator = ' '):
        return [int(s) for s in txt.split(separator)]

    def __init__(self, ui_master, trace_mode = True):
        self.mUI = ui_master
        self.mTraceMode = trace_mode
        top_doc = simpleLoadXML(
            self.mUI.getSrcPath(self.mUI.getName(), subdir = "xult",
                extension="xml"))

        top_node = top_doc.getroot()
        if self.mTraceMode:
            top_node = TracedXMLNode(top_node,
                filename = self.mUI.getName())

        self.mTop = self.activateWidget(top_node, None)

        if self.mTraceMode:
            top_node.reportProblems()

        #QtCore.QMetaObject.connectSlotsByName(self.mTop)

    def getTop(self):
        return self.mTop

    def activateWidget(self, node, parent):
        if not isNode(node):
            return None
        if node.get("ctx") is not None:
            if node.get("ctx") not in Config.UI_CONTEXTS:
                if self.mTraceMode:
                    node.deactivate()
                return None
        assert nodeIsJustContainer(node)
        ctrl = self._activateWidget(node, parent)
        if ctrl is not None and node.get("persist"):
            self.mUI._regPersistentProperties(ctrl, node.get("persist"))
        return ctrl

    def _activateWidget(self, node, parent):
        if node.tag == "insert":
            insert_doc = simpleLoadXML(
                self.mUI.getSrcPath(node.get("file"),
                subdir="ui", extension="xult"))
            insert_node = insert_doc.getroot()

            if self.mTraceMode:
                insert_node = TracedXMLNode(insert_node,
                    filename = node.get("file"))

            ctrl = self.activateWidget(insert_node, parent)

            if self.mTraceMode:
                insert_node.reportProblems()
            return ctrl

        if node.tag == "main":
            return self._activate_main(node, parent)
        if node.tag == "dialog":
            return self._activate_dialog(node, parent)
        if node.tag in ("vbox", "hbox", "grid", "form"):
            return self._activate_box(node, parent)

        if node.tag == "menu-bar":
            return self._activate_menubar(node, parent)
        if node.tag == "menu":
            return self._activate_menu(node, parent)
        if node.tag == "menu-action":
            return self._activate_menu_action(node, parent)
        if node.tag == "menu-separator":
            return self._activate_menu_separator(node, parent)
        if node.tag == "spacer":
            return self._activate_spacer(node, parent)
        if node.tag == "splitter":
            return self._activate_splitter(node, parent)
        if node.tag == "separator":
            return self._activate_separator(node, parent)
        if node.tag == "combo-box":
            return self._activate_combobox(node, parent)
        if node.tag == "list":
            return self._activate_list(node, parent)
        if node.tag == "combo-line-mem":
            return self._activate_comboline_mem(node, parent)
        if node.tag == "tool-button":
            return self._activate_toolbutton(node, parent)
        if node.tag == "tool-button-menu":
            return self._activate_toolbuttonmenu(node, parent)
        if node.tag == "tool-bar":
            return self._activate_toolbar(node, parent)
        if node.tag == "push-button":
            return self._activate_pushbutton(node, parent)
        if node.tag == "radio-button":
            return self._activate_radiobutton(node, parent)
        if node.tag == "check-box":
            return self._activate_checkbox(node, parent)
        if node.tag == "spin-box":
            return self._activate_spinbox(node, parent)
        if node.tag == "slider":
            return self._activate_slider(node, parent)
        if node.tag == "dial":
            return self._activate_dial(node, parent)
        if node.tag == "line-edit":
            return self._activate_lineedit(node, parent)
        if node.tag == "label":
            return self._activate_label(node, parent)
        if node.tag == "plain-text-edit":
            return self._activate_plaintextedit(node, parent)
        if node.tag == "scintilla":
            return self._activate_scintilla(node, parent)
        if node.tag == "tab-box":
            return self._activate_tabbox(node, parent)
        if node.tag == "tab":
            return self._activate_tab(node, parent)
        if node.tag == "status-bar":
            return self._activate_statusbar(node, parent)
        if node.tag == "progress-bar":
            return self._activate_progressbar(node, parent)
        if node.tag == "table-view":
            return self._activate_tableview(node, parent)
        if node.tag == "tree-widget-t":
            return self._activate_treewidget_t(node, parent)
        if node.tag == "tree-widget":
            return self._activate_treewidget(node, parent)
        if node.tag == "text-edit":
            return self._activate_textedit(node, parent)
        if node.tag == "web-view":
            return self._activate_webview(node, parent)
        if node.tag == "graphics-view":
            return self._activate_graphicsview(node, parent)
        if node.tag == "scroll-area":
            return self._activate_scroll_area(node, parent)
        if node.tag == "dialog-button-box":
            return self._activate_dialog_button_box(node, parent)

        print("Not used tag:", node.tag, file = sys.stderr)
        return None
        #raiseRuntimeError("XULT: Bad widget kind: %s" % node.tag)

    def _activate_main(self, node, parent):
        assert parent is None
        ctrl = qt_widgets.MainWindow(None)
        self._setupCtrl_Id(ctrl, node)
        ctrl.resize(int(node.get("width")),   int(node.get("height")))
        ctrl.move(int(node.get("screen-x")), int(node.get("screen-y")))
        if node.get("icon"):
            ctrl.setWindowIcon(self.mUI.getIcon(node.get("icon")))
        ctrl.setWindowTitle(qt_str(msg(node.get("title"))))
        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is None:
                continue
            elif isinstance(sub_ctrl, QtWidgets.QMenuBar):
                ctrl.setMenuBar(sub_ctrl)
            elif isinstance(sub_ctrl, QtWidgets.QStatusBar):
                ctrl.setStatusBar(sub_ctrl)
            else:
                assert False, nd
        return ctrl

    def _activate_dialog(self, node, parent):
        assert parent is None
        ctrl = qt_widgets.Dialog()
        self._setupCtrl_Id(ctrl, node)
        ctrl.resize(int(node.get("width")),   int(node.get("height")))
        ctrl.move(int(node.get("screen-x")), int(node.get("screen-y")))
        if node.get("icon"):
            ctrl.setWindowIcon(self.mUI.getIcon(node.get("icon")))
        if node.get("size-grip") is not None:
            ctrl.setSizeGripEnabled(
                qt_conv.convBoolean(node.get("size-grip")))
        ctrl.setWindowTitle(qt_str(msg(node.get("title"))))
        if node.get("layout"):
            self._activateLayout(ctrl,
                node.get("layout"), node)
        else:
            for nd in node.iterchildren():
                self.activateWidget(nd, ctrl)
        return ctrl

    def _activate_menubar(self, node, parent):
        ctrl = QtWidgets.QMenuBar(parent)
        self._setupCtrl_Id(ctrl, node)
        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is None:
                continue
            elif isinstance(sub_ctrl, QtWidgets.QMenu):
                ctrl.addAction(sub_ctrl.menuAction())
            else:
                assert False
        return ctrl

    def _activate_menu(self, node, parent):
        ctrl = QtWidgets.QMenu(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Title(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is None:
                continue
            elif isinstance(sub_ctrl, QtWidgets.QMenu):
                ctrl.addAction(sub_ctrl.menuAction())
            elif isinstance(sub_ctrl, QtWidgets.QAction):
                ctrl.addAction(sub_ctrl)
            else:
                assert False
        return ctrl

    def _activate_menu_separator(self, node, parent):
        assert nodeIsPure(node) and nodeNoAttrs(node)
        parent.addSeparator()

    def _activate_menu_action(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QAction(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Text(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_Command(ctrl, node, kind="triggered")
        if node.get("checkable"):
            ctrl.setCheckable(qt_conv.convBoolean(node.get("checkable")))
            if node.get("checked") is not None:
                ctrl.setChecked(qt_conv.convBoolean(node.get("checked")))
        return ctrl

    def _activate_spacer(self, node, parent):
        assert nodeIsPure(node)
        width  = int(node.get("width", "10"))
        height = int(node.get("height", "10"))
        ctrl = QtWidgets.QSpacerItem(width, height,
            qt_conv.getPolicy(node, "h-policy", "expanding"),
            qt_conv.getPolicy(node, "v-policy", "minimum"))
        self._setupCtrl_Options(ctrl, node)
        return ctrl

    def _activate_statusbar(self, node, parent):
        ctrl = QtWidgets.QStatusBar(parent)
        self._setupCtrl_Id(ctrl, node)
        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is None:
                continue
            stretch = 0
            if nd.get("stretch"):
                stretch = int(nd.get("stretch"))
            ctrl.addWidget(sub_ctrl, stretch)
        return ctrl

    def _activate_separator(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QFrame()
        if node.get("orient") == "horizontal":
            ctrl.setFrameShape(QtWidgets.QFrame.HLine)
        else:
            ctrl.setFrameShape(QtWidgets.QFrame.VLine)
        ctrl.setFrameShadow(QtWidgets.QFrame.Sunken)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        return ctrl

    def _activate_combobox(self, node, parent):
        items = []
        for nd in node.iterchildren():
            assert nd.tag == "item"
            item = [nd.get(key) for key in ("text", "image", "value")]
            if item[0] is None:
                label = nd.get("label")
                item[0] = qt_str(item[2] if label is None else label)
            else:
                item[0] = qt_str(msg(item[0]))
            if item[1] is not None:
                item[1] = self.mUI.getIcon(item[1])
            items.append(item)
        ctrl = qt_widgets.ComboBoxWithValues(parent, items,
            qt_conv.convBoolean(node.get("with-wrong", "false")),
            node.get("to-hide"))
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        ctrl.setEditable(qt_conv.convBoolean(node.get("editable", "false")))
        if node.get("value") is not None:
            ctrl.setValue(node.get("value"))
        self._setupCtrl_Command(ctrl, node, kind = "activated")
        if ctrl.isEditable():
            self._setupCtrl_Command(ctrl, node, kind = "editTextChanged")
        return ctrl

    def _activate_list(self, node, parent):
        items = []
        for nd in node.iterchildren():
            assert nd.tag == "item"
            item = [nd.get(key) for key in ("text", "image")]
            if item[0] is None:
                label = nd.get("label")
                item[0] = qt_str(item[2] if label is None else label)
            else:
                item[0] = qt_str(msg(item[0]))
            if item[1] is not None:
                item[1] = self.mUI.getIcon(item[1])
            items.append(item)
        ctrl = qt_widgets.ListWidget(parent, items,
            qt_conv.convBoolean(node.get("with-wrong", "false")))
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        if node.get("value") is not None:
            ctrl.setValue(node.get("value"))
        self._setupCtrl_Command(ctrl, node, kind = "itemActivated")
        return ctrl

    def _activate_comboline_mem(self, node, parent):
        assert nodeIsPure(node)
        ctrl = qt_widgets.ComboLineWithMemory(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        if not qt_conv.convBoolean(node.get("completer", "true")):
            ctrl.setCompleter(None)
        if node.get("enter") is not None:
            command = node.get("enter")
            ctrl.lineEdit().returnPressed.connect(
                lambda: self.mUI.action(command))
        self._setupCtrl_Command(ctrl, node, kind = "editTextChanged")
        return ctrl

    def _activate_pushbutton(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QPushButton(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Text(ctrl, node)
        self._setupCtrl_Icon(ctrl, node, supctrl = ctrl)
        kind = "pressed"
        if node.get("checkable"):
            kind = "toggled"
            ctrl.setCheckable(qt_conv.convBoolean(node.get("checkable")))
            if node.get("checked") is not None:
                ctrl.setChecked(qt_conv.convBoolean(node.get("checked")))
        self._setupCtrl_Command(ctrl, node, kind = kind)
        return ctrl

    def _activate_radiobutton(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QRadioButton(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Text(ctrl, node)
        self._setupCtrl_Icon(ctrl, node, supctrl = ctrl)
        if node.get("checked") is not None:
            ctrl.setChecked(qt_conv.convBoolean(node.get("checked")))
        self._setupCtrl_Command(ctrl, node, kind = "toggled")
        return ctrl

    def _activate_toolbuttonmenu(self, node, parent):
        assert nodeIsPure(node)
        ctrl = qt_widgets.ToolButtonMenu(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        if node.get("style"):
            ctrl.setToolButtonStyle(
                qt_conv.getToolButtonStyle(node, "style"))
        self._setupCtrl_Icon(ctrl, node)
        return ctrl

    def _activate_toolbutton(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QToolButton(parent)
        action = QtWidgets.QAction(ctrl)
        self._setupCtrl_Id(action, node)
        self._setupCtrl_Options(ctrl, node, False)
        self._setupCtrl_VOptions(action, node)
        self._setupCtrl_ToolTip(action, node)
        if node.get("style"):
            ctrl.setToolButtonStyle(
                qt_conv.getToolButtonStyle(node, "style"))
        self._setupCtrl_Text(action, node)
        self._setupCtrl_Icon(action, node, supctrl = ctrl)
        if node.get("checkable"):
            ctrl.setCheckable(qt_conv.convBoolean(node.get("checkable")))
            if node.get("checked") is not None:
                ctrl.setChecked(qt_conv.convBoolean(node.get("checked")))
        self._setupCtrl_Command(action, node, kind = "triggered")
        ctrl.setDefaultAction(action)
        return ctrl

    def _activate_toolbar(self, node, parent):
        ctrl = QtWidgets.QToolBar(parent)
        self._setupCtrl_Id(ctrl, node)
        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is not None:
                ctrl.addWidget(sub_ctrl)
        return ctrl

    def _activate_checkbox(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QCheckBox(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Text(ctrl, node)
        self._setupCtrl_Icon(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        if node.get("checked") is not None:
            ctrl.setChecked(qt_conv.convBoolean(node.get("checked")))
        self._setupCtrl_Command(ctrl, node, kind = "stateChanged")
        return ctrl

    def _activate_spinbox(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QSpinBox(parent)
        self._setupCtrl_Id(ctrl, node)
        if node.get("value"):
            ctrl.setValue(int(node.get("value")))
        if node.get("min"):
            ctrl.setMinimum(int(node.get("min")))
        if node.get("max"):
            ctrl.setMaximum(int(node.get("max")))
        self._setupCtrl_Icon(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        if node.get("checked") is not None:
            ctrl.setChecked(qt_conv.convBoolean(node.get("checked")))
        self._setupCtrl_Command(ctrl, node, kind = "valueChanged")
        return ctrl

    def _activate_slider(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QSlider(
            QtCore.Qt.Horizontal if node.get("orient") == "horizontal"
            else QtCore.Qt.Vertical,
            parent)
        self._setupCtrl_Id(ctrl, node)
        if node.get("value"):
            ctrl.setValue(int(node.get("value")))
        if node.get("min"):
            ctrl.setMinimum(int(node.get("min")))
        if node.get("max"):
            ctrl.setMaximum(int(node.get("max")))
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_Command(ctrl, node, kind = "valueChanged")
        return ctrl

    def _activate_dial(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QDial(parent)
        self._setupCtrl_Id(ctrl, node)
        if node.get("value"):
            ctrl.setValue(int(node.get("value")))
        if node.get("min"):
            ctrl.setMinimum(int(node.get("min")))
        if node.get("max"):
            ctrl.setMaximum(int(node.get("max")))
        self._setupCtrl_Icon(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        if node.get("checked") is not None:
            ctrl.setChecked(qt_conv.convBoolean(node.get("checked")))
        self._setupCtrl_Command(ctrl, node, kind = "valueChanged")
        return ctrl

    def _activate_label(self, node, parent):
        #assert nodeIsPure(node)
        ctrl = qt_widgets.Label(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Text(ctrl, node)
        if node.get("image") is not None:
            ctrl.setPixmap(self.mUI.getPixmap(node.get("image")))
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        if node.get("align") is not None:
            ctrl.setAlignment(qt_conv.convAlignment(node.get("align")))
        if node.get("wrap") is not None:
            ctrl.setWordWrap(qt_conv.convBoolean(node.get("wrap")))
        if node.get("rtf") is not None:
            ctrl.setTextFormat(1)

        return ctrl

    def _activate_lineedit(self, node, parent):
        assert nodeIsPure(node)
        ctrl = QtWidgets.QLineEdit(parent)
        self._setupCtrl_Id(ctrl, node)
        if node.get("value") is not None:
            ctrl.setText(qt_str(node.get("value")))
        self._setupCtrl_Icon(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        if node.get("enter") is not None:
            command = node.get("enter")
            ctrl.returnPressed.connect(lambda: self.mUI.action(command))
        self._setupCtrl_Command(ctrl, node, kind = "textEdited")
        return ctrl

    def _activate_plaintextedit(self, node, parent):
        ctrl = qt_widgets.PlainTextEdit(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_Command(ctrl, node, kind = "textChanged")
        return ctrl

    def _activate_splitter(self, node, parent):
        ctrl = qt_widgets.Splitter(parent)
        if node.get("orient") == "horizontal":
            ctrl.setOrientation(QtCore.Qt.Horizontal)
        else:
            ctrl.setOrientation(QtCore.Qt.Vertical)
        self._setupCtrl_Id(ctrl, node)
        if node.get("handle-width"):
            ctrl.setHandleWidth(int(node.get("handle-width")))
        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is not None:
                ctrl.addWidget(sub_ctrl)
        if node.get("items-stretch"):
            for idx, st in enumerate(node.get("items-stretch").split()):
                ctrl.setStretchFactor(idx, int(st))
        ctrl.setup(qt_conv.convBoolean(node.get("care-hidden", "false")))
        return ctrl

    def _activate_tabbox(self, node, parent):
        ctrl = qt_widgets.TabBox(parent)
        ctrl.setTabPosition(
            qt_conv.getTabPos(node, "position", "north"))
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)

        self._setupCtrl_Command(ctrl, node, kind = "currentChanged")

        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            assert sub_ctrl is None

        if node.get("cur-idx"):
            ctrl.setCurrentIndex(int(node.get("cur-idx")))
        return ctrl

    def _activate_tab(self, node, parent):
        ctrl = qt_widgets.TabWidget(parent)
        self._setupCtrl_Id(ctrl, node)
        layout = self._activateLayout(ctrl,
            node.get("layout", "grid"), node)
        ctrl.setLayout(layout)
        ctrl.activate()
        self._setupCtrl_Text(ctrl, node)
        self._setupCtrl_Icon(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)

    def _activate_progressbar(self, node, parent):
        assert nodeIsPure(node)
        ctrl = qt_widgets.ProgressBar(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        if node.get("range") is not None:
            ctrl.setRange(*self._toIntSeq(node.get("range")))
        if node.get("value") is not None:
            ctrl.setValue(int(node.get("value")))
        return ctrl

    @staticmethod
    def _collect_columns(node):
        col_names = []
        for nd in node.iterchildren():
            assert nd.tag == "column"
            if nd.get("text"):
                col_names.append(qt_str(msg(nd.get("text"))))
            elif nd.get("label") is not None:
                col_names.append(qt_str(nd.get("label")))
            else:
                col_names.append(qt_str(""))
        return col_names

    def _activate_tableview(self, node, parent):
        ctrl = qt_widgets.TableView(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ScrollBars(ctrl, node)
        row_height = int(node.get("row-height",
            DefaultStyleCfg.TABLE_ROW_HEIGTH))
        ctrl.verticalHeader().setDefaultSectionSize(row_height)
        if node.get("no-alt-row-colors") is None:
            ctrl.setAlternatingRowColors(True)
        ctrl.setShowGrid(qt_conv.convBoolean(node.get("grid", "true")))

        col_names = self._collect_columns(node)
        model = QtGui.QStandardItemModel(0, len(col_names), ctrl)
        for idx, col_name in enumerate(col_names):
            model.setHeaderData(idx, QtCore.Qt.Horizontal, col_name)
        ctrl.setModel(model)
        ctrl.horizontalHeader().setStretchLastSection(True)
        ctrl.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        ctrl.verticalHeader().setHidden(True)
        ctrl.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        if not any(col_names):
            ctrl.horizontalHeader().setHidden(True)
        ctrl.setSelectionModel(QtCore.QItemSelectionModel(model))
        ctrl.setSelectionMode(qt_conv.convSelection(
            node.get("selection", "single")))
        ctrl.setSelectionBehavior(qt_conv.convSelBehavior(
            node.get("behavior", "rows")))
        return ctrl

    def _activate_treewidget(self, node, parent):
        ctrl = qt_widgets.TreeWidget(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ScrollBars(ctrl, node)
        col_names = self._collect_columns(node)
        ctrl.setHeaderLabels(col_names)

        ctrl.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        ctrl.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)

        header_view = QtWidgets.QHeaderView(QtCore.Qt.Horizontal, ctrl)
        ctrl.setHeader(header_view)
        if node.get("section-size"):
            header_view.setDefaultSectionSize(int(node.get("section-size")))
        if node.get("main-column-no") is not None:
            idx = int(node.get("main-column-no"))
            if idx > 0:
                header_view.moveSection(0, idx)
            else:
                ctrl.setColumnHidden(0, True)
        if node.get("wide-contents") is not None:
            header_view.setSectionResizeMode(
                QtWidgets.QHeaderView.ResizeToContents)
            header_view.setStretchLastSection(False)
        else:
            header_view.setStretchLastSection(True)

        if not any(col_names):
            header_view.setHidden(True)
        return ctrl

    def _activate_treewidget_t(self, node, parent):
        ctrl = qt_widgets.TreeWidget(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ScrollBars(ctrl, node)
        return ctrl

    def _activate_graphicsview(self, node, parent):
        ctrl = qt_widgets.GraphicsView(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ScrollBars(ctrl, node)
        return ctrl

    def _activate_textedit(self, node, parent):
        ctrl = QtWidgets.QTextEdit(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ScrollBars(ctrl, node)
        return ctrl

    def _activate_scintilla(self, node, parent):
        assert qt_widgets.SCINTILLA_AWAILABLE, (
            "Use QScintilla package to access widget")
        ctrl = qt_widgets.Scintilla(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Command(ctrl, node, kind = "textChanged")
        return ctrl

    def _activate_scroll_area(self, node, parent):
        ctrl = QtWidgets.QScrollArea(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ScrollBars(ctrl, node)
        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is not None:
                ctrl.setWidget(sub_ctrl)
                break
        return ctrl

    def _activate_webview(self, node, parent):
        ctrl = qt_widgets.WebView(parent, node.get("id"))
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ScrollBars(ctrl, node)
        if node.get("src"):
            url = self.mUI.getURL_BaseDir() + "/ui/" + node.get("src")
            ctrl.load(QtCore.QUrl(url))
        return ctrl

    def _activate_dialog_button_box(self, node, parent):
        ctrl = QtWidgets.QDialogButtonBox(parent)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        if node.get("orient") == "vertical":
            ctrl.setOrientation(QtCore.Qt.Vertical)

        for nd in node.iterchildren():
            assert nd.tag == "dialog-button"
            btn = ctrl.addButton(qt_str(msg(nd.get("text"))),
                qt_conv.convButtonRole(nd.get("role")))
            self._setupCtrl_Id(btn, nd)
            self._setupCtrl_Command(btn, nd, kind = "pressed")
            self._setupCtrl_ToolTip(btn, nd)

        ctrl.accepted.connect(parent.accept)
        ctrl.rejected.connect(parent.reject)
        return ctrl

    #===================================
    def _activate_box(self, node, parent):
        if node.get("scrolling"):
            vv = node.get("scrolling").split()
            ctrl = QtWidgets.QScrollArea(parent)
            ctrl.setWidgetResizable(vv[2] == "resizable")
            ctrl.setHorizontalScrollBarPolicy(
                qt_conv.convScrollBarPolicy(vv[0]))
            ctrl.setVerticalScrollBarPolicy(
                qt_conv.convScrollBarPolicy(vv[1]))
            if node.get("listen"):
                widget = qt_widgets.Widget(ctrl)
            else:
                widget = QtWidgets.QWidget(ctrl)
            ctrl.setWidget(widget)
            #widget = ctrl
        else:
            if node.get("listen"):
                ctrl = qt_widgets.Widget(parent)
            else:
                ctrl = QtWidgets.QWidget(parent)
            widget = ctrl
        layout = self._activateLayout(widget, node.tag, node)
        widget.setLayout(layout)
        self._setupCtrl_Id(ctrl, node)
        self._setupCtrl_Options(ctrl, node)
        self._setupCtrl_ToolTip(ctrl, node)

        placement = node.get("placement")
        if placement == "central":
            parent.setCentralWidget(ctrl)
            return None
        if placement == "permanent":
            parent.addPermanentWidget(ctrl)
            return None
        if placement and placement.startswith("corner-"):
            parent.setCornerWidget(ctrl,
                qt_conv.convCorner(placement[7:]))
            return None
        return ctrl

    #===================================
    def _activateLayout(self, ctrl, mode, node):
        if mode in ("hbox", "vbox"):
            layout = self._activateBoxLayout(ctrl, mode, node)
        elif mode == "form":
            layout = self._activateFormLayout(ctrl, node)
        elif mode == "grid":
            layout = self._activateGridLayout(ctrl, node)
        else:
            assert False

        margins = DefaultStyleCfg.LAYOUT_MARGINS
        if node.get("layout-margins"):
            margins = self._toIntSeq(node.get("layout-margins"))
            if len(margins) < 4:
                margins *= 4
        layout.setContentsMargins(*margins)

        layout.setSpacing(int(
            node.get("spacing", DefaultStyleCfg.SPACING)))

        return layout

    #===================================
    def _activateBoxLayout(self, ctrl, mode, node):
        if mode == "hbox":
            layout = QtWidgets.QHBoxLayout(ctrl)
        elif mode == "vbox":
            layout = QtWidgets.QVBoxLayout(ctrl)
        else:
            assert False

        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is None:
                continue
            if isinstance(sub_ctrl, QtWidgets.QSpacerItem):
                layout.addSpacerItem(sub_ctrl)
                continue
            alignment = qt_conv.convAlignment(nd.get("align", "whole"))
            if isinstance(sub_ctrl, QtWidgets.QLayout):
                layout.addLayout(sub_ctrl, 0, alignment)
            else:
                layout.addWidget(sub_ctrl, 0, alignment)

        if node.get("items-stretch"):
            for idx, st in enumerate(node.get("items-stretch").split()):
                layout.setStretch(idx, int(st))
        return layout

    #===================================
    def _activateGridLayout(self, ctrl, node):
        layout = QtWidgets.QGridLayout(ctrl)

        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is None:
                continue
            alignment = qt_conv.convAlignment(nd.get("align", "whole"))
            place = nd.get("place")
            if not place:
                row, row_span, col, col_span = 0, 1, 0, 1
            else:
                pp = place.split()
                if '-' in pp[0]:
                    row, r1 = self._toIntSeq(pp[0], '-')
                    row_span = r1 - row + 1
                else:
                    row, row_span = int(pp[0]), 1
                if '-' in pp[1]:
                    col, c1 = self._toIntSeq(pp[1], '-')
                    col_span = c1 - col + 1
                else:
                    col, col_span = int(pp[1]), 1

            if isinstance(sub_ctrl, QtWidgets.QLayout):
                layout.addLayout(sub_ctrl, row, col,
                    row_span, col_span, alignment)
            else:
                layout.addWidget(sub_ctrl,  row, col,
                    row_span, col_span, alignment)

        if node.get("columns-stretch"):
            for idx, st in enumerate(node.get("columns-stretch").split()):
                layout.setColumnStretch(idx, int(st))
        if node.get("rows-stretch"):
            for idx, st in enumerate(node.get("rows-stretch").split()):
                layout.setRowStretch(idx, int(st))
        return layout

    #===================================
    def _activateFormLayout(self, ctrl, node):
        layout = QtWidgets.QFormLayout(ctrl)

        label_style = node.get("label-style")

        for nd in node.iterchildren():
            sub_ctrl = self.activateWidget(nd, ctrl)
            if sub_ctrl is None:
                continue
            title = nd.get("title")
            if title is not None:
                layout.addRow(qt_str(msg(title)), sub_ctrl)
            else:
                layout.addRow(sub_ctrl)
            if label_style is not None:
                label_ctr = layout.labelForField(sub_ctrl)
                if label_ctr is not None:
                    label_ctr.setStyleSheet(label_style)

        if node and node.get("vspacing"):
            layout.setVerticalSpacing(int(node.get("vspacing")))
        if node and node.get("label-align"):
            alignment = qt_conv.convAlignment(nd.get("label-align"))
            layout.setLabelAlignment(alignment)
        return layout

    #===================================
    def _setupCtrl_Id(self, ctrl, node):
        ui_id = node.get("id")
        if not ui_id:
            return
            #ui_id = self.mUI._getTechWidgetId(node.tag)
        assert ui_id not in self.mUI.mWidgets
        ctrl.setObjectName(ui_id)
        self.mUI.mWidgets[ui_id] = ctrl

    def _setupCtrl_Title(self, ctrl, node, attr = "title"):
        if node.get(attr) is not None:
            title = qt_str(msg(node.get(attr)))
            ctrl.setTitle(title)

    def _setupCtrl_Text(self, ctrl, node, attr = "text", alt_attr = "label"):
        if node.get(attr) is not None:
            text = qt_str(msg(node.get(attr)))
            ctrl.setText(text)
        elif node.get(alt_attr) is not None:
            ctrl.setText(qt_str(node.get(alt_attr)))

    def _setupCtrl_Icon(self, ctrl, node, attr = "text", supctrl = None):
        if node.get("image"):
            ctrl.setIcon(self.mUI.getIcon(node.get("image")))
            if node.get("img-size") is not None:
                w, h = self._toIntSeq(node.get("img-size"))
                (supctrl if supctrl else ctrl).setIconSize(QtCore.QSize(w, h))

    def _setupCtrl_ToolTip(self, ctrl, node):
        if node.get("tooltip") is not None:
            text = qt_str(msg(node.get("tooltip")))
            ctrl.setToolTip(text)

    def _setupCtrl_VOptions(self, ctrl, node):
        disabled = node.get("disabled")
        if disabled is not None:
            ctrl.setDisabled(qt_conv.convBoolean(disabled))
        hidden = node.get("hidden")
        if hidden is not None:
            ctrl.setHidden(qt_conv.convBoolean(hidden))

    def _setupCtrl_Options(self, ctrl, node, setup_voptions = True):
        if setup_voptions:
            self._setupCtrl_VOptions(ctrl, node)
        if isinstance(ctrl, QtWidgets.QWidget):
            margins = DefaultStyleCfg.WIDGET_MARGINS
            if node.get("margins"):
                margins = self._toIntSeq(node.get("margins"))
                if len(margins) < 4:
                    margins *= 4
            ctrl.setContentsMargins(*margins)
        if node.get("fixed-width"):
            ctrl.setFixedWidth(int(node.get("fixed-width")))
        if node.get("fixed-height"):
            ctrl.setFixedHeight(int(node.get("fixed-height")))
        if node.get("max-size"):
            ctrl.setMaximumSize(int(node.get("max-size")))
        if node.get("min-width"):
            ctrl.setMinimumWidth(int(node.get("min-width")))
        if node.get("min-height"):
            ctrl.setMinimumHeight(int(node.get("min-height")))
        if node.get("max-height"):
            ctrl.setMaximumHeight(int(node.get("max-height")))
        if node.get("min-size"):
            ctrl.setMinimumSize(int(node.get("min-size")))
        if node.get("size-policy"):
            p = node.get("size-policy").split()
            ctrl.setSizePolicy(
                qt_conv.convPolicy(p[0]),
                qt_conv.convPolicy(p[1]))
        if node.get("icon-size"):
            w, h = self._toIntSeq(node.get("icon-size"))
            ctrl.setIconSize(QtCore.QSize(w, h))
        if node.get("style") is not None:
            style_text = node.get("style")
            ctrl.setStyleSheet(style_text)
        if node.get("sclass") is not None:
            ctrl.setProperty("sclass", node.get("sclass"))
        if node.get("cursor"):
            ctrl.setCursor(qt_conv.convCursor(node.get("cursor")))

    def _setupCtrl_Command(self, ctrl, node, kind):
        if node.get("command") is not None:
            command = node.get("command")
            self.mUI._mapAction(ctrl, command, kind)

    def _setupCtrl_Orientation(self, ctrl, node):
        if node.get("orientation"):
            ctrl.setOrientation(
                qt_conv.getOrientation(node, "orientation"))

    def _setupCtrl_ScrollBars(self, ctrl, node):
        if node.get("scroll-bars"):
            vv = node.get("scroll-bars").split()
            ctrl.setHorizontalScrollBarPolicy(
                qt_conv.convScrollBarPolicy(vv[0]))
            ctrl.setVerticalScrollBarPolicy(
                qt_conv.convScrollBarPolicy(vv[1]))
