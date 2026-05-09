import csv
import json
import os
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")

SPIRIT_GROUP = "精灵分布"
SOURCE_SPIRIT_GROUP = "精灵"
SOURCE_NAME = "17173"
SOURCE_PAGE = "https://map.17173.com/rocom/maps/shijie"
EXPORT_PATH = os.path.join(DATA_DIR, "17173_all_resources_wiki_coords.json")
EXCLUDED_SOURCE_SPIRIT_CATEGORIES = {
    17310030023: "未分类精灵",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex 17173 spirit replacer)",
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
    extra_sources["17173Spirits"] = {
        "sourcePage": SOURCE_PAGE,
        "sourceFile": os.path.relpath(EXPORT_PATH, PROJECT_DIR).replace("\\", "/"),
        "targetGroup": SPIRIT_GROUP,
        "note": "Wiki spirit distribution markers were replaced by 17173 spirit markers.",
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


def ensure_spirit_icons(icon_payload, spirit_points):
    icons = icon_payload.setdefault("icons", {})
    removed = 0
    old_spirit_types = {
        str(point["markType"])
        for point in spirit_points["oldMarkers"]
    }
    for mark_type in old_spirit_types:
        if icons.pop(mark_type, None) is not None:
            removed += 1

    icon_dir = os.path.join(ASSETS_DIR, "icons", "17173_spirits")
    os.makedirs(icon_dir, exist_ok=True)
    added = 0
    for category in spirit_points["categories"].values():
        mark_type = str(category["markType"])
        icon_url = category.get("icon", "")
        if not icon_url:
            continue
        ext = os.path.splitext(icon_url.split("?")[0])[1] or ".png"
        local_name = f"{mark_type}_{safe_filename(category['markTypeName'])}{ext.lower()}"
        local_path = os.path.join(icon_dir, local_name)
        if not os.path.exists(local_path):
            with open(local_path, "wb") as file:
                file.write(fetch_bytes(icon_url))
        if mark_type not in icons:
            added += 1
        icons[mark_type] = {
            "group": SPIRIT_GROUP,
            "markType": category["markType"],
            "markTypeName": category["markTypeName"],
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


def prepare_spirit_points(export_payload):
    source_points = [
        point
        for point in export_payload.get("points", [])
        if point.get("sourceGroupName") == SOURCE_SPIRIT_GROUP
        and point.get("sourceCategoryId") not in EXCLUDED_SOURCE_SPIRIT_CATEGORIES
    ]
    categories = {}
    markers = []
    for point in source_points:
        mark_type = int(point["sourceCategoryId"])
        categories.setdefault(mark_type, {
            "group": SPIRIT_GROUP,
            "markType": mark_type,
            "markTypeName": point["sourceCategoryName"],
            "length": "",
            "defaultShow": "",
            "collectible": "",
            "icon": point.get("sourceCategoryIcon", ""),
            "desc": "17173 洛克王国世界互动地图精灵分类",
        })
        markers.append({
            "id": point["id"],
            "group": SPIRIT_GROUP,
            "markType": mark_type,
            "markTypeName": point["sourceCategoryName"],
            "title": point.get("title") or point["sourceCategoryName"],
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
    return source_points, categories, markers


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
        group_categories = [item for item in categories if item["group"] == group]
        group_summary = {
            **summary,
            "selectedGroups": [group],
            "categoryCount": len(group_categories),
            "markerCount": len(group_markers),
            "countsByGroup": {group: len(group_markers)},
            "countsByType": {
                f"{marker['markType']} {marker['markTypeName']}": sum(
                    1
                    for item in group_markers
                    if item["markType"] == marker["markType"]
                )
                for marker in group_markers
            },
            "fetchedAt": fetched_at,
        }
        payload = {
            "meta": group_summary,
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

    source_points, new_spirit_categories, new_spirit_markers = prepare_spirit_points(export_payload)
    old_spirit_markers = [
        marker
        for marker in points_payload["markers"]
        if marker.get("group") == SPIRIT_GROUP
    ]
    spirit_context = {
        "oldMarkers": old_spirit_markers,
        "categories": new_spirit_categories,
    }

    markers = [
        marker
        for marker in points_payload["markers"]
        if marker.get("group") != SPIRIT_GROUP
    ]
    markers.extend(new_spirit_markers)
    points_payload["markers"] = markers

    old_category_count = len([
        category
        for category in categories_payload["categories"]
        if category.get("group") == SPIRIT_GROUP
    ])
    categories = [
        category
        for category in categories_payload["categories"]
        if category.get("group") != SPIRIT_GROUP
    ]
    categories.extend(
        new_spirit_categories[key]
        for key in sorted(new_spirit_categories)
    )
    categories_payload["categories"] = categories
    categories_payload.setdefault("meta", {})["totalCategories"] = len(categories)
    categories_payload["meta"]["updatedAt"] = fetched_at

    removed_icons, added_icons = ensure_spirit_icons(icons_payload, spirit_context)

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
    categories_by_type = {
        str(category["markType"]): category
        for category in categories
    }
    summary = build_summary(categories, markers, fetched_at, groups, points_payload.get("meta", {}))
    points_payload["meta"] = summary

    write_json(categories_path, categories_payload)
    write_json(points_path, points_payload)
    write_json(by_type_path, rebuild_by_type(markers, categories_by_type, summary))
    write_json(os.path.join(DATA_DIR, "wiki_resource_summary.json"), summary)
    write_json(icons_path, icons_payload)
    write_csv(os.path.join(DATA_DIR, "wiki_resource_points.csv"), markers)
    write_group_files(categories, markers, fetched_at, groups, summary)

    write_json(os.path.join(DATA_DIR, "17173_spirit_replace_summary.json"), {
        "sourcePage": SOURCE_PAGE,
        "sourceFile": os.path.relpath(EXPORT_PATH, PROJECT_DIR).replace("\\", "/"),
        "fetchedAt": fetched_at,
        "sourceSpiritPointCount": len(source_points),
        "excludedSourceSpiritCategories": EXCLUDED_SOURCE_SPIRIT_CATEGORIES,
        "removedWikiSpiritMarkers": len(old_spirit_markers),
        "added17173SpiritMarkers": len(new_spirit_markers),
        "removedWikiSpiritCategories": old_category_count,
        "added17173SpiritCategories": len(new_spirit_categories),
        "removedWikiSpiritIconEntries": removed_icons,
        "added17173SpiritIconEntries": added_icons,
        "addedByType": {
            new_spirit_categories[key]["markTypeName"]: sum(
                1
                for marker in new_spirit_markers
                if marker["markType"] == key
            )
            for key in sorted(new_spirit_categories)
        },
    })

    print(f"Removed wiki spirit markers: {len(old_spirit_markers)}")
    print(f"Added 17173 spirit markers: {len(new_spirit_markers)}")
    print(f"Removed wiki spirit categories: {old_category_count}")
    print(f"Added 17173 spirit categories: {len(new_spirit_categories)}")
    print(f"Total markers: {len(markers)}")


if __name__ == "__main__":
    main()
