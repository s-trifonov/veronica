import logging, json, threading, time
from wsgiref.simple_server import make_server, WSGIRequestHandler
from http.client import HTTPConnection

from config.ver_cfg import Config
from .hserv import setupHServer, HServHandler
from .runtime import RT_Guard
#========================================
class InternalHttpApp(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.mEnv = None
        self.mAgents = dict()
        self.mStopped = False
        self.mHttpD = None
        self.mPort = Config.IN_HTTP_PORT
        self.mLock = threading.Lock()
        self.mEventCache = []
        self.mRqHandlers = dict()

    def getBaseUrl(self):
        return "http://localhost:%d" % self.mPort

    def regRqHandler(self, request, rq_h):
        self.mRqHandlers[request] = rq_h

    def activate(self, env):
        self.mEnv = env
        self.start()
        time.sleep(.1)

    def run(self):
        logging.basicConfig(level = 30)
        host, port = setupHServer(self, {
            "host": "localhost",
            "port": self.mPort,
            "dir-files": [
                ["/ui", self.mEnv.getUIApp().getSrcPath("ui")],
                ["/icons", self.mEnv.getUIApp().getSrcPath("icons")],
                ["/config", self.mEnv.getUIApp().getSrcPath("config")]
            ]},
            False)
        self.mHttpD = make_server(host, port, application,
            handler_class = _LoggingWSGIRequestHandler)
        while not self.mStopped:
            self.mHttpD.handle_request()

    def stop(self):
        self.mStopped = True
        self.ping()

    def ping(self):
        conn = HTTPConnection("localhost", self.mPort)
        conn.request("GET", "/ping", headers = {
            "Content-Type": "application/json",
            "Encoding": "utf-8"})
        conn.getresponse()

    def setup(self, config, in_container):
        pass

    def checkFilePath(self, fpath):
        if fpath == "/favicon.ico":
            return self.mEnv.getUIApp().getSrcPath("icons/h2.ico")
        return None

    def regAgent(self, name, agent):
        assert name not in self.mAgents
        self.mAgents[name] = agent

    def request(self, resp_h, rq_path, query_args, rq_descr):
        if rq_path == "/ping":
            return resp_h.makeResponse(mode = "json",
                content = "true")
        if rq_path == "/load":
            agent = query_args["agent"]
            rq = json.loads(query_args["rq"]) if "rq" in query_args else None
            #with RT_Guard.syncro():
            report = self.mAgents[agent].httpLoad(agent, rq)
            return resp_h.makeResponse(mode = "json",
                content = json.dumps(report))
        if rq_path == "/event":
            agent = query_args["agent"]
            evt_code = query_args["code"]
            evt_data = query_args.get("data")
            if evt_data is not None:
                evt_data = json.loads(evt_data)
            with self.mLock:
                self.mEventCache.append((agent, evt_code, evt_data))
            with RT_Guard.syncro():
                self.mEnv.postIdle()
            return resp_h.makeResponse(mode = "json", content = "true")
        if rq_path in self.mRqHandlers:
            content, mode  = self.mRqHandlers[rq_path].processRq(query_args)
            return resp_h.makeResponse(mode = mode, content = content)

        assert False, "Bad reques type: " + rq_path
        return None

    def isEmpty(self):
        with self.mLock:
            return len(self.mEventCache) == 0

    def pushEvents(self):
        ret = 0
        with self.mLock:
            for agent, evt_code, evt_data in self.mEventCache:
                self.mAgents[agent].httpEvent(agent, evt_code, evt_data)
                ret += 1
            self.mEventCache = []
        return ret

#========================================
def application(environ, start_response):
    return HServHandler.request(environ, start_response)

#========================================
class _LoggingWSGIRequestHandler(WSGIRequestHandler):
    def log_message(self, format_str, *args):
        logging.info(("%s - - [%s] %s\n" %
            (self.client_address[0], self.log_date_time_string(),
            format_str % args)).rstrip())
