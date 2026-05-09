import csv
import json
import os
from datetime import datetime, timezone


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")

WIKI_OUTDOOR_BATTLE_MARK_TYPE = 601
WIKI_OUTDOOR_BATTLE_NAME = "露天挑战"


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


def build_summary(categories, markers, fetched_at, groups, previous_meta):
    counts_by_group = {}
    counts_by_type = {}
    for marker in markers:
        counts_by_group[marker["group"]] = counts_by_group.get(marker["group"], 0) + 1
        key = f"{marker['markType']} {marker['markTypeName']}"
        counts_by_type[key] = counts_by_type.get(key, 0) + 1

    extra_sources = dict(previous_meta.get("extraSources", {}))
    extra_sources["removedWikiOutdoorBattle"] = {
        "markType": WIKI_OUTDOOR_BATTLE_MARK_TYPE,
        "markTypeName": WIKI_OUTDOOR_BATTLE_NAME,
        "note": "Wiki outdoor battle markers were removed after adding 17173 outdoor battle markers.",
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


def main():
    fetched_at = utc_now()
    points_path = os.path.join(DATA_DIR, "wiki_resource_points.json")
    categories_path = os.path.join(DATA_DIR, "wiki_map_categories.json")
    icons_path = os.path.join(DATA_DIR, "wiki_resource_icons.json")
    by_type_path = os.path.join(DATA_DIR, "wiki_resource_points_by_type.json")

    points_payload = read_json(points_path)
    categories_payload = read_json(categories_path)
    icons_payload = read_json(icons_path)

    removed_markers = [
        marker
        for marker in points_payload["markers"]
        if marker.get("markType") == WIKI_OUTDOOR_BATTLE_MARK_TYPE
    ]
    markers = [
        marker
        for marker in points_payload["markers"]
        if marker.get("markType") != WIKI_OUTDOOR_BATTLE_MARK_TYPE
    ]
    removed_categories = [
        category
        for category in categories_payload["categories"]
        if category.get("markType") == WIKI_OUTDOOR_BATTLE_MARK_TYPE
    ]
    categories = [
        category
        for category in categories_payload["categories"]
        if category.get("markType") != WIKI_OUTDOOR_BATTLE_MARK_TYPE
    ]

    removed_icons = 1 if icons_payload.setdefault("icons", {}).pop(str(WIKI_OUTDOOR_BATTLE_MARK_TYPE), None) else 0

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

    points_payload["markers"] = markers
    points_payload["meta"] = summary
    categories_payload["categories"] = categories
    categories_payload.setdefault("meta", {})["totalCategories"] = len(categories)
    categories_payload["meta"]["updatedAt"] = fetched_at
    icons_payload.setdefault("meta", {})["iconCount"] = len(icons_payload["icons"])
    icons_payload["meta"]["fetchedAt"] = fetched_at

    write_json(points_path, points_payload)
    write_json(categories_path, categories_payload)
    write_json(icons_path, icons_payload)
    write_json(by_type_path, rebuild_by_type(markers, categories_by_type, summary))
    write_json(os.path.join(DATA_DIR, "wiki_resource_summary.json"), summary)
    write_csv(os.path.join(DATA_DIR, "wiki_resource_points.csv"), markers)
    write_group_files(categories, markers, fetched_at, groups, summary)

    write_json(os.path.join(DATA_DIR, "wiki_outdoor_battle_remove_summary.json"), {
        "fetchedAt": fetched_at,
        "removedMarkType": WIKI_OUTDOOR_BATTLE_MARK_TYPE,
        "removedMarkTypeName": WIKI_OUTDOOR_BATTLE_NAME,
        "removedMarkers": len(removed_markers),
        "removedCategories": len(removed_categories),
        "removedIconEntries": removed_icons,
        "totalMarkers": len(markers),
    })

    print(f"Removed wiki outdoor battle markers: {len(removed_markers)}")
    print(f"Removed wiki outdoor battle categories: {len(removed_categories)}")
    print(f"Total markers: {len(markers)}")


if __name__ == "__main__":
    main()
