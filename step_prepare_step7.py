# step_prepare_step7.py
import os, json   # ← оставлены «про запас», как в других подготовках
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt


class StepPrepareStep7(QWidget):
    """Переходный экран-напоминание перед Шагом 7."""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ПОДГОТОВКА К ШАГУ 7", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        root.addWidget(title)

        # ── информационный текст ──
        info = QTextEdit(readOnly=True)
        info.setFrameShape(QTextEdit.Shape.NoFrame)
        info.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        info.setStyleSheet("font-size:12pt;")

        info.setMarkdown(
            "**Перед тем, как продолжить, убедитесь в готовности следующих пунктов ⬇**\n\n"
            "1. *YouTube-превью* альбома **загружено** и у вас есть ссылка\n"
            "2. Альбом **полностью оформлен** в DISCO и *готов к публикации*\n\n"
            "Публикуйте альбом на DISCO и подготовьте публичную ссылку на него (которая находится на search.imaginemx.com)\n"
            "Когда всё будет готово — нажмите «Следующий шаг»."
        )
        root.addWidget(info)

        # ── навигация ──
        nav = QHBoxLayout()
        next_btn = QPushButton("➡ Следующий шаг", clicked=self.go_to_step7)
        next_btn.setStyleSheet("background-color:#388E3C;color:white;font-weight:bold;")
        back_btn = QPushButton("⬅ Назад",
                               clicked=lambda:
                               self.main_app.stack.setCurrentWidget(
                                   self.main_app.main_menu))
        nav.addWidget(next_btn)
        nav.addWidget(back_btn)
        root.addLayout(nav)

    # ───────────────────── переход к Шагу 7 ─────────────────────
    def go_to_step7(self):
        from step7_social_media import Step7SocialMedia
        w = Step7SocialMedia(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)
