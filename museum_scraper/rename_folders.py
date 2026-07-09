import os

ROOT = "museum_data/sculpture"

for folder in os.listdir(ROOT):

    old_path = os.path.join(ROOT, folder)

    if not os.path.isdir(old_path):
        continue

    new_name = folder.replace("_", " ")

    new_path = os.path.join(ROOT, new_name)

    if old_path == new_path:
        continue

    if os.path.exists(new_path):
        print(f"Skipped (already exists): {new_name}")
        continue

    os.rename(old_path, new_path)

    print(f"Renamed:\n  {folder}\n  -> {new_name}\n")

print("Done.")