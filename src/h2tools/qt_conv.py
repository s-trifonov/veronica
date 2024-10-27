from PyQt5 import QtCore, QtWidgets

def convBoolean(value):
    return str(value).lower() in ("", "true", "1", "yes", "on")

#===================================
def getPolicy(node, key, default = None):
    return convPolicy(node.get(key, default))

#===================================
def convPolicy(value):
    return {
        "expanding":    QtWidgets.QSizePolicy.Expanding,
        "fixed":     QtWidgets.QSizePolicy.Fixed,
        "ignored":      QtWidgets.QSizePolicy.Ignored,
        "maximum":      QtWidgets.QSizePolicy.Maximum,
        "min-exp":      QtWidgets.QSizePolicy.MinimumExpanding,
        "minimum":      QtWidgets.QSizePolicy.Minimum,
        "preferred":    QtWidgets.QSizePolicy.Preferred}[value]

#===================================
def getOrientation(node, key, default = None):
    return {
        "horizontal":   QtCore.Qt.Horizontal,
        "vertical":  QtCore.Qt.Vertical}[node.get(key, default)]

#===================================
def getToolButtonStyle(node, key, default = None):
    return {
        "beside":   QtCore.Qt.ToolButtonTextBesideIcon,
        "follow":   QtCore.Qt.ToolButtonFollowStyle,
        "icon": QtCore.Qt.ToolButtonIconOnly,
        "text":     QtCore.Qt.ToolButtonTextOnly,
        "under":    QtCore.Qt.ToolButtonTextUnderIcon}[node.get(key, default)]

#===================================
def getTabPos(node, key, default = None):
    return {
        "east":         QtWidgets.QTabWidget.East,
        "north":     QtWidgets.QTabWidget.North,
        "south":        QtWidgets.QTabWidget.South,
        "west":         QtWidgets.QTabWidget.West}[node.get(key, default)]

#===================================
def convCorner(value):
    return {
        "bottom-left":  QtCore.Qt.BottomLeftCorner,
        "bottom-right": QtCore.Qt.BottomRightCorner,
        "top-left":  QtCore.Qt.TopLeftCorner,
        "top-right":    QtCore.Qt.TopRightCorner}[value]

#===================================
def convAlignment(value):
    if '|' in value:
        v1, q, v2 = value.partition('|')
        return convAlignment(v1) | convAlignment(v2)
    ret = {
        "bottom":   QtCore.Qt.AlignBottom,
        "center":   QtCore.Qt.AlignHCenter,
        "justify":  QtCore.Qt.AlignJustify,
        "left":  QtCore.Qt.AlignLeft,
        "right":    QtCore.Qt.AlignRight,
        "top":      QtCore.Qt.AlignTop,
        "vcenter":  QtCore.Qt.AlignVCenter,
        "whole":    0}[value]
    return QtCore.Qt.Alignment(ret)

#===================================
def convScrollBarPolicy(value):
    return {
        "flexible": QtCore.Qt.ScrollBarAsNeeded,
        "off":          QtCore.Qt.ScrollBarAlwaysOff,
        "on":            QtCore.Qt.ScrollBarAlwaysOn}[value]

#===================================
def convButtonRole(value):
    return {
        "accept":      QtWidgets.QDialogButtonBox.AcceptRole,
        "action":           QtWidgets.QDialogButtonBox.ActionRole,
        "apply":            QtWidgets.QDialogButtonBox.ApplyRole,
        "destructive":      QtWidgets.QDialogButtonBox.DestructiveRole,
        "help":             QtWidgets.QDialogButtonBox.HelpRole,
        "no":               QtWidgets.QDialogButtonBox.NoRole,
        "reject":           QtWidgets.QDialogButtonBox.RejectRole,
        "reset":            QtWidgets.QDialogButtonBox.ResetRole,
        "yes":              QtWidgets.QDialogButtonBox.YesRole}[value]

#===================================
def convCursor(value):
    return {
        "arrow":        QtCore.Qt.ArrowCursor,
        "buzy":             QtCore.Qt.BusyCursor,
        "closed-hand":      QtCore.Qt.ClosedHandCursor,
        "cross":            QtCore.Qt.CrossCursor,
        "dnd-copy":         QtCore.Qt.DragCopyCursor,
        "dnd-link":         QtCore.Qt.DragLinkCursor,
        "dnd-move":         QtCore.Qt.DragMoveCursor,
        "forbidden":        QtCore.Qt.ForbiddenCursor,
        "ibeam":            QtCore.Qt.IBeamCursor,
        "open-hand":        QtCore.Qt.OpenHandCursor,
        "pointing-hand":    QtCore.Qt.PointingHandCursor,
        "size-all":         QtCore.Qt.SizeAllCursor,
        "size-bdiag":       QtCore.Qt.SizeBDiagCursor,
        "size-fdiag":       QtCore.Qt.SizeFDiagCursor,
        "size-hor":         QtCore.Qt.SizeHorCursor,
        "size-ver":         QtCore.Qt.SizeVerCursor,
        "split-h":          QtCore.Qt.SplitHCursor,
        "split-v":          QtCore.Qt.SplitVCursor,
        "up_arrow":         QtCore.Qt.UpArrowCursor,
        "wait":             QtCore.Qt.WaitCursor,
        "whats-this":       QtCore.Qt.WhatsThisCursor}[value]

#===================================
def convSelection(value):
    return {
        "single": QtWidgets.QAbstractItemView.SingleSelection,
        "contiguous": QtWidgets.QAbstractItemView.ContiguousSelection,
        "extended": QtWidgets.QAbstractItemView.ExtendedSelection,
        "multi": QtWidgets.QAbstractItemView.MultiSelection,
        "none": QtWidgets.QAbstractItemView.NoSelection}[value]

#===================================
def convSelBehavior(value):
    return {
        "rows": QtWidgets.QAbstractItemView.SelectRows,
        "columns": QtWidgets.QAbstractItemView.SelectColumns,
        "items": QtWidgets.QAbstractItemView.SelectItems}[value]

