import os, sys, traceback
from io import StringIO
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from nturl2path import pathname2url
from config.messenger import msg
from datetime import datetime
from binascii import crc32

#===================================================
class _H:
    sWINDOWS = sys.platform.lower().startswith("win")
    sWIN_DEFAULT_PATHEXT = (
        '.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC')

#=========Accurate store procedure============
class _BaseStoreHandler:
    def __init__(self, fname):
        self.mFName = fname
        if os.path.dirname(fname):
            self.mNewFile = (os.path.dirname(fname) + "/#"
                + os.path.basename(fname) + "#")
        else:
            self.mNewFile = "#" + os.path.basename(fname) + "#"
        if os.path.exists(self.mNewFile):
            os.remove(self.mNewFile)

    def close(self):
        backup_f = self.mFName + "~"
        if os.path.exists(backup_f):
            os.remove(backup_f)
        if os.path.exists(self.mFName):
            os.rename(self.mFName, backup_f)
        os.rename(self.mNewFile, self.mFName)


class StoreHandler(_BaseStoreHandler):
    def __init__(self, fname, binary_mode = False):
        _BaseStoreHandler.__init__(self, fname)
        if binary_mode:
            self.mStream = open(self.mNewFile, "wb")
        else:
            self.mStream = open(self.mNewFile, "w", encoding="utf-8")

    def close(self):
        self.mStream.close()
        _BaseStoreHandler.close(self)

def storeFile(fname, content):
    try:
        st = StoreHandler(fname)
        st.mStream.write(content)
        st.close()
    except Exception:
        raiseRuntimeError(msg("file.save", (fname, getExceptionValue())))

#================Zip archive================
class StoreArchiveHandler(_BaseStoreHandler):
    def __init__(self, fname):
        _BaseStoreHandler.__init__(self, fname)
        self.mArchive = ZipFile(self.mNewFile, 'w', ZIP_DEFLATED)

    def close(self):
        self.mArchive.close()
        _BaseStoreHandler.close(self)

    sReadAccessMask = int("444", 8) << 16

    def addFile(self, filename, content, timestamp = None):
        if timestamp:
            filename = ZipInfo(filename,
                datetime.fromtimestamp(timestamp).timetuple())
            filename.external_attr = self.sReadAccessMask
        self.mArchive.writestr(filename, content.encode('utf-8'))

    def writeFile(self, name, fname):
        self.mArchive.write(fname, name)

#================fILE url================
def makeFileURL(fname):
    ffname = os.path.abspath(fname)
    if _H.sWINDOWS:
        ffname = pathname2url(ffname)
    if ffname.startswith("///"):
        return "file:" + ffname
    return "file://" + ffname

#===========Exception handling================
def getExceptionValue():
    rep = StringIO()
    traceback.print_exc(file = rep, limit = 30)
    ret = rep.getvalue()
    rep.close()
    print("EXC:", ret, file = sys.stderr)
    return ret

def raiseRuntimeError(message):
    print("RUNTIME EXC:", str(message), file=sys.stderr)
    raise RuntimeError()

#===========================
class FileControlHandler:
    sPermanentIgnore = set()

    def __init__(self, fname, kind):
        self.mFName = fname
        self.mKind  = kind
        self.mTimestamp = None
        self.mQIgnore = False

    def getFName(self):
        return self.mFName

    def sameFName(self, fname):
        return self.mFName == fname

    def noFile(self):
        return self.mTimestamp is None

    def _getTimeStamp(self):
        if not os.path.exists(self.mFName):
            return None
        try:
            st = os.stat(self.mFName)
            if st.st_mtime:
                return st.st_mtime
            return st.ctime
        except Exception:
            return None

    def resetControl(self, keep_ignore = False):
        self.mTimestamp = self._getTimeStamp()
        if not keep_ignore:
            self.mQIgnore = False

    def clear(self):
        self.mTimestamp = None

    def hasConflict(self, should_exist = False):
        if self.mKind in self.sPermanentIgnore:
            return False
        if self.mQIgnore:
            return False
        if self._getTimeStamp() != self.mTimestamp:
            return True
        return should_exist and self.mTimestamp is None

    def setIgnore(self, permanent_mode):
        if permanent_mode:
            self.sPermanentIgnore.add(self.mKind)
        else:
            self.mQIgnore = True

#===========================
# Modification of http://bugs.python.org/file16441/which.py
# returns only one value instead of a generator
def which(file, mode = os.F_OK | os.X_OK):
    if os.path.exists(file) and os.access(file, mode):
        return file

    path = os.environ.get('PATH', os.defpath).split(os.pathsep)
    if _H.sWINDOWS:
        if '.' not in path:
            path.insert(0, '')

        # given the quite usual mess in PATH on Windows,
        # let's rather remove duplicates
        path, orig, seen = [], path, set()
        for dir_name in orig:
            if not dir_name.lower() in seen:
                path.append(dir_name)
                seen.add(dir_name.lower())

    pathext = ['']
    if _H.sWINDOWS:
        v_pathext = os.environ.get('PATHEXT', _H.sWIN_DEFAULT_PATHEXT)
        pathext += v_pathext.lower().split(os.pathsep)

    for dir_name in path:
        basepath = os.path.join(dir_name, file)
        for ext in pathext:
            fullpath = basepath + ext
            if os.path.exists(fullpath) and os.access(fullpath, mode):
                return fullpath
    return None

#===========================
def runSpawnCmd(the_cmd):
    args = the_cmd.split()[:]
    f_exe = which(args[0])
    if f_exe:
        args[0] = f_exe
    return os.spawnv(os.P_NOWAIT, args[0], args)

#===========================
class SubStepCounter:
    def __init__(self, env, sub_count, total_count):
        self.mEnv          = env
        self.mSubMax       = sub_count
        self.mTotalMax     = total_count
        self.mSubCounter   = 0
        self.mTotalCounter = 0

    def oneStep(self):
        self.mTotalCounter += 1
        while (self.mTotalCounter < self.mTotalMax
                and (self.mTotalCounter * self.mSubMax
                > self.mSubCounter * self.mTotalMax)):
            self.mSubCounter += 1
            self.mEnv.stepProgress()

    def finishUp(self):
        while self.mTotalCounter < self.mTotalMax:
            self.mTotalCounter += 1
            self.mEnv.stepProgress()

#===========================
def getOsDirName(name, level = 1):
    name = os.path.abspath(name)
    for _ in range(level):
        name = os.path.dirname(name)
    return name

def isWINDOWS():
    return _H.sWINDOWS


#===========================
_CHUNK_SIZE_ = 32768
def fileCRC32(fname):
    global _CHUNK_SIZE_
    with open(fname, "rb") as inp:
        crc = crc32(inp.read(_CHUNK_SIZE_))
        while True:
            chunk = inp.read(_CHUNK_SIZE_)
            if not chunk:
                break
            crc = crc32(chunk, crc)
    return "%08X" % (crc & 0xFFFFFFFF)

#===========================
def htmlResponse(title, content, css):
    ret = f'''<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <title>{title}</title>\n'''
    if css is not None:
        ret += f'''
    <link href="/help?subj={css}" rel="stylesheet"/>\n'''
    ret += f'''
  </head>
  <body>\n{content}\n</body>\n</doc>'''
    return ret
