import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import os
import time
from datetime import datetime, timezone
from io import BytesIO
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

SOURCE_PAGE = "https://wiki.biligame.com/rocom/大地图"
MAP_WIDGET_URL = "https://wiki.biligame.com/rocom/Widget:Map4/main?action=raw"
MAP_CODE_WIDGET_URL = "https://wiki.biligame.com/rocom/Widget:Map4.1/mapc?action=raw"
TILE_SIZE = 256
CRS_TRANSFORM_SCALE = 0.0078125

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex wiki basemap fetcher)",
    "Referer": "https://wiki.biligame.com/rocom/",
}


DEFAULT_LAYERS = {
    "G": {
        "name": "G",
        "description": "地上层",
        "tileUrl": "https://wiki-dev-patch-oss.oss-cn-hangzhou.aliyuncs.com/res/lkwg/map-3.0/{z}/tile-{x}_{y}.png",
        "index": 0,
    },
    "B1": {
        "name": "B1",
        "description": "地下层 B1",
        "tileUrl": "https://wiki-dev-patch-oss.oss-cn-hangzhou.aliyuncs.com/res/lkwg/map-1.0/tiles-B1/{z}/tile-{x}_{y}.png",
        "index": -1,
    },
    "B2": {
        "name": "B2",
        "description": "地下层 B2",
        "tileUrl": "https://wiki-dev-patch-oss.oss-cn-hangzhou.aliyuncs.com/res/lkwg/map-1.0/tiles-B2/{z}/tile-{x}_{y}.png",
        "index": -2,
    },
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_bytes(url, retries=4):
    last_error = None
    for attempt in range(retries):
        try:
            request = Request(url, headers=HEADERS)
            with urlopen(request, timeout=30) as response:
                status = getattr(response, "status", 200)
                content_type = response.headers.get("content-type", "")
                body = response.read()
                return status, content_type, body
        except HTTPError as exc:
            if exc.code == 404:
                return exc.code, exc.headers.get("content-type", ""), exc
            last_error = exc
        except Exception as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(0.5 * (attempt + 1))
    return None, "", last_error


def fetch_text(url):
    status, _content_type, body = fetch_bytes(url)
    if status != 200 or not isinstance(body, bytes):
        raise RuntimeError(f"Failed to fetch {url}: {body}")
    return body.decode("utf-8-sig")


def tile_url(template, z, x, y):
    return template.replace("{z}", str(z)).replace("{x}", str(x)).replace("{y}", str(y))


def is_png(body):
    return isinstance(body, bytes) and body.startswith(b"\x89PNG\r\n\x1a\n")


def scan_tile(layer, zoom, x, y):
    url = tile_url(layer["tileUrl"], zoom, x, y)
    status, content_type, body = fetch_bytes(url)
    if status == 200 and "image/png" in content_type and is_png(body):
        return {"x": x, "y": y, "url": url, "bytes": body}
    return None


def scan_tiles(layer, zoom, min_x, max_x, min_y, max_y, workers):
    hits = []
    coords = [
        (x, y)
        for y in range(min_y, max_y + 1)
        for x in range(min_x, max_x + 1)
    ]

    def scan_pass(pass_coords, pass_workers, label):
        pass_hits = []
        misses = []
        with ThreadPoolExecutor(max_workers=pass_workers) as executor:
            futures = {
                executor.submit(scan_tile, layer, zoom, x, y): (x, y)
                for x, y in pass_coords
            }
            for future in as_completed(futures):
                x, y = futures[future]
                try:
                    hit = future.result()
                except Exception:
                    hit = None
                if hit:
                    pass_hits.append(hit)
                    print(f"tile {zoom}/{x}_{y}: ok{label}")
                else:
                    misses.append((x, y))
                    print(f"tile {zoom}/{x}_{y}: miss{label}")
        return pass_hits, misses

    first_hits, misses = scan_pass(coords, workers, "")
    hits.extend(first_hits)
    if misses:
        retry_workers = max(1, min(4, workers))
        print(f"Retrying {len(misses)} missing tiles with {retry_workers} workers...")
        retry_hits, _retry_misses = scan_pass(misses, retry_workers, " retry")
        seen = {(hit["x"], hit["y"]) for hit in hits}
        for hit in retry_hits:
            key = (hit["x"], hit["y"])
            if key not in seen:
                hits.append(hit)
                seen.add(key)
    hits.sort(key=lambda hit: (hit["y"], hit["x"]))
    return hits


def save_tiles(layer_name, zoom, hits):
    tile_dir = os.path.join(ASSETS_DIR, "wiki_tiles", layer_name, f"z{zoom}")
    os.makedirs(tile_dir, exist_ok=True)
    saved = []
    for hit in hits:
        filename = f"tile-{hit['x']}_{hit['y']}.png"
        path = os.path.join(tile_dir, filename)
        with open(path, "wb") as file:
            file.write(hit["bytes"])
        saved.append({k: hit[k] for k in ("x", "y", "url")})
    return tile_dir, saved


def transparent_tile():
    return Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))


def stitch_tiles(hits, output_path, bounds_override=None):
    if not hits:
        raise RuntimeError("No tiles to stitch.")

    hit_map = {(hit["x"], hit["y"]): hit for hit in hits}
    if bounds_override:
        min_x = bounds_override["xMin"]
        max_x = bounds_override["xMax"]
        min_y = bounds_override["yMin"]
        max_y = bounds_override["yMax"]
    else:
        min_x = min(hit["x"] for hit in hits)
        max_x = max(hit["x"] for hit in hits)
        min_y = min(hit["y"] for hit in hits)
        max_y = max(hit["y"] for hit in hits)
    width = (max_x - min_x + 1) * TILE_SIZE
    height = (max_y - min_y + 1) * TILE_SIZE

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    blank = transparent_tile()
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            hit = hit_map.get((x, y))
            if hit:
                tile = Image.open(BytesIO(hit["bytes"])).convert("RGBA")
            else:
                tile = blank
            canvas.alpha_composite(tile, ((x - min_x) * TILE_SIZE, (y - min_y) * TILE_SIZE))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path)
    return {
        "tileBounds": {"xMin": min_x, "xMax": max_x, "yMin": min_y, "yMax": max_y},
        "imageSize": [width, height],
    }


def coordinate_metadata(zoom, tile_bounds):
    scale = (2 ** zoom) * CRS_TRANSFORM_SCALE
    coord_per_pixel = 1 / scale
    x_min_coord = tile_bounds["xMin"] * TILE_SIZE * coord_per_pixel
    x_max_coord = (tile_bounds["xMax"] + 1) * TILE_SIZE * coord_per_pixel
    y_min_coord = tile_bounds["yMin"] * TILE_SIZE * coord_per_pixel
    y_max_coord = (tile_bounds["yMax"] + 1) * TILE_SIZE * coord_per_pixel
    return {
        "leafletSimpleCrsTransformScale": CRS_TRANSFORM_SCALE,
        "pixelPerCoordinate": scale,
        "coordinatePerPixel": coord_per_pixel,
        "pixelFormula": {
            "x": f"(lng - {x_min_coord}) * {scale}",
            "y": f"(lat - {y_min_coord}) * {scale}",
        },
        "coordinateBounds": {
            "lngMin": x_min_coord,
            "lngMax": x_max_coord,
            "latMin": y_min_coord,
            "latMax": y_max_coord,
        },
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and stitch the Roco wiki basemap tiles.")
    parser.add_argument("--layer", choices=sorted(DEFAULT_LAYERS), default="G")
    parser.add_argument("--zoom", type=int, default=5)
    parser.add_argument("--scan-min-x", type=int, default=-3)
    parser.add_argument("--scan-max-x", type=int, default=2)
    parser.add_argument("--scan-min-y", type=int, default=-3)
    parser.add_argument("--scan-max-y", type=int, default=2)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument(
        "--preserve-scan-bounds",
        action="store_true",
        help="Stitch the full scan range and fill missing tiles with transparency.",
    )
    parser.add_argument(
        "--metadata-output",
        default=os.path.join(DATA_DIR, "wiki_basemap_metadata.json"),
        help="Path for the stitched map metadata JSON.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    layer = DEFAULT_LAYERS[args.layer]
    fetched_at = utc_now()

    widget_source = fetch_text(MAP_WIDGET_URL)
    code_widget_source = fetch_text(MAP_CODE_WIDGET_URL)

    hits = scan_tiles(
        layer,
        args.zoom,
        args.scan_min_x,
        args.scan_max_x,
        args.scan_min_y,
        args.scan_max_y,
        args.workers,
    )
    if not hits:
        raise SystemExit("No wiki basemap tiles were found in the scan range.")

    tile_dir, saved_tiles = save_tiles(args.layer, args.zoom, hits)
    map_path = os.path.join(ASSETS_DIR, "maps", f"wiki_{args.layer}_z{args.zoom}.png")
    bounds_override = None
    if args.preserve_scan_bounds:
        bounds_override = {
            "xMin": args.scan_min_x,
            "xMax": args.scan_max_x,
            "yMin": args.scan_min_y,
            "yMax": args.scan_max_y,
        }
    stitch_info = stitch_tiles(hits, map_path, bounds_override)
    coord_info = coordinate_metadata(args.zoom, stitch_info["tileBounds"])

    metadata = {
        "sourcePage": SOURCE_PAGE,
        "mapWidgetUrl": MAP_WIDGET_URL,
        "mapCodeWidgetUrl": MAP_CODE_WIDGET_URL,
        "fetchedAt": fetched_at,
        "layer": layer,
        "zoom": args.zoom,
        "scanRange": {
            "xMin": args.scan_min_x,
            "xMax": args.scan_max_x,
            "yMin": args.scan_min_y,
            "yMax": args.scan_max_y,
        },
        "tileCount": len(saved_tiles),
        "tileDirectory": os.path.abspath(tile_dir),
        "stitchedMap": os.path.abspath(map_path),
        **stitch_info,
        **coord_info,
        "tiles": saved_tiles,
        "rawWidgetExtracts": {
            "mapWidgetContainsTileUrl": layer["tileUrl"] in widget_source,
            "mapCodeContainsCrsScale": str(CRS_TRANSFORM_SCALE) in code_widget_source,
        },
    }
    write_json(args.metadata_output, metadata)

    print()
    print(f"Layer: {args.layer}")
    print(f"Zoom: {args.zoom}")
    print(f"Tiles: {len(saved_tiles)}")
    print(f"Tile bounds: {stitch_info['tileBounds']}")
    print(f"Image size: {stitch_info['imageSize'][0]}x{stitch_info['imageSize'][1]}")
    print(f"Map: {map_path}")
    print(f"Metadata: {args.metadata_output}")


if __name__ == "__main__":
    main()
