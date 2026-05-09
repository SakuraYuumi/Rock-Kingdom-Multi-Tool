import argparse
import json
import os

from PIL import Image, ImageDraw


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
DEV_ARTIFACTS_DIR = os.path.join(PROJECT_DIR, "dev_artifacts")


COLORS = {
    "采集": (255, 64, 64, 190),
    "收集": (0, 180, 255, 190),
}
DEFAULT_ICON_ANCHOR = (15, 42)
DEFAULT_WIKI_ICON_SIZE = (40, 50)


def read_json(path):
    with open(path, "r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def to_pixel(marker, metadata):
    bounds = metadata["coordinateBounds"]
    scale = metadata["pixelPerCoordinate"]
    x = (marker["lng"] - bounds["lngMin"]) * scale
    y = (marker["lat"] - bounds["latMin"]) * scale
    return round(x, 2), round(y, 2)


def load_icon_map(path):
    if not path or not os.path.exists(path):
        return {}
    payload = read_json(path)
    return payload.get("icons", {})


def load_scaled_icon(icon_path, icon_width):
    image = Image.open(icon_path).convert("RGBA")
    if icon_width and image.width != icon_width:
        icon_height = max(1, round(image.height * icon_width / image.width))
        image = image.resize((icon_width, icon_height), Image.LANCZOS)
    return image


def icon_anchor_for(image):
    scale_x = image.width / DEFAULT_WIKI_ICON_SIZE[0]
    scale_y = image.height / DEFAULT_WIKI_ICON_SIZE[1]
    return DEFAULT_ICON_ANCHOR[0] * scale_x, DEFAULT_ICON_ANCHOR[1] * scale_y


def parse_args():
    parser = argparse.ArgumentParser(description="Project wiki resource coordinates onto the stitched wiki basemap.")
    parser.add_argument(
        "--points",
        default=os.path.join(DATA_DIR, "wiki_resource_points.json"),
    )
    parser.add_argument(
        "--metadata",
        default=os.path.join(DATA_DIR, "wiki_basemap_metadata.json"),
    )
    parser.add_argument(
        "--output",
        default=os.path.join(DATA_DIR, "wiki_resource_points_pixels.json"),
    )
    parser.add_argument(
        "--preview",
        default=os.path.join(DEV_ARTIFACTS_DIR, "resource_previews", "wiki_G_z5_resources_preview.png"),
    )
    parser.add_argument("--radius", type=int, default=3)
    parser.add_argument(
        "--icons",
        default=os.path.join(DATA_DIR, "wiki_resource_icons.json"),
    )
    parser.add_argument(
        "--icon-width",
        type=int,
        default=24,
        help="Width used when drawing wiki marker icons on the static preview.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    points_data = read_json(args.points)
    metadata = read_json(args.metadata)
    icon_map = load_icon_map(args.icons)
    icon_cache = {}
    markers = points_data["markers"]
    width, height = metadata["imageSize"]

    projected = []
    in_bounds = 0
    for marker in markers:
        x, y = to_pixel(marker, metadata)
        inside = 0 <= x < width and 0 <= y < height
        if inside:
            in_bounds += 1
        icon_entry = icon_map.get(str(marker["markType"]), {})
        projected.append({
            **marker,
            "icon": icon_entry.get("relativePath", ""),
            "iconSourceUrl": icon_entry.get("sourceUrl", ""),
            "wikiMapPixel": {
                "x": x,
                "y": y,
                "inBounds": inside,
                "basemap": os.path.basename(metadata["stitchedMap"]),
            },
        })

    output = {
        "meta": {
            **points_data["meta"],
            "basemap": metadata["stitchedMap"],
            "basemapZoom": metadata["zoom"],
            "basemapLayer": metadata["layer"]["name"],
            "basemapImageSize": metadata["imageSize"],
            "coordinateBounds": metadata["coordinateBounds"],
            "pixelPerCoordinate": metadata["pixelPerCoordinate"],
            "projectedCount": len(projected),
            "inBoundsCount": in_bounds,
            "outOfBoundsCount": len(projected) - in_bounds,
            "iconMetadata": os.path.abspath(args.icons) if os.path.exists(args.icons) else "",
            "iconWidth": args.icon_width,
        },
        "markers": projected,
    }
    write_json(args.output, output)

    with Image.open(metadata["stitchedMap"]).convert("RGBA") as image:
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for marker in projected:
            pixel = marker["wikiMapPixel"]
            if not pixel["inBounds"]:
                continue
            x = pixel["x"]
            y = pixel["y"]
            icon_path = marker.get("icon", "")
            if icon_path:
                abs_icon_path = os.path.join(PROJECT_DIR, icon_path)
                try:
                    if abs_icon_path not in icon_cache:
                        icon_cache[abs_icon_path] = load_scaled_icon(abs_icon_path, args.icon_width)
                    icon = icon_cache[abs_icon_path]
                    anchor_x, anchor_y = icon_anchor_for(icon)
                    overlay.alpha_composite(icon, (round(x - anchor_x), round(y - anchor_y)))
                    continue
                except Exception:
                    pass
            color = COLORS.get(marker["group"], (255, 255, 255, 180))
            r = args.radius
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=(255, 255, 255, 210))
        preview = Image.alpha_composite(image, overlay)
        os.makedirs(os.path.dirname(args.preview), exist_ok=True)
        preview.save(args.preview)

    print(f"Projected: {len(projected)}")
    print(f"In bounds: {in_bounds}")
    print(f"Out of bounds: {len(projected) - in_bounds}")
    print(f"Output: {args.output}")
    print(f"Preview: {args.preview}")


if __name__ == "__main__":
    main()
