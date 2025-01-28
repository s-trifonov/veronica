import argparse, json, os, sys
from glob import glob
from pymongo import MongoClient
from PIL import Image

from deep.loading import preparePackTrainData
from deep.lmodel import doLearn
#=========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode",  default = "simple",
        help = "Modes: simple/deep")
    parser.add_argument("-e", "--stderr",  default = "",
        help = "Redefine stderr stream")
    parser.add_argument("-E", "--eportion",
        type = int, default = 10,
        help = "Epoch portion (default 10")
    parser.add_argument("-P", "--portion",
        type = int, default = 10,
        help = "Data portion (default 10)")
    parser.add_argument("-N", "--n_epochs",
        type = int, default = 50,
        help = "Epoch count")
    parser.add_argument("project", nargs="?", help="Project")
    run_args = parser.parse_args()

    assert run_args.mode in ("simple", "deep")

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

    mongo_client = MongoClient(m_host, m_port)
    mongo_agent = mongo_client[m_top_path][project_info["prj-name"]]

    img_cnt = 0
    train_data = []
    for it in mongo_agent.find({
            "_tp": "annotation", "round":"lpack"}):
        pack_img_file, pack_descr = it["file"], it["data"]
        img = Image.open(project_info["dir"] + pack_img_file + ".tif")
        train_data += preparePackTrainData(img, pack_descr)
        img_cnt += 1

    del mongo_agent
    mongo_client.close()

    print(f"Loaded: {len(train_data)} items for {img_cnt} image(s)")

    if run_args.mode == "deep":
        import jax.numpy as jnp
        train_data = [(jnp.array(patch_img_data).reshape((128, 128, 1)),
                jnp.array(patch_descr["target"], float))
            for patch_descr, patch_img_data in train_data]

        result = doLearn(train_data, run_args.n_epochs,
            run_args.portion, run_args.eportion)
    else:
        assert run_args.mode == "simple"

