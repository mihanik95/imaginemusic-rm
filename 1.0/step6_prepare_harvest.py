# step6_prepare_harvest.py
import os, json, shutil, subprocess
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore         import Qt, QUrl
from PyQt6.QtMultimedia   import QSoundEffect
from PyQt6.QtGui          import QDesktopServices


SESSION_FILE = "session.json"
CONFIG_FILE  = "config.json"


class Step6PrepareHarvest(QWidget):
    """
    Шаг 6 — подготовка альбома для Harvest.
      1. Проверяем, что в AIFF / MP3 лежат финальные файлы, скачанные с DISCO.
      2. Создаём папку альбома в *Harvest Albums*.
      3. Копируем обложку, конвертируем AIFF → WAV 24/48, копируем .xlsx,
         генерируем таб-разделённый .txt.
    """

    # ──────────────────────────── UI ────────────────────────────
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.setLayout(self._build_ui())
        self.load_config()          # подгружаем config.json

    def _build_ui(self) -> QVBoxLayout:
        lo = QVBoxLayout()
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)

        # ── заголовок ──
        title = QLabel("ШАГ 6: ПОДГОТОВКА ДЛЯ HARVEST",
                       alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt; font-weight:600; margin-bottom:8px;")
        lo.addWidget(title)

        # ── лог  ──
        self.log_out = QTextEdit(readOnly=True)
        self.log_out.setMinimumHeight(160)
        lo.addWidget(self.log_out)

        # ── run-кнопка ──
        self.run_btn = QPushButton("✅ Подготовить релиз для Harvest",
                                   clicked=self.run_step6)
        self.run_btn.setMinimumHeight(32)
        lo.addWidget(self.run_btn)

        # ── описание шага ──
        desc = QLabel(
            "Описание: программа проверит, что в папках *_ALL ALBUMS AIFF* и "
            "*_ALL ALBUMS MP3* лежат финальные треки, затем создаст структуру "
            "альбома в *Harvest Albums*, скопирует обложку, конвертирует все "
            "AIFF в 24-битные / 48 кГц WAV, перенесёт файл метаданных и "
            "сгенерирует .txt.\n\n"
            "Ваша задача – убедиться, что файлы действительно скачаны с DISCO, "
            "а затем нажать «Подготовить релиз для Harvest».",
            wordWrap=True
        )
        desc.setStyleSheet("margin-top:8px;")
        lo.addWidget(desc)

        # ── навигация ──
        nav = QHBoxLayout()
        self.next_btn = QPushButton("➡ Следующий шаг", enabled=False,
                                    clicked=self.go_to_next_step)
        self.back_btn = QPushButton("⬅ Назад",
                                    clicked=lambda:
                                    self.main_app.stack.setCurrentWidget(
                                        self.main_app.main_menu))
        nav.addWidget(self.next_btn)
        nav.addWidget(self.back_btn)
        lo.addLayout(nav)
        return lo

    # ─────────────────────── helpers ────────────────────────
    def log(self, text: str):
        self.log_out.append(text)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.show_error("Ошибка", "config.json не найден. Повторите предыдущие шаги."); return
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def _err(self, title: str, msg: str):
        QMessageBox.critical(self, title, msg)

    # ─────────────────────── logic ──────────────────────────
    def run_step6(self):
        # session.json
        if not os.path.exists(SESSION_FILE):
            self._err("Ошибка", "Нет session.json — повторите предыдущие шаги."); return
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            self.session_data = json.load(f)

        # проверяем треки
        if not self.verify_all_tracks():
            return

        # готовим Harvest
        self.prepare_for_harvest()

    # ---------- verify ----------
    def verify_all_tracks(self) -> bool:
        code  = self.session_data.get("album_code","IMG000")
        name  = self.session_data.get("album_name","Unknown")

        p_aiff = self.config.get("_ALL ALBUMS AIFF","")
        p_mp3  = self.config.get("_ALL ALBUMS MP3","")
        if not os.path.isdir(p_aiff) or not os.path.isdir(p_mp3):
            self._err("Ошибка", "Папки AIFF / MP3 не найдены в config.json"); return False

        f_aiff_folder = self.session_data.get("album_path_aiff","")
        f_mp3_folder  = self.session_data.get("album_path_mp3","")
        if not os.path.isdir(f_aiff_folder) or not os.path.isdir(f_mp3_folder):
            self._err("Ошибка", "Альбом не найден в AIFF или MP3"); return False

        for trk in self.session_data.get("tracks", []):
            num  = trk.get("track_number","")
            t_nm = trk.get("track_name","")
            base = f"{code} - {name} - {num} {t_nm}"

            # AIFF
            if not any(os.path.exists(os.path.join(f_aiff_folder, base + ext))
                       for ext in (".aiff", ".aif")):
                self._err("Ошибка", f"Не найден AIFF: {base}"); return False

            # MP3
            if not os.path.exists(os.path.join(f_mp3_folder, base + ".mp3")):
                self._err("Ошибка", f"Не найден MP3: {base}.mp3"); return False
        self.log("✅ Все треки найдены.")
        return True

    # ---------- prepare ----------
    def prepare_for_harvest(self):
        code = self.session_data.get("album_code","IMG000")
        name = self.session_data.get("album_name","Unknown")
        cover= self.session_data.get("cover_file","")
        meta_root = self.config.get("_ALL ALBUMS METADATA","")
        hv_root = self.config.get("_ALL ALBUMS HARVEST","")

        if not os.path.isdir(hv_root):
            self._err("Ошибка", "Папка Harvest Albums не найдена!"); return

        hv_album = os.path.join(hv_root, f"{code} {name}")
        if os.path.exists(hv_album):
            if QMessageBox.question(self, "Перезапись",
                                    f"Папка {hv_album} уже существует. Удалить и создать заново?",
                                    QMessageBox.StandardButton.Yes |
                                    QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No) \
               == QMessageBox.StandardButton.No:
                self.log("Отмена."); return
            try: shutil.rmtree(hv_album)
            except Exception as e:
                self._err("Ошибка", f"Не удалось удалить старую папку: {e}"); return
        os.makedirs(hv_album)

        # обложка
        if cover and os.path.exists(cover):
            shutil.copy2(cover, os.path.join(hv_album, os.path.basename(cover)))
            self.log("✅ Обложка скопирована.")

        # конвертация AIFF → WAV
        aiff_folder = self.session_data["album_path_aiff"]
        for fname in os.listdir(aiff_folder):
            fpath = os.path.join(aiff_folder, fname)
            if os.path.isdir(fpath) and fname.lower() == "stems":
                continue
            if fname.lower().endswith((".aif", ".aiff")):
                wav_out = os.path.join(hv_album, os.path.splitext(fname)[0] + ".wav")
                if self.convert_to_wav_24_48(fpath, wav_out):
                    self.log(f"✅ {fname} → WAV")
                else:
                    self._err("Ошибка", f"Не удалось конвертировать {fname}"); return
            else:                                   # копируем «как есть»
                shutil.copy2(fpath, os.path.join(hv_album, fname))

        # метаданные .xlsx + .txt
        meta_xlsx = os.path.join(
            meta_root, f"{code.upper()} {name.upper()} METADATA.xlsx")
        if os.path.exists(meta_xlsx):
            dst_xlsx = os.path.join(hv_album, os.path.basename(meta_xlsx))
            shutil.copy2(meta_xlsx, dst_xlsx)
            dst_txt  = dst_xlsx.replace(".xlsx", ".txt")
            self.generate_tab_delimited(dst_xlsx, dst_txt)
            self.log("✅ Метаданные и TXT скопированы.")
        else:
            self.log("❌ Файл METADATA.xlsx не найден — пропускаем.")

        self.log(f"✅ Папка для Harvest подготовлена: {hv_album}")
        self.activate_next_step()

    # ---------- converters ----------
    def convert_to_wav_24_48(self, src, dst) -> bool:
        try:
            subprocess.run(["ffmpeg","-y","-i", src,
                            "-c:a","pcm_s24le","-ar","48000", dst],
                           check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print("ffmpeg error:", e)
            return False

    def generate_tab_delimited(self, xlsx_path, txt_path):
        try:
            df = pd.read_excel(xlsx_path, dtype=str).fillna("")
            df.to_csv(txt_path, sep='\t', index=False)
        except Exception as e:
            self._err("Ошибка", f"Не удалось сохранить TXT: {e}")

    # ---------- misc ----------
    def activate_next_step(self):
        self.next_btn.setEnabled(True)
        self.next_btn.setStyleSheet(
            "background-color:#388E3C; color:white; font-weight:bold;")
        # пинг
        self._snd = QSoundEffect()
        self._snd.setSource(QUrl.fromLocalFile("notify.wav"))
        self._snd.setVolume(0.5)
        self._snd.play()

    def show_question(self, title, text) -> bool:
        return QMessageBox.question(
            self, title, text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes

    def show_error(self, title, text):   # оставлено для совместимости
        self._err(title, text)

    def go_to_next_step(self):
        from step_prepare_step7 import StepPrepareStep7
        w = StepPrepareStep7(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)

