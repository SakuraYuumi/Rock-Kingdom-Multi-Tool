import json
import math
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
POINTS_PATH = PROJECT_DIR / "data" / "17173_all_resources_wiki_coords.json"
DETAILS_PATH = PROJECT_DIR / "data" / "17173_marker_details.json"
SUMMARY_PATH = PROJECT_DIR / "data" / "17173_detail_link_summary.json"
WIKI_PATHS = [
    PROJECT_DIR / "data" / "wiki_resource_points_pixels_z6.json",
    PROJECT_DIR / "data" / "wiki_resource_points_pixels_z7.json",
]

DEFAULT_DISTANCE_Z7 = 44.0
DISTANCE_BY_MARK_TYPE_Z7 = {
    803: 60.0,
}

CHEST_MARK_TYPES = {
    301,
    303,
    304,
    305,
    306,
    307,
    308,
    309,
    310,
    311,
    313,
    314,
    315,
    316,
    317,
    318,
    319,
    320,
    321,
    322,
    171730101,
    171730102,
    171730103,
    171730104,
    171730105,
    171730106,
    171730107,
    171730108,
    171730109,
    171730110,
}

MANUAL_CATEGORY_BY_MARK_TYPE = {
    201: {17310030039},
    202: {17310030038},
    203: {17310030041},
    204: {17310030025},
    209: {17310030029},
    210: {17310030039},
    701: {17310030044},
    702: {17310030043},
    703: {17310030046},
    704: {17310030045},
    705: {17310030069},
    706: {17310030063},
    707: {17310030075},
    708: {17310030079},
    709: {17310030068},
    710: {17310030078},
    711: {17310030065},
    712: {17310030062},
    713: {17310030064},
    714: {17310030055},
    716: {17310030071},
    717: {17310030073},
    718: {17310030051},
    719: {17310030060},
    720: {17310030066},
    721: {17310030056},
    723: {17310030050},
    724: {17310030070},
    725: {17310030054},
    727: {17310030057},
    728: {17310030067},
    729: {17310030049},
    730: {17310030077},
    731: {17310030058},
    732: {17310030059},
    733: {17310030074},
    736: {17310030053},
    738: {17310030072},
    739: {17310030052},
    801: {17310030002},
    802: {17310030035},
    803: {17310030047},
    807: {17310030080},
    808: {17310030082},
    809: {17310030081},
    171730031: {17310030031},
    17310030005: {17310030005},
    17310030006: {17310030006},
    17310030007: {17310030007},
    17310030008: {17310030008},
    17310030009: {17310030009},
    17310030010: {17310030010},
    17310030011: {17310030011},
    17310030012: {17310030012},
    17310030013: {17310030013},
    17310030014: {17310030014},
    17310030015: {17310030015},
    17310030016: {17310030016},
    17310030018: {17310030018},
    17310030019: {17310030019},
    17310030020: {17310030020},
    17310030021: {17310030021},
    17310030022: {17310030022},
    17310030025: {17310030025},
    17310030026: {17310030026},
    17310030027: {17310030027},
    17310030028: {17310030028},
    17310030029: {17310030029},
    17310030033: {17310030033},
    17310030034: {17310030034},
    17310030036: {17310030036},
    17310030037: {17310030037},
}

for mark_type in CHEST_MARK_TYPES:
    MANUAL_CATEGORY_BY_MARK_TYPE.setdefault(mark_type, set()).add(17310030001)


def read_json(path):
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_json(path, data):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    temp_path.replace(path)


def wiki_scale(payload):
    width = float(payload.get("meta", {}).get("basemapImageSize", [3072])[0] or 3072)
    return width / 3072.0


def infer_existing_category_links(markers, points_by_id):
    inferred = defaultdict(set)
    for marker in markers:
        point_id = marker.get("sourcePointId")
        point = points_by_id.get(str(point_id))
        if not point:
            continue
        try:
            inferred[int(marker["markType"])].add(int(point["sourceCategoryId"]))
        except Exception:
            pass
    return inferred


def threshold_for(marker, scale):
    z7_threshold = DISTANCE_BY_MARK_TYPE_Z7.get(int(marker["markType"]), DEFAULT_DISTANCE_Z7)
    return z7_threshold * (scale / 2.0)


def candidate_categories(marker, inferred):
    mark_type = int(marker["markType"])
    categories = set(inferred.get(mark_type, set()))
    categories.update(MANUAL_CATEGORY_BY_MARK_TYPE.get(mark_type, set()))
    return categories


def link_file(path, points, points_by_id, details):
    payload = read_json(path)
    markers = payload.get("markers", [])
    scale = wiki_scale(payload)
    inferred = infer_existing_category_links(markers, points_by_id)
    points_by_category = defaultdict(list)
    for point in points:
        if str(point.get("sourcePointId")) not in details:
            continue
        points_by_category[int(point["sourceCategoryId"])].append(point)

    used_point_ids = {str(marker.get("sourcePointId")) for marker in markers if marker.get("sourcePointId")}
    edges = []
    for index, marker in enumerate(markers):
        if marker.get("sourcePointId"):
            continue
        pixel = marker.get("wikiMapPixel") or {}
        if not pixel.get("inBounds", True):
            continue
        categories = candidate_categories(marker, inferred)
        if not categories:
            continue
        wx = float(pixel["x"])
        wy = float(pixel["y"])
        max_distance = threshold_for(marker, scale)
        for category_id in categories:
            for point in points_by_category.get(category_id, []):
                point_id = str(point["sourcePointId"])
                if point_id in used_point_ids:
                    continue
                pp = point["wikiMapPixel"]
                px = float(pp["x"]) * scale
                py = float(pp["y"]) * scale
                distance = math.hypot(wx - px, wy - py)
                if distance <= max_distance:
                    edges.append((distance, index, point_id, point))

    edges.sort(key=lambda item: item[0])
    linked_markers = set()
    newly_used = set()
    updates = []
    for distance, index, point_id, point in edges:
        if index in linked_markers or point_id in used_point_ids or point_id in newly_used:
            continue
        marker = markers[index]
        marker["sourceName"] = "17173"
        marker["sourceUrl"] = point.get("sourceUrl") or "https://map.17173.com/rocom/maps/shijie"
        marker["sourcePointId"] = int(point["sourcePointId"])
        marker["sourceCategoryName"] = point.get("sourceCategoryName") or ""
        marker["sourceCategoryId"] = int(point["sourceCategoryId"])
        linked_markers.add(index)
        newly_used.add(point_id)
        updates.append({
            "markType": int(marker["markType"]),
            "markTypeName": marker.get("markTypeName", ""),
            "sourceCategoryId": int(point["sourceCategoryId"]),
            "sourceCategoryName": point.get("sourceCategoryName", ""),
            "distance": round(distance, 3),
            "sourcePointId": int(point["sourcePointId"]),
        })

    if updates:
        write_json(path, payload)
    by_type = Counter((item["markTypeName"], item["sourceCategoryName"]) for item in updates)
    return {
        "path": str(path.relative_to(PROJECT_DIR)),
        "scale": scale,
        "added": len(updates),
        "byType": [
            {"wiki": wiki, "17173": source, "count": count}
            for (wiki, source), count in by_type.most_common()
        ],
        "maxDistance": max((item["distance"] for item in updates), default=0.0),
    }


def main():
    points_payload = read_json(POINTS_PATH)
    details = read_json(DETAILS_PATH).get("details", {})
    points = points_payload.get("points", [])
    points_by_id = {str(point["sourcePointId"]): point for point in points}
    summaries = [link_file(path, points, points_by_id, details) for path in WIKI_PATHS]
    summary = {
        "version": 1,
        "sourcePoints": len(points),
        "details": len(details),
        "files": summaries,
    }
    write_json(SUMMARY_PATH, summary)
    for item in summaries:
        print(f"{item['path']}: added {item['added']} links, max distance {item['maxDistance']}")


if __name__ == "__main__":
    main()
