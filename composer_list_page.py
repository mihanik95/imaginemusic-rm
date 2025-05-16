# composer_list_page.py
import os, json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox,
    QHeaderView
)
from PyQt6.QtCore import Qt
from add_composer_dialog import AddComposerDialog

from util_json import load_json_safe, dump_json_safe

DATABASES_FOLDER     = "_DATABASES"
COMPOSER_DB_FILENAME = "composer_database.json"

BTN_STYLE = "QPushButton{padding:6px 12px;font-size:12pt;}"
BTN_GREEN = ("QPushButton{background:#388E3C;color:white;font-weight:bold;"
             "padding:6px 12px;font-size:12pt;}")

class ComposerListPage(QWidget):
    """Экран «КОМПОЗИТОРЫ» (работа с composer_database.json)."""

    # ────────────────────────── UI ──────────────────────────
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self._build_ui()
        self.load_composers()                       # заполняем таблицу

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── заголовок ──
        title = QLabel("КОМПОЗИТОРЫ", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        root.addWidget(title)

        # ── таблица ──
        self.table = QTableWidget(columnCount=6)
        self.table.setHorizontalHeaderLabels([
            "First Name", "Middle Name", "Last Name",
            "Society", "IPI", "Publisher"
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._toggle_remove_btn)
        root.addWidget(self.table)

        # ── кнопки операций ──
        ops = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Обновить", clicked=self.load_composers)
        self.refresh_btn.setStyleSheet(BTN_STYLE)

        self.add_btn = QPushButton("➕ Добавить", clicked=self.add_new_composer)
        self.add_btn.setStyleSheet(BTN_STYLE)

        self.remove_btn = QPushButton("🗑 Удалить", clicked=self.remove_composer)
        self.remove_btn.setEnabled(False)
        self.remove_btn.setStyleSheet(BTN_STYLE)

        ops.addWidget(self.refresh_btn)
        ops.addWidget(self.add_btn)
        ops.addWidget(self.remove_btn)
        ops.addStretch(1)                           # сдвигаем кнопки влево
        root.addLayout(ops)

        # ── подсказка ──
        hint = QLabel(
            "⚠ Чтобы изменить существующие данные, перезалейте **TOTAL METADATA** "
            "в настройках. Здесь можно только **добавить** нового автора или "
            "**удалить** выбранного.",
            wordWrap=True
        )
        hint.setStyleSheet("font-size:10pt; margin-top:4px;")
        root.addWidget(hint)

        # ── навигация ──
        nav = QHBoxLayout()
        back_btn = QPushButton("⬅ В главное меню", clicked=self.go_back)
        back_btn.setStyleSheet(BTN_GREEN)           # зелёная кнопка, как в других шагах
        nav.addStretch(1)
        nav.addWidget(back_btn)
        nav.addStretch(1)
        root.addLayout(nav)

    # ────────────────────── загрузка / отображение ──────────────────────
    def load_composers(self):
        self.table.setRowCount(0)
        db_path = os.path.join(DATABASES_FOLDER, COMPOSER_DB_FILENAME)
        data = load_json_safe(db_path, {"composers": {}, "publishers": {}})
        composers   = data.get("composers", {})
        publishers  = data.get("publishers", {})

        for row, (full, info) in enumerate(sorted(composers.items())):
            self.table.insertRow(row)

            pub_key = info.get("publisher_key", "")
            pub = publishers.get(pub_key, {})
            pub_disp = pub.get("publisher_name", "")
            if pub_disp and pub.get("publisher_society"):
                pub_disp += f" ({pub['publisher_society']})"

            # первый item хранит полное имя в UserRole (нужно для удаления)
            item_first = QTableWidgetItem(info.get("first_name", ""))
            item_first.setData(Qt.ItemDataRole.UserRole, full)
            self.table.setItem(row, 0, item_first)
            self.table.setItem(row, 1, QTableWidgetItem(info.get("middle_name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(info.get("last_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(info.get("society", "")))
            self.table.setItem(row, 4, QTableWidgetItem(info.get("ipi", "")))
            self.table.setItem(row, 5, QTableWidgetItem(pub_disp))

        self.remove_btn.setEnabled(False)           # после перезагрузки — неактивна

    # ────────────────────── действия пользователя ───────────────────────
    def _toggle_remove_btn(self):
        self.remove_btn.setEnabled(bool(self.table.selectedItems()))

    def add_new_composer(self):
        dlg = AddComposerDialog(self)
        if dlg.exec():
            full = f"{dlg.first_name_edit.text().strip()} {dlg.last_name_edit.text().strip()}"
            QMessageBox.information(self, "Добавлено",
                                    f"Композитор «{full}» успешно добавлен!")
            self.load_composers()

    def remove_composer(self):
        sel_items = self.table.selectedItems()
        if not sel_items:
            return
        row = sel_items[0].row()
        full = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        if QMessageBox.question(
            self, "Удалить?", f"Удалить «{full}» из базы?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
            return

        # правим JSON
        db_path = os.path.join(DATABASES_FOLDER, COMPOSER_DB_FILENAME)
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if full in data.get("composers", {}):
            del data["composers"][full]
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        QMessageBox.information(self, "Удалено",
                                f"Композитор «{full}» удалён.")
        self.load_composers()

    # ─────────────────────────── навигация ────────────────────────────
    def go_back(self):
        self.main_app.stack.setCurrentWidget(self.main_app.main_menu)
