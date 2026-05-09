import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")

API_URL = "https://wiki.biligame.com/rocom/api.php"
DEFAULT_GROUPS = ("地点", "互动事件", "宝箱", "任务", "战斗", "精灵分布", "收集", "采集")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex wiki icon fetcher)",
    "Referer": "https://wiki.biligame.com/rocom/",
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_bytes(url, retries=3):
    last_error = None
    for attempt in range(retries):
        try:
            request = Request(url, headers=HEADERS)
            with urlopen(request, timeout=30) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


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


def extract_file_name(icon_field):
    match = re.search(r"\{\{filepath:([^}]+)\}\}", icon_field or "")
    if match:
        return match.group(1).strip()
    return ""


def safe_filename(text):
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = text.replace("（", "(").replace("）", ")")
    return text.strip()


def resolve_image_url(file_name):
    query = urlencode(
        {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url",
            "titles": f"File:{file_name}",
        }
    )
    data = fetch_json(f"{API_URL}?{query}")
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = page.get("imageinfo") or []
        if info and info[0].get("url"):
            return {
                "url": info[0]["url"],
                "descriptionUrl": info[0].get("descriptionurl", ""),
                "title": page.get("title", ""),
                "pageId": page.get("pageid"),
            }
    return {}


def parse_args():
    parser = argparse.ArgumentParser(description="Download marker icons used by the Roco wiki map.")
    parser.add_argument(
        "--categories",
        default=os.path.join(DATA_DIR, "wiki_map_categories.json"),
    )
    parser.add_argument(
        "--groups",
        default=",".join(DEFAULT_GROUPS),
        help="Comma-separated wiki groups to download icons for. Default: 地点,互动事件,宝箱,任务,战斗,精灵分布,收集,采集",
    )
    parser.add_argument(
        "--points",
        default=os.path.join(DATA_DIR, "wiki_resource_points.json"),
        help="Point data used to limit icon downloads to mark types that actually have markers.",
    )
    parser.add_argument(
        "--all-category-icons",
        action="store_true",
        help="Download icons for all selected categories, including categories with no markers.",
    )
    parser.add_argument(
        "--include-all-groups",
        action="store_true",
        help="Download icons for every group in the category file.",
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.join(ASSETS_DIR, "icons", "wiki"),
    )
    parser.add_argument(
        "--metadata",
        default=os.path.join(DATA_DIR, "wiki_resource_icons.json"),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    payload = read_json(args.categories)
    categories = payload.get("categories", [])
    groups = None if args.include_all_groups else {group.strip() for group in args.groups.split(",") if group.strip()}
    selected = [item for item in categories if groups is None or item.get("group") in groups]
    if not args.all_category_icons and os.path.exists(args.points):
        points_payload = read_json(args.points)
        used_mark_types = {
            str(marker.get("markType"))
            for marker in points_payload.get("markers", [])
        }
        selected = [item for item in selected if str(item.get("markType")) in used_mark_types]

    os.makedirs(args.out_dir, exist_ok=True)
    icons = {}

    for category in selected:
        mark_type = str(category.get("markType"))
        file_name = extract_file_name(category.get("icon", ""))
        if not file_name:
            print(f"{mark_type} {category.get('markTypeName')}: no icon")
            continue

        resolved = resolve_image_url(file_name)
        image_url = resolved.get("url")
        if not image_url:
            print(f"{mark_type} {category.get('markTypeName')}: unresolved {file_name}")
            continue

        ext = os.path.splitext(image_url.split("?")[0])[1] or os.path.splitext(file_name)[1] or ".png"
        local_name = f"{mark_type}_{safe_filename(category.get('markTypeName', mark_type))}{ext.lower()}"
        local_path = os.path.join(args.out_dir, local_name)
        with open(local_path, "wb") as file:
            file.write(fetch_bytes(image_url))

        icons[mark_type] = {
            "group": category.get("group", ""),
            "markType": category.get("markType"),
            "markTypeName": category.get("markTypeName", ""),
            "wikiFileName": file_name,
            "wikiFileTitle": resolved.get("title", ""),
            "sourceUrl": image_url,
            "descriptionUrl": resolved.get("descriptionUrl", ""),
            "localPath": os.path.abspath(local_path),
            "relativePath": os.path.relpath(local_path, PROJECT_DIR).replace("\\", "/"),
        }
        print(f"{mark_type} {category.get('markTypeName')}: {local_name}")

    write_json(
        args.metadata,
        {
            "meta": {
                "fetchedAt": utc_now(),
                "apiUrl": API_URL,
                "categorySource": os.path.abspath(args.categories),
                "groups": sorted(groups) if groups is not None else "all",
                "iconCount": len(icons),
                "outputDirectory": os.path.abspath(args.out_dir),
            },
            "icons": icons,
        },
    )
    print()
    print(f"Downloaded {len(icons)} icons.")
    print(f"Metadata: {args.metadata}")


if __name__ == "__main__":
    main()
