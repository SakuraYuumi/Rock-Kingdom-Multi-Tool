import json
import math
import os
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from fetch_17173_chests import (
    SOURCE_TILE_SIZE,
    SOURCE_TILE_X_MIN,
    SOURCE_TILE_Y_MIN,
    SOURCE_TILE_ZOOM,
    SOURCE_WORLD_SIZE,
    SOURCE_PAGE,
    TRANSFORM_X,
    TRANSFORM_Y,
    WIKI_COORD_MIN,
    WIKI_PIXEL_PER_COORD,
    pixel_to_wiki_coord,
    to_17173_pixel,
)


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DEV_ARTIFACTS_DIR = os.path.join(PROJECT_DIR, "dev_artifacts")

LOCATION_API = "https://terra-api.17173.com/app/location/list?mapIds=4010"
LOCAL_BUNDLE = os.path.join(DEV_ARTIFACTS_DIR, "17173", "source_bundle", "17173_index_bundle.js")
OUTPUT_PATH = os.path.join(DATA_DIR, "17173_all_resources_wiki_coords.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex 17173 coordinate exporter)",
    "Referer": SOURCE_PAGE,
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_json(url):
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8-sig"))


def read_text(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def extract_balanced(text, start_index, opener="[", closer="]"):
    depth = 0
    quote = None
    escaped = False
    for index in range(start_index, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1]
    raise ValueError("Could not find matching bracket in 17173 bundle")


def split_top_level_objects(text):
    objects = []
    start = None
    depth = 0
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : index + 1])
                start = None
    return objects


def extract_string(name, text, default=""):
    match = re.search(rf'(?<![A-Za-z0-9_]){name}:"((?:\\.|[^"\\])*)"', text)
    if not match:
        return default
    return json.loads(f'"{match.group(1)}"')


def extract_int(name, text, default=None):
    match = re.search(rf"(?<![A-Za-z0-9_]){name}:(-?\d+)", text)
    return int(match.group(1)) if match else default


def extract_17173_categories():
    if not os.path.exists(LOCAL_BUNDLE):
        return {}

    bundle = read_text(LOCAL_BUNDLE)
    marker = "4010:"
    start = bundle.find(marker)
    if start < 0:
        return {}

    array_start = start + len(marker)
    groups_text = extract_balanced(bundle, array_start)
    categories = {}

    for group_text in split_top_level_objects(groups_text[1:-1]):
        group_title = extract_string("title", group_text)
        group_id = extract_int("id", group_text)
        categories_key = "categories:"
        categories_index = group_text.find(categories_key)
        if categories_index < 0:
            continue
        category_array_start = categories_index + len(categories_key)
        category_text = extract_balanced(group_text, category_array_start)
        for category_item in split_top_level_objects(category_text[1:-1]):
            category_id = extract_int("id", category_item)
            if category_id is None:
                continue
            categories[category_id] = {
                "sourceGroupId": group_id,
                "sourceGroupName": group_title,
                "sourceCategoryId": category_id,
                "sourceCategoryName": extract_string("title", category_item),
                "sourceCategoryGroupId": extract_int("group_id", category_item),
                "icon": extract_string("icon", category_item),
            }

    return categories


def apply_wiki_transform(source_x, source_y):
    return (
        TRANSFORM_X[0] * source_x + TRANSFORM_X[1] * source_y + TRANSFORM_X[2],
        TRANSFORM_Y[0] * source_x + TRANSFORM_Y[1] * source_y + TRANSFORM_Y[2],
    )


def convert_point(point, category):
    source_x, source_y = to_17173_pixel(point)
    wiki_x, wiki_y = apply_wiki_transform(source_x, source_y)
    wiki_lng, wiki_lat = pixel_to_wiki_coord(wiki_x, wiki_y)
    in_bounds = 0 <= wiki_x <= 3072 and 0 <= wiki_y <= 3072

    return {
        "id": f"17173-{point['id']}",
        "sourcePointId": point["id"],
        "mapId": point.get("mapId") or point.get("map_id"),
        "title": point.get("title") or "",
        "sourceGroupId": category.get("sourceGroupId"),
        "sourceGroupName": category.get("sourceGroupName", "未分类"),
        "sourceCategoryId": point.get("category_id"),
        "sourceCategoryName": category.get("sourceCategoryName", "未分类"),
        "sourceCategoryIcon": category.get("icon", ""),
        "sourceLongitude": point.get("longitude"),
        "sourceLatitude": point.get("latitude"),
        "sourceTilePixel": {
            "x": round(source_x, 6),
            "y": round(source_y, 6),
        },
        "wikiMapPixel": {
            "x": round(wiki_x, 6),
            "y": round(wiki_y, 6),
            "inBounds": in_bounds,
        },
        "wikiCoord": {
            "lng": round(wiki_lng, 6),
            "lat": round(wiki_lat, 6),
        },
        "sourceUrl": SOURCE_PAGE,
    }


def main():
    fetched_at = utc_now()
    category_table = extract_17173_categories()
    payload = fetch_json(LOCATION_API)
    source_points = payload.get("data", [])

    converted = []
    for point in source_points:
        category_id = point.get("category_id")
        category = category_table.get(category_id, {
            "sourceGroupId": None,
            "sourceGroupName": "未分类",
            "sourceCategoryId": category_id,
            "sourceCategoryName": "未分类",
            "sourceCategoryGroupId": None,
            "icon": "",
        })
        converted.append(convert_point(point, category))

    counts_by_group = {}
    counts_by_category = {}
    for point in converted:
        counts_by_group[point["sourceGroupName"]] = counts_by_group.get(point["sourceGroupName"], 0) + 1
        key = f"{point['sourceCategoryId']} {point['sourceCategoryName']}"
        counts_by_category[key] = counts_by_category.get(key, 0) + 1

    categories = []
    for category in sorted(category_table.values(), key=lambda item: (item["sourceGroupId"], item["sourceCategoryId"])):
        key = f"{category['sourceCategoryId']} {category['sourceCategoryName']}"
        categories.append({
            **category,
            "pointCount": counts_by_category.get(key, 0),
        })

    result = {
        "meta": {
            "sourcePage": SOURCE_PAGE,
            "locationApi": LOCATION_API,
            "fetchedAt": fetched_at,
            "sourcePointCount": len(source_points),
            "convertedPointCount": len(converted),
            "inBoundsCount": sum(1 for point in converted if point["wikiMapPixel"]["inBounds"]),
            "outOfBoundsCount": sum(1 for point in converted if not point["wikiMapPixel"]["inBounds"]),
            "categoryCountFrom17173Page": len(category_table),
            "categoryCountInPointApi": len({point.get("category_id") for point in source_points}),
            "countsByGroup": counts_by_group,
            "countsByCategory": counts_by_category,
            "coordinateTransform": {
                "sourcePixelSpace": "17173 z12 stitched WebMercator tile pixels",
                "sourceTileZoom": SOURCE_TILE_ZOOM,
                "sourceTileSize": SOURCE_TILE_SIZE,
                "sourceTileOrigin": {
                    "x": SOURCE_TILE_X_MIN,
                    "y": SOURCE_TILE_Y_MIN,
                },
                "sourceWorldSize": SOURCE_WORLD_SIZE,
                "targetPixelSpace": "wiki_G_z6.png pixels",
                "wikiCoordinateFormula": {
                    "lng": "wikiMapPixel.x / 0.5 + -3072",
                    "lat": "wikiMapPixel.y / 0.5 + -3072",
                    "pixelPerCoordinate": WIKI_PIXEL_PER_COORD,
                    "coordinateMin": WIKI_COORD_MIN,
                },
                "transformX": TRANSFORM_X,
                "transformY": TRANSFORM_Y,
                "alignmentNote": "The wiki basemap is a crop of the 17173 tile image, not a direct resize.",
            },
            "programDataNote": "This file is standalone and is not loaded by the current app.",
        },
        "categories": categories,
        "points": converted,
    }

    write_json(OUTPUT_PATH, result)
    print(f"17173 source points: {len(source_points)}")
    print(f"Converted points: {len(converted)}")
    print(f"In bounds: {result['meta']['inBoundsCount']}")
    print(f"Out of bounds: {result['meta']['outOfBoundsCount']}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
