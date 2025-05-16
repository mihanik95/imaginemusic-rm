import sys, os, json

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget
)
from PyQt6.QtGui  import QPixmap, QCursor
from PyQt6.QtCore import Qt

from step1_create_structure import Step1CreateStructure
from settings_page          import SettingsPage
from composer_list_page     import ComposerListPage
from step_prepare_step1     import StepPrepareStep1

from util_json import load_json_safe


# ───────────────────────── util: путь к ресурсам ──────────────────────────
def rsrc(rel_path: str) -> str:
    """
    Возвращает абсолютный путь к ресурсу:
    • при запуске из исходников — рядом с .py  
    • в упакованном .app / .exe — внутри каталога Resources
    """
    if getattr(sys, 'frozen', False):                # PyInstaller
        base = sys._MEIPASS                         # type: ignore
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, rel_path)


CONFIG_FILE = "config.json"                         # имя не меняем — используем rsrc()

# ───────────────────────────── главное окно ───────────────────────────────
class AlbumReleaseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Imagine Music Release Master")
        self.setGeometry(100, 100, 800, 600)

        root_layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack)

        # ── главное меню ──
        self.main_menu = QWidget()
        menu_lo = QVBoxLayout(self.main_menu)
        menu_lo.setAlignment(Qt.AlignmentFlag.AlignTop)
        menu_lo.setSpacing(14)

        # логотип
        logo_path = rsrc("logo.png")
        if os.path.exists(logo_path):
            logo_lbl = QLabel()
            logo_lbl.setPixmap(
                QPixmap(logo_path).scaledToHeight(
                    180, Qt.TransformationMode.SmoothTransformation)
            )
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            menu_lo.addWidget(logo_lbl)

        # большой заголовок
        title = QLabel("IMAGINE MUSIC RELEASE MASTER", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        menu_lo.addWidget(title)

        # общий стиль кнопок
        btn_style = "font-size:14pt;padding:8px 12px;"

        self.start_button = QPushButton("✅ НОВЫЙ АЛЬБОМ", clicked=self.start_step1)
        self.start_button.setStyleSheet(btn_style)
        self.start_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        menu_lo.addWidget(self.start_button)

        self.settings_button = QPushButton("⚙️ НАСТРОЙКИ", clicked=self.show_settings)
        self.settings_button.setStyleSheet(btn_style)
        self.settings_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        menu_lo.addWidget(self.settings_button)

        self.composer_button = QPushButton("🎼 СПИСОК КОМПОЗИТОРОВ", clicked=self.show_composer_list)
        self.composer_button.setStyleSheet(btn_style)
        self.composer_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        menu_lo.addWidget(self.composer_button)

        # поясняющий текст
        welcome = QLabel(
            "Добро пожаловать в Release Master! Это приложение ускорит выпуск альбомов "
            "Imagine Music: проведёт вас шаг за шагом — от структуры и стемов до финальных "
            "метаданных и обложек. Сконцентрируйтесь на музыке, а рутиной займётся программа."
        )
        welcome.setWordWrap(True)
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("margin-top:18px;font-size:13pt;")
        menu_lo.addWidget(welcome)

        self.stack.addWidget(self.main_menu)

        # ── остальные страницы ──
        self.step1_page       = Step1CreateStructure(self)
        self.settings_page    = SettingsPage(self)
        self.composer_list_pg = ComposerListPage(self)

        for w in (self.step1_page, self.settings_page, self.composer_list_pg):
            self.stack.addWidget(w)

        self.load_settings()

    # ── навигация ──
    def start_step1(self):
        prep = StepPrepareStep1(self)
        self.stack.addWidget(prep)
        self.stack.setCurrentWidget(prep)

    def show_settings(self):
        self.stack.setCurrentWidget(self.settings_page)

    def show_composer_list(self):
        self.stack.setCurrentWidget(self.composer_list_pg)

    # ── загрузка путей из config.json ──
    def load_settings(self):
        cfg_path = rsrc(CONFIG_FILE)
        self.paths = load_json_safe(cfg_path, {})


# ────────────────────────────── запуск ──────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AlbumReleaseApp()
    win.show()

    # центрируем окно
    geo = win.frameGeometry()
    geo.moveCenter(win.screen().availableGeometry().center())
    win.move(geo.topLeft())

    sys.exit(app.exec())
