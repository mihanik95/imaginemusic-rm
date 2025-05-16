# step1_create_structure.py
import os, re, json, subprocess, shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QTextEdit,
    QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

from util_json import load_json_safe

CONFIG_FILE  = "config.json"
SESSION_FILE = "session.json"


# ──────────── util ────────────
def get_track_duration(file_path: str) -> float | None:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return round(float(r.stdout.strip()), 2)
    except Exception:
        return None


# ──────────── ШАГ 1 ────────────
class Step1CreateStructure(QWidget):
    """Шаг 1 — создаём структуру альбома и session.json."""

    # ───── UI ─────
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

        lay = QVBoxLayout(self)                 # общие «нулевые» отступы
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # Заголовок
        title = QLabel("ШАГ 1: СТРУКТУРА АЛЬБОМА",
                       alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        lay.addWidget(title)

        # Выбор альбома
        lay.addWidget(QLabel("📂 Выберите альбом из _НЕГОТОВЫЕ:"))
        self.album_list = QListWidget()
        lay.addWidget(self.album_list)

        self.select_button = QPushButton("✅ Выбрать альбом",
                                         clicked=self.process_selected_album)
        lay.addWidget(self.select_button)

        # Лог
        self.log_output = QTextEdit(readOnly=True)
        lay.addWidget(self.log_output)

        # Подсказка
        self.description = QLabel(
            "Описание шага: программа сканирует выбранный альбом, находит папку "
            "_MASTERED, извлекает код, название и список треков, создаёт структуру "
            "папок в _ALL ALBUMS AIFF/MP3 и сохраняет всё в session.json. \n\n"
            "Ваша задача – отметить нужный альбом в списке и нажать «Выбрать альбом», "
            "затем убедиться, что количество треков совпадает с _MASTERED, ни один "
            "трек не потерян, а BPM указаны верно.",
            wordWrap=True
        )
        self.description.setStyleSheet("margin-top:8px;")
        lay.addWidget(self.description)

        # ── навигация (стиль шага 4) ──
        nav = QHBoxLayout()
        self.next_button = QPushButton("➡ Следующий шаг")
        self.next_button.setEnabled(False)      # появляется сразу, но неактивен
        self.next_button.clicked.connect(self.go_to_next_step)

        back_btn = QPushButton("⬅ Назад")
        back_btn.clicked.connect(self.go_back)

        nav.addWidget(self.next_button)
        nav.addWidget(back_btn)
        lay.addLayout(nav)

        # ── внутреннее ──
        self.selected_album = self.album_code = self.album_name = None
        self.track_list, self.tracks_data = [], []

        self.load_settings()
        self.load_albums()

    # ───────── настройки / альбомы ─────────
    def load_settings(self):
        cfg_path = CONFIG_FILE                         # либо rsrc(CONFIG_FILE)
        self.paths = load_json_safe(cfg_path, {})      # ← одно слово

    def load_albums(self):
        self.album_list.clear()
        if "_НЕГОТОВЫЕ" in self.paths:
            p = self.paths["_НЕГОТОВЫЕ"]
            if os.path.exists(p):
                self.album_list.addItems(
                    d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d))
                )
            else:
                self.log("❌ Папка _НЕГОТОВЫЕ не найдена!")

    # ───────── логи ─────────
    def log(self, msg: str): self.log_output.append(msg)

    # ───────── основная логика ─────────
    def process_selected_album(self):
        item = self.album_list.currentItem()
        if not item:
            self.log("❌ Выберите альбом!"); return

        self.selected_album = item.text()
        album_path = os.path.join(self.paths["_НЕГОТОВЫЕ"], self.selected_album)
        mastered_path = os.path.join(album_path, "_MASTERED")
        self.log(f"\n🔹 Выбран альбом: {self.selected_album}")

        if not os.path.exists(mastered_path):
            self.show_error("Ошибка! В папке альбома нет _MASTERED.")
            self.log("❌ Нет _MASTERED."); return

        self.log("📂 Найдена _MASTERED, анализирую…")
        mastered_tracks = [
            f for f in os.listdir(mastered_path)
            if re.match(r'IMG\d{3} - .* - \d{2} .*\.aif{1,2}$', f)
        ]
        if not mastered_tracks:
            self.show_error("Ошибка! В _MASTERED не найдено треков.")
            self.log("❌ Нет треков."); return

        self.log(f"✅ Найдено {len(mastered_tracks)} треков:")
        for t in mastered_tracks: self.log(f"   🎵 {t}")

        m = re.match(r'(IMG\d{3}) - (.*?) - \d{2} .*', mastered_tracks[0])
        if not m:
            self.show_error("Ошибка! Не удалось определить код и название альбома.")
            self.log("❌ Не удалось спарсить код/название."); return
        self.album_code, self.album_name = m.groups()
        self.track_list = sorted(mastered_tracks)

        self.log(f"📌 Код: {self.album_code}")
        self.log(f"📌 Название: {self.album_name}")

        self.tracks_data.clear()
        for track_file in self.track_list:
            tm = re.match(r'(IMG\d{3}) - (.*?) - (\d{2}) (.*)\.aif{1,2}$', track_file)
            if not tm: continue
            _, _, track_number, track_name = tm.groups()

            full_path = os.path.join(mastered_path, track_file)
            duration  = get_track_duration(full_path)

            poss = os.listdir(album_path)
            track_folder = next((x for x in poss if track_name in x), None)
            if track_folder and (fm := re.match(r'(.+?) - (.+) (\d+)$', track_folder)):
                composer_full, _, bpm = fm.groups()
                composers = [c.strip() for c in composer_full.split(" and ")]
            else:
                composers = ["Неизвестный"]; bpm = "000"

            self.tracks_data.append({
                "track_number": track_number,
                "track_name": track_name,
                "composers": composers,
                "track_bpm": bpm,
                "duration": duration,
                "mastered_file": track_file
            })

        self.create_album_folders(album_path)
        self.show_success_popup()
        self.next_button.setEnabled(True)   # ← теперь просто активируем
        self.next_button.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold;")
        # проигрываем звук
        self.next_step_sound = QSoundEffect()
        self.next_step_sound.setSource(QUrl.fromLocalFile("notify.wav"))
        self.next_step_sound.setVolume(0.5)
        self.next_step_sound.play()

    # ──────────────────────────────────────────────────────────────────────────
    #             создание структуры IMG PART и папок альбома
    # ──────────────────────────────────────────────────────────────────────────
    def find_or_create_img_part(self, base_path: str) -> str:
        """Возвращает подходящую _IMG PART X (макс 5 альбомов) или создаёт новую."""
        parts = sorted(
            [d for d in os.listdir(base_path) if re.match(r'_IMG PART \d+', d)],
            key=lambda x: int(x.split()[-1])
        )
        if not parts:
            new_part = os.path.join(base_path, "_IMG PART 1")
            os.makedirs(new_part)
            return new_part

        last_part = os.path.join(base_path, parts[-1])
        if len([d for d in os.listdir(last_part) if os.path.isdir(os.path.join(last_part, d))]) < 5:
            return last_part

        new_num = int(parts[-1].split()[-1]) + 1
        new_part = os.path.join(base_path, f"_IMG PART {new_num}")
        os.makedirs(new_part)
        return new_part

    def create_album_folders(self, album_path_negotovoe: str):
        """Создаёт все нужные папки (c перезаписью) и сохраняет session.json."""
        ai_parent = self.find_or_create_img_part(self.paths["_ALL ALBUMS AIFF"])
        mp_parent = self.find_or_create_img_part(self.paths["_ALL ALBUMS MP3"])

        album_aiff = os.path.join(ai_parent, f"{self.album_code} {self.album_name}")
        album_mp3  = os.path.join(mp_parent,  f"{self.album_code} {self.album_name}")

        # ── если каталоги уже существуют ────────────────────────────────────
        if os.path.exists(album_aiff) or os.path.exists(album_mp3):
            ask = QMessageBox.question(
                self, "Папки уже существуют",
                "Каталоги альбома уже есть в _ALL ALBUMS.\n"
                "Перезаписать их (старые данные будут удалены)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if ask == QMessageBox.StandardButton.No:
                self.log("⚠️ Создание отменено пользователем."); return

            # удаляем и логируем
            for p in (album_aiff, album_mp3):
                if os.path.exists(p):
                    shutil.rmtree(p)
                    self.log(f"♻️ Удалён старый каталог: {p}")

        # ── создаём заново ────────────────────────────────────────────────────
        os.makedirs(album_aiff, exist_ok=True)
        os.makedirs(album_mp3,  exist_ok=True)

        stems_path = os.path.join(album_aiff, "Stems")
        os.makedirs(stems_path, exist_ok=True)

        self.log(f"📂 Созданы:\n  - {album_aiff}\n  - {album_mp3}\n  - {stems_path}")

        # подпапки стемов
        for tr in self.tracks_data:
            folder_name = f"{self.album_code} - {self.album_name} - {tr['track_number']} {tr['track_name']}"
            fp = os.path.join(stems_path, folder_name)
            os.makedirs(fp, exist_ok=True)
            tr["stems_folder"] = fp
            self.log(f"📁 Папка стемов: {fp}")

        # ── session.json ─────────────────────────────────────────────────────
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "album_code":  self.album_code,
                "album_name":  self.album_name,
                "album_path_negotovoe": album_path_negotovoe,
                "album_path_aiff":     album_aiff,
                "album_path_mp3":      album_mp3,
                "stems_path":          stems_path,
                "tracks":              self.tracks_data
            }, f, indent=4, ensure_ascii=False)

        self.log("💾 session.json сохранён — можно переходить к Шагу 2.")

    # ──────────────────────────────────────────────────────────────────────────
    #                     всплывающие окна / навигация
    # ──────────────────────────────────────────────────────────────────────────
    def show_success_popup(self):
        tcount = len(self.tracks_data)

        # формируем перечень строк вида «01 Track Name (Composer, BPM=120)»
        details = "\n".join(
            f"{t['track_number']} {t['track_name']} "
            f"({', '.join(t['composers'])}, BPM={t['track_bpm']})"
            for t in self.tracks_data
        )

        msg = QMessageBox(self)
        msg.setWindowTitle("🎵 Анализ завершён")
        msg.setIcon(QMessageBox.Icon.Information)

        # основной текст сразу содержит полный список — ничего дополнительно раскрывать не нужно
        msg.setText(f"Найдено треков: {tcount}\n\n{details}")
        msg.exec()

    def show_error(self, text: str):
        m = QMessageBox()
        m.setWindowTitle("❌ Ошибка")
        m.setText(text)
        m.setIcon(QMessageBox.Icon.Critical)
        m.exec()

    def go_to_next_step(self):
        from step2_process_stems import Step2ProcessStems
        w = Step2ProcessStems(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)

    def go_back(self):
        self.main_app.stack.setCurrentWidget(self.main_app.main_menu)