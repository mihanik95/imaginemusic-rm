import os, json, re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QCursor

from add_composer_dialog import AddComposerDialog
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
from util_path import rsrc

DATABASES_FOLDER     = "_DATABASES"
COMPOSER_DB_FILENAME = "composer_database.json"
SESSION_FILE         = "session.json"

# ────────────────────────── вспомогательная логика ──────────────────────────
def smart_lookup(name: str, db: dict[str, dict]) -> str | None:
    """1) точное совпадение; 2) First + Last (Middle — опц.)."""
    norm = " ".join(name.split()).strip()
    if norm in db:
        return norm

    parts = norm.split()
    if len(parts) < 2:
        return None
    first, last = parts[0].lower(), parts[-1].lower()

    for key in db:
        p = key.split()
        if len(p) >= 2 and p[0].lower() == first and p[-1].lower() == last:
            return key
    return None


# ─────────────────────────────── ШАГ 3: КОМПОЗИТОРЫ ─────────────────────────
class Step3ComposerMatch(QWidget):
    """Сопоставляем композиторов треков с базой composer_database.json"""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.session_data: dict | None = None
        self.setLayout(self._ui())

    # ─── UI ───
    def _ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ШАГ 3: КОМПОЗИТОРЫ", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        root.addWidget(title)

        # ── список треков ──
        self.track_list = QListWidget()
        root.addWidget(self.track_list)

        # ── основная кнопка ──
        self.run_btn = QPushButton("✅ Сопоставить композиторов", clicked=self.match_composers)
        self.run_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        root.addWidget(self.run_btn)

        # ── описание ──
        desc = QLabel(
            "Описание шага: программа сопоставляет авторов треков с базой композиторов, "
            "чтобы позже автоматически подтянуть точные данные в метаданные.\n\n"
            "Нажмите «Сопоставить композиторов». Если кто‑то не найден, выберите его в базе "
            "или добавьте нового автора. Важно соблюдать точное написание — так имя будет "
            "использоваться во всех будущих релизах.",
            wordWrap=True
        )
        desc.setStyleSheet("margin-top:8px;")
        root.addWidget(desc)

        # ── навигация ──
        nav = QHBoxLayout()
        self.next_btn = QPushButton("➡ Следующий шаг", enabled=False,
                                    clicked=self.go_to_next_step)
        self.back_btn = QPushButton("⬅ Назад", clicked=self.go_back)
        nav.addWidget(self.next_btn)
        nav.addWidget(self.back_btn)
        root.addLayout(nav)

        # заполнить список треков
        self._load_session()

        return root

    # ───────────────────────── session.json / список треков ──────────────────
    def _load_session(self):
        if not os.path.exists(SESSION_FILE):
            return
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            self.session_data = json.load(f)

        self.track_list.clear()
        for t in self.session_data.get("tracks", []):
            tn  = t.get("track_number", "??")
            ttl = t.get("track_name", "Unknown")
            cps = ", ".join(t.get("composers", []))
            self.track_list.addItem(f"{tn} {ttl} | {cps}")

    # ───────────────────────────── основная логика ───────────────────────────
    def match_composers(self):
        db_path = os.path.join(DATABASES_FOLDER, COMPOSER_DB_FILENAME)
        if not os.path.exists(db_path):
            QMessageBox.warning(self, "Ошибка", "Не найдена composer_database.json.")
            return

        with open(db_path, "r", encoding="utf-8") as f:
            composers_db = json.load(f).get("composers", {})

        tracks = self.session_data.get("tracks", [])
        for tr in tracks:
            matched = []
            for name in tr.get("composers", []):
                key = smart_lookup(name, composers_db)
                if key:
                    matched.append(key)
                else:
                    matched.append(self._resolve_unknown(name, composers_db))
            tr["matched_composers"] = matched

        # сохраняем результат
        self.session_data["tracks"] = tracks
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(self.session_data, f, indent=4)

        # --- НОВОЕ: сообщение в «лог» вместо всплывающего окна ---
        self.track_list.addItem("✅ Композиторы успешно сопоставлены!")

        # активируем «Следующий шаг» + звук
        self.next_btn.setEnabled(True)
        self.next_btn.setStyleSheet(
            "background-color:#388E3C; color:white; font-weight:bold;")

        self.next_step_sound = QSoundEffect()
        self.next_step_sound.setSource(QUrl.fromLocalFile(rsrc("notify.wav")))
        self.next_step_sound.setVolume(0.5)
        self.next_step_sound.play()

    # ─────────────── «композитор не найден»  →  выбрать / добавить ────────────
    def _resolve_unknown(self, comp_name, db) -> str:
        msg = QMessageBox(self)
        msg.setWindowTitle("Композитор не найден")
        msg.setText(f"«{comp_name}» не найден в базе.\nЧто сделать?")
        choose = msg.addButton("Выбрать из базы",  QMessageBox.ButtonRole.YesRole)
        add    = msg.addButton("Добавить нового",  QMessageBox.ButtonRole.NoRole)
        msg.addButton("Отмена",                    QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() == choose:
            return self._choose_existing(db) or ""
        if msg.clickedButton() == add:
            return self._add_new_flow(comp_name, db) or ""
        return ""

    def _choose_existing(self, db) -> str:
        items = sorted(db.keys())
        if not items:
            QMessageBox.warning(self, "Ошибка", "База композиторов пуста."); return ""
        text, ok = QInputDialog.getItem(self, "Выберите композитора", "", items, 0, False)
        return text if ok else ""

    def _add_new_flow(self, default_name, db) -> str:
        dlg = AddComposerDialog(self)
        dlg.first_name_edit.setText(default_name)
        if dlg.exec():
            parts = [dlg.first_name_edit.text().strip(),
                     dlg.middle_name_edit.text().strip(),
                     dlg.last_name_edit.text().strip()]
            full = " ".join(p for p in parts if p)
            self._reload_db(db)
            return full
        return ""

    def _reload_db(self, db):
        path = os.path.join(DATABASES_FOLDER, COMPOSER_DB_FILENAME)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                db.clear(); db.update(json.load(f).get("composers", {}))

    # ─────────────────────────────── навигация ───────────────────────────────
    def go_to_next_step(self):
        from step4_add_cover import Step4AddCover
        w = Step4AddCover(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)

    def go_back(self):
        self.main_app.stack.setCurrentWidget(self.main_app.main_menu)
