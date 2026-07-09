import os

ROOT = "museum_data/sculpture"

classes = []

for folder in os.listdir(ROOT):

    path = os.path.join(ROOT, folder)

    if os.path.isdir(path):

        classes.append(folder)

classes.sort()

with open(
    "artifact_classes.txt",
    "w",
    encoding="utf-8"
) as f:

    for c in classes:
        f.write(c + "\n")

print("Classes:", len(classes))
print("artifact_classes.txt created.")