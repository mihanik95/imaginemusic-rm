# step_prepare_step6.py
import os, json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt


class StepPrepareStep6(QWidget):
    """Переходный экран‑напоминание перед Шагом 6."""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ПОДГОТОВКА К ШАГУ 6", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        root.addWidget(title)

        # ── «фиктивный лог» (заполняет всё пространство) ──
        info = QTextEdit(readOnly=True)
        info.setFrameShape(QTextEdit.Shape.NoFrame)
        info.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        info.setStyleSheet("font-size:12pt;")

        info.setMarkdown(
            "**Перед тем, как продолжить ⬇**\n\n"
            "1. Убедитесь, что в таблице TOTAL METADATA всё заполнено корректно, ISRC-номера идут по порядку за предыдущим альбомом и нет никаких странных сдвигов колонок, больших отступов и так далее.\n"
            "2. Заходите на DISCO и вносите все оставшиеся метаданные из таблицы в залитые ранее треки.\n"
            "3. Создавайте DISCO-плейлист и получайте на него ссылку.\n"
            "4. Скачивайте плейлист в папки _ALL ALBUMS AIFF и _ALL ALBUMS MP3\n"
            "5. Убедитесь, что все созданные программой файлы (папка с альбомом, стемы, метаданные) были успешно загружены на Яндекс.Диск.\n"
            "6. Отправляйте ссылку на плейлист Михаилу, а также информируйте о том, что папки с треками и метаданные готовы, а альбом залит на DISCO.\n\n"
            "Когда всё готово, нажмите «Следующий шаг»."
        )
        root.addWidget(info)

        # ── навигация ──
        nav = QHBoxLayout()
        next_btn = QPushButton("➡ Следующий шаг", clicked=self.go_to_step6)
        next_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold;")

        back_btn = QPushButton("⬅ Назад", clicked=lambda:
            self.main_app.stack.setCurrentWidget(self.main_app.main_menu)
        )
        nav.addWidget(next_btn)
        nav.addWidget(back_btn)
        root.addLayout(nav)

    def go_to_step6(self):
        from step6_prepare_harvest import Step6PrepareHarvest
        w = Step6PrepareHarvest(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)
