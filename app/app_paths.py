import shutil
import sys
from pathlib import Path


APP_NAME = "洛克王国多功能辅助工具"
PROJECT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
RUNTIME_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_DIR
STATIC_DATA_DIR = PROJECT_DIR / "data"
ASSETS_DIR = PROJECT_DIR / "assets"
USER_DATA_DIR = RUNTIME_DIR / "user_data"
USER_CACHE_DIR = USER_DATA_DIR / "cache"
LOG_DIR = RUNTIME_DIR


def ensure_user_data_layout():
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def data_path(*parts):
    return STATIC_DATA_DIR.joinpath(*parts)


def asset_path(*parts):
    return ASSETS_DIR.joinpath(*parts)


def legacy_data_path(*parts):
    return STATIC_DATA_DIR.joinpath(*parts)


def user_data_path(*parts):
    ensure_user_data_layout()
    path = USER_DATA_DIR.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def user_cache_path(*parts):
    ensure_user_data_layout()
    path = USER_CACHE_DIR.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def migrate_user_file(*parts):
    target = user_data_path(*parts)
    legacy = legacy_data_path(*parts)
    if not target.exists() and legacy.exists() and legacy.is_file():
        shutil.copy2(legacy, target)
    return target


def migrate_user_dir(*parts):
    target = user_data_path(*parts)
    legacy = legacy_data_path(*parts)
    if not target.exists() and legacy.exists() and legacy.is_dir():
        shutil.copytree(legacy, target)
    target.mkdir(parents=True, exist_ok=True)
    return target


def startup_error_path():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR / "启动错误.log"
