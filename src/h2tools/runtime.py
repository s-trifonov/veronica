import sys
from threading import RLock

from config.ver_cfg import Config
from .utils import getExceptionValue

#================================
class RT_Guard:
    def __init__(self, canceled = None):
        self.mCheckId  = None
        self.mCanceled = canceled

    @staticmethod
    def isFree():
        return not RuntimeEnvironment.isCheckedIn()

    @classmethod
    def freeze(cls):
        if cls.isFree():
            return RT_Guard()
        return NoGuard()

    @classmethod
    def syncro(cls):
        return RuntimeEnvironment.getLock()

    def __enter__(self):
        if self.mCanceled is not None:
            self.mCanceled = False
        self.mCheckId = RuntimeEnvironment.checkin()

    def __exit__(self, tp, value, traceback):
        if tp is not None:
            if Config.DEBUG_MODE:
                getExceptionValue()
            if self.mCanceled is not None:
                self.mCanceled[0] = True
        RuntimeEnvironment.checkout(self.mCheckId)
        self.mCheckId = None

#================================
class NoGuard:
    def __enter__(self):
        pass

    def __exit__(self, tp, value, traceback):
        pass

#================================
def _dummyRunning(is_running):
    return None
def _dummyLoop():
    return None
def _dummyIdle():
    return None
def _dummyChOut():
    return None
#================================

class RT_Host:
    def __init__(self):
        self.mInform_F     = _dummyRunning
        self.mLoop_F       = _dummyLoop
        self.mIdle_F       = _dummyIdle
        self.mChOut_F      = _dummyChOut
        self.mMode         = 0
        self.mCID_Count    = 0
        self.mCID_Stack    = None
        self.mIdleHandlers = []
        self.mInLoop       = False
        self.mLock         = RLock()
        self.mIdleCount    = 0

    def setup(self, idle_f, loop_f, inform_f, checkout_f):
        self.mIdle_F     = idle_f
        self.mLoop_F     = loop_f
        self.mInform_F   = inform_f
        self.mChOut_F    = checkout_f
        self.mMode       = 0
        self.mCID_Stack  = []

    def _informStatus(self):
        self.mInform_F(len(self.mCID_Stack) > 0 or self.mMode < 0
            or len(self.mIdleHandlers) > 0)

    def getMode(self):
        return self.mMode

    def isStarted(self):
        return self.mMode != 0

    def isGoingQuit(self):
        return self.mMode < 0

    def isWithIdle(self):
        return self.mMode > 1

    def getLock(self):
        return self.mLock

    def registerIdleHandler(self, handler):
        if handler not in self.mIdleHandlers:
            self.mIdleHandlers.append(handler)
            self.mIdleHandlers.sort(key =
                lambda h: h.getIdlePriority())

    def unregisterIdleHandler(self, handler):
        if handler in self.mIdleHandlers:
            self.mIdleHandlers.remove(handler)

    def _idlePing(self):
        if self.mMode > 1 and len(self.mIdleHandlers):
            self.mIdle_F()

    def startSession(self, use_idle):
        self.mMode = 2 if use_idle else 1
        self._idlePing()

    def goQuit(self):
        self.mMode = -1

    def checkin(self):
        self.mLock.acquire()
        if len(self.mCID_Stack) != 0:
            assert False
        cid = self.mCID_Count
        self.mCID_Count += 1
        self.mCID_Stack.append(cid)
        self._informStatus()
        return cid

    def checkout(self, check_id):
        self.mChOut_F()
        cid = self.mCID_Stack.pop()
        if cid != check_id:
            print("Improper runtime checkin/checkout!", cid, check_id,
                file = sys.stderr)
            assert False
        if self.mMode > 1:
            self._idlePing()
        self._informStatus()
        self.mLock.release()

    def isCheckedIn(self):
        return len(self.mCID_Stack) > 0

    def dropIdleCount(self):
        self.mIdleCount = 0

    def idleEvent(self):
        if (self.mMode <= 1 or len(self.mIdleHandlers) == 0
                or len(self.mCID_Stack) > 0):
            self._informStatus()
            return
        self.mIdleCount += 1
        if self.mIdleCount > 100:
            idle_handler = self.mIdleHandlers[0]
            done = False
            with RT_Guard():
                done = idle_handler.onIdle()
            if done and idle_handler in self.mIdleHandlers:
                self.mIdleHandlers.remove(idle_handler)
        self._idlePing()
        self._informStatus()

    def doWaitEvents(self, use_idle = False):
        if self.mInLoop:
            print("WaitLoop in cycle!!!", file = sys.stderr)
            return
        if self.mMode < 0:
            print("Go quit, no waits!", file = sys.stderr)
            return
        suspended_mode = self.mMode
        try:
            self.mMode = 2 if use_idle else 1
            self.mInLoop = True
            self.mLoop_F()
        finally:
            self.mMode = suspended_mode
            self.mInLoop = False


#================================
RuntimeEnvironment = RT_Host()
