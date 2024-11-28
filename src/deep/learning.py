import argparse, json, os, sys
from glob import glob
from pymongo import MongoClient
from PIL import Image

from deep.loading import preparePackTrainData
#=========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--stderr",  default = "",
        help = "Redefine stderr stream")
    parser.add_argument("project", nargs="?", help="Project")
    run_args = parser.parse_args()

    project_path = run_args.project
    if not project_path:
        variants = list(glob(os.curdir + "/*.vprj"))
        if len(variants) == 1:
            project_path = variants[0]
            print(f"Project {project_path} is selected and used",
                file = sys.stderr)
        elif len(variants) == 0:
            print("No projects (*.vprj) in current directory",
                file = sys.stderr)
            sys.exit()
        else:
            print("Too many projects (*.vprj) in current directory",
                file = sys.stderr)
            sys.exit()

    with open(project_path, "r", encoding = "utf-8") as input:
        project_info = json.loads(input.read())

    m_host = project_info.get("mongo-host", "localhost")
    m_port = project_info.get("mongo-port", 27017)
    m_top_path = project_info.get("mongo-top", "Veronica")

    mongo_agent = MongoClient(m_host, m_port)[m_top_path][
        project_info["prj-name"]]

    img_cnt = 0
    train_data = []
    for it in mongo_agent.find({
            "_tp": "annotation", "round":"lpack"}):
        pack_img_file, pack_descr = it["file"], it["data"]
        img = Image.open(project_info["dir"] + pack_img_file + ".tif")
        train_data += preparePackTrainData(img, pack_descr)
        img_cnt += 1

    print(f"Loaded: {len(train_data)} items for {img_cnt} image(s)")


