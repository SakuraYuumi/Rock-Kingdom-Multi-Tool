import json
import os


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DEV_ARTIFACTS_DIR = os.path.join(PROJECT_DIR, "dev_artifacts")
WEB_DIR = os.path.join(DEV_ARTIFACTS_DIR, "web_preview")


SOURCE_PATH = os.path.join(DATA_DIR, "wiki_resource_points_pixels_z6.json")
OUTPUT_PATH = os.path.join(WEB_DIR, "resource-data.js")


def read_json(path):
    with open(path, "r", encoding="utf-8-sig") as file:
        return json.load(file)


def to_web_path(path):
    return "../../" + path.replace("\\", "/")


def main():
    data = read_json(SOURCE_PATH)
    meta = data["meta"]

    payload = {
        "meta": {
            "sourcePage": meta["sourcePage"],
            "basemapImage": "../../assets/maps/wiki_G_z6.png",
            "imageSize": meta["basemapImageSize"],
            "markerCount": meta["projectedCount"],
            "iconWidth": meta["iconWidth"],
            "iconAnchor": [15, 42],
            "countsByGroup": meta["countsByGroup"],
            "countsByType": meta["countsByType"],
        },
        "markers": [],
    }

    for index, marker in enumerate(data["markers"]):
        pixel = marker["wikiMapPixel"]
        if not pixel["inBounds"]:
            continue
        payload["markers"].append({
            "id": marker.get("id") or f"marker-{index}",
            "group": marker["group"],
            "markType": marker["markType"],
            "markTypeName": marker["markTypeName"],
            "title": marker.get("title") or "",
            "layer": marker["layer"],
            "x": pixel["x"],
            "y": pixel["y"],
            "icon": to_web_path(marker["icon"]),
        })

    os.makedirs(WEB_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("window.ROCO_RESOURCE_MAP = ")
        json.dump(payload, file, ensure_ascii=False, separators=(",", ":"))
        file.write(";\n")

    print(f"Markers: {len(payload['markers'])}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
