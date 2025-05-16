# step5_generate_metadata.py
import os, json, shutil, subprocess
import pandas as pd, openpyxl

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QDateEdit, QMessageBox
)
from PyQt6.QtCore        import Qt, QDate, QUrl
from PyQt6.QtGui         import QDesktopServices
from PyQt6.QtMultimedia  import QSoundEffect


SESSION_FILE        = "session.json"
CONFIG_FILE         = "config.json"
DATABASES_FOLDER    = "_DATABASES"
COMPOSER_DB_FILE    = os.path.join(DATABASES_FOLDER, "composer_database.json")
ISRC_DB_FILE        = os.path.join(DATABASES_FOLDER, "isrc_database.json")
TOTAL_METADATA_FILE = "_IMAGINE MUSIC TOTAL METADATA.xlsx"


# ──────────────────────────────── ШАГ 5 ────────────────────────────────
class Step5GenerateMetadata(QWidget):
    """ШАГ 5 — формирование .xlsx-метаданных и синхронизация с TOTAL METADATA"""

    # ────────────────────── GUI ──────────────────────
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.setLayout(self._build_ui())
        self._load_data()                      # session / cfg / базы

    # ---------- интерфейс ----------
    def _build_ui(self) -> QVBoxLayout:
        root = QVBoxLayout(); root.setContentsMargins(0,0,0,0); root.setSpacing(8)

        # заголовок
        ttl = QLabel("ШАГ 5: МЕТАДАННЫЕ", alignment=Qt.AlignmentFlag.AlignCenter)
        ttl.setStyleSheet("font-size:22pt;font-weight:600;margin-bottom:8px;")
        root.addWidget(ttl)

        # поля альбома
        root.addWidget(QLabel("Альбом: дата релиза (YYYY-MM-DD)"))
        self.ed_date = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd",
                                 date=QDate.currentDate())
        root.addWidget(self.ed_date)

        root.addWidget(QLabel("Альбом: описание"))
        self.ed_desc = QTextEdit(); root.addWidget(self.ed_desc)

        root.addWidget(QLabel("Альбом: Styles"))
        self.ed_style = QLineEdit(); root.addWidget(self.ed_style)

        # таблица треков
        root.addWidget(QLabel("Заполните поля Description / Instrumentation / Keywords:"))
        self.tbl = QTableWidget(0,4)
        self.tbl.setHorizontalHeaderLabels(
            ["Track Name","Description","Instrumentation","Keywords"])
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        root.addWidget(self.tbl)

        # run-кнопка
        self.btn_run = QPushButton("✅ Сформировать метаданные",
                                   clicked=self._run, minimumHeight=32)
        root.addWidget(self.btn_run)

        # пояснение
        desc = QLabel(
            "Описание шага: программа собирает данные о треках, добавляет ISRC-коды, "
            "создаёт альбомный файл METADATA.xlsx.\n\n"
            "Ваша задача – заполнить поля выше и нажать «Сформировать метаданные». "
            "После проверки файла подтвердите добавление строк в общую таблицу "
            "TOTAL METADATA.",
            wordWrap=True
        )
        desc.setStyleSheet("margin-top:8px;")
        root.addWidget(desc)

        # навигация
        nav = QHBoxLayout()
        self.btn_next = QPushButton("➡ Следующий шаг", enabled=False,
                                    clicked=self._go_next)
        self.btn_back = QPushButton("⬅ Назад",
                                    clicked=lambda:
                                    self.main_app.stack.setCurrentWidget(
                                        self.main_app.main_menu))
        nav.addWidget(self.btn_next); nav.addWidget(self.btn_back)
        root.addLayout(nav)

        return root

    # ---------- загрузка данных ----------
    def _load_data(self):
        # session
        if not os.path.exists(SESSION_FILE):
            self._err("Нет session.json — повторите предыдущие шаги."); return
        with open(SESSION_FILE,"r",encoding="utf-8") as f:
            self.ses = json.load(f)

        # config
        if not os.path.exists(CONFIG_FILE):
            self._err("Нет config.json."); return
        with open(CONFIG_FILE,"r",encoding="utf-8") as f:
            cfg = json.load(f)
        self.meta_dir = cfg.get("_ALL ALBUMS METADATA","")
        if not os.path.isdir(self.meta_dir):
            self._err(f"Папка METADATA не найдена:\n{self.meta_dir}"); return

        # базы
        with open(COMPOSER_DB_FILE,"r",encoding="utf-8") as f:
            db = json.load(f)
        self.composers  = db.get("composers",{})
        self.publishers = db.get("publishers",{})

        self.isrc_db = {}
        if os.path.exists(ISRC_DB_FILE):
            with open(ISRC_DB_FILE,"r",encoding="utf-8") as f:
                self.isrc_db = json.load(f)
        self.last_isrc = self._find_last_isrc()

        # наполняем таблицу
        self.tracks = self.ses.get("tracks",[])
        self.tbl.setRowCount(len(self.tracks))
        for r,trk in enumerate(self.tracks):
            itm = QTableWidgetItem(trk.get("track_name",""))
            itm.setFlags(itm.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl.setItem(r,0,itm)
            for c in (1,2,3):
                self.tbl.setItem(r,c,QTableWidgetItem(""))

    # ---------- основной процесс ----------
    def _run(self):
        self._commit_table_edits()      # ← фиксация последнего ввода

        code,name,cover = (self.ses.get(k,"") for k in
                           ("album_code","album_name","cover_file"))
        day   = self.ed_date.date().toString("yyyy-MM-dd")
        desc  = self.ed_desc.toPlainText().strip()
        style = self.ed_style.text().strip()

        # сохраняем описание альбома в session.json
        self.ses["album_description"] = desc
        with open(SESSION_FILE,"w",encoding="utf-8") as f:
            json.dump(self.ses,f,indent=4)

        # читаем таблицу
        for r,trk in enumerate(self.tracks):
            trk["manual_description"]     = (self.tbl.item(r,1).text() or "").strip()
            trk["manual_instrumentation"] = (self.tbl.item(r,2).text() or "").strip()
            trk["manual_keywords"]        = (self.tbl.item(r,3).text() or "").strip()

        # общий набор ключевых слов альбома
        album_kw = sorted({kw.strip()
                           for t in self.tracks
                           for kw in t.get("manual_keywords","").split(",")
                           if kw.strip()})
        album_kw_str = ", ".join(album_kw)

        new_isrc = self._next_isrc(len(self.tracks))
        cols     = self._columns(); rows=[]

        for i,trk in enumerate(self.tracks):
            rd = {}
            # --- ALBUM ---
            rd.update({
                "LIBRARY: Name"        : self._lib_name(code),
                "ALBUM: Code"          : code,
                "ALBUM: Identity"      : "",
                "ALBUM: Title"         : name,
                "ALBUM: Display Title" : f"{code} {name}",
                "ALBUM: Description"   : desc,
                "ALBUM: Keywords"      : album_kw_str,
                "ALBUM: Tags"          : "",
                "ALBUM: Styles"        : style,
                "ALBUM: Release Date"  : day,
                "ALBUM: Artwork Filename": os.path.basename(cover)
            })
            # --- TRACK ---
            rd["TRACK: Title"]         = trk.get("track_name","")
            rd["TRACK: Display Title"] = trk.get("track_name","")
            rd["TRACK: Alternate Title"]= ""
            rd["TRACK: Description"]   = trk.get("manual_description","")
            rd["TRACK: Number"]        = str(i+1)              # 1,2,3…
            rd["TRACK: Is Main"]       = "Y"
            rd["TRACK: Main Track Number"]= ""
            rd["TRACK: Version"]       = "Main"
            rd["TRACK: Duration"]      = self._dur_mmss(trk.get("duration",0.0))
            rd["TRACK: BPM"]           = str(trk.get("track_bpm",""))
            rd["TRACK: Tempo"]         = self._tempo(trk.get("track_bpm",0))
            rd["TRACK: Genre"]         = "Trailer"
            rd["TRACK: Mixout"]        = ""
            rd["TRACK: Instrumentation"]= trk.get("manual_instrumentation","")
            rd["TRACK: Keywords"]      = trk.get("manual_keywords","")
            rd["TRACK: Lyrics"]        = ""
            rd["TRACK: Identity"]      = trk.get("track_name","")
            rd["TRACK: Category Codes"]= ""

            # writers / publishers
            writers,pubs = self._build_wp(trk.get("matched_composers",[]))
            rd["TRACK: Composer(s)"]  = " and ".join(self._full_name(w) for w in writers)
            rd["TRACK: Publisher(s)"] = " and ".join(sorted({w["publisher_name"]
                                                             for w in writers if w["publisher_name"]}))
            rd["TRACK: Artist(s)"]    = rd["TRACK: Composer(s)"]

            # --- Audio Filename (без расширения) ---
            audio_path   = trk.get("mastered_file","")          # полный путь
            base_name    = os.path.basename(audio_path)         # IMG001 - Album - 01 Track.aif
            audio_no_ext = os.path.splitext(base_name)[0]       # IMG001 - Album - 01 Track
            rd["TRACK: Audio Filename"] = audio_no_ext

            # пустой ARTIST:1
            for f in ("First Name","Middle Name","Last Name","Society","IPI"):
                rd[f"ARTIST:1: {f}"] = ""

            for n in (1,2,3): self._fill_writer(rd,writers[:3]+[None]*3,n)
            for n in (1,2):   self._fill_publisher(rd,pubs[:2],n)

            rd["CODE: ISWC"] = ""
            rd["CODE: ISRC"] = new_isrc[i]
            self.isrc_db[new_isrc[i]] = {
                "album_code":code,"album_title":name,
                "track_title":trk.get("track_name","")}

            rows.append([rd.get(c,"") for c in cols])

        # записываем isrc-базу
        with open(ISRC_DB_FILE,"w",encoding="utf-8") as f:
            json.dump(self.isrc_db,f,indent=4)

        # xlsx-файл альбома
        out = os.path.join(self.meta_dir,
                           f"{code.upper()} {name.upper()} METADATA.xlsx")
        if os.path.exists(out) and \
           QMessageBox.question(self,"Файл уже существует",
                                f"{os.path.basename(out)} уже есть. Заменить?",
                                QMessageBox.StandardButton.Yes|
                                QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) == \
           QMessageBox.StandardButton.No:
            return

        pd.DataFrame(rows,columns=cols).fillna("").to_excel(out,index=False)
        self._info("Файл METADATA.xlsx создан — проверьте его.")
        self._open(out)

        if QMessageBox.question(self,"Синхронизация",
                                "Добавить строки в TOTAL METADATA?",
                                QMessageBox.StandardButton.Yes|
                                QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) == \
           QMessageBox.StandardButton.Yes:
            self._sync_total(out,code)

    # ---------- фиксация последнего ввода ----------
    def _commit_table_edits(self):
        """
        Завершает редактирование активной ячейки, чтобы её содержимое
        гарантированно попало в QTableWidgetItem перед чтением.
        """
        editor = self.tbl.focusWidget()
        if editor is not None:
            editor.clearFocus()                 # отдаём фокус родителю
        self.tbl.setFocus(Qt.FocusReason.OtherFocusReason)
        QApplication.processEvents()            # завершить цикл событий

    # ---------- TOTAL METADATA ----------
    def _sync_total(self, meta_xlsx:str, album_code:str):
        sheet = "IMT" if album_code.startswith("IMT") else "IMG"
        total = os.path.join(self.meta_dir,TOTAL_METADATA_FILE)
        if not os.path.exists(total):
            self._err(f"Не найден {TOTAL_METADATA_FILE}"); return

        shutil.copy2(total,os.path.join(
            self.meta_dir,"_IMAGINE MUSIC TOTAL METADATA (backup).xlsx"))

        wb = openpyxl.load_workbook(total)
        if sheet not in wb.sheetnames:
            self._err(f"В таблице нет листа {sheet}"); return
        ws = wb[sheet]

        start = self._last_real_row(ws)+2      # ровно ОДНА пустая строка
        data  = pd.read_excel(meta_xlsx,dtype=str).fillna("").values.tolist()

        for r,row in enumerate(data,start):
            for c,val in enumerate(row,1):
                ws.cell(row=r,column=c,value=str(val))

        wb.save(total)

        self.btn_next.setEnabled(True)
        self.btn_next.setStyleSheet("background:#388E3C;color:white;font-weight:bold;")

        snd = QSoundEffect(self); snd.setSource(QUrl.fromLocalFile("notify.wav"))
        snd.setVolume(0.5); snd.play()

        self._info("Синхронизация выполнена (бэкап создан).")

    # ────────────────────── util helpers ──────────────────────
    def _find_last_isrc(self) -> str:
        codes = [k for k in self.isrc_db if k.startswith("RU-AD4-20-") and len(k) == 15]
        if not codes: return "RU-AD4-20-01000"
        return max(codes, key=lambda x: int(x[-5:]))

    def _next_isrc(self, n: int):
        base = self._find_last_isrc()[:-5]
        last = int(self._find_last_isrc()[-5:])
        return [f"{base}{last+i+1:05d}" for i in range(n)]

    def _lib_name(self, code: str) -> str:
        return "Imagine Music Tools" if code.startswith("IMT") else "Imagine Music"

    @staticmethod
    def _dur_mmss(sec: float) -> str:
        m, s = divmod(int(sec), 60)
        return f"{m}.{s:02d}"

    @staticmethod
    def _tempo(bpm) -> str:
        try: bpm = int(bpm)
        except: bpm = 0
        if bpm <= 70:  return "Slow"
        if bpm <= 90:  return "Downtempo"
        if bpm <= 115: return "Midtempo"
        if bpm <= 140: return "Uptempo"
        return "Fast"

    @staticmethod
    def _columns():
        # … список колонок без изменений …
        return [
            "LIBRARY: Name","ALBUM: Code","ALBUM: Identity","ALBUM: Title","ALBUM: Display Title",
            "ALBUM: Description","ALBUM: Keywords","ALBUM: Tags","ALBUM: Styles","ALBUM: Release Date",
            "ALBUM: Artwork Filename",
            "TRACK: Title","TRACK: Display Title","TRACK: Alternate Title","TRACK: Description",
            "TRACK: Number","TRACK: Is Main","TRACK: Main Track Number","TRACK: Version","TRACK: Duration",
            "TRACK: BPM","TRACK: Tempo","TRACK: Genre","TRACK: Mixout","TRACK: Instrumentation",
            "TRACK: Keywords","TRACK: Lyrics","TRACK: Identity","TRACK: Category Codes",
            "TRACK: Composer(s)","TRACK: Publisher(s)","TRACK: Artist(s)","TRACK: Audio Filename",
            "ARTIST:1: First Name","ARTIST:1: Middle Name","ARTIST:1: Last Name",
            "ARTIST:1: Society","ARTIST:1: IPI",
            "WRITER:1: First Name","WRITER:1: Middle Name","WRITER:1: Last Name",
            "WRITER:1: Capacity","WRITER:1: Society","WRITER:1: IPI","WRITER:1: Territory",
            "WRITER:1: Owner Performance Share %","WRITER:1: Owner Mechanical Share %","WRITER:1: Original Publisher",
            "WRITER:2: First Name","WRITER:2: Middle Name","WRITER:2: Last Name",
            "WRITER:2: Capacity","WRITER:2: Society","WRITER:2: IPI","WRITER:2: Territory",
            "WRITER:2: Owner Performance Share %","WRITER:2: Owner Mechanical Share %","WRITER:2: Original Publisher",
            "WRITER:3: First Name","WRITER:3: Middle Name","WRITER:3: Last Name",
            "WRITER:3: Capacity","WRITER:3: Society","WRITER:3: IPI","WRITER:3: Territory",
            "WRITER:3: Owner Performance Share %","WRITER:3: Owner Mechanical Share %","WRITER:3: Original Publisher",
            "PUBLISHER:1: Name","PUBLISHER:1: Capacity","PUBLISHER:1: Society","PUBLISHER:1: IPI",
            "PUBLISHER:1: Territory","PUBLISHER:1: Owner Performance Share %","PUBLISHER:1: Owner Mechanical Share %",
            "PUBLISHER:2: Name","PUBLISHER:2: Capacity","PUBLISHER:2: Society","PUBLISHER:2: IPI",
            "PUBLISHER:2: Territory","PUBLISHER:2: Owner Performance Share %","PUBLISHER:2: Owner Mechanical Share %",
            "CODE: ISWC","CODE: ISRC"
        ]

    # ---------- writer / publisher helpers ----------
    @staticmethod
    def _full_name(w):                 # first + middle + last
        return " ".join(p for p in (w["first_name"], w["middle_name"], w["last_name"]) if p).strip()

    def _build_wp(self, names):
        n = len(names)
        if n == 0: return [], []
        shares = ([100] if n == 1 else
                  [50, 50][:n] if n == 2 else
                  [34, 33, 33][:n] if n == 3 else
                  self._even_shares(n))

        writers, pubs = [], {}
        for share, nm in zip(shares, names):
            c = self.composers.get(nm, {})
            pub_key = c.get("publisher_key", "")
            p_info  = self.publishers.get(pub_key, {}) if pub_key else {}
            w = dict(
                first_name=c.get("first_name", ""), middle_name=c.get("middle_name", ""),
                last_name=c.get("last_name", ""),  capacity=c.get("capacity", "Composer/Author"),
                society=c.get("society", ""), ipi=c.get("ipi", ""),
                publisher_name = p_info.get("publisher_name", pub_key),
                owner_perf_share=str(share), owner_mech_share=str(share)
            )
            writers.append(w)

            if w["publisher_name"]:
                pubs.setdefault(w["publisher_name"], dict(
                    publisher_name = w["publisher_name"],
                    publisher_society = p_info.get("publisher_society", ""),
                    publisher_ipi = p_info.get("publisher_ipi", ""),
                    owner_perf_share = w["owner_perf_share"],
                    owner_mech_share = w["owner_mech_share"]
                ))
        return writers, list(pubs.values())

    @staticmethod
    def _even_shares(n):
        base, rem = divmod(100, n)
        return [base + (1 if i < rem else 0) for i in range(n)]

    def _fill_writer(self, rd, slots, idx):
        p = f"WRITER:{idx}"
        w = slots[idx-1]
        if not w:
            for fld in ("First Name","Middle Name","Last Name","Capacity","Society","IPI",
                        "Territory","Owner Performance Share %","Owner Mechanical Share %",
                        "Original Publisher"):
                rd[f"{p}: {fld}"] = ""; return
        rd[f"{p}: First Name"] = w["first_name"]
        rd[f"{p}: Middle Name"] = w["middle_name"]
        rd[f"{p}: Last Name"] = w["last_name"]
        rd[f"{p}: Capacity"] = w["capacity"]
        rd[f"{p}: Society"] = w["society"]
        rd[f"{p}: IPI"] = w["ipi"]
        rd[f"{p}: Territory"] = "WORLD"
        rd[f"{p}: Owner Performance Share %"] = w["owner_perf_share"]
        rd[f"{p}: Owner Mechanical Share %"] = w["owner_mech_share"]
        rd[f"{p}: Original Publisher"] = w["publisher_name"]

    def _fill_publisher(self, rd, pubs, idx):
        p = f"PUBLISHER:{idx}"
        if idx > len(pubs):
            for fld in ("Name","Capacity","Society","IPI","Territory",
                        "Owner Performance Share %","Owner Mechanical Share %"):
                rd[f"{p}: {fld}"] = ""; return
        pb = pubs[idx-1]
        rd[f"{p}: Name"]       = pb["publisher_name"]
        rd[f"{p}: Capacity"]   = "Original Publisher"
        rd[f"{p}: Society"]    = pb["publisher_society"]
        rd[f"{p}: IPI"]        = pb["publisher_ipi"]
        rd[f"{p}: Territory"]  = "WORLD"
        rd[f"{p}: Owner Performance Share %"] = pb["owner_perf_share"]
        rd[f"{p}: Owner Mechanical Share %"]  = pb["owner_mech_share"]

    # ---------- misc ----------
    @staticmethod
    def _last_real_row(ws):
        for row in range(ws.max_row, 0, -1):
            if any((cell.value not in ("", None)) for cell in ws[row]):
                return row
        return 1

    def _err(self, msg):
        QMessageBox.critical(self, "Ошибка", msg)

    def _info(self, msg):
        QMessageBox.information(self, "Информация", msg)

    def _open(self, path):
        if os.name == "posix":
            subprocess.run(["open", path], check=False)
        elif os.name == "nt":
            os.startfile(path)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    # ---------- переходы ----------
    def _go_next(self):
        from step_prepare_step6 import StepPrepareStep6
        w = StepPrepareStep6(self.main_app)
        self.main_app.stack.addWidget(w)
        self.main_app.stack.setCurrentWidget(w)
