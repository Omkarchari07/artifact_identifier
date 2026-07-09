import os
import json

from json_loader import load_folder_json

ROOT = "museum_data/sculpture"

database = {}

for folder in os.listdir(ROOT):

    folder_path = os.path.join(ROOT, folder)

    if not os.path.isdir(folder_path):
        continue

    info, info_path = load_folder_json(folder_path)

    if info is None:
        continue

    database[folder] = info

with open(
    "artifact_database.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        database,
        f,
        indent=4,
        ensure_ascii=False
    )

print("Artifacts:", len(database))
print("artifact_database.json created.")