import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_DIR / "data" / "17173_marker_details.json"
LOCATION_API = "https://terra-api.17173.com/app/location/list?mapIds=4010"
SOURCE_PAGE = "https://map.17173.com/rocom/maps/shijie"


def normalize_image_url(value):
    if not value:
        return ""
    if value.startswith("//"):
        return "https:" + value
    if value.startswith("http://"):
        return "https://" + value.removeprefix("http://")
    return value


def main():
    request = Request(
        LOCATION_API,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": SOURCE_PAGE,
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    points = payload.get("data") or []
    details = {}
    for item in points:
        source_point_id = item.get("id")
        if source_point_id is None:
            continue
        author = item.get("author") or {}
        images = [
            normalize_image_url(image)
            for image in (item.get("images") or [])
            if image
        ]
        details[str(source_point_id)] = {
            "sourcePointId": source_point_id,
            "mapId": item.get("mapId") or item.get("map_id"),
            "title": item.get("title") or "",
            "description": item.get("description") or "",
            "categoryId": item.get("category_id"),
            "image": normalize_image_url(item.get("image") or ""),
            "images": images,
            "videoUrl": normalize_image_url(item.get("video_url") or ""),
            "authorNickName": author.get("nickName") or "",
            "authorUserId": author.get("userId") or "",
        }

    output = {
        "meta": {
            "sourcePage": SOURCE_PAGE,
            "locationApi": LOCATION_API,
            "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pointCount": len(points),
            "detailCount": len(details),
        },
        "details": details,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"details: {len(details)}")
    print(f"output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
