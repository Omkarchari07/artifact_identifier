import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test Record
record_id = "gom_goa-acc-no-0320-104"

# Try different possible image names
image_variants = [
    "_01_l.jpg",
    "_01_h.jpg",
    "_02_l.jpg",
    "_02_h.jpg",
    "_03_l.jpg",
    "_03_h.jpg",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://museumsofindia.gov.in/"
}

os.makedirs("images/test", exist_ok=True)

for variant in image_variants:

    image_url = (
        f"https://museumsofindia.gov.in/repository/file/"
        f"gom_goa/{record_id}/{record_id}{variant}"
    )

    print(f"\nTrying: {image_url}")

    try:

        response = requests.get(
            image_url,
            headers=HEADERS,
            verify=False,
            timeout=60
        )

        print("Status:", response.status_code)

        if response.status_code == 200:

            save_path = os.path.join(
                "images",
                "test",
                variant.replace("/", "_")
            )

            with open(save_path, "wb") as f:
                f.write(response.content)

            print("✅ Downloaded:", save_path)

        else:

            print("❌ Not Found")

    except Exception as e:

        print(e)