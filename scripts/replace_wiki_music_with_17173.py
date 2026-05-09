import csv
import json
import os
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")

SOURCE_PAGE = "https://map.17173.com/rocom/maps/shijie"
EXPORT_PATH = os.path.join(DATA_DIR, "17173_all_resources_wiki_coords.json")
WIKI_MUSIC_MARK_TYPE = 810
SOURCE_MUSIC_CATEGORY_ID = 17310030036
TARGET_GROUP = "收集"
TARGET_NAME = "乐谱"
SOURCE_NAME = "17173"
WIKI_MUSIC_ICON_RELATIVE_PATH = "assets/icons/wiki/810_乐谱.png"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex 17173 music replacer)",
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


def build_summary(categories, markers, fetched_at, groups, previous_meta):
    counts_by_group = {}
    counts_by_type = {}
    for marker in markers:
        counts_by_group[marker["group"]] = counts_by_group.get(marker["group"], 0) + 1
        key = f"{marker['markType']} {marker['markTypeName']}"
        counts_by_type[key] = counts_by_type.get(key, 0) + 1

    extra_sources = dict(previous_meta.get("extraSources", {}))
    extra_sources["17173Music"] = {
        "sourcePage": SOURCE_PAGE,
        "sourceFile": os.path.relpath(EXPORT_PATH, PROJECT_DIR).replace("\\", "/"),
        "sourceCategoryId": SOURCE_MUSIC_CATEGORY_ID,
        "sourceCategoryName": "崭新乐章",
        "targetName": TARGET_NAME,
        "note": "Wiki music score markers were replaced by 17173 music markers and renamed to 乐谱.",
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


def ensure_music_icon(icon_payload, old_markers, source_icon_url):
    icons = icon_payload.setdefault("icons", {})
    removed = 0
    if old_markers and icons.pop(str(WIKI_MUSIC_MARK_TYPE), None) is not None:
        removed = 1

    local_path = os.path.join(PROJECT_DIR, WIKI_MUSIC_ICON_RELATIVE_PATH)
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Missing wiki music icon: {local_path}")

    icons[str(SOURCE_MUSIC_CATEGORY_ID)] = {
        "group": TARGET_GROUP,
        "markType": SOURCE_MUSIC_CATEGORY_ID,
        "markTypeName": TARGET_NAME,
        "wikiFileName": "地图_点位_icon_音符.png",
        "wikiFileTitle": "File:地图_点位_icon_音符.png",
        "sourceUrl": "",
        "descriptionUrl": SOURCE_PAGE,
        "localPath": os.path.abspath(local_path),
        "relativePath": WIKI_MUSIC_ICON_RELATIVE_PATH,
    }
    icon_payload.setdefault("meta", {})["iconCount"] = len(icons)
    icon_payload["meta"]["fetchedAt"] = utc_now()
    return removed


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


def main():
    fetched_at = utc_now()
    points_path = os.path.join(DATA_DIR, "wiki_resource_points.json")
    categories_path = os.path.join(DATA_DIR, "wiki_map_categories.json")
    icons_path = os.path.join(DATA_DIR, "wiki_resource_icons.json")
    by_type_path = os.path.join(DATA_DIR, "wiki_resource_points_by_type.json")

    points_payload = read_json(points_path)
    categories_payload = read_json(categories_path)
    icons_payload = read_json(icons_path)
    export_payload = read_json(EXPORT_PATH)

    source_points = [
        point
        for point in export_payload.get("points", [])
        if point.get("sourceCategoryId") == SOURCE_MUSIC_CATEGORY_ID
    ]
    source_icon_url = next((point.get("sourceCategoryIcon", "") for point in source_points), "")

    old_music_markers = [
        marker
        for marker in points_payload["markers"]
        if marker.get("markType") == WIKI_MUSIC_MARK_TYPE
    ]
    markers = [
        marker
        for marker in points_payload["markers"]
        if marker.get("markType") != WIKI_MUSIC_MARK_TYPE
        and marker.get("markType") != SOURCE_MUSIC_CATEGORY_ID
    ]

    new_markers = []
    for point in source_points:
        new_markers.append({
            "id": point["id"],
            "group": TARGET_GROUP,
            "markType": SOURCE_MUSIC_CATEGORY_ID,
            "markTypeName": TARGET_NAME,
            "title": point.get("title") or TARGET_NAME,
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
        })
    markers.extend(new_markers)
    points_payload["markers"] = markers

    old_categories = [
        category
        for category in categories_payload["categories"]
        if category.get("markType") == WIKI_MUSIC_MARK_TYPE
        or category.get("markType") == SOURCE_MUSIC_CATEGORY_ID
    ]
    categories = [
        category
        for category in categories_payload["categories"]
        if category.get("markType") != WIKI_MUSIC_MARK_TYPE
        and category.get("markType") != SOURCE_MUSIC_CATEGORY_ID
    ]
    categories.append({
        "group": TARGET_GROUP,
        "markType": SOURCE_MUSIC_CATEGORY_ID,
        "markTypeName": TARGET_NAME,
        "length": "",
        "defaultShow": "",
        "collectible": "",
        "icon": "{{filepath:地图_点位_icon_音符.png}}",
        "desc": "17173 洛克王国世界互动地图崭新乐章，程序中显示为乐谱",
    })
    categories_payload["categories"] = categories
    categories_payload.setdefault("meta", {})["totalCategories"] = len(categories)
    categories_payload["meta"]["updatedAt"] = fetched_at

    removed_icons = ensure_music_icon(icons_payload, old_music_markers, source_icon_url)

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
    summary = build_summary(categories, markers, fetched_at, groups, points_payload.get("meta", {}))
    points_payload["meta"] = summary

    write_json(categories_path, categories_payload)
    write_json(points_path, points_payload)
    write_json(by_type_path, rebuild_by_type(markers, categories_by_type, summary))
    write_json(os.path.join(DATA_DIR, "wiki_resource_summary.json"), summary)
    write_json(icons_path, icons_payload)
    write_csv(os.path.join(DATA_DIR, "wiki_resource_points.csv"), markers)
    write_group_files(categories, markers, fetched_at, groups, summary)

    write_json(os.path.join(DATA_DIR, "17173_music_replace_summary.json"), {
        "sourcePage": SOURCE_PAGE,
        "sourceFile": os.path.relpath(EXPORT_PATH, PROJECT_DIR).replace("\\", "/"),
        "fetchedAt": fetched_at,
        "removedWikiMusicMarkType": WIKI_MUSIC_MARK_TYPE,
        "removedWikiMusicMarkers": len(old_music_markers),
        "removedMusicCategories": len(old_categories),
        "removedMusicIconEntries": removed_icons,
        "sourceMusicCategoryId": SOURCE_MUSIC_CATEGORY_ID,
        "sourceMusicCategoryName": "崭新乐章",
        "targetMusicName": TARGET_NAME,
        "added17173MusicMarkers": len(new_markers),
        "totalMarkers": len(markers),
    })

    print(f"Removed wiki music markers: {len(old_music_markers)}")
    print(f"Added 17173 music markers: {len(new_markers)}")
    print(f"Total markers: {len(markers)}")


if __name__ == "__main__":
    main()
