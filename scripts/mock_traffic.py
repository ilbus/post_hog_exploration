import httpx
import time
import random
import uuid
import os
from datetime import datetime, timezone

API_URL = "http://localhost:8000/ingest"
API_KEY = os.getenv("API_SECRET_KEY", "local_dev_secret_key_12345")


def generate_payload():
    return {
        "event": "$autocapture",
        "distinct_id": f"user_{random.randint(1, 3)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "properties": {
            "$session_id": str(uuid.uuid4()),
            "$element_text": "Upgrade Plan",
            "attr__class": "btn btn-primary upgrade-btn",
        },
    }


if __name__ == "__main__":
    headers = {"X-API-Key": API_KEY}
    print(f"Flooding {API_URL}...")

    with httpx.Client() as client:
        while True:
            try:
                client.post(API_URL, json=generate_payload(), headers=headers)
                print(".", end="", flush=True)
                time.sleep(0.5)
            except Exception:
                print("x", end="", flush=True)
                time.sleep(1)
