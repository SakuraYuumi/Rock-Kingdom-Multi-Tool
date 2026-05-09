import sys
import traceback
from pathlib import Path


PROJECT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

try:
    from app.app_paths import startup_error_path
except Exception:
    RUNTIME_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_DIR

    def startup_error_path():
        return RUNTIME_DIR / "启动错误.log"


def show_startup_error(error_path, error_text):
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication([])
        lines = error_text.strip().splitlines()
        summary = "\n".join(lines[-8:])
        QMessageBox.critical(
            None,
            "洛克王国多功能辅助工具启动失败",
            f"洛克王国多功能辅助工具启动失败，错误已写入：\n{error_path}\n\n错误摘要：\n{summary}",
        )
    except Exception:
        pass


if __name__ == "__main__":
    try:
        from app.roco_resource_map_qt import main

        sys.exit(main())
    except Exception:
        error_path = startup_error_path()
        error_text = traceback.format_exc()
        error_path.write_text(error_text, encoding="utf-8")
        show_startup_error(error_path, error_text)
