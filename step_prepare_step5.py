# step_prepare_step5.py
import os, json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt


class StepPrepareStep5(QWidget):
    """Переходный экран‑напоминание перед Шагом 5."""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ПОДГОТОВКА К ШАГУ 5", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        root.addWidget(title)

        # ── «фиктивный лог» (заполняет всё пространство) ──
        info = QTextEdit(readOnly=True)
        info.setFrameShape(QTextEdit.Shape.NoFrame)
        info.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        info.setStyleSheet("font-size:12pt;")          # тот же кегль, что в других шагах

        info.setMarkdown(
            "**Перед тем, как продолжить, подготовьте следующие данные ⬇**\n\n"
            "1. *Дата релиза*\n"
            "2. *Описание альбома*\n"
            "3. *Album Style*\n"
            "4. *Описания треков*\n"
            "5. *Keywords*\n"
            "6. *Instrumentation*\n\n"
            "Когда всё готово, нажмите «Следующий шаг»."
        )
        root.addWidget(info)                          # он займёт всё свободное место

        # ── навигация ──
        nav = QHBoxLayout()
        next_btn = QPushButton("➡ Следующий шаг",
                               clicked=self.go_to_step5)
        next_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold;")
        back_btn = QPushButton("⬅ Назад",
                               clicked=lambda:
                               self.main_app.stack.setCurrentWidget(
                                   self.main_app.main_menu))
        nav.addWidget(next_btn)
        nav.addWidget(back_btn)
        root.addLayout(nav)

    # ────────────────────────── переход к Шагу 5 ──────────────────────────
    def go_to_step5(self):
        from step5_generate_metadata import Step5GenerateMetadata
        w = Step5GenerateMetadata(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)
