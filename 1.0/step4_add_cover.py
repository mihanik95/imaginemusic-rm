# step4_add_cover.py
import os, json, shutil, re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

SESSION_FILE = "session.json"
CONFIG_FILE  = "config.json"


class Step4AddCover(QWidget):
    """ШАГ 4 — копируем обложку в альбом (_AIFF)."""

    # ────────────────────────── UI ──────────────────────────
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.setLayout(self._build_ui())

    def _build_ui(self):
        lo = QVBoxLayout()
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ШАГ 4: ОБЛОЖКА", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt; font-weight:600; margin-bottom:8px;")
        lo.addWidget(title)

        # ── лог ──
        self.log_out = QTextEdit(readOnly=True)
        lo.addWidget(self.log_out)

        # ── run‑кнопка ──
        self.run_btn = QPushButton("✅ Найти и добавить обложку", clicked=self.run_step4)
        self.run_btn.setMinimumHeight(32)          # такой же, как в шагах 2‑3
        lo.addWidget(self.run_btn)

        # ── описание ──
        desc = QLabel(
            "Описание шага: программа ищет изображение в папке _ALL ALBUMS COVERS, "
            "копирует его в альбом (_ALL ALBUMS AIFF) и переименовывает по стандарту.\n\n"
            "Ваша задача – нажать «Найти и добавить обложку». Если приложение сообщит, "
            "что файл не найден, убедитесь, что в нужной папке есть изображение с меткой "
            "«8 MB» и повторите попытку.",
            wordWrap=True
        )
        desc.setStyleSheet("margin-top:8px;")
        lo.addWidget(desc)

        # ── навигация ──
        nav = QHBoxLayout()
        self.next_btn = QPushButton("➡ Следующий шаг", enabled=False,
                                    clicked=self.go_to_next_step)
        back_btn = QPushButton("⬅ Назад",
                               clicked=lambda: self.main_app.stack.setCurrentWidget(
                                   self.main_app.main_menu))
        nav.addWidget(self.next_btn)
        nav.addWidget(back_btn)
        lo.addLayout(nav)

        return lo

    # ────────────────────── helpers ──────────────────────
    def log(self, text: str):
        self.log_out.append(text)

    def _err(self, title: str, msg: str):
        QMessageBox.critical(self, title, msg)

    # ────────────────────── logic ────────────────────────
    def run_step4(self):
        # 1) session.json
        if not os.path.exists(SESSION_FILE):
            self._err("Ошибка", "Нет session.json — повторите предыдущие шаги."); return
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            ses = json.load(f)

        code, name, aiff = (ses.get(k, "") for k in
                            ("album_code", "album_name", "album_path_aiff"))
        if not (code and name and aiff):
            self.log("❌ Недостаточно данных в session.json."); return

        # 2) config.json → папка обложек
        if not os.path.exists(CONFIG_FILE):
            self._err("Ошибка", "Нет config.json!"); return
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            covers_root = json.load(f).get("_ALL ALBUMS COVERS", "")
        if not covers_root or not os.path.isdir(covers_root):
            self._err("Ошибка", f"Папка обложек не найдена:\n{covers_root}"); return

        # 3) ищем файл
        album_dir = os.path.join(covers_root, f"{code} {name}")
        if not os.path.isdir(album_dir):
            self.log(f"❌ Нет папки: {album_dir}"); return
        cover = next((f for f in os.listdir(album_dir)
                      if re.search(r"8[\s_]?mb", f, re.I)), None)
        if not cover:
            self.log("❌ Не найден файл с «8 MB»."); return
        self.log(f"✅ Найден файл: {cover}")

        # 4) копируем
        ext = os.path.splitext(cover)[1]
        dst = os.path.join(aiff, f"{code} {name}{ext}")
        try:
            shutil.copy2(os.path.join(album_dir, cover), dst)
            self.log(f"✅ Скопировано → {os.path.basename(dst)}")
        except Exception as e:
            self.log(f"❌ Ошибка копирования: {e}"); return

        # 5) сохраняем и активируем «Следующий шаг»
        ses["cover_file"] = dst
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(ses, f, indent=4)
        self.log("✅ Шаг 4 завершён!")
        self.next_btn.setEnabled(True)
        self.next_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold;")
        self.next_step_sound = QSoundEffect()
        self.next_step_sound.setSource(QUrl.fromLocalFile("notify.wav"))
        self.next_step_sound.setVolume(0.5)
        self.next_step_sound.play()

    # ────────────────────── next ────────────────────────
    def go_to_next_step(self):
        from step_prepare_step5 import StepPrepareStep5
        w = StepPrepareStep5(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)