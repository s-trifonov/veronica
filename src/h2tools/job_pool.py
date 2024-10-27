import threading, logging, abc
from uuid import uuid4
from .http_serv import loggingException

#===============================================
class TimeoutError(RuntimeError):
    pass

def handleTimeout():
    raise TimeoutError

#===============================================
class ExecutionTask:
    def __init__(self):
        self.mUID = uuid4().int

    def getUID(self):
        return self.mUID

    @abc.abstractmethod
    def execIt(self):
        assert False

    @abc.abstractmethod
    def setFailed(self, reason):
        assert False

#===============================================
class TaskHandler:
    def __init__(self, task, ord_no, priority):
        self.mTask     = task
        self.mOrdNo    = ord_no
        self.mPriority = priority

    def getOrd(self):
        return (self.mPriority, self.mOrdNo)

    def execIt(self, max_timeout):
        timeout_h = None
        if max_timeout > 0:
            timeout_h = threading.Timer(max_timeout, handleTimeout)
            timeout_h.start()
        try:
            self.mTask.execIt()
            if timeout_h is not None:
                timeout_h.cancel()
                timeout_h = None
        except TimeoutError:
            logging.error("Job canceled by timeout")
            self.Task.setFailed("TIMEOUT")
        except Exception:
            loggingException("Bad task work")
            self.mTask.setFailed("EXCEPTION(ext)")
        if timeout_h is not None:
            timeout_h.cancel()

#===============================================
class Worker(threading.Thread):
    def __init__(self, master, max_timeout):
        threading.Thread.__init__(self)
        self.mMaster = master
        self.mMaxTimeout = max_timeout
        self.start()

    def run(self):
        while True:
            task_h = self.mMaster._pickTask()
            task_h.execIt(self.mMaxTimeout)

#===============================================
class JobPool:
    def __init__(self, thread_count, pool_size, max_timeout = -1):
        self.mThrCondition = threading.Condition()
        self.mLock = threading.Lock()

        self.mTaskPool   = []
        self.mPoolSize   = int(pool_size)
        self.mMaxTimeout = int(max_timeout)
        self.mTaskCount  = 0

        self.mWorkers = [Worker(self, self.mMaxTimeout)
            for idx in range(int(thread_count))]

    @classmethod
    def create(cls, config, prefix, one_thread = False, no_timeout = False):
        if one_thread:
            thread_count = 1
        else:
            thread_count = config.get(prefix + ".threads-count", as_int = True)
        pool_size = config.get(prefix + ".pool-size", strip_it = True)
        if no_timeout:
            max_timeout = -1
        else:
            max_timeout = config.get(prefix + ".max-timeout", as_int = True)
        return cls(thread_count, pool_size, max_timeout)

    def putTask(self, task, priority = 10):
        with self.mThrCondition:
            if len(self.mTaskPool) >= self.mPoolSize:
                task.setFailed("POOL-OVERFLOW")
            else:
                self.mTaskPool.append(TaskHandler(task,
                    self.mTaskCount, priority))
                self.mTaskCount += 1
                self.mTaskPool.sort(key = TaskHandler.getOrd)
            self.mThrCondition.notify()

    def _pickTask(self):
        while True:
            with self.mThrCondition:
                with self.mLock:
                    if len(self.mTaskPool) > 0:
                        return self.mTaskPool.pop()
                self.mThrCondition.wait()
