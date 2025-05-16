# step7_social_media.py
import os, json, traceback
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from step_finals import StepFinals

# ─── опциональный автоперевод EN→RU ───
try:
    from deep_translator import GoogleTranslator       # pip install deep-translator
    _tr_ok = True
except Exception:
    _tr_ok = False
# ──────────────────────────────────────

SESSION_FILE = "session.json"


class Step7SocialMedia(QWidget):
    """ШАГ 7 — формирование текстов для соцсетей и завершение релиза."""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.setWindowTitle("Шаг 7: Соцсети")

        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ШАГ 7: СОЦСЕТИ", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt; font-weight:600; margin-bottom:8px;")
        root.addWidget(title)

        # ── session.json ──
        if not os.path.exists(SESSION_FILE):
            QMessageBox.critical(self, "Ошибка", "Нет session.json — повторите предыдущие шаги.")
            self._back(); return
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            ses = json.load(f)
        self.album_code = ses.get("album_code", "")
        self.album_name = ses.get("album_name", "")
        self.album_desc_en = ses.get("album_description", "")

        # ── ссылки ──
        root.addWidget(QLabel("Ссылка на DISCO / Client Area:"))
        self.disco_in = QLineEdit();  root.addWidget(self.disco_in)

        root.addWidget(QLabel("Ссылка на YouTube-превью:"))
        self.yt_in = QLineEdit();     root.addWidget(self.yt_in)

        # ── описания ──
        root.addWidget(QLabel("Описание альбома (англ.):"))
        self.desc_en_in = QTextEdit(); self.desc_en_in.setText(self.album_desc_en)
        root.addWidget(self.desc_en_in)

        root.addWidget(QLabel("Описание альбома (рус.):"))
        self.desc_ru_in = QTextEdit(); self.desc_ru_in.setPlaceholderText("Автоперевод…")
        root.addWidget(self.desc_ru_in)
        self._auto_translate()

        # ── run-кнопка (обычный стиль) ──
        self.gen_btn = QPushButton("✅ Сгенерировать тексты", clicked=self._generate)
        self.gen_btn.setMinimumHeight(32)
        root.addWidget(self.gen_btn)

        # ── результат ──
        self.out = QTextEdit(readOnly=True); root.addWidget(self.out)

        # ── описание / ваша задача ──
        desc = QLabel(
            "Описание шага: программа формирует готовые посты для Instagram, Facebook, LinkedIn, "
            "VK и описание для YouTube.\n\n"
            "Ваша задача – ввести ссылки, при необходимости поправить русский перевод, "
            "нажать «Сгенерировать тексты», скопировать их и отправить Лизе для публикации. "
            "После этого жмите «Завершить выпуск альбома».",
            wordWrap=True
        )
        desc.setStyleSheet("margin-top:8px;")
        root.addWidget(desc)

        # ── навигация ──
        nav = QHBoxLayout()
        self.finish_btn = QPushButton("➡ Завершить выпуск альбома",
                                      enabled=False, clicked=self._finish)
        self.finish_btn.setMinimumHeight(32)
        back_btn = QPushButton("⬅ Назад", clicked=self._back)
        nav.addWidget(self.finish_btn); nav.addWidget(back_btn)
        root.addLayout(nav)

    # ────────────────── helpers ──────────────────
    def _auto_translate(self):
        if not (_tr_ok and self.album_desc_en.strip()):
            return
        try:
            ru = GoogleTranslator(source="en", target="ru").translate(self.album_desc_en)
            self.desc_ru_in.setText(ru)
        except Exception:
            print("[Step7] auto-translation failed:\n", traceback.format_exc())

    def _generate(self):
        disco, yt = self.disco_in.text().strip(), self.yt_in.text().strip()
        if not (disco and yt):
            QMessageBox.warning(self, "Внимание", "Заполните ссылки на DISCO и YouTube!"); return

        desc_en = self.desc_en_in.toPlainText().strip()
        desc_ru = self.desc_ru_in.toPlainText().strip()
        code, name = self.album_code, self.album_name

        insta = f"{code} {name} | New Album\n\n{desc_en}\n\n#imaginemusic"
        fb    = (f"{code} {name} | New Album\n\n{desc_en}\n\n"
                 f"The album is available for listening in our client area: {disco}\nPreview: {yt}")
        li    = (f"{code} {name} | New Album\n\n{desc_en}\n\n"
                 f"The album is available for listening in our client area: {disco}\n"
                 f"Preview: {yt}\n\n#imaginemusic #trailermusic")
        vk    = (f"{code} {name} | Новый альбом\n\n{desc_ru}\n\n"
                 f"Альбом уже доступен для прослушивания: {disco}\nПревью: {yt}")
        yt_desc = (f"{code} {name} | New Album\n\n{desc_en}\n\n"
                   f"The album is available for listening in our client area: {disco}")

        self.out.setPlainText(
            "=== INSTAGRAM ===\n" + insta + "\n\n"
            "=== FACEBOOK ===\n"  + fb    + "\n\n"
            "=== LINKEDIN ===\n"  + li    + "\n\n"
            "=== VK ===\n"       + vk    + "\n\n"
            "=== YOUTUBE ===\n"  + yt_desc
        )

        self.finish_btn.setEnabled(True)
        self.finish_btn.setStyleSheet("background:#388E3C; color:white; font-weight:bold;")

    # ─────────────── переходы ───────────────
    def _finish(self):
        w = StepFinals(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)

    def _back(self):
        self.main_app.stack.setCurrentWidget(self.main_app.main_menu)
