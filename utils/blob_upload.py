import requests
import os

BLOB_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")


def upload_to_blob(file):
    url = "https://blob.vercel-storage.com/upload"

    headers = {
        "Authorization": f"Bearer {BLOB_TOKEN}",
    }

    files = {
        "file": (file.name, file, file.content_type),
    }

    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        return response.json()["url"]

    return None