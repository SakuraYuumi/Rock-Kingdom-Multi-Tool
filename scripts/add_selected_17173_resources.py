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
EXPORT_PATH = os.path.join(DATA_DIR, "17173_all_resources_wiki_coords.json")
SOURCE_NAME = "17173"
BLACK_MARK_TYPE = 602
OUTDOOR_BATTLE_OVERLAP_PX = 32

TARGETS = {
    17310030033: {
        "group": "收集",
        "name": "魔法石",
    },
    17310030034: {
        "group": "收集",
        "name": "魔法",
    },
    17310030025: {
        "group": "地点",
        "name": "克罗修斯的试炼",
        "titleContains": "克罗修斯的试炼",
    },
    17310030026: {
        "group": "战斗",
        "name": "露天对战",
        "skipBlackOverlap": True,
    },
    17310030027: {
        "group": "任务",
        "name": "支线任务",
    },
    17310030028: {
        "group": "任务",
        "name": "未分类任务",
    },
    17310030029: {
        "group": "地点",
        "name": "挑战小游戏",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex 17173 selected resource importer)",
    "Referer": SOURCE_PAGE,
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path):
    with open(path, "r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


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


def safe_filename(text):
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = text.replace("（", "(").replace("）", ")")
    return text.strip() or "resource"


def fetch_bytes(url):
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=30) as response:
        return response.read()


def distance(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def is_near_black_marker(point, black_pixels):
    pixel = point["wikiMapPixel"]
    return any(distance(pixel, item) <= OUTDOOR_BATTLE_OVERLAP_PX for item in black_pixels)


def accepts_point(point, target, black_pixels):
    title_filter = target.get("titleContains")
    if title_filter and title_filter not in (point.get("title") or ""):
        return False
    if target.get("skipBlackOverlap") and is_near_black_marker(point, black_pixels):
        return False
    return True


def ensure_icons(icon_payload, selected_points_by_category):
    icons = icon_payload.setdefault("icons", {})
    icon_dir = os.path.join(ASSETS_DIR, "icons", "17173_selected")
    os.makedirs(icon_dir, exist_ok=True)
    added = 0
    updated = 0

    for category_id, points in selected_points_by_category.items():
        if not points:
            continue
        target = TARGETS[category_id]
        icon_url = next((point.get("sourceCategoryIcon", "") for point in points), "")
        if not icon_url:
            continue
        ext = os.path.splitext(icon_url.split("?")[0])[1] or ".png"
        local_name = f"{category_id}_{safe_filename(target['name'])}{ext.lower()}"
        local_path = os.path.join(icon_dir, local_name)
        if not os.path.exists(local_path):
            with open(local_path, "wb") as file:
                file.write(fetch_bytes(icon_url))
        key = str(category_id)
        if key in icons:
            updated += 1
        else:
            added += 1
        icons[key] = {
            "group": target["group"],
            "markType": category_id,
            "markTypeName": target["name"],
            "wikiFileName": "",
            "wikiFileTitle": "",
            "sourceUrl": icon_url,
            "descriptionUrl": SOURCE_PAGE,
            "localPath": os.path.abspath(local_path),
            "relativePath": os.path.relpath(local_path, PROJECT_DIR).replace("\\", "/"),
        }

    icon_payload.setdefault("meta", {})["iconCount"] = len(icons)
    icon_payload["meta"]["fetchedAt"] = utc_now()
    return added, updated


def build_summary(categories, markers, fetched_at, groups, previous_meta, import_summary):
    counts_by_group = {}
    counts_by_type = {}
    for marker in markers:
        counts_by_group[marker["group"]] = counts_by_group.get(marker["group"], 0) + 1
        key = f"{marker['markType']} {marker['markTypeName']}"
        counts_by_type[key] = counts_by_type.get(key, 0) + 1

    extra_sources = dict(previous_meta.get("extraSources", {}))
    extra_sources["17173SelectedResources"] = {
        "sourcePage": SOURCE_PAGE,
        "sourceFile": os.path.relpath(EXPORT_PATH, PROJECT_DIR).replace("\\", "/"),
        "targetCategories": {
            str(category_id): {
                "name": target["name"],
                "group": target["group"],
            }
            for category_id, target in TARGETS.items()
        },
        "outdoorBattleOverlapPx": OUTDOOR_BATTLE_OVERLAP_PX,
        "importedByType": import_summary,
    }

    return {
        "sourcePage": previous_meta.get("sourcePage", "https://wiki.biligame.com/rocom/大地图"),
        "categoryUrl": previous_meta.get("categoryUrl", "https://wiki.biligame.com/rocom/Data:Mapnew/type/json?action=raw"),
        "pointUrlTemplate": previous_meta.get(
            "pointUrlTemplate",
            "https://wiki.biligame.com/rocom/Data:Mapnew/type/{mark_type}/json?action=raw",
        ),
        "fetchedAt": fetched_at,
        "selectedGroups": list(groups),
        "categoryCount": len(categories),
        "markerCount": len(markers),
        "countsByGroup": counts_by_group,
        "countsByType": counts_by_type,
        "extraSources": extra_sources,
    }


def rebuild_by_type(markers, categories_by_type, summary):
    payload = {
        "meta": summary,
        "types": {},
    }
    for marker in markers:
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
        entry = payload["types"].setdefault(key, {
            "category": category,
            "sourceUrl": marker.get("sourceUrl", ""),
            "points": [],
        })
        entry["points"].append(marker)
    return payload


def group_summary(summary, categories, group, group_markers, fetched_at):
    counts_by_type = {}
    for marker in group_markers:
        key = f"{marker['markType']} {marker['markTypeName']}"
        counts_by_type[key] = counts_by_type.get(key, 0) + 1
    return {
        **summary,
        "selectedGroups": [group],
        "categoryCount": len([item for item in categories if item["group"] == group]),
        "markerCount": len(group_markers),
        "countsByGroup": {group: len(group_markers)},
        "countsByType": counts_by_type,
        "fetchedAt": fetched_at,
    }


def write_group_files(categories, markers, fetched_at, groups, summary):
    safe_names = {
        "采集": "gathering",
        "收集": "collection",
    }
    specific_names = {
        "地点": "wiki_location_points.json",
        "互动事件": "wiki_interactive_event_points.json",
        "宝箱": "wiki_treasure_points.json",
        "采集": "wiki_gathering_points.json",
        "收集": "wiki_collection_points.json",
        "任务": "wiki_quest_points.json",
        "战斗": "wiki_battle_points.json",
        "精灵分布": "wiki_pet_distribution_points.json",
    }
    by_group = {group: [] for group in groups}
    for marker in markers:
        by_group.setdefault(marker["group"], []).append(marker)

    for group, group_markers in by_group.items():
        payload = {
            "meta": group_summary(summary, categories, group, group_markers, fetched_at),
            "markers": group_markers,
        }
        safe_name = safe_names.get(group, f"group_{group}")
        write_json(os.path.join(DATA_DIR, f"wiki_{safe_name}_points.json"), payload)
        if group in specific_names:
            write_json(os.path.join(DATA_DIR, specific_names[group]), payload)


def marker_from_point(point, target):
    return {
        "id": point["id"],
        "group": target["group"],
        "markType": int(point["sourceCategoryId"]),
        "markTypeName": target["name"],
        "title": point.get("title") or target["name"],
        "lat": point["wikiCoord"]["lat"],
        "lng": point["wikiCoord"]["lng"],
        "layer": "",
        "time": None,
        "version": None,
        "sourceUrl": SOURCE_PAGE,
        "sourceName": SOURCE_NAME,
        "sourceGroupName": point.get("sourceGroupName"),
        "sourceCategoryId": point.get("sourceCategoryId"),
        "sourceCategoryName": point.get("sourceCategoryName"),
        "sourcePointId": point.get("sourcePointId"),
        "sourceLatitude": point.get("sourceLatitude"),
        "sourceLongitude": point.get("sourceLongitude"),
    }


def main():
    fetched_at = utc_now()
    points_path = os.path.join(DATA_DIR, "wiki_resource_points.json")
    pixels_path = os.path.join(DATA_DIR, "wiki_resource_points_pixels_z6.json")
    categories_path = os.path.join(DATA_DIR, "wiki_map_categories.json")
    icons_path = os.path.join(DATA_DIR, "wiki_resource_icons.json")
    by_type_path = os.path.join(DATA_DIR, "wiki_resource_points_by_type.json")

    points_payload = read_json(points_path)
    pixels_payload = read_json(pixels_path)
    categories_payload = read_json(categories_path)
    icons_payload = read_json(icons_path)
    export_payload = read_json(EXPORT_PATH)

    target_ids = set(TARGETS)
    black_pixels = [
        marker["wikiMapPixel"]
        for marker in pixels_payload.get("markers", [])
        if marker.get("markType") == BLACK_MARK_TYPE
        and marker.get("wikiMapPixel", {}).get("inBounds")
    ]

    original_count = len(points_payload["markers"])
    markers = [
        marker
        for marker in points_payload["markers"]
        if not (
            marker.get("sourceName") == SOURCE_NAME
            and marker.get("markType") in target_ids
        )
    ]
    removed_existing = original_count - len(markers)

    selected_points_by_category = {category_id: [] for category_id in target_ids}
    skipped_by_category = {category_id: 0 for category_id in target_ids}
    for point in export_payload.get("points", []):
        category_id = point.get("sourceCategoryId")
        if category_id not in TARGETS:
            continue
        target = TARGETS[category_id]
        if accepts_point(point, target, black_pixels):
            selected_points_by_category[category_id].append(point)
        else:
            skipped_by_category[category_id] += 1

    new_markers = []
    for category_id in sorted(TARGETS):
        target = TARGETS[category_id]
        for point in selected_points_by_category[category_id]:
            new_markers.append(marker_from_point(point, target))
    markers.extend(new_markers)
    points_payload["markers"] = markers

    categories = [
        category
        for category in categories_payload["categories"]
        if category.get("markType") not in target_ids
    ]
    for category_id in sorted(TARGETS):
        target = TARGETS[category_id]
        points = selected_points_by_category[category_id]
        icon_url = next((point.get("sourceCategoryIcon", "") for point in points), "")
        categories.append({
            "group": target["group"],
            "markType": category_id,
            "markTypeName": target["name"],
            "length": "",
            "defaultShow": "",
            "collectible": "",
            "icon": icon_url,
            "desc": "17173 洛克王国世界互动地图新增分类",
        })
    categories_payload["categories"] = categories
    categories_payload.setdefault("meta", {})["totalCategories"] = len(categories)
    categories_payload["meta"]["updatedAt"] = fetched_at

    icon_added, icon_updated = ensure_icons(icons_payload, selected_points_by_category)

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
    categories_by_type = {str(category["markType"]): category for category in categories}
    imported_by_type = {
        TARGETS[category_id]["name"]: len(selected_points_by_category[category_id])
        for category_id in sorted(TARGETS)
    }
    summary = build_summary(categories, markers, fetched_at, groups, points_payload.get("meta", {}), imported_by_type)
    points_payload["meta"] = summary

    write_json(categories_path, categories_payload)
    write_json(points_path, points_payload)
    write_json(by_type_path, rebuild_by_type(markers, categories_by_type, summary))
    write_json(os.path.join(DATA_DIR, "wiki_resource_summary.json"), summary)
    write_json(icons_path, icons_payload)
    write_csv(os.path.join(DATA_DIR, "wiki_resource_points.csv"), markers)
    write_group_files(categories, markers, fetched_at, groups, summary)

    write_json(os.path.join(DATA_DIR, "17173_selected_resources_import_summary.json"), {
        "sourcePage": SOURCE_PAGE,
        "sourceFile": os.path.relpath(EXPORT_PATH, PROJECT_DIR).replace("\\", "/"),
        "fetchedAt": fetched_at,
        "removedExisting17173SelectedMarkers": removed_existing,
        "addedCount": len(new_markers),
        "addedByType": imported_by_type,
        "skippedByType": {
            TARGETS[category_id]["name"]: skipped_by_category[category_id]
            for category_id in sorted(TARGETS)
        },
        "outdoorBattleOverlapPx": OUTDOOR_BATTLE_OVERLAP_PX,
        "wikiBlackMarkerCount": len(black_pixels),
        "iconEntriesAdded": icon_added,
        "iconEntriesUpdated": icon_updated,
        "totalMarkers": len(markers),
    })

    print(f"Removed existing selected 17173 markers: {removed_existing}")
    print(f"Added selected 17173 markers: {len(new_markers)}")
    print(f"Skipped selected 17173 markers: {sum(skipped_by_category.values())}")
    print(f"Total markers: {len(markers)}")


if __name__ == "__main__":
    main()
