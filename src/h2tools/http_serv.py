import os, traceback, logging, json, abc
from io import StringIO
from urllib.parse import parse_qs
from cgi import parse_header, parse_multipart
import logging.config

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

def loggingException(message):
    rep = StringIO()
    traceback.print_exc(file = rep)
    logging.error(message + "\n" + rep.getvalue())

#===============================================
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):

    """Handle requests in a separate thread."""


#========================================
SERVER_SHELL = None
SERVER_FILE_DIR = None

#========================================
class MyRequestHandler(BaseHTTPRequestHandler):

    sContentTypes = {
        "html":   "text/html",
        "htm":    "text/html",
        "xml":    "text/xml",
        "css":    "text/css",
        "js":     "application/javascript"}

    sErrorCodes = {
        202: "202 Accepted",
        204: "204 No Content",
        303: "303 See Other",
        400: "400 Bad Request",
        408: "408 Request Timeout",
        404: "404 Not Found",
        422: "422 Unprocessable Entity",
        423: "423 Locked",
        500: "500 Internal Error"}

    sPostContentMode = False

    def makeResponse(self,
            mode        = "html",
            content     = None,
            error       = None,
            add_headers = None):
        response_code = 200
        response_status = "200 OK"
        if error is not None:
            response_code = error
            response_status  = self.sErrorCodes[error]
        if content is not None:
            response_body = content.encode("utf-8")
            response_headers = [("Content-Type", self.sContentTypes[mode]),
                                ("Content-Length", str(len(response_body)))]
        else:
            response_body = response_status
            response_headers = []
        if add_headers is not None:
            response_headers += add_headers

        self.send_response(response_code, response_status)
        for name, value in response_headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(response_body)
        self.wfile.flush()
        return True

    def log_message(self, format_str, *args):
        logging.info(("%s - - [%s] %s\n" % (self.client_address[0],
            self.log_date_time_string(), format_str % args)).rstrip())

    def address_string(self):
        host, port = self.client_address[:2]
        #return socket.getfqdn(host)
        return host

    #===============================================
    def _readPostContent(self):
        content_len = int(self.headers.get('content-length', 0))
        return self.rfile.read(content_len)

    def _parsePOST_content(self):
        try:
            return self._readPostContent().decode("utf-8")
        except Exception:
            loggingException("Exception on read request body")
            return ""

    def _parsePOST_vars(self):
        ctype, pdict = parse_header(self.headers['content-type'])
        if ctype == 'multipart/form-data':
            return parse_multipart(self.rfile, pdict)
        if ctype == 'application/x-www-form-urlencoded':
            return parse_qs(self._parsePOST_content(), keep_blank_values = 1)
        return {}

    #===============================================
    def parseRequest(self):
        content = None
        path, q, query_string = self.path.partition('?')

        query_args = dict()
        if query_string:
            for a, v in parse_qs(query_string).items():
                query_args[a] = v[0]

        if self.command == "POST":
            if self.sPostContentMode:
                content = self._parsePOST_content()
            else:
                for a, v in self._parsePOST_vars().items():
                    query_args[a] = v[0]
        return path, query_args, content

    #===============================================
    def doIt(self):
        global SERVER_SHELL
        try:
            path, query_args, content = self.parseRequest()
            if '.' in path and not query_args and not content:
                return self.fileResponse(path)
            return SERVER_SHELL.evalRequest(path, query_args, content, self)
        except Exception:
            loggingException("Exception on %s request" % self.command)
            return self.makeResponse(error = 500,
                content = "FAILED")

    #===============================================
    def fileResponse(self, fname):
        global SERVER_FILE_DIR
        if SERVER_FILE_DIR is not None:
            fpath = SERVER_FILE_DIR + "/" + fname
            if os.path.exists(fpath):
                with open(fpath, "r", encoding = "utf-8") as inp:
                    content = inp.read()
                return self.makeResponse(mode = fname.rpartition('.')[2],
                    content = content)
        return self.makeResponse(error = 500,
            content = "File %s not found" % fname)

    #===============================================
    def do_GET(self):
        return self.doIt()

    def do_POST(self):
        return self.doIt()


#========================================
class ServerShell_Base:
    @abc.abstractmethod
    def evalRequest(self, path, query_args, content, handler):
        return handler.makeResponse(error = 500,
            content = "NOT YET IMPLEMENTED")


#========================================
def runService(config, prefix, server_shell, file_dir = None,
        use_post_content = False):
    global SERVER_SHELL, SERVER_FILE_DIR
    host = config.get(prefix + ".host", strip_it = True)
    port = config.get(prefix + ".port", as_int = True)
    if file_dir:
        SERVER_FILE_DIR = file_dir
    else:
        SERVER_FILE_DIR = config.get(prefix + ".file-dir", strip_it = True)
    SERVER_SHELL = server_shell

    logging_config = config.get(prefix + ".logging", strip_it = True)
    if logging_config:
        logging.config.dictConfig(json.loads(logging_config))

    logging.basicConfig(level = 0)

    if use_post_content:
        MyRequestHandler.sPostContentMode = True

    server = ThreadedHTTPServer((host, port), MyRequestHandler)
    logging.info("HTTPServer %s listening %s:%d" % (prefix, host, port))
    server.serve_forever()
