import sys
import os
import json
import time
import zipfile
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame,
                             QFileDialog, QLineEdit, QFormLayout, QMessageBox,
                             QProgressBar, QDialog, QCheckBox,
                             QComboBox, QGraphicsView, QGraphicsScene,
                             QGraphicsPixmapItem, QGraphicsRectItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QRectF, QPointF, QTimer
from PyQt6.QtGui import (QPixmap, QPainter, QPen, QColor, QBrush, 
                         QIcon, QFont, QImage, QPainterPath)

PACK_EXTENSION = ".dvp"
COVER_WIDTH = 240
COVER_HEIGHT = 175
COVER_RATIO = COVER_WIDTH / COVER_HEIGHT
CONFIG_PATH = "packer_config.json"
LOCALIZATION_DIR = "localization"
APP_ICON = "app.ico"

DEFAULT_CONFIG = {"last_source_dir": "", "last_cover_dir": "", "language": "en"}


EN_DEFAULT = {
    "_name": "English",
    "_code": "en",

    "app.title": "Devers Packer",
    "app.subtitle": "Pack games into .dvp format",
    "app.byline": "Made by One Studio",

    "section.info": "GAME INFORMATION",
    "section.cover": "COVER",

    "field.source": "Game folder:",
    "field.source_placeholder": "Game folder...",
    "field.name": "Name:",
    "field.name_placeholder": "Game name",
    "field.exe": "Executable:",
    "field.exe_placeholder": "Game.exe",

    "cover.none": "NO COVER\n240 × 175",
    "cover.format_hint": "Format: 240×175 px (PNG)\nPick a larger image — it will be cropped automatically.",
    "cover.status_none": "No cover selected",
    "cover.status_ready": "Cover ready ({w}×{h})",
    "cover.pick": "Pick cover",
    "cover.clear": "Clear",

    "cover.crop_title": "Crop cover",
    "cover.crop_reset": "Reset",
    "cover.crop_hint": "Drag edges to crop. Wheel to zoom. Esc — cancel, Enter — apply.",
    "cover.crop_apply": "Apply",
    "cover.crop_cancel": "Cancel",
    "cover.crop_keep_ratio": "Keep 240:175 ratio",
    "cover.crop_result": "Result: {w}×{h} px",

    "progress.ready": "Ready to pack",
    "progress.packing": "Packing: {done}/{total}",
    "progress.scanning": "Scanning files...",
    "progress.done": "Done: {name} ({size})",
    "progress.error": "Error",

    "pack.button": "PACK INTO .DVP",
    "pack.button_busy": "PACKING...",

    "hint.source_size": "Source size: {size}  •  Output: output/{name}",

    "dialog.done_title": "Done",
    "dialog.done_message": "File created successfully!\n\n{name}\nSize: {size}",
    "dialog.open_folder": "Open folder",
    "dialog.ok": "OK",

    "dialog.error_title": "Error",
    "dialog.overwrite_title": "Overwrite",
    "dialog.overwrite_msg": "File '{name}' already exists.\nOverwrite?",

    "dialog.missing_exe_title": "File not found",
    "dialog.missing_exe_msg": "File '{exe}' not found in game folder.\nContinue packing?",

    "dialog.missing_fields_title": "Error",
    "dialog.missing_fields_msg": "Fill in all required fields!",

    "settings.language": "Language:",
    "crop.title": "Crop cover",
}


def ensure_default_localization():
    os.makedirs(LOCALIZATION_DIR, exist_ok=True)
    en_path = os.path.join(LOCALIZATION_DIR, "en.json")
    if not os.path.exists(en_path):
        try:
            with open(en_path, "w", encoding="utf-8") as f:
                json.dump(EN_DEFAULT, f, indent=4, ensure_ascii=False)
        except Exception:
            pass


class LocalizationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.current_lang = "en"
        self.strings = {}
        self.fallback = {}
        self.available = {}
        self.load_available()

    def load_available(self):
        self.available = {}
        if not os.path.exists(LOCALIZATION_DIR):
            return
        for f in os.listdir(LOCALIZATION_DIR):
            if not f.endswith(".json"):
                continue
            code = f[:-5]
            try:
                with open(os.path.join(LOCALIZATION_DIR, f), "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                self.available[code] = data.get("_name", code.upper())
            except Exception:
                pass
        if "en" not in self.available:
            self.available["en"] = "English"

    def set_language(self, code):
        if code not in self.available:
            code = "en"
        self.current_lang = code

        en_path = os.path.join(LOCALIZATION_DIR, "en.json")
        try:
            with open(en_path, "r", encoding="utf-8") as f:
                self.fallback = json.load(f)
        except Exception:
            self.fallback = EN_DEFAULT.copy()

        if code == "en":
            self.strings = self.fallback
        else:
            path = os.path.join(LOCALIZATION_DIR, f"{code}.json")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.strings = json.load(f)
            except Exception:
                self.strings = {}

    def t(self, key, **kwargs):
        value = self.strings.get(key)
        if value is None:
            value = self.fallback.get(key, key)
        if kwargs:
            try:
                value = value.format(**kwargs)
            except Exception:
                pass
        return value


L = LocalizationManager()


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def build_app_icon():
    if os.path.exists(APP_ICON):
        icon = QIcon(APP_ICON)
        if not icon.isNull():
            return icon
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Segoe UI Symbol", int(size * 0.72), QFont.Weight.Bold))
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "✦")
        p.end()
        icon.addPixmap(pm)
    return icon


class CoverCropDialog(QDialog):
    HANDLE_SIZE = 12

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(L.t("cover.crop_title"))
        self.setWindowIcon(QApplication.windowIcon())
        self.setFixedSize(900, 720)
        self.setStyleSheet("""
            QDialog { background-color: #0A0A0A; }
            QLabel { color: #CCCCCC; font-size: 12px; }
            QLabel#Hint { color: #666666; font-size: 11px; }
            QLabel#Title { color: #FFFFFF; font-size: 20px; font-weight: 900; letter-spacing: -1px; }
            QPushButton { background-color: #FFFFFF; color: #000000; padding: 10px 22px; border-radius: 8px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #E0E0E0; }
            QPushButton#Secondary { background-color: #1A1A1A; color: #FFFFFF; border: 1px solid #333333; }
            QPushButton#Secondary:hover { background-color: #2A2A2A; }
            QCheckBox { color: #CCCCCC; font-size: 12px; spacing: 8px; }
            QCheckBox::indicator { width: 16px; height: 16px; background-color: #1A1A1A; border: 1px solid #333333; border-radius: 4px; }
            QCheckBox::indicator:checked { background-color: #FFFFFF; border: 1px solid #FFFFFF; }
        """)

        self.original_pixmap = QPixmap(image_path)
        if self.original_pixmap.isNull():
            QMessageBox.critical(parent, L.t("dialog.error_title"), "Cannot load image")
            self.reject()
            return

        self.image_path = image_path
        self.crop_rect = QRectF()
        self.active_handle = None
        self.drag_start_pos = QPointF()
        self.drag_start_rect = QRectF()
        self.keep_ratio = True
        self.result_path = None

        self._build_ui()
        self._init_crop_rect()
        self._update_scene()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        top = QHBoxLayout()
        title = QLabel(L.t("cover.crop_title"))
        title.setObjectName("Title")
        top.addWidget(title)
        top.addStretch()
        self.size_label = QLabel("")
        self.size_label.setStyleSheet("color: #888888; font-size: 12px;")
        top.addWidget(self.size_label)
        layout.addLayout(top)

        self.view = QGraphicsView()
        self.view.setStyleSheet("""
            QGraphicsView { background-color: #050505; border: 1px solid #1A1A1A; border-radius: 10px; }
        """)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.mousePressEvent = self._mouse_press
        self.view.mouseMoveEvent = self._mouse_move
        self.view.mouseReleaseEvent = self._mouse_release
        self.view.wheelEvent = self._wheel

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        layout.addWidget(self.view, stretch=1)

        controls = QHBoxLayout()
        self.ratio_check = QCheckBox(L.t("cover.crop_keep_ratio"))
        self.ratio_check.setChecked(True)
        self.ratio_check.stateChanged.connect(self._on_ratio_toggle)
        controls.addWidget(self.ratio_check)
        controls.addStretch()
        reset_btn = QPushButton(L.t("cover.crop_reset"))
        reset_btn.setObjectName("Secondary")
        reset_btn.clicked.connect(self._reset_crop)
        controls.addWidget(reset_btn)
        layout.addLayout(controls)

        hint = QLabel(L.t("cover.crop_hint"))
        hint.setObjectName("Hint")
        layout.addWidget(hint)

        btns = QHBoxLayout()
        cancel = QPushButton(L.t("cover.crop_cancel"))
        cancel.setObjectName("Secondary")
        cancel.clicked.connect(self.reject)
        apply_btn = QPushButton(L.t("cover.crop_apply"))
        apply_btn.clicked.connect(self._apply)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(apply_btn)
        layout.addLayout(btns)

    def _init_crop_rect(self):
        iw = self.original_pixmap.width()
        ih = self.original_pixmap.height()
        if iw / ih > COVER_RATIO:
            h = ih
            w = h * COVER_RATIO
        else:
            w = iw
            h = w / COVER_RATIO
        x = (iw - w) / 2
        y = (ih - h) / 2
        self.crop_rect = QRectF(x, y, w, h)

    def _reset_crop(self):
        self._init_crop_rect()
        self._update_scene()

    def _on_ratio_toggle(self, state):
        self.keep_ratio = self.ratio_check.isChecked()
        if self.keep_ratio:
            self._enforce_ratio()

    def _enforce_ratio(self):
        r = self.crop_rect
        iw = self.original_pixmap.width()
        ih = self.original_pixmap.height()
        cx = r.center().x(); cy = r.center().y()
        w = r.width(); h = w / COVER_RATIO
        if h > ih:
            h = ih; w = h * COVER_RATIO
        if w > iw:
            w = iw; h = w / COVER_RATIO
        x = max(0, min(cx - w / 2, iw - w))
        y = max(0, min(cy - h / 2, ih - h))
        self.crop_rect = QRectF(x, y, w, h)

    def _update_scene(self):
        self.scene.clear()
        self.scene.setSceneRect(0, 0, self.original_pixmap.width(), self.original_pixmap.height())
        self.scene.addItem(QGraphicsPixmapItem(self.original_pixmap))

        dark = QBrush(QColor(0, 0, 0, 160))
        iw = self.original_pixmap.width(); ih = self.original_pixmap.height()
        r = self.crop_rect

        for rect in (
            QRectF(0, 0, iw, r.top()),
            QRectF(0, r.bottom(), iw, ih - r.bottom()),
            QRectF(0, r.top(), r.left(), r.height()),
            QRectF(r.right(), r.top(), iw - r.right(), r.height()),
        ):
            item = QGraphicsRectItem(rect)
            item.setBrush(dark); item.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(item)

        border = QGraphicsRectItem(r)
        pen = QPen(QColor(255, 255, 255)); pen.setWidth(2)
        border.setPen(pen); border.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.scene.addItem(border)

        self._handles = []
        hs = self.HANDLE_SIZE
        for cx, cy in [(r.left(), r.top()), (r.right(), r.top()),
                       (r.left(), r.bottom()), (r.right(), r.bottom()),
                       (r.center().x(), r.top()), (r.center().x(), r.bottom()),
                       (r.left(), r.center().y()), (r.right(), r.center().y())]:
            h = QGraphicsRectItem(QRectF(cx - hs/2, cy - hs/2, hs, hs))
            h.setPen(QPen(QColor(0, 0, 0))); h.setBrush(QBrush(QColor(255, 255, 255)))
            self.scene.addItem(h); self._handles.append(h)

        self.size_label.setText(L.t("cover.crop_result", w=COVER_WIDTH, h=COVER_HEIGHT))
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _get_handle_at(self, pos):
        if not hasattr(self, "_handles"): return -1
        for i, h in enumerate(self._handles):
            if h.rect().adjusted(-3, -3, 3, 3).contains(pos):
                return i
        return -1

    def _mouse_press(self, event):
        if event.button() != Qt.MouseButton.LeftButton: return
        pos = self.view.mapToScene(event.pos())
        idx = self._get_handle_at(pos)
        r = self.crop_rect
        if idx >= 0:
            self.active_handle = idx
            self.drag_start_pos = pos
            self.drag_start_rect = QRectF(r)
        elif r.contains(pos):
            self.active_handle = -2
            self.drag_start_pos = pos
            self.drag_start_rect = QRectF(r)

    def _mouse_move(self, event):
        pos = self.view.mapToScene(event.pos())
        if self.active_handle is None:
            if self._get_handle_at(pos) >= 0:
                self.view.setCursor(Qt.CursorShape.SizeAllCursor)
            elif self.crop_rect.contains(pos):
                self.view.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.view.setCursor(Qt.CursorShape.CrossCursor)
            return

        delta = pos - self.drag_start_pos
        r = QRectF(self.drag_start_rect)
        iw = self.original_pixmap.width(); ih = self.original_pixmap.height()

        if self.active_handle == -2:
            nx = max(0, min(r.x() + delta.x(), iw - r.width()))
            ny = max(0, min(r.y() + delta.y(), ih - r.height()))
            self.crop_rect = QRectF(nx, ny, r.width(), r.height())
        else:
            l, t, rr, b = r.left(), r.top(), r.right(), r.bottom()
            ah = self.active_handle
            if ah == 0: l = max(0, min(r.left() + delta.x(), rr - 20)); t = max(0, min(r.top() + delta.y(), b - 20))
            elif ah == 1: rr = min(iw, max(r.right() + delta.x(), l + 20)); t = max(0, min(r.top() + delta.y(), b - 20))
            elif ah == 2: l = max(0, min(r.left() + delta.x(), rr - 20)); b = min(ih, max(r.bottom() + delta.y(), t + 20))
            elif ah == 3: rr = min(iw, max(r.right() + delta.x(), l + 20)); b = min(ih, max(r.bottom() + delta.y(), t + 20))
            elif ah == 4: t = max(0, min(r.top() + delta.y(), b - 20))
            elif ah == 5: b = min(ih, max(r.bottom() + delta.y(), t + 20))
            elif ah == 6: l = max(0, min(r.left() + delta.x(), rr - 20))
            elif ah == 7: rr = min(iw, max(r.right() + delta.x(), l + 20))
            new_r = QRectF(l, t, rr - l, b - t)

            if self.keep_ratio:
                w = new_r.width(); h = new_r.height()
                if ah in (4, 5): w = h * COVER_RATIO
                elif ah in (6, 7): h = w / COVER_RATIO
                else: h = w / COVER_RATIO
                cx = new_r.center().x(); cy = new_r.center().y()
                w = min(w, iw); h = min(h, ih)
                if w / h > COVER_RATIO: w = h * COVER_RATIO
                else: h = w / COVER_RATIO
                x = max(0, min(cx - w/2, iw - w))
                y = max(0, min(cy - h/2, ih - h))
                new_r = QRectF(x, y, w, h)

            self.crop_rect = new_r
        self._update_scene()

    def _mouse_release(self, event):
        self.active_handle = None

    def _wheel(self, event):
        if event.angleDelta().y() > 0: self.view.scale(1.15, 1.15)
        else: self.view.scale(1/1.15, 1/1.15)

    def _apply(self):
        r = self.crop_rect
        if r.width() < 10 or r.height() < 10:
            QMessageBox.warning(self, L.t("dialog.error_title"), "Area is too small")
            return
        cropped = self.original_pixmap.copy(int(r.x()), int(r.y()), int(r.width()), int(r.height()))
        final = cropped.scaled(COVER_WIDTH, COVER_HEIGHT,
                               Qt.AspectRatioMode.IgnoreAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        tmp_path = os.path.join(os.path.expanduser("~"), ".devers_cover_temp.png")
        try:
            final.save(tmp_path, "PNG")
        except Exception as e:
            QMessageBox.critical(self, L.t("dialog.error_title"), str(e))
            return
        self.result_path = tmp_path
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape: self.reject()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter): self._apply()
        else: super().keyPressEvent(event)


class PackWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_pack = pyqtSignal(str, bool, str)

    def __init__(self, source_dir, output_path, game_name, game_exe, cover_path):
        super().__init__()
        self.source_dir = source_dir
        self.output_path = output_path
        self.game_name = game_name
        self.game_exe = game_exe
        self.cover_path = cover_path

    def run(self):
        try:
            self.status.emit(L.t("progress.scanning"))
            all_files = []
            for root, dirs, files in os.walk(self.source_dir):
                for file in files:
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, self.source_dir)
                    all_files.append((full, rel))

            total_size = sum(os.path.getsize(f[0]) for f in all_files)
            total_files = len(all_files)

            manifest = {
                "name": self.game_name,
                "exe": self.game_exe,
                "version": "1.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "files_count": total_files,
                "total_size": total_size
            }

            if self.cover_path and os.path.exists(self.cover_path):
                with open(self.cover_path, "rb") as cf:
                    manifest["cover_data"] = cf.read().hex()
                manifest["cover_ext"] = ".png"

            with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                zf.writestr("manifest.json", json.dumps(manifest, indent=2))
                processed = 0
                for full, rel in all_files:
                    zf.write(full, rel)
                    processed += 1
                    if processed % max(1, total_files // 100) == 0:
                        self.progress.emit(int((processed / total_files) * 100))
                        self.status.emit(L.t("progress.packing", done=processed, total=total_files))

            self.progress.emit(100)
            self.finished_pack.emit(self.output_path, True, "")
        except Exception as e:
            self.finished_pack.emit("", False, str(e))


class PackerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(L.t("app.title"))
        self.setWindowIcon(QApplication.windowIcon())
        self.setFixedSize(720, 950)

        self.source_dir = ""
        self.cover_path = ""
        self.pack_worker = None
        self.config = load_config()

        self.apply_styles()
        self.init_ui()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #000000; }
            QLabel#Title { color: #FFFFFF; font-size: 32px; font-weight: 900; letter-spacing: -1px; }
            QLabel#Sub { color: #666666; font-size: 13px; }
            QLabel { color: #CCCCCC; font-size: 13px; }
            QLabel#SectionTitle { color: #FFFFFF; font-size: 12px; font-weight: bold; letter-spacing: 1px; }
            QLabel#Hint { color: #555555; font-size: 11px; }
            QLabel#Byline { color: #444444; font-size: 11px; letter-spacing: 1px; }
            QLineEdit { background-color: #1A1A1A; color: #FFFFFF; border: 1px solid #333333; border-radius: 8px; padding: 12px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #FFFFFF; }
            QComboBox { background-color: #1A1A1A; color: #FFFFFF; border: 1px solid #333333; border-radius: 8px; padding: 12px; font-size: 13px; }
            QComboBox::drop-down { border: none; }
            QComboBox#LangCombo { background-color: #0F0F0F; border: 1px solid #1A1A1A; border-radius: 8px; padding: 6px 12px; font-size: 12px; color: #CCCCCC; }
            QComboBox#LangCombo:hover { border: 1px solid #333333; }
            QComboBox#LangCombo::drop-down { border: none; width: 20px; }
            QPushButton#Primary { background-color: #FFFFFF; color: #000000; border-radius: 12px; font-weight: 900; font-size: 16px; letter-spacing: 1px; }
            QPushButton#Primary:hover { background-color: #E0E0E0; }
            QPushButton#Primary:disabled { background-color: #333333; color: #666666; }
            QPushButton#Secondary { background-color: #1A1A1A; color: #FFFFFF; padding: 10px; border-radius: 8px; font-weight: bold; font-size: 13px; border: 1px solid #333333; }
            QPushButton#Secondary:hover { background-color: #333333; }
            QProgressBar { background-color: #1A1A1A; border: 1px solid #333333; border-radius: 8px; text-align: center; color: #FFFFFF; height: 22px; font-size: 11px; }
            QProgressBar::chunk { background-color: #FFFFFF; border-radius: 7px; }
            QFrame#CoverBox { background-color: #0D0D0D; border: 1px solid #1A1A1A; border-radius: 10px; }
        """)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(50, 35, 50, 35)
        layout.setSpacing(15)

        header = QHBoxLayout()
        title = QLabel(L.t("app.title"))
        title.setObjectName("Title")
        header.addWidget(title)
        header.addStretch()

        self.lang_combo = QComboBox()
        self.lang_combo.setObjectName("LangCombo")
        self.lang_combo.setFixedWidth(150)
        items = sorted(L.available.items(), key=lambda x: (x[0] != "en", x[1].lower()))
        for code, name in items:
            self.lang_combo.addItem(name, code)
        cur = self.config.get("language", "en")
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == cur:
                self.lang_combo.setCurrentIndex(i)
                break
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        header.addWidget(self.lang_combo)
        layout.addLayout(header)

        sub = QLabel(L.t("app.subtitle"))
        sub.setObjectName("Sub")
        layout.addWidget(sub)

        layout.addSpacing(20)

        sec1 = QLabel(L.t("section.info"))
        sec1.setObjectName("SectionTitle")
        layout.addWidget(sec1)

        form = QFormLayout()
        form.setSpacing(12)

        src_row = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setReadOnly(True)
        self.source_input.setPlaceholderText(L.t("field.source_placeholder"))
        src_btn = QPushButton("...")
        src_btn.setObjectName("Secondary")
        src_btn.setFixedWidth(50)
        src_btn.clicked.connect(self.browse_source)
        src_row.addWidget(self.source_input)
        src_row.addWidget(src_btn)
        form.addRow(L.t("field.source"), src_row)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(L.t("field.name_placeholder"))
        self.name_input.textChanged.connect(self._update_output_hint)
        form.addRow(L.t("field.name"), self.name_input)

        self.exe_combo = QComboBox()
        self.exe_combo.setEditable(True)
        self.exe_combo.lineEdit().setPlaceholderText(L.t("field.exe_placeholder"))
        form.addRow(L.t("field.exe"), self.exe_combo)

        layout.addLayout(form)
        layout.addSpacing(10)

        sec2 = QLabel(L.t("section.cover"))
        sec2.setObjectName("SectionTitle")
        layout.addWidget(sec2)

        cover_box = QFrame()
        cover_box.setObjectName("CoverBox")
        cb = QHBoxLayout(cover_box)
        cb.setContentsMargins(20, 20, 20, 20)
        cb.setSpacing(20)

        self.cover_preview = QLabel()
        self.cover_preview.setFixedSize(COVER_WIDTH, COVER_HEIGHT)
        self.cover_preview.setStyleSheet("""
            background-color: #141414; border: 1px dashed #333333;
            border-radius: 8px; color: #444444; font-size: 11px;
        """)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setText(L.t("cover.none"))
        cb.addWidget(self.cover_preview)

        cr = QVBoxLayout()
        cr.setSpacing(10)
        self.cover_status = QLabel(L.t("cover.status_none"))
        self.cover_status.setStyleSheet("color: #888888; font-size: 12px;")
        cr.addWidget(self.cover_status)

        cover_hint = QLabel(L.t("cover.format_hint"))
        cover_hint.setObjectName("Hint")
        cover_hint.setWordWrap(True)
        cr.addWidget(cover_hint)
        cr.addStretch()

        row = QHBoxLayout()
        pick = QPushButton(L.t("cover.pick")); pick.setObjectName("Secondary")
        pick.clicked.connect(self.browse_cover)
        clr = QPushButton(L.t("cover.clear")); clr.setObjectName("Secondary")
        clr.setFixedWidth(90); clr.clicked.connect(self.clear_cover)
        row.addWidget(pick); row.addWidget(clr); row.addStretch()
        cr.addLayout(row)
        cb.addLayout(cr, stretch=1)

        layout.addWidget(cover_box)
        layout.addSpacing(10)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.status = QLabel(L.t("progress.ready"))
        self.status.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.status)

        self.output_hint = QLabel("")
        self.output_hint.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(self.output_hint)

        layout.addStretch()

        self.pack_btn = QPushButton(L.t("pack.button"))
        self.pack_btn.setObjectName("Primary")
        self.pack_btn.setFixedHeight(65)
        self.pack_btn.clicked.connect(self.start_packing)
        layout.addWidget(self.pack_btn)

        byline = QLabel(L.t("app.byline"))
        byline.setObjectName("Byline")
        byline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(byline)

    def _on_language_changed(self, idx):
        code = self.lang_combo.itemData(idx)
        if not code or code == L.current_lang:
            return
        self.config["language"] = code
        save_config(self.config)
        QTimer.singleShot(50, self._restart_with_new_language)

    def _restart_with_new_language(self):
        L.set_language(self.config.get("language", "en"))
        global _new_window
        _new_window = PackerWindow()
        _new_window.show()
        QTimer.singleShot(50, self._close_old)

    def _close_old(self):
        try:
            self.hide()
            self.deleteLater()
        except Exception:
            pass

    def browse_source(self):
        d = QFileDialog.getExistingDirectory(self, L.t("field.source"),
                                             self.config.get("last_source_dir", ""))
        if d:
            self.source_dir = d
            self.source_input.setText(d)
            self.config["last_source_dir"] = d
            save_config(self.config)
            if not self.name_input.text():
                self.name_input.setText(os.path.basename(d))
            self.exe_combo.clear()
            exes = [f for f in os.listdir(d) if f.lower().endswith(".exe")]
            if len(exes) == 1:
                self.exe_combo.setCurrentText(exes[0])
            elif len(exes) > 1:
                self.exe_combo.addItems(exes)
                self.exe_combo.setCurrentIndex(0)
            self._update_output_hint()

    def browse_cover(self):
        f, _ = QFileDialog.getOpenFileName(self, L.t("cover.pick"),
                                           self.config.get("last_cover_dir", ""),
                                           "Images (*.png *.jpg *.jpeg *.bmp)")
        if not f:
            return
        self.config["last_cover_dir"] = os.path.dirname(f)
        save_config(self.config)
        d = CoverCropDialog(f, self)
        if d.exec() == QDialog.DialogCode.Accepted and d.result_path:
            self.cover_path = d.result_path
            pm = QPixmap(self.cover_path)
            if not pm.isNull():
                self.cover_preview.setPixmap(pm)
                self.cover_preview.setText("")
                self.cover_preview.setStyleSheet("""
                    background-color: transparent;
                    border: 1px solid #222222; border-radius: 8px;
                """)
                self.cover_status.setText(L.t("cover.status_ready", w=pm.width(), h=pm.height()))
                self.cover_status.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")

    def clear_cover(self):
        self.cover_path = ""
        self.cover_preview.setPixmap(QPixmap())
        self.cover_preview.setText(L.t("cover.none"))
        self.cover_preview.setStyleSheet("""
            background-color: #141414; border: 1px dashed #333333;
            border-radius: 8px; color: #444444; font-size: 11px;
        """)
        self.cover_status.setText(L.t("cover.status_none"))
        self.cover_status.setStyleSheet("color: #888888; font-size: 12px;")

    def _update_output_hint(self):
        if not self.source_dir or not self.name_input.text():
            self.output_hint.setText("")
            return
        try:
            total = 0
            for root, _, files in os.walk(self.source_dir):
                for f in files:
                    total += os.path.getsize(os.path.join(root, f))
            safe = "".join(c for c in self.name_input.text() if c.isalnum() or c in "._- ")
            size_str = f"{total / (1024*1024):.1f} MB"
            self.output_hint.setText(L.t("hint.source_size",
                                         size=size_str,
                                         name=safe + PACK_EXTENSION))
        except Exception:
            self.output_hint.setText("")

    def start_packing(self):
        if not self.source_dir:
            QMessageBox.warning(self, L.t("dialog.missing_fields_title"), L.t("field.source"))
            return
        if not self.name_input.text().strip():
            QMessageBox.warning(self, L.t("dialog.missing_fields_title"), L.t("field.name"))
            return
        exe_name = self.exe_combo.currentText().strip()
        if not exe_name:
            QMessageBox.warning(self, L.t("dialog.missing_fields_title"), L.t("field.exe"))
            return

        exe_found = False
        for root, _, files in os.walk(self.source_dir):
            for f in files:
                if f.lower() == exe_name.lower():
                    exe_found = True; break
            if exe_found: break
        if not exe_found:
            r = QMessageBox.question(self, L.t("dialog.missing_exe_title"),
                                     L.t("dialog.missing_exe_msg", exe=exe_name))
            if r != QMessageBox.StandardButton.Yes:
                return

        os.makedirs("output", exist_ok=True)
        safe = "".join(c for c in self.name_input.text() if c.isalnum() or c in "._- ")
        out_path = os.path.join("output", safe + PACK_EXTENSION)

        if os.path.exists(out_path):
            r = QMessageBox.question(self, L.t("dialog.overwrite_title"),
                                     L.t("dialog.overwrite_msg", name=safe + PACK_EXTENSION))
            if r == QMessageBox.StandardButton.No:
                return

        self.pack_btn.setEnabled(False)
        self.pack_btn.setText(L.t("pack.button_busy"))
        self.progress.setValue(0)

        self.pack_worker = PackWorker(
            self.source_dir, out_path,
            self.name_input.text().strip(),
            exe_name, self.cover_path
        )
        self.pack_worker.progress.connect(self.progress.setValue)
        self.pack_worker.status.connect(self.status.setText)
        self.pack_worker.finished_pack.connect(self.on_done)
        self.pack_worker.start()

    def on_done(self, path, ok, err):
        self.pack_btn.setEnabled(True)
        self.pack_btn.setText(L.t("pack.button"))

        if ok:
            mb = os.path.getsize(path) / (1024 * 1024)
            self.status.setText(L.t("progress.done",
                                    name=os.path.basename(path),
                                    size=f"{mb:.2f} MB"))
            self.progress.setValue(100)

            msg = QMessageBox(self)
            msg.setWindowTitle(L.t("dialog.done_title"))
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(L.t("dialog.done_message",
                            name=os.path.basename(path),
                            size=f"{mb:.2f} MB"))
            open_btn = msg.addButton(L.t("dialog.open_folder"), QMessageBox.ButtonRole.ActionRole)
            msg.addButton(L.t("dialog.ok"), QMessageBox.ButtonRole.AcceptRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                folder = os.path.abspath(os.path.dirname(path))
                if os.name == 'nt': os.startfile(folder)
                elif sys.platform == 'darwin': subprocess.Popen(['open', folder])
                else: subprocess.Popen(['xdg-open', folder])
        else:
            self.status.setText(L.t("progress.error"))
            QMessageBox.critical(self, L.t("dialog.error_title"), err)


_new_window = None


if __name__ == "__main__":
    ensure_default_localization()
    app = QApplication(sys.argv)
    app.setWindowIcon(build_app_icon())

    cfg = load_config()
    L.load_available()
    L.set_language(cfg.get("language", "en"))

    w = PackerWindow()
    w.show()
    sys.exit(app.exec())