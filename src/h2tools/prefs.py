import os, json

from config.messenger import msg
from .utils import getExceptionValue, StoreHandler
from .keyboard import KeyboardSupport

#=================================
class PreferenceHandler:
    sDefaultProperties = {}

    def __init__(self, env, file_name,
            default_properties = None, no_save = False):
        self.mFileName  = env.getUIApp().getProfilePath(file_name)
        self.mProperties = None
        self.mNoSaveMode = no_save
        if default_properties is not None:
            self.sDefaultProperties = default_properties

        if not self._loadFile(env):
            self.mProperties = self.sDefaultProperties.copy()
            self._saveFile(env)
        else:
            self._checkKbd(env)

    def iterStdProperties(self):
        for key, val in self.sDefaultProperties.items():
            yield (key, self.mProperties.get(key, val))

    def getProperty(self, key):
        return self.mProperties.get(key)

    def _loadFile(self, env):
        if not os.path.exists(self.mFileName):
            return False

        try:
            with open(self.mFileName, "r", encoding = "utf-8") as inp:
                properties = json.loads(inp.read())
            assert isinstance(properties, dict)
            updated = False
            if "file-kbd" not in properties and "keyboard-file" in properties:
                properties["file-kbd"] = properties["keyboard-file"]
                del properties["keyboard-file"]
                updated = True
            for opt, val in self.sDefaultProperties.items():
                if opt not in properties:
                    properties[opt] = val
                    updated = True
            self.mProperties = properties
            if updated:
                self._saveFile(env)
            return True
        except Exception:
            getExceptionValue()
            env.postAlert(msg("file.preferences.bad"), level = 2)
            return False

    def _saveFile(self, env):
        if not self.mNoSaveMode:
            fout = StoreHandler(self.mFileName)
            print(json.dumps(self.mProperties, indent = 4, sort_keys = True,
                ensure_ascii = False), file = fout.mStream)
            fout.close()
        self._checkKbd(env)

    def _checkKbd(self, env):
        message = KeyboardSupport.checkKbdFile(
            env.getUIApp().getProfilePath(
                self.mProperties["file-kbd"]))
        if message is not None:
            env.postAlert(
                msg("keyboard.cfg.error") + "\n" + message)

    def update(self, values, env):
        self.mProperties.update(values)
        self._saveFile(env)
