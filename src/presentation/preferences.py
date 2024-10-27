from h2tools.tools_qt import qt_str
from presentation.dialog import DialogPresentation

#=================================
class Preferences_Dialog(DialogPresentation):
    def __init__(self, top_presentation):
        DialogPresentation.__init__(self,
            top_presentation, "preferences")

        self.mPreferenceH = self.getEnv().getPreferenceHandler()
        self.mInputs = {prop: self.getWidget("prefs-" + prop)
            for prop, _ in self.mPreferenceH.iterStdProperties()}
        self.mProperties = None

    def execute(self):
        for key, val in self.mPreferenceH.iterStdProperties():
            self.mInputs[key].setText(qt_str(val))
        ret = self._execute()
        if ret:
            self.mPreferenceH.update({key: ctrl.text().strip()
                for key, ctrl in self.mInputs.items()}, self.getEnv())

    def doAction(self, act):
        if act.isAction("prefs-edit-kbd"):
            self.getEnv().runExtEdit(
                self.getEnv().getUIApp().getProfilePath(
                    self.getEnv().getPreference("file-kbd")))
            act.done()
            return
