import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import quote, urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")

SOURCE_PAGE = "https://wiki.biligame.com/rocom/大地图"
CATEGORY_URL = "https://wiki.biligame.com/rocom/Data:Mapnew/type/json?action=raw"
POINT_URL_TEMPLATE = "https://wiki.biligame.com/rocom/Data:Mapnew/type/{mark_type}/json?action=raw"
API_URL = "https://wiki.biligame.com/rocom/api.php"

DEFAULT_GROUPS = ("地点", "互动事件", "宝箱", "任务", "战斗", "精灵分布", "收集", "采集")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex coordinate fetcher)",
    "Referer": "https://wiki.biligame.com/rocom/",
}


def fetch_text(url, retries=3):
    last_error = None
    for attempt in range(retries):
        try:
            request = Request(url, headers=HEADERS)
            with urlopen(request, timeout=8) as response:
                return response.read().decode("utf-8-sig")
        except HTTPError as exc:
            if exc.code == 404:
                raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc
            last_error = exc
        except Exception as exc:
            last_error = exc
        if attempt + 1 < retries:
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def fetch_json(url):
    return json.loads(fetch_text(url))


def fetch_point_json(mark_type):
    query = urlencode({
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "titles": f"Data:Mapnew/type/{mark_type}/json",
    })
    try:
        data = fetch_json(f"{API_URL}?{query}")
    except RuntimeError as exc:
        print(f"{mark_type}: skipped (data page fetch failed: {exc})")
        return None
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    if "missing" in page:
        return None

    revisions = page.get("revisions") or []
    if not revisions:
        return []

    revision = revisions[0]
    content = (
        revision.get("slots", {})
        .get("main", {})
        .get("*", revision.get("*", ""))
    )
    return json.loads(content or "[]")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_category(item):
    return {
        "group": item.get("type", ""),
        "markType": item.get("markType"),
        "markTypeName": item.get("markTypeName", ""),
        "length": item.get("length", ""),
        "defaultShow": item.get("defaultShow", ""),
        "collectible": item.get("collectible", ""),
        "icon": item.get("icon", ""),
        "desc": item.get("desc", ""),
    }


def normalize_point(category, item, source_url):
    point = item.get("point") or {}
    return {
        "id": item.get("id", ""),
        "group": category["group"],
        "markType": category["markType"],
        "markTypeName": category["markTypeName"],
        "title": item.get("title", ""),
        "lat": point.get("lat"),
        "lng": point.get("lng"),
        "layer": item.get("layer", ""),
        "time": item.get("time"),
        "version": item.get("version"),
        "sourceUrl": source_url,
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
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
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(categories, markers, fetched_at, groups):
    counts_by_group = {}
    counts_by_type = {}
    for marker in markers:
        counts_by_group[marker["group"]] = counts_by_group.get(marker["group"], 0) + 1
        key = f"{marker['markType']} {marker['markTypeName']}"
        counts_by_type[key] = counts_by_type.get(key, 0) + 1

    return {
        "sourcePage": SOURCE_PAGE,
        "categoryUrl": CATEGORY_URL,
        "pointUrlTemplate": POINT_URL_TEMPLATE,
        "fetchedAt": fetched_at,
        "selectedGroups": list(groups),
        "categoryCount": len(categories),
        "markerCount": len(markers),
        "countsByGroup": counts_by_group,
        "countsByType": counts_by_type,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch Roco wiki map resource coordinates from wiki.biligame.com."
    )
    parser.add_argument(
        "--groups",
        default=",".join(DEFAULT_GROUPS),
        help="Comma-separated wiki groups to fetch. Default: 地点,互动事件,宝箱,任务,战斗,精灵分布,收集,采集",
    )
    parser.add_argument(
        "--include-all-groups",
        action="store_true",
        help="Fetch every group listed by the wiki category index.",
    )
    parser.add_argument("--out-dir", default=DATA_DIR)
    return parser.parse_args()


def main():
    args = parse_args()
    fetched_at = utc_now()

    category_payload = fetch_json(CATEGORY_URL)
    all_categories = [clean_category(item) for item in category_payload.get("data", [])]
    groups = sorted({item["group"] for item in all_categories}) if args.include_all_groups else [
        group.strip() for group in args.groups.split(",") if group.strip()
    ]
    selected_categories = [item for item in all_categories if item["group"] in groups]

    all_markers = []
    by_group = {group: [] for group in groups}
    by_type = {}

    for category in selected_categories:
        mark_type = category["markType"]
        source_url = POINT_URL_TEMPLATE.format(mark_type=mark_type)
        raw_points = fetch_point_json(mark_type)
        if raw_points is None:
            print(f"{category['group']} / {mark_type} {category['markTypeName']}: skipped (missing data page)")
            continue
        points = [normalize_point(category, item, source_url) for item in raw_points]
        all_markers.extend(points)
        by_group.setdefault(category["group"], []).extend(points)
        by_type[str(mark_type)] = {
            "category": category,
            "sourceUrl": source_url,
            "points": points,
        }
        print(f"{category['group']} / {mark_type} {category['markTypeName']}: {len(points)}")

    output = {
        "meta": build_summary(selected_categories, all_markers, fetched_at, groups),
        "markers": all_markers,
    }

    write_json(os.path.join(args.out_dir, "wiki_map_categories.json"), {
        "meta": {
            "sourcePage": SOURCE_PAGE,
            "sourcePageEncoded": quote(SOURCE_PAGE, safe=":/"),
            "categoryUrl": CATEGORY_URL,
            "fetchedAt": fetched_at,
            "totalCategories": len(all_categories),
        },
        "categories": all_categories,
    })
    write_json(os.path.join(args.out_dir, "wiki_resource_points.json"), output)
    write_json(os.path.join(args.out_dir, "wiki_resource_points_by_type.json"), {
        "meta": output["meta"],
        "types": by_type,
    })
    write_json(os.path.join(args.out_dir, "wiki_resource_summary.json"), output["meta"])
    write_csv(os.path.join(args.out_dir, "wiki_resource_points.csv"), all_markers)

    for group, markers in by_group.items():
        safe_name = {
            "采集": "gathering",
            "收集": "collection",
        }.get(group, f"group_{group}")
        write_json(os.path.join(args.out_dir, f"wiki_{safe_name}_points.json"), {
            "meta": build_summary(
                [item for item in selected_categories if item["group"] == group],
                markers,
                fetched_at,
                [group],
            ),
            "markers": markers,
        })

    print()
    print(f"Fetched {len(all_markers)} points from {len(selected_categories)} categories.")
    print(f"Data directory: {os.path.abspath(args.out_dir)}")


if __name__ == "__main__":
    main()
