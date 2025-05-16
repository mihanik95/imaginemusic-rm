# step_finals.py
import os, json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QSoundEffect


class StepFinals(QWidget):
    """Финальный экран-напоминание после выпуска альбома."""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ФИНАЛЬНЫЕ ДЕЙСТВИЯ", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt; font-weight:600; margin-bottom:8px;")
        root.addWidget(title)

        # ── памятка ──
        info = QTextEdit(readOnly=True)
        info.setFrameShape(QTextEdit.Shape.NoFrame)
        info.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        info.setStyleSheet("font-size:12pt;")
        info.setMarkdown(
            "**Ура, вся работа в приложении завершена!** Не забудьте выполнить следующие пункты ⬇\n\n"
            "1. Выставить все посты в социальных сетях (Лиза)\n"
            "2. Отправить общую рассылку (Михаил)\n"
            "3. Зарегистрировать треки в BMI (Михаил)\n"
            "4. Залить треки в Harvest\n"
            "5. 🎉 Сказать себе, что ты молодец\n\n"
            "**До следующего релиза!**"
        )
        root.addWidget(info)

        # ── навигация ──
        nav = QHBoxLayout()
        back_btn = QPushButton("⬅ В главное меню", clicked=self.go_to_main_menu)
        back_btn.setMinimumHeight(32)                           # одинаковая высота
        back_btn.setStyleSheet("background:#388E3C; color:white; font-weight:bold;")
        nav.addStretch(1)
        nav.addWidget(back_btn)
        nav.addStretch(1)
        root.addLayout(nav)

        # ── звук ──
        self.sound = QSoundEffect(self)
        self.sound.setSource(QUrl.fromLocalFile("bruh.wav"))  # WAV/OGG файл
        self.sound.setVolume(0.5)
        self.sound.play()

    # ── helpers ──
    def go_to_main_menu(self):
        self.main_app.stack.setCurrentWidget(self.main_app.main_menu)
