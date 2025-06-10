import sys, argparse, json
from pymongo import MongoClient

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", default = "localhost:27017",
    help = "Mongo host URL address")
parser.add_argument("-v", "--vault",  default = "V0",
    help = "Mongo vault directory")
parser.add_argument("data", nargs="?", help="Data in JSon format")
run_args = parser.parse_args()

host, _, port = run_args.url.partition(':')
host = host.strip()
port = int(port)

client = MongoClient(host, port)["Veronica"][run_args.vault]

with open(run_args.data, "r", encoding="utf-8") as inp:
    data = json.loads(inp.read())

cnt = 0
for descr in data:
    client.update_one(descr, {"$set": descr}, upsert = True)
    cnt += 1

print("Done:", cnt, file=sys.stderr)
