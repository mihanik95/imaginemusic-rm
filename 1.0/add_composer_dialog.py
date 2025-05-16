import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QComboBox
)
from PyQt6.QtCore import Qt

DATABASES_FOLDER = "_DATABASES"
COMPOSER_DB_FILENAME = "composer_database.json"

class AddComposerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить нового композитора")
        self.setModal(True)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Поля ввода
        self.first_name_edit = QLineEdit()
        self.middle_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.society_edit = QLineEdit()
        self.ipi_edit = QLineEdit()

        layout.addWidget(QLabel("First Name:"))
        layout.addWidget(self.first_name_edit)

        layout.addWidget(QLabel("Middle Name:"))
        layout.addWidget(self.middle_name_edit)

        layout.addWidget(QLabel("Last Name:"))
        layout.addWidget(self.last_name_edit)

        layout.addWidget(QLabel("Society (PRO):"))
        layout.addWidget(self.society_edit)

        layout.addWidget(QLabel("IPI Number:"))
        layout.addWidget(self.ipi_edit)

        # Добавим ComboBox для выбора publisher
        layout.addWidget(QLabel("Publisher:"))
        self.publisher_combo = QComboBox()
        layout.addWidget(self.publisher_combo)

        # Сразу загрузим publishers для ComboBox
        self.load_publishers()

        # Кнопки "OK" / "Cancel"
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.reject)

    def load_publishers(self):
        """Считываем publisher-keys из composer_database.json, кладём их в ComboBox."""
        db_path = os.path.join(DATABASES_FOLDER, COMPOSER_DB_FILENAME)
        self.publisher_combo.clear()
        self.publisher_combo.addItem("")  # вариант "нет издателя"

        if not os.path.exists(db_path):
            return

        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        publishers_db = data.get("publishers", {})
        # publishers_db = {
        #   "Imagine International Music Publishing": {...},
        #   "Imagine Music Publishing RU": {...}
        # }
        # Ключи — это те, что "Imagine International Music Publishing"

        for publisher_key in publishers_db.keys():
            self.publisher_combo.addItem(publisher_key)

    def on_ok(self):
        """Сохраняем нового композитора в JSON и выходим"""
        first_name = self.first_name_edit.text().strip()
        middle_name = self.middle_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        society = self.society_edit.text().strip()
        ipi = self.ipi_edit.text().strip()
        publisher_key = self.publisher_combo.currentText().strip()

        # Проверяем, что хотя бы first_name и last_name не пусты
        if not first_name and not last_name:
            # Можно вывести messageBox, но не будем
            return

        parts = [
            self.first_name_edit.text().strip(),
            self.middle_name_edit.text().strip(),
            self.last_name_edit.text().strip()
        ]
        parts = [p for p in parts if p]  # фильтр пустых
        full_key = " ".join(parts)
        if not full_key:
            return

        db_path = os.path.join(DATABASES_FOLDER, COMPOSER_DB_FILENAME)

        # Если база не существует, создаём структуру { "composers": {}, "publishers": {} }
        if not os.path.exists(db_path):
            data = { "composers": {}, "publishers": {} }
        else:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "composers" not in data:
                    data["composers"] = {}
                if "publishers" not in data:
                    data["publishers"] = {}

        composers_db = data["composers"]

        if full_key not in composers_db:
            composers_db[full_key] = {
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "society": society,
                "ipi": ipi,
                "publisher_key": publisher_key  # <-- важно!
            }

        # Сохраняем обратно
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        self.accept()
