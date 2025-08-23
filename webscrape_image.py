import os
import json
import base64
import imghdr
from urllib.parse import unquote, urlparse, parse_qs
from rapidfuzz import fuzz
import os
from sys import argv


# Configuration
DIRECTORY = argv[1]
ITEM_MAX = int(argv[2])
OUTPUT_FOLDER = argv[3]
ORDERED = int(argv[4])
if ITEM_MAX < ORDERED:
    ORDERED = ITEM_MAX - 1

#if ORDERED:
   # OUTPUT_FOLDER += "_ordenado"

# Ensure output folder exists
os.makedirs(os.path.join(DIRECTORY, OUTPUT_FOLDER), exist_ok=True)

def extract_keywords(url):
    """Extract the search query keywords from a Google search URL."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    query = qs.get("q", [""])[0]
    return unquote(query).replace("+", " ")

# Iterate through all files in the directory
for filename in os.listdir(DIRECTORY):
    if filename.startswith("FU") and filename.endswith(".json"):
        filepath = os.path.join(DIRECTORY, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON file: {filename}")
                continue

        # Extract search keywords
        try:
            url = data["results"][0]["content"]["url"]
            keywords = extract_keywords(url)
        except (KeyError, IndexError, TypeError):
            print(f"No valid URL found in: {filename}")
            continue

        # Get items
        try:
            items = data["results"][0]["content"]["results"]["organic"]
        except (KeyError, IndexError, TypeError):
            print(f"No valid items found in: {filename}")
            continue

        # Sort items by similarity to keywords
        # Filter items that have thumbnail and product_id
        valid_items = [item for item in items if "thumbnail" in item] #and "product_id" in item]

        if ORDERED > 1:
            valid_items_order = sorted(valid_items, key=lambda item: fuzz.ratio(keywords, item.get("title", "")), reverse=True)[:ORDERED]
            remaining = [item for item in valid_items if item not in valid_items_order]
            valid_items = valid_items_order + remaining[:ITEM_MAX - len(valid_items_order)]
        else:
            valid_items = valid_items[:ITEM_MAX]


        # Process each item
        for item in valid_items:
            thumbnail_b64 = item["thumbnail"]
            if  not "product_id" in item:
                product_id = "pos_" + str(item["pos_overall"])
            else:
                product_id = str(item["product_id"])

            if thumbnail_b64.startswith("data:"):
                _, thumbnail_b64 = thumbnail_b64.split(",", 1)

            try:
                image_bytes = base64.b64decode(thumbnail_b64)
            except Exception as e:
                print(f"Failed to decode base64 for {product_id} in {filename}: {e}")
                continue

            img_type = imghdr.what(None, h=image_bytes) or "jpg"
            output_name = f"{keywords}_{product_id}_{filename.split('.json')[0]}.{img_type}"
            output_path = os.path.join(DIRECTORY, OUTPUT_FOLDER, output_name)

            try:
                with open(output_path, "wb") as img_file:
                    img_file.write(image_bytes)
                print(f"Saved: {output_name}")
            except Exception as e:
                print(f"Failed to save image for {product_id} in {filename}: {e}")
