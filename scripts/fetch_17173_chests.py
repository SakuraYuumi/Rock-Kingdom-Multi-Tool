import csv
import json
import math
import os
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")

SOURCE_PAGE = "https://map.17173.com/rocom/maps/shijie"
LOCATION_API = "https://terra-api.17173.com/app/location/list?mapIds=4010"
DUPLICATE_DISTANCE_PX = 24

SOURCE_TILE_ZOOM = 12
SOURCE_TILE_SIZE = 256
SOURCE_TILE_X_MIN = 2032
SOURCE_TILE_Y_MIN = 2032
SOURCE_WORLD_SIZE = SOURCE_TILE_SIZE * (2 ** SOURCE_TILE_ZOOM)

# Fitted by registering dev_artifacts/17173/alignment/17173_rocom_z12_stitched.png to the wiki z6
# basemap. The two maps are the same pixel scale, but the wiki map is a crop of
# the 17173 tile space rather than a direct resize.
TRANSFORM_X = (1.000007219550505, -0.0000889857547223961, -486.2928464737367)
TRANSFORM_Y = (-0.000024905604790605112, 0.9990897235965729, -662.7596392208782)

WIKI_COORD_MIN = -3072
WIKI_PIXEL_PER_COORD = 0.5

SOURCE_CATEGORY_NAMES = {
    17310030001: "宝箱",
    17310030031: "精灵的宝藏",
}

LEGACY_SOURCE_MARK_TYPES = set(SOURCE_CATEGORY_NAMES)
SOURCE_ICON_URLS = {
    17310030001: "https://ue.17173cdn.com/a/terra/icon/rocom/17310030001.png",
    17310030031: "https://ue.17173cdn.com/a/terra/icon/rocom/17310030031.png",
}

CHEST_TYPE_NAMES = {
    "普通宝箱": 301,
    "稀有宝箱": 302,
    "珍贵宝箱": 303,
    "华丽宝箱": 304,
    "普通系宝箱": 305,
    "草系宝箱": 306,
    "火系宝箱": 307,
    "水系宝箱": 308,
    "光系宝箱": 309,
    "地系宝箱": 310,
    "冰系宝箱": 311,
    "龙系宝箱": 312,
    "电系宝箱": 313,
    "毒系宝箱": 314,
    "虫系宝箱": 315,
    "武系宝箱": 316,
    "翼系宝箱": 317,
    "萌系宝箱": 318,
    "幽系宝箱": 319,
    "恶系宝箱": 320,
    "机械系宝箱": 321,
    "幻系宝箱": 322,
}

ELEMENT_RULES = (
    ("普通系宝箱", ("普通系", "贵重宝箱（普通", "贵重宝箱(普通", "属性宝箱（普通", "属性宝箱(普通")),
    ("草系宝箱", ("草系", "（草", "(草")),
    ("火系宝箱", ("火系", "（火", "(火")),
    ("水系宝箱", ("水系", "（水", "(水")),
    ("光系宝箱", ("光系", "（光", "(光")),
    ("地系宝箱", ("地系", "地面系", "岩系", "（地", "(地", "（岩", "(岩")),
    ("冰系宝箱", ("冰系", "（冰", "(冰")),
    ("龙系宝箱", ("龙系", "（龙", "(龙")),
    ("电系宝箱", ("电系", "（电", "(电")),
    ("毒系宝箱", ("毒系", "（毒", "(毒")),
    ("虫系宝箱", ("虫系", "（虫", "(虫")),
    ("武系宝箱", ("武系", "战斗系", "（武", "(武")),
    ("翼系宝箱", ("翼系", "翼属性", "（翼", "(翼")),
    ("萌系宝箱", ("萌系", "（萌", "(萌")),
    ("幽系宝箱", ("幽系", "幽灵系", "（幽", "(幽")),
    ("恶系宝箱", ("恶系", "恶魔", "（恶", "(恶")),
    ("机械系宝箱", ("机械系", "机械宝箱", "（机械", "(机械")),
    ("幻系宝箱", ("幻系", "（幻", "(幻")),
)

NEW_CHEST_CATEGORIES = {
    "精灵的宝藏": {
        "markType": 171730031,
        "icon": SOURCE_ICON_URLS[17310030031],
    },
    "闪光点宝箱": {
        "markType": 171730101,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
    "挖掘宝箱": {
        "markType": 171730102,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
    "露天宝箱": {
        "markType": 171730103,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
    "地下宝箱": {
        "markType": 171730104,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
    "精灵翻找宝箱": {
        "markType": 171730105,
        "icon": SOURCE_ICON_URLS[17310030031],
    },
    "翻找宝箱": {
        "markType": 171730106,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
    "观察宝箱": {
        "markType": 171730107,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
    "NPC宝箱": {
        "markType": 171730108,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
    "钓鱼宝箱": {
        "markType": 171730109,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
    "交互宝箱": {
        "markType": 171730110,
        "icon": SOURCE_ICON_URLS[17310030001],
    },
}

NEW_MARK_TYPES = {item["markType"] for item in NEW_CHEST_CATEGORIES.values()}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex 17173 coordinate fetcher)",
    "Referer": SOURCE_PAGE,
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_bytes(url):
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=30) as response:
        return response.read()


def fetch_json(url):
    return json.loads(fetch_bytes(url).decode("utf-8-sig"))


def read_json(path):
    with open(path, "r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def safe_filename(text):
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = text.replace("（", "(").replace("）", ")")
    return text.strip()


def to_17173_pixel(point):
    lng = float(point["longitude"])
    lat = max(min(float(point["latitude"]), 85.05112878), -85.05112878)
    lat_rad = math.radians(lat)
    world_x = (lng + 180.0) / 360.0 * SOURCE_WORLD_SIZE
    world_y = (
        1.0
        - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi
    ) / 2.0 * SOURCE_WORLD_SIZE
    x = world_x - SOURCE_TILE_X_MIN * SOURCE_TILE_SIZE
    y = world_y - SOURCE_TILE_Y_MIN * SOURCE_TILE_SIZE
    return x, y


def to_wiki_pixel(point):
    x, y = to_17173_pixel(point)
    pixel_x = TRANSFORM_X[0] * x + TRANSFORM_X[1] * y + TRANSFORM_X[2]
    pixel_y = TRANSFORM_Y[0] * x + TRANSFORM_Y[1] * y + TRANSFORM_Y[2]
    return pixel_x, pixel_y


def pixel_to_wiki_coord(x, y):
    return (
        x / WIKI_PIXEL_PER_COORD + WIKI_COORD_MIN,
        y / WIKI_PIXEL_PER_COORD + WIKI_COORD_MIN,
    )


def distance(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def is_duplicate(pixel, existing_pixels):
    return any(distance(pixel, item) <= DUPLICATE_DISTANCE_PX for item in existing_pixels)


def build_summary(categories, markers, fetched_at, groups):
    counts_by_group = {}
    counts_by_type = {}
    for marker in markers:
        counts_by_group[marker["group"]] = counts_by_group.get(marker["group"], 0) + 1
        key = f"{marker['markType']} {marker['markTypeName']}"
        counts_by_type[key] = counts_by_type.get(key, 0) + 1

    return {
        "sourcePage": "https://wiki.biligame.com/rocom/大地图",
        "categoryUrl": "https://wiki.biligame.com/rocom/Data:Mapnew/type/json?action=raw",
        "pointUrlTemplate": "https://wiki.biligame.com/rocom/Data:Mapnew/type/{mark_type}/json?action=raw",
        "fetchedAt": fetched_at,
        "selectedGroups": list(groups),
        "categoryCount": len(categories),
        "markerCount": len(markers),
        "countsByGroup": counts_by_group,
        "countsByType": counts_by_type,
        "extraSources": {
            "17173": {
                "sourcePage": SOURCE_PAGE,
                "locationApi": LOCATION_API,
                "duplicateDistancePx": DUPLICATE_DISTANCE_PX,
            }
        },
    }


def write_csv(path, rows):
    fieldnames = [
        "id",
        "group",
        "markType",
        "markTypeName",
        "title",
        "lat",
        "lng",
        "layer",
        "time",
        "version",
        "sourceUrl",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def remove_legacy_source_categories(category_payload):
    categories = category_payload.get("categories", [])
    filtered = [
        item
        for item in categories
        if item.get("markType") not in LEGACY_SOURCE_MARK_TYPES
    ]
    removed = len(categories) - len(filtered)
    category_payload["categories"] = filtered
    category_payload.setdefault("meta", {})["totalCategories"] = len(filtered)
    return removed


def ensure_new_source_categories(category_payload):
    categories = category_payload.get("categories", [])
    existing = {str(item.get("markType")) for item in categories}
    added = 0
    for name, info in NEW_CHEST_CATEGORIES.items():
        if str(info["markType"]) in existing:
            continue
        categories.append({
            "group": "宝箱",
            "markType": info["markType"],
            "markTypeName": name,
            "length": "",
            "defaultShow": "",
            "collectible": "",
            "icon": info["icon"],
            "desc": "17173 洛克王国世界互动地图新增宝箱分类",
        })
        added += 1
    category_payload["categories"] = categories
    category_payload.setdefault("meta", {})["totalCategories"] = len(categories)
    return added


def sync_source_icons(icon_payload):
    icons = icon_payload.setdefault("icons", {})
    removed = 0
    for mark_type in LEGACY_SOURCE_MARK_TYPES:
        if icons.pop(str(mark_type), None) is not None:
            removed += 1

    icon_dir = os.path.join(ASSETS_DIR, "icons", "17173")
    os.makedirs(icon_dir, exist_ok=True)
    added = 0
    for name, info in NEW_CHEST_CATEGORIES.items():
        mark_type = str(info["markType"])
        icon_url = info["icon"]
        ext = os.path.splitext(icon_url.split("?")[0])[1] or ".png"
        local_name = f"{mark_type}_{safe_filename(name)}{ext.lower()}"
        local_path = os.path.join(icon_dir, local_name)
        if not os.path.exists(local_path):
            with open(local_path, "wb") as file:
                file.write(fetch_bytes(icon_url))
        if mark_type not in icons:
            added += 1
        icons[mark_type] = {
            "group": "宝箱",
            "markType": info["markType"],
            "markTypeName": name,
            "wikiFileName": "",
            "wikiFileTitle": "",
            "sourceUrl": icon_url,
            "descriptionUrl": SOURCE_PAGE,
            "localPath": os.path.abspath(local_path),
            "relativePath": os.path.relpath(local_path, PROJECT_DIR).replace("\\", "/"),
        }

    icon_payload.setdefault("meta", {})["iconCount"] = len(icons)
    icon_payload["meta"]["fetchedAt"] = utc_now()
    return removed, added


def new_category(name, categories_by_type):
    return categories_by_type[str(NEW_CHEST_CATEGORIES[name]["markType"])]


def classify_chest_category(title, source_category_id, categories_by_type):
    normalized = (title or "").strip()

    for type_name, keywords in ELEMENT_RULES:
        if any(keyword in normalized for keyword in keywords):
            return categories_by_type[str(CHEST_TYPE_NAMES[type_name])]

    if "华丽" in normalized or "豪华" in normalized:
        return categories_by_type[str(CHEST_TYPE_NAMES["华丽宝箱"])]
    if "珍贵" in normalized or "贵重" in normalized or "传说" in normalized:
        return categories_by_type[str(CHEST_TYPE_NAMES["珍贵宝箱"])]
    if "稀有" in normalized:
        return categories_by_type[str(CHEST_TYPE_NAMES["稀有宝箱"])]

    if source_category_id == 17310030031 or "精灵宝" in normalized or "精灵的宝藏" in normalized or normalized == "宝藏":
        return new_category("精灵的宝藏", categories_by_type)
    if "精灵" in normalized and any(keyword in normalized for keyword in ("翻找", "查找", "搜索", "探索", "发现", "挖掘")):
        return new_category("精灵翻找宝箱", categories_by_type)
    if any(keyword in normalized for keyword in ("闪光点", "闪光", "光点", "发光")):
        return new_category("闪光点宝箱", categories_by_type)
    if any(keyword in normalized for keyword in ("挖掘", "挖宝", "挖箱", "土地里")):
        return new_category("挖掘宝箱", categories_by_type)
    if any(keyword in normalized for keyword in ("露天", "漏天", "裸露", "地上")):
        return new_category("露天宝箱", categories_by_type)
    if any(keyword in normalized for keyword in ("地下", "底下", "地底", "洞内", "山洞")):
        return new_category("地下宝箱", categories_by_type)
    if any(keyword in normalized for keyword in ("翻找", "查找", "搜索", "探索", "发现")):
        return new_category("翻找宝箱", categories_by_type)
    if "观察" in normalized:
        return new_category("观察宝箱", categories_by_type)
    if any(keyword in normalized for keyword in ("NPC", "npc", "对话", "任务", "击杀怪物", "气象员", "气象研究")):
        return new_category("NPC宝箱", categories_by_type)
    if "钓鱼" in normalized:
        return new_category("钓鱼宝箱", categories_by_type)
    if any(keyword in normalized for keyword in ("交互", "木牌", "石碑", "机器", "平台")):
        return new_category("交互宝箱", categories_by_type)

    return categories_by_type[str(CHEST_TYPE_NAMES["普通宝箱"])]


def main():
    fetched_at = utc_now()
    points_path = os.path.join(DATA_DIR, "wiki_resource_points.json")
    pixels_path = os.path.join(DATA_DIR, "wiki_resource_points_pixels_z6.json")
    by_type_path = os.path.join(DATA_DIR, "wiki_resource_points_by_type.json")
    categories_path = os.path.join(DATA_DIR, "wiki_map_categories.json")
    icons_path = os.path.join(DATA_DIR, "wiki_resource_icons.json")

    points_payload = read_json(points_path)
    pixels_payload = read_json(pixels_path)
    by_type_payload = read_json(by_type_path)
    categories_payload = read_json(categories_path)
    icons_payload = read_json(icons_path)

    legacy_categories_removed = remove_legacy_source_categories(categories_payload)
    new_categories_added = ensure_new_source_categories(categories_payload)
    legacy_icons_removed, new_icons_added = sync_source_icons(icons_payload)

    source_mark_types = LEGACY_SOURCE_MARK_TYPES | NEW_MARK_TYPES
    categories_by_type = {
        str(item["markType"]): item
        for item in categories_payload["categories"]
    }
    original_marker_count = len(points_payload["markers"])
    markers = [
        marker
        for marker in points_payload["markers"]
        if marker.get("markType") not in source_mark_types and marker.get("sourceName") != "17173"
    ]
    removed_existing_17173 = original_marker_count - len(markers)
    points_payload["markers"] = markers

    existing_ids = {marker.get("id") for marker in markers}
    wiki_overlap_pixels = [
        {
            "x": marker["wikiMapPixel"]["x"],
            "y": marker["wikiMapPixel"]["y"],
        }
        for marker in pixels_payload["markers"]
        if (
            marker.get("group") == "宝箱"
            and marker.get("markType") not in source_mark_types
            and marker.get("sourceName") != "17173"
            and marker.get("wikiMapPixel", {}).get("inBounds")
        )
    ]

    location_payload = fetch_json(LOCATION_API)
    source_points = [
        item
        for item in location_payload.get("data", [])
        if item.get("category_id") in SOURCE_CATEGORY_NAMES
    ]

    added_markers = []
    skipped_existing = 0
    skipped_internal = 0
    seen_source_positions = set()
    for item in source_points:
        source_id = f"17173-{item['id']}"
        if source_id in existing_ids:
            skipped_existing += 1
            continue

        pixel_x, pixel_y = to_wiki_pixel(item)
        pixel = {"x": pixel_x, "y": pixel_y}
        if is_duplicate(pixel, wiki_overlap_pixels):
            skipped_existing += 1
            continue

        source_key = (
            item["category_id"],
            item.get("title") or "",
            round(pixel_x),
            round(pixel_y),
        )
        if source_key in seen_source_positions:
            skipped_internal += 1
            continue
        seen_source_positions.add(source_key)

        category = classify_chest_category(item.get("title", ""), item["category_id"], categories_by_type)
        lng, lat = pixel_to_wiki_coord(pixel_x, pixel_y)
        marker = {
            "id": source_id,
            "group": category["group"],
            "markType": category["markType"],
            "markTypeName": category["markTypeName"],
            "title": item.get("title") or category["markTypeName"],
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "layer": "",
            "time": None,
            "version": None,
            "sourceUrl": SOURCE_PAGE,
            "sourceName": "17173",
            "sourceCategoryId": item["category_id"],
            "sourcePointId": item["id"],
            "sourceLatitude": item.get("latitude"),
            "sourceLongitude": item.get("longitude"),
            "sourceCategoryName": SOURCE_CATEGORY_NAMES.get(item["category_id"], ""),
        }

        existing_ids.add(source_id)
        markers.append(marker)
        added_markers.append(marker)

    all_categories = categories_payload["categories"]
    groups = points_payload.get("meta", {}).get("selectedGroups") or [
        "地点",
        "互动事件",
        "宝箱",
        "任务",
        "战斗",
        "精灵分布",
        "收集",
        "采集",
    ]
    summary = build_summary(all_categories, markers, fetched_at, groups)
    points_payload["meta"] = summary
    by_type_payload["meta"] = summary
    by_type_payload["types"] = {}

    by_group = {group: [] for group in groups}
    for marker in markers:
        by_group.setdefault(marker["group"], []).append(marker)
        key = str(marker["markType"])
        category = categories_by_type.get(key, {
            "group": marker["group"],
            "markType": marker["markType"],
            "markTypeName": marker["markTypeName"],
            "length": "",
            "defaultShow": "",
            "collectible": "",
            "icon": "",
            "desc": "",
        })
        entry = by_type_payload["types"].setdefault(key, {
            "category": category,
            "sourceUrl": marker.get("sourceUrl", ""),
            "points": [],
        })
        entry["points"].append(marker)

    write_json(categories_path, categories_payload)
    write_json(points_path, points_payload)
    write_json(by_type_path, by_type_payload)
    write_json(os.path.join(DATA_DIR, "wiki_resource_summary.json"), summary)
    write_csv(os.path.join(DATA_DIR, "wiki_resource_points.csv"), markers)
    write_json(icons_path, icons_payload)

    safe_names = {
        "采集": "gathering",
        "收集": "collection",
    }
    for group, group_markers in by_group.items():
        safe_name = safe_names.get(group, f"group_{group}")
        write_json(os.path.join(DATA_DIR, f"wiki_{safe_name}_points.json"), {
            "meta": build_summary(
                [item for item in all_categories if item["group"] == group],
                group_markers,
                fetched_at,
                [group],
            ),
            "markers": group_markers,
        })

    write_json(os.path.join(DATA_DIR, "17173_chest_merge_summary.json"), {
        "sourcePage": SOURCE_PAGE,
        "locationApi": LOCATION_API,
        "fetchedAt": fetched_at,
        "sourceCount": len(source_points),
        "addedCount": len(added_markers),
        "skippedExistingOrOverlap": skipped_existing,
        "skippedInternal": skipped_internal,
        "removedExisting17173": removed_existing_17173,
        "legacyCategoriesRemoved": legacy_categories_removed,
        "newCategoriesAdded": new_categories_added,
        "legacyIconsRemoved": legacy_icons_removed,
        "newIconsAdded": new_icons_added,
        "duplicateDistancePx": DUPLICATE_DISTANCE_PX,
        "coordinateTransform": {
            "sourceTileZoom": SOURCE_TILE_ZOOM,
            "sourceTileSize": SOURCE_TILE_SIZE,
            "sourceTileOrigin": {
                "x": SOURCE_TILE_X_MIN,
                "y": SOURCE_TILE_Y_MIN,
            },
            "sourcePixelSpace": "17173 z12 stitched WebMercator tile pixels",
            "targetPixelSpace": "wiki_G_z6.png pixels",
            "transformX": TRANSFORM_X,
            "transformY": TRANSFORM_Y,
            "alignmentNote": "The wiki basemap is a crop of the 17173 tile image, not a 3072-wide resize.",
        },
        "addedByType": {
            type_name: sum(1 for marker in added_markers if marker["markTypeName"] == type_name)
            for type_name in sorted({marker["markTypeName"] for marker in added_markers})
        },
    })

    print(f"17173 source points: {len(source_points)}")
    print(f"Added: {len(added_markers)}")
    print(f"Skipped existing/overlap: {skipped_existing}")
    print(f"Total markers: {len(markers)}")


if __name__ == "__main__":
    main()
