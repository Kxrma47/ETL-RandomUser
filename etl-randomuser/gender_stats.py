import os
import json
from collections import defaultdict

STORAGE_DIR = "./storage"

def count_genders():
    stats = defaultdict(lambda: {'male': 0, 'female': 0})

    for file in os.listdir(STORAGE_DIR):
        if file.endswith(".json"):
            path = os.path.join(STORAGE_DIR, file)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    user = data["results"][0]
                    country = user["location"].get("country")
                    gender = user.get("gender")
                    if country and gender in ("male", "female"):
                        stats[country][gender] += 1
            except Exception as e:
                print(f"Error reading {file}: {e}")

    for country, counts in stats.items():
        print(f"{country}: {counts['male']} male, {counts['female']} female")

if __name__ == "__main__":
    count_genders()