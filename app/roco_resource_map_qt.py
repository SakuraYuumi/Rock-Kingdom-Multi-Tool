import argparse
import hashlib
import itertools
from collections import OrderedDict
from datetime import datetime
import json
import math
import shutil
import sys
import time
import traceback
from pathlib import Path
import uuid

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

from PyQt5.QtCore import QEvent, Qt, QTimer, QSize, QStringListModel
from PyQt5.QtGui import QBrush, QColor, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap, QSurfaceFormat, QTransform
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QOpenGLWidget,
    QProgressBar,
    QPushButton,
    QComboBox,
    QCompleter,
    QScrollArea,
    QSlider,
    QSplitter,
    QSpinBox,
    QTextEdit,
    QToolTip,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


try:
    from app.app_paths import (
        PROJECT_DIR,
        data_path,
        legacy_data_path,
        migrate_user_dir,
        migrate_user_file,
        startup_error_path,
        user_cache_path,
    )
except ImportError:
    from app_paths import (
        PROJECT_DIR,
        data_path,
        legacy_data_path,
        migrate_user_dir,
        migrate_user_file,
        startup_error_path,
        user_cache_path,
    )

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

try:  # noqa: E402
    from pvp_damage import (
        ATTRIBUTES,
        calculate_pvp_damage,
        calculate_status_effects,
        derived_stats,
        item_label as pvp_item_label,
        find_pokemon_by_key,
        load_pvp_formula,
        load_pvp_creature_skills,
        load_pvp_pokemon,
        load_pvp_skills,
        load_pvp_team,
        load_rocopvp_creatures,
        pokemon_key,
        save_pvp_team,
        skills_for_creature,
        type_multiplier_for,
    )
except ImportError:  # noqa: E402
    from app.pvp_damage import (
        ATTRIBUTES,
        calculate_pvp_damage,
        calculate_status_effects,
        derived_stats,
        item_label as pvp_item_label,
        find_pokemon_by_key,
        load_pvp_formula,
        load_pvp_creature_skills,
        load_pvp_pokemon,
        load_pvp_skills,
        load_pvp_team,
        load_rocopvp_creatures,
        pokemon_key,
        save_pvp_team,
        skills_for_creature,
        type_multiplier_for,
    )

DATA_PATH = data_path("wiki_resource_points_pixels_z6.json")
MAP_PATH = PROJECT_DIR / "assets" / "maps" / "wiki_G_z6.png"
MAP_ZOOM = "z6"
DATA_PATH_Z7 = data_path("wiki_resource_points_pixels_z7.json")
MAP_PATH_Z7 = PROJECT_DIR / "assets" / "maps" / "wiki_G_z7.png"
if DATA_PATH_Z7.exists() and MAP_PATH_Z7.exists():
    DATA_PATH = DATA_PATH_Z7
    MAP_PATH = MAP_PATH_Z7
    MAP_ZOOM = "z7"
MAP_LAYER_LABELS = OrderedDict([
    ("G", "地上"),
    ("B1", "地底 B1"),
    ("B2", "地底 B2"),
])
MAP_LAYER_ALIASES = {
    "": "G",
    "G": "G",
    "0": "G",
    "地上": "G",
    "B1": "B1",
    "-1": "B1",
    "地下": "B1",
    "地底": "B1",
    "B2": "B2",
    "-2": "B2",
}
MAP_LAYER_PATHS = OrderedDict(
    (layer, PROJECT_DIR / "assets" / "maps" / f"wiki_{layer}_{MAP_ZOOM}.png")
    for layer in MAP_LAYER_LABELS
)
STATE_PATH = migrate_user_file("user_dimmed_markers.json")
NOTES_PATH = migrate_user_file("user_marker_notes.json")
ROUTE_STATE_PATH = migrate_user_file("user_route_progress.json")
ROUTE_CACHE_PATH = migrate_user_file("user_route_cache.json")
ACCOUNT_ROOT = migrate_user_dir("accounts")
ACCOUNTS_PATH = migrate_user_file("user_accounts.json")
DEFAULT_ACCOUNT_ID = "default"
DEFAULT_ACCOUNT_NAME = "默认账号"
DETAILS_PATH = data_path("17173_marker_details.json")
EGG_DATA_PATH = data_path("egg_group_data.json")
PVP_TEAM_PRESETS_PATH = migrate_user_file("pvp_team_presets.json")
SUBMISSIONS_PATH = migrate_user_file("user_marker_audit_submissions.json")
SUBMISSION_UPLOADS_DIR = migrate_user_dir("user_marker_submission_uploads")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

OPENGL_FORMAT = QSurfaceFormat()
OPENGL_FORMAT.setSwapInterval(0)
QSurfaceFormat.setDefaultFormat(OPENGL_FORMAT)

SPIRIT_GROUP = "精灵分布"
TOOLTIP_MARK_TYPES = {
    17310030025,
    17310030026,
    17310030027,
    17310030028,
    17310030029,
    17310030033,
    17310030034,
    17310030036,
}
BASE_ICON_WIDTH = 40
MARKER_LAYER_SCALE = 2
MARKER_TILE_SIZE = 512
SIDEBAR_ICON_WIDTH = 22
ICON_ANCHOR = (15, 42)
MIN_SCALE = 0.15
MAX_SCALE = 3.2
INITIAL_SCALE = 0.72
DIMMED_OPACITY = 0.68
CLICK_DRAG_THRESHOLD = 6
ROUTE_BAND_HEIGHT = 640
ROUTE_DRAW_LIMIT = 160
ROUTE_LIST_LIMIT = 5000
ROUTE_EXACT_LIMIT = 12
ROUTE_TWO_OPT_CHUNK = 220
ROUTE_TWO_OPT_PASSES = 3
ROUTE_GLOBAL_TWO_OPT_LIMIT = 650
ROUTE_ALL_START_LIMIT = 40
ROUTE_GREEDY_START_CANDIDATES = 12
ROUTE_DEEP_OPTIMIZE_CANDIDATES = 2
ROUTE_OPTIMIZE_TIME_BUDGET_SECONDS = 2.2
ROUTE_BACKGROUND_INTERVAL_MS = 120
ROUTE_BACKGROUND_WORK_MS = 18
ROUTE_BACKGROUND_MAX_SECONDS = 900
ROUTE_GENERATION_CANDIDATE_LIMIT = 900
ROUTE_BACKGROUND_OPTIMIZATION_LIMIT = 650
ROUTE_TELEPORT_MARK_TYPES = {201, 210, 202, 203, 204}
ROUTE_TELEPORT_FIXED_COST = 520
ROUTE_TELEPORT_MIN_GAIN = 260
ROUTE_TELEPORT_MAX_EXIT_DISTANCE = 900
ROUTE_DIALOG_NORMAL_MIN_SIZE = QSize(520, 360)
ROUTE_DIALOG_PINNED_MIN_SIZE = QSize(360, 240)
ROUTE_DIALOG_PINNED_DEFAULT_SIZE = QSize(650, 500)
ROUTE_DIALOG_ROUTE_WIDTH_NORMAL = 218
ROUTE_DIALOG_ROUTE_WIDTH_PINNED = 142
ROUTE_ARROW_STEP = 5
ROUTE_ARROW_SIZE = 26
ROUTE_AUTO_COMPLETE_RADIUS = 30
ROUTE_AUTO_COMPLETE_REQUIRED_HITS = 8
ROUTE_AUTO_COMPLETE_DWELL_SECONDS = 1.1
MANUAL_ROUTE_UID_PREFIX = "manual-route-point:"
MANUAL_ROUTE_GROUP = "路径点"
MANUAL_ROUTE_MARK_TYPE = -1001
MANUAL_ROUTE_POINT_SCALE = 1 / 6
MINIMAP_MATCH_SIZE = 1024
MINIMAP_TEMPLATE_SIZE = 56
MINIMAP_MATCH_STEP = 4
MINIMAP_LOCAL_SEARCH_RADIUS = 44
MINIMAP_ANCHOR_SEARCH_RADIUS = 92
MINIMAP_MAX_WORLD_JUMP = 260
MINIMAP_BAD_SCORE = 95
MINIMAP_CORRECTION_RADIUS = 260
MINIMAP_CORRECTION_BAD_SCORE = 82
MINIMAP_CORRECTION_MIN_MARGIN = 2.0
MINIMAP_TRACK_SEARCH_RADIUS = 34
MINIMAP_TRACK_STEP = 2
MINIMAP_TRACK_SAMPLE_STEP = 7
MINIMAP_TRACK_BAD_SCORE = 58
MINIMAP_MOTION_SEARCH_RADIUS = 22
MINIMAP_MOTION_SAMPLE_STEP = 6
MINIMAP_MOTION_BAD_SCORE = 46
MINIMAP_MOTION_MIN_IMPROVEMENT = 1.4
MINIMAP_WORLD_PIXELS_PER_MINIMAP_PIXEL = 4.0
SIFT_CACHE_PATH = data_path("wiki_map_sift_cache.npz")
SIFT_REFERENCE_MAX_SIDE = 2048
SIFT_MIN_MATCHES = 12
SIFT_RATIO_TEST = 0.72
SIFT_RANSAC_REPROJ = 5.0
SIFT_MAX_WORLD_JUMP = 420


def write_startup_error(exc_type, exc_value, exc_traceback):
    error_path = startup_error_path()
    error_path.write_text(
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        encoding="utf-8",
    )
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = write_startup_error


def read_json(path):
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    temp_path.replace(path)


def load_pvp_team_presets():
    if not PVP_TEAM_PRESETS_PATH.exists():
        return {"version": 1, "presets": {}}
    try:
        payload = read_json(PVP_TEAM_PRESETS_PATH)
    except Exception:
        return {"version": 1, "presets": {}}
    if not isinstance(payload, dict):
        return {"version": 1, "presets": {}}
    presets = payload.get("presets")
    if not isinstance(presets, dict):
        presets = {}
    return {"version": 1, "presets": presets}


def save_pvp_team_presets(payload):
    presets = payload.get("presets") if isinstance(payload, dict) else {}
    if not isinstance(presets, dict):
        presets = {}
    write_json(PVP_TEAM_PRESETS_PATH, {"version": 1, "presets": presets})


def safe_account_id(account_id):
    text = str(account_id or DEFAULT_ACCOUNT_ID).strip()
    cleaned = "".join(char for char in text if char.isascii() and (char.isalnum() or char in "_-"))
    return (cleaned[:48] or DEFAULT_ACCOUNT_ID)


def account_data_dir(account_id):
    return ACCOUNT_ROOT / safe_account_id(account_id)


def account_data_path(account_id, filename):
    return account_data_dir(account_id) / filename


def account_display_name(account):
    return (account.get("name") or account.get("id") or DEFAULT_ACCOUNT_NAME).strip()


def default_account():
    return {
        "id": DEFAULT_ACCOUNT_ID,
        "name": DEFAULT_ACCOUNT_NAME,
        "createdAt": datetime.now().isoformat(timespec="seconds"),
    }


def normalize_account_registry(payload):
    if not isinstance(payload, dict):
        payload = {}
    accounts = []
    seen = set()
    for account in payload.get("accounts", []):
        if not isinstance(account, dict):
            continue
        account_id = safe_account_id(account.get("id"))
        if account_id in seen:
            continue
        name = account_display_name(account)
        accounts.append({
            "id": account_id,
            "name": name,
            "createdAt": account.get("createdAt") or datetime.now().isoformat(timespec="seconds"),
        })
        seen.add(account_id)
    if DEFAULT_ACCOUNT_ID not in seen:
        accounts.insert(0, default_account())
        seen.add(DEFAULT_ACCOUNT_ID)
    current_id = safe_account_id(payload.get("currentAccountId") or DEFAULT_ACCOUNT_ID)
    if current_id not in seen:
        current_id = DEFAULT_ACCOUNT_ID
    return {
        "version": 1,
        "currentAccountId": current_id,
        "accounts": accounts,
    }


def load_account_registry():
    if ACCOUNTS_PATH.exists():
        try:
            return normalize_account_registry(read_json(ACCOUNTS_PATH))
        except Exception:
            pass
    return normalize_account_registry({})


def save_account_registry(payload):
    write_json(ACCOUNTS_PATH, normalize_account_registry(payload))


def account_by_id(registry, account_id):
    account_id = safe_account_id(account_id)
    for account in registry.get("accounts", []):
        if safe_account_id(account.get("id")) == account_id:
            return account
    return default_account()


def make_unique_account_id(existing_ids):
    existing = {safe_account_id(item) for item in existing_ids}
    while True:
        account_id = f"acct_{uuid.uuid4().hex[:12]}"
        if account_id not in existing:
            return account_id


def load_account_json(account_id, filename, default_payload, legacy_path=None):
    path = account_data_path(account_id, filename)
    if path.exists():
        try:
            payload = read_json(path)
            return payload if isinstance(payload, dict) else default_payload()
        except Exception:
            return default_payload()
    if safe_account_id(account_id) == DEFAULT_ACCOUNT_ID and legacy_path and legacy_path.exists():
        try:
            payload = read_json(legacy_path)
            return payload if isinstance(payload, dict) else default_payload()
        except Exception:
            return default_payload()
    return default_payload()


def migrate_legacy_account_file(filename, legacy_path):
    target = account_data_path(DEFAULT_ACCOUNT_ID, filename)
    if target.exists() or not legacy_path.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.replace(target)


def migrate_legacy_account_state():
    migrate_legacy_account_file("user_dimmed_markers.json", STATE_PATH)
    migrate_legacy_account_file("user_marker_notes.json", NOTES_PATH)
    migrate_legacy_account_file("user_route_progress.json", ROUTE_STATE_PATH)
    migrate_legacy_account_file("user_dimmed_markers.json", legacy_data_path("user_dimmed_markers.json"))
    migrate_legacy_account_file("user_marker_notes.json", legacy_data_path("user_marker_notes.json"))
    migrate_legacy_account_file("user_route_progress.json", legacy_data_path("user_route_progress.json"))


def marker_uid(marker, index):
    marker_id = marker.get("id") or "no-id"
    return f"{marker.get('markType')}:{marker_id}:{index}"


def marker_note_key(marker):
    marker_id = marker.get("id") or f"{marker.get('lng')}:{marker.get('lat')}:{marker.get('title', '')}"
    return f"{marker.get('markType')}:{marker_id}"


def marker_label(marker):
    title = marker.get("title") or ""
    name = marker.get("markTypeName") or marker.get("name") or ""
    if title:
        return f"{name} - {title}"
    return name


def is_manual_route_point(marker):
    uid = str(marker.get("uid") or "")
    return marker.get("routePointKind") == "manual" or uid.startswith(MANUAL_ROUTE_UID_PREFIX)


def route_point_uid(marker):
    return str(marker.get("uid") or "")


def normalize_map_layer(layer):
    key = str(layer or "").strip()
    return MAP_LAYER_ALIASES.get(key, key if key in MAP_LAYER_LABELS else "G")


def map_layer_label(layer):
    return MAP_LAYER_LABELS.get(normalize_map_layer(layer), str(layer or "地上"))


def map_path_for_layer(layer):
    return MAP_LAYER_PATHS.get(normalize_map_layer(layer), MAP_PATH)


def fixed_marker_layer(marker):
    layer = normalize_map_layer(marker.get("layer"))
    if (
        layer == "B1"
        and int(marker.get("markType") or 0) == 701
        and str(marker.get("markTypeName") or marker.get("name") or "") == "黑晶琉璃"
    ):
        return "G"
    return layer


def load_markers():
    payload = read_json(DATA_PATH)
    markers = []
    for index, marker in enumerate(payload["markers"]):
        pixel = marker["wikiMapPixel"]
        if not pixel["inBounds"]:
            continue
        layer = fixed_marker_layer(marker)
        markers.append({
            "uid": marker_uid(marker, index),
            "note_key": marker_note_key(marker),
            "group": marker["group"],
            "mark_type": int(marker["markType"]),
            "name": marker["markTypeName"],
            "title": marker.get("title") or "",
            "label": marker_label(marker),
            "layer": layer,
            "raw_layer": marker.get("layer") or "",
            "x": float(pixel["x"]),
            "y": float(pixel["y"]),
            "icon": PROJECT_DIR / marker["icon"],
            "source_name": marker.get("sourceName") or "",
            "source_url": marker.get("sourceUrl") or "",
            "source_point_id": marker.get("sourcePointId"),
            "source_category_name": marker.get("sourceCategoryName") or "",
        })
    return payload["meta"], markers


def load_egg_group_data():
    if not EGG_DATA_PATH.exists():
        return {"meta": {}, "pokemon": []}
    try:
        payload = read_json(EGG_DATA_PATH)
    except Exception:
        return {"meta": {}, "pokemon": []}
    if not isinstance(payload, dict):
        return {"meta": {}, "pokemon": []}
    pokemon = payload.get("pokemon", [])
    if not isinstance(pokemon, list):
        pokemon = []
    return {"meta": payload.get("meta", {}), "pokemon": pokemon}


def parse_number_range(text):
    if text is None:
        return None
    value = str(text).strip()
    if not value:
        return None
    value = value.replace("～", "-").replace("—", "-").replace("－", "-")
    parts = [part.strip() for part in value.split("-") if part.strip()]
    if not parts:
        return None
    try:
        if len(parts) == 1:
            number = float(parts[0])
            return number, number
        low = float(parts[0])
        high = float(parts[1])
    except Exception:
        return None
    if high < low:
        low, high = high, low
    return low, high


def range_contains(value, range_text):
    parsed = parse_number_range(range_text)
    if parsed is None:
        return False
    low, high = parsed
    return low <= value <= high


def egg_axis_score(value, range_text):
    parsed = parse_number_range(range_text)
    if parsed is None:
        return 0.0
    low, high = parsed
    if not (low <= value <= high):
        return 0.0
    if abs(high - low) < 1e-9:
        return 1.0
    middle = (low + high) / 2.0
    half_width = (high - low) / 2.0
    return max(0.05, 1.0 - abs(value - middle) / (half_width * 1.15))


def usable_egg_groups(pokemon):
    blocked = {"不能", "不可孵蛋", "不能孵蛋"}
    groups = pokemon.get("egg_groups") or []
    return [group for group in groups if group and group not in blocked]


def pokemon_can_breed(pokemon):
    return bool(usable_egg_groups(pokemon)) and not bool(pokemon.get("cannot_breed"))


def pokemon_display_number(pokemon):
    t_id = str(pokemon.get("t_id") or "").strip()
    return t_id.zfill(3) if t_id else ""


def pokemon_label(pokemon):
    number = pokemon_display_number(pokemon)
    name = str(pokemon.get("name") or "")
    return f"No.{number} {name}" if number else name


def normalized_name(text):
    return str(text or "").strip().lower()


def find_egg_pokemon(name, egg_data=None):
    query = normalized_name(name)
    if not query:
        return []
    pokemon = (egg_data or load_egg_group_data()).get("pokemon", [])
    exact = [
        item for item in pokemon
        if normalized_name(item.get("name")) == query
        or normalized_name(item.get("base_name")) == query
    ]
    if exact:
        return sorted(exact, key=lambda item: (pokemon_display_number(item), item.get("name") or ""))
    fuzzy = [
        item for item in pokemon
        if query in normalized_name(item.get("name"))
        or query in normalized_name(item.get("base_name"))
    ]
    return sorted(fuzzy, key=lambda item: (pokemon_display_number(item), item.get("name") or ""))[:80]


def compatible_egg_pokemon(pokemon, egg_data=None):
    groups = set(usable_egg_groups(pokemon))
    if not groups:
        return []
    seen = set()
    compatible = []
    for item in (egg_data or load_egg_group_data()).get("pokemon", []):
        if not pokemon_can_breed(item):
            continue
        if not groups.intersection(usable_egg_groups(item)):
            continue
        key = (pokemon_display_number(item), item.get("name") or "")
        if key in seen:
            continue
        seen.add(key)
        compatible.append(item)
    return sorted(compatible, key=lambda item: (pokemon_display_number(item), item.get("name") or ""))


def local_egg_group_predictions(size, weight, show_details=False, timeout=None):
    del show_details, timeout
    size = float(size)
    weight = float(weight)
    matches = []
    for pokemon in load_egg_group_data().get("pokemon", []):
        if not pokemon_can_breed(pokemon):
            continue
        if not range_contains(size, pokemon.get("egg_diameter")):
            continue
        if not range_contains(weight, pokemon.get("egg_weight")):
            continue
        score = (
            egg_axis_score(size, pokemon.get("egg_diameter"))
            * egg_axis_score(weight, pokemon.get("egg_weight"))
        )
        entry = dict(pokemon)
        entry["attributes"] = pokemon.get("attributes") or ""
        entry["prob"] = score
        matches.append(entry)

    total_score = sum(max(0.0, item.get("prob", 0.0)) for item in matches)
    if total_score > 0:
        for item in matches:
            item["prob"] = max(0.0, item.get("prob", 0.0)) / total_score
    elif matches:
        even = 1.0 / len(matches)
        for item in matches:
            item["prob"] = even

    matches.sort(key=lambda item: (-float(item.get("prob") or 0.0), pokemon_display_number(item), item.get("name") or ""))
    return {
        "success": True,
        "message": "本地推测成功",
        "input": {"size": size, "weight": weight},
        "count": len(matches),
        "total_matches": len(matches),
        "show_details": True,
        "pokemons": matches,
    }


def plan_egg_breeding(parent_name, target_name, parent_gender="male", egg_data=None):
    egg_data = egg_data or load_egg_group_data()
    parent_matches = find_egg_pokemon(parent_name, egg_data)
    target_matches = find_egg_pokemon(target_name, egg_data)
    if not parent_matches:
        return {"error": "没有找到起始精灵"}
    if not target_matches:
        return {"error": "没有找到目标精灵"}

    parent = parent_matches[0]
    target = target_matches[0]
    if not pokemon_can_breed(parent):
        return {"error": f"{parent.get('name')} 没有可用蛋组"}
    if not pokemon_can_breed(target):
        return {"error": f"{target.get('name')} 没有可用蛋组"}

    pokemon = [
        item for item in egg_data.get("pokemon", [])
        if pokemon_can_breed(item) and not item.get("is_form")
    ]
    by_name = {item.get("name"): item for item in pokemon}
    graph = {item.get("name"): set() for item in pokemon}
    group_map = {}
    for item in pokemon:
        for group in usable_egg_groups(item):
            group_map.setdefault(group, []).append(item.get("name"))
    for names in group_map.values():
        for name in names:
            graph[name].update(other for other in names if other != name)

    start = parent.get("base_name") or parent.get("name")
    goal = target.get("base_name") or target.get("name")
    if start not in graph or goal not in graph:
        return {"error": "本地蛋组数据不足，暂时无法规划"}

    queue = [(start, [start])]
    visited = {start}
    path = None
    while queue:
        name, current_path = queue.pop(0)
        if name == goal:
            path = current_path
            break
        for next_name in sorted(graph.get(name, [])):
            if next_name in visited:
                continue
            visited.add(next_name)
            queue.append((next_name, current_path + [next_name]))

    if not path:
        return {"error": "没有找到可连接的蛋组路径"}

    steps = []
    if len(path) == 1:
        steps.append({
            "step": 1,
            "parent1": by_name[start],
            "parent1_gender": parent_gender,
            "parent2": by_name[start],
            "parent2_gender": "female" if parent_gender == "male" else "male",
            "result": by_name[start],
            "note": "同种生蛋",
        })
    else:
        current_gender = parent_gender
        for index in range(len(path) - 1):
            current = by_name[path[index]]
            next_item = by_name[path[index + 1]]
            note = "获得中间精灵" if index < len(path) - 2 else "获得目标精灵"
            steps.append({
                "step": index + 1,
                "parent1": current,
                "parent1_gender": current_gender,
                "parent2": next_item,
                "parent2_gender": "female",
                "result": next_item,
                "result_gender": "male" if index < len(path) - 2 else "female",
                "note": note,
            })
            current_gender = "male"

    return {
        "parent_pokemon": parent,
        "target_pokemon": target,
        "gender": parent_gender,
        "breeding_plan": {
            "steps": len(steps),
            "type": "direct" if len(steps) <= 1 else "multi_step",
            "path": path,
            "plan": steps,
        },
    }


def load_state(markers, account_id=DEFAULT_ACCOUNT_ID):
    valid_uids = {marker["uid"] for marker in markers}
    try:
        payload = load_account_json(
            account_id,
            "user_dimmed_markers.json",
            lambda: {"source": DATA_PATH.name, "dimmedMarkers": []},
            STATE_PATH,
        )
        return set(payload.get("dimmedMarkers", [])) & valid_uids
    except Exception:
        return set()


def load_notes(account_id=DEFAULT_ACCOUNT_ID):
    payload = load_account_json(
        account_id,
        "user_marker_notes.json",
        lambda: {"version": 1, "markers": {}},
        NOTES_PATH,
    )
    payload.setdefault("version", 1)
    payload.setdefault("markers", {})
    return payload


def load_marker_details():
    if not DETAILS_PATH.exists():
        return {"meta": {}, "details": {}}
    try:
        payload = read_json(DETAILS_PATH)
    except Exception:
        return {"meta": {}, "details": {}}
    payload.setdefault("meta", {})
    payload.setdefault("details", {})
    return payload


def load_submissions():
    if not SUBMISSIONS_PATH.exists():
        return {"version": 1, "submissions": []}
    try:
        payload = read_json(SUBMISSIONS_PATH)
    except Exception:
        return {"version": 1, "submissions": []}
    payload.setdefault("version", 1)
    payload.setdefault("submissions", [])
    return payload


def load_route_state(account_id=DEFAULT_ACCOUNT_ID):
    payload = load_account_json(
        account_id,
        "user_route_progress.json",
        lambda: {"version": 1, "completedMarkers": [], "routeMarkers": []},
        ROUTE_STATE_PATH,
    )
    payload.setdefault("version", 1)
    payload.setdefault("completedMarkers", [])
    payload.setdefault("routeMarkers", [])
    return payload


def load_route_cache():
    if not ROUTE_CACHE_PATH.exists():
        return {"version": 1, "routes": {}}
    try:
        payload = read_json(ROUTE_CACHE_PATH)
    except Exception:
        return {"version": 1, "routes": {}}
    if not isinstance(payload, dict):
        return {"version": 1, "routes": {}}
    payload.setdefault("version", 1)
    if not isinstance(payload.get("routes"), dict):
        payload["routes"] = {}
    return payload


class MarkerItem(QGraphicsPixmapItem):
    def __init__(self, marker, pixmap, app):
        super().__init__(pixmap)
        self.marker = marker
        self.app = app
        self.setOffset(-ICON_ANCHOR[0], -ICON_ANCHOR[1])
        self.setPos(marker["x"], marker["y"])
        self.setZValue(2)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setAcceptHoverEvents(True)
        self.setOpacity(DIMMED_OPACITY if marker["uid"] in app.dimmed_uids else 1.0)
        if app.should_show_tooltip(marker):
            self.setToolTip(app.tooltip_text(marker))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.app.toggle_marker(self.marker["uid"])
            event.accept()
            return
        if event.button() == Qt.RightButton:
            self.app.open_marker_detail(self.marker)
            event.accept()
            return
        super().mousePressEvent(event)


class MapView(QGraphicsView):
    def __init__(self, app, scene):
        super().__init__(scene)
        self.app = app
        self.current_scale = INITIAL_SCALE
        self.press_marker = None
        self.press_pos = None
        viewport = QOpenGLWidget()
        viewport.setFormat(OPENGL_FORMAT)
        self.setViewport(viewport)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setOptimizationFlags(
            QGraphicsView.DontSavePainterState
            | QGraphicsView.DontAdjustForAntialiasing
        )
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHints(self.renderHints())
        self.setBackgroundBrush(QBrush(QColor("#eef2f5")))
        self.viewport().setCursor(Qt.OpenHandCursor)

    def set_initial_transform(self):
        transform = QTransform()
        transform.scale(self.current_scale, self.current_scale)
        self.setTransform(transform)

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle == 0:
            return
        factor = 1.12 if angle > 0 else 1 / 1.12
        next_scale = min(MAX_SCALE, max(MIN_SCALE, self.current_scale * factor))
        if abs(next_scale - self.current_scale) < 0.001:
            return
        factor = next_scale / self.current_scale
        self.current_scale = next_scale
        self.scale(factor, factor)
        self.app.update_status()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            marker = self.app.hit_test_marker(self.mapToScene(event.pos()), cycle=True)
            if marker:
                QToolTip.hideText()
                QTimer.singleShot(0, lambda marker=marker: self.app.open_marker_detail(marker))
                event.accept()
                return
        if event.button() == Qt.LeftButton:
            self.press_marker = self.app.hit_test_marker(self.mapToScene(event.pos()), cycle=True)
            self.press_pos = event.pos()
            self.viewport().setCursor(Qt.PointingHandCursor if self.press_marker else Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        marker = None
        if event.buttons() & Qt.LeftButton:
            self.viewport().setCursor(Qt.ClosedHandCursor)
            QToolTip.hideText()
        else:
            marker = self.app.hit_test_marker(self.mapToScene(event.pos()))
            self.viewport().setCursor(Qt.PointingHandCursor if marker else Qt.OpenHandCursor)
            if marker and self.app.should_show_tooltip(marker):
                QToolTip.showText(event.globalPos(), self.app.tooltip_text(marker), self)
            else:
                QToolTip.hideText()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        marker_to_toggle = None
        if event.button() == Qt.LeftButton and self.press_marker is not None and self.press_pos is not None:
            dx = abs(event.pos().x() - self.press_pos.x())
            dy = abs(event.pos().y() - self.press_pos.y())
            release_markers = self.app.markers_at_scene_pos(self.mapToScene(event.pos()))
            if (
                dx <= CLICK_DRAG_THRESHOLD
                and dy <= CLICK_DRAG_THRESHOLD
                and any(marker["uid"] == self.press_marker["uid"] for marker in release_markers)
            ):
                marker_to_toggle = self.press_marker
        self.press_marker = None
        self.press_pos = None
        super().mouseReleaseEvent(event)
        hover_marker = self.app.hit_test_marker(self.mapToScene(event.pos()))
        self.viewport().setCursor(Qt.PointingHandCursor if hover_marker else Qt.OpenHandCursor)
        if marker_to_toggle is not None:
            self.app.toggle_marker(marker_to_toggle["uid"])
            event.accept()

    def leaveEvent(self, event):
        QToolTip.hideText()
        self.viewport().setCursor(Qt.OpenHandCursor)
        super().leaveEvent(event)


class DetailDialog(QDialog):
    def __init__(self, parent, marker, detail, record, save_notes, open_submission):
        super().__init__(parent)
        self.marker = marker
        self.detail = detail
        self.record = record
        self.save_notes = save_notes
        self.open_submission = open_submission
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(marker_label(marker))
        self.setMinimumSize(430, 330)
        self.resize(456, 352)
        self.setStyleSheet("""
            QDialog { background: #f5eedc; }
            QLabel#title { color: #3a2715; font-size: 20px; font-weight: 700; }
            QLabel#type { color: #6b5637; font-size: 13px; }
            QLabel#desc { color: #3b2f1f; font-size: 13px; }
            QLabel#provider { color: #3b2f1f; font-size: 12px; }
            QPushButton#closeButton {
                border: none; background: transparent; color: #3b2f1f;
                font-size: 22px; font-weight: 700;
            }
            QPushButton#uploadButton {
                border: none; background: #e8dfc7; color: #8a7856;
                padding: 4px 9px; border-radius: 2px;
            }
            QFrame#foundBar { background: #9fd3cf; border-top: 1px solid #d68b4c; }
            QCheckBox#foundCheck { color: white; font-size: 14px; font-weight: 700; }
            QFrame#board { background: #95cec9; }
            QLabel#boardTitle { color: white; font-size: 16px; font-weight: 700; }
            QPushButton#moreButton {
                border: none; background: #f28b2e; color: white;
                padding: 3px 10px; border-radius: 10px;
            }
            QFrame#messageArea { background: white; }
            QLabel#author { color: #1e63c6; font-weight: 700; }
            QLabel#message { color: #2f2f2f; }
            QLineEdit {
                border: none; background: white; padding: 7px;
                color: #1f2937;
            }
            QPushButton#postButton {
                border: none; background: white; color: #1f2937;
                padding: 7px 18px;
            }
        """)

        self.record.setdefault("messages", [])
        self.record.setdefault("found", False)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 6)
        header_layout.setSpacing(6)

        top_row = QHBoxLayout()
        self.upload_button = QPushButton("修改坐标信息")
        self.upload_button.setObjectName("uploadButton")
        self.upload_button.clicked.connect(lambda: self.open_submission(self.marker, self.detail))
        top_row.addWidget(self.upload_button)
        top_row.addStretch(1)
        header_layout.addLayout(top_row)

        title_row = QHBoxLayout()
        icon_label = QLabel()
        icon_pixmap = QPixmap(str(marker["icon"]))
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaledToWidth(28, Qt.SmoothTransformation))
        title_row.addWidget(icon_label)

        title_stack = QVBoxLayout()
        display_title = marker.get("title") or marker["name"]
        title_label = QLabel(display_title)
        title_label.setObjectName("title")
        title_label.setWordWrap(True)
        type_label = QLabel(marker["name"])
        type_label.setObjectName("type")
        title_stack.addWidget(title_label)
        title_stack.addWidget(type_label)
        title_row.addLayout(title_stack, 1)
        header_layout.addLayout(title_row)

        description = (detail.get("description") or "").strip() or "暂无详情介绍。"
        desc_label = QLabel(description)
        desc_label.setObjectName("desc")
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)

        provider = detail.get("authorNickName") or ("17173" if detail else "本地数据")
        provider_label = QLabel(f"这些标由{provider}提供")
        provider_label.setObjectName("provider")
        provider_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(provider_label)
        root.addWidget(header)

        found_bar = QFrame()
        found_bar.setObjectName("foundBar")
        found_layout = QHBoxLayout(found_bar)
        found_layout.setContentsMargins(0, 6, 0, 6)
        found_layout.setAlignment(Qt.AlignCenter)
        self.found_check = QCheckBox("我已经找到这个位置")
        self.found_check.setObjectName("foundCheck")
        self.found_check.setChecked(bool(self.record.get("found")))
        self.found_check.stateChanged.connect(self.save_found_state)
        found_layout.addWidget(self.found_check)
        root.addWidget(found_bar)

        board = QFrame()
        board.setObjectName("board")
        board_layout = QVBoxLayout(board)
        board_layout.setContentsMargins(8, 7, 8, 7)
        board_layout.setSpacing(5)

        board_header = QHBoxLayout()
        self.board_title = QLabel()
        self.board_title.setObjectName("boardTitle")
        board_header.addWidget(self.board_title)
        board_header.addStretch(1)
        board_layout.addLayout(board_header)

        self.message_area = QFrame()
        self.message_area.setObjectName("messageArea")
        self.message_layout = QVBoxLayout(self.message_area)
        self.message_layout.setContentsMargins(8, 6, 8, 6)
        self.message_layout.setSpacing(4)
        board_layout.addWidget(self.message_area, 1)

        input_row = QHBoxLayout()
        avatar = QLabel("玩")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(24, 24)
        avatar.setStyleSheet("background: #8d4bd0; color: white; border-radius: 12px; font-weight: 700;")
        input_row.addWidget(avatar)
        self.message_input = QLineEdit()
        self.message_input.setMaxLength(20)
        self.message_input.setPlaceholderText("我也要留言一条...（少于20个字）")
        self.message_input.returnPressed.connect(self.add_message)
        input_row.addWidget(self.message_input, 1)
        post_button = QPushButton("发布")
        post_button.setObjectName("postButton")
        post_button.clicked.connect(self.add_message)
        input_row.addWidget(post_button)
        board_layout.addLayout(input_row)
        root.addWidget(board, 1)
        self.refresh_messages()

    def save_found_state(self):
        self.record["found"] = self.found_check.isChecked()
        self.save_notes()

    def refresh_messages(self):
        while self.message_layout.count():
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        items = self.record.get("messages", [])
        self.board_title.setText(f"留言板({len(items)})")
        if not items:
            empty = QLabel("还没有留言。")
            empty.setStyleSheet("color: #9aa3ad;")
            self.message_layout.addWidget(empty)
            self.message_layout.addStretch(1)
            return
        for item in items[-4:]:
            row = QHBoxLayout()
            row.setSpacing(0)
            author = QLabel(item.get("author", "玩家"))
            author.setObjectName("author")
            text = QLabel(f"：{item.get('text', '')}")
            text.setObjectName("message")
            text.setWordWrap(True)
            row.addWidget(author)
            row.addWidget(text, 1)
            holder = QWidget()
            holder.setLayout(row)
            self.message_layout.addWidget(holder)
        self.message_layout.addStretch(1)

    def add_message(self):
        text = self.message_input.text().strip()
        if not text:
            return
        self.record.setdefault("messages", []).append({
            "author": "玩家",
            "text": text[:20],
            "createdAt": datetime.now().isoformat(timespec="seconds"),
        })
        self.message_input.clear()
        self.refresh_messages()
        self.save_notes()


class ReviewSubmissionDialog(QDialog):
    def __init__(self, parent, marker, detail, category_options, submit_callback):
        super().__init__(parent)
        self.marker = marker
        self.detail = detail
        self.submit_callback = submit_callback
        self.image_paths = []
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.setWindowTitle("推荐标记点")
        self.resize(490, 610)
        self.setMinimumSize(430, 520)
        self.setStyleSheet("""
            QDialog { background: #efe1bf; }
            QLabel#formTitle { color: #3b2f1f; font-size: 18px; }
            QLabel#fieldLabel { color: #3b2f1f; font-size: 13px; }
            QLineEdit, QTextEdit, QComboBox {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid #e1cf9c;
                padding: 7px;
                color: #3b2f1f;
            }
            QTextEdit { min-height: 86px; }
            QPushButton#orangeButton {
                border: none; background: #f28b2e; color: white;
                padding: 8px 16px; font-size: 14px;
            }
            QPushButton#plainButton {
                border: none; background: transparent; color: #c35f49;
                font-weight: 700; font-size: 15px;
            }
            QFrame#previewFrame { background: rgba(255, 255, 255, 0.25); }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 16, 18)
        root.setSpacing(10)

        title = QLabel("推荐标记点")
        title.setObjectName("formTitle")
        root.addWidget(title)

        root.addWidget(self.field_label("标题 *"))
        self.title_input = QLineEdit(marker.get("title") or marker["name"])
        root.addWidget(self.title_input)

        root.addWidget(self.field_label("分类 *"))
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        for option in category_options:
            self.category_combo.addItem(option)
        current_category = marker["name"]
        index = self.category_combo.findText(current_category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setEditText(current_category)
        root.addWidget(self.category_combo)

        root.addWidget(self.field_label("内容"))
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("可以使用 markdown 语法，例如：**加粗**")
        self.content_edit.setPlainText((detail.get("description") or "").strip())
        root.addWidget(self.content_edit)

        root.addWidget(self.field_label("图片"))
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setFrameShape(QFrame.NoFrame)
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(8, 8, 8, 8)
        self.preview_layout.setSpacing(8)
        self.preview_scroll.setWidget(self.preview_container)
        preview_layout.addWidget(self.preview_scroll)
        root.addWidget(preview_frame)
        self.refresh_image_previews()

        upload_button = QPushButton("上传图片")
        upload_button.setObjectName("orangeButton")
        upload_button.clicked.connect(self.pick_images)
        upload_row = QHBoxLayout()
        upload_row.addWidget(upload_button)
        upload_row.addStretch(1)
        root.addLayout(upload_row)

        root.addWidget(self.field_label("添加视频"))
        self.video_input = QLineEdit()
        self.video_input.setPlaceholderText("请输入 B站视频 iframe 地址")
        root.addWidget(self.video_input)

        current_title = QLabel(marker.get("title") or marker["name"])
        current_title.setStyleSheet("font-weight: 700; color: #3b2f1f;")
        root.addWidget(current_title)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        close_button = QPushButton("关闭")
        close_button.setObjectName("orangeButton")
        close_button.clicked.connect(self.reject)
        submit_button = QPushButton("提交")
        submit_button.setObjectName("orangeButton")
        submit_button.clicked.connect(self.submit)
        button_row.addWidget(close_button)
        button_row.addWidget(submit_button)
        root.addLayout(button_row)

    def field_label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def refresh_image_previews(self):
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self.image_paths:
            empty = QLabel("未选择图片")
            empty.setStyleSheet("color: #8a7856;")
            self.preview_layout.addWidget(empty)
            self.preview_layout.addStretch(1)
            return

        for path in self.image_paths:
            card = QFrame()
            card.setStyleSheet("background: transparent;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            remove_button = QPushButton("×")
            remove_button.setObjectName("plainButton")
            remove_button.clicked.connect(lambda _checked=False, path=path: self.remove_image(path))
            remove_button.setFixedWidth(24)
            pixmap = QPixmap(str(path))
            image_label = QLabel()
            image_label.setFixedSize(136, 64)
            image_label.setAlignment(Qt.AlignCenter)
            if not pixmap.isNull():
                image_label.setPixmap(pixmap.scaled(136, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                image_label.setText(path.name)
            card_layout.addWidget(remove_button, 0, Qt.AlignRight)
            card_layout.addWidget(image_label)
            self.preview_layout.addWidget(card)
        self.preview_layout.addStretch(1)

    def pick_images(self):
        files, _filter = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片 (*.png *.jpg *.jpeg *.webp *.gif *.bmp);;所有文件 (*.*)",
        )
        for file_name in files:
            path = Path(file_name)
            if path.suffix.lower() in IMAGE_EXTENSIONS and path.exists() and path not in self.image_paths:
                self.image_paths.append(path)
        self.refresh_image_previews()

    def remove_image(self, path):
        self.image_paths = [item for item in self.image_paths if item != path]
        self.refresh_image_previews()

    def submit(self):
        title = self.title_input.text().strip()
        category = self.category_combo.currentText().strip()
        if not title or not category:
            QMessageBox.warning(self, "缺少信息", "标题和分类不能为空。")
            return

        self.submit_callback(self.marker, {
            "title": title,
            "category": category,
            "description": self.content_edit.toPlainText().strip(),
            "imagePaths": [str(path) for path in self.image_paths],
            "videoUrl": self.video_input.text().strip(),
        })
        QMessageBox.information(self, "已提交", "修改内容已提交到本地后台审核队列。")
        self.accept()


class EggQueryDialog(QDialog):
    def __init__(self, parent, egg_data=None):
        super().__init__(None)
        self.owner = parent
        self.egg_data = egg_data or load_egg_group_data()
        flags = self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        flags |= Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint
        self.setWindowFlags(flags)
        self.setWindowTitle("洛克王国孵蛋查询")
        self.resize(820, 620)
        self.setMinimumSize(680, 500)
        self.setStyleSheet("""
            QDialog { background: #f5eedc; }
            QLabel#title { color: #3a2715; font-size: 20px; font-weight: 700; }
            QLabel#hint { color: #6b5637; font-size: 12px; }
            QLineEdit, QComboBox {
                background: rgba(255, 255, 255, 0.86);
                border: 1px solid #d9c79b;
                padding: 8px;
                color: #3b2f1f;
            }
            QTreeWidget {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid #d9c79b;
                color: #2f2418;
            }
            QTabWidget::pane { border: 1px solid #d9c79b; background: rgba(255,255,255,0.28); }
            QTabBar::tab { min-width: 138px; padding: 7px 12px; color: #3b2f1f; }
            QTabBar::tab:selected { background: #efe1bf; font-weight: 700; }
            QPushButton#orangeButton {
                background: #f28b2e;
                color: white;
                border: none;
                padding: 8px 14px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("洛克王国孵蛋查询")
        title.setObjectName("title")
        root.addWidget(title)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self.build_prediction_tab()
        self.build_group_lookup_tab()
        self.build_plan_tab()

    def orange_button(self, text, handler):
        button = QPushButton(text)
        button.setObjectName("orangeButton")
        button.clicked.connect(handler)
        return button

    def build_prediction_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        form = QHBoxLayout()
        form.addWidget(QLabel("蛋尺寸"))
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("例如：0.16")
        form.addWidget(self.size_input, 1)
        form.addWidget(QLabel("蛋重量"))
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("例如：1.27")
        form.addWidget(self.weight_input, 1)
        self.show_details_check = QCheckBox("显示尺寸和重量区间")
        self.show_details_check.setChecked(True)
        form.addWidget(self.show_details_check)
        layout.addLayout(form)

        examples = QHBoxLayout()
        examples.addWidget(QLabel("示例"))
        examples.addWidget(self.orange_button("书魔虫", lambda: self.fill_example("0.16", "1.27")))
        examples.addWidget(self.orange_button("胆小鳗鱼", lambda: self.fill_example("0.39", "8.99")))
        examples.addStretch(1)
        examples.addWidget(self.orange_button("开始查询", self.run_query))
        layout.addLayout(examples)

        self.status_label = QLabel("等待查询")
        self.status_label.setObjectName("hint")
        layout.addWidget(self.status_label)

        self.result_tree = QTreeWidget()
        self.result_tree.setColumnCount(5)
        self.result_tree.setHeaderLabels(["精灵", "属性", "匹配度", "蛋尺寸", "蛋重量"])
        self.result_tree.setColumnWidth(0, 190)
        self.result_tree.setColumnWidth(1, 120)
        self.result_tree.setColumnWidth(2, 90)
        self.result_tree.setColumnWidth(3, 130)
        self.result_tree.setColumnWidth(4, 130)
        self.result_tree.setRootIsDecorated(False)
        self.result_tree.setWordWrap(True)
        layout.addWidget(self.result_tree, 1)

        self.tabs.addTab(tab, "蛋数据推测")

    def build_group_lookup_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.addWidget(QLabel("精灵名"))
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("例如：书魔虫")
        self.group_name_input.returnPressed.connect(self.run_group_lookup)
        row.addWidget(self.group_name_input, 1)
        row.addWidget(self.orange_button("反查蛋组", self.run_group_lookup))
        layout.addLayout(row)

        self.group_status_label = QLabel("输入精灵名后，会显示蛋组和可配偶精灵。")
        self.group_status_label.setObjectName("hint")
        self.group_status_label.setWordWrap(True)
        layout.addWidget(self.group_status_label)

        self.group_result_tree = QTreeWidget()
        self.group_result_tree.setColumnCount(5)
        self.group_result_tree.setHeaderLabels(["精灵", "蛋组", "属性", "蛋尺寸", "蛋重量"])
        self.group_result_tree.setColumnWidth(0, 190)
        self.group_result_tree.setColumnWidth(1, 180)
        self.group_result_tree.setColumnWidth(2, 120)
        self.group_result_tree.setColumnWidth(3, 120)
        self.group_result_tree.setColumnWidth(4, 120)
        self.group_result_tree.setRootIsDecorated(False)
        self.group_result_tree.setWordWrap(True)
        layout.addWidget(self.group_result_tree, 1)

        self.tabs.addTab(tab, "按精灵名反查蛋组")

    def build_plan_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        form = QHBoxLayout()
        form.addWidget(QLabel("起始精灵"))
        self.plan_parent_input = QLineEdit()
        self.plan_parent_input.setPlaceholderText("例如：书魔虫")
        form.addWidget(self.plan_parent_input, 1)
        form.addWidget(QLabel("性别"))
        self.plan_gender_combo = QComboBox()
        self.plan_gender_combo.addItem("公", "male")
        self.plan_gender_combo.addItem("母", "female")
        form.addWidget(self.plan_gender_combo)
        form.addWidget(QLabel("目标精灵"))
        self.plan_target_input = QLineEdit()
        self.plan_target_input.setPlaceholderText("例如：胆小鳗鱼")
        form.addWidget(self.plan_target_input, 1)
        form.addWidget(self.orange_button("规划", self.run_breeding_plan))
        layout.addLayout(form)

        examples = QHBoxLayout()
        examples.addWidget(QLabel("示例"))
        examples.addWidget(self.orange_button("书魔虫 → 胆小鳗鱼", self.fill_plan_example))
        examples.addStretch(1)
        layout.addLayout(examples)

        self.plan_status_label = QLabel("规划基于蛋组连通关系；子代跟随母亲，实际性别可能需要多次孵化。")
        self.plan_status_label.setObjectName("hint")
        self.plan_status_label.setWordWrap(True)
        layout.addWidget(self.plan_status_label)

        self.plan_result_tree = QTreeWidget()
        self.plan_result_tree.setColumnCount(5)
        self.plan_result_tree.setHeaderLabels(["步骤", "父母 1", "父母 2", "结果", "说明"])
        self.plan_result_tree.setColumnWidth(0, 60)
        self.plan_result_tree.setColumnWidth(1, 180)
        self.plan_result_tree.setColumnWidth(2, 180)
        self.plan_result_tree.setColumnWidth(3, 170)
        self.plan_result_tree.setColumnWidth(4, 180)
        self.plan_result_tree.setRootIsDecorated(False)
        self.plan_result_tree.setWordWrap(True)
        layout.addWidget(self.plan_result_tree, 1)

        self.tabs.addTab(tab, "生蛋规划")

    def fill_example(self, size, weight):
        self.size_input.setText(size)
        self.weight_input.setText(weight)
        self.tabs.setCurrentIndex(0)

    def fill_plan_example(self):
        self.plan_parent_input.setText("书魔虫")
        self.plan_target_input.setText("胆小鳗鱼")
        self.plan_gender_combo.setCurrentIndex(0)

    def run_query(self):
        size_text = self.size_input.text().strip()
        weight_text = self.weight_input.text().strip()
        try:
            size = float(size_text)
            weight = float(weight_text)
        except Exception:
            QMessageBox.warning(self, "孵蛋查询", "蛋尺寸和蛋重量需要填写数字。")
            return
        if size <= 0 or weight <= 0:
            QMessageBox.warning(self, "孵蛋查询", "蛋尺寸和蛋重量必须大于 0。")
            return

        payload = local_egg_group_predictions(size, weight, self.show_details_check.isChecked())
        self.populate_results(payload)

    def populate_results(self, payload):
        self.result_tree.clear()
        pokemons = payload.get("pokemons", [])
        count = int(payload.get("count") or len(pokemons))
        total = int(payload.get("total_matches") or len(pokemons))
        if not pokemons:
            self.status_label.setText("没有找到符合条件的精灵")
            return

        for pokemon in pokemons:
            probability = float(pokemon.get("prob") or 0.0) * 100.0
            item = QTreeWidgetItem([
                pokemon_label(pokemon),
                str(pokemon.get("attributes") or ""),
                f"{probability:.2f}%",
                str(pokemon.get("egg_diameter") or ""),
                str(pokemon.get("egg_weight") or ""),
            ])
            self.result_tree.addTopLevelItem(item)

        self.status_label.setText(f"查询成功：显示 {count} 个结果，共匹配 {total} 个")

    def run_group_lookup(self):
        self.group_result_tree.clear()
        query = self.group_name_input.text().strip()
        matches = find_egg_pokemon(query, self.egg_data)
        if not matches:
            self.group_status_label.setText("没有找到这个精灵")
            return

        selected = matches[0]
        if len(matches) > 1 and normalized_name(matches[0].get("name")) != normalized_name(query):
            for pokemon in matches:
                self.add_group_result_item(pokemon)
            self.group_status_label.setText(f"找到 {len(matches)} 个相近精灵，请输入更完整的名字。")
            return

        groups = usable_egg_groups(selected)
        compatible = compatible_egg_pokemon(selected, self.egg_data)
        self.add_group_result_item(selected)
        for pokemon in compatible:
            if pokemon.get("name") == selected.get("name") and pokemon_display_number(pokemon) == pokemon_display_number(selected):
                continue
            self.add_group_result_item(pokemon)
        group_text = "、".join(groups) if groups else "不能孵蛋"
        self.group_status_label.setText(
            f"{pokemon_label(selected)}：{group_text}；可配偶 {len(compatible)} 个"
        )

    def add_group_result_item(self, pokemon):
        item = QTreeWidgetItem([
            pokemon_label(pokemon),
            "、".join(usable_egg_groups(pokemon)) or "不能孵蛋",
            str(pokemon.get("attributes") or ""),
            str(pokemon.get("egg_diameter") or ""),
            str(pokemon.get("egg_weight") or ""),
        ])
        self.group_result_tree.addTopLevelItem(item)

    def run_breeding_plan(self):
        self.plan_result_tree.clear()
        parent = self.plan_parent_input.text().strip()
        target = self.plan_target_input.text().strip()
        gender = self.plan_gender_combo.currentData() or "male"
        payload = plan_egg_breeding(parent, target, gender, self.egg_data)
        if payload.get("error"):
            self.plan_status_label.setText(payload["error"])
            return

        plan = payload.get("breeding_plan") or {}
        steps = plan.get("plan") or []
        for step in steps:
            parent1 = step.get("parent1") or {}
            parent2 = step.get("parent2") or {}
            result = step.get("result") or {}
            item = QTreeWidgetItem([
                str(step.get("step") or ""),
                f"{pokemon_label(parent1)} ({self.gender_label(step.get('parent1_gender'))})",
                f"{pokemon_label(parent2)} ({self.gender_label(step.get('parent2_gender'))})",
                f"{pokemon_label(result)} ({self.gender_label(step.get('result_gender'))})",
                str(step.get("note") or ""),
            ])
            self.plan_result_tree.addTopLevelItem(item)

        path = " → ".join(plan.get("path") or [])
        self.plan_status_label.setText(
            f"规划成功：{len(steps)} 步；路径 {path}"
        )

    def gender_label(self, gender):
        if gender == "male":
            return "公"
        if gender == "female":
            return "母"
        return ""


class ClickWheelSpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.ClickFocus)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
            return
        super().wheelEvent(event)


class ClickWheelDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.ClickFocus)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
            return
        super().wheelEvent(event)


class LazyModelComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._compact_model = QStringListModel(["空"], self)
        self._popup_model = None
        self.setModel(self._compact_model)

    def set_lazy_popup_model(self, model):
        self._popup_model = model

    def showPopup(self):
        text = self.currentText()
        if self._popup_model is not None and self.model() is not self._popup_model:
            self.blockSignals(True)
            self.setModel(self._popup_model)
            self.setEditText(text)
            self.blockSignals(False)
        super().showPopup()

    def hidePopup(self):
        super().hidePopup()
        text = self.currentText().strip()
        if self.model() is not self._compact_model:
            self.blockSignals(True)
            self.setModel(self._compact_model)
            self.setEditText("" if text == "空" else text)
            self.blockSignals(False)


class PvpDamageDialog(QDialog):
    def __init__(self, parent):
        super().__init__(None)
        self.owner = parent
        self.pokemon = load_pvp_pokemon()
        self.pokemon_slot_labels = [pvp_item_label(item) for item in self.pokemon]
        self.pokemon_slot_lookup = {}
        self.pokemon_slot_lookup_folded = {}
        for item, label in zip(self.pokemon, self.pokemon_slot_labels):
            for key in (label, str(item.get("name") or "")):
                key = key.strip()
                if key:
                    self.pokemon_slot_lookup[key] = item
                    self.pokemon_slot_lookup_folded[key.casefold()] = item
        self.pokemon_slot_completer_model = QStringListModel(self.pokemon_slot_labels, self)
        self.pokemon_slot_dropdown_model = QStringListModel(["空", *self.pokemon_slot_labels], self)
        self.all_skills = load_pvp_skills()
        self.creature_skill_map = load_pvp_creature_skills()
        self.rocopvp_creatures = load_rocopvp_creatures()
        self.rocopvp_creature_index = self.build_rocopvp_creature_index()
        self.skill_preview_cache = {}
        self.skills = self.build_rocopvp_skill_pool() or [
            skill for skill in self.all_skills
            if skill.get("power") is not None and skill.get("category") in {"物攻", "魔攻"}
        ]
        self.formula = load_pvp_formula()
        saved_team = load_pvp_team()
        self.team_slots = {
            "attacker": list(saved_team.get("attacker") or [None] * 6),
            "defender": list(saved_team.get("defender") or [None] * 6),
        }
        self.team_member_builds = self.normalize_team_member_builds()
        self.team_presets_payload = load_pvp_team_presets()
        self.selected_team_slot = {"attacker": 0, "defender": 0}
        self.team_slot_combos = {"attacker": [], "defender": []}
        self.refreshing_team_slots = False
        self.loading_team_member_build = False
        self.loading_team_preset = False
        self.initializing_pvp = True
        flags = self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        flags |= Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint
        self.setWindowFlags(flags)
        self.setWindowTitle("PVP伤害计算")
        self.resize(1120, 780)
        self.setMinimumSize(780, 560)
        self.setStyleSheet("""
            QDialog { background: #f5eedc; }
            QLabel#title { color: #3a2715; font-size: 20px; font-weight: 700; }
            QLabel#hint { color: #6b5637; font-size: 12px; }
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
                background: rgba(255, 255, 255, 0.86);
                border: 1px solid #d9c79b;
                padding: 6px;
                color: #3b2f1f;
            }
            QComboBox QAbstractItemView {
                background: #fffaf0;
                selection-background-color: #bcdcff;
                selection-color: #102a43;
            }
            QComboBox QAbstractItemView::item:hover,
            QListView::item:hover {
                background: #cfe8ff;
                color: #102a43;
            }
            QLabel#panelTitle { color: #3a2715; font-size: 15px; font-weight: 700; }
            QLabel#panelMeta { color: #6b5637; font-size: 12px; }
            QLabel#relation { color: #7a4b15; font-weight: 700; }
            QLabel#statChip {
                background: #fff8e8;
                border: 1px solid #d9c79b;
                border-radius: 10px;
                padding: 2px 7px;
                color: #7a4b15;
            }
            QPushButton#statChip {
                background: #fff8e8;
                border: 1px solid #d9c79b;
                border-radius: 10px;
                padding: 2px 7px;
                color: #7a4b15;
            }
            QPushButton#statChip:checked {
                background: #dff4d8;
                border: 1px solid #59ad62;
                color: #267235;
                font-weight: 700;
            }
            QSpinBox#ivSpin {
                background: #ffbf55;
                border: 1px solid #d38418;
                border-radius: 10px;
                padding: 1px 4px;
                max-width: 48px;
            }
            QLabel#dangerText { color: #9a3412; font-weight: 700; }
            QTreeWidget {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid #d9c79b;
                color: #2f2418;
            }
            QProgressBar {
                background: #eadfc3;
                border: 1px solid #d4bf8b;
                border-radius: 5px;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #d89a35;
                border-radius: 4px;
            }
            QPushButton#orangeButton {
                background: #f28b2e;
                color: white;
                border: none;
                padding: 8px 14px;
            }
            QFrame#teamSlotFrame {
                background: rgba(255, 255, 255, 0.68);
                border: 1px solid #d9c79b;
                padding: 1px;
            }
            QFrame#teamSlotFrame[active="true"] {
                background: #fff0cf;
                border: 2px solid #f28b2e;
            }
            QLabel#teamSlotNumber {
                color: #6b5637;
                font-weight: 700;
                min-width: 14px;
            }
            QComboBox#teamSlotCombo {
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid #d9c79b;
                color: #3b2f1f;
                min-height: 22px;
                max-height: 26px;
                padding: 1px;
            }
            QComboBox#teamSlotCombo[active="true"] {
                background: #fff0cf;
                border: 2px solid #f28b2e;
            }
            QComboBox#teamSlotCombo QLineEdit {
                font-weight: 400;
                padding: 1px;
            }
            QPushButton#sectionToggle {
                background: rgba(255, 249, 234, 0.92);
                border: 1px solid #d9c79b;
                color: #7a4b15;
                font-weight: 700;
                padding: 7px 10px;
                text-align: left;
            }
            QFrame#infoPanel {
                background: rgba(255, 249, 234, 0.72);
                border: 1px solid #d9c79b;
            }
            QLabel#skillPreview {
                color: #1f1a14;
                font-size: 12px;
                font-weight: 400;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.pvp_scroll = QScrollArea()
        self.pvp_scroll.setWidgetResizable(True)
        self.pvp_scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        self.pvp_scroll.setWidget(content_widget)
        outer.addWidget(self.pvp_scroll, 1)

        root = QVBoxLayout(content_widget)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("PVP伤害计算")
        title.setObjectName("title")
        root.addWidget(title)

        hint = QLabel("灼烧、中毒、寄生、冻结作为回合结算状态单独显示。")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        team_frame = QFrame()
        team_frame.setMaximumHeight(112)
        team_layout = QHBoxLayout(team_frame)
        team_layout.setContentsMargins(0, 0, 0, 0)
        team_layout.setSpacing(8)
        self.build_team_section(team_layout, "attacker", "攻击方队伍")
        self.build_team_section(team_layout, "defender", "防守方队伍")
        root.addWidget(team_frame)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)
        preset_label = QLabel("队伍方案")
        preset_label.setObjectName("panelMeta")
        self.team_preset_combo = QComboBox()
        self.team_preset_combo.setMinimumContentsLength(16)
        self.team_preset_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_team_preset_button = QPushButton("保存队伍")
        self.load_team_preset_button = QPushButton("读取队伍")
        self.delete_team_preset_button = QPushButton("删除队伍")
        self.save_team_preset_button.clicked.connect(self.save_team_preset)
        self.load_team_preset_button.clicked.connect(self.load_selected_team_preset)
        self.delete_team_preset_button.clicked.connect(self.delete_selected_team_preset)
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.team_preset_combo, 1)
        preset_row.addWidget(self.save_team_preset_button)
        preset_row.addWidget(self.load_team_preset_button)
        preset_row.addWidget(self.delete_team_preset_button)
        root.addLayout(preset_row)
        self.refresh_team_preset_combo()

        self.attacker_combo = self.make_combo(self.pokemon, pvp_item_label)
        self.defender_combo = self.make_combo(self.pokemon, pvp_item_label)
        self.skill_combo = self.make_combo(self.skills, self.skill_label)
        self.skill_combo.setProperty("allowEmpty", True)
        self.attacker_combo.hide()
        self.defender_combo.hide()
        self.skill_combo.hide()

        self.attacker_combo.currentIndexChanged.connect(self.update_pvp_panels)
        self.defender_combo.currentIndexChanged.connect(self.update_pvp_panels)
        self.skill_combo.currentIndexChanged.connect(self.update_type_multiplier_from_current_skill)
        if self.attacker_combo.lineEdit():
            self.attacker_combo.lineEdit().editingFinished.connect(self.update_pvp_panels)
        if self.defender_combo.lineEdit():
            self.defender_combo.lineEdit().editingFinished.connect(self.update_pvp_panels)
        if self.skill_combo.lineEdit():
            self.skill_combo.lineEdit().editingFinished.connect(self.update_type_multiplier_from_current_skill)

        self.main_name_labels = {}
        self.main_meta_labels = {}
        self.main_attr_layouts = {}
        self.skill_slot_combos = {"attacker": [], "defender": []}
        self.skill_slot_info_labels = {"attacker": [], "defender": []}
        self.main_attr_edit_combos = {"attacker": [], "defender": []}
        self.current_creature_keys = {"attacker": "", "defender": ""}
        self.current_skill_choice_keys = {"attacker": None, "defender": None}
        self.updating_attr_edits = False
        self.stat_configs = {
            "attacker": self.default_stat_config(),
            "defender": self.default_stat_config(),
        }
        self.stat_edit_widgets = {"attacker": {}, "defender": {}}
        self.updating_stat_edits = False
        self.hp_percent_spins = {}
        self.hp_percent_bars = {}
        main_battle_layout = QHBoxLayout()
        main_battle_layout.setSpacing(8)
        main_battle_layout.addWidget(self.build_main_card("attacker", "我方主战"), 1)
        main_battle_layout.addWidget(self.build_main_card("defender", "敌方主战"), 1)
        root.addLayout(main_battle_layout)

        self.skill_relation_label = QLabel("克制关系：等待选择技能")
        self.skill_relation_label.setObjectName("relation")
        self.skill_relation_label.hide()

        compare_title = QLabel("属性对比")
        compare_title.setObjectName("panelTitle")
        root.addWidget(compare_title)
        self.build_stat_compare_section(root)
        self.stat_compare_tree = QTreeWidget(self)
        self.stat_compare_tree.setColumnCount(4)
        self.stat_compare_tree.setHeaderLabels(["属性", "攻击方", "防守方", "差值"])
        self.stat_compare_tree.setRootIsDecorated(False)
        self.stat_compare_tree.setMaximumHeight(150)
        self.stat_compare_tree.hide()

        self.build_matchup_section(root)

        battle_tools_layout = QHBoxLayout()
        battle_tools_layout.setSpacing(10)
        side_tool_width = 360

        parameter_frame = QFrame()
        parameter_frame.setObjectName("infoPanel")
        parameter_frame.setFixedWidth(side_tool_width)
        parameter_layout = QVBoxLayout(parameter_frame)
        parameter_layout.setContentsMargins(8, 6, 8, 6)
        parameter_layout.setSpacing(6)
        calc_header = QHBoxLayout()
        calc_title = QLabel("伤害参数")
        calc_title.setObjectName("panelTitle")
        self.reset_damage_button = QPushButton("重置")
        self.reset_damage_button.clicked.connect(self.reset_damage_controls)
        calc_header.addWidget(calc_title)
        calc_header.addStretch(1)
        calc_header.addWidget(self.reset_damage_button)
        parameter_layout.addLayout(calc_header)

        param_grid = QGridLayout()
        param_grid.setHorizontalSpacing(6)
        param_grid.setVerticalSpacing(3)
        self.type_multiplier = self.make_double_spin(0.0, 8.0, 1.0, 0.05)
        self.attack_modifier = self.make_double_spin(-95.0, 500.0, 0.0, 10.0)
        self.defense_modifier = self.make_double_spin(-95.0, 500.0, 0.0, 10.0)
        self.power_bonus = self.make_double_spin(-500.0, 500.0, 0.0, 5.0)
        self.damage_modifier = self.make_double_spin(-95.0, 500.0, 0.0, 10.0)
        self.reduction_modifier = self.make_double_spin(0.0, 100.0, 0.0, 10.0)
        self.burn_type_multiplier = self.make_double_spin(0.0, 8.0, 1.0, 0.05)
        self.auto_stab = QCheckBox("自动本系 1.25")
        self.auto_stab.setChecked(True)
        self.hit_count = ClickWheelSpinBox()
        self.hit_count.setRange(1, 20)
        self.hit_count.setValue(1)
        for widget in (
            self.type_multiplier,
            self.attack_modifier,
            self.defense_modifier,
            self.power_bonus,
            self.damage_modifier,
            self.reduction_modifier,
            self.burn_type_multiplier,
            self.hit_count,
        ):
            widget.setFixedWidth(86)

        param_label_width = 68

        def add_param_label(text, row, col):
            label = QLabel(text)
            label.setFixedWidth(param_label_width)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            param_grid.addWidget(label, row, col)

        add_param_label("本系", 0, 0)
        param_grid.addWidget(self.auto_stab, 0, 1)
        parameter_rows = [
            ("属性", self.type_multiplier),
            ("攻击%", self.attack_modifier),
            ("防御%", self.defense_modifier),
            ("威力", self.power_bonus),
            ("独伤%", self.damage_modifier),
            ("减伤%", self.reduction_modifier),
            ("连击", self.hit_count),
            ("灼烧", self.burn_type_multiplier),
        ]
        for index, (label, widget) in enumerate(parameter_rows):
            row = index // 2 + 1
            col = (index % 2) * 2
            add_param_label(label, row, col)
            param_grid.addWidget(widget, row, col + 1)

        self.status_spins = {}
        status_start_row = (len(parameter_rows) + 1) // 2 + 1
        for index, (key, label) in enumerate([
            ("burn", "灼烧层数"),
            ("poison", "中毒层数"),
            ("leech", "寄生层数"),
            ("freeze", "冻结层数"),
            ("starfall", "星陨层数"),
        ]):
            spin = ClickWheelSpinBox()
            spin.setRange(0, 99)
            spin.setValue(0)
            spin.setFixedWidth(86)
            self.status_spins[key] = spin
            row = status_start_row + index // 2
            col = (index % 2) * 2
            add_param_label(label, row, col)
            param_grid.addWidget(spin, row, col + 1)
        parameter_layout.addLayout(param_grid)

        self.wish_impact_signature = None

        action_row = QHBoxLayout()
        calculate_button = QPushButton("计算伤害")
        calculate_button.setObjectName("orangeButton")
        calculate_button.clicked.connect(self.calculate)
        action_row.addWidget(calculate_button)
        action_row.addStretch(1)
        parameter_layout.addLayout(action_row)

        self.result_label = QLabel("等待计算")
        self.result_label.setObjectName("hint")
        self.result_label.setWordWrap(True)
        parameter_layout.addWidget(self.result_label)

        self.detail_tree = QTreeWidget()
        self.detail_tree.setColumnCount(2)
        self.detail_tree.setHeaderLabels(["项目", "数值"])
        self.detail_tree.setColumnWidth(0, 180)
        self.detail_tree.setRootIsDecorated(False)
        self.detail_tree.setVisible(False)
        parameter_layout.addWidget(self.detail_tree, 1)
        battle_tools_layout.addWidget(parameter_frame, 0)

        wish_tools_layout = QVBoxLayout()
        wish_tools_layout.setContentsMargins(0, 0, 0, 0)
        wish_tools_layout.setSpacing(8)
        self.build_wish_impact_section(wish_tools_layout)
        battle_tools_layout.addLayout(wish_tools_layout, 1)

        kill_tools_layout = QVBoxLayout()
        kill_tools_layout.setContentsMargins(0, 0, 0, 0)
        kill_tools_layout.setSpacing(8)
        self.build_kill_line_section(kill_tools_layout, side_tool_width)
        battle_tools_layout.addLayout(kill_tools_layout, 0)
        root.addLayout(battle_tools_layout)
        self.connect_dynamic_pvp_inputs()

        if self.pokemon:
            self.attacker_combo.setCurrentIndex(0)
            self.defender_combo.setCurrentIndex(min(1, len(self.pokemon) - 1))
        self.restore_main_from_selected_slots()
        self.refresh_team_buttons()
        self.initializing_pvp = False
        self.update_pvp_panels()
        self.sync_primary_attack_skill_combo()

    def make_combo(self, items, label_func, use_completer=False):
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setMaxVisibleItems(18)
        combo.setProperty("noCompleter", not use_completer)
        labels = []
        for item in items:
            label = label_func(item)
            labels.append(label)
            combo.addItem(label, item)
        combo.view().setMouseTracking(True)
        combo.view().setUniformItemSizes(True)
        combo.view().setStyleSheet("""
            QListView::item:hover { background: #cfe8ff; color: #102a43; }
            QListView::item:selected { background: #bcdcff; color: #102a43; }
        """)
        if use_completer:
            completer = QCompleter(labels, combo)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            combo.setCompleter(completer)
            if completer.popup():
                completer.popup().setMouseTracking(True)
                completer.popup().setUniformItemSizes(True)
                completer.popup().setStyleSheet("""
                    QListView::item:hover { background: #cfe8ff; color: #102a43; }
                    QListView::item:selected { background: #bcdcff; color: #102a43; }
                """)
        if combo.lineEdit():
            combo.lineEdit().setClearButtonEnabled(True)
            combo.lineEdit().setPlaceholderText("输入名称搜索")
        return combo

    def set_combo_items(self, combo, items, label_func):
        current = combo.currentData()
        current_key = pokemon_key(current) if isinstance(current, dict) else ""
        current_text = combo.currentText().strip()
        combo.blockSignals(True)
        combo.clear()
        labels = []
        use_completer = not bool(combo.property("noCompleter"))
        if combo.property("allowEmpty"):
            combo.addItem("无", None)
            if use_completer:
                labels.append("无")
        for item in items:
            label = label_func(item)
            if use_completer:
                labels.append(label)
            combo.addItem(label, item)
        if use_completer:
            completer = QCompleter(labels, combo)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            combo.setCompleter(completer)
            if completer.popup():
                completer.popup().setMouseTracking(True)
                completer.popup().setUniformItemSizes(True)
                completer.popup().setStyleSheet("""
                    QListView::item:hover { background: #cfe8ff; color: #102a43; }
                    QListView::item:selected { background: #bcdcff; color: #102a43; }
                """)
        else:
            combo.setCompleter(None)
        restored = False
        for index in range(combo.count()):
            data = combo.itemData(index)
            label = label_func(data) if isinstance(data, dict) else ""
            if (
                isinstance(data, dict)
                and (pokemon_key(data) == current_key or label == current_text)
            ):
                combo.setCurrentIndex(index)
                restored = True
                break
        if not restored and combo.count() > 0:
            combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def normalize_team_slots(self, slots):
        normalized = {}
        for side in ("attacker", "defender"):
            raw_slots = []
            if isinstance(slots, dict):
                raw_slots = slots.get(side) or []
            result = []
            for slot in list(raw_slots)[:6]:
                result.append(str(slot) if slot else None)
            while len(result) < 6:
                result.append(None)
            normalized[side] = result
        return normalized

    def copy_stat_config(self, config):
        config = config if isinstance(config, dict) else {}
        valid_stats = {key for key, _label in self.stat_rows()}
        raw_ivs = config.get("ivs") if isinstance(config.get("ivs"), dict) else {}
        ivs = {}
        for key in valid_stats:
            try:
                value = int(raw_ivs.get(key, 10))
            except Exception:
                value = 10
            ivs[key] = max(0, min(10, value))
        boosted_stat = config.get("boosted_stat")
        dropped_stat = config.get("dropped_stat")
        try:
            default_iv = int(config.get("default_iv", 10))
        except Exception:
            default_iv = 10
        return {
            "ivs": ivs,
            "boosted_stat": boosted_stat if boosted_stat in valid_stats else None,
            "dropped_stat": dropped_stat if dropped_stat in valid_stats else None,
            "default_iv": max(0, min(10, default_iv)),
        }

    def empty_team_member_build(self):
        return {
            "attributes": [],
            "skills": [None, None, None, None],
            "custom_skills": False,
            "stat_config": self.default_stat_config(),
            "hp_percent": 100,
        }

    def normalize_team_member_build(self, build):
        normalized = self.empty_team_member_build()
        if not isinstance(build, dict):
            return normalized
        attrs = []
        for value in build.get("attributes") or []:
            value = str(value or "")
            if value in ATTRIBUTES and value not in attrs:
                attrs.append(value)
            if len(attrs) >= 2:
                break
        skills = []
        for value in list(build.get("skills") or [])[:4]:
            skills.append(str(value) if value else None)
        while len(skills) < 4:
            skills.append(None)
        raw_stat_config = build.get("stat_config")
        if raw_stat_config is None:
            raw_stat_config = build.get("statConfig")
        try:
            hp_percent = int(build.get("hp_percent", build.get("hpPercent", 100)))
        except Exception:
            hp_percent = 100
        normalized.update({
            "attributes": attrs,
            "skills": skills,
            "custom_skills": bool(build.get("custom_skills", "skills" in build)),
            "stat_config": self.copy_stat_config(raw_stat_config),
            "hp_percent": max(0, min(100, hp_percent)),
        })
        return normalized

    def normalize_team_member_builds(self, builds=None):
        normalized = {}
        for side in ("attacker", "defender"):
            raw_side = builds.get(side) if isinstance(builds, dict) else []
            raw_side = raw_side if isinstance(raw_side, list) else []
            side_builds = []
            for index in range(6):
                side_builds.append(self.normalize_team_member_build(
                    raw_side[index] if index < len(raw_side) else None
                ))
            normalized[side] = side_builds
        return normalized

    def current_team_build(self, side):
        slot = max(0, min(5, int(self.selected_team_slot.get(side, 0))))
        builds = self.team_member_builds.setdefault(side, [])
        while len(builds) < 6:
            builds.append(self.empty_team_member_build())
        return builds[slot]

    def skill_unique_key(self, skill):
        if not isinstance(skill, dict):
            return None
        identity = str(skill.get("id") or "").strip()
        if identity:
            return identity
        return "|".join([
            str(skill.get("name") or ""),
            str(skill.get("category") or ""),
            str(skill.get("attribute") or ""),
            str(skill.get("power") or ""),
        ])

    def set_skill_combo_to_key(self, combo, skill_key):
        combo.blockSignals(True)
        try:
            target = str(skill_key or "")
            combo.setCurrentIndex(0 if combo.count() else -1)
            if not target:
                return
            for index in range(combo.count()):
                data = combo.itemData(index)
                if self.skill_unique_key(data) == target:
                    combo.setCurrentIndex(index)
                    return
        finally:
            combo.blockSignals(False)

    def set_skill_combo_default(self, combo, fallback_index=1):
        combo.blockSignals(True)
        try:
            if combo.count() <= 1:
                combo.setCurrentIndex(0 if combo.count() else -1)
                return
            direct_index = None
            for index in range(1, combo.count()):
                skill = combo.itemData(index)
                if isinstance(skill, dict) and skill.get("power") is not None:
                    direct_index = index
                    break
            target = direct_index if direct_index is not None else min(max(1, fallback_index), combo.count() - 1)
            combo.setCurrentIndex(target)
        finally:
            combo.blockSignals(False)

    def restore_attributes_for_selected_slot(self, side, creature):
        if not hasattr(self, "main_attr_edit_combos"):
            return
        build = self.current_team_build(side)
        attrs = list(build.get("attributes") or [])
        if not attrs and creature:
            attrs = list(creature.get("attributes") or [])
        self.loading_team_member_build = True
        self.updating_attr_edits = True
        try:
            for index, combo in enumerate(self.main_attr_edit_combos.get(side, [])):
                self.set_attr_combo_to_value(combo, attrs[index] if index < len(attrs) else "")
        finally:
            self.updating_attr_edits = False
            self.loading_team_member_build = False

    def restore_stats_for_selected_slot(self, side):
        if not hasattr(self, "stat_configs"):
            return
        build = self.current_team_build(side)
        self.stat_configs[side] = self.copy_stat_config(build.get("stat_config"))
        self.refresh_stat_edit_controls()

    def restore_hp_for_selected_slot(self, side):
        spin = getattr(self, "hp_percent_spins", {}).get(side)
        if spin is None:
            return
        build = self.current_team_build(side)
        spin.blockSignals(True)
        try:
            spin.setValue(max(0, min(100, int(build.get("hp_percent", 100)))))
        finally:
            spin.blockSignals(False)
        bar = self.hp_percent_bars.get(side) if hasattr(self, "hp_percent_bars") else None
        if bar is not None:
            bar.setValue(spin.value())

    def restore_current_team_build(self, side, creature):
        self.restore_attributes_for_selected_slot(side, creature)
        self.restore_stats_for_selected_slot(side)
        self.restore_hp_for_selected_slot(side)

    def restore_skills_for_selected_slot(self, side):
        if not hasattr(self, "skill_slot_combos"):
            return
        build = self.current_team_build(side)
        skill_keys = list(build.get("skills") or [])
        self.loading_team_member_build = True
        try:
            if not build.get("custom_skills") and not any(skill_keys):
                for index, combo in enumerate(self.skill_slot_combos.get(side, [])):
                    self.set_skill_combo_default(combo, index + 1)
                return
            for index, combo in enumerate(self.skill_slot_combos.get(side, [])):
                self.set_skill_combo_to_key(combo, skill_keys[index] if index < len(skill_keys) else None)
        finally:
            self.loading_team_member_build = False

    def capture_current_side_build(self, side):
        if getattr(self, "loading_team_member_build", False) or not hasattr(self, "team_member_builds"):
            return
        slot = max(0, min(5, int(self.selected_team_slot.get(side, 0))))
        if not self.team_slots.get(side) or not self.team_slots[side][slot]:
            self.team_member_builds[side][slot] = self.empty_team_member_build()
            return
        attrs = []
        for combo in getattr(self, "main_attr_edit_combos", {}).get(side, []):
            value = str(combo.currentData() or combo.currentText() or "").strip()
            if value in ATTRIBUTES and value not in attrs:
                attrs.append(value)
        skills = []
        for combo in getattr(self, "skill_slot_combos", {}).get(side, []):
            skill = self.current_data(combo, self.skills, self.skill_label)
            skills.append(self.skill_unique_key(skill))
        while len(skills) < 4:
            skills.append(None)
        hp_spin = getattr(self, "hp_percent_spins", {}).get(side)
        self.team_member_builds[side][slot] = {
            "attributes": attrs[:2],
            "skills": skills[:4],
            "custom_skills": True,
            "stat_config": self.copy_stat_config(self.stat_config_for_side(side)),
            "hp_percent": hp_spin.value() if hp_spin is not None else 100,
        }

    def capture_all_current_builds(self):
        for side in ("attacker", "defender"):
            self.capture_current_side_build(side)

    def refresh_team_preset_combo(self, selected_name=None):
        combo = getattr(self, "team_preset_combo", None)
        if combo is None:
            return
        presets = self.team_presets_payload.get("presets", {})
        names = sorted(str(name) for name in presets.keys())
        combo.blockSignals(True)
        try:
            combo.clear()
            combo.addItem("未选择队伍方案", "")
            for name in names:
                combo.addItem(name, name)
            if selected_name:
                for index in range(combo.count()):
                    if combo.itemData(index) == selected_name:
                        combo.setCurrentIndex(index)
                        break
        finally:
            combo.blockSignals(False)

    def current_team_preset_name(self):
        combo = getattr(self, "team_preset_combo", None)
        if combo is None:
            return ""
        return str(combo.currentData() or "").strip()

    def build_team_preset_payload(self, name):
        self.capture_all_current_builds()
        return {
            "name": name,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "team_slots": self.normalize_team_slots(self.team_slots),
            "selected_team_slot": {
                "attacker": max(0, min(5, int(self.selected_team_slot.get("attacker", 0)))),
                "defender": max(0, min(5, int(self.selected_team_slot.get("defender", 0)))),
            },
            "builds": self.normalize_team_member_builds(self.team_member_builds),
        }

    def save_team_preset(self):
        current_name = self.current_team_preset_name()
        default_name = current_name or datetime.now().strftime("队伍 %m-%d %H%M")
        name, ok = QInputDialog.getText(self, "保存队伍", "方案名称：", QLineEdit.Normal, default_name)
        if not ok:
            return
        name = str(name or "").strip()
        if not name:
            QMessageBox.warning(self, "保存队伍", "请输入队伍方案名称。")
            return
        presets = self.team_presets_payload.setdefault("presets", {})
        presets[name] = self.build_team_preset_payload(name)
        save_pvp_team_presets(self.team_presets_payload)
        self.refresh_team_preset_combo(name)

    def load_selected_team_preset(self):
        name = self.current_team_preset_name()
        if not name:
            QMessageBox.information(self, "读取队伍", "请先选择一个队伍方案。")
            return
        preset = self.team_presets_payload.get("presets", {}).get(name)
        if not isinstance(preset, dict):
            QMessageBox.warning(self, "读取队伍", "这个队伍方案数据无效。")
            return
        self.apply_team_preset(preset)

    def delete_selected_team_preset(self):
        name = self.current_team_preset_name()
        if not name:
            QMessageBox.information(self, "删除队伍", "请先选择一个队伍方案。")
            return
        answer = QMessageBox.question(self, "删除队伍", f"删除队伍方案“{name}”？")
        if answer != QMessageBox.Yes:
            return
        self.team_presets_payload.get("presets", {}).pop(name, None)
        save_pvp_team_presets(self.team_presets_payload)
        self.refresh_team_preset_combo()

    def apply_team_preset(self, preset):
        self.loading_team_preset = True
        try:
            self.team_slots = self.normalize_team_slots(preset.get("team_slots") or preset.get("teamSlots"))
            self.team_member_builds = self.normalize_team_member_builds(preset.get("builds"))
            selected = preset.get("selected_team_slot") or preset.get("selectedTeamSlot") or {}
            for side in ("attacker", "defender"):
                try:
                    self.selected_team_slot[side] = max(0, min(5, int(selected.get(side, 0))))
                except Exception:
                    self.selected_team_slot[side] = 0
                item = find_pokemon_by_key(self.pokemon, self.team_slots[side][self.selected_team_slot[side]])
                combo = self.defender_combo if side == "defender" else self.attacker_combo
                if item:
                    self.set_combo_to_item(combo, item)
                else:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(-1)
                    if combo.lineEdit():
                        combo.lineEdit().clear()
                    combo.blockSignals(False)
            save_pvp_team(self.team_slots)
            self.current_creature_keys = {"attacker": "", "defender": ""}
            self.current_skill_choice_keys = {"attacker": None, "defender": None}
            self.skill_preview_cache.clear()
            self.refresh_team_buttons()
            self.update_pvp_panels()
        finally:
            self.loading_team_preset = False

    def make_double_spin(self, minimum, maximum, value, step):
        spin = ClickWheelDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(2)
        spin.setSingleStep(step)
        spin.setValue(value)
        return spin

    def rocopvp_no_key(self, value):
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        return digits.zfill(3) if digits else ""

    def rocopvp_name_key(self, value):
        text = str(value or "").strip().casefold()
        for old, new in (
            ("ⅰ", "i"),
            ("Ⅰ", "i"),
            ("ⅱ", "ii"),
            ("Ⅱ", "ii"),
            ("ⅲ", "iii"),
            ("Ⅲ", "iii"),
            ("ⅳ", "iv"),
            ("Ⅳ", "iv"),
            ("ⅴ", "v"),
            ("Ⅴ", "v"),
            ("（", ""),
            ("）", ""),
            ("(", ""),
            (")", ""),
            (" ", ""),
            ("\u3000", ""),
        ):
            text = text.replace(old, new)
        return text

    def build_rocopvp_creature_index(self):
        no_name = {}
        name_ids = {}
        by_no = {}
        for creature in self.rocopvp_creatures:
            creature_id = str(creature.get("id") or "").strip()
            no_key = self.rocopvp_no_key(creature.get("no"))
            if not creature_id:
                continue
            if no_key:
                by_no.setdefault(no_key, []).append(creature)
            names = {
                str(creature.get("name") or "").strip(),
                str(creature.get("displayName") or "").strip(),
            }
            form_name = str(creature.get("formName") or "").strip()
            base_name = str(creature.get("name") or "").strip()
            if base_name and form_name and form_name not in base_name:
                names.add(f"{base_name}（{form_name}）")
            for name in names:
                name_key = self.rocopvp_name_key(name)
                if not name_key:
                    continue
                if no_key:
                    no_name[(no_key, name_key)] = creature_id
                name_ids.setdefault(name_key, set()).add(creature_id)
        return {"no_name": no_name, "name_ids": name_ids, "by_no": by_no}

    def rocopvp_candidate_names(self, creature):
        names = []
        for key in ("name", "base_name", "displayName"):
            value = str((creature or {}).get(key) or "").strip()
            if value and value not in names:
                names.append(value)
        for name in list(names):
            if name.endswith("异色"):
                base = name[:-2].strip()
                if base and base not in names:
                    names.append(base)
            if "冬天的样子" in name:
                winter_base = name.replace("冬天的样子", "本来的样子").strip()
                if winter_base and winter_base not in names:
                    names.append(winter_base)
            if "（" in name:
                base = name.split("（", 1)[0].strip()
                if base and base not in names:
                    names.append(base)
        return names

    def rocopvp_creature_id_for(self, creature):
        if not creature:
            return ""
        no_key = self.rocopvp_no_key(creature.get("t_id") or creature.get("no"))
        names = self.rocopvp_candidate_names(creature)
        no_name = self.rocopvp_creature_index.get("no_name", {})
        for name in names:
            creature_id = no_name.get((no_key, self.rocopvp_name_key(name)))
            if creature_id:
                return creature_id
        name_ids = self.rocopvp_creature_index.get("name_ids", {})
        for name in names:
            ids = name_ids.get(self.rocopvp_name_key(name), set())
            if len(ids) == 1:
                return next(iter(ids))
        return ""

    def creature_skill_rows(self, creature):
        creature_id = self.rocopvp_creature_id_for(creature)
        if creature_id:
            rows = self.creature_skill_map.get(str(creature_id), [])
            if rows:
                return rows
        no_key = self.rocopvp_no_key((creature or {}).get("t_id") or (creature or {}).get("no"))
        fallback_options = self.rocopvp_creature_index.get("by_no", {}).get(no_key, [])
        ranked = []
        for option in fallback_options:
            fallback_id = str(option.get("id") or "").strip()
            if not fallback_id or fallback_id == creature_id:
                continue
            rows = self.creature_skill_map.get(fallback_id, [])
            if not rows:
                continue
            display_name = str(option.get("displayName") or option.get("name") or "")
            form_name = str(option.get("formName") or "")
            rank = 0 if ("本来的样子" in display_name or not form_name) else 1
            ranked.append((rank, fallback_id, rows))
        if ranked:
            ranked.sort(key=lambda item: item[0])
            return ranked[0][2]
        return []

    def normalize_rocopvp_skill(self, row):
        if not isinstance(row, dict):
            return None
        power = row.get("power")
        power_value = None
        if power is not None:
            try:
                power_value = float(power)
            except Exception:
                power_value = None
        category = str(row.get("category") or "")
        if not category:
            return None
        return {
            "id": f"rocopvp:{row.get('creatureId', '')}:{row.get('bucket', '')}:{row.get('name', '')}",
            "name": str(row.get("name") or ""),
            "category": category,
            "attribute": str(row.get("element") or row.get("attribute") or ""),
            "power": int(power_value) if power_value is not None and power_value.is_integer() else power_value,
            "cost": row.get("cost"),
            "effect": str(row.get("effect") or ""),
            "_source_text": self.skill_bucket_label(row),
            "_bucket": str(row.get("bucket") or ""),
            "_unlockLevel": str(row.get("unlockLevel") or "").strip(),
            "_from_rocopvp": True,
        }

    def build_rocopvp_skill_pool(self):
        skills = []
        seen = set()
        for rows in self.creature_skill_map.values():
            for row in rows:
                skill = self.normalize_rocopvp_skill(row)
                if not skill:
                    continue
                key = (
                    skill.get("name"),
                    skill.get("category"),
                    skill.get("attribute"),
                    skill.get("power"),
                )
                if key in seen:
                    continue
                seen.add(key)
                skills.append(skill)
        return skills

    def skill_bucket_label(self, row):
        bucket_labels = {
            "levelUp": "可学习",
            "breeding": "遗传",
            "talent": "天赋/血脉",
        }
        bucket = str((row or {}).get("bucket") or "")
        label = bucket_labels.get(bucket, bucket or "来源")
        unlock_level = str((row or {}).get("unlockLevel") or "").strip()
        if bucket == "levelUp" and unlock_level:
            label = f"{label}Lv.{unlock_level}"
        return label

    def skill_label(self, skill):
        if not isinstance(skill, dict):
            return "无"
        power = skill.get("power")
        source_text = skill.get("_source_text")
        parts = [
            str(skill.get("name", "")),
            str(skill.get("category", "")),
            str(skill.get("attribute", "")),
        ]
        if skill.get("category") in {"物攻", "魔攻"}:
            power_text = str(power) if power is not None else "--"
            parts.append(f"威力 {power_text}")
        if source_text:
            parts.append(str(source_text))
        return " / ".join(parts)

    def skill_source_text(self, creature, skill):
        if isinstance(skill, dict) and skill.get("_source_text"):
            return str(skill.get("_source_text") or "")
        if not creature or not skill:
            return ""
        skill_name = str(skill.get("name") or "")
        bucket_labels = {
            "levelUp": "可学习",
            "breeding": "遗传",
            "talent": "天赋/血脉",
        }
        bucket_order = {"levelUp": 0, "breeding": 1, "talent": 2}
        values = []
        seen = set()
        for row in self.creature_skill_rows(creature):
            if str(row.get("name") or "") != skill_name:
                continue
            bucket = str(row.get("bucket") or "")
            label = bucket_labels.get(bucket, bucket or "来源")
            unlock_level = str(row.get("unlockLevel") or "").strip()
            if bucket == "levelUp" and unlock_level:
                label = f"{label}Lv.{unlock_level}"
            if label and label not in seen:
                seen.add(label)
                level = int(unlock_level) if unlock_level.isdigit() else 999
                values.append((bucket_order.get(bucket, 90), level, label))
        values.sort()
        return "、".join(label for _rank, _level, label in values)

    def skill_with_source(self, creature, skill):
        if not creature or not isinstance(skill, dict):
            return skill
        if skill.get("_source_text"):
            return skill
        source_text = self.skill_source_text(creature, skill)
        if not source_text:
            return skill
        patched = dict(skill)
        patched["_source_text"] = source_text
        return patched

    def skill_with_battle_preview(self, source_side, creature, opponent, skill):
        patched = self.skill_with_source(creature, skill)
        if not creature or not opponent or not isinstance(patched, dict):
            return patched
        target_side = "defender" if source_side == "attacker" else "attacker"
        cache_key = (
            source_side,
            pokemon_key(creature),
            tuple(self.selected_attributes_for_side(source_side, creature)),
            repr(self.stat_config_for_side(source_side)),
            pokemon_key(opponent),
            tuple(self.selected_attributes_for_side(target_side, opponent)),
            repr(self.stat_config_for_side(target_side)),
            str(patched.get("id") or ""),
            str(patched.get("name") or ""),
            str(patched.get("category") or ""),
            str(patched.get("attribute") or ""),
            str(patched.get("power") or ""),
            self.auto_stab.isChecked() if hasattr(self, "auto_stab") else True,
            round(self.attack_modifier.value(), 3) if hasattr(self, "attack_modifier") else 0,
            round(self.defense_modifier.value(), 3) if hasattr(self, "defense_modifier") else 0,
            round(self.power_bonus.value(), 3) if hasattr(self, "power_bonus") else 0,
            round(self.damage_modifier.value(), 3) if hasattr(self, "damage_modifier") else 0,
            round(self.reduction_modifier.value(), 3) if hasattr(self, "reduction_modifier") else 0,
            self.hit_count.value() if hasattr(self, "hit_count") else 1,
        )
        cached = self.skill_preview_cache.get(cache_key)
        if cached is not None:
            return cached
        result = calculate_pvp_damage(
            creature,
            opponent,
            patched,
            self.kill_line_options(creature, opponent, patched, source_side, target_side),
            self.formula,
        )
        if not result.get("ok"):
            return patched
        details = result.get("details", {})
        patched = dict(patched)
        patched["_expected_damage"] = int(result.get("damage") or 0)
        patched["_display_power"] = int(details.get("display_power") or 0)
        self.skill_preview_cache[cache_key] = patched
        return patched

    def skill_source_rank(self, creature, skill):
        if not creature or not isinstance(skill, dict):
            return (99, 999, "")
        bucket = str(skill.get("_bucket") or "")
        if bucket:
            order = {"levelUp": 0, "breeding": 1, "talent": 2}
            unlock_level = str(skill.get("_unlockLevel") or "").strip()
            level = int(unlock_level) if unlock_level.isdigit() else 999
            return (order.get(bucket, 90), level, str(skill.get("name") or ""))
        order = {"levelUp": 0, "breeding": 1, "talent": 2}
        skill_name = str(skill.get("name") or "")
        ranks = []
        levels = []
        for row in self.creature_skill_rows(creature):
            if str(row.get("name") or "") != skill_name:
                continue
            bucket = str(row.get("bucket") or "")
            ranks.append(order.get(bucket, 90))
            unlock_level = str(row.get("unlockLevel") or "").strip()
            if unlock_level.isdigit():
                levels.append(int(unlock_level))
        rank = min(ranks) if ranks else 90
        level = min(levels) if levels else 999
        return (rank, level, skill_name)

    def pvp_icon_path(self, kind, name):
        if not name:
            return None
        path = PROJECT_DIR / "assets" / "pvp" / kind / f"{name}.png"
        return path if path.exists() else None

    def make_pvp_icon_label(self, kind, name, size=22):
        label = QLabel(str(name or ""))
        label.setToolTip(str(name or ""))
        label.setAlignment(Qt.AlignCenter)
        if kind in ("attributes", "stats"):
            label.setStyleSheet("""
                QLabel {
                    background: #5a4630;
                    border: 1px solid #d9c79b;
                    border-radius: 12px;
                    color: #fff8e8;
                    padding: 2px;
                }
            """)
        path = self.pvp_icon_path(kind, name)
        if path:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                if kind == "stats":
                    badge_size = size + 8
                    badge = QPixmap(badge_size, badge_size)
                    badge.fill(Qt.transparent)
                    painter = QPainter(badge)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setBrush(QColor("#5a4630"))
                    painter.setPen(QPen(QColor("#d9c79b"), 1))
                    painter.drawEllipse(0, 0, badge_size - 1, badge_size - 1)
                    x = (badge_size - scaled.width()) // 2
                    y = (badge_size - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)
                    painter.end()
                    label.setPixmap(badge)
                    label.setFixedSize(badge_size, badge_size)
                    label.setStyleSheet("")
                else:
                    label.setPixmap(scaled)
                    label.setFixedSize(size + 6, size + 6)
                    label.setStyleSheet("")
        return label

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self.clear_layout(child_layout)

    def build_main_card(self, side, title):
        frame = QFrame()
        frame.setMinimumHeight(300)
        frame.setMaximumHeight(340)
        frame.setMinimumWidth(0)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 249, 234, 0.92);
                border: 1px solid #d9c79b;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        layout.addWidget(title_label)

        name_label = QLabel("未选择")
        name_label.setObjectName("panelTitle")
        name_label.setMaximumHeight(22)
        self.main_name_labels[side] = name_label
        layout.addWidget(name_label)

        attr_layout = QHBoxLayout()
        attr_layout.setSpacing(4)
        self.main_attr_layouts[side] = attr_layout
        layout.addLayout(attr_layout)

        attr_edit_row = QHBoxLayout()
        attr_edit_row.setSpacing(4)
        attr_edit_row.addWidget(QLabel("属性"))
        for index in range(2):
            combo = QComboBox()
            combo.setMaximumWidth(72)
            combo.addItem("无", "")
            for attr in ATTRIBUTES:
                combo.addItem(attr, attr)
            combo.currentIndexChanged.connect(
                lambda _idx=0, s=side: self.on_attribute_override_changed(s)
            )
            self.main_attr_edit_combos[side].append(combo)
            attr_edit_row.addWidget(combo)
        attr_edit_row.addStretch(1)
        layout.addLayout(attr_edit_row)

        meta_label = QLabel("")
        meta_label.setObjectName("panelMeta")
        meta_label.setWordWrap(True)
        meta_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        meta_label.setMaximumHeight(46)
        self.main_meta_labels[side] = meta_label
        layout.addWidget(meta_label)

        hp_row = QHBoxLayout()
        hp_row.setSpacing(6)
        hp_label = QLabel("血量")
        hp_label.setObjectName("panelMeta")
        hp_bar = QProgressBar()
        hp_bar.setRange(0, 100)
        hp_bar.setValue(100)
        hp_bar.setTextVisible(False)
        hp_spin = ClickWheelSpinBox()
        hp_spin.setRange(0, 100)
        hp_spin.setValue(100)
        hp_spin.setSuffix("%")
        hp_spin.setMaximumWidth(60)
        hp_spin.valueChanged.connect(lambda value, s=side: self.on_hp_percent_changed(s, value))
        self.hp_percent_spins[side] = hp_spin
        self.hp_percent_bars[side] = hp_bar
        hp_row.addWidget(hp_label)
        hp_row.addWidget(hp_bar, 1)
        hp_row.addWidget(hp_spin)
        layout.addLayout(hp_row)

        skill_grid = QGridLayout()
        skill_grid.setHorizontalSpacing(4)
        skill_grid.setVerticalSpacing(5)
        for index in range(4):
            slot_widget = QWidget()
            slot_layout = QHBoxLayout(slot_widget)
            slot_layout.setContentsMargins(0, 0, 0, 0)
            slot_layout.setSpacing(4)
            combo = self.make_combo(self.skills, self.skill_label)
            combo.setProperty("allowEmpty", True)
            combo.setMinimumHeight(32)
            combo.setMaximumHeight(38)
            combo.setMinimumWidth(180)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.currentIndexChanged.connect(
                lambda _idx=0, s=side, slot=index: self.on_skill_slot_changed(s, slot)
            )
            self.skill_slot_combos[side].append(combo)
            info_label = QLabel("")
            info_label.setObjectName("skillPreview")
            info_label.setStyleSheet("color: #1f1a14; font-size: 12px; font-weight: 400;")
            info_label.setFixedWidth(76)
            info_label.setMinimumHeight(34)
            info_label.setWordWrap(True)
            info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.skill_slot_info_labels[side].append(info_label)
            skill_label = QLabel(f"技能{index + 1}")
            skill_label.setFixedWidth(42)
            skill_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            slot_layout.addWidget(skill_label)
            slot_layout.addWidget(combo, 1)
            slot_layout.addWidget(info_label)
            skill_grid.addWidget(slot_widget, index // 2, index % 2)
        skill_grid.setColumnStretch(0, 1)
        skill_grid.setColumnStretch(1, 1)
        layout.addLayout(skill_grid)
        return frame

    def on_hp_percent_changed(self, side, value):
        bar = self.hp_percent_bars.get(side)
        if bar is not None:
            bar.setValue(value)
        self.capture_current_side_build(side)
        self.update_kill_lines()

    def set_attr_combo_to_value(self, combo, value):
        for index in range(combo.count()):
            if str(combo.itemData(index) or "") == str(value or ""):
                combo.setCurrentIndex(index)
                return
        combo.setCurrentIndex(0)

    def sync_attribute_editors(self, side, creature):
        key = pokemon_key(creature) if creature else ""
        if self.current_creature_keys.get(side) == key:
            return
        self.current_creature_keys[side] = key
        attrs = list(creature.get("attributes") or []) if creature else []
        self.updating_attr_edits = True
        try:
            for index, combo in enumerate(self.main_attr_edit_combos.get(side, [])):
                self.set_attr_combo_to_value(combo, attrs[index] if index < len(attrs) else "")
        finally:
            self.updating_attr_edits = False

    def selected_attributes_for_side(self, side, fallback_creature=None):
        attrs = []
        for combo in self.main_attr_edit_combos.get(side, []):
            text = combo.currentText().strip()
            value = text if text in ATTRIBUTES else str(combo.currentData() or "")
            if value and value not in attrs:
                attrs.append(value)
        if attrs:
            return attrs
        return list((fallback_creature or {}).get("attributes") or [])

    def effective_creature(self, side, creature=None):
        creature = creature or self.current_data(
            self.defender_combo if side == "defender" else self.attacker_combo,
            self.pokemon,
            pvp_item_label,
        )
        if not creature:
            return None
        patched = dict(creature)
        patched["attributes"] = self.selected_attributes_for_side(side, creature)
        return patched

    def on_attribute_override_changed(self, side):
        if self.updating_attr_edits:
            return
        self.capture_current_side_build(side)
        self.update_pvp_panels()

    def stat_icon_names(self):
        return {
            "hp": "hp",
            "attack": "physicalAttack",
            "special_attack": "magicalAttack",
            "defense": "physicalDefense",
            "special_defense": "magicalDefense",
            "speed": "speed",
        }

    def stat_rows(self):
        return [
            ("hp", "生命"),
            ("attack", "物攻"),
            ("special_attack", "魔攻"),
            ("defense", "物防"),
            ("special_defense", "魔防"),
            ("speed", "速度"),
        ]

    def default_stat_config(self):
        return {
            "ivs": {key: 10 for key, _label in self.stat_rows()},
            "boosted_stat": None,
            "dropped_stat": None,
            "default_iv": 10,
        }

    def stat_config_for_side(self, side):
        return self.stat_configs.get(side) or self.default_stat_config()

    def build_stat_compare_section(self, parent_layout):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.stat_compare_widgets = {"attacker": {}, "defender": {}}
        for side, title in (("attacker", "我方"), ("defender", "敌方")):
            panel = QFrame()
            panel.setObjectName("infoPanel")
            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(10, 8, 10, 8)
            panel_layout.setSpacing(6)
            title_label = QLabel(title)
            title_label.setObjectName("panelTitle")
            panel_layout.addWidget(title_label)
            for key, label in self.stat_rows():
                row = QHBoxLayout()
                row.setSpacing(6)
                icon_label = self.make_pvp_icon_label("stats", self.stat_icon_names().get(key), 22)
                name_label = QLabel(label)
                name_label.setMinimumWidth(38)
                value_label = QLabel("-")
                value_label.setObjectName("dangerText")
                value_label.setMinimumWidth(42)
                bar = QProgressBar()
                bar.setRange(0, 650)
                bar.setValue(0)
                bar.setTextVisible(False)
                plus_label = QPushButton("性格+")
                minus_label = QPushButton("性格-")
                plus_label.setCheckable(True)
                minus_label.setCheckable(True)
                plus_label.setObjectName("statChip")
                minus_label.setObjectName("statChip")
                plus_label.clicked.connect(
                    lambda _checked=False, s=side, stat=key: self.set_stat_nature(s, stat, "boost")
                )
                minus_label.clicked.connect(
                    lambda _checked=False, s=side, stat=key: self.set_stat_nature(s, stat, "drop")
                )
                iv_spin = ClickWheelSpinBox()
                iv_spin.setObjectName("ivSpin")
                iv_spin.setRange(0, 10)
                iv_spin.setValue(10)
                iv_spin.valueChanged.connect(
                    lambda value, s=side, stat=key: self.set_stat_iv(s, stat, value)
                )
                row.addWidget(icon_label)
                row.addWidget(name_label)
                row.addWidget(value_label)
                row.addWidget(bar, 1)
                row.addWidget(plus_label)
                row.addWidget(minus_label)
                row.addWidget(iv_spin)
                panel_layout.addLayout(row)
                self.stat_compare_widgets[side][key] = {
                    "value": value_label,
                    "bar": bar,
                }
                self.stat_edit_widgets[side][key] = {
                    "boost": plus_label,
                    "drop": minus_label,
                    "iv": iv_spin,
                }
            layout.addWidget(panel, 1)
        parent_layout.addLayout(layout)

    def set_stat_nature(self, side, stat, mode):
        if self.updating_stat_edits:
            return
        config = self.stat_config_for_side(side)
        if mode == "boost":
            config["boosted_stat"] = None if config.get("boosted_stat") == stat else stat
            if config.get("dropped_stat") == stat:
                config["dropped_stat"] = None
        else:
            config["dropped_stat"] = None if config.get("dropped_stat") == stat else stat
            if config.get("boosted_stat") == stat:
                config["boosted_stat"] = None
        self.refresh_stat_edit_controls()
        self.capture_current_side_build(side)
        self.update_pvp_panels()

    def set_stat_iv(self, side, stat, value):
        if self.updating_stat_edits:
            return
        self.stat_config_for_side(side).setdefault("ivs", {})[stat] = int(value)
        self.capture_current_side_build(side)
        self.update_pvp_panels()

    def refresh_stat_edit_controls(self):
        self.updating_stat_edits = True
        try:
            for side, rows in self.stat_edit_widgets.items():
                config = self.stat_config_for_side(side)
                ivs = config.get("ivs", {})
                for stat, widgets in rows.items():
                    widgets["boost"].setChecked(config.get("boosted_stat") == stat)
                    widgets["drop"].setChecked(config.get("dropped_stat") == stat)
                    widgets["iv"].setValue(int(ivs.get(stat, 10)))
        finally:
            self.updating_stat_edits = False

    def build_matchup_section(self, parent_layout):
        self.matchup_toggle = QPushButton("属性打击面 / 受击倍率    收起")
        self.matchup_toggle.setObjectName("sectionToggle")
        self.matchup_toggle.clicked.connect(self.toggle_matchup_section)
        parent_layout.addWidget(self.matchup_toggle)

        self.matchup_content = QFrame()
        self.matchup_content.setObjectName("infoPanel")
        content_layout = QHBoxLayout(self.matchup_content)
        content_layout.setContentsMargins(10, 8, 10, 8)
        content_layout.setSpacing(18)
        self.matchup_labels = {"attacker": {}, "defender": {}}
        for side, title in (("attacker", "我方"), ("defender", "敌方")):
            side_layout = QVBoxLayout()
            side_layout.setSpacing(5)
            title_label = QLabel(title)
            title_label.setObjectName("panelTitle")
            weak_label = QLabel()
            resist_label = QLabel()
            cover_label = QLabel()
            for label in (weak_label, resist_label, cover_label):
                label.setWordWrap(True)
                label.setObjectName("panelMeta")
            self.matchup_labels[side] = {
                "title": title_label,
                "weak": weak_label,
                "resist": resist_label,
                "cover": cover_label,
            }
            side_layout.addWidget(title_label)
            side_layout.addWidget(weak_label)
            side_layout.addWidget(resist_label)
            side_layout.addWidget(cover_label)
            side_layout.addStretch(1)
            content_layout.addLayout(side_layout, 1)
        parent_layout.addWidget(self.matchup_content)

    def toggle_matchup_section(self):
        show = not self.matchup_content.isVisible()
        self.matchup_content.setVisible(show)
        self.matchup_toggle.setText(f"属性打击面 / 受击倍率    {'收起' if show else '展开'}")

    def format_type_matchups(self, creature, mode):
        if not creature:
            return "暂无"
        defender_attrs = creature.get("attributes") or []
        values = []
        for attr in ATTRIBUTES:
            multiplier = type_multiplier_for(attr, defender_attrs)
            if (mode == "weak" and multiplier > 1) or (mode == "resist" and multiplier < 1):
                values.append(f"{attr}×{multiplier:g}")
        return "、".join(values) if values else "暂无"

    def carried_skill_cover_text(self, side, opponent):
        if not opponent:
            return "暂无"
        values = []
        seen = set()
        for combo in self.skill_slot_combos.get(side, []):
            skill = self.current_data(combo, self.skills, self.skill_label)
            attr = str(skill.get("attribute") or "") if skill else ""
            if not attr or attr in seen:
                continue
            multiplier = type_multiplier_for(attr, opponent.get("attributes") or [])
            if multiplier > 1:
                seen.add(attr)
                values.append(f"{attr}×{multiplier:g}")
        return "、".join(values) if values else "暂无"

    def update_matchup_panel(self):
        if not hasattr(self, "matchup_labels"):
            return
        attacker = self.effective_creature("attacker")
        defender = self.effective_creature("defender")
        pairs = {
            "attacker": ("我方", attacker, defender),
            "defender": ("敌方", defender, attacker),
        }
        for side, (title, creature, opponent) in pairs.items():
            labels = self.matchup_labels.get(side, {})
            if not labels:
                continue
            creature_name = pvp_item_label(creature) if creature else "未选择"
            labels["title"].setText(f"{title} {creature_name}")
            labels["weak"].setText(f"被克制属性：{self.format_type_matchups(creature, 'weak')}")
            labels["resist"].setText(f"抵抗属性：{self.format_type_matchups(creature, 'resist')}")
            labels["cover"].setText(f"携带技能可克制：{self.carried_skill_cover_text(side, opponent)}")

    def build_wish_impact_section(self, parent_layout):
        self.wish_impact_toggle = QPushButton("愿力冲击    展开")
        self.wish_impact_toggle.setObjectName("sectionToggle")
        self.wish_impact_toggle.clicked.connect(self.toggle_wish_impact_section)
        parent_layout.addWidget(self.wish_impact_toggle)

        self.wish_impact_content = QFrame()
        self.wish_impact_content.setObjectName("infoPanel")
        layout = QVBoxLayout(self.wish_impact_content)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        self.wish_impact_label = QLabel("愿力冲击：等待选择双方主战")
        self.wish_impact_label.setObjectName("hint")
        self.wish_impact_label.setWordWrap(True)
        layout.addWidget(self.wish_impact_label)

        table_row = QHBoxLayout()
        table_row.setSpacing(10)
        self.wish_tables = {}
        for side, title in (("attacker", "我方愿力"), ("defender", "敌方愿力")):
            side_layout = QVBoxLayout()
            side_label = QLabel(title)
            side_label.setObjectName("panelTitle")
            table = QTreeWidget()
            table.setColumnCount(5)
            table.setHeaderLabels(["血脉", "倍率", "显示威力", "普通", "应对"])
            table.setRootIsDecorated(False)
            table.setAlternatingRowColors(True)
            table.setUniformRowHeights(True)
            table.setMaximumHeight(170)
            table.setMinimumHeight(120)
            self.wish_tables[side] = table
            side_layout.addWidget(side_label)
            side_layout.addWidget(table, 1)
            table_row.addLayout(side_layout, 1)
        layout.addLayout(table_row)
        parent_layout.addWidget(self.wish_impact_content)
        self.wish_impact_toggle.setText("愿力冲击    收起")

    def toggle_wish_impact_section(self):
        show = not self.wish_impact_content.isVisible()
        self.wish_impact_content.setVisible(show)
        self.wish_impact_toggle.setText(f"愿力冲击    {'收起' if show else '展开'}")

    def build_kill_line_section(self, parent_layout, fixed_width=None):
        frame = QFrame()
        frame.setObjectName("infoPanel")
        if fixed_width:
            frame.setFixedWidth(fixed_width)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("双方斩杀线")
        title.setObjectName("panelTitle")
        self.kill_detail_toggle = QPushButton("详细倍率 展开")
        self.kill_detail_toggle.setObjectName("sectionToggle")
        self.kill_detail_toggle.clicked.connect(self.toggle_kill_detail_section)
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(self.kill_detail_toggle)
        layout.addLayout(title_row)

        summary_row = QHBoxLayout()
        self.kill_summary_labels = {}
        summary_column = QVBoxLayout()
        summary_column.setSpacing(8)
        for side, title in (("attacker", "我方进攻"), ("defender", "敌方进攻")):
            label = QLabel(f"{title}：等待选择")
            label.setWordWrap(True)
            label.setTextFormat(Qt.RichText)
            label.setObjectName("panelMeta")
            self.kill_summary_labels[side] = label
            summary_column.addWidget(label)
        layout.addLayout(summary_column)

        self.kill_detail_content = QFrame()
        detail_layout = QHBoxLayout(self.kill_detail_content)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(10)
        self.kill_detail_labels = {}
        for side in ("attacker", "defender"):
            label = QLabel("")
            label.setWordWrap(True)
            label.setObjectName("panelMeta")
            self.kill_detail_labels[side] = label
            detail_layout.addWidget(label, 1)
        self.kill_detail_content.hide()
        layout.addWidget(self.kill_detail_content)
        parent_layout.addWidget(frame)

        self.matchup_content.hide()
        self.matchup_toggle.setText("属性打击面 / 受击倍率    展开")

    def toggle_kill_detail_section(self):
        show = not self.kill_detail_content.isVisible()
        self.kill_detail_content.setVisible(show)
        self.kill_detail_toggle.setText(f"详细倍率 {'收起' if show else '展开'}")

    def connect_dynamic_pvp_inputs(self):
        for widget in (
            self.attack_modifier,
            self.defense_modifier,
            self.power_bonus,
            self.damage_modifier,
            self.reduction_modifier,
            self.hit_count,
            self.burn_type_multiplier,
        ):
            widget.valueChanged.connect(lambda _value=0: self.on_damage_parameter_changed())
        for spin in self.status_spins.values():
            spin.valueChanged.connect(lambda _value=0: self.update_kill_lines())
        self.auto_stab.toggled.connect(lambda _checked=False: self.on_damage_parameter_changed())

    def on_damage_parameter_changed(self):
        self.skill_preview_cache.clear()
        QTimer.singleShot(0, self.refresh_deferred_pvp_calculations)

    def refresh_deferred_pvp_calculations(self):
        self.refresh_skill_choices("attacker", self.effective_creature("attacker"))
        self.refresh_skill_choices("defender", self.effective_creature("defender"))
        self.update_kill_lines()
        self.update_wish_impact_preview()

    def reset_damage_controls(self):
        self.auto_stab.setChecked(True)
        self.type_multiplier.setValue(1.0)
        self.attack_modifier.setValue(0.0)
        self.defense_modifier.setValue(0.0)
        self.power_bonus.setValue(0.0)
        self.damage_modifier.setValue(0.0)
        self.reduction_modifier.setValue(0.0)
        self.hit_count.setValue(1)
        self.burn_type_multiplier.setValue(1.0)
        for spin in self.status_spins.values():
            spin.setValue(0)
        self.update_type_multiplier_from_current_skill()
        self.update_kill_lines()
        self.update_wish_impact_preview()

    def calculate_wish_impact(self, source_side, target_side):
        attacker = self.effective_creature(source_side)
        defender = self.effective_creature(target_side)
        if not attacker or not defender:
            return None
        attacker_stats = derived_stats(attacker, self.stat_config_for_side(source_side))
        defender_stats = derived_stats(defender, self.stat_config_for_side(target_side))
        if attacker_stats.get("special_attack", 0) >= attacker_stats.get("attack", 0):
            category = "魔攻"
            channel = "魔法"
        else:
            category = "物攻"
            channel = "物理"
        estimates = []
        for attribute in dict.fromkeys(ATTRIBUTES):
            type_multiplier = type_multiplier_for(attribute, defender.get("attributes") or [])
            normal = self.calculate_wish_attribute(
                attacker,
                defender,
                source_side,
                target_side,
                category,
                attribute,
                type_multiplier,
                1.0,
            )
            counter = self.calculate_wish_attribute(
                attacker,
                defender,
                source_side,
                target_side,
                category,
                attribute,
                type_multiplier,
                2.5,
            )
            estimates.append({
                "attribute": attribute,
                "type_multiplier": type_multiplier,
                "normal": normal,
                "counter": counter,
            })
        estimates.sort(key=lambda row: row["normal"].get("display_power", 0), reverse=True)
        best = estimates[0] if estimates else None
        return {
            "channel": channel,
            "best": best,
            "estimates": estimates,
        }

    def calculate_wish_attribute(
        self,
        attacker,
        defender,
        source_side,
        target_side,
        category,
        attribute,
        type_multiplier,
        factor,
    ):
        result = calculate_pvp_damage(
            attacker,
            defender,
            {
                "name": "愿力冲击",
                "category": category,
                "attribute": attribute,
                "power": 80 * factor,
            },
            {
                "type_multiplier": type_multiplier,
                "auto_stab": True,
                "attack_modifier_percent": self.attack_modifier.value(),
                "defense_modifier_percent": self.defense_modifier.value(),
                "power_bonus": self.power_bonus.value(),
                "damage_modifier_percent": self.damage_modifier.value(),
                "reduction_percent": 0.0,
                "hit_count": 1,
                "attacker_stat_config": self.stat_config_for_side(source_side),
                "defender_stat_config": self.stat_config_for_side(target_side),
            },
            self.formula,
        )
        details = result.get("details", {}) if result.get("ok") else {}
        return {
            "damage": int(result.get("damage") or 0),
            "display_power": int(details.get("display_power") or 0),
        }

    def update_wish_impact_preview(self):
        if not hasattr(self, "wish_impact_label"):
            return
        signature = (
            pokemon_key(self.effective_creature("attacker") or {}),
            tuple(self.selected_attributes_for_side("attacker", self.effective_creature("attacker") or {})),
            repr(self.stat_config_for_side("attacker")),
            pokemon_key(self.effective_creature("defender") or {}),
            tuple(self.selected_attributes_for_side("defender", self.effective_creature("defender") or {})),
            repr(self.stat_config_for_side("defender")),
            round(self.attack_modifier.value(), 3),
            round(self.defense_modifier.value(), 3),
            round(self.power_bonus.value(), 3),
            round(self.damage_modifier.value(), 3),
        )
        if signature == self.wish_impact_signature:
            return
        self.wish_impact_signature = signature
        left = self.calculate_wish_impact("attacker", "defender")
        right = self.calculate_wish_impact("defender", "attacker")
        if not left or not right:
            self.wish_impact_label.setText("愿力冲击：等待选择双方主战")
            self.populate_wish_table("attacker", None)
            self.populate_wish_table("defender", None)
            return
        def format_wish(payload):
            best = payload.get("best") or {}
            normal = best.get("normal") or {}
            counter = best.get("counter") or {}
            return (
                f"{payload.get('channel', '')}通道 {best.get('attribute', '无')}×{best.get('type_multiplier', 1):g} "
                f"显威{normal.get('display_power', 0)} 普通{normal.get('damage', 0)} / "
                f"应对{counter.get('damage', 0)}"
            )
        self.wish_impact_label.setText(
            "愿力冲击（RocoPVP，基础80/应对2.5倍）："
            f"我方→敌方 {format_wish(left)}；敌方→我方 {format_wish(right)}"
        )
        self.populate_wish_table("attacker", left)
        self.populate_wish_table("defender", right)

    def populate_wish_table(self, side, payload):
        table = getattr(self, "wish_tables", {}).get(side)
        if table is None:
            return
        table.clear()
        if not payload:
            table.addTopLevelItem(QTreeWidgetItem(["等待选择", "-", "-", "-", "-"]))
            return
        for estimate in payload.get("estimates", []):
            normal = estimate.get("normal") or {}
            counter = estimate.get("counter") or {}
            item = QTreeWidgetItem([
                str(estimate.get("attribute") or ""),
                f"×{estimate.get('type_multiplier', 1):g}",
                str(normal.get("display_power", 0)),
                str(normal.get("damage", 0)),
                str(counter.get("damage", 0)),
            ])
            icon_path = self.pvp_icon_path("attributes", estimate.get("attribute"))
            if icon_path:
                item.setIcon(0, QIcon(str(icon_path)))
            table.addTopLevelItem(item)
        for column in range(table.columnCount()):
            table.resizeColumnToContents(column)

    def calculate_starfall_damage(self, attacker, defender):
        spin = self.status_spins.get("starfall")
        stacks = spin.value() if spin is not None else 0
        if stacks <= 0:
            return {"damage": 0, "stacks": 0}
        power = 30 * stacks
        type_multiplier = type_multiplier_for("幻", defender.get("attributes") or [])
        result = calculate_pvp_damage(
            attacker,
            defender,
            {
                "name": "星陨印记",
                "category": "魔攻",
                "attribute": "幻",
                "power": power,
            },
            {
                "type_multiplier": type_multiplier,
                "auto_stab": False,
                "attack_modifier_percent": self.attack_modifier.value(),
                "defense_modifier_percent": self.defense_modifier.value(),
                "power_bonus": 0.0,
                "damage_modifier_percent": self.damage_modifier.value(),
                "reduction_percent": self.reduction_modifier.value(),
                "hit_count": 1,
                "attacker_stat_config": self.stat_config_for_side("attacker"),
                "defender_stat_config": self.stat_config_for_side("defender"),
            },
            self.formula,
        )
        if not result.get("ok"):
            return {"damage": 0, "stacks": stacks, "power": power, "type_multiplier": type_multiplier}
        return {
            "damage": int(result.get("damage") or 0),
            "stacks": stacks,
            "power": power,
            "type_multiplier": type_multiplier,
            "details": result.get("details", {}),
        }

    def selected_side_skills(self, side):
        skills = []
        seen = set()
        for combo in self.skill_slot_combos.get(side, []):
            skill = self.current_data(combo, self.skills, self.skill_label)
            if not skill:
                continue
            key = (
                str(skill.get("id") or ""),
                str(skill.get("name") or ""),
                str(skill.get("attribute") or ""),
                str(skill.get("category") or ""),
                str(skill.get("power") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            skills.append(skill)
        return skills

    def kill_line_options(self, attacker, defender, skill, source_side, target_side):
        return {
            "type_multiplier": type_multiplier_for(skill.get("attribute"), defender.get("attributes") or []),
            "auto_stab": self.auto_stab.isChecked(),
            "attack_modifier_percent": self.attack_modifier.value(),
            "defense_modifier_percent": self.defense_modifier.value(),
            "power_bonus": self.power_bonus.value(),
            "damage_modifier_percent": self.damage_modifier.value(),
            "reduction_percent": self.reduction_modifier.value(),
            "hit_count": self.hit_count.value(),
            "attacker_stat_config": self.stat_config_for_side(source_side),
            "defender_stat_config": self.stat_config_for_side(target_side),
        }

    def best_kill_line(self, source_side, attacker, defender, target_side):
        if not attacker or not defender:
            return None
        best = None
        for skill in self.selected_side_skills(source_side):
            result = calculate_pvp_damage(
                attacker,
                defender,
                skill,
                self.kill_line_options(attacker, defender, skill, source_side, target_side),
                self.formula,
            )
            if not result.get("ok"):
                continue
            if best is None or result.get("damage", 0) > best["result"].get("damage", 0):
                best = {"skill": skill, "result": result}
        if best is None:
            return None
        stats = derived_stats(defender, self.stat_config_for_side(target_side))
        max_hp = max(1, int(stats.get("hp") or 1))
        hp_percent = self.hp_percent_spins.get(target_side).value() if target_side in self.hp_percent_spins else 100
        current_hp = max_hp * hp_percent / 100.0
        damage = int(best["result"].get("damage") or 0)
        kill_percent = min(999.0, damage / max_hp * 100.0)
        hits_to_kill = "∞" if damage <= 0 else str(max(1, math.ceil(current_hp / max(1, damage))))
        details = best["result"].get("details", {})
        skill_name = best["skill"].get("name")
        summary = "<br>".join([
            f"<b>{'我方进攻' if source_side == 'attacker' else '敌方进攻'}</b>",
            f"{pvp_item_label(attacker)} → {pvp_item_label(defender)}",
            f"技能：{skill_name}",
            f"预计伤害：{damage}    显示威力：{details.get('display_power'):.0f}",
            f"斩杀线：HP≤{kill_percent:.1f}%    当前：{hp_percent}%",
            f"需要：{hits_to_kill} 次",
        ])
        detail = (
            f"{skill_name}："
            f"威力 {details.get('skill_power'):.0f} / 显示威力 {details.get('display_power'):.0f} / "
            f"本系×{details.get('stab_multiplier'):.2f} / 属性×{details.get('type_multiplier'):.2f} / "
            f"攻防×{details.get('ability_multiplier'):.3f} / 减伤×{details.get('reduction_modifier'):.2f} / "
            f"独伤×{details.get('damage_modifier'):.2f} / 单段 {best['result'].get('single_damage')} / "
            f"连击 {best['result'].get('hit_count')}"
        )
        return {
            "summary": summary,
            "detail": detail,
            "kills_current": damage >= current_hp,
        }

    def update_kill_lines(self):
        if not hasattr(self, "kill_summary_labels"):
            return
        attacker = self.effective_creature("attacker")
        defender = self.effective_creature("defender")
        directions = {
            "attacker": (attacker, defender, "defender"),
            "defender": (defender, attacker, "attacker"),
        }
        for side, (source, target, target_side) in directions.items():
            payload = self.best_kill_line(side, source, target, target_side)
            summary_label = self.kill_summary_labels.get(side)
            detail_label = self.kill_detail_labels.get(side)
            if not payload:
                if summary_label:
                    summary_label.setText("等待选择主战精灵和技能")
                if detail_label:
                    detail_label.setText("")
                continue
            status = "可斩杀" if payload["kills_current"] else "未到斩杀线"
            if summary_label:
                summary_label.setText(f"{payload['summary']}<br>状态：{status}")
            if detail_label:
                detail_label.setText(payload["detail"])

    def build_team_section(self, parent_layout, side, title):
        section_frame = QFrame()
        section_frame.setObjectName("infoPanel")
        section = QVBoxLayout(section_frame)
        section.setContentsMargins(6, 4, 6, 4)
        section.setSpacing(2)
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        title_label.setMaximumHeight(20)
        header.addWidget(title_label)
        header.addStretch(1)
        section.addLayout(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(2)
        for index in range(6):
            slot_frame, combo = self.make_team_slot_combo(side, index)
            self.team_slot_combos[side].append(combo)
            grid.addWidget(slot_frame, index // 3, index % 3)
            grid.setColumnStretch(index % 3, 1)
        section.addLayout(grid)
        parent_layout.addWidget(section_frame, 1)

    def make_team_slot_combo(self, side, index):
        frame = QFrame()
        frame.setObjectName("teamSlotFrame")
        frame.setMinimumWidth(160)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setProperty("teamSide", side)
        frame.setProperty("teamSlotIndex", index)
        frame.installEventFilter(self)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(3, 1, 3, 1)
        layout.setSpacing(2)

        number_label = QLabel(f"{index + 1}.")
        number_label.setObjectName("teamSlotNumber")
        layout.addWidget(number_label)

        combo = LazyModelComboBox()
        combo.setObjectName("teamSlotCombo")
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setMaxVisibleItems(10)
        combo.setMinimumWidth(126)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.set_lazy_popup_model(self.pokemon_slot_dropdown_model)
        completer = QCompleter(self.pokemon_slot_completer_model, combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        combo.setCompleter(completer)
        combo.view().setMouseTracking(True)
        combo.view().setUniformItemSizes(True)
        combo.setProperty("teamSide", side)
        combo.setProperty("teamSlotIndex", index)
        combo.installEventFilter(self)
        combo._slot_frame = frame
        if completer.popup():
            completer.popup().setMouseTracking(True)
            completer.popup().setUniformItemSizes(True)
            completer.popup().setStyleSheet("""
                QListView::item:hover { background: #cfe8ff; color: #102a43; }
                QListView::item:selected { background: #bcdcff; color: #102a43; }
            """)
        combo.activated.connect(lambda _idx=0, s=side, slot=index: self.on_team_slot_changed(s, slot))
        completer.activated[str].connect(
            lambda text, s=side, slot=index: self.on_team_slot_completion(s, slot, text)
        )
        if combo.lineEdit():
            combo.lineEdit().setClearButtonEnabled(True)
            combo.lineEdit().setPlaceholderText("输入精灵名")
            combo.lineEdit().setProperty("teamSide", side)
            combo.lineEdit().setProperty("teamSlotIndex", index)
            combo.lineEdit().installEventFilter(self)
            combo.lineEdit().editingFinished.connect(lambda s=side, slot=index: self.on_team_slot_edited(s, slot))
        layout.addWidget(combo, 1)
        return frame, combo

    def eventFilter(self, obj, event):
        side = obj.property("teamSide") if hasattr(obj, "property") else None
        slot = obj.property("teamSlotIndex") if hasattr(obj, "property") else None
        if (
            side in {"attacker", "defender"}
            and slot is not None
            and event.type() == QEvent.MouseButtonPress
            and not self.refreshing_team_slots
            and self.selected_team_slot.get(str(side)) != int(slot)
        ):
            self.select_team_slot(str(side), int(slot))
        return super().eventFilter(obj, event)

    def restore_main_from_selected_slots(self):
        for side in ("attacker", "defender"):
            for index, key in enumerate(self.team_slots.get(side, [])):
                item = find_pokemon_by_key(self.pokemon, key)
                if item:
                    self.selected_team_slot[side] = index
                    combo = self.defender_combo if side == "defender" else self.attacker_combo
                    self.set_combo_to_item(combo, item)
                    break

    def refresh_team_buttons(self):
        self.refreshing_team_slots = True
        try:
            for side, combos in self.team_slot_combos.items():
                for index, combo in enumerate(combos):
                    item = find_pokemon_by_key(self.pokemon, self.team_slots[side][index])
                    combo.blockSignals(True)
                    combo.setCurrentIndex(0)
                    combo.setEditText(pvp_item_label(item) if item else "")
                    combo.setToolTip(pvp_item_label(item) if item else "空")
                    combo.blockSignals(False)
                    is_active = index == self.selected_team_slot[side]
                    combo.setProperty("active", is_active)
                    frame = getattr(combo, "_slot_frame", None)
                    if frame is not None:
                        frame.setProperty("active", is_active)
                        frame.style().unpolish(frame)
                        frame.style().polish(frame)
                    combo.style().unpolish(combo)
                    combo.style().polish(combo)
        finally:
            self.refreshing_team_slots = False

    def resolve_team_slot_text(self, combo):
        text = combo.currentText().strip()
        if not text or text == "空":
            return None
        normalized = text.split(". ", 1)[-1].strip()
        item = self.pokemon_slot_lookup.get(normalized)
        if item:
            return item
        item = self.pokemon_slot_lookup_folded.get(normalized.casefold())
        if item:
            return item
        for item in self.pokemon:
            label = pvp_item_label(item)
            if label == normalized or str(item.get("name") or "") == normalized:
                return item
        for item in self.pokemon:
            label = pvp_item_label(item)
            if normalized and (normalized in label or normalized in str(item.get("name") or "")):
                return item
        return None

    def team_slot_item_from_combo(self, combo):
        return self.resolve_team_slot_text(combo)

    def apply_team_slot_choice(self, side, index, item):
        if not getattr(self, "loading_team_preset", False):
            self.capture_current_side_build(side)
        self.selected_team_slot[side] = max(0, min(5, index))
        slot = self.selected_team_slot[side]
        old_key = self.team_slots[side][slot]
        new_key = pokemon_key(item) if item else None
        self.team_slots[side][slot] = new_key
        if old_key != new_key:
            self.team_member_builds[side][slot] = self.empty_team_member_build()
        combo = self.defender_combo if side == "defender" else self.attacker_combo
        if item:
            self.set_combo_to_item(combo, item)
        else:
            combo.blockSignals(True)
            combo.setCurrentIndex(-1)
            if combo.lineEdit():
                combo.lineEdit().clear()
            combo.blockSignals(False)
        save_pvp_team(self.team_slots)
        self.refresh_team_buttons()
        self.update_pvp_panels()

    def on_team_slot_changed(self, side, index):
        if self.refreshing_team_slots:
            return
        combo = self.team_slot_combos[side][index]
        item = self.team_slot_item_from_combo(combo)
        self.apply_team_slot_choice(side, index, item)

    def on_team_slot_completion(self, side, index, text):
        if self.refreshing_team_slots:
            return
        combo = self.team_slot_combos[side][index]
        combo.setEditText(str(text or ""))
        self.apply_team_slot_choice(side, index, self.team_slot_item_from_combo(combo))

    def on_team_slot_edited(self, side, index):
        if self.refreshing_team_slots:
            return
        combo = self.team_slot_combos[side][index]
        item = self.team_slot_item_from_combo(combo)
        if item or not combo.currentText().strip() or combo.currentText().strip() == "空":
            self.apply_team_slot_choice(side, index, item)
        else:
            self.refresh_team_buttons()

    def select_team_slot(self, side, index):
        if not getattr(self, "loading_team_preset", False):
            self.capture_current_side_build(side)
        self.selected_team_slot[side] = max(0, min(5, index))
        item = find_pokemon_by_key(self.pokemon, self.team_slots[side][self.selected_team_slot[side]])
        combo = self.defender_combo if side == "defender" else self.attacker_combo
        if item:
            self.set_combo_to_item(combo, item)
        else:
            combo.blockSignals(True)
            combo.setCurrentIndex(-1)
            if combo.lineEdit():
                combo.lineEdit().clear()
            combo.blockSignals(False)
        self.refresh_team_buttons()
        self.update_pvp_panels()

    def set_combo_to_item(self, combo, item):
        target_key = pokemon_key(item)
        for index in range(combo.count()):
            data = combo.itemData(index)
            if isinstance(data, dict) and pokemon_key(data) == target_key:
                combo.setCurrentIndex(index)
                return True
        return False

    def save_current_to_slot(self, side):
        combo = self.defender_combo if side == "defender" else self.attacker_combo
        item = self.current_data(combo, self.pokemon, pvp_item_label)
        if item:
            self.apply_team_slot_choice(side, self.selected_team_slot[side], item)

    def clear_selected_slot(self, side):
        self.apply_team_slot_choice(side, self.selected_team_slot[side], None)

    def on_skill_slot_changed(self, side, slot):
        self.update_skill_slot_info(side, slot)
        if side == "attacker":
            skill = self.current_data(self.skill_slot_combos[side][slot], self.skills, self.skill_label)
            if skill:
                self.set_combo_to_item(self.skill_combo, skill)
                self.update_type_multiplier_from_current_skill()
            else:
                self.skill_combo.blockSignals(True)
                self.skill_combo.setCurrentIndex(0)
                self.skill_combo.blockSignals(False)
        self.capture_current_side_build(side)
        self.update_matchup_panel()
        self.update_kill_lines()

    def sync_primary_attack_skill_combo(self):
        if not hasattr(self, "skill_combo"):
            return
        for combo in self.skill_slot_combos.get("attacker", []):
            skill = self.current_data(combo, self.skills, self.skill_label)
            if skill:
                self.set_skill_combo_to_key(self.skill_combo, self.skill_unique_key(skill))
                return
        self.set_skill_combo_to_key(self.skill_combo, None)

    def update_skill_slot_info(self, side, slot):
        labels = self.skill_slot_info_labels.get(side, [])
        combos = self.skill_slot_combos.get(side, [])
        if slot >= len(labels) or slot >= len(combos):
            return
        skill = self.current_data(combos[slot], self.skills, self.skill_label)
        if not skill:
            labels[slot].clear()
            labels[slot].setToolTip("")
            return
        creature = self.effective_creature(side)
        opponent_side = "defender" if side == "attacker" else "attacker"
        opponent = self.effective_creature(opponent_side)
        skill = self.skill_with_battle_preview(side, creature, opponent, skill)
        values = []
        if skill.get("_expected_damage") is not None:
            values.append(f"预计伤害 {skill.get('_expected_damage')}")
        if skill.get("_display_power") is not None:
            values.append(f"威力 {skill.get('_display_power')}")
        text = "\n".join(values)
        labels[slot].setText(text)
        tooltip = []
        if skill.get("_expected_damage") is not None:
            tooltip.append(f"预计伤害：{skill.get('_expected_damage')}")
        if skill.get("_display_power") is not None:
            tooltip.append(f"显示威力：{skill.get('_display_power')}")
        labels[slot].setToolTip("\n".join(tooltip))

    def update_type_multiplier_from_current_skill(self):
        defender = self.effective_creature("defender")
        skill = self.current_data(self.skill_combo, self.skills, self.skill_label)
        if not defender or not skill:
            self.skill_relation_label.setText("克制关系：无")
            return
        multiplier = type_multiplier_for(skill.get("attribute"), defender.get("attributes") or [])
        self.type_multiplier.blockSignals(True)
        self.type_multiplier.setValue(multiplier)
        self.type_multiplier.blockSignals(False)
        burn_multiplier = type_multiplier_for("火", defender.get("attributes") or [])
        self.burn_type_multiplier.blockSignals(True)
        self.burn_type_multiplier.setValue(burn_multiplier)
        self.burn_type_multiplier.blockSignals(False)
        defender_attrs = "/".join(defender.get("attributes") or [])
        relation = self.type_relation_text(multiplier)
        self.skill_relation_label.setText(
            f"克制关系：{skill.get('attribute')} → {defender_attrs or '无'} = ×{multiplier:g}（{relation}）"
        )

    def type_relation_text(self, multiplier):
        if multiplier >= 3:
            return "双重克制"
        if multiplier > 1:
            return "克制"
        if multiplier <= 0.25:
            return "双重抵抗"
        if multiplier < 1:
            return "抵抗"
        return "普通"

    def update_pvp_panels(self):
        attacker = self.current_data(self.attacker_combo, self.pokemon, pvp_item_label)
        defender = self.current_data(self.defender_combo, self.pokemon, pvp_item_label)
        self.update_main_card("attacker", attacker)
        self.update_main_card("defender", defender)
        self.refresh_skill_choices("attacker", attacker)
        self.refresh_skill_choices("defender", defender)
        self.update_stat_compare(attacker, defender)
        self.update_type_multiplier_from_current_skill()
        self.update_matchup_panel()
        self.update_kill_lines()
        self.update_wish_impact_preview()

    def refresh_skill_choices(self, side, creature):
        opponent_side = "defender" if side == "attacker" else "attacker"
        opponent = self.effective_creature(opponent_side)
        signature = (
            pokemon_key(creature) if creature else "",
            tuple(self.selected_attributes_for_side(side, creature or {})),
            pokemon_key(opponent) if opponent else "",
            tuple(self.selected_attributes_for_side(opponent_side, opponent or {})),
            repr(self.stat_config_for_side(side)),
            repr(self.stat_config_for_side(opponent_side)),
            self.auto_stab.isChecked() if hasattr(self, "auto_stab") else True,
            round(self.attack_modifier.value(), 3) if hasattr(self, "attack_modifier") else 0,
            round(self.defense_modifier.value(), 3) if hasattr(self, "defense_modifier") else 0,
            round(self.power_bonus.value(), 3) if hasattr(self, "power_bonus") else 0,
            round(self.damage_modifier.value(), 3) if hasattr(self, "damage_modifier") else 0,
            round(self.reduction_modifier.value(), 3) if hasattr(self, "reduction_modifier") else 0,
            self.hit_count.value() if hasattr(self, "hit_count") else 1,
        )
        if self.current_skill_choice_keys.get(side) == signature:
            self.restore_skills_for_selected_slot(side)
            for slot, _combo in enumerate(self.skill_slot_combos.get(side, [])):
                self.update_skill_slot_info(side, slot)
            if side == "attacker":
                self.sync_primary_attack_skill_combo()
            return
        self.current_skill_choice_keys[side] = signature
        source_rows = self.creature_skill_rows(creature)
        available = [self.normalize_rocopvp_skill(row) for row in source_rows]
        available = [skill for skill in available if skill]
        available.sort(key=lambda skill: self.skill_source_rank(creature, skill))
        for combo in self.skill_slot_combos.get(side, []):
            self.set_combo_items(combo, available, self.skill_label)
        self.restore_skills_for_selected_slot(side)
        for slot, _combo in enumerate(self.skill_slot_combos.get(side, [])):
            self.update_skill_slot_info(side, slot)
        if side == "attacker":
            self.set_combo_items(self.skill_combo, available, self.skill_label)
            self.sync_primary_attack_skill_combo()

    def update_main_card(self, side, creature):
        name_label = self.main_name_labels.get(side)
        meta_label = self.main_meta_labels.get(side)
        attr_layout = self.main_attr_layouts.get(side)
        if name_label is None or meta_label is None or attr_layout is None:
            return
        self.clear_layout(attr_layout)
        self.sync_attribute_editors(side, creature)
        self.restore_current_team_build(side, creature)
        if not creature:
            name_label.setText("未选择")
            meta_label.setText("")
            return
        name_label.setText(pvp_item_label(creature))
        for attr in self.selected_attributes_for_side(side, creature):
            attr_layout.addWidget(self.make_pvp_icon_label("attributes", attr, 24))
        attr_layout.addStretch(1)
        stats = derived_stats(creature, self.stat_config_for_side(side))
        meta_label.setText(str(creature.get("abilities_text") or ""))
        if side in self.hp_percent_bars:
            self.hp_percent_bars[side].setValue(self.hp_percent_spins[side].value())
        meta_label.setToolTip(meta_label.text())

    def update_stat_compare(self, attacker, defender):
        self.stat_compare_tree.clear()
        if hasattr(self, "stat_compare_widgets"):
            for side_widgets in self.stat_compare_widgets.values():
                for widgets in side_widgets.values():
                    widgets["value"].setText("-")
                    widgets["bar"].setValue(0)
        if not attacker or not defender:
            return
        attacker_stats = derived_stats(attacker, self.stat_config_for_side("attacker"))
        defender_stats = derived_stats(defender, self.stat_config_for_side("defender"))
        max_bar = max(650, *(int(attacker_stats.get(key, 0)) for key, _label in self.stat_rows()), *(int(defender_stats.get(key, 0)) for key, _label in self.stat_rows()))
        for side, stats in (("attacker", attacker_stats), ("defender", defender_stats)):
            for key, _label in self.stat_rows():
                widgets = getattr(self, "stat_compare_widgets", {}).get(side, {}).get(key)
                if not widgets:
                    continue
                value = int(stats.get(key, 0))
                widgets["value"].setText(str(value))
                widgets["bar"].setRange(0, max_bar)
                widgets["bar"].setValue(value)
        for key, label in self.stat_rows():
            attack_value = attacker_stats.get(key, 0)
            defend_value = defender_stats.get(key, 0)
            item = QTreeWidgetItem([
                label,
                str(attack_value),
                str(defend_value),
                f"{attack_value - defend_value:+}",
            ])
            icon_path = self.pvp_icon_path("stats", self.stat_icon_names().get(key))
            if icon_path:
                item.setIcon(0, QIcon(str(icon_path)))
            self.stat_compare_tree.addTopLevelItem(item)
        for col in range(4):
            self.stat_compare_tree.resizeColumnToContents(col)

    def current_data(self, combo, items, label_func):
        data = combo.currentData()
        text = combo.currentText().strip()
        if isinstance(data, dict):
            label = label_func(data)
            name = str(data.get("name") or "")
            if not text or label == text or name == text or text in label:
                return data
        for item in items:
            if label_func(item) == text or str(item.get("name") or "") == text:
                return item
        for item in items:
            if text and text in label_func(item):
                return item
        return None

    def calculate(self):
        attacker = self.effective_creature("attacker")
        defender = self.effective_creature("defender")
        skill = self.current_data(self.skill_combo, self.skills, self.skill_label)
        if not attacker or not defender or not skill:
            self.result_label.setText("请选择攻击方、防守方和技能。")
            return

        result = calculate_pvp_damage(
            attacker,
            defender,
            skill,
            {
                "type_multiplier": self.type_multiplier.value(),
                "auto_stab": self.auto_stab.isChecked(),
                "attack_modifier_percent": self.attack_modifier.value(),
                "defense_modifier_percent": self.defense_modifier.value(),
                "power_bonus": self.power_bonus.value(),
                "damage_modifier_percent": self.damage_modifier.value(),
                "reduction_percent": self.reduction_modifier.value(),
                "hit_count": self.hit_count.value(),
                "attacker_stat_config": self.stat_config_for_side("attacker"),
                "defender_stat_config": self.stat_config_for_side("defender"),
            },
            self.formula,
        )
        self.detail_tree.clear()
        if not result.get("ok"):
            self.result_label.setText(result.get("message", "计算失败"))
            return

        status_options = {
            "burn_type_multiplier": self.burn_type_multiplier.value(),
            "defender_stat_config": self.stat_config_for_side("defender"),
            **{
                f"{key}_stacks": spin.value()
                for key, spin in self.status_spins.items()
                if key != "starfall"
            },
        }
        status_result = calculate_status_effects(defender, status_options, self.formula)
        starfall_result = self.calculate_starfall_damage(attacker, defender)
        status_damage = status_result.get("total_damage", 0) + starfall_result.get("damage", 0)
        total_damage = result["damage"] + status_damage

        self.result_label.setText(
            f"{pvp_item_label(attacker)} 使用 {skill.get('name')} 攻击 {pvp_item_label(defender)}："
            f"直伤 {result['damage']}，状态 {status_damage}，总伤害 {total_damage}，"
            f"约占生命 {total_damage / max(1, status_result.get('defender_hp', 1)) * 100:.1f}%"
        )
        details = result.get("details", {})
        rows = [
            ("技能分类", details.get("category")),
            ("攻击使用", f"{details.get('attack_stat_name')} {details.get('attack_stat'):.0f}"),
            ("防御使用", f"{details.get('defense_stat_name')} {details.get('defense_stat'):.0f}"),
            ("防御方生命", f"{status_result.get('defender_hp', 0):.0f}"),
            ("技能威力", f"{details.get('skill_power'):.0f}"),
            ("有效威力", f"{details.get('effective_power'):.0f}"),
            ("显示威力", f"{details.get('display_power'):.0f}"),
            ("本系倍率", f"{details.get('stab_multiplier'):.2f}"),
            ("属性倍率", f"{details.get('type_multiplier'):.2f}"),
            ("攻防增减倍率", f"{details.get('ability_multiplier'):.3f}"),
            ("减伤倍率", f"{details.get('reduction_modifier'):.2f}"),
            ("独立伤害倍率", f"{details.get('damage_modifier'):.2f}"),
            ("RocoPVP常数", f"{details.get('roco_constant'):.6f}"),
            ("单段伤害", result.get("single_damage")),
            ("连击次数", result.get("hit_count")),
            ("直伤合计", result.get("damage")),
        ]
        for name, value in rows:
            self.detail_tree.addTopLevelItem(QTreeWidgetItem([str(name), str(value)]))
        for row in status_result.get("rows", []):
            label = f"{row['label']} x{row['stacks']}"
            if row.get("kind") == "threshold":
                value = f"冻结阈值 {row['value']} HP"
            elif row.get("kind") == "drain":
                value = f"伤害 {row['value']} / 回复 {row['value']}"
            else:
                value = f"伤害 {row['value']}"
            self.detail_tree.addTopLevelItem(QTreeWidgetItem([label, value]))
        if starfall_result.get("stacks", 0) > 0:
            self.detail_tree.addTopLevelItem(QTreeWidgetItem([
                f"星陨印记 x{starfall_result.get('stacks')}",
                (
                    f"威力 {starfall_result.get('power', 0)} / "
                    f"幻系倍率 ×{starfall_result.get('type_multiplier', 1.0):g} / "
                    f"伤害 {starfall_result.get('damage', 0)}"
                ),
            ]))


def _manual_route_marker_at(view, event):
    app = getattr(view, "app", None)
    if app is None:
        return None
    scene_pos = view.mapToScene(event.pos())
    tolerance = max(24, getattr(app, "marker_icon_width", BASE_ICON_WIDTH) * 0.55)
    best_marker = None
    best_distance = tolerance * tolerance
    for marker in app.visible_markers():
        dx = scene_pos.x() - marker["x"]
        dy = scene_pos.y() - marker["y"]
        distance = dx * dx + dy * dy
        if distance < best_distance:
            best_distance = distance
            best_marker = marker
    return best_marker


_original_mapview_mouse_release = MapView.mouseReleaseEvent


def _mapview_mouse_release_with_manual_route(self, event):
    if event.button() == Qt.LeftButton and getattr(self.app, "manual_route_mode", False):
        press_pos = getattr(self, "press_pos", event.pos())
        delta = event.pos() - press_pos
        if abs(delta.x()) <= CLICK_DRAG_THRESHOLD and abs(delta.y()) <= CLICK_DRAG_THRESHOLD:
            scene_pos = self.mapToScene(event.pos())
            QGraphicsView.mouseReleaseEvent(self, event)
            self.app.add_manual_route_point(scene_pos)
            self.press_marker = None
            self.press_pos = None
            self.viewport().setCursor(Qt.OpenHandCursor)
            event.accept()
            return
    _original_mapview_mouse_release(self, event)


MapView.mouseReleaseEvent = _mapview_mouse_release_with_manual_route


class RoutePreviewView(QGraphicsView):
    def __init__(self, scene, owner=None):
        super().__init__(scene)
        self.owner = owner
        self.current_scale = 0.34
        self.initialized_view = False
        self.press_pos = None
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        next_scale = max(0.08, min(2.4, self.current_scale * factor))
        factor = next_scale / self.current_scale
        self.current_scale = next_scale
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        owner = self.owner
        if event.button() == Qt.LeftButton and owner is not None and getattr(owner, "manual_route_mode", False):
            press_pos = self.press_pos or event.pos()
            delta = event.pos() - press_pos
            if abs(delta.x()) <= CLICK_DRAG_THRESHOLD and abs(delta.y()) <= CLICK_DRAG_THRESHOLD:
                scene_pos = self.mapToScene(event.pos())
                QGraphicsView.mouseReleaseEvent(self, event)
                owner.add_manual_route_point(scene_pos)
                self.press_pos = None
                event.accept()
                return
        self.press_pos = None
        super().mouseReleaseEvent(event)

    def set_initial_focus(self, x, y):
        if not self.initialized_view:
            transform = QTransform()
            transform.scale(self.current_scale, self.current_scale)
            self.setTransform(transform)
            self.initialized_view = True
        self.centerOn(x, y)


class RouteNavigationDialog(QDialog):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def keyPressEvent(self, event):
        if getattr(self.owner, "route_dialog_pinned", False):
            if event.key() == Qt.Key_F12:
                self.owner.toggle_route_dialog_pin()
                event.accept()
                return
            if event.key() == Qt.Key_F9:
                self.owner.focus_current_player_position()
                event.accept()
                return
            if event.key() == Qt.Key_F10:
                self.owner.focus_route_start_marker()
                event.accept()
                return
            if event.key() == Qt.Key_F11:
                self.owner.toggle_route_list_panel()
                event.accept()
                return
        super().keyPressEvent(event)


class MinimapSelectionCircle(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.radius = 96
        self.drag_offset = None
        self.locked_for_game = False
        self.setWindowTitle("小地图识别区域")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setMouseTracking(True)
        self.resize(self.radius * 2 + 28, self.radius * 2 + 28)
        screen = QApplication.primaryScreen()
        if screen is not None:
            center = screen.availableGeometry().center()
            self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        center_x = self.width() / 2
        center_y = self.height() / 2
        painter.setBrush(QBrush(QColor(255, 120, 0, 36)))
        painter.setPen(QPen(QColor("#ff7800"), 4))
        painter.drawEllipse(
            int(center_x - self.radius),
            int(center_y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawText(self.rect(), Qt.AlignCenter, "拖动定位\n滚轮缩放")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        if event.button() == Qt.RightButton:
            self.close()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            self.move(event.globalPos() - self.drag_offset)
            self.owner.update_minimap_circle_region(self.capture_region())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        self.owner.update_minimap_circle_region(self.capture_region())
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        old_center = self.frameGeometry().center()
        delta = 10 if event.angleDelta().y() > 0 else -10
        self.radius = max(36, min(240, self.radius + delta))
        self.resize(self.radius * 2 + 28, self.radius * 2 + 28)
        self.move(old_center.x() - self.width() // 2, old_center.y() - self.height() // 2)
        self.owner.update_minimap_circle_region(self.capture_region())
        self.update()

    def capture_region(self):
        geometry = self.frameGeometry()
        return {
            "x": geometry.x() + geometry.width() // 2 - self.radius,
            "y": geometry.y() + geometry.height() // 2 - self.radius,
            "size": self.radius * 2,
        }

    def set_locked_for_game(self, locked):
        self.locked_for_game = locked
        transparent_flag = getattr(Qt, "WindowTransparentForInput", None)
        flags = self.windowFlags()
        if transparent_flag is not None:
            if locked:
                flags |= transparent_flag
            else:
                flags &= ~transparent_flag
        self.setWindowFlags(flags | Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.show()


class RocoResourceMapQt(QMainWindow):
    def __init__(self):
        super().__init__()
        QApplication.instance().installEventFilter(self)
        self.setWindowTitle("洛克王国多功能辅助工具")
        self.resize(1320, 840)
        self.setMinimumSize(960, 620)
        self.tearing_down = False

        self.meta, self.markers = load_markers()
        self.markers_by_uid = {marker["uid"]: marker for marker in self.markers}
        self.current_layer = "G"
        self.layer_buttons = {}
        self.layer_pixmap_cache = {}
        self.resource_types = self.build_resource_types()
        self.visible_types = set()
        migrate_legacy_account_state()
        self.account_registry = load_account_registry()
        self.account_id = safe_account_id(self.account_registry.get("currentAccountId"))
        self.account_name = account_display_name(account_by_id(self.account_registry, self.account_id))
        save_account_registry(self.account_registry)
        self.updating_account_combo = False
        self.dimmed_uids = load_state(self.markers, self.account_id)
        self.notes_payload = load_notes(self.account_id)
        self.route_state = load_route_state(self.account_id)
        self.route_cache = load_route_cache()
        self.completed_route_uids = set(self.route_state.get("completedMarkers", []))
        self.marker_details_payload = load_marker_details()
        self.marker_icon_width = int(self.meta.get("iconWidth") or BASE_ICON_WIDTH)
        anchor_scale = self.marker_icon_width / BASE_ICON_WIDTH
        self.icon_anchor = (ICON_ANCHOR[0] * anchor_scale, ICON_ANCHOR[1] * anchor_scale)

        self.icon_pixmaps = {}
        self.sidebar_icons = {}
        self.icon_hit_sizes = {}
        self._visible_markers_cache_signature = None
        self._visible_markers_cache = []
        self.marker_hit_cycle_key = None
        self.marker_hit_cycle_index = 0
        self.base_pixmap = None
        self.map_item = None
        self.marker_tile_items = []
        self.tree_items_by_type = {}
        self.updating_tree = False
        self.detail_windows = []
        self.submission_windows = []
        self.egg_query_dialog = None
        self.pvp_damage_dialog = None
        self.search_mode = False
        self.highlight_item = None
        self.route_markers = []
        self.current_route_index = 0
        self.route_path_item = None
        self.route_dialog = None
        self.route_dialog_pinned = False
        self.route_dialog_normal_widgets = []
        self.route_dialog_pin_widgets = []
        self.route_dialog_normal_layouts = []
        self.route_dialog_pin_label = None
        self.route_dialog_route_list_button = None
        self.route_dialog_route_list_visible = True
        self.route_dialog_side_panel = None
        self.route_dialog_pin_bar_widgets = []
        self.route_dialog_unpinned_size = None
        self.minimap_follow_button = None
        self.minimap_circle_lock_button = None
        self.route_dialog_pin_button = None
        self.route_dialog_tree = None
        self.route_dialog_status_label = None
        self.route_arrow_item = None
        self.route_helper_marker_items = []
        self.manual_route_mode = False
        self.manual_route_button = None
        self.route_preview_scene = None
        self.route_preview_view = None
        self.route_preview_map_item = None
        self.route_preview_path_item = None
        self.route_preview_arrow_item = None
        self.route_preview_current_item = None
        self.route_preview_player_item = None
        self.route_preview_marker_items = []
        self.route_preview_marker_signature = None
        self.route_preview_icon_cache = {}
        self.route_preview_opacity_slider = None
        self.route_transition_hints = {}
        self.route_transition_cache = {}
        self.route_nearest_teleport_cache = {}
        self.route_teleport_marker_cache = None
        self.route_background_job = None
        self.route_background_timer = QTimer(self)
        self.route_background_timer.setInterval(ROUTE_BACKGROUND_INTERVAL_MS)
        self.route_background_timer.timeout.connect(self.run_route_background_step)
        self.route_auto_complete_candidate_uid = None
        self.route_auto_complete_candidate_hits = 0
        self.route_auto_complete_candidate_started_at = 0.0
        self.route_auto_complete_last_seen_at = 0.0
        self.route_preview_player_display_pos = None
        self.route_preview_player_target_pos = None
        self.route_preview_player_motion = []
        self.route_preview_player_motion_started_at = 0.0
        self.route_preview_player_last_update_at = 0.0
        self.route_preview_player_angle = 38.0
        self.route_preview_player_target_angle = 38.0
        self.minimap_follow_enabled = False
        self.minimap_circle = None
        self.minimap_circle_locked = False
        self.minimap_circle_region = None
        self.minimap_match_map_image = None
        self.minimap_match_scale_x = 1.0
        self.minimap_match_scale_y = 1.0
        self.minimap_last_world_pos = None
        self.minimap_calibrated = False
        self.minimap_reference_image = None
        self.minimap_reference_player_local = None
        self.minimap_reference_world_pos = None
        self.minimap_previous_image = None
        self.minimap_previous_player_local = None
        self.minimap_tracking_failures = 0
        self.minimap_world_pixels_per_minimap_pixel = MINIMAP_WORLD_PIXELS_PER_MINIMAP_PIXEL
        self.sift_ready = False
        self.sift_method = None
        self.sift_ref_image = None
        self.sift_ref_scale = 1.0
        self.sift_keypoints = None
        self.sift_descriptors = None
        self.sift_matcher = None
        self.minimap_follow_status_label = None
        self.minimap_follow_timer = QTimer(self)
        self.minimap_follow_timer.setInterval(33)
        self.minimap_follow_timer.timeout.connect(self.update_minimap_follow)
        self.marker_rebuild_timer = QTimer(self)
        self.marker_rebuild_timer.setSingleShot(True)
        self.marker_rebuild_timer.setInterval(35)
        self.marker_rebuild_timer.timeout.connect(self.apply_deferred_marker_rebuild)
        self.initial_fit_done = False
        self.pending_save = QTimer(self)
        self.pending_save.setSingleShot(True)
        self.pending_save.setInterval(250)
        self.pending_save.timeout.connect(self.save_state)
        self.route_preview_player_animation_timer = QTimer(self)
        self.route_preview_player_animation_timer.setInterval(6)
        self.route_preview_player_animation_timer.timeout.connect(self.animate_route_preview_player)

        self.build_ui()
        self.build_scene()
        try:
            self.restore_route_from_state()
        except Exception as error:
            self.route_markers = []
            self.current_route_index = 0
            self.route_state = {"version": 1, "completedMarkers": [], "routeMarkers": []}
            try:
                self.save_route_state()
            except Exception:
                pass
            print(f"Route state disabled after load error: {error}")
        self.update_status()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.initial_fit_done:
            self.initial_fit_done = True
            QTimer.singleShot(0, self.fit_to_window)

    def closeEvent(self, event):
        self.tearing_down = True
        super().closeEvent(event)

    def refresh_account_combo(self):
        combo = getattr(self, "account_combo", None)
        if combo is None:
            return
        self.updating_account_combo = True
        combo.clear()
        current_index = 0
        for index, account in enumerate(self.account_registry.get("accounts", [])):
            account_id = safe_account_id(account.get("id"))
            combo.addItem(account_display_name(account), account_id)
            if account_id == self.account_id:
                current_index = index
        combo.setCurrentIndex(current_index)
        self.updating_account_combo = False

    def on_account_combo_changed(self, index):
        if self.updating_account_combo or index < 0:
            return
        account_id = self.account_combo.itemData(index)
        if account_id:
            self.switch_account(account_id)

    def account_name_exists(self, name, exclude_id=None):
        target = name.strip().casefold()
        exclude_id = safe_account_id(exclude_id) if exclude_id else None
        for account in self.account_registry.get("accounts", []):
            if exclude_id and safe_account_id(account.get("id")) == exclude_id:
                continue
            if account_display_name(account).casefold() == target:
                return True
        return False

    def save_account_registry_state(self):
        self.account_registry["currentAccountId"] = self.account_id
        save_account_registry(self.account_registry)

    def save_current_account_state(self):
        if getattr(self, "pending_save", None) is not None and self.pending_save.isActive():
            self.pending_save.stop()
        self.save_state()
        self.save_route_state()
        self.save_notes()

    def add_account(self):
        name, ok = QInputDialog.getText(self, "新增账号", "账号名称：")
        if not ok:
            return
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "新增账号", "账号名称不能为空。")
            return
        if self.account_name_exists(name):
            QMessageBox.warning(self, "新增账号", "已经有同名账号。")
            return
        account_id = make_unique_account_id(account.get("id") for account in self.account_registry.get("accounts", []))
        self.account_registry.setdefault("accounts", []).append({
            "id": account_id,
            "name": name,
            "createdAt": datetime.now().isoformat(timespec="seconds"),
        })
        self.switch_account(account_id)

    def rename_account(self):
        name, ok = QInputDialog.getText(self, "账号改名", "账号名称：", text=self.account_name)
        if not ok:
            return
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "账号改名", "账号名称不能为空。")
            return
        if self.account_name_exists(name, exclude_id=self.account_id):
            QMessageBox.warning(self, "账号改名", "已经有同名账号。")
            return
        for account in self.account_registry.get("accounts", []):
            if safe_account_id(account.get("id")) == self.account_id:
                account["name"] = name
                break
        self.account_name = name
        self.save_account_registry_state()
        self.refresh_account_combo()
        self.update_status()

    def delete_account(self):
        if self.account_id == DEFAULT_ACCOUNT_ID:
            QMessageBox.information(self, "删除账号", "默认账号不能删除。")
            return
        accounts = [
            account
            for account in self.account_registry.get("accounts", [])
            if safe_account_id(account.get("id")) != self.account_id
        ]
        if not accounts:
            QMessageBox.information(self, "删除账号", "至少需要保留一个账号。")
            return
        reply = QMessageBox.question(
            self,
            "删除账号",
            f"确定删除账号「{self.account_name}」及其采集、路线、备注记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        deleted_account_id = self.account_id
        fallback_account_id = safe_account_id(accounts[0].get("id"))
        self.close_account_bound_windows()
        if self.route_background_timer.isActive():
            self.route_background_timer.stop()
        self.route_background_job = None

        self.account_registry["accounts"] = accounts
        self.account_id = fallback_account_id
        self.account_name = account_display_name(account_by_id(self.account_registry, fallback_account_id))
        self.account_registry["currentAccountId"] = fallback_account_id
        self.save_account_registry_state()
        shutil.rmtree(account_data_dir(deleted_account_id), ignore_errors=True)

        self.dimmed_uids = load_state(self.markers, self.account_id)
        self.notes_payload = load_notes(self.account_id)
        self.route_state = load_route_state(self.account_id)
        self.completed_route_uids = set(self.route_state.get("completedMarkers", []))
        self.route_auto_complete_candidate_uid = None
        self.route_auto_complete_candidate_hits = 0
        self.route_auto_complete_candidate_started_at = 0.0
        self.restore_route_from_state()
        self.rebuild_marker_tiles()
        self.refresh_route_overlay()
        self.refresh_account_combo()
        self.update_status()

    def close_account_bound_windows(self):
        for dialog in list(getattr(self, "detail_windows", [])):
            dialog.close()
        QApplication.processEvents()

    def switch_account(self, account_id):
        account_id = safe_account_id(account_id)
        if account_id == self.account_id:
            return
        if account_by_id(self.account_registry, account_id).get("id") != account_id:
            return
        self.save_current_account_state()
        self.close_account_bound_windows()
        if self.route_background_timer.isActive():
            self.route_background_timer.stop()
        self.route_background_job = None

        self.account_id = account_id
        self.account_name = account_display_name(account_by_id(self.account_registry, account_id))
        self.account_registry["currentAccountId"] = account_id
        self.save_account_registry_state()

        self.dimmed_uids = load_state(self.markers, self.account_id)
        self.notes_payload = load_notes(self.account_id)
        self.route_state = load_route_state(self.account_id)
        self.completed_route_uids = set(self.route_state.get("completedMarkers", []))
        self.route_auto_complete_candidate_uid = None
        self.route_auto_complete_candidate_hits = 0
        self.route_auto_complete_candidate_started_at = 0.0
        self.restore_route_from_state()
        self.rebuild_marker_tiles()
        self.refresh_route_overlay()
        self.refresh_account_combo()
        self.update_status()

    def build_resource_types(self):
        resource_types = OrderedDict()
        for marker in self.markers:
            mark_type = marker["mark_type"]
            if mark_type not in resource_types:
                resource_types[mark_type] = {
                    "name": marker["name"],
                    "group": marker["group"],
                    "count": 0,
                    "count_by_layer": {},
                    "icon": marker["icon"],
                }
            resource_types[mark_type]["count"] += 1
            layer = marker.get("layer", "G")
            layer_counts = resource_types[mark_type]["count_by_layer"]
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        return resource_types

    def resource_type_count_for_layer(self, info, layer=None):
        layer = self.current_layer if layer is None else normalize_map_layer(layer)
        return info.get("count_by_layer", {}).get(layer, 0)

    def marker_matches_current_layer(self, marker):
        return marker.get("layer", "G") == self.current_layer

    def route_point_matches_current_layer(self, marker):
        return self.marker_matches_current_layer(marker) and (
            is_manual_route_point(marker) or marker.get("mark_type") in self.visible_types
        )

    def route_point_completed(self, marker):
        uid = route_point_uid(marker)
        if uid in self.completed_route_uids:
            return True
        return not is_manual_route_point(marker) and uid in self.dimmed_uids

    def route_point_by_uid(self, uid):
        uid = str(uid or "")
        for marker in self.route_markers:
            if route_point_uid(marker) == uid:
                return marker
        return self.markers_by_uid.get(uid)

    def create_manual_route_point(self, x, y, title=None, uid=None, layer=None):
        layer = normalize_map_layer(layer or self.current_layer)
        title = (title or "").strip() or f"路径点 {len(self.route_markers) + 1}"
        return {
            "uid": uid or f"{MANUAL_ROUTE_UID_PREFIX}{uuid.uuid4().hex[:16]}",
            "routePointKind": "manual",
            "group": MANUAL_ROUTE_GROUP,
            "category": MANUAL_ROUTE_GROUP,
            "mark_type": MANUAL_ROUTE_MARK_TYPE,
            "name": "路径点",
            "title": title,
            "label": title,
            "layer": layer,
            "raw_layer": layer,
            "x": float(x),
            "y": float(y),
        }

    def add_manual_route_point(self, scene_pos):
        if self.base_pixmap is None:
            return
        x = max(0.0, min(float(scene_pos.x()), float(self.base_pixmap.width())))
        y = max(0.0, min(float(scene_pos.y()), float(self.base_pixmap.height())))
        nearby = self.hit_test_marker(scene_pos)
        title = self.marker_title(nearby) if nearby is not None else None
        point = self.create_manual_route_point(x, y, title=title)
        self.route_markers.append(point)
        if len(self.route_markers) == 1:
            self.current_route_index = 0
        self.refresh_route_tree()
        self.render_route_path()
        self.update_status()

    def active_map_path(self):
        return map_path_for_layer(self.current_layer)

    def sift_cache_path(self):
        cache_name = "wiki_map_sift_cache.npz"
        if self.current_layer == "G":
            if SIFT_CACHE_PATH.exists():
                return SIFT_CACHE_PATH
        else:
            cache_name = f"wiki_map_sift_cache_{self.current_layer}.npz"
            static_cache = data_path(cache_name)
            if static_cache.exists():
                return static_cache
        return user_cache_path(cache_name)

    def load_layer_pixmap(self, layer):
        layer = normalize_map_layer(layer)
        if layer not in self.layer_pixmap_cache:
            self.layer_pixmap_cache[layer] = QPixmap(str(map_path_for_layer(layer)))
        return self.layer_pixmap_cache[layer]

    def update_layer_buttons(self):
        for layer, button in self.layer_buttons.items():
            button.blockSignals(True)
            button.setChecked(layer == self.current_layer)
            button.setEnabled(map_path_for_layer(layer).exists())
            button.blockSignals(False)

    def switch_map_layer(self, layer, center_on=None):
        layer = normalize_map_layer(layer)
        path = map_path_for_layer(layer)
        if not path.exists():
            QMessageBox.warning(self, "地图图层", f"{map_layer_label(layer)} 底图还没有下载：{path}")
            self.update_layer_buttons()
            return False

        old_center = None
        if center_on is None and hasattr(self, "view") and self.view is not None:
            old_center = self.view.mapToScene(self.view.viewport().rect().center())

        self.current_layer = layer
        pixmap = self.load_layer_pixmap(layer)
        if pixmap.isNull():
            QMessageBox.warning(self, "地图图层", f"{map_layer_label(layer)} 底图无法读取：{path}")
            self.update_layer_buttons()
            return False

        self.base_pixmap = pixmap
        if self.map_item is not None:
            self.map_item.setPixmap(pixmap)
        if hasattr(self, "scene"):
            self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())

        self.minimap_match_map_image = None
        self.sift_ready = False
        self.route_teleport_marker_cache = None
        self.route_transition_cache = {}
        self.route_nearest_teleport_cache = {}
        self.route_preview_marker_signature = None
        self.update_layer_buttons()
        if not self.search_mode:
            self.populate_filter_tree()
        self.clear_highlight()
        self.update_route_preview_map()
        self.request_marker_rebuild()

        if center_on is not None:
            self.view.centerOn(center_on[0], center_on[1])
        elif old_center is not None:
            self.view.centerOn(old_center)
        self.update_status()
        return True

    def build_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        sidebar = QWidget()
        sidebar.setMinimumWidth(278)
        sidebar.setMaximumWidth(340)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 8, 10)
        sidebar_layout.setSpacing(8)

        brand = QLabel("洛克王国")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet("font-size: 34px; font-weight: 900; color: #353331; letter-spacing: 0px;")
        sidebar_layout.addWidget(brand)
        subtitle = QLabel("洛克王国世界互动地图")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; font-weight: 700; color: #3d3830;")
        sidebar_layout.addWidget(subtitle)

        account_row = QHBoxLayout()
        account_row.addWidget(QLabel("账号"))
        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self.on_account_combo_changed)
        account_row.addWidget(self.account_combo, 1)
        add_account_button = QPushButton("新增")
        add_account_button.clicked.connect(self.add_account)
        rename_account_button = QPushButton("改名")
        rename_account_button.clicked.connect(self.rename_account)
        delete_account_button = QPushButton("删除")
        delete_account_button.clicked.connect(self.delete_account)
        account_row.addWidget(add_account_button)
        account_row.addWidget(rename_account_button)
        account_row.addWidget(delete_account_button)
        sidebar_layout.addLayout(account_row)
        self.refresh_account_combo()

        search_row = QHBoxLayout()
        clear_search = QPushButton("X")
        clear_search.setFixedWidth(38)
        clear_search.setStyleSheet("background: #6fa6a1; color: white; padding: 7px; border: none;")
        clear_search.clicked.connect(self.clear_search)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索标注点标题及内容")
        self.search_input.returnPressed.connect(self.run_search)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.setStyleSheet("background: white; border: 1px solid #6fa6a1; padding: 8px;")
        search_button = QPushButton("搜索")
        search_button.setStyleSheet("background: #6fa6a1; color: white; padding: 8px; border: none;")
        search_button.clicked.connect(self.run_search)
        search_row.addWidget(clear_search)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(search_button)
        sidebar_layout.addLayout(search_row)

        title = QLabel("资源")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        sidebar_layout.addWidget(title)
        self.filter_status = QLabel()
        self.filter_status.setStyleSheet("color: #657286;")
        sidebar_layout.addWidget(self.filter_status)

        actions = QHBoxLayout()
        filter_show_all = QPushButton("全部显示")
        filter_show_all.setStyleSheet("background: #f28b2e; color: white; padding: 7px; border: none;")
        filter_show_all.clicked.connect(lambda: self.set_all_filters(True))
        filter_hide_all = QPushButton("全部隐藏")
        filter_hide_all.setStyleSheet("background: #6fa6a1; color: white; padding: 7px; border: none;")
        filter_hide_all.clicked.connect(lambda: self.set_all_filters(False))
        actions.addWidget(filter_show_all)
        actions.addWidget(filter_hide_all)
        sidebar_layout.addLayout(actions)

        route_panel = QFrame()
        route_panel.setStyleSheet("QFrame { background: #f2f6f7; border: 1px solid #d3e0e3; }")
        route_layout = QVBoxLayout(route_panel)
        route_layout.setContentsMargins(6, 6, 6, 6)
        route_layout.setSpacing(4)
        route_title = QLabel("跑图导航")
        route_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #24313a;")
        route_layout.addWidget(route_title)
        self.route_status_label = QLabel("未生成路线")
        self.route_status_label.setStyleSheet("color: #5f6b7a;")
        route_layout.addWidget(self.route_status_label)

        route_buttons_top = QHBoxLayout()
        generate_route = QPushButton("生成最优路线")
        generate_route.clicked.connect(self.generate_route_from_visible)
        clear_route = QPushButton("清空")
        clear_route.clicked.connect(self.clear_route)
        for button in (generate_route, clear_route):
            route_buttons_top.addWidget(button)
        route_layout.addLayout(route_buttons_top)

        route_buttons_bottom = QHBoxLayout()
        import_route = QPushButton("导入导航")
        import_route.clicked.connect(self.import_route_file)
        self.manual_route_button = QPushButton("自行规划路线")
        self.manual_route_button.clicked.connect(self.toggle_manual_route_mode)
        for button in (import_route, self.manual_route_button):
            route_buttons_bottom.addWidget(button)
        route_layout.addLayout(route_buttons_bottom)

        self.route_tree = QTreeWidget()
        self.route_tree.setHeaderHidden(True)
        self.route_tree.setColumnCount(2)
        self.route_tree.setColumnWidth(0, 180)
        self.route_tree.setColumnWidth(1, 52)
        self.route_tree.header().setStretchLastSection(False)
        self.route_tree.setUniformRowHeights(False)
        self.route_tree.setWordWrap(True)
        self.route_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.route_tree.setTextElideMode(Qt.ElideNone)
        self.route_tree.itemClicked.connect(self.on_route_item_clicked)
        self.route_tree.itemChanged.connect(self.on_route_item_check_changed)
        self.route_tree.setMaximumHeight(180)
        self.route_tree.setVisible(False)
        route_layout.addWidget(self.route_tree)
        sidebar_layout.addWidget(route_panel)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.setColumnWidth(0, 220)
        self.tree.setColumnWidth(1, 44)
        self.tree.header().setStretchLastSection(False)
        self.tree.setIndentation(14)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tree.setTextElideMode(Qt.ElideRight)
        self.tree.itemChanged.connect(self.on_tree_item_changed)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        sidebar_layout.addWidget(self.tree, 1)
        self.populate_filter_tree()

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setStyleSheet("background: #f6f8fb; border-bottom: 1px solid #d8dee8;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        self.status_label = QLabel()
        self.status_label.setMinimumWidth(360)
        toolbar_layout.addWidget(self.status_label)
        toolbar_layout.addWidget(QLabel("图层"))
        for layer, label in MAP_LAYER_LABELS.items():
            layer_button = QPushButton(label)
            layer_button.setCheckable(True)
            layer_button.setEnabled(map_path_for_layer(layer).exists())
            layer_button.clicked.connect(lambda _checked=False, layer=layer: self.switch_map_layer(layer))
            self.layer_buttons[layer] = layer_button
            toolbar_layout.addWidget(layer_button)
        self.update_layer_buttons()
        route_nav_button = QPushButton("跑图导航")
        route_nav_button.clicked.connect(self.open_route_navigation)
        toolbar_layout.addWidget(route_nav_button)
        egg_query_button = QPushButton("孵蛋查询")
        egg_query_button.clicked.connect(self.open_egg_query_dialog)
        toolbar_layout.addWidget(egg_query_button)
        pvp_damage_button = QPushButton("PVP伤害计算")
        pvp_damage_button.clicked.connect(self.open_pvp_damage_dialog)
        toolbar_layout.addWidget(pvp_damage_button)

        restore_button = QPushButton("恢复全部")
        restore_button.clicked.connect(self.restore_all)
        toolbar_layout.addWidget(restore_button)
        toolbar_layout.addStretch(1)
        main_layout.addWidget(toolbar)

        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.view = MapView(self, self.scene)
        main_layout.addWidget(self.view, 1)

        splitter.addWidget(sidebar)
        splitter.addWidget(main)
        splitter.setSizes([300, 1020])

    def populate_filter_tree(self):
        self.search_mode = False
        groups = OrderedDict()
        for mark_type, info in self.resource_types.items():
            if self.resource_type_count_for_layer(info) <= 0:
                continue
            groups.setdefault(info["group"], []).append((mark_type, info))

        self.updating_tree = True
        self.tree.clear()
        self.tree_items_by_type.clear()
        for group_name, entries in groups.items():
            group_item = QTreeWidgetItem([f"{group_name} ({len(entries)})", ""])
            group_item.setFlags(
                group_item.flags()
                | Qt.ItemIsUserCheckable
                | Qt.ItemIsAutoTristate
            )
            self.tree.addTopLevelItem(group_item)

            checked_count = 0
            for mark_type, info in entries:
                child = QTreeWidgetItem([info["name"], str(self.resource_type_count_for_layer(info))])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                checked = mark_type in self.visible_types
                if checked:
                    checked_count += 1
                child.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
                child.setData(0, Qt.UserRole, mark_type)
                icon = self.get_sidebar_icon(info["icon"])
                if not icon.isNull():
                    child.setIcon(0, QIcon(icon))
                group_item.addChild(child)
                self.tree_items_by_type[mark_type] = child
            if checked_count == 0:
                group_item.setCheckState(0, Qt.Unchecked)
            elif checked_count == len(entries):
                group_item.setCheckState(0, Qt.Checked)
            else:
                group_item.setCheckState(0, Qt.PartiallyChecked)
            group_item.setExpanded(True)
        self.updating_tree = False

    def on_search_text_changed(self, text):
        if not text.strip() and self.search_mode:
            self.clear_search()

    def clear_search(self):
        self.search_mode = False
        self.search_input.clear()
        self.populate_filter_tree()
        self.update_status()

    def open_egg_query_dialog(self):
        dialog = getattr(self, "egg_query_dialog", None)
        if dialog is not None:
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            return
        dialog = EggQueryDialog(None)
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.destroyed.connect(lambda *_args: setattr(self, "egg_query_dialog", None))
        self.egg_query_dialog = dialog
        dialog.show()

    def open_pvp_damage_dialog(self):
        dialog = getattr(self, "pvp_damage_dialog", None)
        if dialog is not None:
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            return
        dialog = PvpDamageDialog(None)
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.destroyed.connect(lambda *_args: setattr(self, "pvp_damage_dialog", None))
        self.pvp_damage_dialog = dialog
        dialog.show()

    def run_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.clear_search()
            return
        terms = [term for term in query.lower().split() if term]
        results = []
        for marker in self.markers:
            detail = self.marker_detail_for(marker)
            haystack = "\n".join([
                marker.get("title") or "",
                marker.get("name") or "",
                marker.get("label") or "",
                marker.get("group") or "",
                map_layer_label(marker.get("layer")),
                detail.get("title") or "",
                detail.get("description") or "",
            ]).lower()
            if all(term in haystack for term in terms):
                results.append(marker)
        self.populate_search_results(results, query)

    def populate_search_results(self, results, query):
        self.search_mode = True
        self.updating_tree = True
        self.tree.clear()
        self.tree_items_by_type.clear()
        for marker in results[:300]:
            title = marker.get("title") or marker["name"]
            detail = self.marker_detail_for(marker)
            description = (detail.get("description") or "").strip()
            second = f"{map_layer_label(marker.get('layer'))} / {marker['name']}"
            if description:
                second = f"{map_layer_label(marker.get('layer'))} / {marker['name']}  {description[:28]}"
            item = QTreeWidgetItem([title, second])
            item.setData(0, Qt.UserRole, {"kind": "search_result", "uid": marker["uid"]})
            icon = self.get_sidebar_icon(marker["icon"])
            if not icon.isNull():
                item.setIcon(0, QIcon(icon))
            self.tree.addTopLevelItem(item)
        if not results:
            empty = QTreeWidgetItem([f"没有搜到：{query}", ""])
            empty.setFlags(empty.flags() & ~Qt.ItemIsSelectable)
            self.tree.addTopLevelItem(empty)
        self.updating_tree = False
        shown = min(len(results), 300)
        suffix = "" if len(results) <= 300 else f"（显示前 {shown} 个）"
        self.filter_status.setText(f"搜索结果 {len(results)} 个{suffix}")

    def build_scene(self):
        self.base_pixmap = self.load_layer_pixmap(self.current_layer)
        if self.base_pixmap.isNull():
            raise RuntimeError(f"地图图片不存在或无法读取：{self.active_map_path()}")
        self.scene.setSceneRect(0, 0, self.base_pixmap.width(), self.base_pixmap.height())
        self.map_item = self.scene.addPixmap(self.base_pixmap)
        self.map_item.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)
        self.map_item.setTransformationMode(Qt.SmoothTransformation)
        self.map_item.setZValue(0)
        self.rebuild_marker_tiles()

        self.view.set_initial_transform()
        self.view.centerOn(self.base_pixmap.width() / 2, self.base_pixmap.height() / 2)

    def rebuild_marker_tiles(self):
        if getattr(self, "route_markers", None):
            QTimer.singleShot(0, self.refresh_route_overlay)
        if self.base_pixmap is None:
            return
        for item in self.marker_tile_items:
            self.scene.removeItem(item)
        self.marker_tile_items = []

        columns = math.ceil(self.base_pixmap.width() / MARKER_TILE_SIZE)
        rows = math.ceil(self.base_pixmap.height() / MARKER_TILE_SIZE)
        markers_by_tile = {(column, row): [] for row in range(rows) for column in range(columns)}
        for marker in self.visible_markers():
            width, height = self.marker_hit_size(marker)
            left = marker["x"] - self.icon_anchor[0]
            top = marker["y"] - self.icon_anchor[1]
            right = left + width
            bottom = top + height
            min_column = max(0, int(left // MARKER_TILE_SIZE))
            max_column = min(columns - 1, int(right // MARKER_TILE_SIZE))
            min_row = max(0, int(top // MARKER_TILE_SIZE))
            max_row = min(rows - 1, int(bottom // MARKER_TILE_SIZE))
            for row in range(min_row, max_row + 1):
                for column in range(min_column, max_column + 1):
                    markers_by_tile[(column, row)].append(marker)

        for row in range(rows):
            for column in range(columns):
                tile_markers = markers_by_tile[(column, row)]
                if not tile_markers:
                    continue
                tile_x = column * MARKER_TILE_SIZE
                tile_y = row * MARKER_TILE_SIZE
                tile_width = min(MARKER_TILE_SIZE, self.base_pixmap.width() - tile_x)
                tile_height = min(MARKER_TILE_SIZE, self.base_pixmap.height() - tile_y)
                tile = QPixmap(tile_width * MARKER_LAYER_SCALE, tile_height * MARKER_LAYER_SCALE)
                tile.fill(Qt.transparent)
                painter = QPainter(tile)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                for marker in tile_markers:
                    pixmap = self.get_marker_pixmap(marker["icon"])
                    if pixmap.isNull():
                        continue
                    painter.setOpacity(DIMMED_OPACITY if marker["uid"] in self.dimmed_uids else 1.0)
                    painter.drawPixmap(
                        round((marker["x"] - self.icon_anchor[0] - tile_x) * MARKER_LAYER_SCALE),
                        round((marker["y"] - self.icon_anchor[1] - tile_y) * MARKER_LAYER_SCALE),
                        pixmap,
                    )
                painter.end()
                item = self.scene.addPixmap(tile)
                item.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)
                item.setTransformationMode(Qt.FastTransformation)
                item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
                item.setPos(tile_x, tile_y)
                item.setScale(1 / MARKER_LAYER_SCALE)
                item.setZValue(2)
                self.marker_tile_items.append(item)

    def get_marker_pixmap(self, path):
        key = str(path)
        if key not in self.icon_pixmaps:
            pixmap = QPixmap(key)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToWidth(self.marker_icon_width * MARKER_LAYER_SCALE, Qt.SmoothTransformation)
                self.icon_hit_sizes[key] = (
                    pixmap.width() / MARKER_LAYER_SCALE,
                    pixmap.height() / MARKER_LAYER_SCALE,
                )
            else:
                self.icon_hit_sizes[key] = (self.marker_icon_width, self.marker_icon_width)
            self.icon_pixmaps[key] = pixmap
        return self.icon_pixmaps[key]

    def marker_hit_size(self, marker):
        key = str(marker["icon"])
        if key not in self.icon_hit_sizes:
            self.get_marker_pixmap(marker["icon"])
        return self.icon_hit_sizes.get(key, (self.marker_icon_width, self.marker_icon_width))

    def get_sidebar_icon(self, path):
        key = str(path)
        if key not in self.sidebar_icons:
            pixmap = QPixmap(key)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToWidth(SIDEBAR_ICON_WIDTH, Qt.SmoothTransformation)
            self.sidebar_icons[key] = pixmap
        return self.sidebar_icons[key]

    def should_show_tooltip(self, marker):
        detail = self.marker_detail_for(marker)
        if (detail.get("title") or detail.get("description") or detail.get("image") or detail.get("images")):
            return True
        return marker["group"] == SPIRIT_GROUP or marker["mark_type"] in TOOLTIP_MARK_TYPES

    def tooltip_text(self, marker):
        detail = self.marker_detail_for(marker)
        detail_title = (detail.get("title") or "").strip()
        detail_description = " ".join((detail.get("description") or "").split())
        title = detail_title or marker.get("title") or marker["name"]
        lines = [f"{marker['name']}：{title}" if title != marker["name"] else title]
        if detail_description:
            if len(detail_description) > 140:
                detail_description = detail_description[:140].rstrip() + "..."
            lines.append(detail_description)
        elif detail_title:
            source_category = marker.get("source_category_name") or ""
            if source_category and source_category not in lines[0]:
                lines.append(f"17173：{source_category}")
        return "\n".join(lines)

    def markers_at_scene_pos(self, scene_pos):
        map_x = scene_pos.x()
        map_y = scene_pos.y()
        matches = []
        for marker in reversed(self.visible_markers()):
            width, height = self.marker_hit_size(marker)
            left = marker["x"] - self.icon_anchor[0]
            top = marker["y"] - self.icon_anchor[1]
            if left <= map_x <= left + width and top <= map_y <= top + height:
                center_distance = (marker["x"] - map_x) ** 2 + (marker["y"] - map_y) ** 2
                matches.append((center_distance, marker))
        matches.sort(key=lambda item: item[0])
        return [marker for _distance, marker in matches]

    def hit_test_marker(self, scene_pos, cycle=False):
        matches = self.markers_at_scene_pos(scene_pos)
        if not matches:
            if cycle:
                self.marker_hit_cycle_key = None
                self.marker_hit_cycle_index = 0
            return None
        if not cycle or len(matches) == 1:
            return matches[0]
        key = tuple(marker["uid"] for marker in matches)
        if key == self.marker_hit_cycle_key:
            self.marker_hit_cycle_index = (self.marker_hit_cycle_index + 1) % len(matches)
        else:
            self.marker_hit_cycle_key = key
            self.marker_hit_cycle_index = 0
        return matches[self.marker_hit_cycle_index]

    def focus_marker(self, marker, open_detail=None):
        marker_layer = marker.get("layer", "G")
        if marker_layer != self.current_layer:
            if not self.switch_map_layer(marker_layer, center_on=(marker["x"], marker["y"])):
                return
        if not is_manual_route_point(marker) and marker.get("mark_type") not in self.visible_types:
            self.visible_types.add(marker["mark_type"])
            item = self.tree_items_by_type.get(marker["mark_type"])
            if item is not None:
                self.updating_tree = True
                item.setCheckState(0, Qt.Checked)
                self.updating_tree = False
        self.request_marker_rebuild()
        self.update_status()

        if self.view.current_scale < 1.25:
            factor = 1.25 / self.view.current_scale
            self.view.current_scale = 1.25
            self.view.scale(factor, factor)
        self.view.centerOn(marker["x"], marker["y"])
        if self.highlight_item is not None:
            self.scene.removeItem(self.highlight_item)
            self.highlight_item = None
        radius = 42
        self.highlight_item = QGraphicsEllipseItem(
            marker["x"] - radius,
            marker["y"] - radius,
            radius * 2,
            radius * 2,
        )
        pen = QPen(QColor("#ffcc32"))
        pen.setWidth(5)
        self.highlight_item.setPen(pen)
        self.highlight_item.setBrush(QBrush(Qt.NoBrush))
        self.highlight_item.setZValue(9)
        self.scene.addItem(self.highlight_item)

    def clear_highlight(self):
        if self.highlight_item is not None:
            self.scene.removeItem(self.highlight_item)
            self.highlight_item = None

    def restore_route_from_state(self):
        route_uids = self.route_state.get("routeMarkers", [])
        self.route_markers = [
            self.markers_by_uid[uid]
            for uid in route_uids
            if uid in self.markers_by_uid
        ]
        self.current_route_index = 0
        self.skip_completed_route_markers()
        self.refresh_route_ui()
        self.render_route_path()

    def save_route_state(self):
        write_json(account_data_path(self.account_id, "user_route_progress.json"), {
            "version": 1,
            "accountId": self.account_id,
            "accountName": self.account_name,
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
            "completedMarkers": sorted(self.completed_route_uids),
            "routeMarkers": [marker["uid"] for marker in self.route_markers],
            "currentIndex": self.current_route_index,
        })

    def route_center(self):
        if not hasattr(self, "view"):
            return self.base_pixmap.width() / 2, self.base_pixmap.height() / 2
        center = self.view.mapToScene(self.view.viewport().rect().center())
        return center.x(), center.y()

    def generate_route_from_visible(self):
        candidates = [
            marker
            for marker in self.markers
            if marker["mark_type"] in self.visible_types
            and marker["uid"] not in self.completed_route_uids
        ]
        if not candidates:
            QMessageBox.information(self, "没有可跑资源", "当前显示范围内没有未完成的资源。")
            return

        def snake_key(marker):
            band = int(marker["y"] // ROUTE_BAND_HEIGHT)
            x_key = marker["x"] if band % 2 == 0 else -marker["x"]
            return band, x_key

        ordered = sorted(candidates, key=snake_key)
        center_x, center_y = self.route_center()
        start_index = min(
            range(len(ordered)),
            key=lambda index: (ordered[index]["x"] - center_x) ** 2 + (ordered[index]["y"] - center_y) ** 2,
        )
        self.route_markers = ordered[start_index:] + ordered[:start_index]
        self.current_route_index = 0
        self.skip_completed_route_markers()
        self.refresh_route_ui()
        self.render_route_path()
        self.save_route_state()
        self.focus_current_route_marker()

    def skip_completed_route_markers(self):
        while (
            self.current_route_index < len(self.route_markers)
            and self.route_markers[self.current_route_index]["uid"] in self.completed_route_uids
        ):
            self.current_route_index += 1

    def current_route_marker(self):
        self.skip_completed_route_markers()
        if 0 <= self.current_route_index < len(self.route_markers):
            return self.route_markers[self.current_route_index]
        return None

    def complete_current_route_marker(self):
        marker = self.current_route_marker()
        if marker is None:
            return
        self.completed_route_uids.add(marker["uid"])
        self.dimmed_uids.add(marker["uid"])
        self.current_route_index += 1
        self.skip_completed_route_markers()
        self.rebuild_marker_tiles()
        self.refresh_route_ui()
        self.render_route_path()
        self.queue_state_and_route_save()
        next_marker = self.current_route_marker()
        if next_marker is not None:
            self.focus_marker(next_marker, open_detail=False)

    def focus_current_route_marker(self):
        marker = self.current_route_marker()
        if marker is not None:
            self.focus_marker(marker, open_detail=False)

    def clear_route(self):
        self.route_markers = []
        self.current_route_index = 0
        if self.route_path_item is not None:
            self.scene.removeItem(self.route_path_item)
            self.route_path_item = None
        self.refresh_route_ui()
        self.save_route_state()

    def refresh_route_ui(self):
        if not hasattr(self, "route_tree"):
            return
        self.route_tree.clear()
        total = len(self.route_markers)
        completed = sum(1 for marker in self.route_markers if marker["uid"] in self.completed_route_uids)
        current = self.current_route_marker()
        if total:
            current_text = current.get("title") or current["name"] if current else "已完成"
            self.route_status_label.setText(f"进度 {completed}/{total}  当前：{current_text}")
        else:
            self.route_status_label.setText("未生成路线")

        for index, marker in enumerate(self.route_markers):
            completed_mark = marker["uid"] in self.completed_route_uids
            prefix = "✓" if completed_mark else ("▶" if index == self.current_route_index else str(index + 1))
            title = marker.get("title") or marker["name"]
            item = QTreeWidgetItem([f"{prefix}. {title}", marker["name"]])
            item.setData(0, Qt.UserRole, {"kind": "route_marker", "uid": marker["uid"], "index": index})
            icon = self.get_sidebar_icon(marker["icon"])
            if not icon.isNull():
                item.setIcon(0, QIcon(icon))
            if completed_mark:
                item.setForeground(0, QBrush(QColor("#8b95a3")))
                item.setForeground(1, QBrush(QColor("#8b95a3")))
            self.route_tree.addTopLevelItem(item)
        if self.current_route_index < self.route_tree.topLevelItemCount():
            self.route_tree.setCurrentItem(self.route_tree.topLevelItem(self.current_route_index))

    def render_route_path(self):
        if self.route_path_item is not None:
            self.scene.removeItem(self.route_path_item)
            self.route_path_item = None
        remaining = [
            marker
            for marker in self.route_markers[self.current_route_index:self.current_route_index + ROUTE_DRAW_LIMIT]
            if marker["uid"] not in self.completed_route_uids
        ]
        if len(remaining) < 2:
            return
        path = QPainterPath()
        path.moveTo(remaining[0]["x"], remaining[0]["y"])
        for marker in remaining[1:]:
            path.lineTo(marker["x"], marker["y"])
        self.route_path_item = QGraphicsPathItem(path)
        pen = QPen(QColor("#26a6a1"))
        pen.setWidth(4)
        pen.setCosmetic(True)
        self.route_path_item.setPen(pen)
        self.route_path_item.setZValue(4)
        self.scene.addItem(self.route_path_item)

    def on_route_item_clicked(self, item, _column):
        data = item.data(0, Qt.UserRole)
        if not isinstance(data, dict) or data.get("kind") != "route_marker":
            return
        marker = self.markers_by_uid.get(data.get("uid"))
        if marker is None:
            return
        self.current_route_index = data.get("index", 0)
        self.refresh_route_ui()
        self.render_route_path()
        self.save_route_state()
        self.focus_marker(marker, open_detail=True)

    def queue_state_and_route_save(self):
        self.pending_save.start()
        self.save_route_state()
        self.update_status()

    def visible_markers(self):
        signature = (self.current_layer, tuple(sorted(self.visible_types)))
        if self._visible_markers_cache_signature == signature:
            return self._visible_markers_cache
        self._visible_markers_cache_signature = signature
        self._visible_markers_cache = [
            marker
            for marker in self.markers
            if marker["mark_type"] in self.visible_types
            and self.marker_matches_current_layer(marker)
        ]
        return self._visible_markers_cache

    def open_route_navigation(self):
        if self.route_dialog is not None:
            self.route_dialog.show()
            self.route_dialog.raise_()
            self.route_dialog.activateWindow()
            return

        dialog = RouteNavigationDialog(self)
        dialog.setWindowTitle("跑图导航")
        dialog.setMinimumSize(ROUTE_DIALOG_NORMAL_MIN_SIZE)
        dialog.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(4)
        top_left = QVBoxLayout()
        top_left.setSpacing(4)

        title_row = QHBoxLayout()
        title = QLabel("跑图导航")
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #263238;")
        self.route_dialog_status_label = QLabel("未生成路线")
        self.route_dialog_status_label.setStyleSheet("color: #5f6b7a;")
        title_row.addWidget(title)
        title_row.addWidget(self.route_dialog_status_label, 1)
        top_left.addLayout(title_row)

        buttons = QHBoxLayout()
        locate_button = QPushButton("定位小洛克位置")
        locate_button.clicked.connect(self.focus_current_player_position)
        route_start_button = QPushButton("定位路线源头")
        route_start_button.clicked.connect(self.focus_route_start_marker)
        complete_button = QPushButton("完成当前资源点")
        complete_button.clicked.connect(self.complete_current_route_marker)
        for button in (locate_button, route_start_button, complete_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        top_left.addLayout(buttons)

        follow_row = QHBoxLayout()
        follow_button = QPushButton("开启AI导航")
        follow_button.clicked.connect(self.toggle_minimap_follow)
        self.minimap_follow_button = follow_button
        circle_button = QPushButton("选择小地图范围")
        circle_button.clicked.connect(self.show_minimap_circle)
        lock_circle_button = QPushButton("固定小地图圈")
        lock_circle_button.clicked.connect(self.toggle_minimap_circle_lock)
        self.minimap_circle_lock_button = lock_circle_button
        pin_button = QPushButton("固定导航")
        pin_button.clicked.connect(self.toggle_route_dialog_pin)
        self.route_dialog_pin_button = pin_button
        self.minimap_follow_status_label = QLabel("未启用")
        self.minimap_follow_status_label.setStyleSheet("color: #5f6b7a;")
        for button in (follow_button, circle_button, lock_circle_button, pin_button):
            follow_row.addWidget(button)
        follow_row.addWidget(self.minimap_follow_status_label, 1)
        top_left.addLayout(follow_row)

        opacity_row = QHBoxLayout()
        opacity_label = QLabel("地图透明度")
        opacity_row.addWidget(opacity_label)
        self.route_preview_opacity_slider = QSlider(Qt.Horizontal)
        self.route_preview_opacity_slider.setRange(0, 100)
        self.route_preview_opacity_slider.setValue(100)
        self.route_preview_opacity_slider.valueChanged.connect(self.set_route_preview_opacity)
        opacity_row.addWidget(self.route_preview_opacity_slider, 1)
        top_left.addLayout(opacity_row)

        top_row.addLayout(top_left, 3)

        tree = QTreeWidget()
        tree.setHeaderLabels(["路线顺序", "分类"])
        tree.setColumnWidth(0, 164)
        tree.setColumnWidth(1, 50)
        tree.header().setStretchLastSection(False)
        tree.setUniformRowHeights(False)
        tree.setWordWrap(True)
        tree.setIndentation(10)
        tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tree.setTextElideMode(Qt.ElideNone)
        tree.itemClicked.connect(self.on_route_item_clicked)
        tree.itemChanged.connect(self.on_route_item_check_changed)
        tree.setMinimumWidth(ROUTE_DIALOG_ROUTE_WIDTH_NORMAL)
        tree.setMaximumHeight(16777215)
        self.route_preview_scene = QGraphicsScene(dialog)
        self.route_preview_view = RoutePreviewView(self.route_preview_scene, self)
        self.route_preview_view.setMinimumSize(220, 180)
        self.route_preview_view.setRenderHint(QPainter.Antialiasing, True)
        self.route_preview_view.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.route_preview_map_item = QGraphicsPixmapItem(QPixmap(str(self.active_map_path())))
        self.route_preview_map_item.setOpacity(1.0)
        self.route_preview_scene.addItem(self.route_preview_map_item)

        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(2)
        pin_bar = QHBoxLayout()
        pin_bar.setContentsMargins(4, 0, 4, 0)
        pin_bar.setSpacing(0)
        self.route_dialog_route_list_button = QPushButton("隐藏路线")
        self.route_dialog_route_list_button.clicked.connect(self.toggle_route_list_panel)
        self.route_dialog_pin_label = QLabel("F9 定位小洛克位置  F10 定位路线源头  F11 开启/关闭路线顺序  F12 解除固定")
        self.route_dialog_pin_label.setFixedHeight(18)
        self.route_dialog_pin_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.route_dialog_pin_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #d05b00; padding: 0px;")
        self.route_dialog_pin_bar_widgets = [self.route_dialog_pin_label]
        for widget in self.route_dialog_pin_bar_widgets:
            widget.setVisible(False)
        self.route_dialog_route_list_button.setVisible(False)
        pin_bar.addWidget(self.route_dialog_pin_label, 1)

        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(2)
        left_column.addLayout(pin_bar)
        left_column.addLayout(top_row)
        left_column.addWidget(self.route_preview_view, 1)

        self.route_dialog_side_panel = QWidget(dialog)
        side_column = QVBoxLayout(self.route_dialog_side_panel)
        side_column.setContentsMargins(0, 0, 0, 0)
        side_column.setSpacing(2)
        side_column.addWidget(tree, 1)

        main_row.addLayout(left_column, 1)
        main_row.addWidget(self.route_dialog_side_panel, 0)
        layout.addLayout(main_row, 1)

        self.route_dialog_normal_widgets = [
            title,
            self.route_dialog_status_label,
            locate_button,
            route_start_button,
            complete_button,
            pin_button,
            follow_button,
            circle_button,
            lock_circle_button,
            self.minimap_follow_status_label,
            opacity_label,
            self.route_preview_opacity_slider,
        ]
        self.route_dialog_normal_layouts = [top_row, title_row, buttons, follow_row, opacity_row]
        self.route_dialog_pin_widgets = [self.route_dialog_pin_label]

        self.route_dialog = dialog
        self.route_dialog_tree = tree
        dialog.destroyed.connect(self.on_route_dialog_destroyed)
        self.refresh_route_tree()
        self.update_route_preview()
        dialog.show()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and self.route_dialog is not None and self.route_dialog_pinned:
            if event.key() == Qt.Key_F12:
                self.toggle_route_dialog_pin()
                return True
            if event.key() == Qt.Key_F9:
                self.focus_current_player_position()
                return True
            if event.key() == Qt.Key_F10:
                self.focus_route_start_marker()
                return True
            if event.key() == Qt.Key_F11:
                self.toggle_route_list_panel()
                return True
        return super().eventFilter(obj, event)

    def on_route_dialog_destroyed(self, *args):
        self.minimap_follow_enabled = False
        self.minimap_follow_timer.stop()
        self.route_dialog = None
        self.route_dialog_pinned = False
        self.route_dialog_normal_widgets = []
        self.route_dialog_pin_widgets = []
        self.route_dialog_normal_layouts = []
        self.route_dialog_pin_bar_widgets = []
        self.route_dialog_route_list_button = None
        self.route_dialog_route_list_visible = True
        self.route_dialog_side_panel = None
        self.route_dialog_unpinned_size = None
        self.minimap_follow_button = None
        self.minimap_circle_lock_button = None
        self.route_dialog_pin_button = None
        self.route_dialog_tree = None
        self.route_dialog_status_label = None
        self.route_dialog_pin_label = None
        self.route_preview_scene = None
        self.route_preview_view = None
        self.route_preview_map_item = None
        self.route_preview_path_item = None
        self.route_preview_arrow_item = None
        self.route_preview_current_item = None
        self.route_preview_player_item = None
        self.route_preview_opacity_slider = None
        self.route_preview_marker_items = []
        self.route_preview_marker_signature = None
        self.minimap_follow_status_label = None
        if self.minimap_circle is not None:
            self.minimap_circle.close()
            self.minimap_circle = None

    def toggle_route_dialog_pin(self):
        if self.route_dialog is None:
            return
        self.route_dialog_pinned = not self.route_dialog_pinned
        flags = Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
        if self.route_dialog_pinned:
            flags = Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            self.route_dialog_unpinned_size = self.route_dialog.size()
            self.route_dialog_route_list_visible = True
            self.route_dialog.setMinimumSize(ROUTE_DIALOG_PINNED_MIN_SIZE)
            self.route_dialog.setMaximumSize(16777215, 16777215)
        else:
            self.route_dialog.setMinimumSize(ROUTE_DIALOG_NORMAL_MIN_SIZE)
            self.route_dialog.setMaximumSize(16777215, 16777215)
        self.route_dialog.setWindowFlags(flags)
        for widget in self.route_dialog_normal_widgets:
            if widget is not None:
                widget.setVisible(not self.route_dialog_pinned)
        for layout in self.route_dialog_normal_layouts:
            for index in range(layout.count()):
                item = layout.itemAt(index)
                widget = item.widget()
                if widget is not None and widget not in self.route_dialog_pin_widgets:
                    widget.setVisible(not self.route_dialog_pinned)
        for widget in self.route_dialog_pin_widgets:
            if widget is not None:
                widget.setVisible(self.route_dialog_pinned)
        if self.route_dialog_side_panel is not None:
            self.route_dialog_side_panel.setVisible(
                (not self.route_dialog_pinned) or self.route_dialog_route_list_visible
            )
            self.route_dialog_side_panel.setMaximumWidth(
                ROUTE_DIALOG_ROUTE_WIDTH_PINNED if self.route_dialog_pinned else ROUTE_DIALOG_ROUTE_WIDTH_NORMAL + 18
            )
            self.route_dialog_side_panel.setMinimumWidth(
                ROUTE_DIALOG_ROUTE_WIDTH_PINNED if self.route_dialog_pinned else ROUTE_DIALOG_ROUTE_WIDTH_NORMAL
            )
        if self.route_dialog_tree is not None:
            self.route_dialog_tree.setMaximumHeight(16777215)
            self.route_dialog_tree.setMinimumWidth(
                ROUTE_DIALOG_ROUTE_WIDTH_PINNED if self.route_dialog_pinned else ROUTE_DIALOG_ROUTE_WIDTH_NORMAL
            )
            if self.route_dialog_pinned:
                self.route_dialog_tree.setHeaderLabels(["路线顺序", ""])
                self.route_dialog_tree.setColumnHidden(1, True)
                self.route_dialog_tree.setColumnWidth(0, ROUTE_DIALOG_ROUTE_WIDTH_PINNED - 8)
            else:
                self.route_dialog_tree.setHeaderLabels(["路线顺序", "分类"])
                self.route_dialog_tree.setColumnHidden(1, False)
                self.route_dialog_tree.setColumnWidth(0, 164)
                self.route_dialog_tree.setColumnWidth(1, 50)
        if self.route_preview_view is not None:
            if self.route_dialog_pinned:
                self.route_preview_view.setMinimumSize(160, 120)
            else:
                self.route_preview_view.setMinimumSize(220, 180)
        if self.route_dialog_route_list_button is not None:
            self.route_dialog_route_list_button.setText("隐藏路线" if self.route_dialog_route_list_visible else "显示路线")
        self.route_dialog.show()
        if self.route_dialog_pinned:
            self.route_dialog.resize(ROUTE_DIALOG_PINNED_DEFAULT_SIZE)
            self.route_dialog.raise_()
        elif self.route_dialog_unpinned_size is not None:
            self.route_dialog.resize(self.route_dialog_unpinned_size)

    def toggle_route_list_panel(self):
        self.route_dialog_route_list_visible = not self.route_dialog_route_list_visible
        if self.route_dialog_side_panel is not None:
            self.route_dialog_side_panel.setVisible(self.route_dialog_route_list_visible)
        if self.route_dialog_route_list_button is not None:
            self.route_dialog_route_list_button.setText("隐藏路线" if self.route_dialog_route_list_visible else "显示路线")

    def toggle_minimap_circle_lock(self):
        if self.minimap_circle is None:
            self.show_minimap_circle()
        self.minimap_circle_locked = not self.minimap_circle_locked
        self.minimap_circle.set_locked_for_game(self.minimap_circle_locked)
        if self.minimap_circle_lock_button is not None:
            self.minimap_circle_lock_button.setText("取消固定小地图圈" if self.minimap_circle_locked else "固定小地图圈")
        if self.minimap_follow_status_label is not None:
            if self.minimap_circle_locked:
                self.minimap_follow_status_label.setText("小地图圈已固定，开始识别定位")
            else:
                self.minimap_follow_status_label.setText("小地图圈可拖动，滚轮可缩放")
        if self.minimap_circle_locked:
            self.minimap_follow_enabled = True
            self.minimap_follow_timer.start()
            if self.minimap_follow_button is not None:
                self.minimap_follow_button.setText("关闭AI导航")
            self.minimap_circle.hide()
            self.update_minimap_follow()
        else:
            self.minimap_follow_enabled = False
            self.minimap_follow_timer.stop()
            if self.minimap_follow_button is not None:
                self.minimap_follow_button.setText("开启AI导航")
            self.minimap_circle.show()
            self.minimap_circle.raise_()

    def set_route_preview_opacity(self, value):
        if self.route_preview_map_item is not None:
            self.route_preview_map_item.setOpacity(max(0, min(100, value)) / 100)

    def route_preview_icon_pixmap(self, marker):
        cache_key = marker.get("mark_type") or marker.get("title") or marker.get("uid")
        if cache_key in self.route_preview_icon_cache:
            return self.route_preview_icon_cache[cache_key]

        candidates = []
        for key in (
            "iconPath",
            "icon_path",
            "iconFile",
            "icon_file",
            "icon",
            "imagePath",
            "image_path",
            "image",
        ):
            value = marker.get(key)
            if not value or str(value).startswith(("http://", "https://", "data:")):
                continue
            raw_path = Path(str(value))
            if raw_path.is_absolute():
                candidates.append(raw_path)
            else:
                candidates.extend(
                    [
                        PROJECT_DIR / raw_path,
                        PROJECT_DIR / "assets" / raw_path,
                        PROJECT_DIR / "assets" / "icons" / raw_path.name,
                        PROJECT_DIR / "assets" / "resources" / raw_path.name,
                    ]
                )

        pixmap = QPixmap()
        for path in candidates:
            if path.exists():
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    break

        if pixmap.isNull():
            pixmap = QPixmap(self.marker_icon_width, self.marker_icon_width)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setBrush(QBrush(QColor("#58b7c9")))
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawEllipse(2, 2, self.marker_icon_width - 4, self.marker_icon_width - 4)
            painter.end()

        self.route_preview_icon_cache[cache_key] = pixmap
        return pixmap

    def route_point_pixmap_scale(self, marker, pixmap):
        if pixmap.isNull() or pixmap.width() <= 0:
            return 1.0
        scale = self.marker_icon_width / pixmap.width()
        if is_manual_route_point(marker):
            scale *= MANUAL_ROUTE_POINT_SCALE
        return scale

    def route_point_pixmap_offset(self, marker, pixmap):
        if is_manual_route_point(marker):
            return -pixmap.width() / 2, -pixmap.height() / 2
        return -self.icon_anchor[0], -self.icon_anchor[1]

    def update_route_preview_map(self):
        if getattr(self, "tearing_down", False):
            return
        if self.route_preview_scene is None or self.route_preview_map_item is None:
            return
        pixmap = QPixmap(str(self.active_map_path()))
        if pixmap.isNull():
            return
        self.route_preview_map_item.setPixmap(pixmap)
        self.route_preview_scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.route_preview_marker_signature = None

    def update_route_preview(self):
        if getattr(self, "tearing_down", False):
            return
        if self.route_preview_scene is None or self.route_preview_map_item is None:
            return
        for item_name in ("route_preview_path_item", "route_preview_arrow_item", "route_preview_current_item"):
            item = getattr(self, item_name, None)
            if item is not None:
                try:
                    self.route_preview_scene.removeItem(item)
                except RuntimeError:
                    pass
                setattr(self, item_name, None)
        steps = self.route_remaining_steps(800)
        markers = [marker for marker, _kind in steps]
        preview_markers = self.route_preview_markers(1200)
        route_uids = tuple(route_point_uid(marker) for marker in preview_markers if route_point_uid(marker))
        if route_uids != self.route_preview_marker_signature:
            for item in self.route_preview_marker_items:
                try:
                    self.route_preview_scene.removeItem(item)
                except RuntimeError:
                    pass
            self.route_preview_marker_items = []
            self.route_preview_marker_signature = route_uids
            for marker in preview_markers:
                pixmap = self.route_preview_icon_pixmap(marker)
                item = QGraphicsPixmapItem(pixmap)
                item.setScale(self.route_point_pixmap_scale(marker, pixmap))
                offset_x, offset_y = self.route_point_pixmap_offset(marker, pixmap)
                item.setOffset(offset_x, offset_y)
                item.setPos(marker["x"], marker["y"])
                item.setZValue(2)
                item.setAcceptedMouseButtons(Qt.NoButton)
                item.setData(0, route_point_uid(marker))
                self.route_preview_scene.addItem(item)
                self.route_preview_marker_items.append(item)
        for item in self.route_preview_marker_items:
            uid = item.data(0)
            item.setOpacity(DIMMED_OPACITY if uid in self.completed_route_uids or uid in self.dimmed_uids else 1.0)

        if len(markers) >= 2:
            path = QPainterPath()
            arrow_path = QPainterPath()
            path.moveTo(markers[0]["x"], markers[0]["y"])
            for index, marker in enumerate(markers[1:], start=1):
                previous = markers[index - 1]
                path.lineTo(marker["x"], marker["y"])
                if index % ROUTE_ARROW_STEP == 0 or index == 1 or index == len(markers) - 1:
                    self.add_route_arrow(arrow_path, previous, marker)
            preview_pen = QPen(QColor("#ff7a00"), 3)
            preview_pen.setCosmetic(True)
            self.route_preview_path_item = QGraphicsPathItem(path)
            self.route_preview_path_item.setPen(preview_pen)
            self.route_preview_path_item.setZValue(3)
            self.route_preview_path_item.setAcceptedMouseButtons(Qt.NoButton)
            self.route_preview_scene.addItem(self.route_preview_path_item)
            arrow_pen = QPen(QColor("#00a7ff"), 4)
            arrow_pen.setCosmetic(True)
            self.route_preview_arrow_item = QGraphicsPathItem(arrow_path)
            self.route_preview_arrow_item.setPen(arrow_pen)
            self.route_preview_arrow_item.setZValue(4)
            self.route_preview_arrow_item.setAcceptedMouseButtons(Qt.NoButton)
            self.route_preview_scene.addItem(self.route_preview_arrow_item)

        current = self.current_route_marker()
        if current is not None:
            radius = 52
            self.route_preview_current_item = QGraphicsEllipseItem(
                current["x"] - radius,
                current["y"] - radius,
                radius * 2,
                radius * 2,
            )
            self.route_preview_current_item.setPen(QPen(QColor("#ffe300"), 6))
            self.route_preview_current_item.setBrush(QBrush(QColor(255, 227, 0, 64)))
            self.route_preview_current_item.setZValue(5)
            self.route_preview_current_item.setAcceptedMouseButtons(Qt.NoButton)
            self.route_preview_scene.addItem(self.route_preview_current_item)

        if self.route_preview_view is not None:
            if current is not None and hasattr(self.route_preview_view, "set_initial_focus"):
                self.route_preview_view.set_initial_focus(current["x"], current["y"])
            elif not getattr(self.route_preview_view, "initialized_view", True):
                self.route_preview_view.fitInView(self.route_preview_map_item, Qt.KeepAspectRatio)

    def toggle_minimap_follow(self):
        if self.minimap_follow_enabled:
            self.minimap_follow_enabled = False
            self.minimap_follow_timer.stop()
            if self.minimap_follow_button is not None:
                self.minimap_follow_button.setText("开启AI导航")
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText("未启用")
            return
        if self.minimap_circle is None:
            self.show_minimap_circle()
        if not self.minimap_circle_locked:
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText("请先调整圆圈位置，再点击固定小地图圈开始识别")
            return
        self.minimap_follow_enabled = True
        if self.minimap_follow_button is not None:
            self.minimap_follow_button.setText("关闭AI导航")
        self.minimap_follow_timer.start()
        self.update_minimap_follow()

    def show_minimap_circle(self):
        if self.minimap_circle is None:
            self.minimap_circle = MinimapSelectionCircle(self)
            self.minimap_circle.destroyed.connect(self.on_minimap_circle_destroyed)
        self.minimap_circle.set_locked_for_game(self.minimap_circle_locked)
        self.minimap_circle.show()
        self.minimap_circle.raise_()
        self.minimap_circle.activateWindow()
        self.update_minimap_circle_region(self.minimap_circle.capture_region())

    def on_minimap_circle_destroyed(self, *args):
        self.minimap_circle = None
        if self.minimap_follow_status_label is not None and self.minimap_follow_enabled:
            self.minimap_follow_status_label.setText("实验模式：识别圆圈已关闭")

    def update_minimap_circle_region(self, region):
        self.minimap_circle_region = region
        if self.minimap_follow_status_label is not None:
            self.minimap_follow_status_label.setText(
                f"识别区域 x:{region['x']} y:{region['y']} 大小:{region['size']}"
            )

    def calibrate_minimap_to_view_center(self):
        if self.route_preview_view is None:
            return
        center = self.route_preview_view.mapToScene(self.route_preview_view.viewport().rect().center())
        pixmap = self.capture_minimap_region()
        if pixmap is None or pixmap.isNull():
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText("校准失败：无法截图小地图")
            return
        image = pixmap.toImage().convertToFormat(QImage.Format_RGB32)
        player_local, detected_player = self.detect_minimap_player(image)
        self.minimap_reference_image = image
        self.minimap_reference_player_local = player_local
        self.minimap_reference_world_pos = (center.x(), center.y())
        self.minimap_previous_image = image
        self.minimap_previous_player_local = player_local
        self.minimap_calibrated = True
        self.minimap_tracking_failures = 0
        self.minimap_last_world_pos = (center.x(), center.y())
        self.set_route_preview_player_position(center.x(), center.y())
        sift_ok = self.prepare_sift_tracker()
        if self.minimap_follow_status_label is not None:
            player_text = "已识别角色箭头" if detected_player else "未识别箭头，使用中心"
            sift_text = "SIFT已就绪" if sift_ok else "SIFT不可用"
            self.minimap_follow_status_label.setText(f"已校准到导航地图中心，{player_text}，{sift_text}")

    def cv_read_image(self, path):
        if cv2 is None or np is None:
            return None
        try:
            data = np.fromfile(str(path), dtype=np.uint8)
            return cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception:
            return None

    def qimage_to_bgr(self, image):
        if cv2 is None or np is None:
            return None
        rgba = image.convertToFormat(QImage.Format_RGBA8888)
        width = rgba.width()
        height = rgba.height()
        ptr = rgba.bits()
        ptr.setsize(rgba.byteCount())
        array = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        return cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)

    def create_feature_detector(self):
        if cv2 is None:
            return None, None
        if hasattr(cv2, "SIFT_create"):
            return cv2.SIFT_create(nfeatures=18000, contrastThreshold=0.025), "SIFT"
        if hasattr(cv2, "AKAZE_create"):
            return cv2.AKAZE_create(), "AKAZE"
        return None, None

    def create_sift_matcher(self):
        if self.sift_method == "SIFT":
            return cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=64))
        return cv2.BFMatcher(cv2.NORM_HAMMING)

    def prepare_sift_tracker(self):
        if cv2 is None or np is None:
            QMessageBox.warning(self, "AI小地图跟随", "当前 Python 环境缺少 OpenCV，无法使用 SIFT/AKAZE 跟随。")
            return False
        detector, method = self.create_feature_detector()
        if detector is None:
            QMessageBox.warning(self, "AI小地图跟随", "当前 OpenCV 不支持 SIFT 或 AKAZE。")
            return False
        self.sift_method = method

        cache_path = self.sift_cache_path()
        if cache_path.exists():
            try:
                cache = np.load(str(cache_path), allow_pickle=False)
                expected_width = getattr(self, "map_pixmap", QPixmap(str(self.active_map_path()))).width()
                if str(cache["method"]) == method and int(cache["source_w"]) == expected_width:
                    self.sift_ref_scale = float(cache["scale"])
                    self.sift_keypoints = cache["pts"].astype(np.float32)
                    self.sift_descriptors = cache["desc"]
                    self.sift_matcher = self.create_sift_matcher()
                    self.sift_ready = self.sift_descriptors is not None and len(self.sift_descriptors) > 0
                    if self.sift_ready:
                        if self.minimap_follow_status_label is not None:
                            self.minimap_follow_status_label.setText(f"{method}缓存已加载：{len(self.sift_keypoints)}点")
                        return True
            except Exception:
                pass

        cache_path = user_cache_path(cache_path.name)
        source = self.cv_read_image(self.active_map_path())
        if source is None:
            QMessageBox.warning(self, "AI小地图跟随", "无法读取地图底图生成识别缓存。")
            return False
        height, width = source.shape[:2]
        scale = min(1.0, SIFT_REFERENCE_MAX_SIDE / max(width, height))
        if scale < 1.0:
            ref = cv2.resize(source, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
        else:
            ref = source
        gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            keypoints, descriptors = detector.detectAndCompute(gray, None)
        finally:
            QApplication.restoreOverrideCursor()
        if descriptors is None or len(keypoints) < SIFT_MIN_MATCHES:
            QMessageBox.warning(self, "AI小地图跟随", "地图底图可识别特征太少，无法生成缓存。")
            return False
        pts = np.array([kp.pt for kp in keypoints], dtype=np.float32)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            np.savez_compressed(
                str(cache_path),
                method=np.array(method),
                source_w=np.array(width),
                source_h=np.array(height),
                scale=np.array(scale),
                pts=pts,
                desc=descriptors,
            )
        except Exception:
            pass
        self.sift_ref_image = ref
        self.sift_ref_scale = scale
        self.sift_keypoints = pts
        self.sift_descriptors = descriptors
        self.sift_matcher = self.create_sift_matcher()
        self.sift_ready = True
        if self.minimap_follow_status_label is not None:
            self.minimap_follow_status_label.setText(f"{method}缓存已生成：{len(pts)}点")
        return True

    def minimap_feature_image_and_mask(self, image, player_local):
        bgr = self.qimage_to_bgr(image)
        if bgr is None:
            return None, None
        height, width = bgr.shape[:2]
        center = (width // 2, height // 2)
        radius = int(min(width, height) * 0.38)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)

        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        orange = cv2.inRange(hsv, (5, 70, 110), (35, 255, 255))
        white = cv2.inRange(hsv, (0, 0, 205), (180, 70, 255))
        player_mask = cv2.bitwise_or(orange, white)
        player_mask = cv2.dilate(player_mask, np.ones((9, 9), np.uint8), iterations=1)
        px, py = int(player_local[0]), int(player_local[1])
        cv2.circle(player_mask, (px, py), int(min(width, height) * 0.15), 255, -1)
        mask[player_mask > 0] = 0
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        return gray, mask

    def track_minimap_sift(self, image, player_local):
        if not self.sift_ready and not self.prepare_sift_tracker():
            return None, 0, 0
        detector, method = self.create_feature_detector()
        if detector is None or self.sift_descriptors is None or self.sift_matcher is None:
            return None, 0, 0
        gray, mask = self.minimap_feature_image_and_mask(image, player_local)
        if gray is None:
            return None, 0, 0
        keypoints, descriptors = detector.detectAndCompute(gray, mask)
        if descriptors is None or len(keypoints) < SIFT_MIN_MATCHES:
            return None, 0, 0
        try:
            matches = self.sift_matcher.knnMatch(descriptors, self.sift_descriptors, k=2)
        except Exception:
            return None, 0, 0
        good = []
        for pair in matches:
            if len(pair) < 2:
                continue
            first, second = pair
            if first.distance < SIFT_RATIO_TEST * second.distance:
                good.append(first)
        if len(good) < SIFT_MIN_MATCHES:
            return None, len(good), 0
        src = np.float32([keypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst = np.float32([self.sift_keypoints[m.trainIdx] for m in good]).reshape(-1, 1, 2)
        homography, inlier_mask = cv2.findHomography(src, dst, cv2.RANSAC, SIFT_RANSAC_REPROJ)
        if homography is None or inlier_mask is None:
            return None, len(good), 0
        inliers = int(inlier_mask.ravel().sum())
        if inliers < SIFT_MIN_MATCHES:
            return None, len(good), inliers
        player_point = np.float32([[[player_local[0], player_local[1]]]])
        mapped = cv2.perspectiveTransform(player_point, homography)[0][0]
        world_x = float(mapped[0] / self.sift_ref_scale)
        world_y = float(mapped[1] / self.sift_ref_scale)
        if self.minimap_last_world_pos is not None:
            jump = math.hypot(world_x - self.minimap_last_world_pos[0], world_y - self.minimap_last_world_pos[1])
            if jump > SIFT_MAX_WORLD_JUMP:
                return None, len(good), inliers
        return (world_x, world_y), len(good), inliers

    def update_minimap_follow(self):
        if not self.minimap_circle_locked:
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText("固定小地图圈后才会开始识别")
            return
        if self.minimap_circle_region is None:
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText("请先选择小地图范围")
            return
        pixmap = self.capture_minimap_region()
        if pixmap is None or pixmap.isNull():
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText("无法截图小地图范围")
            return
        image = pixmap.toImage().convertToFormat(QImage.Format_RGB32)
        player_local, detected_player = self.detect_minimap_player(image)
        if not self.minimap_calibrated:
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText("请先把导航地图中心对准角色位置，然后点击校准到地图中心")
            return
        world_pos, match_count, inliers = self.track_minimap_sift(image, player_local)
        if world_pos is None:
            self.minimap_tracking_failures += 1
            if self.minimap_last_world_pos is not None:
                self.set_route_preview_player_position(self.minimap_last_world_pos[0], self.minimap_last_world_pos[1])
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText(f"SIFT未定位，保持上次位置  匹配:{match_count} 内点:{inliers}")
            return
        if self.minimap_last_world_pos is not None:
            jump = math.hypot(
                world_pos[0] - self.minimap_last_world_pos[0],
                world_pos[1] - self.minimap_last_world_pos[1],
            )
            if jump > MINIMAP_MAX_WORLD_JUMP:
                self.set_route_preview_player_position(self.minimap_last_world_pos[0], self.minimap_last_world_pos[1])
                if self.minimap_follow_status_label is not None:
                    self.minimap_follow_status_label.setText("已忽略一次异常跳变")
                return
        self.minimap_last_world_pos = world_pos
        self.minimap_tracking_failures = 0
        self.set_route_preview_player_position(world_pos[0], world_pos[1])
        if self.minimap_follow_status_label is not None:
            player_text = "角色点" if detected_player else "中心点"
            self.minimap_follow_status_label.setText(
                f"SIFT跟随：{player_text}  匹配:{match_count} 内点:{inliers}"
            )

    def capture_minimap_region(self):
        region = self.minimap_circle_region
        if region is None:
            return None
        circle_visible = self.minimap_circle is not None and self.minimap_circle.isVisible()
        if circle_visible:
            self.minimap_circle.hide()
            QApplication.processEvents()
        screen = QApplication.primaryScreen()
        pixmap = None
        if screen is not None:
            pixmap = screen.grabWindow(0, region["x"], region["y"], region["size"], region["size"])
        if circle_visible and self.minimap_circle is not None:
            self.minimap_circle.show()
            if self.minimap_circle_locked:
                self.minimap_circle.set_locked_for_game(True)
        return pixmap

    def detect_minimap_player(self, image):
        width = image.width()
        height = image.height()
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) * 0.34
        orange_weight = 0
        orange_x = 0
        orange_y = 0
        for y in range(max(0, int(center_y - radius)), min(height, int(center_y + radius))):
            dy = y - center_y
            for x in range(max(0, int(center_x - radius)), min(width, int(center_x + radius))):
                dx = x - center_x
                if dx * dx + dy * dy > radius * radius:
                    continue
                pixel = image.pixel(x, y)
                red = (pixel >> 16) & 255
                green = (pixel >> 8) & 255
                blue = pixel & 255
                is_orange = red > 210 and 105 <= green <= 205 and blue < 125 and red - green > 28 and green - blue > 35
                is_white_edge = red > 230 and green > 225 and blue > 205 and abs(dx) < radius * 0.45 and abs(dy) < radius * 0.45
                if is_orange:
                    weight = 5 + red - blue
                elif is_white_edge:
                    weight = 1
                else:
                    continue
                orange_weight += weight
                orange_x += x * weight
                orange_y += y * weight
        if orange_weight > 1200:
            return (orange_x / orange_weight, orange_y / orange_weight), True
        return (center_x, center_y), False

    def ensure_minimap_match_map(self):
        if self.minimap_match_map_image is not None:
            return True
        if hasattr(self, "map_item"):
            source_pixmap = self.map_item.pixmap()
        else:
            source_pixmap = QPixmap(str(self.active_map_path()))
        if source_pixmap.isNull():
            return False
        scaled = source_pixmap.scaled(
            MINIMAP_MATCH_SIZE,
            MINIMAP_MATCH_SIZE,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.minimap_match_map_image = scaled.toImage().convertToFormat(QImage.Format_RGB32)
        self.minimap_match_scale_x = source_pixmap.width() / max(1, self.minimap_match_map_image.width())
        self.minimap_match_scale_y = source_pixmap.height() / max(1, self.minimap_match_map_image.height())
        return True

    def minimap_template_features(self, image, player_local):
        template = image.scaled(
            MINIMAP_TEMPLATE_SIZE,
            MINIMAP_TEMPLATE_SIZE,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation,
        ).convertToFormat(QImage.Format_RGB32)
        player_x = player_local[0] * MINIMAP_TEMPLATE_SIZE / max(1, image.width())
        player_y = player_local[1] * MINIMAP_TEMPLATE_SIZE / max(1, image.height())
        center = MINIMAP_TEMPLATE_SIZE / 2
        radius = MINIMAP_TEMPLATE_SIZE * 0.34
        features = []
        for y in range(6, MINIMAP_TEMPLATE_SIZE - 6, 4):
            for x in range(6, MINIMAP_TEMPLATE_SIZE - 6, 4):
                if (x - center) ** 2 + (y - center) ** 2 > radius * radius:
                    continue
                if (x - player_x) ** 2 + (y - player_y) ** 2 < 196:
                    continue
                pixel = template.pixel(x, y)
                red = (pixel >> 16) & 255
                green = (pixel >> 8) & 255
                blue = pixel & 255
                total = red + green + blue + 1
                chroma_red = int(red * 255 / total)
                chroma_green = int(green * 255 / total)
                chroma_blue = int(blue * 255 / total)
                luma = (red + green + blue) // 3
                features.append((x, y, chroma_red, chroma_green, chroma_blue, luma))
        return features, player_x, player_y

    def minimap_tracking_features(self, image, player_local):
        width = image.width()
        height = image.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) * 0.34
        player_x, player_y = player_local
        features = []
        for y in range(int(center_y - radius), int(center_y + radius), MINIMAP_TRACK_SAMPLE_STEP):
            if y < 0 or y >= height:
                continue
            for x in range(int(center_x - radius), int(center_x + radius), MINIMAP_TRACK_SAMPLE_STEP):
                if x < 0 or x >= width:
                    continue
                if (x - center_x) ** 2 + (y - center_y) ** 2 > radius * radius:
                    continue
                if (x - player_x) ** 2 + (y - player_y) ** 2 < 24 * 24:
                    continue
                pixel = image.pixel(x, y)
                red = (pixel >> 16) & 255
                green = (pixel >> 8) & 255
                blue = pixel & 255
                total = red + green + blue + 1
                features.append(
                    (
                        x,
                        y,
                        int(red * 255 / total),
                        int(green * 255 / total),
                        int(blue * 255 / total),
                        (red + green + blue) // 3,
                    )
                )
        return features

    def tracking_pixel_error(self, image, x, y, chroma_red, chroma_green, chroma_blue, luma):
        pixel = image.pixel(x, y)
        red = (pixel >> 16) & 255
        green = (pixel >> 8) & 255
        blue = pixel & 255
        total = red + green + blue + 1
        return (
            abs(chroma_red - int(red * 255 / total))
            + abs(chroma_green - int(green * 255 / total))
            + abs(chroma_blue - int(blue * 255 / total))
            + abs(luma - ((red + green + blue) // 3)) * 0.12
        )

    def minimap_motion_features(self, image, player_local):
        width = image.width()
        height = image.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) * 0.36
        player_x, player_y = player_local
        features = []
        for y in range(int(center_y - radius), int(center_y + radius), MINIMAP_MOTION_SAMPLE_STEP):
            if y < 2 or y >= height - 2:
                continue
            for x in range(int(center_x - radius), int(center_x + radius), MINIMAP_MOTION_SAMPLE_STEP):
                if x < 2 or x >= width - 2:
                    continue
                if (x - center_x) ** 2 + (y - center_y) ** 2 > radius * radius:
                    continue
                if (x - player_x) ** 2 + (y - player_y) ** 2 < 28 * 28:
                    continue
                pixel = image.pixel(x, y)
                red = (pixel >> 16) & 255
                green = (pixel >> 8) & 255
                blue = pixel & 255
                luma = (red + green + blue) // 3
                right = image.pixel(x + 2, y)
                down = image.pixel(x, y + 2)
                right_luma = (((right >> 16) & 255) + ((right >> 8) & 255) + (right & 255)) // 3
                down_luma = (((down >> 16) & 255) + ((down >> 8) & 255) + (down & 255)) // 3
                contrast = abs(luma - right_luma) + abs(luma - down_luma)
                saturation = max(red, green, blue) - min(red, green, blue)
                weight = contrast + saturation * 0.12
                if weight < 8:
                    continue
                total = red + green + blue + 1
                features.append(
                    (
                        x,
                        y,
                        int(red * 255 / total),
                        int(green * 255 / total),
                        int(blue * 255 / total),
                        luma,
                        min(4.0, max(1.0, weight / 18)),
                    )
                )
        features.sort(key=lambda item: item[-1], reverse=True)
        return features[:520]

    def match_minimap_motion(self, previous, current, player_local):
        features = self.minimap_motion_features(previous, player_local)
        if len(features) < 24:
            return None
        width = current.width()
        height = current.height()
        best_dx = 0
        best_dy = 0
        best_score = float("inf")
        zero_score = None
        for dy in range(-MINIMAP_MOTION_SEARCH_RADIUS, MINIMAP_MOTION_SEARCH_RADIUS + 1):
            for dx in range(-MINIMAP_MOTION_SEARCH_RADIUS, MINIMAP_MOTION_SEARCH_RADIUS + 1):
                weighted_error = 0.0
                total_weight = 0.0
                valid = 0
                for x, y, chroma_red, chroma_green, chroma_blue, luma, weight in features:
                    target_x = x + dx
                    target_y = y + dy
                    if target_x < 0 or target_x >= width or target_y < 0 or target_y >= height:
                        continue
                    weighted_error += self.tracking_pixel_error(
                        current,
                        target_x,
                        target_y,
                        chroma_red,
                        chroma_green,
                        chroma_blue,
                        luma,
                    ) * weight
                    total_weight += weight
                    valid += 1
                    if total_weight > 0 and weighted_error / total_weight > best_score + 12:
                        break
                if valid < len(features) * 0.68 or total_weight <= 0:
                    continue
                score = weighted_error / total_weight
                if dx == 0 and dy == 0:
                    zero_score = score
                if score < best_score:
                    best_score = score
                    best_dx = dx
                    best_dy = dy
        if zero_score is None:
            zero_score = best_score
        return best_dx, best_dy, best_score, zero_score, len(features)

    def track_minimap_incremental(self, image, player_local):
        if self.minimap_previous_image is None or self.minimap_last_world_pos is None:
            self.minimap_previous_image = image
            self.minimap_previous_player_local = player_local
            return self.minimap_last_world_pos, 0
        result = self.match_minimap_motion(self.minimap_previous_image, image, self.minimap_previous_player_local or player_local)
        if result is None:
            return None, 0
        dx, dy, score, zero_score, feature_count = result
        movement = math.hypot(dx, dy)
        improvement = zero_score - score
        if movement >= 0.5 and (score > MINIMAP_MOTION_BAD_SCORE or improvement < MINIMAP_MOTION_MIN_IMPROVEMENT):
            return None, score
        if movement < 0.5:
            self.minimap_previous_image = image
            self.minimap_previous_player_local = player_local
            return self.minimap_last_world_pos, score

        last_x, last_y = self.minimap_last_world_pos
        world_x = last_x - dx * self.minimap_world_pixels_per_minimap_pixel
        world_y = last_y - dy * self.minimap_world_pixels_per_minimap_pixel
        if math.hypot(world_x - last_x, world_y - last_y) > MINIMAP_MAX_WORLD_JUMP:
            return None, score
        self.minimap_previous_image = image
        self.minimap_previous_player_local = player_local
        return (world_x, world_y), score

    def match_minimap_near_world(self, image, player_local, anchor_world, radius_world=MINIMAP_CORRECTION_RADIUS):
        if anchor_world is None or not self.ensure_minimap_match_map():
            return None, float("inf"), 0
        features, player_x, player_y = self.minimap_template_features(image, player_local)
        if not features:
            return None, float("inf"), 0
        map_image = self.minimap_match_map_image
        max_x = map_image.width() - MINIMAP_TEMPLATE_SIZE
        max_y = map_image.height() - MINIMAP_TEMPLATE_SIZE
        anchor_x = int(anchor_world[0] / self.minimap_match_scale_x - player_x)
        anchor_y = int(anchor_world[1] / self.minimap_match_scale_y - player_y)
        radius_x = max(4, int(radius_world / self.minimap_match_scale_x))
        radius_y = max(4, int(radius_world / self.minimap_match_scale_y))
        start_x = max(0, anchor_x - radius_x)
        end_x = min(max_x, anchor_x + radius_x)
        start_y = max(0, anchor_y - radius_y)
        end_y = min(max_y, anchor_y + radius_y)
        best_x = anchor_x
        best_y = anchor_y
        best_error = float("inf")
        second_error = float("inf")
        step = 2
        for y in range(start_y, end_y + 1, step):
            for x in range(start_x, end_x + 1, step):
                error = 0
                for fx, fy, chroma_red, chroma_green, chroma_blue, luma in features:
                    pixel = map_image.pixel(x + fx, y + fy)
                    red = (pixel >> 16) & 255
                    green = (pixel >> 8) & 255
                    blue = pixel & 255
                    total = red + green + blue + 1
                    error += abs(chroma_red - int(red * 255 / total))
                    error += abs(chroma_green - int(green * 255 / total))
                    error += abs(chroma_blue - int(blue * 255 / total))
                    error += abs(luma - ((red + green + blue) // 3)) * 0.18
                    if error >= best_error:
                        break
                if error < best_error:
                    second_error = best_error
                    best_error = error
                    best_x = x
                    best_y = y
                elif error < second_error:
                    second_error = error
        score = best_error / max(1, len(features))
        margin = (second_error - best_error) / max(1, len(features)) if second_error < float("inf") else 99
        if score > MINIMAP_CORRECTION_BAD_SCORE or margin < MINIMAP_CORRECTION_MIN_MARGIN:
            return None, score, margin
        world_x = (best_x + player_x) * self.minimap_match_scale_x
        world_y = (best_y + player_y) * self.minimap_match_scale_y
        return (world_x, world_y), score, margin

    def blend_world_positions(self, predicted, corrected):
        if predicted is None:
            return corrected
        if corrected is None:
            return predicted
        distance = math.hypot(corrected[0] - predicted[0], corrected[1] - predicted[1])
        if distance > MINIMAP_CORRECTION_RADIUS * 1.25:
            return predicted
        correction_weight = 0.35 if distance < 120 else 0.2
        return (
            predicted[0] * (1 - correction_weight) + corrected[0] * correction_weight,
            predicted[1] * (1 - correction_weight) + corrected[1] * correction_weight,
        )

    def track_minimap_hybrid(self, image, player_local):
        last_pos = self.minimap_last_world_pos
        predicted, motion_score = self.track_minimap_incremental(image, player_local)
        correction_anchor = predicted or last_pos
        corrected, correction_score, margin = self.match_minimap_near_world(image, player_local, correction_anchor)
        if predicted is None and corrected is None:
            return None, motion_score or correction_score
        if predicted is None:
            self.minimap_previous_image = image
            self.minimap_previous_player_local = player_local
            return corrected, correction_score
        blended = self.blend_world_positions(predicted, corrected)
        return blended, correction_score if corrected is not None else motion_score

    def shifted_minimap_image(self, image, dx, dy):
        shifted = QImage(image.size(), QImage.Format_RGB32)
        shifted.fill(QColor("#000000"))
        painter = QPainter(shifted)
        painter.drawImage(dx, dy, image)
        painter.end()
        return shifted

    def selftest_minimap_motion(self, image, player_local):
        previous_image = self.minimap_previous_image
        previous_player = self.minimap_previous_player_local
        last_world = self.minimap_last_world_pos
        ok = True
        for dx, dy in ((8, 0), (-7, 5), (0, -8)):
            shifted = self.shifted_minimap_image(image, dx, dy)
            result = self.match_minimap_motion(image, shifted, player_local)
            if result is None:
                ok = False
                break
            found_dx, found_dy, score, zero_score, feature_count = result
            if abs(found_dx - dx) > 2 or abs(found_dy - dy) > 2:
                ok = False
                break
        self.minimap_previous_image = previous_image
        self.minimap_previous_player_local = previous_player
        self.minimap_last_world_pos = last_world
        return ok

    def track_minimap_from_calibration(self, image, player_local):
        if (
            not self.minimap_calibrated
            or self.minimap_reference_image is None
            or self.minimap_reference_player_local is None
            or self.minimap_reference_world_pos is None
        ):
            return None, 0
        reference = self.minimap_reference_image
        features = self.minimap_tracking_features(reference, self.minimap_reference_player_local)
        if len(features) < 20:
            return None, 0

        width = image.width()
        height = image.height()
        best_dx = 0
        best_dy = 0
        best_score = float("inf")
        second_score = float("inf")
        for dy in range(-MINIMAP_TRACK_SEARCH_RADIUS, MINIMAP_TRACK_SEARCH_RADIUS + 1, MINIMAP_TRACK_STEP):
            for dx in range(-MINIMAP_TRACK_SEARCH_RADIUS, MINIMAP_TRACK_SEARCH_RADIUS + 1, MINIMAP_TRACK_STEP):
                total_error = 0
                count = 0
                for x, y, chroma_red, chroma_green, chroma_blue, luma in features:
                    target_x = x + dx
                    target_y = y + dy
                    if target_x < 0 or target_x >= width or target_y < 0 or target_y >= height:
                        continue
                    total_error += self.tracking_pixel_error(
                        image,
                        target_x,
                        target_y,
                        chroma_red,
                        chroma_green,
                        chroma_blue,
                        luma,
                    )
                    count += 1
                if count < len(features) * 0.65:
                    continue
                score = total_error / count
                if score < best_score:
                    second_score = best_score
                    best_score = score
                    best_dx = dx
                    best_dy = dy
                elif score < second_score:
                    second_score = score

        if best_score > MINIMAP_TRACK_BAD_SCORE:
            return None, best_score
        if second_score < float("inf") and second_score - best_score < 2.5:
            return None, best_score

        ref_x, ref_y = self.minimap_reference_world_pos
        world_x = ref_x - best_dx * self.minimap_world_pixels_per_minimap_pixel
        world_y = ref_y - best_dy * self.minimap_world_pixels_per_minimap_pixel
        return (world_x, world_y), best_score

    def minimap_search_anchors(self):
        anchors = []
        if self.minimap_last_world_pos is not None:
            anchors.append((self.minimap_last_world_pos[0], self.minimap_last_world_pos[1], MINIMAP_LOCAL_SEARCH_RADIUS, 2))
        current = self.current_route_marker()
        if current is not None:
            anchors.append((current["x"], current["y"], MINIMAP_ANCHOR_SEARCH_RADIUS, MINIMAP_MATCH_STEP))
        if self.route_preview_view is not None:
            center = self.route_preview_view.mapToScene(self.route_preview_view.viewport().rect().center())
            anchors.append((center.x(), center.y(), MINIMAP_ANCHOR_SEARCH_RADIUS, MINIMAP_MATCH_STEP))
        if hasattr(self, "view"):
            center = self.view.mapToScene(self.view.viewport().rect().center())
            anchors.append((center.x(), center.y(), MINIMAP_ANCHOR_SEARCH_RADIUS, MINIMAP_MATCH_STEP))
        return anchors

    def match_minimap_to_world(self, image, player_local):
        if not self.ensure_minimap_match_map():
            return None, 0
        features, player_x, player_y = self.minimap_template_features(image, player_local)
        if not features:
            return None, 0
        map_image = self.minimap_match_map_image
        max_x = map_image.width() - MINIMAP_TEMPLATE_SIZE
        max_y = map_image.height() - MINIMAP_TEMPLATE_SIZE
        if max_x <= 0 or max_y <= 0:
            return None, 0

        ranges = []
        anchors = self.minimap_search_anchors()
        for anchor_x, anchor_y, radius, step in anchors:
            last_x = int(anchor_x / self.minimap_match_scale_x - player_x)
            last_y = int(anchor_y / self.minimap_match_scale_y - player_y)
            ranges.append(
                (
                    max(0, last_x - radius),
                    min(max_x, last_x + radius),
                    max(0, last_y - radius),
                    min(max_y, last_y + radius),
                    step,
                )
            )
        if not ranges:
            ranges.append((0, max_x, 0, max_y, MINIMAP_MATCH_STEP))

        best_x = 0
        best_y = 0
        best_error = float("inf")
        for start_x, end_x, start_y, end_y, step in ranges:
            for y in range(start_y, end_y + 1, step):
                for x in range(start_x, end_x + 1, step):
                    error = 0
                    for fx, fy, chroma_red, chroma_green, chroma_blue, luma in features:
                        pixel = map_image.pixel(x + fx, y + fy)
                        red = (pixel >> 16) & 255
                        green = (pixel >> 8) & 255
                        blue = pixel & 255
                        total = red + green + blue + 1
                        map_chroma_red = int(red * 255 / total)
                        map_chroma_green = int(green * 255 / total)
                        map_chroma_blue = int(blue * 255 / total)
                        map_luma = (red + green + blue) // 3
                        error += abs(chroma_red - map_chroma_red)
                        error += abs(chroma_green - map_chroma_green)
                        error += abs(chroma_blue - map_chroma_blue)
                        error += abs(luma - map_luma) * 0.18
                        if error >= best_error:
                            break
                    if error < best_error:
                        best_error = error
                        best_x = x
                        best_y = y

        world_x = (best_x + player_x) * self.minimap_match_scale_x
        world_y = (best_y + player_y) * self.minimap_match_scale_y
        normalized_score = best_error / max(1, len(features))
        if normalized_score > MINIMAP_BAD_SCORE:
            return None, normalized_score
        return (world_x, world_y), normalized_score

    def set_route_preview_player_position(self, x, y, angle=None):
        if self.route_preview_scene is None:
            return
        item = self.route_preview_player_item
        if item is None:
            player_path = QPainterPath()
            player_path.moveTo(0, -29)
            player_path.lineTo(24, 29)
            player_path.lineTo(0, 16)
            player_path.lineTo(-24, 29)
            player_path.closeSubpath()
            item = QGraphicsPathItem(player_path)
            item.setPen(QPen(QColor("#fff8dc"), 8))
            item.setBrush(QBrush(QColor("#ff9826")))
            item.setZValue(9)
            item.setAcceptedMouseButtons(Qt.NoButton)
            self.route_preview_scene.addItem(item)
            self.route_preview_player_item = item
            self._sift_v2_player_item = item

        target = (float(x), float(y))
        self.route_preview_player_target_pos = target
        if angle is not None:
            self.route_preview_player_target_angle = float(angle) % 360.0
        now = time.monotonic()
        display = self.route_preview_player_display_pos
        if display is None:
            display = target
            self.route_preview_player_display_pos = display
            self.route_preview_player_angle = self.route_preview_player_target_angle
            self.route_preview_player_last_update_at = now
        else:
            target_delta = math.hypot(target[0] - display[0], target[1] - display[1])
            if target_delta < 0.45:
                target = display
                self.route_preview_player_target_pos = target
            else:
                self.route_preview_player_motion = []
        self.animate_route_preview_player()
        if not self.route_preview_player_animation_timer.isActive():
            self.route_preview_player_animation_timer.start()

    def route_preview_player_motion_position(self, now):
        frames = getattr(self, "route_preview_player_motion", [])
        if not frames:
            return None
        elapsed = max(0.0, now - self.route_preview_player_motion_started_at)
        if elapsed >= frames[-1].time:
            frame = frames[-1]
            self.route_preview_player_motion = []
            return (frame.x, frame.y), frame.angle, True
        for index in range(1, len(frames)):
            frame = frames[index]
            if frame.time >= elapsed:
                previous = frames[index - 1]
                span = max(0.001, frame.time - previous.time)
                local = (elapsed - previous.time) / span
                x = previous.x + (frame.x - previous.x) * local
                y = previous.y + (frame.y - previous.y) * local
                angle_diff = ((frame.angle - previous.angle + 180.0) % 360.0) - 180.0
                angle = (previous.angle + angle_diff * local) % 360.0
                return (x, y), angle, False
        frame = frames[-1]
        self.route_preview_player_motion = []
        return (frame.x, frame.y), frame.angle, True

    def animate_route_preview_player(self):
        item = self.route_preview_player_item
        target = self.route_preview_player_target_pos
        if item is None or target is None:
            if self.route_preview_player_animation_timer.isActive():
                self.route_preview_player_animation_timer.stop()
            return
        now = time.monotonic()
        display = self.route_preview_player_display_pos or target
        dt = max(0.001, min(0.05, now - (self.route_preview_player_last_update_at or now)))
        motion = self.route_preview_player_motion_position(now)
        if motion is not None:
            display, motion_angle, motion_done = motion
            self.route_preview_player_target_angle = motion_angle
        else:
            dx = target[0] - display[0]
            dy = target[1] - display[1]
            distance = math.hypot(dx, dy)
            if distance < 0.25:
                display = target
            else:
                alpha = min(0.98, max(0.32, 1.0 - math.exp(-dt * 34.0)))
                display = (display[0] + dx * alpha, display[1] + dy * alpha)

        target_angle = float(self.route_preview_player_target_angle)
        current_angle = float(self.route_preview_player_angle)
        diff = ((target_angle - current_angle + 180.0) % 360.0) - 180.0
        if abs(diff) < 0.8:
            current_angle = target_angle
        else:
            angle_alpha = min(0.995, max(0.68, 1.0 - math.exp(-dt * 120.0)))
            current_angle = (current_angle + diff * angle_alpha) % 360.0

        self.route_preview_player_display_pos = display
        self.route_preview_player_angle = current_angle
        self.route_preview_player_last_update_at = now
        item.setRotation(self.route_preview_player_angle)
        item.setPos(display[0], display[1])
        item.setVisible(True)
        if (
            not getattr(self, "route_preview_player_motion", [])
            and display == target
            and abs(((target_angle - current_angle + 180.0) % 360.0) - 180.0) < 0.8
        ):
            self.route_preview_player_animation_timer.stop()

    def clear_route_preview_player_position(self):
        if self.route_preview_scene is not None and self.route_preview_player_item is not None:
            self.route_preview_scene.removeItem(self.route_preview_player_item)
        if getattr(self, "_sift_v2_player_item", None) is self.route_preview_player_item:
            self._sift_v2_player_item = None
        self.route_preview_player_item = None
        self.route_preview_player_display_pos = None
        self.route_preview_player_target_pos = None
        self.route_preview_player_motion = []
        self.route_preview_player_motion_started_at = 0.0
        self.route_preview_player_last_update_at = 0.0
        if self.route_preview_player_animation_timer.isActive():
            self.route_preview_player_animation_timer.stop()

    def marker_title(self, marker):
        return marker.get("title") or marker.get("name") or marker.get("label") or marker.get("mark_type") or "未命名"

    def serialize_route_point(self, marker):
        if is_manual_route_point(marker):
            return {
                "kind": "manual",
                "uid": route_point_uid(marker),
                "title": self.marker_title(marker),
                "x": float(marker["x"]),
                "y": float(marker["y"]),
                "layer": normalize_map_layer(marker.get("layer")),
            }
        return {
            "kind": "marker",
            "uid": route_point_uid(marker),
        }

    def route_points_from_payload(self, payload):
        raw_route = []
        if isinstance(payload, dict):
            raw_route = (
                payload.get("routePoints")
                or payload.get("routeMarkers")
                or payload.get("markers")
                or payload.get("uids")
                or payload.get("route")
                or []
            )
        elif isinstance(payload, list):
            raw_route = payload
        if not isinstance(raw_route, list):
            return []

        title_index = {}
        for marker in self.markers:
            title = self.marker_title(marker)
            title_index.setdefault(title, []).append(marker["uid"])

        route_points = []
        seen_resource_uids = set()
        for entry in raw_route:
            if isinstance(entry, str):
                marker = self.markers_by_uid.get(entry)
                if marker is not None and entry not in seen_resource_uids:
                    seen_resource_uids.add(entry)
                    route_points.append(marker)
                continue

            if not isinstance(entry, dict):
                continue
            kind = str(entry.get("kind") or entry.get("routePointKind") or "").lower()
            uid = str(entry.get("uid") or entry.get("id") or "")
            if uid in self.markers_by_uid and kind != "manual":
                if uid not in seen_resource_uids:
                    seen_resource_uids.add(uid)
                    route_points.append(self.markers_by_uid[uid])
                continue

            if kind != "manual":
                title = entry.get("title") or entry.get("name") or entry.get("label")
                candidates = title_index.get(title or "", [])
                if len(candidates) == 1 and candidates[0] not in seen_resource_uids:
                    seen_resource_uids.add(candidates[0])
                    route_points.append(self.markers_by_uid[candidates[0]])
                    continue

            if "x" in entry and "y" in entry:
                try:
                    x = float(entry["x"])
                    y = float(entry["y"])
                except Exception:
                    continue
                route_points.append(self.create_manual_route_point(
                    x,
                    y,
                    title=entry.get("title") or entry.get("name") or entry.get("label"),
                    uid=uid if uid.startswith(MANUAL_ROUTE_UID_PREFIX) else None,
                    layer=entry.get("layer") or self.current_layer,
                ))
        return route_points

    def save_route_state(self):
        route_resource_uids = [
            route_point_uid(marker)
            for marker in self.route_markers
            if route_point_uid(marker) in self.markers_by_uid
        ]
        route_point_uids = {route_point_uid(marker) for marker in self.route_markers}
        payload = {
            "version": 1,
            "accountId": self.account_id,
            "accountName": self.account_name,
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
            "completedMarkers": sorted(
                uid for uid in self.completed_route_uids
                if uid in self.markers_by_uid or uid in route_point_uids
            ),
            "routeMarkers": route_resource_uids,
            "routePoints": [self.serialize_route_point(marker) for marker in self.route_markers],
            "currentRouteIndex": max(0, min(self.current_route_index, len(self.route_markers))),
        }
        write_json(account_data_path(self.account_id, "user_route_progress.json"), payload)

    def restore_route_from_state(self):
        self.route_markers = self.route_points_from_payload(self.route_state)
        route_point_uids = {route_point_uid(marker) for marker in self.route_markers}
        self.completed_route_uids = {
            uid for uid in self.completed_route_uids
            if uid in self.markers_by_uid or uid in route_point_uids
        }
        index = self.route_state.get("currentRouteIndex", self.route_state.get("currentIndex", 0))
        try:
            index = int(index)
        except Exception:
            index = 0
        self.current_route_index = max(0, min(index, len(self.route_markers)))
        self.clear_route_path()
        self.advance_route_index()
        self.update_route_transition_hints()
        self.refresh_route_tree()
        self.render_route_path()

    def route_candidate_markers(self):
        candidates = []
        seen = set()
        for marker in self.visible_markers():
            uid = marker["uid"]
            if uid in seen or uid in self.dimmed_uids or uid in self.completed_route_uids:
                continue
            seen.add(uid)
            candidates.append(marker)
        return candidates

    def generate_route_from_visible(self):
        candidates = self.route_candidate_markers()
        if not candidates:
            QMessageBox.information(self, "跑图导航", "当前筛选下没有可以生成路线的资源。")
            return

        cache_key = self.route_cache_key(candidates)
        cached_route = self.load_cached_route(cache_key)
        if cached_route is None and len(candidates) > ROUTE_GENERATION_CANDIDATE_LIMIT:
            QMessageBox.warning(
                self,
                "跑图导航",
                (
                    f"当前有 {len(candidates)} 个候选点，超过安全生成上限 "
                    f"{ROUTE_GENERATION_CANDIDATE_LIMIT} 个。\n\n"
                    "请先隐藏不需要的资源类型，或只勾选一种/几种资源后再生成路线，"
                    "这样可以避免窗口卡死。"
                ),
            )
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            if cached_route is not None:
                self.route_markers = cached_route
            else:
                self.route_markers = self.build_optimized_route(candidates)
                self.save_cached_route(cache_key, self.route_markers)
        finally:
            QApplication.restoreOverrideCursor()
        self.current_route_index = 0
        self.update_route_transition_hints()
        self.route_auto_complete_candidate_uid = None
        self.route_auto_complete_candidate_hits = 0
        self.route_auto_complete_candidate_started_at = 0.0
        self.advance_route_index()
        self.refresh_route_tree()
        self.render_route_path()
        self.focus_current_route_marker()
        self.save_route_state()
        self.start_route_background_optimization(cache_key, candidates, self.route_markers)
        self.update_status()

    def route_cache_key(self, candidates):
        payload = {
            "source": DATA_PATH.name,
            "routeVersion": 3,
            "layer": self.current_layer,
            "markerUids": sorted(marker["uid"] for marker in candidates),
            "teleportTypes": sorted(ROUTE_TELEPORT_MARK_TYPES),
            "teleportFixedCost": ROUTE_TELEPORT_FIXED_COST,
            "teleportMinGain": ROUTE_TELEPORT_MIN_GAIN,
            "teleportMaxExitDistance": ROUTE_TELEPORT_MAX_EXIT_DISTANCE,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def load_cached_route(self, cache_key):
        route = self.route_cache.get("routes", {}).get(cache_key)
        if not isinstance(route, dict):
            return None
        route_uids = route.get("routeMarkers")
        if not isinstance(route_uids, list) or not route_uids:
            return None
        markers = []
        seen = set()
        for uid in route_uids:
            marker = self.markers_by_uid.get(uid)
            if marker is None or uid in seen:
                return None
            if (
                marker.get("mark_type") not in self.visible_types
                or not self.marker_matches_current_layer(marker)
                or uid in self.dimmed_uids
                or uid in self.completed_route_uids
            ):
                return None
            seen.add(uid)
            markers.append(marker)
        return markers

    def save_cached_route(self, cache_key, route_markers):
        routes = self.route_cache.setdefault("routes", {})
        routes[cache_key] = {
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
            "routeMarkers": [marker["uid"] for marker in route_markers],
        }
        if len(routes) > 30:
            oldest = sorted(
                routes,
                key=lambda key: routes[key].get("updatedAt", ""),
            )[: len(routes) - 30]
            for key in oldest:
                routes.pop(key, None)
        write_json(ROUTE_CACHE_PATH, self.route_cache)

    def start_route_background_optimization(self, cache_key, candidates, route_markers):
        if len(candidates) < 4 or len(candidates) > ROUTE_BACKGROUND_OPTIMIZATION_LIMIT:
            return
        self.route_background_job = {
            "cacheKey": cache_key,
            "candidates": list(candidates),
            "bestRoute": list(route_markers),
            "bestCost": self.route_path_cost(route_markers),
            "startedAt": time.monotonic(),
            "passes": 0,
            "pairs": itertools.cycle(self.route_background_pairs(len(route_markers))),
        }
        if not self.route_background_timer.isActive():
            self.route_background_timer.start()

    def route_background_pairs(self, count):
        pairs = []
        for span in range(2, min(count, 28)):
            for left in range(0, count - span):
                pairs.append((left, left + span))
        return pairs or [(0, count - 1)]

    def run_route_background_step(self):
        job = self.route_background_job
        if not job:
            self.route_background_timer.stop()
            return
        if time.monotonic() - job["startedAt"] > ROUTE_BACKGROUND_MAX_SECONDS:
            self.route_background_job = None
            self.route_background_timer.stop()
            return
        deadline = time.perf_counter() + ROUTE_BACKGROUND_WORK_MS / 1000.0
        route = job["bestRoute"]
        improved = False
        while time.perf_counter() < deadline:
            left, right = next(job["pairs"])
            if right >= len(route):
                continue
            candidate = route[:left] + list(reversed(route[left : right + 1])) + route[right + 1 :]
            candidate_cost = self.route_path_cost(candidate)
            if candidate_cost + 0.001 < job["bestCost"]:
                route = candidate
                job["bestRoute"] = route
                job["bestCost"] = candidate_cost
                improved = True
                break
        job["passes"] += 1
        if improved:
            self.save_cached_route(job["cacheKey"], route)
            self.update_status()

    def squared_distance(self, first, second):
        return (first["x"] - second["x"]) ** 2 + (first["y"] - second["y"]) ** 2

    def route_distance(self, first, second):
        return math.hypot(first["x"] - second["x"], first["y"] - second["y"])

    def route_distance_to_point(self, marker, x, y):
        return math.hypot(marker["x"] - x, marker["y"] - y)

    def route_teleport_markers(self):
        cache = self.route_teleport_marker_cache
        if cache is not None and cache[0] == len(self.markers) and cache[1] == self.current_layer:
            return cache[2]
        teleports = [
            marker for marker in self.markers
            if marker.get("mark_type") in ROUTE_TELEPORT_MARK_TYPES
            and self.marker_matches_current_layer(marker)
        ]
        self.route_teleport_marker_cache = (len(self.markers), self.current_layer, teleports)
        return teleports

    def nearest_route_teleport(self, marker):
        cache_key = (
            self.current_layer,
            len(self.markers),
            marker.get("uid") or marker.get("id") or id(marker),
            round(float(marker["x"]), 3),
            round(float(marker["y"]), 3),
        )
        cached = self.route_nearest_teleport_cache.get(cache_key)
        if cached is not None:
            return cached
        teleports = self.route_teleport_markers()
        if not teleports:
            result = (None, float("inf"))
            self.route_nearest_teleport_cache[cache_key] = result
            return result
        best = min(
            teleports,
            key=lambda teleport: (teleport["x"] - marker["x"]) ** 2 + (teleport["y"] - marker["y"]) ** 2,
        )
        result = (best, self.route_distance(best, marker))
        self.route_nearest_teleport_cache[cache_key] = result
        return result

    def route_transition_plan(self, previous, marker):
        cache_key = (
            self.current_layer,
            previous.get("uid"), marker.get("uid"),
            round(float(previous["x"]), 3), round(float(previous["y"]), 3),
            round(float(marker["x"]), 3), round(float(marker["y"]), 3),
            len(self.markers),
        )
        cached = self.route_transition_cache.get(cache_key)
        if cached is not None:
            return cached
        direct = self.route_distance(previous, marker)
        teleport, exit_distance = self.nearest_route_teleport(marker)
        if teleport is None or exit_distance > ROUTE_TELEPORT_MAX_EXIT_DISTANCE:
            plan = {
                "mode": "walk",
                "cost": direct,
                "direct": direct,
                "teleport": None,
                "exit_distance": exit_distance,
            }
            self.route_transition_cache[cache_key] = plan
            return plan
        teleport_cost = ROUTE_TELEPORT_FIXED_COST + exit_distance
        if direct - teleport_cost >= ROUTE_TELEPORT_MIN_GAIN:
            plan = {
                "mode": "teleport",
                "cost": teleport_cost,
                "direct": direct,
                "teleport": teleport,
                "exit_distance": exit_distance,
            }
            self.route_transition_cache[cache_key] = plan
            return plan
        plan = {
            "mode": "walk",
            "cost": direct,
            "direct": direct,
            "teleport": teleport,
            "exit_distance": exit_distance,
        }
        self.route_transition_cache[cache_key] = plan
        return plan

    def route_travel_cost(self, previous, marker):
        return self.route_transition_plan(previous, marker)["cost"]

    def route_total_distance(self, route, start_x, start_y):
        if not route:
            return 0.0
        total = self.route_distance_to_point(route[0], start_x, start_y)
        for index in range(1, len(route)):
            total += self.route_distance(route[index - 1], route[index])
        return total

    def route_path_distance(self, route):
        total = 0.0
        for index in range(1, len(route)):
            total += self.route_distance(route[index - 1], route[index])
        return total

    def route_path_cost(self, route):
        total = 0.0
        for index in range(1, len(route)):
            total += self.route_travel_cost(route[index - 1], route[index])
        return total

    def update_route_transition_hints(self):
        self.route_transition_hints = {}
        for index in range(len(self.route_markers) - 1):
            previous = self.route_markers[index]
            marker = self.route_markers[index + 1]
            plan = self.route_transition_plan(previous, marker)
            if plan.get("mode") == "teleport":
                self.route_transition_hints[route_point_uid(previous)] = plan

    def build_nearest_route(self, candidates, start_index):
        unvisited = list(candidates)
        current = unvisited.pop(start_index)
        route = [current]
        while unvisited:
            current_x = current["x"]
            current_y = current["y"]
            best_index = min(
                range(len(unvisited)),
                key=lambda index: self.route_travel_cost(current, unvisited[index]),
            )
            current = unvisited.pop(best_index)
            route.append(current)
        return route

    def route_seed_indices(self, candidates):
        count = len(candidates)
        if count <= ROUTE_ALL_START_LIMIT:
            return list(range(count))
        seeds = set()
        key_funcs = (
            lambda marker: marker["x"],
            lambda marker: -marker["x"],
            lambda marker: marker["y"],
            lambda marker: -marker["y"],
            lambda marker: marker["x"] + marker["y"],
            lambda marker: -(marker["x"] + marker["y"]),
            lambda marker: marker["x"] - marker["y"],
            lambda marker: marker["y"] - marker["x"],
        )
        for key_func in key_funcs:
            seeds.add(min(range(count), key=lambda index: key_func(candidates[index])))
        center_x = sum(marker["x"] for marker in candidates) / count
        center_y = sum(marker["y"] for marker in candidates) / count
        seeds.add(max(range(count), key=lambda index: (candidates[index]["x"] - center_x) ** 2 + (candidates[index]["y"] - center_y) ** 2))
        while len(seeds) < min(ROUTE_GREEDY_START_CANDIDATES, count):
            seeds.add(max(
                range(count),
                key=lambda index: min(
                    (candidates[index]["x"] - candidates[seed]["x"]) ** 2
                    + (candidates[index]["y"] - candidates[seed]["y"]) ** 2
                    for seed in seeds
                ),
            ))
        return list(seeds)

    def build_optimized_route(self, candidates, start_x=None, start_y=None):
        if len(candidates) <= 1:
            return list(candidates)

        self.route_transition_cache = {}
        self.route_nearest_teleport_cache = {}
        deadline = time.perf_counter() + ROUTE_OPTIMIZE_TIME_BUDGET_SECONDS
        if len(candidates) <= ROUTE_EXACT_LIMIT:
            return self.build_exact_open_route(candidates)

        best_route = None
        best_distance = float("inf")
        seed_routes = []
        for candidate_start_index in self.route_seed_indices(candidates):
            route = self.build_nearest_route(candidates, candidate_start_index)
            seed_routes.append((self.route_path_cost(route), route))
            QApplication.processEvents()
            if time.perf_counter() > deadline and seed_routes:
                break
        seed_routes.sort(key=lambda item: item[0])
        for _, route in seed_routes[: min(ROUTE_DEEP_OPTIMIZE_CANDIDATES, len(seed_routes))]:
            if time.perf_counter() > deadline:
                break
            route = self.optimize_route_open(route, deadline)
            distance = self.route_path_cost(route)
            if distance < best_distance:
                best_distance = distance
                best_route = route
        if best_route is not None:
            return best_route
        if seed_routes:
            return seed_routes[0][1]
        return list(candidates)

    def build_exact_open_route(self, candidates):
        points = list(candidates)
        count = len(points)
        full_mask = (1 << count) - 1
        states = {(1 << index, index): (0.0, None) for index in range(count)}

        for mask in range(1 << count):
            for last in range(count):
                state = states.get((mask, last))
                if state is None:
                    continue
                current_cost = state[0]
                for next_index in range(count):
                    bit = 1 << next_index
                    if mask & bit:
                        continue
                    next_mask = mask | bit
                    next_cost = current_cost + self.route_travel_cost(points[last], points[next_index])
                    old_state = states.get((next_mask, next_index))
                    if old_state is None or next_cost < old_state[0]:
                        states[(next_mask, next_index)] = (next_cost, last)

        best_last = min(
            range(count),
            key=lambda last: states.get((full_mask, last), (float("inf"), None))[0],
        )
        order = []
        mask = full_mask
        last = best_last
        while last is not None:
            order.append(last)
            _, previous = states[(mask, last)]
            mask &= ~(1 << last)
            last = previous
        order.reverse()
        return [points[index] for index in order]

    def build_exact_route(self, candidates, start_index):
        points = list(candidates)
        count = len(points)
        start_mask = 1 << start_index
        states = {(start_mask, start_index): (0.0, None)}
        full_mask = (1 << count) - 1

        for mask in range(1 << count):
            if not mask & start_mask:
                continue
            for last in range(count):
                state = states.get((mask, last))
                if state is None:
                    continue
                current_cost = state[0]
                for next_index in range(count):
                    bit = 1 << next_index
                    if mask & bit:
                        continue
                    next_mask = mask | bit
                    next_cost = current_cost + self.route_distance(points[last], points[next_index])
                    old_state = states.get((next_mask, next_index))
                    if old_state is None or next_cost < old_state[0]:
                        states[(next_mask, next_index)] = (next_cost, last)

        best_last = min(
            range(count),
            key=lambda last: states.get((full_mask, last), (float("inf"), None))[0],
        )
        order = []
        mask = full_mask
        last = best_last
        while last is not None:
            order.append(last)
            cost, previous = states[(mask, last)]
            mask &= ~(1 << last)
            last = previous
        order.reverse()
        return [points[index] for index in order]

    def two_opt_route(self, route):
        if len(route) < 4:
            return list(route)
        route = list(route)
        for _ in range(ROUTE_TWO_OPT_PASSES):
            improved = False
            for left in range(1, len(route) - 2):
                left_prev = route[left - 1]
                left_item = route[left]
                original_left = self.route_distance(left_prev, left_item)
                for right in range(left + 1, len(route) - 1):
                    right_item = route[right]
                    right_next = route[right + 1]
                    old_distance = original_left + self.route_distance(right_item, right_next)
                    new_distance = self.route_distance(left_prev, right_item) + self.route_distance(left_item, right_next)
                    if new_distance + 0.001 < old_distance:
                        route[left : right + 1] = reversed(route[left : right + 1])
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                break
        return route

    def optimize_route_open(self, route, deadline=None):
        if len(route) < 4:
            return list(route)
        route = list(route)
        if len(route) > ROUTE_GLOBAL_TWO_OPT_LIMIT:
            optimized = []
            for offset in range(0, len(route), ROUTE_TWO_OPT_CHUNK):
                chunk = route[offset : offset + ROUTE_TWO_OPT_CHUNK]
                if optimized and chunk:
                    bridge_index = min(
                        range(len(chunk)),
                        key=lambda index: self.squared_distance(optimized[-1], chunk[index]),
                    )
                    chunk = chunk[bridge_index:] + chunk[:bridge_index]
                optimized.extend(self.two_opt_route(chunk))
            return optimized

        for _ in range(ROUTE_TWO_OPT_PASSES):
            improved = False
            current_cost = self.route_path_cost(route)
            for left in range(0, len(route) - 1):
                if deadline is not None and time.perf_counter() > deadline:
                    return route
                old_internal = 0.0
                new_internal = 0.0
                for right in range(left + 1, len(route)):
                    if deadline is not None and (right & 31) == 0 and time.perf_counter() > deadline:
                        return route
                    old_internal += self.route_travel_cost(route[right - 1], route[right])
                    new_internal += self.route_travel_cost(route[right], route[right - 1])
                    old_boundary = old_internal
                    new_boundary = new_internal
                    if left > 0:
                        previous = route[left - 1]
                        old_boundary += self.route_travel_cost(previous, route[left])
                        new_boundary += self.route_travel_cost(previous, route[right])
                    if right + 1 < len(route):
                        next_item = route[right + 1]
                        old_boundary += self.route_travel_cost(route[right], next_item)
                        new_boundary += self.route_travel_cost(route[left], next_item)
                    candidate_cost = current_cost - old_boundary + new_boundary
                    if candidate_cost + 0.001 < current_cost:
                        route[left : right + 1] = reversed(route[left : right + 1])
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                break
        return route

    def optimize_route_from_start(self, route, start_x, start_y):
        return self.optimize_route_open(route)

    def advance_route_index(self):
        while self.current_route_index < len(self.route_markers):
            marker = self.route_markers[self.current_route_index]
            if not self.route_point_completed(marker):
                break
            self.current_route_index += 1

    def current_route_marker(self):
        self.advance_route_index()
        for marker in self.route_markers[self.current_route_index:]:
            if (
                self.route_point_matches_current_layer(marker)
                and not self.route_point_completed(marker)
            ):
                return marker
        return None

    def clear_route_path(self):
        if self.route_path_item is not None and hasattr(self, "scene"):
            try:
                self.scene.removeItem(self.route_path_item)
            except RuntimeError:
                pass
        self.route_path_item = None
        if self.route_arrow_item is not None and hasattr(self, "scene"):
            try:
                self.scene.removeItem(self.route_arrow_item)
            except RuntimeError:
                pass
        self.route_arrow_item = None
        for item in getattr(self, "route_helper_marker_items", []):
            if hasattr(self, "scene"):
                try:
                    self.scene.removeItem(item)
                except RuntimeError:
                    pass
        self.route_helper_marker_items = []

    def refresh_route_overlay(self):
        if getattr(self, "tearing_down", False):
            return
        self.refresh_route_tree()
        self.render_route_path()
        self.update_status()

    def request_marker_rebuild(self):
        self.marker_rebuild_timer.start()
        self.update_status()

    def apply_deferred_marker_rebuild(self):
        self.rebuild_marker_tiles()
        self.refresh_route_overlay()

    def route_remaining_markers(self, limit=None):
        self.advance_route_index()
        markers = []
        for marker in self.route_markers[self.current_route_index:]:
            if not self.route_point_matches_current_layer(marker):
                continue
            if self.route_point_completed(marker):
                continue
            markers.append(marker)
            if limit is not None and len(markers) >= limit:
                break
        return markers

    def route_remaining_steps(self, limit=None):
        route_limit = None
        if limit is not None:
            route_limit = max(1, limit)
        markers = self.route_remaining_markers(route_limit)
        steps = []
        for index, marker in enumerate(markers):
            if index > 0:
                previous = markers[index - 1]
                plan = self.route_transition_plan(previous, marker)
                teleport = plan.get("teleport") if plan.get("mode") == "teleport" else None
                if teleport is not None and self.marker_matches_current_layer(teleport):
                    if not steps or route_point_uid(steps[-1][0]) != route_point_uid(teleport):
                        steps.append((teleport, "teleport"))
            if not steps or route_point_uid(steps[-1][0]) != route_point_uid(marker):
                steps.append((marker, "manual" if is_manual_route_point(marker) else "resource"))
            if limit is not None and len(steps) >= limit:
                break
        return steps

    def route_preview_markers(self, limit=None):
        markers = []
        seen = set()

        def add_marker(marker):
            uid = marker.get("uid")
            if not uid or uid in seen:
                return
            if not self.marker_matches_current_layer(marker):
                return
            seen.add(uid)
            markers.append(marker)

        visible_route_markers = [
            marker
            for marker in self.route_markers
            if self.route_point_matches_current_layer(marker)
        ]
        for index, marker in enumerate(visible_route_markers):
            add_marker(marker)
            if index + 1 < len(visible_route_markers):
                plan = self.route_transition_plan(marker, visible_route_markers[index + 1])
                teleport = plan.get("teleport") if plan.get("mode") == "teleport" else None
                if teleport is not None:
                    add_marker(teleport)
            if limit is not None and len(markers) >= limit:
                break
        return markers

    def render_route_path(self):
        self.clear_route_path()
        if not hasattr(self, "scene"):
            return
        steps = self.route_remaining_steps(ROUTE_DRAW_LIMIT)
        markers = [marker for marker, _kind in steps]
        for marker, kind in steps:
            if kind not in ("teleport", "manual"):
                continue
            pixmap = self.route_preview_icon_pixmap(marker)
            if pixmap.isNull():
                continue
            item = QGraphicsPixmapItem(pixmap)
            item.setScale(self.route_point_pixmap_scale(marker, pixmap))
            offset_x, offset_y = self.route_point_pixmap_offset(marker, pixmap)
            item.setOffset(offset_x, offset_y)
            item.setPos(marker["x"], marker["y"])
            item.setZValue(8)
            item.setAcceptedMouseButtons(Qt.NoButton)
            item.setData(0, marker.get("uid"))
            self.scene.addItem(item)
            self.route_helper_marker_items.append(item)
        if len(markers) < 2:
            return
        path = QPainterPath()
        arrow_path = QPainterPath()
        path.moveTo(markers[0]["x"], markers[0]["y"])
        for index, marker in enumerate(markers[1:], start=1):
            previous = markers[index - 1]
            path.lineTo(marker["x"], marker["y"])
            if index % ROUTE_ARROW_STEP == 0 or index == 1 or index == len(markers) - 1:
                self.add_route_arrow(arrow_path, previous, marker)
        pen = QPen(QColor("#ff7a00"), 3)
        pen.setCosmetic(True)
        self.route_path_item = QGraphicsPathItem(path)
        self.route_path_item.setPen(pen)
        self.route_path_item.setZValue(6)
        self.route_path_item.setAcceptedMouseButtons(Qt.NoButton)
        self.scene.addItem(self.route_path_item)
        arrow_pen = QPen(QColor("#00a7ff"), 4)
        arrow_pen.setCosmetic(True)
        self.route_arrow_item = QGraphicsPathItem(arrow_path)
        self.route_arrow_item.setPen(arrow_pen)
        self.route_arrow_item.setZValue(7)
        self.route_arrow_item.setAcceptedMouseButtons(Qt.NoButton)
        self.scene.addItem(self.route_arrow_item)

    def add_route_arrow(self, path, previous, marker):
        dx = marker["x"] - previous["x"]
        dy = marker["y"] - previous["y"]
        length = math.hypot(dx, dy)
        if length < 1:
            return
        unit_x = dx / length
        unit_y = dy / length
        tip_x = previous["x"] + dx * 0.62
        tip_y = previous["y"] + dy * 0.62
        back_x = tip_x - unit_x * ROUTE_ARROW_SIZE
        back_y = tip_y - unit_y * ROUTE_ARROW_SIZE
        side_x = -unit_y * ROUTE_ARROW_SIZE * 0.42
        side_y = unit_x * ROUTE_ARROW_SIZE * 0.42
        path.moveTo(back_x + side_x, back_y + side_y)
        path.lineTo(tip_x, tip_y)
        path.lineTo(back_x - side_x, back_y - side_y)

    def refresh_route_tree(self):
        self.update_route_transition_hints()
        remaining = self.route_remaining_markers()
        visible_route_markers = [
            marker
            for marker in self.route_markers
            if self.route_point_matches_current_layer(marker)
        ]
        completed = sum(1 for marker in self.route_markers if self.route_point_completed(marker))
        current = remaining[0] if remaining else None

        if not self.route_markers:
            status_text = "未生成路线"
        elif current is None:
            status_text = f"路线已完成  已完成 {completed}"
        else:
            extra = "" if len(remaining) <= ROUTE_LIST_LIMIT else f"  列表显示前 {ROUTE_LIST_LIMIT} 个"
            status_text = f"剩余 {len(remaining)} / 路线 {len(self.route_markers)}  当前：{self.marker_title(current)}{extra}"

        for label in (getattr(self, "route_status_label", None), getattr(self, "route_dialog_status_label", None)):
            if label is not None:
                label.setText(status_text)

        trees = []
        side_tree = getattr(self, "route_tree", None)
        if side_tree is not None and side_tree.isVisible():
            trees.append(side_tree)
        dialog_tree = getattr(self, "route_dialog_tree", None)
        if dialog_tree is not None:
            trees.append(dialog_tree)
        for tree in trees:
            if tree is None:
                continue
            tree.blockSignals(True)
            tree.clear()
            for display_index, marker in enumerate(visible_route_markers[:ROUTE_LIST_LIMIT], start=1):
                prefix = "▶ " if marker is current else ""
                title = self.marker_title(marker)
                category = marker.get("group") or marker.get("category") or marker.get("mark_type") or ""
                item = QTreeWidgetItem([f"{prefix}{display_index}. {title}", str(category)])
                item.setToolTip(0, f"{display_index}. {title}")
                item.setToolTip(1, str(category))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                if self.route_point_completed(marker):
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)
                item.setData(0, Qt.UserRole, route_point_uid(marker))
                tree.addTopLevelItem(item)
                plan = self.route_transition_hints.get(route_point_uid(marker))
                if plan is not None:
                    teleport = plan.get("teleport")
                    if teleport is not None:
                        teleport_text = (
                            f"   传送到 {self.marker_title(teleport)}，"
                            f"落点约 {int(plan.get('exit_distance', 0))} 距离"
                        )
                        hint_item = QTreeWidgetItem([teleport_text, "传送"])
                        hint_item.setToolTip(0, teleport_text)
                        hint_item.setToolTip(1, "传送")
                        hint_item.setData(0, Qt.UserRole, "")
                        tree.addTopLevelItem(hint_item)
            tree.blockSignals(False)
        self.update_route_preview()

    def tracked_player_position(self):
        for name in (
            "minimap_last_world_pos",
            "_sift_v2_last_world",
            "route_preview_player_world_pos",
            "player_world_pos",
            "current_world_pos",
        ):
            value = getattr(self, name, None)
            if value:
                try:
                    return float(value[0]), float(value[1])
                except Exception:
                    pass
        item = getattr(self, "route_preview_player_item", None)
        if item is not None:
            try:
                center = item.sceneBoundingRect().center()
                return center.x(), center.y()
            except Exception:
                pass
        return None

    def focus_current_player_position(self):
        pos = self.tracked_player_position()
        if pos is None:
            if self.minimap_follow_status_label is not None:
                self.minimap_follow_status_label.setText("还没有识别到当前位置，请先校准或开启小地图跟随")
            else:
                QMessageBox.information(self, "跑图导航", "还没有识别到当前位置，请先校准或开启小地图跟随。")
            return
        self._last_focus_player_position = pos
        if self.route_preview_scene is not None:
            self.set_route_preview_player_position(pos[0], pos[1])
        if self.route_preview_view is not None:
            self.route_preview_view.centerOn(pos[0], pos[1])
        elif hasattr(self, "view"):
            self.view.centerOn(pos[0], pos[1])

    def focus_route_start_marker(self):
        marker = next(
            (
                marker
                for marker in self.route_markers
                if self.route_point_matches_current_layer(marker)
            ),
            None,
        )
        if marker is None:
            QMessageBox.information(self, "跑图导航", "目前没有路线源头。")
            return
        if self.route_preview_view is not None:
            self.route_preview_view.centerOn(marker["x"], marker["y"])
        else:
            self.focus_marker(marker)
        if self.route_dialog_tree is not None and self.route_dialog_tree.topLevelItemCount() > 0:
            self.route_dialog_tree.setCurrentItem(self.route_dialog_tree.topLevelItem(0))

    def focus_current_route_marker(self):
        marker = self.current_route_marker()
        if marker is None:
            message = "目前没有路线。" if not self.route_markers else "当前路线已经跑完。"
            QMessageBox.information(self, "跑图导航", message)
            self.refresh_route_tree()
            self.render_route_path()
            self.save_route_state()
            return
        self.focus_marker(marker)
        self.refresh_route_tree()
        self.render_route_path()
        self.save_route_state()

    def auto_complete_route_at_position(self, x, y):
        now = time.monotonic()
        marker = self.current_route_marker()
        if marker is None:
            self.route_auto_complete_candidate_uid = None
            self.route_auto_complete_candidate_hits = 0
            self.route_auto_complete_candidate_started_at = 0.0
            return False
        uid = route_point_uid(marker)
        if self.route_point_completed(marker):
            self.route_auto_complete_candidate_uid = None
            self.route_auto_complete_candidate_hits = 0
            self.route_auto_complete_candidate_started_at = 0.0
            return False
        distance = math.hypot(marker["x"] - x, marker["y"] - y)
        if distance > ROUTE_AUTO_COMPLETE_RADIUS:
            self.route_auto_complete_candidate_uid = None
            self.route_auto_complete_candidate_hits = 0
            self.route_auto_complete_candidate_started_at = 0.0
            return False
        if self.route_auto_complete_candidate_uid == uid:
            self.route_auto_complete_candidate_hits += 1
        else:
            self.route_auto_complete_candidate_uid = uid
            self.route_auto_complete_candidate_hits = 1
            self.route_auto_complete_candidate_started_at = now
        self.route_auto_complete_last_seen_at = now
        if self.route_auto_complete_candidate_hits < ROUTE_AUTO_COMPLETE_REQUIRED_HITS:
            return False
        if now - self.route_auto_complete_candidate_started_at < ROUTE_AUTO_COMPLETE_DWELL_SECONDS:
            return False
        self.route_auto_complete_candidate_uid = None
        self.route_auto_complete_candidate_hits = 0
        self.route_auto_complete_candidate_started_at = 0.0
        self.completed_route_uids.add(uid)
        if not is_manual_route_point(marker):
            self.dimmed_uids.add(uid)
        self.current_route_index += 1
        self.advance_route_index()
        self.rebuild_marker_tiles()
        self.pending_save.start()
        self.refresh_route_tree()
        self.render_route_path()
        self.save_route_state()
        self.update_status()
        return True

    def complete_current_route_marker(self):
        marker = self.current_route_marker()
        if marker is None:
            message = "目前没有路线。" if not self.route_markers else "当前路线已经跑完。"
            QMessageBox.information(self, "跑图导航", message)
            return
        self.route_auto_complete_candidate_uid = None
        self.route_auto_complete_candidate_hits = 0
        self.route_auto_complete_candidate_started_at = 0.0
        uid = route_point_uid(marker)
        self.completed_route_uids.add(uid)
        if not is_manual_route_point(marker):
            self.dimmed_uids.add(uid)
        self.current_route_index += 1
        self.advance_route_index()
        self.rebuild_marker_tiles()
        self.pending_save.start()
        self.refresh_route_tree()
        self.render_route_path()
        self.focus_current_route_marker()
        self.save_route_state()
        self.update_status()

    def clear_route(self):
        self.route_markers = []
        self.current_route_index = 0
        self.route_transition_hints = {}
        if self.route_background_timer.isActive():
            self.route_background_timer.stop()
        self.route_background_job = None
        self.route_auto_complete_candidate_uid = None
        self.route_auto_complete_candidate_hits = 0
        self.route_auto_complete_candidate_started_at = 0.0
        self.clear_route_path()
        self.clear_highlight()
        self.refresh_route_tree()
        self.save_route_state()
        self.update_status()

    def import_route_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "导入导航",
            str(PROJECT_DIR),
            "导航文件 (*.json);;所有文件 (*.*)",
        )
        if not file_name:
            return
        try:
            payload = read_json(Path(file_name))
            route_points = self.route_points_from_payload(payload)
        except Exception as error:
            QMessageBox.warning(self, "导入导航", f"导入失败：{error}")
            return
        if not route_points:
            QMessageBox.information(self, "导入导航", "没有在文件中找到可用的路线点。")
            return
        self.route_markers = route_points
        self.current_route_index = 0
        self.advance_route_index()
        self.refresh_route_tree()
        self.render_route_path()
        self.focus_current_route_marker()
        self.save_route_state()
        self.update_status()

    def export_route_file(self):
        if not self.route_markers:
            QMessageBox.information(self, "保存导航", "当前没有可以保存的路线。")
            return False
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "保存导航",
            str(PROJECT_DIR / "我的跑图路线.json"),
            "导航文件 (*.json);;所有文件 (*.*)",
        )
        if not file_name:
            return False
        path = Path(file_name)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")
        payload = {
            "version": 1,
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "routeMarkers": [
                route_point_uid(marker)
                for marker in self.route_markers
                if route_point_uid(marker) in self.markers_by_uid
            ],
            "routePoints": [self.serialize_route_point(marker) for marker in self.route_markers],
            "markers": [
                {
                    "uid": route_point_uid(marker),
                    "kind": "manual" if is_manual_route_point(marker) else "marker",
                    "title": self.marker_title(marker),
                    "category": marker.get("group") or marker.get("category") or marker.get("mark_type") or "",
                    "x": marker["x"],
                    "y": marker["y"],
                }
                for marker in self.route_markers
            ],
        }
        write_json(path, payload)
        return True

    def toggle_manual_route_mode(self):
        if not self.manual_route_mode:
            self.manual_route_mode = True
            if self.manual_route_button is not None:
                self.manual_route_button.setText("结束规划")
            self.route_markers = []
            self.current_route_index = 0
            self.clear_route_path()
            self.refresh_route_tree()
            self.update_status()
            QMessageBox.information(self, "自行规划路线", "已进入自行规划路线模式，左键点击地图任意位置即可按顺序加入路线。")
            return

        save_box = QMessageBox(self)
        save_box.setWindowTitle("自行规划路线")
        save_box.setText("是否保存当前规划路线为导航文件？")
        save_box.setIcon(QMessageBox.Question)
        save_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        save_box.setDefaultButton(QMessageBox.Yes)
        save_box.button(QMessageBox.Yes).setText("是")
        save_box.button(QMessageBox.No).setText("不保存")
        save_box.button(QMessageBox.Cancel).setText("取消")
        choice = save_box.exec_()
        if choice == QMessageBox.Cancel:
            return

        self.manual_route_mode = False
        if self.manual_route_button is not None:
            self.manual_route_button.setText("自行规划路线")
        if choice == QMessageBox.Yes:
            if not self.export_route_file():
                self.manual_route_mode = True
                if self.manual_route_button is not None:
                    self.manual_route_button.setText("结束规划")
                return
        else:
            pass
        self.save_route_state()
        self.refresh_route_tree()
        self.render_route_path()
        self.update_status()

    def add_marker_to_manual_route(self, marker):
        point = self.create_manual_route_point(marker["x"], marker["y"], title=self.marker_title(marker), layer=marker.get("layer"))
        self.route_markers.append(point)
        if len(self.route_markers) == 1:
            self.current_route_index = 0
        self.refresh_route_tree()
        self.render_route_path()
        self.update_status()

    def on_route_item_check_changed(self, item, column):
        if column != 0:
            return
        uid = item.data(0, Qt.UserRole)
        marker = self.route_point_by_uid(uid)
        if marker is None:
            return
        self.route_auto_complete_candidate_uid = None
        self.route_auto_complete_candidate_hits = 0
        self.route_auto_complete_candidate_started_at = 0.0
        if item.checkState(0) == Qt.Checked:
            self.completed_route_uids.add(uid)
            if not is_manual_route_point(marker):
                self.dimmed_uids.add(uid)
        else:
            self.completed_route_uids.discard(uid)
            if not is_manual_route_point(marker):
                self.dimmed_uids.discard(uid)
            for index, route_marker in enumerate(self.route_markers):
                if route_point_uid(route_marker) == uid:
                    self.current_route_index = min(self.current_route_index, index)
                    break
        self.advance_route_index()
        self.rebuild_marker_tiles()
        self.pending_save.start()
        self.refresh_route_tree()
        self.render_route_path()
        self.save_route_state()
        self.update_status()

    def open_route_marker_detail(self, marker):
        self.open_marker_detail(marker)
        if self.detail_windows:
            self.detail_windows[-1].raise_()
            self.detail_windows[-1].activateWindow()

    def on_route_item_clicked(self, item, column):
        uid = item.data(0, Qt.UserRole)
        marker = self.route_point_by_uid(uid)
        if marker is None:
            return
        for index, marker in enumerate(self.route_markers):
            if route_point_uid(marker) == uid:
                if not self.route_point_completed(marker):
                    self.current_route_index = index
                break
        self.advance_route_index()
        marker = self.route_point_by_uid(uid)
        self.focus_marker(marker)
        self.refresh_route_tree()
        self.render_route_path()
        self.save_route_state()

    def update_status(self):
        if getattr(self, "tearing_down", False):
            return
        visible_signature = (self.current_layer, tuple(sorted(self.visible_types)))
        if getattr(self, "_route_visible_signature", None) != visible_signature:
            self._route_visible_signature = visible_signature
            if getattr(self, "route_markers", None):
                QTimer.singleShot(0, self.refresh_route_overlay)
        visible = self.visible_markers()
        visible_dimmed = sum(1 for marker in visible if marker["uid"] in self.dimmed_uids)
        active = len(visible) - visible_dimmed
        scale = getattr(getattr(self, "view", None), "current_scale", INITIAL_SCALE)
        self.status_label.setText(
            f"账号：{self.account_name}  {map_layer_label(self.current_layer)}  "
            f"显示 {len(visible)}  未暗淡 {active}  比例 {scale * 100:.0f}%"
        )
        layer_types = {
            mark_type
            for mark_type, info in self.resource_types.items()
            if self.resource_type_count_for_layer(info) > 0
        }
        visible_layer_types = self.visible_types & layer_types
        self.filter_status.setText(f"{len(visible_layer_types)}/{len(layer_types)} 类资源")

    def on_tree_item_changed(self, _item, _column):
        if self.updating_tree or self.search_mode:
            return
        layer_types = {
            mark_type
            for mark_type, info in self.resource_types.items()
            if self.resource_type_count_for_layer(info) > 0
        }
        visible = set(self.visible_types) - layer_types
        for mark_type, item in self.tree_items_by_type.items():
            if item.checkState(0) == Qt.Checked:
                visible.add(mark_type)
        self.visible_types = visible
        self.apply_marker_visibility()

    def on_tree_item_clicked(self, item, _column):
        data = item.data(0, Qt.UserRole)
        if not isinstance(data, dict) or data.get("kind") != "search_result":
            return
        uid = data.get("uid")
        marker = next((item for item in self.markers if item["uid"] == uid), None)
        if marker is None:
            return
        self.focus_marker(marker)
        self.open_marker_detail(marker)

    def apply_marker_visibility(self):
        self.request_marker_rebuild()
        self.update_status()

    def set_all_filters(self, checked):
        self.updating_tree = True
        state = Qt.Checked if checked else Qt.Unchecked
        for index in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(index).setCheckState(0, state)
        for mark_type, item in self.tree_items_by_type.items():
            item.setCheckState(0, state)
        self.updating_tree = False
        layer_types = {
            mark_type
            for mark_type, info in self.resource_types.items()
            if self.resource_type_count_for_layer(info) > 0
        }
        if checked:
            self.visible_types = set(self.visible_types) | layer_types
        else:
            self.visible_types = set(self.visible_types) - layer_types
        self.apply_marker_visibility()

    def toggle_marker(self, uid):
        if uid in self.dimmed_uids:
            self.dimmed_uids.remove(uid)
        else:
            self.dimmed_uids.add(uid)
        self.rebuild_marker_tiles()
        self.pending_save.start()
        self.update_status()

    def save_state(self):
        write_json(account_data_path(self.account_id, "user_dimmed_markers.json"), {
            "source": DATA_PATH.name,
            "accountId": self.account_id,
            "accountName": self.account_name,
            "dimmedMarkers": sorted(self.dimmed_uids),
        })

    def restore_all(self):
        if self.search_input.text():
            self.search_input.clear()
        self.search_mode = False
        self.visible_types = set(self.resource_types)
        self.dimmed_uids.clear()
        self.completed_route_uids.clear()
        self.route_markers = []
        self.current_route_index = 0
        self.clear_route_path()
        self.refresh_route_tree()
        self.save_route_state()
        self.populate_filter_tree()
        self.rebuild_marker_tiles()
        self.fit_to_window()
        self.pending_save.start()
        self.update_status()

    def zoom_by(self, factor):
        next_scale = min(MAX_SCALE, max(MIN_SCALE, self.view.current_scale * factor))
        if abs(next_scale - self.view.current_scale) < 0.001:
            return
        factor = next_scale / self.view.current_scale
        self.view.current_scale = next_scale
        self.view.scale(factor, factor)
        self.update_status()

    def zoom_100(self):
        factor = 1.0 / self.view.current_scale
        self.view.current_scale = 1.0
        self.view.scale(factor, factor)
        self.update_status()

    def fit_to_window(self):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        fitted_scale = self.view.transform().m11()
        if fitted_scale < MIN_SCALE:
            transform = QTransform()
            transform.scale(MIN_SCALE, MIN_SCALE)
            self.view.setTransform(transform)
            self.view.current_scale = MIN_SCALE
            self.view.centerOn(self.map_item.boundingRect().center())
        else:
            self.view.current_scale = fitted_scale
        self.update_status()

    def note_record_for(self, marker):
        return self.notes_payload.setdefault("markers", {}).setdefault(marker["note_key"], {
            "description": "",
            "messages": [],
            "images": [],
        })

    def save_notes(self):
        self.notes_payload["accountId"] = self.account_id
        self.notes_payload["accountName"] = self.account_name
        self.notes_payload["updatedAt"] = datetime.now().isoformat(timespec="seconds")
        write_json(account_data_path(self.account_id, "user_marker_notes.json"), self.notes_payload)

    def marker_detail_for(self, marker):
        source_point_id = marker.get("source_point_id")
        if source_point_id is None:
            return {}
        return self.marker_details_payload.get("details", {}).get(str(source_point_id), {})

    def category_options(self):
        seen = OrderedDict()
        for info in self.resource_types.values():
            seen.setdefault(info["name"], None)
        return list(seen)

    def open_marker_detail(self, marker):
        for dialog in list(self.detail_windows):
            if dialog.marker["note_key"] == marker["note_key"]:
                dialog.raise_()
                dialog.activateWindow()
                return
            dialog.close()
        dialog = DetailDialog(
            self,
            marker,
            self.marker_detail_for(marker),
            self.note_record_for(marker),
            self.save_notes,
            self.open_submission_dialog,
        )
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.setWindowModality(Qt.NonModal)
        self.detail_windows.append(dialog)
        dialog.finished.connect(lambda _result, dialog=dialog: self.forget_detail_window(dialog))
        dialog.destroyed.connect(lambda _obj=None, dialog=dialog: self.forget_detail_window(dialog))
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def forget_detail_window(self, dialog):
        if dialog in self.detail_windows:
            self.detail_windows.remove(dialog)

    def open_submission_dialog(self, marker, detail):
        dialog = ReviewSubmissionDialog(
            self,
            marker,
            detail,
            self.category_options(),
            self.submit_marker_review,
        )
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        self.submission_windows.append(dialog)
        dialog.finished.connect(lambda _result, dialog=dialog: self.forget_submission_window(dialog))
        dialog.destroyed.connect(lambda _obj=None, dialog=dialog: self.forget_submission_window(dialog))
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def forget_submission_window(self, dialog):
        if dialog in self.submission_windows:
            self.submission_windows.remove(dialog)

    def submit_marker_review(self, marker, proposal):
        submission_id = uuid.uuid4().hex
        uploaded_images = []
        target_dir = SUBMISSION_UPLOADS_DIR / submission_id
        for index, image_path_text in enumerate(proposal.get("imagePaths", []), start=1):
            source = Path(image_path_text)
            if not source.exists() or source.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{index:02d}_{uuid.uuid4().hex[:8]}{source.suffix.lower()}"
            shutil.copy2(source, target)
            uploaded_images.append({
                "name": source.name,
                "path": str(target.relative_to(PROJECT_DIR)).replace("\\", "/"),
            })

        payload = load_submissions()
        payload["updatedAt"] = datetime.now().isoformat(timespec="seconds")
        payload.setdefault("submissions", []).append({
            "id": submission_id,
            "status": "pending_review",
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "markerUid": marker["uid"],
            "markerNoteKey": marker["note_key"],
            "sourcePointId": marker.get("source_point_id"),
            "current": {
                "title": marker.get("title") or marker["name"],
                "category": marker["name"],
                "group": marker["group"],
            },
            "proposal": {
                "title": proposal.get("title", ""),
                "category": proposal.get("category", ""),
                "description": proposal.get("description", ""),
                "images": uploaded_images,
                "videoUrl": proposal.get("videoUrl", ""),
            },
        })
        write_json(SUBMISSIONS_PATH, payload)


def run_check():
    errors = []
    if not DATA_PATH.exists():
        errors.append(f"missing data: {DATA_PATH}")
    if not MAP_PATH.exists():
        errors.append(f"missing map: {MAP_PATH}")
    for layer, path in MAP_LAYER_PATHS.items():
        if not path.exists():
            errors.append(f"missing {map_layer_label(layer)} map: {path}")
    if errors:
        for error in errors:
            print(error)
        return 1
    meta, markers = load_markers()
    missing_icons = [marker for marker in markers if not marker["icon"].exists()]
    resource_types = {marker["mark_type"] for marker in markers}
    layer_counts = {}
    for marker in markers:
        layer_counts[marker["layer"]] = layer_counts.get(marker["layer"], 0) + 1
    details = load_marker_details().get("details", {})
    print(f"markers: {len(markers)}")
    print(f"resource types: {len(resource_types)}")
    print(f"map: {MAP_PATH}")
    print(f"layers: {', '.join(f'{map_layer_label(layer)}={layer_counts.get(layer, 0)}' for layer in MAP_LAYER_LABELS)}")
    print(f"map size: {meta['basemapImageSize'][0]}x{meta['basemapImageSize'][1]}")
    print(f"missing icons: {len(missing_icons)}")
    print(f"17173 details: {len(details)}")
    return 0 if not missing_icons else 1


def run_selftest():
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(False)
    window = RocoResourceMapQt()
    total = len(window.markers)
    resource_type_count = len(window.resource_types)
    layer_counts = {}
    for marker in window.markers:
        layer_counts[marker["layer"]] = layer_counts.get(marker["layer"], 0) + 1
    surface_total = layer_counts.get("G", 0)
    default_hidden_ok = len(window.visible_types) == 0 and len(window.visible_markers()) == 0
    first_uid = window.markers[0]["uid"] if window.markers else ""
    window.toggle_marker(first_uid)
    after_dim = first_uid in window.dimmed_uids
    window.toggle_marker(first_uid)
    after_restore = first_uid in window.dimmed_uids
    account_state_isolated_ok = False
    account_delete_ok = False
    black_glaze_surface_ok = not any(
        marker.get("layer") == "B1" and marker.get("mark_type") == 701 and marker.get("name") == "黑晶琉璃"
        for marker in window.markers
    )
    window.set_all_filters(False)
    visible_after_clear = len(window.visible_markers())
    window.set_all_filters(True)
    visible_after_all = len(window.visible_markers())
    b1_marker = next((marker for marker in window.markers if marker.get("layer") == "B1"), None)
    b2_marker = next((marker for marker in window.markers if marker.get("layer") == "B2"), None)
    layer_switch_b1_ok = b1_marker is None
    layer_focus_b2_ok = b2_marker is None
    if b1_marker is not None:
        layer_switch_b1_ok = (
            window.switch_map_layer("B1")
            and window.current_layer == "B1"
            and window.base_pixmap.width() == 6144
        )
        window.set_all_filters(True)
        layer_switch_b1_ok = layer_switch_b1_ok and len(window.visible_markers()) == layer_counts.get("B1", 0)
    if b2_marker is not None:
        window.focus_marker(b2_marker)
        layer_focus_b2_ok = (
            window.current_layer == "B2"
            and b2_marker["mark_type"] in window.visible_types
            and any(marker["uid"] == b2_marker["uid"] for marker in window.visible_markers())
        )
    window.switch_map_layer("G")
    window.set_all_filters(True)
    has_detail_payload = len(window.marker_details_payload.get("details", {})) > 0
    detail_marker = next((marker for marker in window.markers if marker.get("source_point_id")), window.markers[0])
    tooltip_17173_ok = (
        window.should_show_tooltip(detail_marker)
        and bool(window.marker_detail_for(detail_marker))
        and bool(window.tooltip_text(detail_marker).strip())
    )
    window.open_marker_detail(detail_marker)
    app.processEvents()
    detail_opened = len(window.detail_windows) == 1
    for dialog in list(window.detail_windows):
        dialog.close()
    app.processEvents()
    detail_closed = len(window.detail_windows) == 0
    window.search_input.setText("炼金台")
    window.run_search()
    app.processEvents()
    search_result_count = window.tree.topLevelItemCount()
    first_result = window.tree.topLevelItem(0) if search_result_count else None
    if first_result is not None:
        window.on_tree_item_clicked(first_result, 0)
        app.processEvents()
    search_focus_works = window.highlight_item is not None and len(window.detail_windows) >= 1
    for dialog in list(window.detail_windows):
        dialog.close()
    app.processEvents()

    route_dialog_opens = False
    route_slot_accepts_args = False
    route_player_center_ok = False
    route_player_moves_ok = False
    route_player_icon_ok = False
    route_arrows_ok = False
    locate_player_ok = False
    cache_button_removed = False
    pinned_layout_ok = False
    route_list_toggle_ok = False
    auto_position_without_calibration_ok = False
    nav_button_layout_ok = False
    auto_complete_route_ok = False
    route_preview_dim_ok = False
    player_angle_detection_ok = cv2 is None or np is None
    player_animation_120fps_ok = False
    route_global_open_ok = False
    teleport_route_hint_ok = False
    route_teleport_marker_visible_ok = False
    transition_pause_ok = False
    locked_circle_hidden_ok = False
    route_tree_tall_ok = False
    pinned_shortcuts_ok = False
    route_dialog_resize_ok = False
    compact_route_panel_ok = False
    resource_tree_no_hscroll_ok = False
    invalid_frame_no_drift_ok = False
    route_player_update_keeps_view_ok = False
    route_candidate_guard_ok = False
    clear_route_highlight_ok = False
    overlapping_marker_cycle_ok = False
    egg_query_feature_ok = False
    pvp_damage_feature_ok = False
    manual_route_anywhere_ok = False
    manual_first_point_visible_ok = False
    manual_route_no_save_keeps_ok = False

    def settle_player_motion():
        frames = getattr(window, "route_preview_player_motion", [])
        if frames:
            window.route_preview_player_motion_started_at = time.monotonic() - frames[-1].time - 0.01
            window.animate_route_preview_player()
            app.processEvents()
            return
        for _index in range(30):
            window.route_preview_player_last_update_at = time.monotonic() - 0.2
            window.animate_route_preview_player()
            app.processEvents()
            display = getattr(window, "route_preview_player_display_pos", None)
            target = getattr(window, "route_preview_player_target_pos", None)
            if display is not None and target is not None and math.hypot(display[0] - target[0], display[1] - target[1]) < 1.0:
                break
        target = getattr(window, "route_preview_player_target_pos", None)
        item = getattr(window, "route_preview_player_item", None)
        if target is not None and item is not None:
            window.route_preview_player_display_pos = target
            item.setPos(target[0], target[1])
            app.processEvents()

    try:
        window.open_route_navigation()
        app.processEvents()
        route_dialog_opens = window.route_dialog is not None and window.route_preview_scene is not None
        nav_button_layout_ok = (
            window.minimap_follow_button is not None
            and window.minimap_follow_button.text() == "开启AI导航"
            and window.minimap_circle_lock_button is not None
            and window.minimap_circle_lock_button.text() == "固定小地图圈"
            and window.route_dialog_pin_button is not None
            and window.route_dialog_pin_button.text() == "固定导航"
            and any(button.text() == "定位小洛克位置" for button in window.route_dialog.findChildren(QPushButton))
            and any(button.text() == "定位路线源头" for button in window.route_dialog.findChildren(QPushButton))
            and any(button.text() == "完成当前资源点" for button in window.route_dialog.findChildren(QPushButton))
        )
        window.route_markers = window.markers[:8]
        window.current_route_index = 0
        window.refresh_route_tree()
        window.render_route_path()
        app.processEvents()
        line_markers = [{"x": float(x), "y": 0.0} for x in (0, 10, 20, 30)]
        line_route = window.build_optimized_route(line_markers, 15.0, 0.0)
        route_global_open_ok = (
            abs(window.route_path_distance(line_route) - 30.0) < 0.001
            and line_route[0]["x"] in (0.0, 30.0)
            and line_route[-1]["x"] in (0.0, 30.0)
        )
        player_animation_120fps_ok = (
            window.route_preview_player_animation_timer is not None
            and window.route_preview_player_animation_timer.interval() <= 8
        )
        old_markers_for_teleport = window.markers
        old_route_for_teleport = window.route_markers
        try:
            resource_a = {"uid": "route-test-a", "x": 0.0, "y": 0.0, "mark_type": 802, "title": "A", "name": "资源", "group": "收集"}
            resource_b = {"uid": "route-test-b", "x": 2600.0, "y": 0.0, "mark_type": 802, "title": "B", "name": "资源", "group": "收集"}
            teleport = {"uid": "route-test-tp", "x": 2520.0, "y": 0.0, "mark_type": 202, "title": "测试传送点", "name": "传送点", "group": "地点"}
            window.markers = old_markers_for_teleport + [teleport]
            plan = window.route_transition_plan(resource_a, resource_b)
            window.route_markers = [resource_a, resource_b]
            window.current_route_index = 0
            window.update_route_transition_hints()
            window.render_route_path()
            window.update_route_preview()
            teleport_route_hint_ok = (
                plan.get("mode") == "teleport"
                and plan.get("teleport") is teleport
                and resource_a["uid"] in window.route_transition_hints
            )
            route_teleport_marker_visible_ok = (
                any(item.data(0) == teleport["uid"] for item in window.route_helper_marker_items)
                and any(item.data(0) == teleport["uid"] for item in window.route_preview_marker_items)
            )
        finally:
            window.markers = old_markers_for_teleport
            window.route_markers = old_route_for_teleport
            window.update_route_transition_hints()
            window.render_route_path()
        route_arrows_ok = window.route_preview_arrow_item is not None
        cache_button_removed = not any(
            button.text() == "生成SIFT缓存"
            for button in window.route_dialog.findChildren(QPushButton)
        )
        route_tree_tall_ok = (
            window.route_dialog_tree is not None
            and window.route_dialog_tree.maximumHeight() > 10000
        )
        fake_minimap = QPixmap(str(MAP_PATH)).copy(768, 768, 220, 220)
        window.capture_minimap_region = lambda: fake_minimap
        window.prepare_sift_tracker = lambda *args, **kwargs: True
        window.calibrate_minimap_to_view_center(True)
        app.processEvents()
        route_slot_accepts_args = True
        calibrated_pos = window.minimap_last_world_pos
        item = window.route_preview_player_item
        if item is not None and calibrated_pos is not None:
            center = item.sceneBoundingRect().center()
            route_player_center_ok = (
                abs(center.x() - calibrated_pos[0]) < 1.0
                and abs(center.y() - calibrated_pos[1]) < 1.0
            )
            route_player_icon_ok = isinstance(item, QGraphicsPathItem)
        from app.sift_tracker_v2 import _apply_world_pos

        target_pos = (1234.0, 2345.0)
        view_center_before = None
        if window.route_preview_view is not None:
            window.route_preview_view.centerOn(320.0, 420.0)
            app.processEvents()
            viewport_center = window.route_preview_view.viewport().rect().center()
            view_center_before = window.route_preview_view.mapToScene(viewport_center)
        _apply_world_pos(window, target_pos)
        app.processEvents()
        if window.route_preview_view is not None and view_center_before is not None:
            viewport_center = window.route_preview_view.viewport().rect().center()
            view_center_after = window.route_preview_view.mapToScene(viewport_center)
            route_player_update_keeps_view_ok = (
                abs(view_center_after.x() - view_center_before.x()) < 2.0
                and abs(view_center_after.y() - view_center_before.y()) < 2.0
            )
        item = window.route_preview_player_item
        if item is not None:
            settle_player_motion()
            center = item.sceneBoundingRect().center()
            route_player_moves_ok = abs(center.x() - target_pos[0]) < 1.0 and abs(center.y() - target_pos[1]) < 1.0

        window.completed_route_uids.clear()
        for marker in window.route_markers:
            window.dimmed_uids.discard(marker["uid"])
        complete_marker = window.route_markers[0]
        window.dimmed_uids.discard(complete_marker["uid"])
        window.current_route_index = 0
        early_auto_results = [
            window.auto_complete_route_at_position(complete_marker["x"], complete_marker["y"])
            for _ in range(max(1, ROUTE_AUTO_COMPLETE_REQUIRED_HITS - 1))
        ]
        window.route_auto_complete_candidate_started_at = time.monotonic() - ROUTE_AUTO_COMPLETE_DWELL_SECONDS - 0.1
        auto_complete_route_ok = (
            not any(early_auto_results)
            and window.auto_complete_route_at_position(complete_marker["x"], complete_marker["y"])
            and complete_marker["uid"] in window.completed_route_uids
            and complete_marker["uid"] in window.dimmed_uids
            and window.current_route_index >= 1
        )
        route_preview_dim_ok = any(
            item.data(0) == complete_marker["uid"] and item.opacity() < 1.0
            for item in window.route_preview_marker_items
        )
        window.completed_route_uids.clear()
        window.dimmed_uids.discard(complete_marker["uid"])
        window.current_route_index = 0
        window.refresh_route_tree()
        window.render_route_path()

        if window.route_preview_view is not None:
            window.route_preview_view.centerOn(0, 0)
            window.focus_current_player_position()
            app.processEvents()
            focused_pos = getattr(window, "_last_focus_player_position", None)
            locate_player_ok = (
                focused_pos is not None
                and abs(focused_pos[0] - target_pos[0]) < 1.0
                and abs(focused_pos[1] - target_pos[1]) < 1.0
            )

        from app import sift_tracker_v2
        if cv2 is not None and np is not None:
            arrow = np.zeros((96, 96, 3), dtype=np.uint8)
            cv2.fillConvexPoly(arrow, np.array([[74, 48], [30, 27], [40, 48], [30, 69]], dtype=np.int32), (18, 142, 255))
            cv2.polylines(arrow, [np.array([[74, 48], [30, 27], [40, 48], [30, 69]], dtype=np.int32)], True, (245, 245, 245), 3)
            decoy_star = np.array([[18, 57], [22, 65], [30, 67], [24, 74], [26, 83], [18, 78], [10, 83], [12, 74], [6, 67], [14, 65]], dtype=np.int32)
            cv2.fillPoly(arrow, [decoy_star], (22, 150, 255))
            cv2.polylines(arrow, [decoy_star], True, (245, 245, 245), 3)
            player_pos, found, angle = sift_tracker_v2._detect_player_local_bgr(arrow)
            angle_diff = abs(((float(angle or 0.0) - 90.0 + 180.0) % 360.0) - 180.0)
            stable_anchor_ok = abs(player_pos[0] - 48.0) < 1.0 and abs(player_pos[1] - 48.0) < 1.0
            rotated_anchor_ok = True
            for expected_angle, polygon in (
                (0.0, np.array([[48, 18], [27, 66], [48, 56], [69, 66]], dtype=np.int32)),
                (180.0, np.array([[48, 78], [27, 30], [48, 40], [69, 30]], dtype=np.int32)),
                (270.0, np.array([[20, 48], [66, 27], [56, 48], [66, 69]], dtype=np.int32)),
            ):
                rotated = np.zeros((96, 96, 3), dtype=np.uint8)
                cv2.fillConvexPoly(rotated, polygon, (18, 142, 255))
                cv2.polylines(rotated, [polygon], True, (245, 245, 245), 3)
                rotated_pos, rotated_found, rotated_angle = sift_tracker_v2._detect_player_local_bgr(rotated)
                rotated_diff = abs(((float(rotated_angle or 0.0) - expected_angle + 180.0) % 360.0) - 180.0)
                rotated_anchor_ok = (
                    rotated_anchor_ok
                    and bool(rotated_found)
                    and rotated_angle is not None
                    and rotated_diff < 35.0
                    and abs(rotated_pos[0] - 48.0) < 1.0
                    and abs(rotated_pos[1] - 48.0) < 1.0
                )
            player_angle_detection_ok = (
                bool(found)
                and angle is not None
                and angle_diff < 35.0
                and stable_anchor_ok
                and rotated_anchor_ok
            )

        old_track_minimap_sift_v2 = sift_tracker_v2.track_minimap_sift_v2
        try:
            auto_pos = (3456.0, 2345.0)
            sift_tracker_v2.track_minimap_sift_v2 = (
                lambda owner, image, *args, **kwargs: sift_tracker_v2._result(True, auto_pos, "自动全图定位")
            )
            window.minimap_calibrated = False
            window.minimap_circle_locked = True
            window.minimap_follow_enabled = True
            window.minimap_last_world_pos = None
            window._sift_v2_last_world = None
            window.route_preview_player_world_pos = None
            window.player_world_pos = None
            window.current_world_pos = None
            window.update_minimap_follow()
            app.processEvents()
            item = window.route_preview_player_item
            if item is not None:
                settle_player_motion()
                center = item.sceneBoundingRect().center()
                auto_position_without_calibration_ok = (
                    abs(center.x() - auto_pos[0]) < 1.0
                    and abs(center.y() - auto_pos[1]) < 1.0
                    and window.minimap_calibrated is False
                )
        finally:
            sift_tracker_v2.track_minimap_sift_v2 = old_track_minimap_sift_v2

        window._sift_v2_pause_until = time.time() + 1.0
        transition_result = sift_tracker_v2.update_minimap_follow_v2(window)
        transition_pause_ok = (
            not bool(transition_result)
            and "保护" in transition_result.get("message", "")
        )
        window._sift_v2_pause_until = 0.0

        old_prepare = sift_tracker_v2.prepare_sift_tracker_v2
        old_homography = sift_tracker_v2._homography_position
        old_template = sift_tracker_v2._template_position
        old_motion = sift_tracker_v2._relative_motion_position
        try:
            drift_start = (2222.0, 1888.0)
            window.minimap_last_world_pos = drift_start
            window._sift_v2_last_world = drift_start
            window._sift_v2_lost_frames = 0
            window._sift_v2_last_good_time = 1.0
            window._sift_v2_pause_until = 0.0
            sift_tracker_v2.prepare_sift_tracker_v2 = lambda owner, force=False: True
            sift_tracker_v2._homography_position = lambda owner, gray, mask, player=None: (None, 0, 0, "invalid")
            sift_tracker_v2._template_position = lambda owner, gray, mask, player=None: (None, 0.0, "invalid")
            sift_tracker_v2._relative_motion_position = lambda owner, gray, mask: ((4444.0, 3333.0), 0.99)
            result = sift_tracker_v2.track_minimap_sift_v2(window, fake_minimap)
            invalid_frame_no_drift_ok = (
                not bool(result)
                and window.minimap_last_world_pos == drift_start
                and 0 < window._sift_v2_lost_frames < sift_tracker_v2.SIFT_FULL_RELOCALIZE_AFTER
                and getattr(window, "_sift_v2_prev_gray", None) is None
            )
        finally:
            sift_tracker_v2.prepare_sift_tracker_v2 = old_prepare
            sift_tracker_v2._homography_position = old_homography
            sift_tracker_v2._template_position = old_template
            sift_tracker_v2._relative_motion_position = old_motion

        window.update_minimap_follow = lambda *args, **kwargs: None
        window.show_minimap_circle()
        app.processEvents()
        if window.minimap_circle is not None:
            window.minimap_circle_locked = False
            window.toggle_minimap_circle_lock()
            window.minimap_follow_timer.stop()
            app.processEvents()
            locked_circle_hidden_ok = (
                window.minimap_circle_locked is True
                and window.minimap_circle is not None
                and not window.minimap_circle.isVisible()
                and window.minimap_circle_lock_button is not None
                and window.minimap_circle_lock_button.text() == "取消固定小地图圈"
                and window.minimap_follow_button is not None
                and window.minimap_follow_button.text() == "关闭AI导航"
            )

        window.toggle_route_dialog_pin()
        app.processEvents()
        pinned_size = window.route_dialog.size() if window.route_dialog is not None else QSize()
        pinned_flags = window.route_dialog.windowFlags() if window.route_dialog is not None else Qt.WindowFlags()
        pinned_hint = window.route_dialog_pin_label.text() if window.route_dialog_pin_label is not None else ""
        if window.route_dialog_tree is not None:
            compact_route_panel_ok = (
                window.route_dialog_side_panel.maximumWidth() <= ROUTE_DIALOG_ROUTE_WIDTH_PINNED
                and window.route_dialog_tree.columnWidth(0) <= ROUTE_DIALOG_ROUTE_WIDTH_PINNED
                and window.route_dialog_tree.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
                and window.route_dialog_tree.wordWrap()
            )
        route_dialog_resize_ok = (
            window.route_dialog.minimumWidth() <= ROUTE_DIALOG_PINNED_MIN_SIZE.width()
            and window.route_dialog.minimumHeight() <= ROUTE_DIALOG_PINNED_MIN_SIZE.height()
        )
        shortcut_hits = []

        class FakeRouteKey:
            def __init__(self, key):
                self._key = key
                self.accepted = False

            def key(self):
                return self._key

            def accept(self):
                self.accepted = True

        old_focus_player_shortcut = window.focus_current_player_position
        old_focus_start_shortcut = window.focus_route_start_marker
        try:
            window.focus_current_player_position = lambda *args, **kwargs: shortcut_hits.append("player")
            window.focus_route_start_marker = lambda *args, **kwargs: shortcut_hits.append("start")
            f9_event = FakeRouteKey(Qt.Key_F9)
            f10_event = FakeRouteKey(Qt.Key_F10)
            f11_event = FakeRouteKey(Qt.Key_F11)
            route_list_was_visible = window.route_dialog_side_panel.isVisible()
            window.route_dialog.keyPressEvent(f9_event)
            window.route_dialog.keyPressEvent(f10_event)
            window.route_dialog.keyPressEvent(f11_event)
            pinned_shortcuts_ok = (
                shortcut_hits == ["player", "start"]
                and f9_event.accepted
                and f10_event.accepted
                and f11_event.accepted
                and window.route_dialog_side_panel.isVisible() != route_list_was_visible
            )
            if window.route_dialog_side_panel.isVisible() != route_list_was_visible:
                window.toggle_route_list_panel()
        finally:
            window.focus_current_player_position = old_focus_player_shortcut
            window.focus_route_start_marker = old_focus_start_shortcut
        pinned_layout_ok = (
            window.route_dialog_pinned is True
            and bool(pinned_flags & Qt.FramelessWindowHint)
            and not bool(pinned_flags & Qt.WindowMinimizeButtonHint)
            and not bool(pinned_flags & Qt.WindowMaximizeButtonHint)
            and not bool(pinned_flags & Qt.WindowCloseButtonHint)
            and window.route_dialog_tree is not None
            and window.route_dialog_tree.isColumnHidden(1)
            and all(key in pinned_hint for key in ("F9", "F10", "F11", "F12"))
            and window.route_dialog_pin_label is not None
            and window.route_dialog_pin_label.isVisible()
            and window.route_dialog_pin_label.height() <= 20
            and window.route_dialog_side_panel is not None
            and window.route_dialog_side_panel.isVisible()
            and window.route_dialog_route_list_button is not None
            and not window.route_dialog_route_list_button.isVisible()
            and window.minimap_follow_status_label is not None
            and not window.minimap_follow_status_label.isVisible()
            and 620 <= pinned_size.width() <= 680
            and 470 <= pinned_size.height() <= 530
        )
        route_list_toggle_ok = (
            window.route_dialog_side_panel is not None
            and window.route_dialog_side_panel.isVisible()
            and window.route_dialog_route_list_button is not None
            and not window.route_dialog_route_list_button.isVisible()
        )
        resource_tree_no_hscroll_ok = (
            window.tree.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
            and window.tree.columnWidth(1) <= 50
        )

        old_route_markers = list(window.route_markers)
        old_route_index = window.current_route_index
        old_completed_route_uids = set(window.completed_route_uids)
        old_manual_mode = window.manual_route_mode
        old_exec = QMessageBox.exec_

        class FakeScenePos:
            def __init__(self, x, y):
                self._x = x
                self._y = y

            def x(self):
                return self._x

            def y(self):
                return self._y

        try:
            window.manual_route_mode = True
            window.route_markers = []
            window.current_route_index = 0
            window.completed_route_uids.clear()
            window.add_manual_route_point(FakeScenePos(1234.5, 2345.5))
            manual_first_point_visible_ok = (
                len(window.route_markers) == 1
                and len(window.route_helper_marker_items) >= 1
                and window.route_helper_marker_items[-1].data(0) == route_point_uid(window.route_markers[0])
            )
            window.add_manual_route_point(FakeScenePos(1301.0, 2388.0))
            manual_route_anywhere_ok = (
                len(window.route_markers) == 2
                and all(is_manual_route_point(marker) for marker in window.route_markers)
                and abs(window.route_markers[0]["x"] - 1234.5) < 0.1
                and window.route_path_item is not None
            )
            QMessageBox.exec_ = lambda _box: QMessageBox.No
            window.toggle_manual_route_mode()
            manual_route_no_save_keeps_ok = (
                window.manual_route_mode is False
                and len(window.route_markers) == 2
                and all(is_manual_route_point(marker) for marker in window.route_markers)
            )
        finally:
            QMessageBox.exec_ = old_exec
            window.manual_route_mode = old_manual_mode
            if window.manual_route_button is not None:
                window.manual_route_button.setText("结束规划" if old_manual_mode else "自行规划路线")
            window.route_markers = old_route_markers
            window.current_route_index = old_route_index
            window.completed_route_uids = old_completed_route_uids
            window.refresh_route_tree()
            window.render_route_path()
            window.save_route_state()
    except Exception:
        route_slot_accepts_args = False

    old_route_markers = list(window.route_markers)
    old_route_index = window.current_route_index
    old_completed_route_uids = set(window.completed_route_uids)
    old_visible_types = set(window.visible_types)
    old_route_background_job = window.route_background_job
    old_warning = QMessageBox.warning
    old_load_cached_route = window.load_cached_route
    old_build_optimized_route = window.build_optimized_route
    try:
        warning_calls = []
        build_calls = []
        QMessageBox.warning = lambda *args, **kwargs: warning_calls.append(args) or QMessageBox.Ok
        window.load_cached_route = lambda _key: None
        window.build_optimized_route = lambda candidates, *args, **kwargs: build_calls.append(len(candidates)) or list(candidates)
        window.visible_types = set(window.resource_types)
        window.completed_route_uids.clear()
        window.generate_route_from_visible()
        route_candidate_guard_ok = bool(warning_calls) and not build_calls

        window.highlight_item = QGraphicsEllipseItem(0, 0, 12, 12)
        window.scene.addItem(window.highlight_item)
        window.route_markers = [window.markers[0]] if window.markers else []
        window.clear_route()
        clear_route_highlight_ok = window.highlight_item is None
    finally:
        QMessageBox.warning = old_warning
        window.load_cached_route = old_load_cached_route
        window.build_optimized_route = old_build_optimized_route
        if window.route_background_timer.isActive():
            window.route_background_timer.stop()
        window.route_background_job = old_route_background_job
        window.visible_types = old_visible_types
        window.route_markers = old_route_markers
        window.current_route_index = old_route_index
        window.completed_route_uids = old_completed_route_uids
        window.refresh_route_tree()
        window.render_route_path()
        window.save_route_state()
        window._visible_markers_cache_signature = None

    old_markers = list(window.markers)
    old_visible_types = set(window.visible_types)
    old_cycle_key = window.marker_hit_cycle_key
    old_cycle_index = window.marker_hit_cycle_index
    try:
        if len(window.markers) >= 2:
            base_a = dict(window.markers[0])
            base_b = dict(window.markers[1])
            base_a.update({"uid": "__overlap_a__", "x": 2888.0, "y": 2999.0, "layer": window.current_layer})
            base_b.update({"uid": "__overlap_b__", "x": 2888.0, "y": 2999.0, "layer": window.current_layer, "mark_type": base_a["mark_type"]})
            window.markers = old_markers + [base_a, base_b]
            window.visible_types = set(old_visible_types) | {base_a["mark_type"]}
            window._visible_markers_cache_signature = None
            first_overlap = window.hit_test_marker(FakeScenePos(2888.0, 2999.0), cycle=True)
            second_overlap = window.hit_test_marker(FakeScenePos(2888.0, 2999.0), cycle=True)
            overlapping_marker_cycle_ok = (
                first_overlap is not None
                and second_overlap is not None
                and first_overlap["uid"] != second_overlap["uid"]
                and {first_overlap["uid"], second_overlap["uid"]} == {"__overlap_a__", "__overlap_b__"}
            )
    finally:
        window.markers = old_markers
        window.visible_types = old_visible_types
        window.marker_hit_cycle_key = old_cycle_key
        window.marker_hit_cycle_index = old_cycle_index
        window._visible_markers_cache_signature = None

    egg_dialog = EggQueryDialog(window)
    try:
        egg_dialog.fill_example("0.16", "1.27")
        egg_dialog.run_query()
        egg_dialog.group_name_input.setText("书魔虫")
        egg_dialog.run_group_lookup()
        egg_dialog.fill_plan_example()
        egg_dialog.run_breeding_plan()
        egg_query_feature_ok = (
            egg_dialog.result_tree.topLevelItemCount() >= 1
            and any(
                "书魔虫" in egg_dialog.result_tree.topLevelItem(index).text(0)
                for index in range(egg_dialog.result_tree.topLevelItemCount())
            )
            and egg_dialog.group_result_tree.topLevelItemCount() >= 1
            and egg_dialog.plan_result_tree.topLevelItemCount() >= 1
            and "查询成功" in egg_dialog.status_label.text()
        )
    finally:
        egg_dialog.close()
        egg_dialog.deleteLater()
        app.processEvents()

    pvp_dialog = PvpDamageDialog(window)
    try:
        pvp_dialog.status_spins["burn"].setValue(1)
        pvp_dialog.calculate()
        pvp_damage_feature_ok = (
            pvp_dialog.detail_tree.topLevelItemCount() > 0
            and "总伤害" in pvp_dialog.result_label.text()
            and any(
                "灼烧" in pvp_dialog.detail_tree.topLevelItem(index).text(0)
                for index in range(pvp_dialog.detail_tree.topLevelItemCount())
            )
        )
    finally:
        pvp_dialog.close()
        pvp_dialog.deleteLater()
        app.processEvents()

    original_account_id = window.account_id
    probe_uid = next((marker["uid"] for marker in window.markers if marker["uid"] not in window.dimmed_uids), "")
    test_account_id = make_unique_account_id(account.get("id") for account in window.account_registry.get("accounts", []))
    delete_test_account_id = make_unique_account_id(
        list(account.get("id") for account in window.account_registry.get("accounts", [])) + [test_account_id]
    )
    old_question = QMessageBox.question
    try:
        if probe_uid:
            old_had_probe = probe_uid in window.dimmed_uids
            window.account_registry.setdefault("accounts", []).append({
                "id": test_account_id,
                "name": "自检账号",
                "createdAt": datetime.now().isoformat(timespec="seconds"),
            })
            window.switch_account(test_account_id)
            blank_account_ok = (
                probe_uid not in window.dimmed_uids
                and probe_uid not in window.completed_route_uids
                and not window.notes_payload.get("markers")
            )
            window.dimmed_uids.add(probe_uid)
            window.completed_route_uids.add(probe_uid)
            window.save_state()
            window.save_route_state()
            window.switch_account(original_account_id)
            restored_account_ok = (probe_uid in window.dimmed_uids) == old_had_probe
            account_state_isolated_ok = blank_account_ok and restored_account_ok
        window.account_registry.setdefault("accounts", []).append({
            "id": delete_test_account_id,
            "name": "待删除自检账号",
            "createdAt": datetime.now().isoformat(timespec="seconds"),
        })
        window.switch_account(delete_test_account_id)
        window.save_state()
        QMessageBox.question = lambda *args, **kwargs: QMessageBox.Yes
        window.delete_account()
        account_delete_ok = (
            safe_account_id(delete_test_account_id)
            not in {safe_account_id(account.get("id")) for account in window.account_registry.get("accounts", [])}
            and not account_data_dir(delete_test_account_id).exists()
        )
    finally:
        QMessageBox.question = old_question
        if window.account_id != original_account_id:
            window.switch_account(original_account_id)
        window.account_registry["accounts"] = [
            account
            for account in window.account_registry.get("accounts", [])
            if safe_account_id(account.get("id")) not in {test_account_id, delete_test_account_id}
        ]
        window.account_registry["currentAccountId"] = original_account_id
        save_account_registry(window.account_registry)
        shutil.rmtree(account_data_dir(test_account_id), ignore_errors=True)
        shutil.rmtree(account_data_dir(delete_test_account_id), ignore_errors=True)
        window.refresh_account_combo()
    checks = {
        "markers": total > 0,
        "resource_type_count": resource_type_count > 0,
        "default_hidden_ok": bool(default_hidden_ok),
        "after_dim": bool(after_dim),
        "after_restore": not bool(after_restore),
        "visible_after_clear": visible_after_clear == 0,
        "visible_after_all": visible_after_all == surface_total,
        "layer_switch_b1_ok": bool(layer_switch_b1_ok),
        "layer_focus_b2_ok": bool(layer_focus_b2_ok),
        "has_detail_payload": bool(has_detail_payload),
        "tooltip_17173_ok": bool(tooltip_17173_ok),
        "detail_opened": bool(detail_opened),
        "detail_closed": bool(detail_closed),
        "search_result_count": search_result_count > 0,
        "search_focus_works": bool(search_focus_works),
        "route_dialog_opens": bool(route_dialog_opens),
        "route_slot_accepts_args": bool(route_slot_accepts_args),
        "route_player_center_ok": bool(route_player_center_ok),
        "route_player_moves_ok": bool(route_player_moves_ok),
        "route_player_icon_ok": bool(route_player_icon_ok),
        "route_arrows_ok": bool(route_arrows_ok),
        "locate_player_ok": bool(locate_player_ok),
        "cache_button_removed": bool(cache_button_removed),
        "pinned_layout_ok": bool(pinned_layout_ok),
        "route_list_toggle_ok": bool(route_list_toggle_ok),
        "auto_position_without_calibration_ok": bool(auto_position_without_calibration_ok),
        "nav_button_layout_ok": bool(nav_button_layout_ok),
        "auto_complete_route_ok": bool(auto_complete_route_ok),
        "route_preview_dim_ok": bool(route_preview_dim_ok),
        "player_angle_detection_ok": bool(player_angle_detection_ok),
        "player_animation_120fps_ok": bool(player_animation_120fps_ok),
        "route_global_open_ok": bool(route_global_open_ok),
        "teleport_route_hint_ok": bool(teleport_route_hint_ok),
        "route_teleport_marker_visible_ok": bool(route_teleport_marker_visible_ok),
        "transition_pause_ok": bool(transition_pause_ok),
        "locked_circle_hidden_ok": bool(locked_circle_hidden_ok),
        "route_tree_tall_ok": bool(route_tree_tall_ok),
        "pinned_shortcuts_ok": bool(pinned_shortcuts_ok),
        "route_dialog_resize_ok": bool(route_dialog_resize_ok),
        "compact_route_panel_ok": bool(compact_route_panel_ok),
        "resource_tree_no_hscroll_ok": bool(resource_tree_no_hscroll_ok),
        "invalid_frame_no_drift_ok": bool(invalid_frame_no_drift_ok),
        "route_player_update_keeps_view_ok": bool(route_player_update_keeps_view_ok),
        "route_candidate_guard_ok": bool(route_candidate_guard_ok),
        "clear_route_highlight_ok": bool(clear_route_highlight_ok),
        "overlapping_marker_cycle_ok": bool(overlapping_marker_cycle_ok),
        "black_glaze_surface_ok": bool(black_glaze_surface_ok),
        "egg_query_feature_ok": bool(egg_query_feature_ok),
        "pvp_damage_feature_ok": bool(pvp_damage_feature_ok),
        "account_state_isolated_ok": bool(account_state_isolated_ok),
        "account_delete_ok": bool(account_delete_ok),
        "manual_route_anywhere_ok": bool(manual_route_anywhere_ok),
        "manual_first_point_visible_ok": bool(manual_first_point_visible_ok),
        "manual_route_no_save_keeps_ok": bool(manual_route_no_save_keeps_ok),
    }
    failed_checks = [name for name, ok in checks.items() if not ok]
    selftest_return_code = 0 if not failed_checks else 1
    window.tearing_down = True
    for timer_name in (
        "route_background_timer",
        "minimap_follow_timer",
        "marker_rebuild_timer",
        "pending_save",
        "route_preview_player_animation_timer",
    ):
        timer = getattr(window, timer_name, None)
        if timer is not None:
            timer.stop()
    if window.route_dialog is not None:
        if window.route_preview_scene is not None:
            window.route_preview_scene.clear()
        window.route_dialog.close()
        window.route_dialog.deleteLater()
        app.processEvents()
    if getattr(window, "scene", None) is not None:
        window.scene.clear()
    if getattr(window, "view", None) is not None:
        window.view.setScene(None)
    window.layer_pixmap_cache.clear()
    window.icon_pixmaps.clear()
    window.sidebar_icons.clear()
    window.close()
    window.deleteLater()
    app.processEvents()
    print(f"markers: {total}")
    print(f"resource types: {resource_type_count}")
    print(f"default hidden: {default_hidden_ok}")
    print(f"dim after first toggle: {after_dim}")
    print(f"dim after second toggle: {after_restore}")
    print(f"visible after clear: {visible_after_clear}")
    print(f"visible after all: {visible_after_all}")
    print(f"layer counts: {layer_counts}")
    print(f"B1 layer switch: {layer_switch_b1_ok}")
    print(f"B2 focus switch: {layer_focus_b2_ok}")
    print(f"17173 details loaded: {has_detail_payload}")
    print(f"17173 hover tooltip: {tooltip_17173_ok}")
    print(f"detail dialog opens: {detail_opened}")
    print(f"detail dialog closes: {detail_closed}")
    print(f"search results: {search_result_count}")
    print(f"search focus works: {search_focus_works}")
    print(f"route dialog opens: {route_dialog_opens}")
    print(f"minimap slot accepts Qt args: {route_slot_accepts_args}")
    print(f"route player centered: {route_player_center_ok}")
    print(f"route player moves: {route_player_moves_ok}")
    print(f"route player icon: {route_player_icon_ok}")
    print(f"route preview arrows: {route_arrows_ok}")
    print(f"locate player works: {locate_player_ok}")
    print(f"SIFT cache button removed: {cache_button_removed}")
    print(f"pinned layout minimal: {pinned_layout_ok}")
    print(f"route list toggle works: {route_list_toggle_ok}")
    print(f"auto position without calibration: {auto_position_without_calibration_ok}")
    print(f"nav button layout: {nav_button_layout_ok}")
    print(f"auto complete route: {auto_complete_route_ok}")
    print(f"route preview dimmed: {route_preview_dim_ok}")
    print(f"player angle detection: {player_angle_detection_ok}")
    print(f"player animation 120fps: {player_animation_120fps_ok}")
    print(f"global route open path: {route_global_open_ok}")
    print(f"teleport route hint: {teleport_route_hint_ok}")
    print(f"teleport marker visible in route: {route_teleport_marker_visible_ok}")
    print(f"transition pause protects: {transition_pause_ok}")
    print(f"locked circle hidden: {locked_circle_hidden_ok}")
    print(f"route tree tall: {route_tree_tall_ok}")
    print(f"pinned shortcuts F9/F10/F11: {pinned_shortcuts_ok}")
    print(f"route dialog can shrink: {route_dialog_resize_ok}")
    print(f"compact route panel: {compact_route_panel_ok}")
    print(f"resource tree horizontal bar hidden: {resource_tree_no_hscroll_ok}")
    print(f"invalid frame no drift: {invalid_frame_no_drift_ok}")
    print(f"route player update keeps view: {route_player_update_keeps_view_ok}")
    print(f"route candidate guard: {route_candidate_guard_ok}")
    print(f"clear route removes highlight: {clear_route_highlight_ok}")
    print(f"overlapping marker cycle: {overlapping_marker_cycle_ok}")
    print(f"black glaze fixed to surface: {black_glaze_surface_ok}")
    print(f"egg query feature: {egg_query_feature_ok}")
    print(f"PVP damage feature: {pvp_damage_feature_ok}")
    print(f"account state isolated: {account_state_isolated_ok}")
    print(f"account delete works: {account_delete_ok}")
    print(f"manual route anywhere: {manual_route_anywhere_ok}")
    print(f"manual first point visible: {manual_first_point_visible_ok}")
    print(f"manual route no-save keeps route: {manual_route_no_save_keeps_ok}")
    if failed_checks:
        print("selftest failed checks:", ", ".join(failed_checks))
    return selftest_return_code


def parse_args():
    parser = argparse.ArgumentParser(description="洛克王国多功能辅助工具（Qt版）")
    parser.add_argument("--check", action="store_true", help="检查数据和图片资源是否齐全，不打开窗口")
    parser.add_argument("--selftest", action="store_true", help="构建界面并检查点击、筛选逻辑")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.check:
        return run_check()
    if args.selftest:
        return int(run_selftest())

    app = QApplication.instance() or QApplication(sys.argv)
    try:
        window = RocoResourceMapQt()
    except Exception as exc:
        QMessageBox.critical(None, "启动失败", str(exc))
        return 1
    window.show()
    return app.exec_()


try:
    from app.sift_tracker_v2 import install as _install_sift_tracker_v2

    _install_sift_tracker_v2(globals())
except Exception:
    pass


if __name__ == "__main__":
    sys.exit(main())
