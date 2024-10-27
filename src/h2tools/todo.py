import json, os
from datetime import datetime
from io import StringIO
from xml.sax.saxutils import escape

from config.messenger import msg
from .utils import StoreHandler, getExceptionValue
#===============================================
class _ToDoEvent:
    def __init__(self, user_name, ev_date = None):
        self.mUserName = user_name
        self.mDate = ev_date
        if self.mDate is None:
            self.mDate = datetime.now().partition('.')[0]

    def getUser(self):
        return self.mUserName

    def getDate(self):
        return self.mDate

    def report(self):
        return {"user": self.mUserName, "date": self.mDate}

    def htmpRep(self, outp):
        data_class, data_cnt = self.htmlData()
        print('<tr>'
            + f'<td class="todo-user">{escape(self.mUserName)}</td>'
            + f'<td class="todo-date">{self.mDate}</td>'
            + f'<td class="{data_class}">{data_cnt}</td></tr>',
            file = outp)

#===============================================
class RunTaskEvent(_ToDoEvent):
    def __init__(self, task_id, user_name,
            ev_date = None, count = 1):
        _ToDoEvent.__init__(self, user_name, ev_date)
        self.mTaskId = task_id
        self.mCount = count

    @classmethod
    def getKind(cls):
        return "run-task"

    def getTaskId(self):
        return self.mTaskId

    def getCount(self):
        return self.mCount

    def report(self):
        ret = _ToDoEvent.report(self)
        ret.update({"task": self.mTaskId, "count": self.mCount})
        return ret

    def htmlData(self):
        return "todo-task", (msg("todo.task.done", escape(self.mTaskId)) +
            msg("todo.task.count", self.mCount))

#===============================================
class MessageEvent(_ToDoEvent):
    def __init__(self, message, user_name, ev_date = None):
        _ToDoEvent.__init__(self, user_name, ev_date)
        self.mMessage = message

    @classmethod
    def getKind(cls):
        return "message"

    def getMessage(self):
        return self.mMessage

    def report(self):
        ret = _ToDoEvent.report(self)
        ret["message"] = self.mMessage
        return ret

    def htmlData(self):
        return "todo-msg", msg("todo.message", escape(self.mMessage))

#===============================================
class StatusEvent(_ToDoEvent):
    def __init__(self, status_id, status_value,
            user_name, ev_date = None):
        _ToDoEvent.__init__(self, user_name, ev_date)
        self.mStatusId = status_id
        self.mStatusValue = status_value

    @classmethod
    def getKind(cls):
        return "status"

    def getStatusId(self):
        return self.mStatusId

    def getStatusValue(self):
        return self.mStatusValue

    def report(self):
        ret = _ToDoEvent.report(self)
        ret.update({"status": self.mStatusId, "value": self.mStatusValue})
        return ret

    def htmlData(self):
        return "todo-status", msg("todo.status",
            escape(self.mStatusId), escape(self.mStatusValue))

#===============================================
class TodoList:
    def __init__(self, env):
        self.mEvents = []
        self.mStatusDict = dict()
        self.mMessages = []
        self.mTasks = dict()
        self.mState = 0
        self.mTaskCount = 0
        fname = env.getUIApp().getProfilePath("todo.js")
        if fname is not None and os.path.exists(fname):
            try:
                self.load(fname)
            except Exception:
                getExceptionValue()
                env.alert(msg("todo.file.bad", fname), level = 3)
        self.fixState()

    def isEmpty(self):
        return len(self.mEvents) == 0

    def load(self, fname):
        with open(fname, "r", encoding = "utf-8") as inp:
            for line in inp:
                self._addEvent(self.parseOne(json.loads(line)))

    def save(self, env):
        fname = env.getUIApp().getProfilePath("todo.js")
        st = StoreHandler(fname)
        try:
            with st.mStream as outp:
                for evt in self.mEvents:
                    print(json.dumps(evt.report(), ensure_ascii = False),
                        file = outp)
        except Exception:
            getExceptionValue()
            env.alert(msg("todo.file.bad.save", fname), level = 3)
        st.close()
        self.fixState()

    def fixState(self):
        self.mState = len(self.mEvents)

    def isChanged(self):
        return self.mState != len(self.mEvents)

    def getState(self):
        return len(self.mEvents)

    def getTaskCount(self):
        return self.mTaskCount

    def parseOne(self, obj):
        if "status" in obj:
            return StatusEvent(obj["status"], obj["value"],
                obj["user"], obj["date"])
        if "message" in obj:
            return MessageEvent(obj["message"],
                obj["user"], obj["date"])
        return RunTaskEvent(obj["task"], obj["user"],
            obj["date"], obj["count"])

    def _addEvent(self, evt):
        self.mEvents.append(evt)
        if evt.getKind() == "status":
            self.mStatusDict[evt.getStatusId()] = evt
        elif evt.getKind == "message":
            self.mMessages.append(evt)
        else:
            self.mTaskCount += 1
            self.mTasks[evt.getTaskId()] = evt

    def iterMessages(self):
        return iter(self.mMessages)

    def addMessage(self, message, user_name):
        evt_h = MessageEvent(message, user_name)
        self._addEvent(evt_h)
        return evt_h

    def iterStatus(self):
        for status_id in sorted(self.mStatusDict.keys()):
            yield self.mStatusDict[status_id]

    def setStatus(self, status_id, status_value, user_name):
        evt_h = StatusEvent(status_id, status_value, user_name)
        self._addEvent(evt_h)
        return evt_h

    def iterTasks(self):
        for task_id in sorted(self.mTasks.keys()):
            yield self.mTasks[task_id]

    def regTaskRun(self, task_id, user_name):
        prev_task = self.mTasks.get(task_id)
        count = 1 if prev_task is None else prev_task.getCount() + 1
        evt_h = RunTaskEvent(task_id, user_name, count = count)
        self._addEvent(evt_h)
        return evt_h

    def htmlRep(self):
        title = msg("todo.title")
        outp = StringIO()
        print(f"<h2>{title}</h2>", file = outp)
        print('<table class="todo-list">', file = outp)
        for evt in self.mEvents:
            evt.htmlRep(outp)
        print('</table>', file = outp)
        return title, outp.getvalue()
