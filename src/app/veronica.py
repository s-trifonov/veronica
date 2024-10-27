import sys, os, argparse,  signal
from glob import glob
from PyQt5 import QtCore,  QtWidgets, QtWebEngineWidgets

from h2tools.http_in_app import InternalHttpApp
from h2tools.utils import getOsDirName, isWINDOWS

_keep_compiler_happy = QtWebEngineWidgets

interrupted = False
def signal_handler(signal, frame):
    global interrupted
    interrupted = True

#=========================================
def runApp(qt_app, profile_path, src_path, project_path,
        debug_mode, test_mode, multirun_mode, advances_mode):
    from h2tools.qt_app import QT_Application
    from h2tools.qt_env import QT_Environment
    from model.project import Project
    from presentation.top_pre import TopPresentation
    from config.ver_cfg import Config
    global sPrefsDefault
    if debug_mode or test_mode:
        if debug_mode:
            Config.DEBUG_MODE = True
        if test_mode:
            Config.UI_CONTEXTS.add("test")

    if isWINDOWS() and not multirun_mode:
        mem_h = QtCore.QSharedMemory(qt_app)
        mem_h.setKey("VERONICA_SHARED")
        if mem_h.attach():
            print("Duplicate Veronica runs blocked", file = sys.stderr)
            sys.exit()
        if not mem_h.create(1):
            print("Duplicate Veronica runs blocked?", file = sys.stderr)
            sys.exit()

    int_http_app = InternalHttpApp()
    app = QT_Application(qt_app, "Veronica", profile_path, src_path,
        int_http_app.getBaseUrl(), pp_no_save = multirun_mode)
    env = QT_Environment(app, "veronica", Config.PREFS_FILE,
        int_http_app, multirun_mode, Config.PREFS_DEFAULT)
    project = Project(project_path, env, advances_mode)
    top_pre = TopPresentation(env, project)
    top_pre.start()
    sys.exit(app.execute())


#=========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--stderr",  default = "",
        help = "Redefine stderr stream")
    parser.add_argument("-p", "--profile",  default = "",
        help = "Profile directory")
    parser.add_argument("--debug", action="store_true",
        help = "No try/catch, debug mode")
    parser.add_argument("--test", action="store_true",
        help = "Provide testing functionality")
    parser.add_argument("--adv", action="store_true",
        help = "Provide unstable advances functionality")
    parser.add_argument("--multirun", action="store_true",
        help = "Multirun mode, no storing session information")
    parser.add_argument("project", nargs="?", help="Project")
    run_args = parser.parse_args()
    #=========================================

    if run_args.stderr:
        sys.stderr = open(run_args.stderr, "w", encoding="utf-8")

    profile_path = run_args.profile
    if not profile_path:
        home_dir = os.environ.get("HOME")

        if home_dir and os.path.exists(home_dir):
            profile_path = home_dir + "/.veronica"
        else:
            profile_path = "C:/veronica/profile"

    if not os.path.isdir(profile_path):
        try:
            os.mkdir(profile_path)
        except Exception:
            print("Failed to access or create profile directory:",
                profile_path, "application canceled", file = sys.stderr)

    src_path = getOsDirName(__file__, 2)

    project_path = run_args.project
    if not project_path:
        variants = list(glob(os.curdir + "/*.vprj"))
        if len(variants) == 1:
            project_path = variants[0]
            print(f"Project {profile_path} is selected and used",
                file = sys.stderr)
        elif len(variants) == 0:
            print("No projects (*.vprj) in current directory",
                file = sys.stderr)
            sys.exit()
        else:
            print("Too many projects (*.vprj) in current directory",
                file = sys.stderr)
            sys.exit()

    signal.signal(signal.SIGINT, signal_handler)

    qt_app = QtWidgets.QApplication(['', '--no-sandbox'])

    runApp(qt_app, profile_path, src_path, project_path,
        run_args.debug, run_args.test, run_args.multirun,
        run_args.adv)

    if run_args.stderr:
        sys.sderr.close()
