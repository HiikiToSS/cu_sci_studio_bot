import argparse
import os
import random

import pymongo
from dotenv import load_dotenv

load_dotenv()

MONGODB_HOST = os.getenv("MONGODB_HOST")

parser = argparse.ArgumentParser()
parser.add_argument("count", type=int)
args = parser.parse_args()

client = pymongo.MongoClient(MONGODB_HOST)
database = client.get_database("cu_graph_bot")
collection = database.get_collection("users")
users = ["@" + i["username"] for i in collection.find({"_links.4": {"$exists": True}})]
print(*random.choices(users, k=args.count))
