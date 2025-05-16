import os, json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt


class StepPrepareStep1(QWidget):
    """Переходный экран‑напоминание перед Шагом 1."""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ПАМЯТКА", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        root.addWidget(title)

        # ── текст-памятка ──
        info = QTextEdit(readOnly=True)
        info.setFrameShape(QTextEdit.Shape.NoFrame)
        info.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        info.setStyleSheet("font-size:12pt;")

        info.setMarkdown(
            "**Напоминание о том, что необходимо проверить перед началом работы:**\n\n"
            "1. Убедиться, что все файлы в *_НЕГОТОВОЕ/Альбом/_MASTERED* на месте и правильно проименованы "
            "(в формате *IMG000 - Album - 01 Track.aif*) — это лежит в корне всех процессов, "
            "которые будут происходить далее\n"
            "2. Описания альбома, треков, album style и дата релиза согласованы и готовы к вставке\n"
            "3. Обложка от дизайнера получена и лежит в *_ALL ALBUMS COVERS/Альбом*\n"
            "4. Видео превью залито на YouTube и ссылка на него под рукой\n"
            "5. Все отмастеренные треки **залиты на DISCO**\n"
            "6. В каждом треке заполнены **Keywords** и **Instrumentation**\n\n"
            "Когда всё готово, нажмите «Следующий шаг»."
        )
        root.addWidget(info)

        # ── навигация ──
        nav = QHBoxLayout()
        next_btn = QPushButton("➡ Начать работу",
                               clicked=self.go_to_step1)
        next_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold;")
        back_btn = QPushButton("⬅ Назад",
                               clicked=lambda:
                               self.main_app.stack.setCurrentWidget(
                                   self.main_app.main_menu))
        nav.addWidget(next_btn)
        nav.addWidget(back_btn)
        root.addLayout(nav)

    # ────────────────────────── переход к Шагу 1 ──────────────────────────
    def go_to_step1(self):
        from step1_create_structure import Step1CreateStructure
        w = Step1CreateStructure(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)