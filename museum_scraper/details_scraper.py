# import os
# import json
# import time
# import requests
# from bs4 import BeautifulSoup

# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # ---------------------------------------------------
# # CONFIG
# # ---------------------------------------------------

# BASE_RECORD_URL = "https://museumsofindia.gov.in/repository/record/"

# HEADERS = {
#     "User-Agent": "Mozilla/5.0",
#     "Referer": "https://museumsofindia.gov.in/"
# }

# # Your master json generated previously
# MASTER_JSON = "output/sculpture_clean.json"

# # Folder containing all artifact folders
# DATASET_FOLDER = "museum_data/sculpture"

# # ---------------------------------------------------


# def clean(text):
#     if text is None:
#         return ""

#     text = text.replace("\n", " ")
#     text = text.replace("\r", " ")
#     text = " ".join(text.split())
#     return text


# # Read record identifiers
# with open(MASTER_JSON, "r", encoding="utf-8") as f:
#     records = json.load(f)

# print(f"\nFound {len(records)} records\n")

# for i, record in enumerate(records, start=1):

#     record_id = record["recordIdentifier"]
#     title = record["title"]

#     folder_name = (
#         title.replace("/", "_")
#              .replace("\\", "_")
#              .replace(":", "")
#              .replace("*", "")
#              .replace("?", "")
#              .replace('"', "")
#              .replace("<", "")
#              .replace(">", "")
#              .replace("|", "")
#              .strip()
#     )

#     folder = os.path.join(DATASET_FOLDER, folder_name)

#     if not os.path.exists(folder):
#         print(f"Skipping: {folder_name}")
#         continue

#     url = BASE_RECORD_URL + record_id

#     print(f"[{i}/{len(records)}] {title}")

#     try:

#         response = requests.get(
#             url,
#             headers=HEADERS,
#             verify=False,
#             timeout=60
#         )

#         if response.status_code != 200:
#             print("Failed:", response.status_code)
#             continue

#         soup = BeautifulSoup(response.text, "html.parser")

#         table = soup.find("table")

#         if table is None:
#             print("No table found.")
#             continue

#         info = {
#             "title": title,
#             "object_type": "",
#             "main_material": "",
#             "country": "",
#             "provenance": "",
#             "style": "",
#             "patron_dynasty": "",
#             "period": "",
#             "tribe": "",
#             "culture": "",
#             "brief_description": "",
#             "detailed_description": ""
#         }

#         mapping = {
#             "Object Type": "object_type",
#             "Main Material": "main_material",
#             "Country": "country",
#             "Provenance": "provenance",
#             "Style": "style",
#             "Patron/Dynasty": "patron_dynasty",
#             "Period / Year of Work": "period",
#             "Tribe": "tribe",
#             "Culture": "culture",
#             "Brief Description": "brief_description",
#             "Detailed Description": "detailed_description"
#         }

#         rows = table.find_all("tr")

#         for row in rows:

#             th = row.find("th")
#             td = row.find("td")

#             if th is None or td is None:
#                 continue

#             key = clean(th.get_text())

#             if key in mapping:
#                 info[mapping[key]] = clean(td.get_text(" ", strip=True))

#         save_path = os.path.join(folder, "info.json")

#         with open(save_path, "w", encoding="utf-8") as f:
#             json.dump(info, f, indent=4, ensure_ascii=False)

#         print("✓ Saved")

#     except Exception as e:
#         print(e)

#     time.sleep(1)

# print("\nDone.")

import os
import re
import json
import time
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# CONFIG
# ============================================================

BASE_URL = "https://museumsofindia.gov.in/repository/record/"
MASTER_JSON = "output/sculpture_clean.json"

DATASET_FOLDER = "museum_data/sculpture"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://museumsofindia.gov.in/"
}

# ============================================================
# Helper Functions
# ============================================================

def clean_text(text):
    if text is None:
        return ""

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = " ".join(text.split())

    return text.strip()


def clean_name(name):

    name = re.sub(r'[\\/*?:"<>|]', "", name)

    name = name.replace("(", "")
    name = name.replace(")", "")
    name = name.replace(".", "")
    name = name.replace(",", "")
    name = name.replace("&", "and")

    name = "_".join(name.split())

    return name


def find_folder(title):

    possible = []

    possible.append(title)

    possible.append(clean_name(title))

    possible.append(clean_name(title).replace("_", " "))

    possible.append(title.replace("_", " "))

    for folder in possible:

        path = os.path.join(DATASET_FOLDER, folder)

        if os.path.isdir(path):

            return path

    return None


def scrape_table(soup):

    data = {}

    table = soup.find("table")

    if table is None:
        return data

    rows = table.find_all("tr")

    for row in rows:

        th = row.find("th")
        td = row.find("td")

        if th is None:
            continue

        if td is None:
            continue

        key = clean_text(th.get_text())

        value = clean_text(td.get_text(" ", strip=True))

        data[key] = value

    return data


# ============================================================
# Read JSON
# ============================================================

with open(MASTER_JSON, "r", encoding="utf-8") as f:

    records = json.load(f)

print()

print("=" * 60)
print("Records Found :", len(records))
print("=" * 60)

matched = 0
skipped = 0
failed = 0

# ============================================================
# MAIN LOOP
# ============================================================

for index, record in enumerate(records, start=1):

    title = record["title"]

    record_id = record["recordIdentifier"]

    print()
    print(f"[{index}/{len(records)}] {title}")

    folder = find_folder(title)

    if folder is None:

        print("Folder not found")

        skipped += 1

        continue

    url = BASE_URL + record_id

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            verify=False,
            timeout=60
        )

        if response.status_code != 200:

            print("HTTP", response.status_code)

            failed += 1

            continue

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        info = scrape_table(soup)

        # Always keep title

        info["title"] = title

        # Save original page also

        info["museum_record"] = url
                # -------------------------------------------------------
        # If table extraction failed, try all table rows
        # -------------------------------------------------------

        if len(info) <= 2:

            print("Primary parser found very little data.")
            print("Trying fallback parser...")

            tables = soup.find_all("table")

            for table in tables:

                rows = table.find_all("tr")

                for row in rows:

                    cells = row.find_all(["th", "td"])

                    if len(cells) < 2:
                        continue

                    key = clean_text(cells[0].get_text())

                    value = clean_text(cells[1].get_text(" ", strip=True))

                    if key != "":
                        info[key] = value

        # -------------------------------------------------------
        # Remove empty values
        # -------------------------------------------------------

        cleaned = {}

        for key, value in info.items():

            if value is None:
                continue

            if value == "":
                continue

            cleaned[key] = value

        # -------------------------------------------------------
        # Save JSON
        # -------------------------------------------------------

        save_path = os.path.join(folder, "info.json")

        with open(
            save_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                cleaned,
                f,
                indent=4,
                ensure_ascii=False
            )

        print("✓ info.json updated")

        matched += 1

        # -------------------------------------------------------
        # Optional folder rename
        # -------------------------------------------------------

        current_folder = os.path.basename(folder)

        new_folder = current_folder.replace("_", " ")

        if current_folder != new_folder:

            new_path = os.path.join(
                DATASET_FOLDER,
                new_folder
            )

            if not os.path.exists(new_path):

                os.rename(folder, new_path)

                print("✓ Folder renamed")

        time.sleep(0.5)

    except Exception as e:

        failed += 1

        print("ERROR")

        print(e)

        continue

# ============================================================
# REPORT
# ============================================================

print()
print("=" * 60)
print("SCRAPING COMPLETE")
print("=" * 60)

print("Total Records :", len(records))
print("Matched       :", matched)
print("Skipped       :", skipped)
print("Failed        :", failed)

print("=" * 60)
print("Finished")