import sys, os, abc, json

from config.messenger import msg
from .utils import getExceptionValue, StoreHandler

#=========================================
class PersistPropertyRecord:
    sRecordConstructors = dict()

    @classmethod
    def _registerType(cls, name, constructor):
        cls.sRecordConstructors[name] = constructor

    @classmethod
    def create(cls, master, name, ctrl, stored_value):
        pp = cls.sRecordConstructors[name](master, ctrl)
        if stored_value is not None:
            try:
                pp.initValue(stored_value)
                pp.mValue = stored_value
            except Exception:
                print("Failed to set persistent property %s to %s" %
                    (name, ctrl.objectName()), file = sys.stderr)
                getExceptionValue()
        return pp

    def __init__(self, master, name, ctrl):
        self.mMaster = master
        self.mName = name
        self.mCtrl = ctrl

    @abc.abstractmethod
    def getValue(self):
        pass

    @abc.abstractmethod
    def initValue(self, value):
        pass

    def dumpData(self):
        return {
            "tp": self.mName,
            "value":  self.getValue(),
            "widget": self.mCtrl.objectName()}

#=========================================
class PersistProperty_Value(PersistPropertyRecord):
    def __init__(self, master, ctrl):
        PersistPropertyRecord.__init__(self, master, "value", ctrl)

    def getValue(self):
        return self.mCtrl.getValue()

    def initValue(self, value):
        self.mCtrl.setValue(value)


PersistPropertyRecord._registerType("value",
    PersistProperty_Value)

#=========================================
class PersistProperty_MemState(PersistPropertyRecord):
    def __init__(self, master, ctrl):
        PersistPropertyRecord.__init__(self, master, "state", ctrl)

    def getValue(self):
        return self.mCtrl.getMemState()[:]

    def initValue(self, value):
        self.mCtrl.setMemState(value)


PersistPropertyRecord._registerType("state",
    PersistProperty_MemState)

#=========================================
class PersistProperty_Checked(PersistPropertyRecord):
    def __init__(self, master, ctrl):
        PersistPropertyRecord.__init__(self, master, "checked", ctrl)

    def getValue(self):
        return not not self.mCtrl.isChecked()

    def initValue(self, value):
        self.mCtrl.setChecked(value)


PersistPropertyRecord._registerType("checked",
    PersistProperty_Checked)

#=========================================
class PersistProperty_ZoomState(PersistPropertyRecord):
    def __init__(self, master, ctrl):
        PersistPropertyRecord.__init__(self, master, "zoom", ctrl)

    def getValue(self):
        return int(self.mCtrl.getZoomState())

    def initValue(self, value):
        self.mCtrl.setZoomState(value)


PersistPropertyRecord._registerType("zoom",
    PersistProperty_ZoomState)

#=========================================
class PersistProperty_ColumnsSizes(PersistPropertyRecord):
    def __init__(self, master, ctrl):
        PersistPropertyRecord.__init__(self, master, "column-sizes", ctrl)

    def getValue(self):
        return self.mCtrl.getColSizesInfo()

    def initValue(self, value):
        self.mCtrl._initColSizes(value)


PersistPropertyRecord._registerType("column-sizes",
    PersistProperty_ColumnsSizes)

#=========================================
class PersistProperty_SplitSizes(PersistPropertyRecord):
    def __init__(self, master, ctrl):
        PersistPropertyRecord.__init__(self, master, "split-sizes", ctrl)

    def getValue(self):
        return self.mCtrl.getSplitSizes()

    def initValue(self, value):
        self.mCtrl.setSplitSizes(value)


PersistPropertyRecord._registerType("split-sizes",
    PersistProperty_SplitSizes)

#=========================================
class PersistProperty_ScreenRegion(PersistPropertyRecord):
    def __init__(self, master, ctrl):
        PersistPropertyRecord.__init__(self, master, "screen-region", ctrl)

    def getValue(self):
        width, height, left, top = self.mCtrl.getRegion()
        return [width, height, left, top]

    def initValue(self, val_seq):
        width, height, left, top = val_seq
        self.mCtrl.setRegion(width, height, left, top)


PersistPropertyRecord._registerType("screen-region",
    PersistProperty_ScreenRegion)

#=========================================
class UIPersistPropertiesHandler:
    def __init__(self, ui_application, no_save = False):
        self.mUIapp  = ui_application
        self.mFileName  = self.mUIapp.getProfilePath("h2-pp.js")
        self.mRecords   = []
        self.mToRestore = None
        self.mBadLoad   = False
        self.mBadSave   = False
        self.mNoSaveMode = no_save
        if os.path.exists(self.mFileName):
            try:
                self.mToRestore = {}
                with open(self.mFileName, "r", encoding = "utf=8") as inp:
                    records = json.loads(inp.read())
                for rec in records:
                    self.mToRestore[(rec["tp"], rec["widget"])] = rec["value"]
            except Exception:
                print("Persistent Properties file %s: fail to read" %
                    self.mFileName, file = sys.stderr)
                getExceptionValue()
                self.mStored = None
                self.mBadLoad = True

    def register(self, ctrl, persist):
        assert self.mToRestore is not False
        for tp in persist.split():
            stored_value = None
            if self.mToRestore is not None:
                stored_value = self.mToRestore.get((tp, ctrl.objectName()))
            self.mRecords.append(
                PersistPropertyRecord.create(self, tp, ctrl, stored_value))

    def keepState(self, env):
        self.mToRestore = False
        if self.mBadLoad:
            env.postAlert(msg("persist-ui.bad.load"), level = 2)
            self.mBadLoad = False

        if self.mBadSave:
            return None
        try:
            return self._keepState()
        except Exception:
            getExceptionValue()
            env.postAlert(msg("persist-ui.failed"), level = 3)
            self.mBadSave = True

    def _keepState(self):
        if self.mNoSaveMode:
            return True
        if os.path.exists(self.mFileName):
            with open(self.mFileName, "r", encoding = "utf=8") as inp:
                content0 = inp.read()
        else:
            content0 = None
        content1 = json.dumps([rec.dumpData() for rec in self.mRecords],
            indent = 4, sort_keys = True, ensure_ascii = False)
        if content0 == content1:
            return False
        fout = StoreHandler(self.mFileName)
        print(content1, file = fout.mStream)
        fout.close()
        return True
