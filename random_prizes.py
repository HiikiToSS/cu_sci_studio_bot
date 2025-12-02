from dotenv import load_dotenv
import os
import argparse
import pymongo
import random

load_dotenv()

MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_PORT = os.getenv("MONGODB_PORT")
MONGODB_IP = os.getenv("MONGODB_IP")

parser = argparse.ArgumentParser()
parser.add_argument("count", type=int)
args = parser.parse_args()

MONGO_HOST = (
    f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_IP}:{MONGODB_PORT}"
)
client = pymongo.MongoClient(MONGO_HOST)
database = client.get_database("cu_graph_bot")
collection = database.get_collection("users")
users = ["@" + i["username"] for i in collection.find({"_links.4": {"$exists": True}})]
print(*random.choices(users, k=args.count))
