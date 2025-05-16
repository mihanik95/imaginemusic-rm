# step2_process_stems.py
"""
Шаг 2 — обработка стемов:
  • ищем/конвертируем стем‑файлы,
  • показываем окно проверки, где можно переименовать или удалить лишние стемы,
  • переименовываем окончательно, сохраняем в session.json.
"""
import os, re, json, subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QMessageBox, QLineEdit, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QCursor
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

SESSION_FILE     = "session.json"
IGNORE_KEYWORDS  = ["mix", "full mix", "unmastered", "mastered", "master", "bpm"]
AUDIO_EXTENSIONS = (".wav", ".aif", ".aiff")

# ───────────────────── helpers ─────────────────────
def show_error(title: str, text: str):
    m = QMessageBox(); m.setWindowTitle(title); m.setText(text)
    m.setIcon(QMessageBox.Icon.Critical); m.exec()

def load_session():
    if not os.path.exists(SESSION_FILE):
        show_error("Ошибка", f"Не найден {SESSION_FILE}. Повторите Шаг 1.")
        return None
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def is_stem(fn: str, track: str) -> bool:
    low, base = fn.lower(), os.path.splitext(fn.lower())[0]
    if os.path.splitext(low)[1] not in AUDIO_EXTENSIONS:     return False
    if "pdf" in low or any(k in low for k in IGNORE_KEYWORDS): return False
    return base.strip() != track.lower().strip()

def do_ffmpeg_convert(src: str, dst: str) -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", src, "-c:a", "pcm_s24be", "-ar", "48000", dst],
            check=True
        ); return True
    except Exception as e:
        print(f"FFmpeg error: {e}"); return False

def clean_stem_name(fname: str, track: str) -> str:
    base, _ = os.path.splitext(fname)
    tmp = re.sub(re.escape(track), "", base, flags=re.IGNORECASE)
    tmp = re.sub(r"(?i)\bstem\b|\b\d{2,3}\b", "", tmp)
    tmp = re.sub(r"[_,\-.]", " ", tmp).replace("&", "AND")
    tmp = re.sub(r"\s{2,}", " ", tmp)
    return tmp.strip().upper()

# ────────────────── диалог проверки ──────────────────
class StemsCheckDialog(QDialog):
    """Переименование/удаление стемов."""
    def __init__(self, track_key: str, stems: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Проверка стемов")
        self.corrected_stems: list[dict] = []

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"Трек: {track_key}\nКоличество стемов: {len(stems)}"))

        self.rows = []                           # (line_edit, stem_obj, del_btn)
        for st in stems:
            row = QHBoxLayout()
            le  = QLineEdit(st["stem"], self)
            btn = QPushButton("❌", clicked=lambda _=None, l=le, s=st, b=None: self._del(l, s, b))
            btn.setFixedWidth(30); btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            row.addWidget(le); row.addWidget(btn); lay.addLayout(row)
            self.rows.append((le, st, btn))

        ok = QPushButton("OK", clicked=self.on_ok)
        lay.addWidget(ok)

    def _del(self, le, st, _):
        if os.path.exists(st["old_path"]): os.remove(st["old_path"])
        st["__delete__"] = True; le.hide()

    def on_ok(self):
        for le, st, _ in self.rows:
            if not st.get("__delete__"):
                st["stem"] = le.text().strip()
                self.corrected_stems.append(st)
        self.accept()

# ───────────────────── основной виджет шага 2 ─────────────────────
class Step2ProcessStems(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.session_data: dict | None = None
        self.setLayout(self._ui())

    # ─── UI ───
    def _ui(self):
        lo = QVBoxLayout()
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)

        title = QLabel("ШАГ 2: СТЕМЫ", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        lo.addWidget(title)

        # лог
        self.log_output = QTextEdit(readOnly=True)
        lo.addWidget(self.log_output)

        # run‑кнопка
        self.run_btn = QPushButton("✅ Начать поиск стемов", clicked=self.run_step2)
        lo.addWidget(self.run_btn)

        # описание
        desc = QLabel(
            "Описание шага: программа находит стемы для каждого трека, конвертирует их "
            "в AIFF 24 bit/48 kHz и переносит их в альбом (_ALL ALBUMS AIFF), "
            "а также переименовывает их согласно стандарту.\n\n"
            "Ваша задача — проверить названия стемов (исправить опечатки) и убедиться, "
            "что лишние файлы не попали в список. Ненужные удаляйте кнопкой ❌. "
            "Хорошая практика — сверить количество стемов в _НЕГОТОВЫЕ и "
            "в _AIFF, чтобы убедиться, что ни один файл не потерялся.",
            wordWrap=True
        )
        desc.setStyleSheet("margin-top:8px;")
        lo.addWidget(desc)

        # навигация
        nav = QHBoxLayout()
        self.next_btn = QPushButton("➡ Следующий шаг", enabled=False,
                                    clicked=self.go_to_next_step)
        back_btn = QPushButton("⬅ Назад", clicked=self.go_back)
        nav.addWidget(self.next_btn); nav.addWidget(back_btn)
        lo.addLayout(nav)
        return lo

    def log(self, t: str): self.log_output.append(t)

    # ─── логика шага ───
    def run_step2(self):
        session = load_session()
        if not session:
            self.log("❌ Нет session.json"); return
        self.session_data = session

        album_code  = session.get("album_code", "IMG000")
        album_name  = session.get("album_name", "Unknown")
        album_path  = session.get("album_path_negotovoe", "")
        tracks_info = session.get("tracks", [])

        if not os.path.isdir(album_path):
            show_error("Ошибка", f"Не найдена папка альбома:\n{album_path}"); return

        self.log(f"🎵 {album_code} – {album_name}")
        stems_map, album_folders = {}, os.listdir(album_path)

        # поиск стемов
        for trk in tracks_info:
            tnum, tname = trk.get("track_number", "00"), trk.get("track_name", "Unknown")
            stems_folder = trk.get("stems_folder", "")
            track_key = f"{tnum} {tname}"

            real = next((x for x in album_folders if tname.lower() in x.lower()), None)
            if not real:
                self.log(f"⚠️ Нет папки для «{track_key}»"); stems_map[track_key] = []; continue
            cand = [os.path.join(album_path, real)]
            sub  = os.path.join(cand[0], "Stems");  cand.append(sub) if os.path.isdir(sub) else None

            processed, stems = set(), []
            for c in cand:
                for root, dirs, files in os.walk(c):
                    if "archive" in dirs: dirs.remove("archive")
                    for f in files:
                        if not is_stem(f, tname) or f in processed: continue
                        processed.add(f)

                        short  = clean_stem_name(f, tname)
                        prefix = f"{album_code} - {album_name} - {tnum} {tname} "
                        ext    = ".aiff"
                        src, dst = os.path.join(root, f), os.path.join(stems_folder, prefix+short+ext)

                        self.log(f"🔄 {f} → {os.path.basename(dst)}")
                        if do_ffmpeg_convert(src, dst):
                            stems.append({"old_path": dst, "prefix": prefix, "stem": short, "ext": ext})
            stems_map[track_key] = stems

        # диалоги проверки
        updated = {}
        for track_key, lst in stems_map.items():
            if not lst:
                QMessageBox.critical(self, "Ошибка", f"Нет стемов для «{track_key}»."); return
            dlg = StemsCheckDialog(track_key, lst, self)
            updated[track_key] = lst if dlg.exec() != QDialog.DialogCode.Accepted else dlg.corrected_stems

        # итоговое переименование
        for tr in tracks_info:
            key = f"{tr['track_number']} {tr['track_name']}"
            for st in updated.get(key, []):
                old = st["old_path"]
                new = os.path.join(os.path.dirname(old), st["prefix"]+st["stem"]+st["ext"])
                if new != old and os.path.exists(old):
                    try: os.rename(old, new); st["old_path"] = new
                    except Exception as e: self.log(f"⚠️ Ошибка переименования: {e}")
            tr["stems"] = [os.path.basename(s["old_path"]) for s in updated.get(key, [])]

        # сохранить сессию
        session["tracks"] = tracks_info
        with open(SESSION_FILE, "w", encoding="utf-8") as f: json.dump(session, f, indent=4)

        self.log("✅ Шаг 2 завершён!")
        self.next_btn.setEnabled(True)
        self.next_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold;")
        self.next_step_sound = QSoundEffect()
        self.next_step_sound.setSource(QUrl.fromLocalFile("notify.wav"))
        self.next_step_sound.setVolume(0.5)
        self.next_step_sound.play()

    # ─── навигация ───
    def go_to_next_step(self):
        from step3_composer_match import Step3ComposerMatch
        w = Step3ComposerMatch(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)

    def go_back(self):
        self.main_app.stack.setCurrentWidget(self.main_app.main_menu)
