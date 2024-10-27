import os
from collections import Counter
from .utils import fileCRC32
#===============================================
class _FileInfoHandler:
    def __init__(self, filename, size,
            timestamp = -1, version = -1, hash_code = None):
        self.mFileName  = filename
        self.mSize      = int(size)
        self.mTimeStamp = int(timestamp)
        self.mVersion   = int(version)
        self.mHashCode  = hash_code.upper() if hash_code else '-'
        self.mState     = ""

    def getFileName(self):
        return self.mFileName

    def getSize(self):
        return self.mSize

    def getTimeStamp(self):
        return self.mTimeStamp

    def getVersion(self):
        return self.mVersion()

    def getHashCode(self):
        return self.mHashCode

    def getState(self):
        return self.mState

    def setState(self, state):
        self.mState = state

    def check(self, other, cmp_timestamp = False):
        if ((self.mSize == other.mSize)
                and (min(self.mVersion, other.mVersion) < 0
                or self.mVersion == other.mVersion)
                and ('-' in [self.mHashCode, other.mHashCode]
                or self.mHashCode == other.mHashCode)):
            if cmp_timestamp:
                return (min(self.mTimeStamp, other.mTimeStamp) < 0
                    or self.mTimeStamp == other.mTimeStamp)
            return True
        return False

    def merge(self, other):
        if self.mTimeStamp < 0:
            self.mTimeStamp = other.mTimeStamp
        if self.mVersion < 0:
            self.mVersion = other.mVersion
        if self.mHashCode == '-':
            self.mHashCode = other.mHashCode

    def reportIt(self, output):
        print("%s\t%d\t%d\t%d\t%s" %
            (self.mFileName, self.mSize, self.mTimeStamp,
            self.mVersion, self.mHashCode), file = output)

    def reportState(self, output):
        print("%s\t%s\t%d\t%d\t%d\t%s" % (self.mState, self.mFileName,
            self.mSize, self.mTimeStamp, self.mVersion, self.mHashCode),
            file = output)

#===============================================
class FileInfoDirectory:
    def __init__(self, rep = None, kind = None):
        self.mFiles = dict()
        self.mFileList = []
        self.mKind = kind
        if rep is not None:
            self.loadList(rep)

    def loadFiles(self, file_dir, files, no_time = True, no_hash = False):
        for filename in files:
            self.loadFile(file_dir, filename, no_time, no_hash)

    def loadFile(self, file_dir, filename, no_time = True, no_hash = False):
        file_path = file_dir + "/" + filename
        hash_code = None if no_hash else fileCRC32(file_path)
        loc_info = os.stat(file_path)
        self.regFileEntry(filename, loc_info.st_size,
            -1 if no_time else loc_info.st_mtime, -1, hash_code)

    def regFileEntry(self, filename, size, timestamp = -1, version = -1,
            hash_code = None, add_to_list = True):
        assert filename not in self.mFiles
        self.mFiles[filename] = _FileInfoHandler(
            filename, size, timestamp, version, hash_code)
        if add_to_list:
            self.mFileList.append(filename)

    def loadList(self, rep):
        for line in rep.split('\n'):
            if not line:
                continue
            if line.startswith('#'):
                map_idx = [0] + [{"size": 1, "timestamp": 2,
                    "svn-version": 3, "crc32": 4}[field]
                    for field in line.strip().split('\t')[1:]]
                continue
            values = line.split()
            fields = [values[0], -1, -1, -1, None]
            for idx, val in enumerate(line.strip().split('\t')):
                fields[map_idx[idx]] = val
            self.regFileEntry(*fields)

    def getListSize(self):
        return len(self.mFileList)

    def getDirSize(self):
        return len(self.mFiles)

    def get(self, filename):
        return self.mFiles.get(filename)

    def iter(self):
        for filename in self.mFileList:
            yield self.mFiles[filename]

    def checkInfo(self, file_info, cmp_timestamp = False):
        the_info = self.mFiles.get(file_info.getFileName())
        if the_info is None:
            return False
        return the_info.check(file_info, cmp_timestamp)

    def compare(self, other, cmp_timestamp = False):
        is_ok = True
        for filename in self.mFileList:
            info1 = self.mFiles[filename]
            if info1.getState() == "ignore":
                continue
            info2 = other.get(filename)
            if info2 is None:
                is_ok = False
                info1.setState("item-drop")
            elif not info1.check(info2, cmp_timestamp):
                is_ok = False
                info1.setState("changed")
        return is_ok

    def merge(self, other):
        is_ok = True
        for filename in self.mFileList:
            info1 = self.mFiles[filename]
            info2 = other.get(filename)
            if info2 is None:
                is_ok = False
                info1.setState("item-drop")
            else:
                info1.merge(info2)
        return is_ok

    def reportList(self, output):
        print("##filename\tsize\ttimestamp\tsvn-version\tcrc32", file = output)
        for filename in self.mFileList:
            self.mFiles[filename].reportIt(output)

    def reportBadStates(self, output, max_lines = -1):
        print("##state\tfilename\tsize\ttimestamp\tsvn-version\tsrc32",
            file = output)
        cnt_rest = max_lines
        for filename in self.mFileList:
            f_info = self.mFiles[filename]
            f_state = f_info.getState()
            if not f_state or f_state == "ignore":
                continue
            cnt_rest -= 1
            if cnt_rest == 0:
                print("...and more", file = output)
                break
            f_info.reportState(output)
        counter = Counter([info.getState()
            for info in self.mFiles.values()])
        if "" in counter:
            del counter[""]
        print("Total:", " ".join(["%s %d" % (state, cnt)
            for state, cnt in sorted(counter.items())]),
            file = output)

#===============================================
