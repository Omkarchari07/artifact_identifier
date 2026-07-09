import os
import re
import json
import time
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------- CONFIG ---------------- #

CATEGORY = "sculpture"          # sculpture / architecture / arm
MUSEUM = "gom_goa"

API_URL = "https://museumsofindia.gov.in/repository/collection/fetchRecords"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://museumsofindia.gov.in/"
}

OUTPUT_FOLDER = os.path.join("museum_data", CATEGORY)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------------------------------- #

def clean_name(name):
    """Convert title into Windows-safe folder/file name"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace("(", "")
    name = name.replace(")", "")
    name = name.replace(".", "")
    name = name.replace(",", "")
    name = name.replace("&", "and")
    name = "_".join(name.split())
    return name


page = 1
total = 0

while True:

    print(f"\nFetching Page {page}")

    params = {
        "collectionType": "ObjectType",
        "collectionCategory": CATEGORY,
        "pageNo": page,
        "museum": MUSEUM
    }

    response = requests.get(
        API_URL,
        params=params,
        headers=HEADERS,
        verify=False,
        timeout=60
    )

    if response.status_code != 200:
        print("Stopped. Status:", response.status_code)
        break

    data = response.json()

    records = data["listOfResult"]

    if len(records) == 0:
        break

    for record in records:

        title = record["title"]

        folder_name = clean_name(title)

        folder = os.path.join(
            OUTPUT_FOLDER,
            folder_name
        )

        os.makedirs(folder, exist_ok=True)

        description = BeautifulSoup(
            record["description"],
            "html.parser"
        ).get_text(" ", strip=True)

        info = {
            "title": title,
            "description": description,
            "museum": record["museumName"]
        }

        with open(
            os.path.join(folder, "info.json"),
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                info,
                f,
                indent=4,
                ensure_ascii=False
            )

        record_id = record["recordIdentifier"]

        image_number = 1

        while True:

            image_url = (
                f"https://museumsofindia.gov.in/repository/file/"
                f"{MUSEUM}/"
                f"{record_id}/"
                f"{record_id}_{image_number:02d}_l.jpg"
            )

            image = requests.get(
                image_url,
                headers=HEADERS,
                verify=False,
                timeout=60
            )

            if image.status_code != 200:
                break

            filename = f"{folder_name}_{image_number}.jpg"

            with open(
                os.path.join(folder, filename),
                "wb"
            ) as img:

                img.write(image.content)

            print("Downloaded:", filename)

            image_number += 1

        total += 1

    page += 1

    time.sleep(1)

print("\nFinished")
print("Artifacts:", total)