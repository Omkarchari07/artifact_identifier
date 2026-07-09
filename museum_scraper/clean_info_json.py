import os
import json

from json_loader import load_folder_json

ROOT = "museum_data/sculpture"

FIELD_MAP = {
    "Title": "title",
    "Object Type": "object_type",
    "Main Material": "main_material",
    "Provenance": "provenance",
    "Style": "style",
    "Period / Year of Work": "period",
    "Tribe": "tribe",
    "Culture": "culture",
    "Brief Description": "brief_description",
    "Detailed Description": "detailed_description"
}

for folder in os.listdir(ROOT):

    folder_path = os.path.join(ROOT, folder)

    if not os.path.isdir(folder_path):
        continue

    data, json_path = load_folder_json(folder_path)

    if data is None:
        continue

    cleaned = {}

    for old_key, new_key in FIELD_MAP.items():

        cleaned[new_key] = data.get(old_key, "")

    with open(json_path, "w", encoding="utf-8") as f:

        json.dump(
            cleaned,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(folder)

print("\nFinished")