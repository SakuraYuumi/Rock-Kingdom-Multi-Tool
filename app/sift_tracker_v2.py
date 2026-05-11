from __future__ import annotations

import inspect
import math
import time
from pathlib import Path

try:
    import cv2
    import numpy as np
except Exception:  # pragma: no cover - optional runtime dependency
    cv2 = None
    np = None

try:
    from PyQt5.QtCore import QEvent, QObject, QPointF, QTimer, Qt
    from PyQt5.QtWidgets import QApplication, QLabel, QAbstractButton, QGraphicsEllipseItem
    from PyQt5.QtGui import QColor, QBrush, QImage, QPen, QPixmap
except Exception:  # pragma: no cover - PyQt is provided by the app runtime
    QEvent = None
    QObject = object
    QPointF = None
    QTimer = None
    Qt = None
    QApplication = None
    QLabel = None
    QAbstractButton = None
    QGraphicsEllipseItem = None
    QColor = None
    QBrush = None
    QImage = None
    QPen = None
    QPixmap = None


HOST_GLOBALS = {}
_RUNTIME_FILTER = None
_RUNTIME_SCAN_TIMER = None

SIFT_CACHE_VERSION = 2
SIFT_CACHE_NAME = "wiki_map_sift_cache_v2.npz"
SIFT_REFERENCE_MAX_SIDE = 4096
SIFT_MAP_NFEATURES = 120000
SIFT_QUERY_MAX_EDGE = 224
SIFT_QUERY_NFEATURES = 360
SIFT_MINIMAP_ELLIPSE_SCALE = 0.98
SIFT_MINIMAP_CENTER_EXCLUDE_RADIUS_RATIO = 0.17
SIFT_MATCH_RATIO = 0.86
SIFT_MIN_MATCH_COUNT = 6
SIFT_RANSAC_THRESHOLD = 8.0
SIFT_MIN_INLIER_COUNT = 6
SIFT_MIN_INLIER_RATIO = 0.45
SIFT_LOCAL_SEARCH_RADIUS = 440
SIFT_LOST_EXPAND_STEP = 280
SIFT_MAX_LOCAL_RADIUS = 2200
SIFT_FULL_RELOCALIZE_AFTER = 5
SIFT_MAX_WORLD_JUMP = 520
SIFT_TEMPLATE_MIN_SCORE = 0.30
SIFT_MOTION_MIN_RESPONSE = 0.22
SIFT_MOTION_MAX_LOST_FRAMES = 3
SIFT_MOTION_MAX_GOOD_AGE = 1.8
SIFT_DEFAULT_WORLD_PER_MINIMAP_PIXEL = 3.8
SIFT_INVALID_FRAME_COOLDOWN = 0.10
SIFT_INVALID_FULL_RELOCALIZE_AFTER = 0.85
SIFT_FAILED_MATCH_COOLDOWN = 0.08
SIFT_FULL_RELOCALIZE_COOLDOWN = 0.10
SIFT_FULL_MATCH_MIN_INTERVAL = 0.48


class SiftTrackResult(dict):
    """Small compatibility object for old callers that unpack `(pos, message)`."""

    def __iter__(self):
        yield self.get("position")
        yield self.get("message", "")

    def __getitem__(self, key):
        if isinstance(key, int):
            values = (
                self.get("position"),
                self.get("message", ""),
                self.get("match_count", 0),
                self.get("inliers", 0),
                self.get("ok", False),
            )
            return values[key]
        return super().__getitem__(key)

    def __bool__(self):
        return bool(self.get("ok"))


def install(host_globals):
    """Patch the existing route/minimap classes without touching the rest of the app."""

    HOST_GLOBALS.clear()
    HOST_GLOBALS.update(host_globals)
    patched = 0
    for obj in list(host_globals.values()):
        if not isinstance(obj, type):
            continue
        names = set(dir(obj))
        if {"prepare_sift_tracker", "track_minimap_sift"} & names:
            obj.prepare_sift_tracker = prepare_sift_tracker_v2
            obj.track_minimap_sift = track_minimap_sift_v2
            if "minimap_feature_image_and_mask" in names:
                obj.minimap_feature_image_and_mask = minimap_feature_image_and_mask_v2
            patched += 1
        if "update_minimap_follow" in names and not getattr(obj, "_sift_v2_update_patched", False):
            obj._sift_v2_old_update_minimap_follow = obj.update_minimap_follow
            obj.update_minimap_follow = update_minimap_follow_v2
            obj._sift_v2_update_patched = True
            _patch_owner_lifecycle(obj)
            patched += 1
        patched += _patch_minimap_trigger_methods(obj)
    _install_runtime_filter_later()
    return patched


def _install_runtime_filter_later():
    if QTimer is None:
        return

    def attempt():
        app = QApplication.instance() if QApplication is not None else None
        if app is None:
            QTimer.singleShot(300, attempt)
            return
        _install_runtime_filter(app)

    QTimer.singleShot(0, attempt)


def _install_runtime_filter(app):
    global _RUNTIME_FILTER, _RUNTIME_SCAN_TIMER
    if _RUNTIME_FILTER is None:
        _RUNTIME_FILTER = _SiftV2RuntimeFilter(app)
        app.installEventFilter(_RUNTIME_FILTER)
    if _RUNTIME_SCAN_TIMER is None and QTimer is not None:
        _RUNTIME_SCAN_TIMER = QTimer(app)
        _RUNTIME_SCAN_TIMER.setInterval(500)
        _RUNTIME_SCAN_TIMER.timeout.connect(_scan_runtime_windows)
        _RUNTIME_SCAN_TIMER.start()


class _SiftV2RuntimeFilter(QObject):
    def eventFilter(self, obj, event):
        try:
            etype = event.type()
        except Exception:
            return False
        if QEvent is None:
            return False
        if etype in (QEvent.Show, QEvent.WindowActivate):
            try:
                window = obj.window()
            except Exception:
                window = obj
            _maybe_prepare_route_window(window)
        if etype == QEvent.MouseButtonRelease and QAbstractButton is not None and isinstance(obj, QAbstractButton):
            text = obj.text()
            window = obj.window()
            _handle_runtime_button(window, text)
        return False


def _scan_runtime_windows():
    app = QApplication.instance() if QApplication is not None else None
    if app is None:
        return
    for window in app.topLevelWidgets():
        _maybe_prepare_route_window(window)


def _window_title(widget):
    try:
        return widget.windowTitle()
    except Exception:
        return ""


def _is_route_window(widget):
    title = _window_title(widget)
    if "跑图导航" in title or "导航" in title:
        return True
    try:
        if widget.findChildren(QAbstractButton):
            texts = " ".join(button.text() for button in widget.findChildren(QAbstractButton))
            return "小地图" in texts and "定位当前位置" in texts
    except Exception:
        pass
    return False


def _maybe_prepare_route_window(window):
    if window is None or not _is_route_window(window):
        return
    _setup_owner_runtime_hooks(window)
    last = _last_world_pos(window)
    if last is not None:
        _apply_world_pos(window, last)


def _handle_runtime_button(window, text):
    if window is None or not _is_route_window(window):
        return
    _setup_owner_runtime_hooks(window)
    label = str(text)
    if "校准" in label or "中心" in label or "当前位置" in label:
        _anchor_to_view_center(window)
    if "固定小地图" in label or "AI小地图" in label or "跟随" in label or "固定窗口" in label:
        if "固定小地图" in label or "AI小地图" in label or "跟随" in label:
            _force_full_relocalize(window)
        if _owner_follow_should_run(window):
            _ensure_follow_timer_running(window)


def _setup_owner_runtime_hooks(owner):
    if getattr(owner, "_sift_v2_runtime_ready", False):
        return
    setattr(owner, "_sift_v2_runtime_ready", True)
    try:
        for button in owner.findChildren(QAbstractButton):
            text = button.text()
            if any(key in text for key in ("校准", "固定小地图", "AI小地图", "跟随", "当前位置")):
                button.clicked.connect(lambda _checked=False, w=owner, t=text: _handle_runtime_button(w, t))
    except Exception:
        pass


def _patch_owner_lifecycle(cls):
    if getattr(cls, "_sift_v2_lifecycle_patched", False):
        return

    old_init = getattr(cls, "__init__", None)

    def init_wrapper(self, *args, **kwargs):
        if old_init is not None:
            old_init(self, *args, **kwargs)
        _setup_owner_runtime_hooks(self)

    cls.__init__ = init_wrapper

    old_show = getattr(cls, "showEvent", None)

    def show_wrapper(self, event):
        if old_show is not None:
            old_show(self, event)
        _setup_owner_runtime_hooks(self)
        if _last_world_pos(self) is not None:
            _apply_world_pos(self, _last_world_pos(self))

    cls.showEvent = show_wrapper
    cls._sift_v2_lifecycle_patched = True


def _patch_minimap_trigger_methods(cls):
    count = 0
    for name, value in list(cls.__dict__.items()):
        if not callable(value):
            continue
        if name.startswith("_sift_v2_"):
            continue
        lower = name.lower()
        if "minimap" not in lower and "mini_map" not in lower:
            continue
        is_trigger = any(token in lower for token in ("fix", "lock", "pin", "toggle", "calibr", "center", "follow", "track"))
        if not is_trigger:
            continue
        marker = f"_sift_v2_wrapped_{name}"
        if getattr(cls, marker, False):
            continue

        def make_wrapper(method):
            def wrapper(self, *args, **kwargs):
                result = _call_qt_slot_method(method, self, args, kwargs)
                method_name = getattr(method, "__name__", "").lower()
                if "calibr" in method_name or "center" in method_name:
                    _anchor_to_view_center(self)
                if "fix" in method_name or "lock" in method_name or "pin" in method_name or "follow" in method_name or "track" in method_name:
                    if (
                        ("lock" in method_name or "fix" in method_name or method_name.startswith("toggle_minimap_follow"))
                        and _owner_follow_should_run(self)
                    ):
                        _force_full_relocalize(self)
                    if _owner_follow_should_run(self):
                        _ensure_follow_timer_running(self)
                return result

            wrapper.__name__ = getattr(method, "__name__", "sift_v2_wrapper")
            return wrapper

        setattr(cls, name, make_wrapper(value))
        setattr(cls, marker, True)
        count += 1
    return count


def _call_qt_slot_method(method, owner, args, kwargs):
    """Call a Qt-connected method while ignoring surplus signal arguments."""

    if not args and not kwargs:
        return method(owner)
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        try:
            return method(owner, *args, **kwargs)
        except TypeError:
            return method(owner)

    params = list(signature.parameters.values())
    if params and params[0].name == "self":
        params = params[1:]

    accepts_args = any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in params)
    accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params)
    if accepts_args:
        call_args = args
    else:
        positional_capacity = sum(
            1
            for param in params
            if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        )
        call_args = args[:positional_capacity]

    if accepts_kwargs:
        call_kwargs = kwargs
    else:
        allowed_keywords = {
            param.name
            for param in params
            if param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        }
        call_kwargs = {key: value for key, value in kwargs.items() if key in allowed_keywords}

    return method(owner, *call_args, **call_kwargs)


def _project_dir():
    value = HOST_GLOBALS.get("PROJECT_DIR")
    if value:
        return Path(value)
    return Path(__file__).resolve().parents[1]


def _cache_path(owner=None):
    if owner is not None:
        owner_cache = getattr(owner, "sift_cache_path", None)
        if callable(owner_cache):
            try:
                return Path(owner_cache())
            except Exception:
                pass
    try:
        from app.app_paths import data_path, user_cache_path
    except Exception:
        try:
            from app_paths import data_path, user_cache_path
        except Exception:
            data_dir = _project_dir() / "user_data" / "cache"
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir / SIFT_CACHE_NAME
    static_cache = data_path(SIFT_CACHE_NAME)
    if static_cache.exists():
        return static_cache
    return user_cache_path(SIFT_CACHE_NAME)


def _write_cache_path(owner=None):
    if owner is not None:
        owner_cache = getattr(owner, "sift_cache_path", None)
        if callable(owner_cache):
            try:
                path = Path(owner_cache())
                if "_internal" not in path.parts:
                    return path
            except Exception:
                pass
    try:
        from app.app_paths import user_cache_path
    except Exception:
        try:
            from app_paths import user_cache_path
        except Exception:
            data_dir = _project_dir() / "user_data" / "cache"
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir / SIFT_CACHE_NAME
    return user_cache_path(SIFT_CACHE_NAME)


def _cache_text(value):
    try:
        return str(value.item())
    except Exception:
        return str(value)


def _reference_scaled_shape(map_path):
    bgr = _read_image(map_path)
    if bgr is None:
        return None
    h, w = bgr.shape[:2]
    scale = min(1.0, SIFT_REFERENCE_MAX_SIDE / float(max(h, w)))
    return int(h * scale), int(w * scale)


def _cache_matches_reference(data, map_path, map_mtime):
    try:
        if int(data["version"]) != SIFT_CACHE_VERSION:
            return False
        cached_map = _cache_text(data["map_path"])
        if cached_map == str(map_path) and int(data["map_mtime"]) == int(map_mtime):
            return True
        if Path(cached_map).name != Path(map_path).name:
            return False
        cached_shape = tuple(int(v) for v in data["shape"])
    except Exception:
        return False
    return cached_shape == _reference_scaled_shape(map_path)


def _load_sift_cache(owner, data):
    setattr(owner, "_sift_v2_scale", float(data["scale"]))
    setattr(owner, "_sift_v2_points", data["points"].astype(np.float32))
    setattr(owner, "_sift_v2_desc", data["desc"].astype(np.float32))
    setattr(owner, "_sift_v2_shape", tuple(int(v) for v in data["shape"]))


def _build_full_matcher(desc):
    if cv2 is None or desc is None or len(desc) < SIFT_MIN_MATCH_COUNT:
        return None
    try:
        matcher = _create_matcher()
        train_desc = np.ascontiguousarray(desc.astype(np.float32))
        matcher.add([train_desc])
        matcher.train()
        return matcher
    except Exception:
        return None


def _read_image(path):
    if cv2 is None or np is None:
        return None
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def _image_area(path):
    if cv2 is None or np is None:
        return 0
    img = _read_image(path)
    if img is None:
        return 0
    return int(img.shape[0] * img.shape[1])


def _find_reference_map_path(owner=None):
    if owner is not None:
        active_map_path = getattr(owner, "active_map_path", None)
        if callable(active_map_path):
            try:
                path = Path(active_map_path())
                if path.exists():
                    return path
            except Exception:
                pass
    preferred_keys = (
        "LOGIC_MAP_PATH",
        "WIKI_MAP_PATH",
        "BASE_MAP_PATH",
        "MAP_IMAGE_PATH",
        "MAP_PATH",
        "WORLD_MAP_PATH",
    )
    for key in preferred_keys:
        value = HOST_GLOBALS.get(key)
        if value and Path(value).exists():
            return Path(value)

    project = _project_dir()
    candidates = []
    for folder in (project / "data", project / "assets", project / "web", project):
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            name = path.name.lower()
            score = 0
            if "map" in name or "地图" in name:
                score += 100
            if "wiki" in name or "world" in name or "z7" in name:
                score += 50
            if "icon" in name or "marker" in name or "resource" in name:
                score -= 100
            area = _image_area(path)
            if area >= 2_000_000:
                candidates.append((score, area, path))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


def _qimage_to_bgr(image):
    if cv2 is None or np is None or QImage is None:
        return None
    if QPixmap is not None and isinstance(image, QPixmap):
        image = image.toImage()
    if not isinstance(image, QImage):
        return image if isinstance(image, np.ndarray) else None

    fmt = getattr(QImage, "Format_RGBA8888", QImage.Format_ARGB32)
    qimage = image.convertToFormat(fmt)
    width = qimage.width()
    height = qimage.height()
    if width <= 0 or height <= 0:
        return None
    ptr = qimage.bits()
    ptr.setsize(qimage.byteCount())
    raw = np.frombuffer(ptr, dtype=np.uint8).reshape((height, qimage.bytesPerLine()))
    rgba = raw[:, : width * 4].reshape((height, width, 4))
    return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)


def _create_sift(nfeatures):
    if cv2 is None:
        return None
    if hasattr(cv2, "SIFT_create"):
        return cv2.SIFT_create(
            nfeatures=nfeatures,
            contrastThreshold=0.015,
            edgeThreshold=10,
            sigma=1.2,
        )
    return None


def _create_matcher():
    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=64)
    return cv2.FlannBasedMatcher(index_params, search_params)


def _homography_geometry_valid(H, query_shape):
    try:
        h, w = query_shape[:2]
        corners = np.float32([[[0, 0]], [[w, 0]], [[w, h]], [[0, h]]])
        mapped = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
        if not np.all(np.isfinite(mapped)):
            return False
        edges = [
            float(np.linalg.norm(mapped[(index + 1) % 4] - mapped[index]))
            for index in range(4)
        ]
        min_edge = min(edges)
        max_edge = max(edges)
        if min_edge < 8.0 or max_edge > 2400.0 or max_edge / max(1.0, min_edge) > 8.0:
            return False
        area = abs(float(cv2.contourArea(mapped.astype(np.float32))))
        ratio = area / max(1.0, float(w * h))
        return 0.05 <= ratio <= 90.0
    except Exception:
        return False


def _update_homography_world_scale(owner, H, player_local, scale):
    try:
        x, y = float(player_local[0]), float(player_local[1])
        delta = 8.0
        pts = np.float32([[[x, y]], [[x + delta, y]], [[x, y + delta]]])
        mapped = cv2.perspectiveTransform(pts, H).reshape(-1, 2)
        dx = float(np.linalg.norm(mapped[1] - mapped[0])) / delta / max(0.001, scale)
        dy = float(np.linalg.norm(mapped[2] - mapped[0])) / delta / max(0.001, scale)
        value = (dx + dy) * 0.5
        if 0.4 <= value <= 20.0:
            setattr(owner, "_sift_v2_world_per_query_px", value)
    except Exception:
        pass


def _clahe_gray(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _edge_image(gray):
    sx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(sx, sy)
    return cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def _angle_delta(target, current):
    return ((float(target) - float(current) + 180.0) % 360.0) - 180.0


def _stabilize_player_angle(owner, angle, now=None):
    if angle is None:
        try:
            setattr(owner, "_sift_v2_player_angle_changed", False)
        except Exception:
            pass
        return None
    raw = float(angle) % 360.0
    if now is None:
        now = time.time()
    prev = getattr(owner, "_sift_v2_player_angle", None)
    prev_time = float(getattr(owner, "_sift_v2_player_angle_time", 0.0) or 0.0)
    if prev is None or now - prev_time > 0.75:
        try:
            setattr(owner, "_sift_v2_player_angle", raw)
            setattr(owner, "_sift_v2_player_angle_time", now)
            setattr(owner, "_sift_v2_player_angle_pending", None)
            setattr(owner, "_sift_v2_player_angle_changed", False)
        except Exception:
            pass
        return raw

    diff = _angle_delta(raw, prev)
    abs_diff = abs(diff)
    changed = abs_diff > 18.0
    pending = getattr(owner, "_sift_v2_player_angle_pending", None)
    if abs_diff > 125.0:
        if pending is not None and abs(_angle_delta(raw, pending)) < 34.0:
            stable = raw
            pending = None
            changed = True
        else:
            stable = float(prev) % 360.0
            pending = raw
            changed = True
    elif abs_diff > 48.0:
        stable = (float(prev) + diff * 0.72) % 360.0
        pending = None
    elif abs_diff < 2.2:
        stable = float(prev) % 360.0
        pending = None
        changed = False
    else:
        stable = raw
        pending = None

    try:
        setattr(owner, "_sift_v2_player_angle", stable)
        setattr(owner, "_sift_v2_player_angle_time", now)
        setattr(owner, "_sift_v2_player_angle_pending", pending)
        setattr(owner, "_sift_v2_player_angle_changed", changed)
        setattr(owner, "_sift_v2_skip_motion_until", now + 0.10 if changed else 0.0)
    except Exception:
        pass
    return stable


def _reset_player_angle_state(owner, clear_angle=False):
    try:
        if clear_angle:
            setattr(owner, "_sift_v2_player_angle", None)
        setattr(owner, "_sift_v2_player_angle_time", 0.0)
        setattr(owner, "_sift_v2_player_angle_pending", None)
        setattr(owner, "_sift_v2_player_angle_changed", False)
        setattr(owner, "_sift_v2_skip_motion_until", 0.0)
    except Exception:
        pass


def _arrow_angle_from_points(points_x, points_y):
    if len(points_x) < 8:
        return None, 0.0
    pts = np.column_stack((points_x, points_y)).astype(np.float32)
    center = pts.mean(axis=0)
    centered = pts - center
    try:
        x_min = int(np.floor(float(points_x.min())))
        y_min = int(np.floor(float(points_y.min())))
        local_x = np.maximum(0, np.rint(points_x - x_min + 1).astype(np.int32))
        local_y = np.maximum(0, np.rint(points_y - y_min + 1).astype(np.int32))
        mask = np.zeros((int(local_y.max()) + 2, int(local_x.max()) + 2), dtype=np.uint8)
        mask[local_y, local_x] = 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            contour = max(contours, key=cv2.contourArea)
            hull = cv2.convexHull(contour)
            perimeter = cv2.arcLength(hull, True)
            approx = cv2.approxPolyDP(hull, max(1.0, perimeter * 0.025), True)
            vertices = approx.reshape(-1, 2).astype(np.float32)
            if 3 <= len(vertices) <= 8:
                best_vertex = None
                best_angle = None
                for index, vertex in enumerate(vertices):
                    prev_vertex = vertices[(index - 1) % len(vertices)]
                    next_vertex = vertices[(index + 1) % len(vertices)]
                    a = prev_vertex - vertex
                    b = next_vertex - vertex
                    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
                    if denom <= 1e-6:
                        continue
                    cos_value = max(-1.0, min(1.0, float(np.dot(a, b) / denom)))
                    corner_angle = math.degrees(math.acos(cos_value))
                    if best_angle is None or corner_angle < best_angle:
                        best_angle = corner_angle
                        best_vertex = vertex
                if best_vertex is not None and best_angle is not None:
                    if best_angle < 82.0 or (len(vertices) <= 4 and best_angle < 108.0):
                        tip_x = float(best_vertex[0] + x_min - 1)
                        tip_y = float(best_vertex[1] + y_min - 1)
                        tip_dx = tip_x - float(center[0])
                        tip_dy = tip_y - float(center[1])
                        if math.hypot(tip_dx, tip_dy) >= 3.0:
                            angle = (math.degrees(math.atan2(tip_dx, -tip_dy)) + 360.0) % 360.0
                            confidence = 1.0 + max(0.0, 108.0 - best_angle) / 52.0 + max(0.0, 7.0 - float(len(vertices))) * 0.12
                            return angle, confidence
    except Exception:
        pass

    try:
        cov = np.cov(centered, rowvar=False)
        values, vectors = np.linalg.eigh(cov)
    except Exception:
        return None, 0.0
    major_index = int(np.argmax(values))
    minor_index = 1 - major_index
    major_value = float(max(values[major_index], 1e-6))
    minor_value = float(max(values[minor_index], 1e-6))
    elongation = math.sqrt(major_value / minor_value)
    if elongation < 1.12:
        return None, elongation

    major = vectors[:, major_index].astype(np.float32)
    if float(np.linalg.norm(major)) <= 1e-6:
        return None, elongation
    major = major / float(np.linalg.norm(major))
    perp = np.array([-major[1], major[0]], dtype=np.float32)
    projection = centered @ major
    perpendicular = centered @ perp
    high = float(np.percentile(projection, 82))
    low = float(np.percentile(projection, 18))
    positive = projection >= high
    negative = projection <= low
    if int(np.count_nonzero(positive)) < 3 or int(np.count_nonzero(negative)) < 3:
        return None, elongation

    pos_width = float(np.std(perpendicular[positive]))
    neg_width = float(np.std(perpendicular[negative]))
    pos_count = float(np.count_nonzero(positive))
    neg_count = float(np.count_nonzero(negative))
    pos_score = pos_width + pos_count * 0.025
    neg_score = neg_width + neg_count * 0.025
    if abs(pos_score - neg_score) < 0.45 and elongation < 1.45:
        return None, elongation

    tip_sign = 1.0 if pos_score < neg_score else -1.0
    tip_vector = major * tip_sign
    angle = (math.degrees(math.atan2(float(tip_vector[0]), -float(tip_vector[1]))) + 360.0) % 360.0
    return angle, elongation


def _center_player_marker_angle(hsv):
    h, w = hsv.shape[:2]
    center_x = w / 2.0
    center_y = h / 2.0
    min_side = min(w, h)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    yy, xx = np.indices((h, w))
    dx = xx.astype(np.float32) - float(center_x)
    dy = yy.astype(np.float32) - float(center_y)
    rr = np.sqrt(dx * dx + dy * dy)

    best_angle = None
    best_score = None
    marker_found = False
    area_min = max(6, int(min_side * min_side * 0.0018))
    area_max = max(96, int(min_side * min_side * 0.075))

    # The real minimap keeps the player marker near the circle center. Search only
    # there; route/resource icons around the edge are much brighter decoys.
    for tier, (sat_min, val_min, radius_ratio, core_ratio) in enumerate(
        (
            (165, 140, 0.24, 0.12),
            (150, 135, 0.25, 0.135),
            (132, 130, 0.25, 0.15),
            (116, 125, 0.24, 0.13),
        )
    ):
        orange = (
            (hue >= 5)
            & (hue <= 36)
            & (sat >= sat_min)
            & (val >= val_min)
            & (rr <= min_side * radius_ratio)
        )
        orange = orange.astype(np.uint8) * 255
        count, labels, stats, centroids = cv2.connectedComponentsWithStats(orange, 8)
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area < area_min or area > area_max:
                continue
            x = int(stats[label, cv2.CC_STAT_LEFT])
            y = int(stats[label, cv2.CC_STAT_TOP])
            bw = int(stats[label, cv2.CC_STAT_WIDTH])
            bh = int(stats[label, cv2.CC_STAT_HEIGHT])
            if bw < 3 or bh < 3 or bw > min_side * 0.48 or bh > min_side * 0.48:
                continue
            mx, my = centroids[label]
            center_dist = math.hypot(float(mx) - center_x, float(my) - center_y)
            if center_dist > min_side * core_ratio:
                continue
            marker_found = True
            points_y, points_x = np.nonzero(labels == label)
            angle, confidence = _arrow_angle_from_points(
                points_x.astype(np.float32),
                points_y.astype(np.float32),
            )
            if angle is None:
                continue
            score = (3 - tier) * 120.0 + min(float(confidence), 3.2) * 120.0 + area * 0.22 - center_dist * 18.0
            if best_score is None or score > best_score:
                best_score = score
                best_angle = angle

    if marker_found:
        cone = (
            (val >= 175)
            & (sat <= 105)
            & (rr >= min_side * 0.025)
            & (rr <= min_side * 0.30)
        )
        cone_count = int(np.count_nonzero(cone))
        if cone_count >= max(18, int(min_side * min_side * 0.003)):
            weights = np.maximum(0.0, val.astype(np.float32) - 150.0)
            total = float(weights[cone].sum())
            if total > 0.0:
                vx = float((dx[cone] * weights[cone]).sum() / total)
                vy = float((dy[cone] * weights[cone]).sum() / total)
                vector_len = math.hypot(vx, vy)
                if vector_len >= min_side * 0.04:
                    angle = (math.degrees(math.atan2(vx, -vy)) + 360.0) % 360.0
                    return True, angle

    return marker_found, best_angle


def _detect_player_local_bgr(bgr):
    h, w = bgr.shape[:2]
    center_x = w / 2.0
    center_y = h / 2.0
    min_side = min(w, h)
    radius = min_side * 0.39
    preferred_radius = min_side * 0.28
    try:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        orange_low = cv2.inRange(hsv, (0, 120, 145), (8, 255, 255))
        orange_main = cv2.inRange(hsv, (8, 105, 145), (34, 255, 255))
        orange = cv2.bitwise_or(orange_low, orange_main)
        white = cv2.inRange(hsv, (0, 0, 210), (180, 65, 255))
    except Exception:
        return (center_x, center_y), False, None

    marker_found, center_angle = _center_player_marker_angle(hsv)
    if marker_found:
        return (center_x, center_y), True, center_angle

    circle_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(circle_mask, (int(center_x), int(center_y)), int(radius), 255, -1)
    orange = cv2.bitwise_and(orange, circle_mask)
    white = cv2.bitwise_and(white, circle_mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    orange = cv2.morphologyEx(orange, cv2.MORPH_OPEN, kernel)
    orange = cv2.morphologyEx(orange, cv2.MORPH_CLOSE, kernel)

    count, labels, stats, centroids = cv2.connectedComponentsWithStats(orange, 8)
    if count <= 1:
        return (center_x, center_y), False, None

    area_min = max(12, int(w * h * 0.00035))
    area_max = max(180, int(w * h * 0.060))
    max_box = min_side * 0.36
    best_label = None
    best_score = None
    best_box = None
    best_angle = None
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < area_min or area > area_max:
            continue
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        bw = int(stats[label, cv2.CC_STAT_WIDTH])
        bh = int(stats[label, cv2.CC_STAT_HEIGHT])
        if bw < 3 or bh < 3 or bw > max_box or bh > max_box:
            continue
        aspect = bw / max(1.0, float(bh))
        if aspect < 0.28 or aspect > 3.6:
            continue
        cx, cy = centroids[label]
        center_dist = math.hypot(float(cx) - center_x, float(cy) - center_y)
        if center_dist > radius:
            continue
        pad = max(4, int(max(bw, bh) * 0.45))
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w, x + bw + pad)
        y2 = min(h, y + bh + pad)
        white_near = int(np.count_nonzero(white[y1:y2, x1:x2]))
        compactness = area / max(1.0, float(bw * bh))
        if white_near < max(3, int(area * 0.04)) and compactness < 0.18:
            continue

        orange_yy, orange_xx = np.nonzero(labels[y1:y2, x1:x2] == label)
        if len(orange_xx) < 8:
            continue
        angle, arrow_confidence = _arrow_angle_from_points(
            orange_xx.astype(np.float32) + x1,
            orange_yy.astype(np.float32) + y1,
        )
        arrow_bonus = max(0.0, min(2.6, arrow_confidence)) * 150.0
        if angle is None:
            continue

        center_bonus = max(0.0, preferred_radius - center_dist) * 4.0
        center_penalty = max(0.0, center_dist - preferred_radius) * 8.0
        white_score = min(float(white_near), area * 1.8) * 0.72
        size_score = min(float(area), area_max * 0.55) * 0.35
        score = center_bonus + arrow_bonus + white_score + size_score + compactness * 45.0 - center_penalty
        if best_score is None or score > best_score:
            best_score = score
            best_label = label
            best_box = (x1, y1, x2, y2)
            best_angle = angle

    if best_label is None or best_box is None:
        return (center_x, center_y), False, None

    x1, y1, x2, y2 = best_box
    component = (labels[y1:y2, x1:x2] == best_label)
    support = np.logical_or(component, white[y1:y2, x1:x2] > 0)
    yy, xx = np.nonzero(support)
    if len(xx) == 0:
        return (center_x, center_y), False, None
    xx = xx + x1
    yy = yy + y1
    anchor_x = (float(xx.min()) + float(xx.max())) * 0.5
    anchor_y = (float(yy.min()) + float(yy.max())) * 0.5
    pixels = bgr[yy, xx].astype(np.float32)
    blue = pixels[:, 0]
    green = pixels[:, 1]
    red = pixels[:, 2]
    orange_weight = np.maximum(0.0, red - blue) + np.maximum(0.0, red - green) * 0.55
    white_weight = ((red > 225) & (green > 220) & (blue > 200)).astype(np.float32) * 8.0
    weights = np.maximum(1.0, orange_weight + white_weight)
    total = float(weights.sum())
    if total < 220.0:
        return (center_x, center_y), False, None
    weighted_x = float((xx.astype(np.float32) * weights).sum() / total)
    weighted_y = float((yy.astype(np.float32) * weights).sum() / total)
    anchor_dist = math.hypot(anchor_x - center_x, anchor_y - center_y)
    if anchor_dist > min_side * 0.20:
        return (center_x, center_y), False, None
    return (center_x, center_y), True, best_angle


def _prepare_query(bgr):
    h, w = bgr.shape[:2]
    _player_local, player_found, player_angle = _detect_player_local_bgr(bgr)
    max_edge = max(h, w)
    scale = 1.0
    if max_edge > SIFT_QUERY_MAX_EDGE:
        scale = SIFT_QUERY_MAX_EDGE / float(max_edge)
        bgr = cv2.resize(bgr, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    qh, qw = bgr.shape[:2]

    mask = np.zeros((qh, qw), dtype=np.uint8)
    center = (qw // 2, qh // 2)
    axes = (
        max(2, int(qw * 0.5 * SIFT_MINIMAP_ELLIPSE_SCALE)),
        max(2, int(qh * 0.5 * SIFT_MINIMAP_ELLIPSE_SCALE)),
    )
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)

    exclude_radius = int(min(qw, qh) * SIFT_MINIMAP_CENTER_EXCLUDE_RADIUS_RATIO)
    if exclude_radius > 0:
        cv2.circle(mask, center, exclude_radius, 0, -1)
        player_center = (int(qw / 2.0), int(qh / 2.0))
        cv2.circle(mask, player_center, exclude_radius, 0, -1)

    gray = _clahe_gray(bgr)
    query_player_local = (float(qw / 2.0), float(qh / 2.0))
    return gray, mask, scale, query_player_local, player_found, player_angle


def _minimap_content_valid(bgr):
    h, w = bgr.shape[:2]
    if h < 32 or w < 32:
        return False, "截图过小"
    try:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    except Exception:
        return False, "画面解析失败"
    yy, xx = np.ogrid[:h, :w]
    cx = w / 2.0
    cy = h / 2.0
    radius = min(w, h) * 0.47
    circle = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= radius * radius
    if not np.any(circle):
        return False, "小地图区域为空"
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    circle_count = int(np.count_nonzero(circle))
    sat_mean = float(sat[circle].mean())
    val_mean = float(val[circle].mean())
    gray_std = float(gray[circle].std())
    terrain = circle & (
        (((hue >= 28) & (hue <= 96) & (sat >= 22) & (val >= 55))
        | ((hue >= 8) & (hue <= 34) & (sat >= 20) & (val >= 70))
        | ((hue >= 92) & (hue <= 130) & (sat >= 18) & (val >= 55)))
    )
    terrain_ratio = float(np.count_nonzero(terrain)) / max(1, circle_count)
    if val_mean < 28 or gray_std < 8:
        return False, "画面过暗或加载中"
    if terrain_ratio < 0.11 and sat_mean < 42:
        return False, "不像小地图画面"
    return True, ""


def _owner_map_layer(owner):
    layer = str(getattr(owner, "current_layer", "G") or "G").upper().strip()
    if layer in {"B1", "-1"}:
        return "B1"
    if layer in {"B2", "-2"}:
        return "B2"
    return "G"


def _minimap_looks_underground(bgr):
    try:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    except Exception:
        return False
    h, w = hsv.shape[:2]
    if h < 32 or w < 32:
        return False
    yy, xx = np.ogrid[:h, :w]
    cx = w / 2.0
    cy = h / 2.0
    radius = min(w, h) * 0.43
    circle = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= radius * radius
    if not np.any(circle):
        return False
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    circle_count = max(1, int(np.count_nonzero(circle)))
    cave_brown = circle & (hue >= 5) & (hue <= 34) & (sat >= 22) & (val >= 35) & (val <= 170)
    cave_gray = circle & (sat <= 58) & (val >= 35) & (val <= 150)
    cave_dark = circle & (val >= 25) & (val <= 115) & (sat <= 140)
    outdoor_green = circle & (hue >= 36) & (hue <= 94) & (sat >= 42) & (val >= 72)
    outdoor_water = circle & (hue >= 92) & (hue <= 132) & (sat >= 38) & (val >= 72)
    cave_ratio = float(np.count_nonzero(cave_brown | cave_gray | cave_dark)) / circle_count
    outdoor_ratio = float(np.count_nonzero(outdoor_green | outdoor_water)) / circle_count
    val_mean = float(val[circle].mean())
    return cave_ratio >= 0.46 and outdoor_ratio <= 0.34 and val_mean <= 145.0


def _minimap_layer_mismatch(owner, bgr):
    layer = _owner_map_layer(owner)
    underground = _minimap_looks_underground(bgr)
    if layer == "G" and underground:
        return True, "当前导航是地上，但小地图像地底层，暂停定位以避免误定位到海上"
    if layer in {"B1", "B2"} and not underground:
        return True, f"当前导航是地底 {layer}，但小地图像地上，暂停定位以避免跨图层误定位"
    return False, ""


def _template_sources(query_gray, query_mask):
    edge = _edge_image(query_gray)
    masked_edge = cv2.bitwise_and(edge, edge, mask=query_mask)
    masked_gray = cv2.bitwise_and(query_gray, query_gray, mask=query_mask)
    return masked_edge, masked_gray


def _smooth_position(last_pos, new_pos, lost_frames):
    if not last_pos:
        return new_pos
    dx = new_pos[0] - last_pos[0]
    dy = new_pos[1] - last_pos[1]
    dist = math.hypot(dx, dy)
    if lost_frames > 0:
        if dist > 180:
            return new_pos
        alpha = 0.92
    elif dist < 0.9:
        return last_pos
    elif dist < 18:
        alpha = 0.58
    elif dist < 25:
        alpha = 0.66
    elif dist < 180:
        alpha = 0.72
    else:
        alpha = 0.86
    return (last_pos[0] + dx * alpha, last_pos[1] + dy * alpha)


def _store_prev_query(owner, query_gray, query_mask):
    setattr(owner, "_sift_v2_prev_gray", query_gray.copy())
    setattr(owner, "_sift_v2_prev_mask", query_mask.copy())


def _relative_motion_position(owner, query_gray, query_mask):
    prev = getattr(owner, "_sift_v2_prev_gray", None)
    prev_mask = getattr(owner, "_sift_v2_prev_mask", None)
    last = _last_world_pos(owner)
    if prev is None or last is None or prev.shape != query_gray.shape:
        return None, 0.0

    try:
        mask = query_mask
        if prev_mask is not None and prev_mask.shape == query_mask.shape:
            mask = cv2.bitwise_and(query_mask, prev_mask)
        p = cv2.bitwise_and(prev, prev, mask=mask).astype(np.float32)
        q = cv2.bitwise_and(query_gray, query_gray, mask=mask).astype(np.float32)
        window = cv2.createHanningWindow((p.shape[1], p.shape[0]), cv2.CV_32F)
        shift, response = cv2.phaseCorrelate(p, q, window)
    except Exception:
        return None, 0.0

    if response < SIFT_MOTION_MIN_RESPONSE:
        return None, float(response)

    dx, dy = float(shift[0]), float(shift[1])
    if abs(dx) > query_gray.shape[1] * 0.32 or abs(dy) > query_gray.shape[0] * 0.32:
        return None, float(response)

    world_per_px = float(getattr(owner, "_sift_v2_world_per_query_px", SIFT_DEFAULT_WORLD_PER_MINIMAP_PIXEL))
    # The minimap texture moves opposite to the player icon, so world motion is inverted.
    pos = (last[0] - dx * world_per_px, last[1] - dy * world_per_px)
    return pos, float(response)


def _last_world_pos(owner):
    for name in (
        "minimap_last_world_pos",
        "_sift_v2_last_world",
        "route_preview_player_world_pos",
        "player_world_pos",
        "current_world_pos",
        "ai_world_pos",
        "tracked_world_pos",
        "minimap_world_pos",
    ):
        value = getattr(owner, name, None)
        if value:
            try:
                return (float(value[0]), float(value[1]))
            except Exception:
                pass
    for item_name in (
        "route_preview_player_item",
        "player_position_item",
        "minimap_player_item",
        "current_position_item",
    ):
        item = getattr(owner, item_name, None)
        if item is None:
            continue
        try:
            pos = item.scenePos()
            return (float(pos.x()), float(pos.y()))
        except Exception:
            pass
    return None


def _set_last_world_pos(owner, pos):
    setattr(owner, "_sift_v2_last_world", pos)
    setattr(owner, "minimap_last_world_pos", pos)
    setattr(owner, "route_preview_player_world_pos", pos)
    setattr(owner, "player_world_pos", pos)
    setattr(owner, "current_world_pos", pos)
    setattr(owner, "ai_world_pos", pos)
    setattr(owner, "tracked_world_pos", pos)
    setattr(owner, "minimap_world_pos", pos)


def _set_status(owner, text):
    candidates = (
        "minimap_status_label",
        "ai_minimap_status_label",
        "follow_status_label",
        "status_label",
        "route_status_label",
    )
    for name in candidates:
        label = getattr(owner, name, None)
        if label is not None and hasattr(label, "setText"):
            try:
                label.setText(str(text))
                return True
            except Exception:
                pass
    if QLabel is not None:
        try:
            for value in owner.__dict__.values():
                if isinstance(value, QLabel):
                    old = value.text()
                    if any(key in old for key in ("小地图", "SIFT", "定位", "跟随", "未启用")):
                        value.setText(str(text))
                        return True
        except Exception:
            pass
    return False


def _iter_owner_values(owner):
    try:
        for value in owner.__dict__.values():
            yield value
    except Exception:
        return


def _find_route_view(owner):
    preferred = (
        "route_preview_view",
        "preview_view",
        "navigation_map_view",
        "nav_map_view",
        "map_view",
        "view",
    )
    for name in preferred:
        value = getattr(owner, name, None)
        if value is not None and hasattr(value, "mapToScene") and hasattr(value, "viewport"):
            return value
    for value in _iter_owner_values(owner):
        if hasattr(value, "mapToScene") and hasattr(value, "viewport") and hasattr(value, "scene"):
            return value
    return None


def _ensure_player_item(owner, pos=None):
    existing = getattr(owner, "_sift_v2_player_item", None)
    if existing is not None:
        return existing
    for name in (
        "route_preview_player_item",
        "player_position_item",
        "minimap_player_item",
        "current_position_item",
    ):
        item = getattr(owner, name, None)
        if item is not None and hasattr(item, "setPos"):
            setattr(owner, "_sift_v2_player_item", item)
            return item
    create_player = getattr(owner, "set_route_preview_player_position", None)
    if pos is not None and callable(create_player):
        try:
            create_player(float(pos[0]), float(pos[1]))
            item = getattr(owner, "route_preview_player_item", None)
            if item is not None:
                setattr(owner, "_sift_v2_player_item", item)
                return item
        except Exception:
            pass
    if QGraphicsEllipseItem is None or QColor is None or QBrush is None or QPen is None:
        return None
    view = _find_route_view(owner)
    if view is None:
        return None
    try:
        scene = view.scene()
    except Exception:
        scene = None
    if scene is None:
        return None
    try:
        item = QGraphicsEllipseItem(-9, -9, 18, 18)
        item.setPen(QPen(QColor(35, 255, 80), 3))
        item.setBrush(QBrush(QColor(35, 255, 80, 110)))
        item.setZValue(200000)
        scene.addItem(item)
        if pos is not None:
            item.setPos(float(pos[0]), float(pos[1]))
        item.setVisible(True)
        setattr(owner, "_sift_v2_player_item", item)
        setattr(owner, "route_preview_player_item", item)
        return item
    except Exception:
        return None


def _anchor_to_view_center(owner):
    last = _last_world_pos(owner)
    if last is not None:
        _apply_world_pos(owner, last)
        return last
    view = _find_route_view(owner)
    if view is None:
        return None
    try:
        center = view.viewport().rect().center()
        scene_pos = view.mapToScene(center)
        pos = (float(scene_pos.x()), float(scene_pos.y()))
    except Exception:
        try:
            rect = view.scene().sceneRect()
            pos = (float(rect.center().x()), float(rect.center().y()))
        except Exception:
            return None
    _apply_world_pos(owner, pos)
    _set_status(owner, "已校准到导航地图中心，SIFT跟随待启动")
    return pos


def _ensure_follow_timer_running(owner):
    if QTimer is None:
        return False
    for name, value in list(getattr(owner, "__dict__", {}).items()):
        if not hasattr(value, "start") or not hasattr(value, "isActive"):
            continue
        lower = str(name).lower()
        if "minimap" in lower or "follow" in lower or "sift" in lower:
            try:
                if not value.isActive():
                    value.start(80)
                return True
            except Exception:
                pass
    timer = getattr(owner, "_sift_v2_follow_timer", None)
    if timer is None:
        try:
            timer = QTimer(owner)
            timer.setInterval(80)
            timer.timeout.connect(lambda: update_minimap_follow_v2(owner))
            setattr(owner, "_sift_v2_follow_timer", timer)
        except Exception:
            return False
    try:
        if timer.interval() > 33:
            timer.setInterval(33)
        if not timer.isActive():
            timer.start(33)
        _set_status(owner, "SIFT跟随已启动")
        return True
    except Exception:
        return False


def _owner_follow_should_run(owner):
    if bool(getattr(owner, "minimap_follow_enabled", False)):
        return True
    if bool(getattr(owner, "minimap_circle_locked", False)):
        return True
    return bool(getattr(owner, "_sift_v2_force_follow", False))


def _force_full_relocalize(owner):
    try:
        setattr(owner, "_sift_v2_lost_frames", SIFT_FULL_RELOCALIZE_AFTER)
        setattr(owner, "_sift_v2_prev_gray", None)
        setattr(owner, "_sift_v2_prev_mask", None)
        setattr(owner, "_sift_v2_last_full_match_time", 0.0)
        setattr(owner, "minimap_calibrated", False)
        setattr(owner, "minimap_reference_image", None)
        setattr(owner, "minimap_reference_player_local", None)
        setattr(owner, "minimap_reference_world_pos", None)
        setattr(owner, "minimap_previous_image", None)
        setattr(owner, "minimap_previous_player_local", None)
        setattr(owner, "minimap_tracking_failures", 0)
    except Exception:
        pass


def _mark_invalid_minimap_frame(owner, now=None):
    if now is None:
        now = time.time()
    try:
        since = float(getattr(owner, "_sift_v2_invalid_since", 0.0) or 0.0)
    except Exception:
        since = 0.0
    if since <= 0.0:
        since = now
        try:
            setattr(owner, "_sift_v2_invalid_since", since)
        except Exception:
            pass
    try:
        setattr(owner, "_sift_v2_prev_gray", None)
        setattr(owner, "_sift_v2_prev_mask", None)
        setattr(owner, "_sift_v2_last_good_time", 0.0)
    except Exception:
        pass
    long_transition = now - since >= SIFT_INVALID_FULL_RELOCALIZE_AFTER
    if now - since >= 0.12:
        _reset_player_angle_state(owner, clear_angle=True)
    try:
        setattr(owner, "_sift_v2_transition_recover_long", long_transition)
        lost = int(getattr(owner, "_sift_v2_lost_frames", 0))
        if lost < SIFT_FULL_RELOCALIZE_AFTER:
            setattr(owner, "_sift_v2_lost_frames", min(max(lost, 1), 2))
        setattr(owner, "_sift_v2_last_full_match_time", 0.0)
    except Exception:
        pass
    return long_transition


def _clear_invalid_minimap_frame(owner, now=None):
    if now is None:
        now = time.time()
    try:
        since = float(getattr(owner, "_sift_v2_invalid_since", 0.0) or 0.0)
    except Exception:
        since = 0.0
    duration = max(0.0, now - since) if since > 0.0 else 0.0
    try:
        setattr(owner, "_sift_v2_invalid_since", 0.0)
        setattr(owner, "_sift_v2_transition_recover_long", duration >= SIFT_INVALID_FULL_RELOCALIZE_AFTER)
    except Exception:
        pass
    return duration


def _find_minimap_circle(owner):
    names = (
        "minimap_selection_circle",
        "minimap_circle",
        "minimap_selector",
        "selection_circle",
        "mini_map_circle",
        "minimap_range_widget",
    )
    for name in names:
        value = getattr(owner, name, None)
        if value is not None and hasattr(value, "geometry"):
            return value
    for value in _iter_owner_values(owner):
        try:
            cname = value.__class__.__name__.lower()
        except Exception:
            continue
        if "minimap" in cname and ("circle" in cname or "selection" in cname):
            if hasattr(value, "geometry"):
                return value
    return None


def _capture_minimap(owner):
    if QApplication is None:
        return None, "Qt截图不可用"
    capture = getattr(owner, "capture_minimap_region", None)
    if callable(capture):
        try:
            pixmap = capture()
            if pixmap is not None and not pixmap.isNull():
                return pixmap, ""
        except Exception:
            pass

    circle = _find_minimap_circle(owner)
    if circle is None:
        return None, "未找到小地图选择圈"
    try:
        region = getattr(owner, "minimap_circle_region", None)
        if region is None and hasattr(circle, "capture_region"):
            region = circle.capture_region()
        if region is not None:
            x, y = int(region["x"]), int(region["y"])
            w = h = int(region.get("size", region.get("width", 0)))
        else:
            geom = circle.geometry()
            if hasattr(circle, "mapToGlobal"):
                if hasattr(circle, "rect"):
                    top_left = circle.mapToGlobal(circle.rect().topLeft())
                else:
                    top_left = circle.mapToGlobal(geom.topLeft())
                x, y = int(top_left.x()), int(top_left.y())
            else:
                x, y = int(geom.x()), int(geom.y())
            w, h = int(geom.width()), int(geom.height())
    except Exception:
        return None, "读取小地图圈位置失败"
    if w < 32 or h < 32:
        return None, "小地图圈过小"
    screen = QApplication.primaryScreen()
    if screen is None:
        return None, "没有可用屏幕"
    circle_visible = False
    try:
        circle_visible = bool(circle.isVisible())
        if circle_visible:
            circle.hide()
            QApplication.processEvents()
        pixmap = screen.grabWindow(0, x, y, w, h)
    except Exception:
        return None, "截取小地图失败"
    finally:
        if circle_visible:
            try:
                circle.show()
                if bool(getattr(owner, "minimap_circle_locked", False)) and hasattr(circle, "set_locked_for_game"):
                    circle.set_locked_for_game(True)
            except Exception:
                pass
    if pixmap is None or pixmap.isNull():
        return None, "小地图截图为空"
    return pixmap, ""


def _apply_world_pos(owner, pos, angle=None):
    _set_last_world_pos(owner, pos)
    if angle is None:
        angle = getattr(owner, "_sift_v2_player_angle", None)
    elif angle is not None:
        try:
            setattr(owner, "_sift_v2_player_angle", float(angle))
        except Exception:
            pass
    handled_item_ids = set()
    set_preview = getattr(owner, "set_route_preview_player_position", None)
    if callable(set_preview):
        try:
            set_preview(float(pos[0]), float(pos[1]), angle)
            for item_name in ("route_preview_player_item", "_sift_v2_player_item"):
                item = getattr(owner, item_name, None)
                if item is not None:
                    handled_item_ids.add(id(item))
        except TypeError:
            try:
                set_preview(float(pos[0]), float(pos[1]))
            except Exception:
                pass
        except Exception:
            pass
    if not handled_item_ids:
        _ensure_player_item(owner, pos)
    for name in (
        "_sift_v2_player_item",
        "route_preview_player_item",
        "player_position_item",
        "minimap_player_item",
        "current_position_item",
    ):
        item = getattr(owner, name, None)
        if item is None:
            continue
        if id(item) in handled_item_ids:
            continue
        try:
            item.setPos(float(pos[0]), float(pos[1]))
        except Exception:
            try:
                item.setPos(QPointF(float(pos[0]), float(pos[1])))
            except Exception:
                pass
        try:
            item.setVisible(True)
        except Exception:
            pass
    follow_view = (
        bool(getattr(owner, "route_preview_auto_follow", True))
        and (
            bool(getattr(owner, "minimap_follow_enabled", False))
            or bool(getattr(owner, "minimap_circle_locked", False))
        )
    )
    for name in ("route_preview_view", "preview_view", "navigation_map_view", "nav_map_view", "map_view", "view"):
        view = getattr(owner, name, None)
        if view is None:
            continue
        if name in ("route_preview_view", "preview_view", "navigation_map_view", "nav_map_view") and follow_view:
            try:
                view.centerOn(float(pos[0]), float(pos[1]))
            except Exception:
                pass
        try:
            view.viewport().update()
        except Exception:
            try:
                view.update()
            except Exception:
                pass


def _keep_last_player_visible(owner):
    last = _last_world_pos(owner)
    if last is None:
        return None
    _apply_world_pos(owner, last, getattr(owner, "_sift_v2_player_angle", None))
    return last


def _result(ok, position=None, message="", match_count=0, inliers=0, method="SIFT", score=0.0, player_angle=None):
    return SiftTrackResult(
        ok=ok,
        position=position,
        world_pos=position,
        message=message,
        match_count=match_count,
        inliers=inliers,
        method=method,
        score=score,
        player_angle=player_angle,
    )


def prepare_sift_tracker_v2(owner, force=False):
    if cv2 is None or np is None:
        setattr(owner, "_sift_v2_error", "未安装 opencv-python，无法使用 SIFT。")
        return False

    map_path = _find_reference_map_path(owner)
    if not map_path:
        setattr(owner, "_sift_v2_error", "没有找到可用于匹配的纯净地图图片。")
        return False
    map_path = Path(map_path)
    if getattr(owner, "_sift_v2_ready", False) and not force:
        if str(getattr(owner, "_sift_v2_map_path", "")) == str(map_path):
            if getattr(owner, "_sift_v2_full_matcher", None) is None:
                setattr(owner, "_sift_v2_full_matcher", _build_full_matcher(getattr(owner, "_sift_v2_desc", None)))
            return True
        setattr(owner, "_sift_v2_ready", False)
        setattr(owner, "_sift_v2_prev_gray", None)
        setattr(owner, "_sift_v2_prev_mask", None)

    detector = _create_sift(SIFT_MAP_NFEATURES)
    if detector is None:
        setattr(owner, "_sift_v2_error", "当前 OpenCV 不支持 SIFT。")
        return False

    cache_path = _cache_path(owner)
    map_mtime = int(map_path.stat().st_mtime)
    loaded = False

    if cache_path.exists() and not force:
        try:
            data = np.load(str(cache_path), allow_pickle=False)
            if _cache_matches_reference(data, map_path, map_mtime):
                _load_sift_cache(owner, data)
                loaded = True
        except Exception:
            loaded = False

    if not loaded:
        bgr = _read_image(map_path)
        if bgr is None:
            setattr(owner, "_sift_v2_error", f"地图图片读取失败：{map_path}")
            return False

        h, w = bgr.shape[:2]
        scale = min(1.0, SIFT_REFERENCE_MAX_SIDE / float(max(h, w)))
        if scale < 1.0:
            ref = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        else:
            ref = bgr

        gray = _clahe_gray(ref)
        keypoints, desc = detector.detectAndCompute(gray, None)
        if desc is None or len(keypoints) < SIFT_MIN_MATCH_COUNT:
            setattr(owner, "_sift_v2_error", "地图 SIFT 特征过少，无法定位。")
            return False

        points = np.array([kp.pt for kp in keypoints], dtype=np.float32)
        desc = desc.astype(np.float32)
        setattr(owner, "_sift_v2_scale", float(scale))
        setattr(owner, "_sift_v2_points", points)
        setattr(owner, "_sift_v2_desc", desc)
        setattr(owner, "_sift_v2_shape", ref.shape[:2])
        cache_path = _write_cache_path(owner)
        try:
            np.savez_compressed(
                str(cache_path),
                version=SIFT_CACHE_VERSION,
                map_path=str(map_path),
                map_mtime=map_mtime,
                scale=float(scale),
                points=points,
                desc=desc,
                shape=np.array(ref.shape[:2], dtype=np.int32),
            )
        except Exception:
            pass

    full_bgr = _read_image(map_path)
    if full_bgr is not None:
        scale = getattr(owner, "_sift_v2_scale", 1.0)
        h, w = full_bgr.shape[:2]
        if scale < 1.0:
            ref = cv2.resize(full_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        else:
            ref = full_bgr
        gray = _clahe_gray(ref)
        setattr(owner, "_sift_v2_edge", _edge_image(gray))
        setattr(owner, "_sift_v2_gray", gray)

    setattr(owner, "_sift_v2_detector", _create_sift(SIFT_QUERY_NFEATURES))
    setattr(owner, "_sift_v2_matcher", _create_matcher())
    setattr(owner, "_sift_v2_full_matcher", _build_full_matcher(getattr(owner, "_sift_v2_desc", None)))
    setattr(owner, "_sift_v2_map_path", str(map_path))
    setattr(owner, "_sift_v2_ready", True)
    setattr(owner, "_sift_v2_error", "")
    if not hasattr(owner, "_sift_v2_lost_frames"):
        setattr(owner, "_sift_v2_lost_frames", 0)
    return True


def minimap_feature_image_and_mask_v2(owner, image):
    bgr = _qimage_to_bgr(image)
    if bgr is None:
        return None, None
    gray, mask, _, _, _, _ = _prepare_query(bgr)
    return gray, mask


def _local_reference_subset(owner, last_pos):
    points = getattr(owner, "_sift_v2_points", None)
    desc = getattr(owner, "_sift_v2_desc", None)
    scale = getattr(owner, "_sift_v2_scale", 1.0)
    lost = int(getattr(owner, "_sift_v2_lost_frames", 0))
    if points is None or desc is None or last_pos is None or lost >= SIFT_FULL_RELOCALIZE_AFTER:
        return points, desc, None, "全图"

    radius = min(SIFT_MAX_LOCAL_RADIUS, SIFT_LOCAL_SEARCH_RADIUS + lost * SIFT_LOST_EXPAND_STEP)
    center = np.array((last_pos[0] * scale, last_pos[1] * scale), dtype=np.float32)
    dist2 = np.sum((points - center) ** 2, axis=1)
    mask = dist2 <= (radius * scale) ** 2
    idx = np.flatnonzero(mask)
    if len(idx) < 80:
        return points, desc, None, "全图"
    return points[idx], desc[idx], idx, f"局部{int(radius)}"


def _homography_position(owner, query_gray, query_mask, player_local=None):
    detector = getattr(owner, "_sift_v2_detector", None) or _create_sift(SIFT_QUERY_NFEATURES)
    matcher = getattr(owner, "_sift_v2_matcher", None) or _create_matcher()
    qkps, qdesc = detector.detectAndCompute(query_gray, query_mask)
    if qdesc is None or len(qkps) < SIFT_MIN_MATCH_COUNT:
        return None, 0, 0, "小地图特征过少"

    last_pos = _last_world_pos(owner)
    ref_points, ref_desc, _, scope = _local_reference_subset(owner, last_pos)
    if ref_desc is None or len(ref_desc) < SIFT_MIN_MATCH_COUNT:
        return None, 0, 0, "地图特征缓存无效"

    full_reference = ref_desc is getattr(owner, "_sift_v2_desc", None)
    query_desc = np.ascontiguousarray(qdesc.astype(np.float32))
    try:
        full_matcher = getattr(owner, "_sift_v2_full_matcher", None) if full_reference else None
        if full_matcher is not None:
            matches = full_matcher.knnMatch(query_desc, k=2)
        else:
            train_desc = np.ascontiguousarray(ref_desc.astype(np.float32))
            matches = matcher.knnMatch(query_desc, train_desc, k=2)
    except Exception:
        return None, 0, 0, "SIFT匹配失败"

    good = []
    for pair in matches:
        if len(pair) < 2:
            continue
        m, n = pair
        if m.distance < SIFT_MATCH_RATIO * n.distance:
            good.append(m)

    if len(good) < SIFT_MIN_MATCH_COUNT:
        return None, len(good), 0, f"{scope}匹配点不足"

    qpts = np.float32([qkps[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    mpts = np.float32([ref_points[m.trainIdx] for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(qpts, mpts, cv2.RANSAC, SIFT_RANSAC_THRESHOLD)
    if H is None or mask is None:
        return None, len(good), 0, f"{scope}单应性失败"

    inliers = int(mask.ravel().sum())
    inlier_ratio = inliers / max(1, len(good))
    if inliers < SIFT_MIN_INLIER_COUNT or inlier_ratio < SIFT_MIN_INLIER_RATIO:
        return None, len(good), inliers, f"{scope}内点不足"

    if full_reference and (inliers < 9 or inlier_ratio < 0.52):
        return None, len(good), inliers, f"{scope}缃俊涓嶈冻"
    if not _homography_geometry_valid(H, query_gray.shape):
        return None, len(good), inliers, f"{scope}鍑犱綍涓嶇ǔ"

    h, w = query_gray.shape[:2]
    if player_local is None:
        player_local = (w / 2.0, h / 2.0)
    player_point = np.float32([[[float(player_local[0]), float(player_local[1])]]])
    mapped = cv2.perspectiveTransform(player_point, H)[0][0]
    scale = getattr(owner, "_sift_v2_scale", 1.0)
    world = (float(mapped[0] / scale), float(mapped[1] / scale))
    _update_homography_world_scale(owner, H, player_local, scale)

    if last_pos:
        jump = math.hypot(world[0] - last_pos[0], world[1] - last_pos[1])
        lost = int(getattr(owner, "_sift_v2_lost_frames", 0))
        allowed = SIFT_MAX_WORLD_JUMP + max(0, lost - 2) * 160
        if jump > allowed and lost < SIFT_FULL_RELOCALIZE_AFTER:
            return None, len(good), inliers, f"{scope}跳变过大"

    return world, len(good), inliers, f"{scope}SIFT"


def _template_position(owner, query_gray, query_mask, player_local=None):
    ref_edge = getattr(owner, "_sift_v2_edge", None)
    if ref_edge is None:
        return None, 0.0, "无模板图"

    qedge, qgray = _template_sources(query_gray, query_mask)
    h, w = qedge.shape[:2]
    if h < 24 or w < 24:
        return None, 0.0, "模板过小"
    if player_local is None:
        player_local = (w / 2.0, h / 2.0)

    last_pos = _last_world_pos(owner)
    scale = getattr(owner, "_sift_v2_scale", 1.0)
    lost = int(getattr(owner, "_sift_v2_lost_frames", 0))
    if not last_pos or lost >= SIFT_FULL_RELOCALIZE_AFTER:
        return None, 0.0, "跳过全图模板"
    search = ref_edge
    ox = oy = 0
    scope = "全图模板"

    if True:
        radius = min(SIFT_MAX_LOCAL_RADIUS, SIFT_LOCAL_SEARCH_RADIUS + lost * SIFT_LOST_EXPAND_STEP)
        cx = int(last_pos[0] * scale)
        cy = int(last_pos[1] * scale)
        r = int(radius * scale)
        x1 = max(0, cx - r)
        y1 = max(0, cy - r)
        x2 = min(ref_edge.shape[1], cx + r)
        y2 = min(ref_edge.shape[0], cy + r)
        if x2 - x1 > w + 12 and y2 - y1 > h + 12:
            search = ref_edge[y1:y2, x1:x2]
            ox, oy = x1, y1
            scope = f"局部模板{int(radius)}"

        else:
            return None, 0.0, "局部模板范围过小"

    if search.shape[0] < h or search.shape[1] < w:
        return None, 0.0, "模板搜索范围过小"

    best_score = -1.0
    best_pos = None
    best_factor = 1.0
    ref_gray = getattr(owner, "_sift_v2_gray", None)
    if ref_gray is None:
        ref_gray = ref_edge
    search_gray = ref_gray[oy : oy + search.shape[0], ox : ox + search.shape[1]]
    factors = (
        0.48,
        0.56,
        0.66,
        0.78,
        0.90,
        1.00,
        1.12,
        1.26,
        1.42,
        1.62,
        1.86,
        2.12,
        2.42,
        2.78,
        3.18,
    )
    for factor in factors:
        tw = max(16, int(w * factor))
        th = max(16, int(h * factor))
        if tw >= search.shape[1] or th >= search.shape[0]:
            continue
        interp = cv2.INTER_AREA if factor < 1.0 else cv2.INTER_LINEAR
        templ_edge = cv2.resize(qedge, (tw, th), interpolation=interp)
        templ_gray = cv2.resize(qgray, (tw, th), interpolation=interp)
        templ_mask = cv2.resize(query_mask, (tw, th), interpolation=cv2.INTER_NEAREST)
        try:
            res_edge = cv2.matchTemplate(search, templ_edge, cv2.TM_CCORR_NORMED, mask=templ_mask)
            res_gray = cv2.matchTemplate(search_gray, templ_gray, cv2.TM_CCORR_NORMED, mask=templ_mask)
            res = res_edge * 0.65 + res_gray * 0.35
        except Exception:
            try:
                res = cv2.matchTemplate(search, templ_edge, cv2.TM_CCOEFF_NORMED)
            except Exception:
                continue
        _, score, _, loc = cv2.minMaxLoc(res)
        if score > best_score:
            best_score = float(score)
            best_pos = (
                (ox + loc[0] + float(player_local[0]) * factor) / scale,
                (oy + loc[1] + float(player_local[1]) * factor) / scale,
            )
            best_factor = factor

    if best_pos is None or best_score < SIFT_TEMPLATE_MIN_SCORE:
        return None, best_score, f"{scope}失败"
    setattr(owner, "_sift_v2_world_per_query_px", max(0.6, best_factor / max(0.001, scale)))
    return best_pos, best_score, f"{scope}x{best_factor:.2f}"


def _try_motion_tracking(owner, query_gray, query_mask, player_angle, started, matches=0, inliers=0, keep_lost=False):
    motion, response = _relative_motion_position(owner, query_gray, query_mask)
    if motion is None:
        return None
    lost = int(getattr(owner, "_sift_v2_lost_frames", 0))
    last = _last_world_pos(owner)
    smooth = _smooth_position(last, motion, lost)
    _set_last_world_pos(owner, smooth)
    if keep_lost:
        setattr(owner, "_sift_v2_lost_frames", min(lost + 1, SIFT_FULL_RELOCALIZE_AFTER))
    else:
        setattr(owner, "_sift_v2_lost_frames", 0)
    setattr(owner, "_sift_v2_last_good_time", time.time())
    setattr(owner, "_sift_v2_pause_until", 0.0)
    try:
        setattr(owner, "_sift_v2_transition_recover_long", False)
    except Exception:
        pass
    _store_prev_query(owner, query_gray, query_mask)
    elapsed = (time.perf_counter() - started) * 1000.0
    msg = f"短时跟随 response:{response:.2f}，等待SIFT校正 {elapsed:.0f}ms"
    if player_angle is not None:
        setattr(owner, "_sift_v2_player_angle", player_angle)
    return _result(True, smooth, msg, matches, inliers, method="短时跟随", score=response, player_angle=player_angle)


def track_minimap_sift_v2(owner, image, *args, **kwargs):
    now = time.time()
    pause_until = float(getattr(owner, "_sift_v2_pause_until", 0.0) or 0.0)
    if now < pause_until:
        last = _last_world_pos(owner)
        remain = max(0.0, pause_until - now)
        return _result(False, last, f"过场/加载保护中，{remain:.1f}s 后重试", method="画面保护")

    if not prepare_sift_tracker_v2(owner):
        last = _last_world_pos(owner)
        error = getattr(owner, "_sift_v2_error", "SIFT未准备")
        return _result(False, last, error, method="SIFT")

    bgr = _qimage_to_bgr(image)
    if bgr is None:
        last = _last_world_pos(owner)
        return _result(False, last, "小地图截图无效", method="SIFT")

    query_gray, query_mask, _, player_local, player_found, player_angle = _prepare_query(bgr)
    started = time.perf_counter()
    if player_found:
        player_angle = _stabilize_player_angle(owner, player_angle, now)
    if not player_found:
        last = _last_world_pos(owner)
        _mark_invalid_minimap_frame(owner, now)
        setattr(owner, "_sift_v2_pause_until", time.time() + SIFT_INVALID_FRAME_COOLDOWN)
        try:
            setattr(owner, "_sift_v2_last_good_time", 0.0)
        except Exception:
            pass
        elapsed = (time.perf_counter() - started) * 1000.0
        msg = f"未识别到小洛克箭头，暂停定位并等待小地图恢复 {elapsed:.0f}ms"
        return _result(False, last, msg, method="画面保护")

    content_ok, content_reason = _minimap_content_valid(bgr)
    if not content_ok:
        last = _last_world_pos(owner)
        _mark_invalid_minimap_frame(owner, now)
        setattr(owner, "_sift_v2_pause_until", time.time() + SIFT_INVALID_FRAME_COOLDOWN)
        try:
            setattr(owner, "_sift_v2_last_good_time", 0.0)
        except Exception:
            pass
        elapsed = (time.perf_counter() - started) * 1000.0
        msg = f"{content_reason}，暂停定位并等待小地图恢复 {elapsed:.0f}ms"
        return _result(False, last, msg, method="画面保护")

    layer_mismatch, layer_reason = _minimap_layer_mismatch(owner, bgr)
    if layer_mismatch:
        last = _keep_last_player_visible(owner)
        _mark_invalid_minimap_frame(owner, now)
        setattr(owner, "_sift_v2_pause_until", time.time() + SIFT_INVALID_FRAME_COOLDOWN)
        elapsed = (time.perf_counter() - started) * 1000.0
        msg = f"{layer_reason} {elapsed:.0f}ms"
        return _result(False, last, msg, method="图层保护")

    lost_before = int(getattr(owner, "_sift_v2_lost_frames", 0))
    invalid_duration = _clear_invalid_minimap_frame(owner, now)
    if invalid_duration >= SIFT_INVALID_FULL_RELOCALIZE_AFTER and 0 < lost_before < 2:
        lost_before = SIFT_FULL_RELOCALIZE_AFTER
        try:
            setattr(owner, "_sift_v2_lost_frames", lost_before)
            setattr(owner, "_sift_v2_prev_gray", None)
            setattr(owner, "_sift_v2_prev_mask", None)
            setattr(owner, "_sift_v2_last_full_match_time", 0.0)
        except Exception:
            pass
    last_good = float(getattr(owner, "_sift_v2_last_good_time", 0.0) or 0.0)
    last_full = float(getattr(owner, "_sift_v2_last_full_match_time", 0.0) or 0.0)
    prev_gray = getattr(owner, "_sift_v2_prev_gray", None)
    recent_good = last_good > 0 and now - last_good <= SIFT_MOTION_MAX_GOOD_AGE
    angle_changed = bool(getattr(owner, "_sift_v2_player_angle_changed", False))
    skip_motion_until = float(getattr(owner, "_sift_v2_skip_motion_until", 0.0) or 0.0)
    motion_allowed = (not angle_changed) and now >= skip_motion_until
    if (
        prev_gray is not None
        and lost_before == 0
        and recent_good
        and last_full > 0
        and now - last_full < SIFT_FULL_MATCH_MIN_INTERVAL
        and motion_allowed
    ):
        motion_result = _try_motion_tracking(owner, query_gray, query_mask, player_angle, started)
        if motion_result is not None:
            return motion_result

    world, matches, inliers, reason = _homography_position(owner, query_gray, query_mask, player_local)
    method = "SIFT"
    score = 0.0

    if world is None:
        may_use_motion = (
            lost_before < SIFT_MOTION_MAX_LOST_FRAMES
            and recent_good
            and player_found
            and prev_gray is not None
            and motion_allowed
        )
        if may_use_motion:
            motion_result = _try_motion_tracking(
                owner,
                query_gray,
                query_mask,
                player_angle,
                started,
                matches,
                inliers,
                keep_lost=True,
            )
            if motion_result is not None:
                return motion_result
        fallback, score, template_reason = _template_position(owner, query_gray, query_mask, player_local)
        if fallback is not None:
            world = fallback
            method = "模板"
            reason = template_reason

    if world is not None:
        lost = int(getattr(owner, "_sift_v2_lost_frames", 0))
        last = _last_world_pos(owner)
        smooth = _smooth_position(last, world, lost)
        _set_last_world_pos(owner, smooth)
        setattr(owner, "_sift_v2_lost_frames", 0)
        setattr(owner, "_sift_v2_last_good_time", time.time())
        setattr(owner, "_sift_v2_last_full_match_time", time.time())
        setattr(owner, "_sift_v2_pause_until", 0.0)
        try:
            setattr(owner, "_sift_v2_transition_recover_long", False)
        except Exception:
            pass
        elapsed = (time.perf_counter() - started) * 1000.0
        if method == "模板":
            msg = f"模板定位 {reason} 分数:{score:.2f} {elapsed:.0f}ms"
        else:
            msg = f"SIFT定位 {reason} 匹配:{matches} 内点:{inliers} {elapsed:.0f}ms"
        _store_prev_query(owner, query_gray, query_mask)
        if player_angle is not None:
            setattr(owner, "_sift_v2_player_angle", player_angle)
        return _result(True, smooth, msg, matches, inliers, method=method, score=score, player_angle=player_angle)

    lost_before = int(getattr(owner, "_sift_v2_lost_frames", 0))
    last_good = float(getattr(owner, "_sift_v2_last_good_time", 0.0) or 0.0)
    may_use_motion = False and (
        lost_before < SIFT_MOTION_MAX_LOST_FRAMES
        and last_good > 0
        and time.time() - last_good <= SIFT_MOTION_MAX_GOOD_AGE
        and player_found
    )
    if may_use_motion:
        motion, response = _relative_motion_position(owner, query_gray, query_mask)
        if motion is not None:
            lost = int(getattr(owner, "_sift_v2_lost_frames", 0))
            last = _last_world_pos(owner)
            smooth = _smooth_position(last, motion, lost)
            _set_last_world_pos(owner, smooth)
            setattr(owner, "_sift_v2_lost_frames", min(lost + 1, SIFT_FULL_RELOCALIZE_AFTER))
            _store_prev_query(owner, query_gray, query_mask)
            elapsed = (time.perf_counter() - started) * 1000.0
            msg = f"短时跟随 response:{response:.2f}，等待SIFT校正 {elapsed:.0f}ms"
            if player_angle is not None:
                setattr(owner, "_sift_v2_player_angle", player_angle)
            return _result(True, smooth, msg, matches, inliers, method="短时跟随", score=response, player_angle=player_angle)

    lost = int(getattr(owner, "_sift_v2_lost_frames", 0)) + 1
    if bool(getattr(owner, "_sift_v2_transition_recover_long", False)):
        lost = max(lost, SIFT_FULL_RELOCALIZE_AFTER)
        try:
            setattr(owner, "_sift_v2_transition_recover_long", False)
        except Exception:
            pass
    setattr(owner, "_sift_v2_lost_frames", lost)
    cooldown = SIFT_FULL_RELOCALIZE_COOLDOWN if lost >= SIFT_FULL_RELOCALIZE_AFTER else SIFT_FAILED_MATCH_COOLDOWN
    setattr(owner, "_sift_v2_pause_until", time.time() + cooldown)
    last = _last_world_pos(owner)
    msg = f"SIFT未定位，保持上次位置 匹配:{matches} 内点:{inliers} 丢失:{lost} 原因:{reason}"
    return _result(False, last, msg, matches, inliers, method="SIFT")


def update_minimap_follow_v2(owner, *args, **kwargs):
    pause_until = float(getattr(owner, "_sift_v2_pause_until", 0.0) or 0.0)
    now = time.time()
    if now < pause_until:
        last = _keep_last_player_visible(owner)
        message = f"过场/加载保护中，{max(0.0, pause_until - now):.1f}s 后重试"
        _set_status(owner, message)
        return _result(False, last, message, method="画面保护")

    pixmap, error = _capture_minimap(owner)
    if pixmap is None:
        _keep_last_player_visible(owner)
        _set_status(owner, error)
        return None

    result = track_minimap_sift_v2(owner, pixmap)
    message = result.get("message", "")
    position = result.get("position")
    if position is not None:
        _apply_world_pos(owner, position, result.get("player_angle"))
        if result.get("ok"):
            auto_complete = getattr(owner, "auto_complete_route_at_position", None)
            if callable(auto_complete):
                try:
                    auto_complete(float(position[0]), float(position[1]))
                except Exception:
                    pass
    if message:
        _set_status(owner, message)
    return result
