import json
import os


def load_folder_json(folder_path):

    preferred_path = os.path.join(folder_path, "info.json")

    if os.path.exists(preferred_path):
        with open(preferred_path, "r", encoding="utf-8") as f:
            return json.load(f), preferred_path

    json_files = [
        filename for filename in os.listdir(folder_path)
        if filename.lower().endswith(".json")
    ]

    if len(json_files) == 1:
        json_path = os.path.join(folder_path, json_files[0])

        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f), json_path

    if len(json_files) > 1:
        raise ValueError(
            f"Multiple JSON files found in {folder_path}. Keep one info.json or one class JSON file."
        )

    return None, None