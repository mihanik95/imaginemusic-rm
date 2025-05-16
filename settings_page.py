# settings_page.py
import os, json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui  import QCursor
from PyQt6.QtCore import Qt

from util_json import load_json_safe, dump_json_safe   # «безопасные» I/O-функции

# ------------------------------------------------------------
# paths / constants
# ------------------------------------------------------------
APP_ROOT    = os.path.dirname(__file__)          # каталог с main.py
CONFIG_FILE = os.path.join(APP_ROOT, "config.json")

DB_DIR            = "_DATABASES"
COMPOSER_DB_FILE  = "composer_database.json"
ISRC_DB_FILE      = "isrc_database.json"

try:
    import pandas as pd
except ImportError:
    pd = None                                    # покажем ошибку при попытке

# ------------------------------------------------------------
# helpers / styles
# ------------------------------------------------------------
BTN_STYLE = "QPushButton{padding:6px 12px;font-size:12pt;}"
BTN_GREEN = ("QPushButton{background:#388E3C;color:white;font-weight:bold;"
             "padding:6px 12px;font-size:12pt;}")

def v_spacer(h: int = 12) -> QSpacerItem:
    return QSpacerItem(0, h,
                       QSizePolicy.Policy.Minimum,
                       QSizePolicy.Policy.Fixed)

def section_title(text: str) -> QLabel:
    lbl = QLabel(text); lbl.setStyleSheet("font-size:16pt;font-weight:600;")
    return lbl

def hint(text: str) -> QLabel:
    lbl = QLabel(text); lbl.setWordWrap(True)
    return lbl

# --------- NaN-cleanup ----------------------------------------------------
def _clean(val) -> str:
    """
    Превращает None, float('nan') или строку 'nan' → пустую строку.
    Остальное возвращает как trimmed-строку.
    """
    if val is None:
        return ""
    if (pd is not None) and isinstance(val, float) and pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s
# -------------------------------------------------------------------------

# ------------------------------------------------------------
# main widget
# ------------------------------------------------------------
class SettingsPage(QWidget):
    """Экран «НАСТРОЙКИ» — дизайн в стиле остальных шагов приложения."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build_ui()
        self._load_config()                       # сама читает JSON

    # ---------------------------------------------------------------- UI
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("НАСТРОЙКИ", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        root.addWidget(title)

        # ── рабочие папки ──
        root.addWidget(section_title("📁 РАБОЧИЕ ПАПКИ"))
        root.addWidget(hint("Укажите, где приложение берёт исходники и куда "
                            "сохраняет готовые файлы."))

        self.folder_fields: dict[str, QLineEdit] = {}
        folders = {
            "_НЕГОТОВЫЕ":              "Путь до папки _НЕГОТОВЫЕ",
            "_ALL ALBUMS AIFF":        "Путь до папки _ALL ALBUMS AIFF",
            "_ALL ALBUMS MP3":         "Путь до папки _ALL ALBUMS MP3",
            "_ALL ALBUMS COVERS":      "Путь до папки _ALL ALBUMS COVERS",
            "_ALL ALBUMS METADATA":    "Путь до папки _ALL ALBUMS METADATA",
            "_ALL ALBUMS HARVEST":     "Путь до папки _ALL ALBUMS HARVEST"
        }

        for key, label_text in folders.items():
            root.addWidget(QLabel(label_text))
            row = QHBoxLayout(); row.setSpacing(4)
            le  = QLineEdit()
            btn = QPushButton("📁 Обзор",
                              clicked=lambda _, k=key: self._pick_dir(k))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(BTN_STYLE)
            row.addWidget(le); row.addWidget(btn)
            root.addLayout(row)

            self.folder_fields[key] = le

        root.addSpacerItem(v_spacer())

        # ── TOTAL-METADATA и базы ──
        root.addWidget(section_title("📊 TOTAL METADATA"))
        root.addWidget(hint("Excel-файл нужен, чтобы обновлять базы композиторов "
                            "и ISRC-кодов."))

        row = QHBoxLayout(); row.setSpacing(4)
        self.tm_edit = QLineEdit()
        tm_btn = QPushButton("📂 Выбрать файл", clicked=self._pick_excel)
        tm_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        tm_btn.setStyleSheet(BTN_STYLE)
        row.addWidget(self.tm_edit); row.addWidget(tm_btn)
        root.addLayout(row)

        self.comp_btn = QPushButton("📥 Подгрузить базу композиторов",
                                    clicked=self._update_composer_db)
        self.comp_btn.setStyleSheet(BTN_STYLE)
        self.comp_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        root.addWidget(self.comp_btn)

        self.isrc_btn = QPushButton("📥 Подгрузить базу ISRC",
                                    clicked=self._update_isrc_db)
        self.isrc_btn.setStyleSheet(BTN_STYLE)
        self.isrc_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        root.addWidget(self.isrc_btn)

        root.addSpacerItem(v_spacer(20))

        # ── нижние кнопки ──
        save_btn = QPushButton("💾 Сохранить настройки", clicked=self._save_config)
        save_btn.setStyleSheet(BTN_GREEN)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        root.addWidget(save_btn)

        back_btn = QPushButton("⬅ Назад",
                               clicked=lambda:
                               self.app.stack.setCurrentWidget(self.app.main_menu))
        back_btn.setStyleSheet(BTN_STYLE)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        root.addWidget(back_btn)

    # ------------------------------------------------------ file dialogs
    def _pick_dir(self, key):
        path = QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if path:
            self.folder_fields[key].setText(path)

    def _pick_excel(self):
        f, _ = QFileDialog.getOpenFileName(self, "Excel-файл", "",
                                           "Excel (*.xlsx *.xls)")
        if f:
            self.tm_edit.setText(f)

    # ------------------------------------------------------ config I/O
    def _save_config(self):
        cfg = {k: w.text().strip() for k, w in self.folder_fields.items()}
        cfg["TOTAL METADATA"] = self.tm_edit.text().strip()

        if not dump_json_safe(cfg, CONFIG_FILE):
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось сохранить конфигурацию — проверьте права на запись."
            )
            return

        self.app.stack.setCurrentWidget(self.app.main_menu)

    def _load_config(self):
        cfg = load_json_safe(CONFIG_FILE, {})
        for k, w in self.folder_fields.items():
            w.setText(cfg.get(k, ""))
        self.tm_edit.setText(cfg.get("TOTAL METADATA", ""))

    # ------------------------------------------------------ DB helpers
    def _check_prereq(self) -> bool:
        if pd is None:
            QMessageBox.critical(self, "Ошибка",
                                 "pandas не установлен.\n`pip install pandas openpyxl`")
            return False
        if not (p := self.tm_edit.text().strip()) or not os.path.exists(p):
            QMessageBox.warning(self, "Ошибка", "Excel-файл не указан.")
            return False
        return True

    def _confirm_over(self, path: str) -> bool:
        if os.path.exists(path):
            ok = QMessageBox.question(
                self, "Файл уже существует",
                f"{os.path.basename(path)} уже есть. Перезаписать?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            return ok == QMessageBox.StandardButton.Yes
        return True

    # ---------------- загрузка / обновление баз --------------------------
    def _update_composer_db(self):
        if not self._check_prereq():
            return
        db_path = os.path.join(DB_DIR, COMPOSER_DB_FILE)
        if not self._confirm_over(db_path):
            return
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            res = {"composers": {}, "publishers": {}}

            xls = pd.ExcelFile(self.tm_edit.text().strip())
            for sh in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sh, dtype=str)
                for _, r in df.iterrows():
                    self._add_composers(res, r)
                    self._add_publisher(res, r)

            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "Готово",
                                    f"База композиторов обновлена:\n{db_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось обновить базу:\n{e}")

    def _update_isrc_db(self):
        if not self._check_prereq():
            return
        db_path = os.path.join(DB_DIR, ISRC_DB_FILE)
        if not self._confirm_over(db_path):
            return
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            xls  = pd.ExcelFile(self.tm_edit.text().strip())
            isrc = {}
            for sh in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sh, dtype=str)
                for _, r in df.iterrows():
                    code = _clean(r.get("CODE: ISRC"))
                    if not code:
                        continue
                    isrc.setdefault(code, {
                        "album_code":  _clean(r.get("ALBUM: Code")),
                        "album_title": _clean(r.get("ALBUM: Title")),
                        "track_title": _clean(r.get("TRACK: Title"))
                    })

            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(dict(sorted(isrc.items())), f,
                          indent=4, ensure_ascii=False)

            QMessageBox.information(self, "Готово",
                                    f"База ISRC обновлена:\n{db_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось обновить базу:\n{e}")

    # ---------------- Excel-row parsers ----------------------------------
    def _add_composers(self, dst, row):
        for i in (1, 2, 3):
            fn = _clean(row.get(f"WRITER:{i}: First Name"))
            ln = _clean(row.get(f"WRITER:{i}: Last Name"))
            mn = _clean(row.get(f"WRITER:{i}: Middle Name"))
            if not (fn or ln):
                continue
            key = " ".join(p for p in (fn, mn, ln) if p)
            dst["composers"].setdefault(key, {
                "first_name": fn,
                "middle_name": mn,
                "last_name": ln,
                "society":       _clean(row.get(f"WRITER:{i}: Society")),
                "ipi":           _clean(row.get(f"WRITER:{i}: IPI")),
                "publisher_key": _clean(row.get(f"WRITER:{i}: Original Publisher"))
            })

    def _add_publisher(self, dst, row):
        name = _clean(row.get("PUBLISHER:1: Name"))
        if not name:
            return
        dst["publishers"].setdefault(name, {
            "publisher_name":    name,
            "publisher_society": _clean(row.get("PUBLISHER:1: Society")),
            "publisher_ipi":     _clean(row.get("PUBLISHER:1: IPI"))
        })
