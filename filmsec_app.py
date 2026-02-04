# FilmSec

import os
import re
import random
import json
import urllib.request
import urllib.parse
import sqlite3
import threading
import time
import io
import gzip
import base64
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Poster (afiş) için opsiyonel Pillow (JPEG yüklemek için gerekir)
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

APP_NAME = "FilmSec"



TMDB_API_KEY = "cff5f74900050a6f9acfe181d731a9c7"
# ================================
# PLATFORM + VERİ KLASÖRÜ
# ================================
def sys_platform() -> str:
    try:
        import sys
        return sys.platform
    except Exception:
        return "unknown"


def app_data_dir() -> str:
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys_platform() == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


DATA_DIR = app_data_dir()
LISTS_DIR = os.path.join(DATA_DIR, "lists")
os.makedirs(LISTS_DIR, exist_ok=True)

WATCHED_FILE = os.path.join(DATA_DIR, "watched_movies.txt")
LISTS_META_FILE = os.path.join(DATA_DIR, "lists.json")
MOVIE_RATINGS_FILE = os.path.join(DATA_DIR, "movie_ratings.json")
MOVIE_NOTES_FILE = os.path.join(DATA_DIR, "movie_notes.json")
WATCH_DATES_FILE = os.path.join(DATA_DIR, "watch_dates.json")
WATCH_HISTORY_FILE = os.path.join(DATA_DIR, "watch_history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
APP_DB_FILE = os.path.join(DATA_DIR, "filmsec.sqlite3")


POSTER_DB_FILE = os.path.join(DATA_DIR, "posters.sqlite3")


# ================================
# DOSYA OKU-YAZ
# ================================
def read_file(file_name: str) -> list[str]:
    if not os.path.exists(file_name):
        return []
    with open(file_name, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    lines.sort(key=str.lower)
    return lines


def write_file(file_name: str, data_list: list[str]) -> None:
    data_list = sorted(list(dict.fromkeys([x.strip() for x in data_list if x and x.strip()])), key=str.lower)
    with open(file_name, "w", encoding="utf-8") as f:
        for item in data_list:
            f.write(item + "\n")


def contains_ci(items: list[str], value: str) -> bool:
    v = value.strip().lower()
    return any(x.strip().lower() == v for x in items)


def remove_ci(items: list[str], value: str) -> list[str]:
    v = value.strip().lower()
    return [x for x in items if x.strip().lower() != v]


def normalize_movie(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()


# default listeler (sqlite seed)
DEFAULT_LIST_SEED_B64 = {
    "adnan_dvd": "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",
    "letterboxd_top": "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",
    "random_picks": "H4sIAG8kf2kC/31TTW8aQQy98yt8DJcKKCkhNz4EqZJNEBBFVdWDYQ3rsjuzmo8k9B/ld/SP1Tuzo6Y5VHuyx/Z7fs+7LQhWhqzjI8HFoNf70u1saEQKLvrj8WW381RwXaItmsf+sNv5qhwZ66gs0fzN7al2rFVI9LqdrUzdGl+hgk2hX8Ksq5heGlQ5TH2OtaDCjZZRac7KsNVKxofEZ2HCezSsQyhcJsbwM8Zy4TktMSdYeyUtDcTV4ENu0BuOQ/GopVSwOqbKSclxy9G4DWx4ksE3hC7tv+Bj4WBW+l3IjOOkR+uFx8bbmvbOptrmZU41Gkd5EvOhzHf6HCJZaMbuDPoASx0LhMemZsNNw+QFY10/KCGaWguZVvKdKEDIGt+0N3CPFX1KKqzQoJUBIW7p3YjGFXJOKlXNf6I6anhU+wJZRXp9Qb/XMNNeOXOGgzYgbCGLXT1By1BCfL2GhZeCtcY8WdGgPOny0CzzhKVo4QyRS8Yttc4PzY1EbdqTkK0P6Iro1mgQk5sCX2yB6gRryqlq70iahq2gaE5wq4INDS25o/4AJuoojLLo4GXrb4bO8Ot7n+60yRuKAgprMd9eQ5NeCDUtqFy/f0zi/6dxTc4blR5uU5NsvPJlDQvef6S/FFkUZFzSe14bicXgNOgOq11USuCnuD+B0+Fh4QUvdF6J6BlVpFz4HXqtpCtGxdalY5pUZOSfUTAl9HJqLeSk+v0mF/7PgvxMtsF/aAyx6VxnEii9O5ftOcH3jBXDnH/xjz/DsApNLAQAAA==",
}

DEFAULTS_DB_FILE = os.path.join(DATA_DIR, "defaults.sqlite3")


def _seed_decode(b64_text: str) -> list[str]:
    data = gzip.decompress(base64.b64decode(b64_text.encode("ascii"))).decode("utf-8")
    return [line.strip() for line in data.split("\n") if line.strip()]


def init_defaults_db() -> None:
    conn = sqlite3.connect(DEFAULTS_DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS default_movies (
            list_id TEXT NOT NULL,
            movie TEXT NOT NULL,
            movie_key TEXT NOT NULL,
            PRIMARY KEY (list_id, movie_key)
        )"""
    )
    cur.execute("SELECT COUNT(*) FROM default_movies")
    count = cur.fetchone()[0]
    if count == 0:
        for list_id, b64_text in DEFAULT_LIST_SEED_B64.items():
            movies = _seed_decode(b64_text)
            rows = [(list_id, m, normalize_movie(m)) for m in movies]
            cur.executemany(
                "INSERT OR IGNORE INTO default_movies (list_id, movie, movie_key) VALUES (?, ?, ?)",
                rows,
            )
        conn.commit()
    conn.close()


def get_default_movies(list_id: str) -> list[str]:
    conn = sqlite3.connect(DEFAULTS_DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT movie FROM default_movies WHERE list_id=? ORDER BY movie_key ASC",
        (list_id,),
    )
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


# ================================
# PUAN / NOT / TARİH / GEÇMİŞ (SQLite)
# ================================
def _app_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(APP_DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def _init_app_db() -> None:
    with _app_db_conn() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS ratings (movie_key TEXT PRIMARY KEY, rating REAL NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS notes (movie_key TEXT PRIMARY KEY, note TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS watch_history (movie_key TEXT PRIMARY KEY, list_id TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS watch_dates (movie_key TEXT NOT NULL, date TEXT NOT NULL, added_at INTEGER NOT NULL, PRIMARY KEY(movie_key, date))"
        )


def _table_has_rows(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
    return cur.fetchone() is not None


def _migrate_legacy_json_to_db() -> None:
    """Eski JSON dosyalarını (varsa) SQLite'a taşır. DB doluysa dokunmaz."""
    _init_app_db()
    with _app_db_conn() as conn:
        if (
            _table_has_rows(conn, "ratings")
            or _table_has_rows(conn, "notes")
            or _table_has_rows(conn, "watch_dates")
            or _table_has_rows(conn, "watch_history")
        ):
            return

        # ratings
        if os.path.exists(MOVIE_RATINGS_FILE):
            try:
                with open(MOVIE_RATINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        try:
                            rv = float(v)
                            if rv > 0:
                                conn.execute(
                                    "INSERT OR REPLACE INTO ratings(movie_key, rating) VALUES(?,?)",
                                    (k, rv),
                                )
                        except Exception:
                            pass
            except Exception:
                pass

        # notes
        if os.path.exists(MOVIE_NOTES_FILE):
            try:
                with open(MOVIE_NOTES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        if v is None:
                            continue
                        s = str(v).strip()
                        if s:
                            conn.execute(
                                "INSERT OR REPLACE INTO notes(movie_key, note) VALUES(?,?)",
                                (k, s),
                            )
            except Exception:
                pass

        # watch_dates
        if os.path.exists(WATCH_DATES_FILE):
            try:
                with open(WATCH_DATES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    now = int(time.time())
                    for k, dates in data.items():
                        if not isinstance(dates, list):
                            continue
                        t = now
                        for d in dates:
                            ds = str(d).strip()
                            if ds:
                                conn.execute(
                                    "INSERT OR REPLACE INTO watch_dates(movie_key, date, added_at) VALUES(?,?,?)",
                                    (k, ds, t),
                                )
                                t += 1
            except Exception:
                pass

        # watch_history
        if os.path.exists(WATCH_HISTORY_FILE):
            try:
                with open(WATCH_HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        if v is None:
                            continue
                        s = str(v).strip()
                        if s:
                            conn.execute(
                                "INSERT OR REPLACE INTO watch_history(movie_key, list_id) VALUES(?,?)",
                                (k, s),
                            )
            except Exception:
                pass


def load_ratings() -> dict:
    _migrate_legacy_json_to_db()
    with _app_db_conn() as conn:
        cur = conn.execute("SELECT movie_key, rating FROM ratings")
        return {k: float(v) for (k, v) in cur.fetchall()}


def save_ratings(ratings: dict) -> None:
    _init_app_db()
    with _app_db_conn() as conn:
        conn.execute("DELETE FROM ratings")
        for k, v in (ratings or {}).items():
            try:
                rv = float(v)
            except Exception:
                continue
            if rv > 0:
                conn.execute(
                    "INSERT OR REPLACE INTO ratings(movie_key, rating) VALUES(?,?)",
                    (k, rv),
                )


def load_notes() -> dict:
    _migrate_legacy_json_to_db()
    with _app_db_conn() as conn:
        cur = conn.execute("SELECT movie_key, note FROM notes")
        return {k: v for (k, v) in cur.fetchall()}


def save_notes(notes: dict) -> None:
    _init_app_db()
    with _app_db_conn() as conn:
        conn.execute("DELETE FROM notes")
        for k, v in (notes or {}).items():
            s = str(v).strip() if v is not None else ""
            if s:
                conn.execute(
                    "INSERT OR REPLACE INTO notes(movie_key, note) VALUES(?,?)",
                    (k, s),
                )


def load_watch_dates() -> dict:
    _migrate_legacy_json_to_db()
    with _app_db_conn() as conn:
        cur = conn.execute(
            "SELECT movie_key, date FROM watch_dates ORDER BY movie_key, added_at"
        )
        out: dict[str, list[str]] = {}
        for k, d in cur.fetchall():
            out.setdefault(k, []).append(d)
        return out


def save_watch_dates(dates: dict) -> None:
    _init_app_db()
    with _app_db_conn() as conn:
        conn.execute("DELETE FROM watch_dates")
        now = int(time.time())
        for k, lst in (dates or {}).items():
            if not isinstance(lst, list):
                continue
            t = now
            for d in lst:
                ds = str(d).strip()
                if ds:
                    conn.execute(
                        "INSERT OR REPLACE INTO watch_dates(movie_key, date, added_at) VALUES(?,?,?)",
                        (k, ds, t),
                    )
                    t += 1
            now = t + 1


def add_watch_date(movie: str, dates: dict) -> dict:
    from datetime import datetime

    movie_key = get_movie_key(movie)
    today = datetime.now().strftime("%d.%m.%Y")

    if movie_key not in dates:
        dates[movie_key] = []
    if today not in dates[movie_key]:
        dates[movie_key].append(today)
    return dates


def load_watch_history() -> dict:
    _migrate_legacy_json_to_db()
    with _app_db_conn() as conn:
        cur = conn.execute("SELECT movie_key, list_id FROM watch_history")
        return {k: v for (k, v) in cur.fetchall()}


def save_watch_history(history: dict) -> None:
    _init_app_db()
    with _app_db_conn() as conn:
        conn.execute("DELETE FROM watch_history")
        for k, v in (history or {}).items():
            s = str(v).strip() if v is not None else ""
            if s:
                conn.execute(
                    "INSERT OR REPLACE INTO watch_history(movie_key, list_id) VALUES(?,?)",
                    (k, s),
                )


def add_to_watch_history(movie: str, list_id: str, history: dict) -> dict:
    movie_key = get_movie_key(movie)
    history[movie_key] = list_id
    return history


def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return {"first_launch": True}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"first_launch": True}


def save_settings(settings: dict) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_movie_key(movie: str) -> str:
    return normalize_movie(movie)


# ================================
# 1) Adnan'ın DVD listesi (TAM)
# ================================

# ================================
# 2) Letterboxd Top 250 listesi
# ================================

# ================================
# 3) Rastgele Film Önerileri
# ================================


# ================================
# LİSTE METADATA (3 sabit liste)
# ================================
BUILTIN_LISTS = [
    {"id": "adnan_dvd", "name": "Adnan'ın DVD Listesi", "filename": "adnan_dvd.txt", "builtin": True},
    {"id": "letterboxd_top", "name": "Letterboxd Önerileri", "filename": "letterboxd_top.txt", "builtin": True},
    {"id": "random_picks", "name": "Rastgele Film Önerileri", "filename": "random_picks.txt", "builtin": True},
]


def load_lists_meta() -> dict:
    if not os.path.exists(LISTS_META_FILE):
        meta = {"lists": BUILTIN_LISTS, "selected": "adnan_dvd"}
        with open(LISTS_META_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return meta
    with open(LISTS_META_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_lists_meta(meta: dict) -> None:
    with open(LISTS_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def list_file_path(list_id: str, meta: dict) -> str:
    for it in meta["lists"]:
        if it["id"] == list_id:
            return os.path.join(LISTS_DIR, it["filename"])
    return os.path.join(LISTS_DIR, f"{list_id}.txt")


def ensure_builtin_lists(meta: dict) -> None:
    # Adnan'ın DVD listesi
    dvd_path = list_file_path("adnan_dvd", meta)
    if not os.path.exists(dvd_path) or not read_file(dvd_path):
        write_file(dvd_path, get_default_movies('adnan_dvd'))

    # Letterboxd önerileri
    letterboxd_path = list_file_path("letterboxd_top", meta)
    if not os.path.exists(letterboxd_path) or not read_file(letterboxd_path):
        write_file(letterboxd_path, get_default_movies('letterboxd_top'))

    # Rastgele film önerileri
    random_path = list_file_path("random_picks", meta)
    if not os.path.exists(random_path) or not read_file(random_path):
        write_file(random_path, get_default_movies('random_picks'))


def remove_movie_from_all_lists(meta: dict, movie: str) -> None:
    """Bir film izlenenlere atılınca tüm listelerden otomatik silinir."""
    for it in meta["lists"]:
        p = os.path.join(LISTS_DIR, it["filename"])
        items = read_file(p)
        new_items = remove_ci(items, movie)
        if len(new_items) != len(items):
            write_file(p, new_items)


# ================================
# UYGULAMA
# ================================
class FilmSecApp(tb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.current_theme = "darkly"

        self.meta = load_lists_meta()
        init_defaults_db()
        ensure_builtin_lists(self.meta)

        # Puan ve notları yükle
        self.ratings = load_ratings()
        self.notes = load_notes()
        self.watch_dates = load_watch_dates()
        self.watch_history = load_watch_history()
        self.settings = load_settings()

        self.title("FilmSec")
        self.geometry("1120x650")
        self.minsize(980, 560)

        # ---------- ÜST BAR ----------
        top = tb.Frame(self, padding=(16, 14))
        top.pack(fill=X)

        tb.Label(top, text="🎬 FilmSec", font=("Segoe UI", 18, "bold")).pack(side=LEFT)

        self.count_badge = tb.Label(
            top,
            text="Liste: 0 | İzlenen: 0",
            bootstyle="secondary",
            padding=(10, 6),
            font=("Segoe UI", 10, "bold"),
        )
        self.count_badge.pack(side=RIGHT)

        # ---------- ANA ALAN ----------
        content = tb.Frame(self, padding=(16, 10))
        content.pack(fill=BOTH, expand=True)

        left = tb.Frame(content)
        left.pack(side=LEFT, fill=BOTH, expand=True)

        right = tb.Frame(content)
        right.pack(side=RIGHT, fill=Y, padx=(14, 0))

        lists_area = tb.Frame(left)
        lists_area.pack(fill=BOTH, expand=True)

        # ✅ Ayarlanabilir alan: Liste ↔ İzlenenler (sürüklenebilir ayırıcı)
        self.splitter = tb.Panedwindow(lists_area, orient=HORIZONTAL)
        self.splitter.pack(fill=BOTH, expand=True)

        # Sol panel: Liste
        pool_container = tb.Frame(self.splitter)
        self.pool_card = tb.Labelframe(pool_container, text="Liste", padding=12, bootstyle="info")
        self.pool_card.pack(fill=BOTH, expand=True)

        # Sağ panel: İzlenenler
        watched_container = tb.Frame(self.splitter)
        self.watched_card = tb.Labelframe(watched_container, text="İzlenenler", padding=12, bootstyle="warning")
        self.watched_card.pack(fill=BOTH, expand=True)

        # PanedWindow içine ekle (başlangıç oranı)
        self.splitter.add(pool_container, weight=1)
        self.splitter.add(watched_container, weight=1)

        # Aşağıdaki eski değişken adıyla devam edilsin
        watched_card = self.watched_card

        # --- Liste seçim barı ---
        bar = tb.Frame(self.pool_card)
        bar.pack(fill=X, pady=(0, 10))

        tb.Label(bar, text="Liste:", font=("Segoe UI", 10, "bold")).pack(side=LEFT)

        self.list_names = [it["name"] for it in self.meta["lists"]]
        self.list_id_by_name = {it["name"]: it["id"] for it in self.meta["lists"]}

        current_id = self.meta.get("selected", "adnan_dvd")
        current_name = next((it["name"] for it in self.meta["lists"] if it["id"] == current_id), self.meta["lists"][0]["name"])

        self.selected_list_var = tk.StringVar(value=current_name)
        self.list_combo = tb.Combobox(
            bar,
            textvariable=self.selected_list_var,
            values=self.list_names,
            state="readonly",
            width=26,
        )
        self.list_combo.pack(side=LEFT, padx=(8, 10))
        self.list_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change_list())

        tb.Button(bar, text="➕", bootstyle="success-outline", command=self.add_new_list, width=3).pack(side=LEFT, padx=(0, 5))
        tb.Button(bar, text="🗑", bootstyle="danger-outline", command=self.remove_current_list, width=3).pack(side=LEFT, padx=(0, 10))

        tb.Button(bar, text="❓ Yardım", bootstyle="secondary-outline", command=self.show_help, width=10).pack(side=RIGHT)

        # --- Liste + (sağında) Afiş önizleme (ayarlanabilir) ---
        self.pool_pane = tb.Panedwindow(self.pool_card, orient=HORIZONTAL)
        self.pool_pane.pack(fill=BOTH, expand=True)

        # Sol: film listesi
        pool_wrap = tb.Frame(self.pool_pane)
        pool_scroll = tb.Scrollbar(pool_wrap, orient=VERTICAL)
        pool_scroll.pack(side=RIGHT, fill=Y)

        self.pool_list = tk.Listbox(
            pool_wrap,
            font=("Segoe UI", 10),
            activestyle="none",
            highlightthickness=0,
            selectborderwidth=0,
        )
        self.pool_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.pool_list.config(yscrollcommand=pool_scroll.set)
        pool_scroll.config(command=self.pool_list.yview)

        # Sağ: afiş alanı
        poster_wrap = tb.Frame(self.pool_pane)
        poster_card = tb.Labelframe(poster_wrap, text="Afiş", padding=10, bootstyle="secondary")
        poster_card.pack(fill=BOTH, expand=True)

        self.poster_title_var = tk.StringVar(value="")
        tb.Label(
            poster_card,
            textvariable=self.poster_title_var,
            font=("Segoe UI", 9, "bold"),
            wraplength=240,
            justify=LEFT,
        ).pack(anchor=W, pady=(0, 6))

        self.poster_img_label = tb.Label(
            poster_card,
            text="🎬 Bir film seç",
            bootstyle="secondary",
            anchor=CENTER,
            padding=6,
        )
        self.poster_img_label.pack(fill=BOTH, expand=True)

        self.poster_preview_win = None
        self.poster_preview_imgtk = None
        self.poster_img_label.bind("<ButtonPress-1>", self._poster_hold_start)
        self.poster_img_label.bind("<ButtonRelease-1>", self._poster_hold_end)
        self.poster_img_label.bind("<B1-Motion>", self._poster_hold_move)
        self.poster_img_label.bind("<Leave>", self._poster_hold_end)

        self.poster_photo = None
        self.current_poster_path = None

        tb.Label(
            poster_card,
            text="Afişi büyütmek için basılı tut",
            bootstyle="secondary",
            font=("Segoe UI", 9),
        ).pack(fill=X, pady=(8, 0))

        # Panedwindow'a ekle (başlangıçta dengeli)
        self.pool_pane.add(pool_wrap, weight=3)
        self.pool_pane.add(poster_wrap, weight=2)

        # --- İzlenen listbox + scrollbar ---
        watched_wrap = tb.Frame(watched_card)
        watched_wrap.pack(fill=BOTH, expand=True)

        watched_scroll = tb.Scrollbar(watched_wrap, orient=VERTICAL)
        watched_scroll.pack(side=RIGHT, fill=Y)

        self.watched_list = tk.Listbox(
            watched_wrap,
            font=("Segoe UI", 10),
            activestyle="none",
            highlightthickness=0,
            selectborderwidth=0,
        )
        self.watched_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.watched_list.config(yscrollcommand=watched_scroll.set)
        watched_scroll.config(command=self.watched_list.yview)

        # ---------- INFO ----------
        self.info = tb.Label(
            left,
            text="Hazır. Bir işlem seç 🙂",
            bootstyle="secondary",
            padding=(12, 10),
            font=("Segoe UI", 11),
            anchor=W,
        )
        self.info.pack(fill=X, pady=(12, 0))

        # ---------- SAĞ PANEL ----------
                
        panel = tb.Labelframe(right, text="Kontroller", padding=12, bootstyle="secondary")
        panel.pack(fill=Y, expand=True)

        btn = {"width": 26, "padding": (8, 6)}

        btn_wrap = tb.Frame(panel)
        btn_wrap.pack(fill=BOTH, expand=True)

        tb.Button(btn_wrap, text="🎲 Rastgele Seç", command=self.pick_movie_popup, bootstyle="success", **btn).pack(fill=X, pady=(0, 6))
        tb.Button(btn_wrap, text="➕ Film Ekle", command=self.add_movie, bootstyle="primary", **btn).pack(fill=X, pady=(0, 6))
        tb.Button(btn_wrap, text="🔍 Film Ara", command=self.search_movie, bootstyle="info", **btn).pack(fill=X, pady=(0, 6))
        tb.Button(btn_wrap, text="↔ Liste ⇄ İzlenenlere Taşı", command=self.toggle_move_selected, bootstyle="warning", **btn).pack(fill=X, pady=(0, 6))
        tb.Button(btn_wrap, text="🗑 Seçileni Kaldır", command=self.delete_selected_anywhere, bootstyle="danger", **btn).pack(fill=X, pady=(0, 6))
        tb.Button(btn_wrap, text="📂 Veri Klasörünü Aç", command=self.open_data_dir, bootstyle="secondary", **btn).pack(fill=X, pady=(0, 6))
        tb.Button(btn_wrap, text="🌓 Mod Değiştir (Light/Dark)", command=self.toggle_theme, bootstyle="secondary", **btn).pack(fill=X)

        # Çıkış butonu her zaman altta görünsün
        tb.Button(panel, text="❌ Çıkış", command=self.destroy, bootstyle="secondary-outline", **btn).pack(side=BOTTOM, fill=X, pady=(10, 0))
# ---------- EVENTLER ----------
        self.pool_list.bind("<<ListboxSelect>>", lambda e: self._on_select("pool"))
        self.watched_list.bind("<<ListboxSelect>>", lambda e: self._on_select("watched"))

        self.pool_list.bind("<Double-Button-1>", lambda e: self._on_double_click("pool"))
        self.watched_list.bind("<Double-Button-1>", lambda e: self._on_double_click("watched"))

        # Sürükle-bırak eventleri
        self.pool_list.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, "pool"))
        self.pool_list.bind("<B1-Motion>", self._on_drag_motion)
        self.pool_list.bind("<ButtonRelease-1>", lambda e: self._on_drag_drop(e, "pool"))
        
        self.watched_list.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, "watched"))
        self.watched_list.bind("<B1-Motion>", self._on_drag_motion)
        self.watched_list.bind("<ButtonRelease-1>", lambda e: self._on_drag_drop(e, "watched"))
        
        self.drag_data = {"item": None, "source": None, "x": 0, "y": 0}
        
        # Sürükleme görseli için label
        self.drag_label = None

        self.apply_listbox_theme()
        self.refresh_lists()

        self.poster_mem_cache = {}
        self.poster_prefetch_gen = 0
        self.poster_prefetching = False
        self.current_poster_bytes = None
        self._poster_db_init()
        self._start_poster_prefetch_for_current_list()


        # Başlangıçta ayırıcıyı makul bir oranla konumlandır (Liste biraz daha geniş)
        try:
            self.after(150, lambda: self.splitter.sashpos(0, int(self.winfo_width() * 0.5)))
        except Exception:
            pass

        
        # İlk açılış popup'ı kaldırıldı: bunun yerine küçük bir ipucu göster
        if self.settings.get("first_launch", True):
            self.settings["first_launch"] = False
            save_settings(self.settings)

        self._set_info("💡 İpucu: Filmlere puan ve not vermek için çift tıklayın!", "info")
        self.after(5000, lambda: self._set_info("Hazır. Bir işlem seç 🙂", "secondary"))

    # ================================
    # Yardım
    # ================================
    def show_help(self):
        text = (
            "🎬 FilmSec - Kısa Kullanım\n\n"
            "• Üstteki menüden hangi film listesini görmek istediğini seç.\n"
            "• 🎲 Rastgele Seç: Bir film önerir. 'Evet' dersen izlenenlere taşır ve tüm listelerden düşer.\n"
            "• ➕ Film Ekle: Film adını yaz, hangi listeye ekleneceğini seç.\n"
            "• 🔍 Film Ara: Seçili listede veya izlenenlerde arar.\n"
            "• ↔ Taşı: Seçili filmi Liste ⇄ İzlenenler arasında taşır.\n"
            "• 🗑 Kaldır: Seçili filmi bulunduğu yerden siler.\n\n"
            "⭐ Puan & Not\n"
            "• Filme çift tıkla: Puan (0-10) ve not penceresi açılır.\n"
            "• Puanlar 0.5 adım: 0, 0.5, 1, 1.5 ... 10\n"
            "• Yıldızlara tıklayarak da puan verebilirsin.\n\n"
            "🖼️ Afişler (TMDb)\n"
            "• Film seçince afiş otomatik bulunur (TMDb).\n"
            "• Afişin üstüne sol tık basılı tutarak büyük önizleme görebilirsin.\n\n"

            "↔ Ayarlanabilir Paneller\\n"
            "• Liste ve İzlenenler arasındaki çizgiyi sürükleyerek genişlikleri ayarlayabilirsin.\n\n"
            "Listeler:\n"
            "- Adnan'ın DVD Listesi\n"
            "- Letterboxd Önerileri\n"
            "- Rastgele Film Önerileri\n"
        )
        messagebox.showinfo("Yardım", text)

    def _set_info(self, text: str, style: str = "secondary"):
        self.info.configure(text=text, bootstyle=style)


    def _center_window(self, win: tk.Toplevel):
        """Pencereyi ekranın ortasına al."""
        try:
            win.update_idletasks()
            w = win.winfo_width() or win.winfo_reqwidth()
            h = win.winfo_height() or win.winfo_reqheight()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = max(0, int((sw - w) / 2))
            y = max(0, int((sh - h) / 2))
            win.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass


    def current_list_id(self) -> str:
        name = self.selected_list_var.get().strip()
        return self.list_id_by_name.get(name, "adnan_dvd")

    def current_list_path(self) -> str:
        return list_file_path(self.current_list_id(), self.meta)

    def _update_counts(self):
        pool = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)
        pool_visible = [m for m in pool if not contains_ci(watched, m)]
        self.count_badge.configure(text=f"Liste: {len(pool_visible)} | İzlenen: {len(watched)}")

        self.pool_card.configure(text=f"Liste: {self.selected_list_var.get()}")

    def refresh_lists(self):
        pool = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)

        pool = [m for m in pool if not contains_ci(watched, m)]
        pool.sort(key=str.lower)

        self.pool_list.delete(0, tk.END)
        for m in pool:
            display_text = self._format_movie_display(m)
            self.pool_list.insert(tk.END, display_text)

        self.watched_list.delete(0, tk.END)
        for m in watched:
            display_text = self._format_movie_display(m)
            self.watched_list.insert(tk.END, display_text)

        self._update_counts()

    def _format_movie_display(self, movie: str) -> str:
        """Film adını puan, izlenme tarihi ve not ikonlarıyla formatla"""
        movie_key = get_movie_key(movie)
        display = movie
        
        # Puan varsa ekle
        if movie_key in self.ratings:
            rating = self.ratings[movie_key]
            display += f" ⭐ {rating}"
        
        # İzlenme tarihi varsa ekle (sadece son izlenme)
        if movie_key in self.watch_dates and self.watch_dates[movie_key]:
            last_watch = self.watch_dates[movie_key][-1]
            display += f" 📅 {last_watch}"
        
        # Not varsa ikon ekle
        if movie_key in self.notes and self.notes[movie_key].strip():
            display += " 📝"
        
        return display

    def on_change_list(self):
        self.meta["selected"] = self.current_list_id()
        save_lists_meta(self.meta)
        self.refresh_lists()
        self._start_poster_prefetch_for_current_list()
        self._set_info(f"📁 Liste seçildi: {self.selected_list_var.get()}", "info")

    # ================================
    # Sürükle-Bırak İşlemleri
    # ================================
    def _on_drag_start(self, event, source):
        """Sürükleme başladığında"""
        widget = event.widget
        index = widget.nearest(event.y)
        
        if index >= 0 and index < widget.size():
            self.drag_data["item"] = widget.get(index)
            self.drag_data["source"] = source
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)
            
            # Görsel sürükleme elemanı oluştur
            self._create_drag_label(event)

    def _create_drag_label(self, event):
        """Sürükleme sırasında gösterilecek label oluştur"""
        if self.drag_label:
            self.drag_label.destroy()
        
        # Film adını kısalt (çok uzunsa)
        movie_text = self.drag_data["item"]
        if len(movie_text) > 50:
            movie_text = movie_text[:47] + "..."
        
        # Toplevel pencere oluştur (üstte kalması için)
        self.drag_label = tk.Toplevel(self)
        self.drag_label.wm_overrideredirect(True)  # Başlık çubuğu yok
        self.drag_label.wm_attributes("-alpha", 0.8)  # Yarı saydam
        self.drag_label.wm_attributes("-topmost", True)  # Her zaman üstte
        
        # Label içeriği
        label = tb.Label(
            self.drag_label,
            text=f"🎬 {movie_text}",
            bootstyle="info",
            padding=10,
            font=("Segoe UI", 10, "bold")
        )
        label.pack()
        
        # Pozisyonu ayarla
        self.drag_label.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def _on_drag_motion(self, event):
        """Sürüklerken - label'ı hareket ettir"""
        if self.drag_label and self.drag_data["item"]:
            self.drag_label.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def _on_drag_drop(self, event, source):
        """Bırakıldığında"""
        # Sürükleme label'ını kaldır
        if self.drag_label:
            self.drag_label.destroy()
            self.drag_label = None
        
        if not self.drag_data["item"] or not self.drag_data["source"]:
            return
        
        # Fare pozisyonunu kontrol et - karşı listeye bırakıldı mı?
        drop_target = None
        
        # Pool list'in konumunu al
        pool_x = self.pool_list.winfo_rootx()
        pool_y = self.pool_list.winfo_rooty()
        pool_w = self.pool_list.winfo_width()
        pool_h = self.pool_list.winfo_height()
        
        # Watched list'in konumunu al
        watched_x = self.watched_list.winfo_rootx()
        watched_y = self.watched_list.winfo_rooty()
        watched_w = self.watched_list.winfo_width()
        watched_h = self.watched_list.winfo_height()
        
        # Fare pozisyonu (root koordinatları)
        mouse_x = event.x_root
        mouse_y = event.y_root
        
        # Hangi liste üzerine bırakıldı kontrol et
        if pool_x <= mouse_x <= pool_x + pool_w and pool_y <= mouse_y <= pool_y + pool_h:
            drop_target = "pool"
        elif watched_x <= mouse_x <= watched_x + watched_w and watched_y <= mouse_y <= watched_y + watched_h:
            drop_target = "watched"
        
        # Farklı listeye bırakıldıysa taşı
        if drop_target and drop_target != self.drag_data["source"]:
            movie = self.drag_data["item"]
            original_movie = self._extract_original_movie_name(movie)
            
            watched = read_file(WATCHED_FILE)
            
            if self.drag_data["source"] == "pool" and drop_target == "watched":
                # Havuzdan izlenenlere taşı
                if not contains_ci(watched, original_movie):
                    watched.append(original_movie)
                    write_file(WATCHED_FILE, watched)
                    
                    # İzlenme tarihini kaydet
                    self.watch_dates = add_watch_date(original_movie, self.watch_dates)
                    save_watch_dates(self.watch_dates)
                    
                    # Hangi listeden eklendiğini kaydet
                    current_list_id = self.current_list_id()
                    self.watch_history = add_to_watch_history(original_movie, current_list_id, self.watch_history)
                    save_watch_history(self.watch_history)
                
                remove_movie_from_all_lists(self.meta, original_movie)
                self.refresh_lists()
                self._set_info(f"✅ '{original_movie}' izlenenlere taşındı", "success")
                
            elif self.drag_data["source"] == "watched" and drop_target == "pool":
                # İzlenenlerden havuza taşı
                watched = remove_ci(watched, original_movie)
                write_file(WATCHED_FILE, watched)
                
                p = self.current_list_path()
                items = read_file(p)
                if not contains_ci(items, original_movie):
                    items.append(original_movie)
                    write_file(p, items)
                
                self.refresh_lists()
                self._set_info(f"↩ '{original_movie}' seçili listeye geri eklendi", "info")
        
        # Drag data'yı temizle
        self.drag_data = {"item": None, "source": None, "x": 0, "y": 0}

    def _on_select(self, which: str):
        if which == "pool":
            if self.pool_list.curselection():
                self.watched_list.selection_clear(0, tk.END)
        else:
            if self.watched_list.curselection():
                self.pool_list.selection_clear(0, tk.END)
        # Seçili filme göre afişi güncelle
        self.update_poster_from_selection()


    def _on_double_click(self, which: str):
        movie = self._get_selected(which)
        if movie:
            # Formatlanmış metinden asıl film adını çıkar
            original_movie = self._extract_original_movie_name(movie)
            self.open_rating_note_popup(original_movie)

    def _get_selected(self, which: str):
        lb = self.pool_list if which == "pool" else self.watched_list
        sel = lb.curselection()
        if not sel:
            return None
        return lb.get(sel[0])

    def _get_selected_anywhere(self):
        movie_pool = self._get_selected("pool")
        if movie_pool:
            return "pool", movie_pool
        movie_watched = self._get_selected("watched")
        if movie_watched:
            return "watched", movie_watched
        return None, None

    
    def update_poster_from_selection(self):
        """Hangi listede seçim varsa o filme göre afişi güncelle."""
        which, movie = self._get_selected_anywhere()
        if not which or not movie:
            # seçim yoksa temizle
            self.poster_title_var.set("")
            self.poster_img_label.configure(image="", text="🎬 Bir film seç")
            self.poster_photo = None
            return

        original_movie = self._extract_original_movie_name(movie)
        self.update_poster_preview(original_movie)

    def _extract_original_movie_name(self, display_text: str) -> str:
        """Formatlanmış metinden orijinal film adını çıkar

        Not: Listbox'ta film adının sonuna şu eklentiler gelebiliyor:
        - ' ⭐ <puan>'
        - ' 📅 <tarih>'
        - ' 📝'
        Bu fonksiyon her durumda saf film adını döndürür.
        """
        clean = display_text
        # Sıralama önemli değil; hangi ek önce geldiyse oradan kırp.
        for marker in (" ⭐", " 📅", " 📝"):
            if marker in clean:
                clean = clean.split(marker)[0]
        return clean.strip()

    # ================================
    # Puan ve Not Popup
    # ================================
    def open_rating_note_popup(self, movie: str):
        """Film için puan ve not girişi popup'ı aç"""
        movie_key = get_movie_key(movie)
        
        popup = tb.Toplevel(self)
        popup.title("⭐ Puan & Not")
        popup.geometry("650x620")
        popup.minsize(620, 560)
        popup.transient(self)
        popup.grab_set()
        self._center_window(popup)

        # Başlık
        header = tb.Frame(popup, bootstyle="info", padding=15)
        header.pack(fill=X)
        
        tb.Label(
            header,
            text=movie,
            font=("Segoe UI", 13, "bold"),
            bootstyle="inverse-info",
            wraplength=500
        ).pack()

        content = tb.Frame(popup, padding=20)
        content.pack(fill=BOTH, expand=True)

        # PUAN KISMI
        rating_frame = tb.Labelframe(content, text="⭐ Puan (0-10)", padding=15, bootstyle="warning")
        rating_frame.pack(fill=X, pady=(0, 15))

        current_rating = self.ratings.get(movie_key, 0.0)
        # Eski kayıtlarda 0.5 dışı değerler olabilir; burada 0.5'e sabitle
        try:
            current_rating = round(float(current_rating) * 2) / 2
        except Exception:
            current_rating = 0.0

        rating_var = tk.DoubleVar(value=current_rating)
        rating_label_var = tk.StringVar(value=f"{current_rating:.1f}")

        def snap_to_half(val: float) -> float:
            """Puanı 0.5 adımlara sabitle."""
            try:
                v = float(val)
            except Exception:
                v = 0.0
            # 0.5 adım
            return round(v * 2) / 2

        def update_rating_label(val):
            snapped = snap_to_half(val)
            # ttk Scale bazen ara değerler üretir; burada 0.5'e kilitle
            if abs(rating_var.get() - snapped) > 1e-9:
                rating_var.set(snapped)
            rating_label_var.set(f"{snapped:.1f}")

        # Slider
        slider = tb.Scale(
            rating_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=rating_var,
            command=update_rating_label,
            bootstyle="warning"
        )
        slider.pack(fill=X, pady=(0, 10))

        # Puan göstergesi
        rating_display = tb.Label(
            rating_frame,
            textvariable=rating_label_var,
            font=("Segoe UI", 24, "bold"),
            bootstyle="warning"
        )
        rating_display.pack()

        # Yıldız gösterimi
        stars_label = tb.Label(
            rating_frame,
            text="",
            font=("Segoe UI", 20),
            cursor="hand2",
        )
        stars_label.pack(pady=(6, 0))
        def update_stars(*args):
            val = snap_to_half(rating_var.get())
            if abs(rating_var.get() - val) > 1e-9:
                rating_var.set(val)
        
            full_stars = int(val)
            half_star = 1 if (val - full_stars) >= 0.5 else 0
            empty_stars = 10 - full_stars - half_star
        
            # Daha net görünüm: dolu ★, yarım ⯨, boş ☆
            stars = "★" * full_stars
            if half_star:
                stars += "⯨"  # yarım yıldız
            stars += "☆" * empty_stars
        
            stars_label.config(text=stars)

        rating_var.trace_add("write", update_stars)
        update_stars()

        def set_rating_by_click(event):
            """Yıldızların üstüne tıklayarak puan ver (0.5 adım)."""
            w = stars_label.winfo_width()
            if w <= 0:
                return
            x = max(0, min(event.x, w))
            ratio = x / w
            raw = ratio * 10  # 0-10
            snapped = snap_to_half(raw)
            rating_var.set(snapped)
            rating_label_var.set(f"{snapped:.1f}")

        stars_label.bind("<Button-1>", set_rating_by_click)

        # NOT KISMI
        note_frame = tb.Labelframe(content, text="📝 Not / Yorum", padding=15, bootstyle="info")
        note_frame.pack(fill=BOTH, expand=True, pady=(0, 15))

        # İzlenme tarihleri varsa göster
        if movie_key in self.watch_dates and self.watch_dates[movie_key]:
            dates_text = ", ".join(self.watch_dates[movie_key])
            tb.Label(
                note_frame,
                text=f"📅 İzlenme: {dates_text}",
                font=("Segoe UI", 9),
                bootstyle="success",
                wraplength=450
            ).pack(anchor=W, pady=(0, 8))

        current_note = self.notes.get(movie_key, "")

        note_scroll = tb.Scrollbar(note_frame)
        note_scroll.pack(side=RIGHT, fill=Y)

        note_text = tk.Text(
            note_frame,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            height=6,
            yscrollcommand=note_scroll.set
        )
        note_text.pack(side=LEFT, fill=BOTH, expand=True)
        note_scroll.config(command=note_text.yview)

        if current_note:
            note_text.insert("1.0", current_note)

        # BUTONLAR
        btn_frame = tb.Frame(popup, padding=10)
        btn_frame.pack(fill=X)

        def move_to_watched():
            watched = read_file(WATCHED_FILE)
            if contains_ci(watched, movie):
                self._set_info(f"ℹ️ '{movie}' zaten izlenenlerde.", "info")
                popup.destroy()
                self.refresh_lists()
                return

            watched.append(movie)
            write_file(WATCHED_FILE, watched)

            # İzlenme tarihini kaydet
            self.watch_dates = add_watch_date(movie, self.watch_dates)
            save_watch_dates(self.watch_dates)

            # Hangi listeden eklendiğini kaydet
            current_list_id = self.current_list_id()
            self.watch_history = add_to_watch_history(movie, current_list_id, self.watch_history)
            save_watch_history(self.watch_history)

            remove_movie_from_all_lists(self.meta, movie)

            popup.destroy()
            self.refresh_lists()
            self._set_info(f"✅ '{movie}' izlenenlere taşındı", "success")


        def save_data():
            # Puanı kaydet
            new_rating = snap_to_half(rating_var.get())
            if new_rating > 0:
                self.ratings[movie_key] = new_rating
            elif movie_key in self.ratings:
                del self.ratings[movie_key]
            
            save_ratings(self.ratings)

            # Notu kaydet
            new_note = note_text.get("1.0", tk.END).strip()
            if new_note:
                self.notes[movie_key] = new_note
            elif movie_key in self.notes:
                del self.notes[movie_key]
            
            save_notes(self.notes)

            popup.destroy()
            self.refresh_lists()
            
            if new_rating > 0 or new_note:
                self._set_info(f"✅ '{movie}' için puan ve not kaydedildi!", "success")
            else:
                self._set_info(f"ℹ️ '{movie}' için veriler temizlendi", "info")

        def clear_data():
            if messagebox.askyesno("Onay", "Bu film için tüm puan ve notları silmek istiyor musunuz?"):
                if movie_key in self.ratings:
                    del self.ratings[movie_key]
                    save_ratings(self.ratings)
                
                if movie_key in self.notes:
                    del self.notes[movie_key]
                    save_notes(self.notes)
                
                popup.destroy()
                self.refresh_lists()
                self._set_info(f"🗑 '{movie}' için tüm veriler silindi", "warning")

        tb.Button(
            btn_frame,
            text="✅ İzlenenlere Taşı",
            bootstyle="warning",
            command=move_to_watched,
            width=18
        ).pack(side=LEFT, padx=5)

        tb.Button(
            btn_frame,
            text="💾 Kaydet",
            bootstyle="success",
            command=save_data,
            width=15
        ).pack(side=LEFT, padx=5)

        tb.Button(
            btn_frame,
            text="❌ İptal",
            bootstyle="secondary",
            command=popup.destroy,
            width=15
        ).pack(side=LEFT, padx=5)

        tb.Button(
            btn_frame,
            text="🗑 Temizle",
            bootstyle="danger",
            command=clear_data,
            width=15
        ).pack(side=LEFT, padx=5)

    def _select_movie_in_pool(self, movie: str):
        try:
            self.pool_list.selection_clear(0, tk.END)
            self.watched_list.selection_clear(0, tk.END)

            pool_now = read_file(self.current_list_path())
            watched = read_file(WATCHED_FILE)
            pool_now = [m for m in pool_now if not contains_ci(watched, m)]

            for i, m in enumerate(pool_now):
                if normalize_movie(m) == normalize_movie(movie):
                    self.pool_list.selection_set(i)
                    self.pool_list.see(i)
                    break
        except Exception:
            pass

    # ================================
    # Light/Dark Toggle + Listbox tema
    # ================================
    def toggle_theme(self):
        self.current_theme = "darkly" if self.current_theme == "flatly" else "flatly"
        self.style.theme_use(self.current_theme)
        self.apply_listbox_theme()
        self.refresh_lists()
        self._set_info(f"🌓 Mod değişti: {self.current_theme}", "secondary")

    def apply_listbox_theme(self):
        if self.current_theme == "darkly":
            bg = "#1f2328"
            fg = "#ffffff"
            selbg = "#3b82f6"
        else:
            bg = "#ffffff"
            fg = "#111827"
            selbg = "#93c5fd"

        self.pool_list.config(bg=bg, fg=fg, selectbackground=selbg, selectforeground=fg)
        self.watched_list.config(bg=bg, fg=fg, selectbackground=selbg, selectforeground=fg)

    # ================================
    # Rastgele Seçim (popup)
    # ================================
    def pick_movie_popup(self):
        pool_all = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)
        pool = [m for m in pool_all if not contains_ci(watched, m)]

        if not pool:
            self._set_info("Bu listede izlenmemiş film kalmamış 🙂", "warning")
            messagebox.showinfo("Bilgi", "Bu listede izlenmemiş film kalmamış.")
            return

        movie = random.choice(pool)
        answer = messagebox.askyesno("Film Önerisi", f"🎲 Tavsiye: {movie}\n\nŞimdi izleyecek misin?")
        if answer:
            watched = read_file(WATCHED_FILE)
            if not contains_ci(watched, movie):
                watched.append(movie)
                write_file(WATCHED_FILE, watched)
                
                # İzlenme tarihini kaydet
                self.watch_dates = add_watch_date(movie, self.watch_dates)
                save_watch_dates(self.watch_dates)
                
                # Hangi listeden eklendiğini kaydet
                current_list_id = self.current_list_id()
                self.watch_history = add_to_watch_history(movie, current_list_id, self.watch_history)
                save_watch_history(self.watch_history)

            remove_movie_from_all_lists(self.meta, movie)

            self.refresh_lists()
            self._set_info(f"✅ '{movie}' izlenenlere aktarıldı. İyi seyirler! 🍿", "success")
        else:
            self._set_info(f"🙂 Tamamdır. Tavsiye: {movie} (Listede kaldı)", "secondary")
            self._select_movie_in_pool(movie)

    # ================================
    # Film Ekle (hangi listeye?)
    # ================================
    def add_movie(self):
        new_movie = simpledialog.askstring("Film Ekle", "Eklemek istediğiniz filmin adını yazın:")
        if not new_movie:
            return
        new_movie = new_movie.strip()
        if not new_movie:
            return

        watched = read_file(WATCHED_FILE)
        if contains_ci(watched, new_movie):
            messagebox.showinfo("Bilgi", "Bu film izlenenlerde var. Listeye eklemeye gerek yok 🙂")
            return

        list_choice = tb.Toplevel(self)
        list_choice.title("Liste Seç")
        list_choice.geometry("360x220")
        list_choice.transient(self)
        list_choice.grab_set()

        tb.Label(list_choice, text="Bu filmi hangi listeye ekleyelim?", padding=(10, 10)).pack()

        var = tk.StringVar(value=self.selected_list_var.get())
        cb = tb.Combobox(list_choice, values=self.list_names, textvariable=var, state="readonly", width=28)
        cb.pack(pady=8)

        def do_add():
            target_name = var.get()
            target_id = self.list_id_by_name.get(target_name)
            if not target_id:
                return

            for it in self.meta["lists"]:
                p = os.path.join(LISTS_DIR, it["filename"])
                items = read_file(p)
                if contains_ci(items, new_movie):
                    messagebox.showinfo("Bilgi", f"Bu film zaten '{it['name']}' listesinde var.")
                    list_choice.destroy()
                    return

            p = list_file_path(target_id, self.meta)
            items = read_file(p)
            items.append(new_movie)
            write_file(p, items)

            self.refresh_lists()
            self._set_info(f"➕ '{new_movie}' eklendi: {target_name}", "success")
            list_choice.destroy()

        tb.Button(list_choice, text="Ekle", bootstyle="success", command=do_add, width=10).pack(pady=(12, 6))
        tb.Button(list_choice, text="İptal", bootstyle="secondary", command=list_choice.destroy, width=10).pack()

    # ================================
    # Film Ara
    # ================================
    def search_movie(self):
        query = simpledialog.askstring("Film Ara", "Aramak istediğiniz kelime/film adı:")
        if not query:
            return
        q = query.strip().lower()
        if not q:
            return

        pool_all = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)

        pool_results = [m for m in pool_all if q in m.lower() and not contains_ci(watched, m)]
        watched_results = [m for m in watched if q in m.lower()]

        if not pool_results and not watched_results:
            messagebox.showinfo("Arama Sonuçları", "Sonuç bulunamadı.")
            return

        win = tb.Toplevel(self)
        win.title("Arama Sonuçları")
        win.geometry("580x440")
        win.transient(self)
        win.grab_set()

        tb.Label(win, text="Bir filme çift tıkla: ana listede seçili olsun.", padding=(10, 10)).pack()

        container = tb.Frame(win, padding=10)
        container.pack(fill=BOTH, expand=True)

        lf_pool = tb.Labelframe(container, text=f"Seçili Liste: {self.selected_list_var.get()}", padding=10, bootstyle="info")
        lf_pool.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        lb_pool = tk.Listbox(lf_pool, font=("Segoe UI", 10), activestyle="none", highlightthickness=0)
        lb_pool.pack(fill=BOTH, expand=True)
        for m in pool_results:
            lb_pool.insert(tk.END, m)

        lf_w = tb.Labelframe(container, text="İzlenenler", padding=10, bootstyle="warning")
        lf_w.pack(side=LEFT, fill=BOTH, expand=True)

        lb_w = tk.Listbox(lf_w, font=("Segoe UI", 10), activestyle="none", highlightthickness=0)
        lb_w.pack(fill=BOTH, expand=True)
        for m in watched_results:
            lb_w.insert(tk.END, m)

        def select_in_main(which: str, movie: str):
            if which == "pool":
                self.watched_list.selection_clear(0, tk.END)
                self.pool_list.selection_clear(0, tk.END)

                pool_visible = [m for m in read_file(self.current_list_path()) if not contains_ci(read_file(WATCHED_FILE), m)]
                for i, mm in enumerate(pool_visible):
                    if normalize_movie(mm) == normalize_movie(movie):
                        self.pool_list.selection_set(i)
                        self.pool_list.see(i)
                        break

                self._set_info(f"🔍 Listede bulundu: {movie}", "info")
            else:
                self.pool_list.selection_clear(0, tk.END)
                self.watched_list.selection_clear(0, tk.END)

                all_w = read_file(WATCHED_FILE)
                for i, mm in enumerate(all_w):
                    if normalize_movie(mm) == normalize_movie(movie):
                        self.watched_list.selection_set(i)
                        self.watched_list.see(i)
                        break

                self._set_info(f"🔍 İzlenenlerde bulundu: {movie}", "warning")

            win.destroy()

        lb_pool.bind("<Double-Button-1>", lambda e: (lb_pool.curselection() and select_in_main("pool", lb_pool.get(lb_pool.curselection()[0]))))
        lb_w.bind("<Double-Button-1>", lambda e: (lb_w.curselection() and select_in_main("watched", lb_w.get(lb_w.curselection()[0]))))

        tb.Button(win, text="Kapat", bootstyle="secondary", command=win.destroy, width=12).pack(pady=(0, 12))

    # ================================
    # Seçili filmi liste ⇄ izlenen arasında taşı
    # ================================
    def toggle_move_selected(self):
        which, movie = self._get_selected_anywhere()
        if not which or not movie:
            messagebox.showwarning("Uyarı", "Taşımak için listeden veya izlenenlerden bir film seç.")
            return

        watched = read_file(WATCHED_FILE)

        if which == "pool":
            # Orijinal film adını çıkar
            original_movie = self._extract_original_movie_name(movie)
            
            if not contains_ci(watched, original_movie):
                watched.append(original_movie)
                write_file(WATCHED_FILE, watched)
                
                # İzlenme tarihini kaydet
                self.watch_dates = add_watch_date(original_movie, self.watch_dates)
                save_watch_dates(self.watch_dates)
                
                # Hangi listeden eklendiğini kaydet
                current_list_id = self.current_list_id()
                self.watch_history = add_to_watch_history(original_movie, current_list_id, self.watch_history)
                save_watch_history(self.watch_history)

            remove_movie_from_all_lists(self.meta, original_movie)

            self.refresh_lists()
            self._set_info(f"✅ '{original_movie}' izlenenlere taşındı ve tüm listelerden çıkarıldı.", "success")
        else:
            # Orijinal film adını çıkar (⭐, 📅, 📝 ekleri olmadan)
            original_movie = self._extract_original_movie_name(movie)
            movie_key = get_movie_key(original_movie)

            # Bu film izlenenlere hangi listeden eklenmişti?
            target_list_id = self.watch_history.get(movie_key)

            # İzlenenlerden kaldır (büyük/küçük harf ve boşluk duyarsız)
            watched = read_file(WATCHED_FILE)
            target_norm = normalize_movie(original_movie)
            watched_cleaned = [m for m in watched if normalize_movie(m) != target_norm]
            write_file(WATCHED_FILE, watched_cleaned)

            # Orijinal listeye (biliniyorsa) ya da seçili listeye geri ekle
            if target_list_id:
                target_path = list_file_path(target_list_id, self.meta)
                if os.path.exists(target_path):
                    items = read_file(target_path)
                    if not contains_ci(items, original_movie):
                        items.append(original_movie)
                        write_file(target_path, items)

                    target_list_name = next((it["name"] for it in self.meta["lists"] if it["id"] == target_list_id), "bilinmeyen liste")
                    self.refresh_lists()
                    self._set_info(f"↩ '{original_movie}' izlenenlerden çıkarıldı ve '{target_list_name}' listesine geri eklendi.", "info")
                    return

            # Geçmiş yoksa / liste yoksa şu anki listeye ekle
            p = self.current_list_path()
            items = read_file(p)
            if not contains_ci(items, original_movie):
                items.append(original_movie)
                write_file(p, items)

            self.refresh_lists()
            self._set_info(f"↩ '{original_movie}' izlenenlerden çıkarıldı ve seçili listeye geri eklendi.", "info")


    # ================================
    # Liste Ekleme
    # ================================
    def add_new_list(self):
        choice_win = tb.Toplevel(self)
        choice_win.title("Yeni Liste Ekle")
        choice_win.geometry("400x260")
        choice_win.transient(self)
        choice_win.grab_set()

        tb.Label(
            choice_win, 
            text="Yeni liste nasıl oluşturulsun?", 
            font=("Segoe UI", 12, "bold"),
            padding=(10, 15)
        ).pack()

        btn_frame = tb.Frame(choice_win, padding=20)
        btn_frame.pack(fill=BOTH, expand=True)

        def file_upload():
            choice_win.destroy()
            self._add_list_from_file()

        def manual_create():
            choice_win.destroy()
            self._add_list_manually()

        tb.Button(
            btn_frame,
            text="📁 Dosya Yükle",
            bootstyle="primary",
            command=file_upload,
            width=25,
            padding=(12, 12)
        ).pack(pady=(0, 15))

        tb.Label(
            btn_frame,
            text="TXT dosyası yükleyin.\nHer satırda 1 film olmalı.",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(pady=(0, 20))

        tb.Button(
            btn_frame,
            text="✍ Manuel Liste Oluştur",
            bootstyle="info",
            command=manual_create,
            width=25,
            padding=(12, 12)
        ).pack(pady=(0, 15))

        tb.Label(
            btn_frame,
            text="Her satıra 1 film yazın.",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack()

    def _add_list_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Film Listesi Dosyası Seçin",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                movies = [line.strip() for line in f.readlines() if line.strip()]
            
            if not movies:
                messagebox.showwarning("Uyarı", "Dosya boş veya geçersiz!")
                return

            list_name = simpledialog.askstring(
                "Liste Adı",
                f"Bu liste için bir isim girin:\n({len(movies)} film yüklendi)"
            )
            
            if not list_name or not list_name.strip():
                return

            list_name = list_name.strip()

            # Liste ID'si oluştur
            list_id = re.sub(r'[^a-z0-9_]', '_', list_name.lower())
            list_id = re.sub(r'_+', '_', list_id).strip('_')
            
            # Aynı isimde liste var mı kontrol et
            if any(it["name"].lower() == list_name.lower() for it in self.meta["lists"]):
                messagebox.showwarning("Uyarı", "Bu isimde bir liste zaten var!")
                return

            # Yeni listeyi ekle
            new_list = {
                "id": list_id,
                "name": list_name,
                "filename": f"{list_id}.txt",
                "builtin": False
            }
            
            self.meta["lists"].append(new_list)
            save_lists_meta(self.meta)

            # Dosyayı kaydet
            list_path = list_file_path(list_id, self.meta)
            write_file(list_path, movies)

            # UI'ı güncelle
            self.list_names = [it["name"] for it in self.meta["lists"]]
            self.list_id_by_name = {it["name"]: it["id"] for it in self.meta["lists"]}
            self.list_combo.configure(values=self.list_names)
            self.selected_list_var.set(list_name)
            self.meta["selected"] = list_id
            save_lists_meta(self.meta)

            self.refresh_lists()
            self._set_info(f"✅ '{list_name}' listesi eklendi ({len(movies)} film)", "success")

        except Exception as e:
            messagebox.showerror("Hata", f"Dosya yüklenirken hata oluştu:\n{e}")

    def _add_list_manually(self):
        manual_win = tb.Toplevel(self)
        manual_win.title("Manuel Liste Oluştur")
        manual_win.geometry("600x550")
        manual_win.transient(self)
        manual_win.grab_set()

        tb.Label(
            manual_win,
            text="Her satıra 1 film yazın:",
            font=("Segoe UI", 11, "bold"),
            padding=(10, 10)
        ).pack()

        text_frame = tb.Frame(manual_win, padding=10)
        text_frame.pack(fill=BOTH, expand=True)

        scroll = tb.Scrollbar(text_frame)
        scroll.pack(side=RIGHT, fill=Y)

        text_widget = tk.Text(
            text_frame,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            yscrollcommand=scroll.set
        )
        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.config(command=text_widget.yview)

        text_widget.insert("1.0", "Örnek:\nThe Matrix (1999)\nInception (2010)\nInterstellar (2014)")

        def save_manual_list():
            content = text_widget.get("1.0", tk.END)
            movies = [line.strip() for line in content.split("\n") if line.strip()]
            
            if not movies:
                messagebox.showwarning("Uyarı", "En az bir film girmelisiniz!")
                return

            list_name = simpledialog.askstring(
                "Liste Adı",
                f"Bu liste için bir isim girin:\n({len(movies)} film)"
            )
            
            if not list_name or not list_name.strip():
                return

            list_name = list_name.strip()

            # Liste ID'si oluştur
            list_id = re.sub(r'[^a-z0-9_]', '_', list_name.lower())
            list_id = re.sub(r'_+', '_', list_id).strip('_')
            
            # Aynı isimde liste var mı kontrol et
            if any(it["name"].lower() == list_name.lower() for it in self.meta["lists"]):
                messagebox.showwarning("Uyarı", "Bu isimde bir liste zaten var!")
                return

            # Yeni listeyi ekle
            new_list = {
                "id": list_id,
                "name": list_name,
                "filename": f"{list_id}.txt",
                "builtin": False
            }
            
            self.meta["lists"].append(new_list)
            save_lists_meta(self.meta)

            # Dosyayı kaydet
            list_path = list_file_path(list_id, self.meta)
            write_file(list_path, movies)

            # UI'ı güncelle
            self.list_names = [it["name"] for it in self.meta["lists"]]
            self.list_id_by_name = {it["name"]: it["id"] for it in self.meta["lists"]}
            self.list_combo.configure(values=self.list_names)
            self.selected_list_var.set(list_name)
            self.meta["selected"] = list_id
            save_lists_meta(self.meta)

            manual_win.destroy()
            self.refresh_lists()
            self._set_info(f"✅ '{list_name}' listesi oluşturuldu ({len(movies)} film)", "success")

        button_frame = tb.Frame(manual_win, padding=10)
        button_frame.pack(fill=X)

        tb.Button(
            button_frame,
            text="Listeyi Kaydet",
            bootstyle="success",
            command=save_manual_list,
            width=15
        ).pack(side=LEFT, padx=(0, 10))

        tb.Button(
            button_frame,
            text="İptal",
            bootstyle="secondary",
            command=manual_win.destroy,
            width=15
        ).pack(side=LEFT)

    # ================================
    # Listeyi Kaldır
    # ================================
    def remove_current_list(self):
        current_id = self.current_list_id()
        current_name = self.selected_list_var.get()

        # Sabit listeleri kaldırmaya izin verme
        current_list_obj = next((it for it in self.meta["lists"] if it["id"] == current_id), None)
        if current_list_obj and current_list_obj.get("builtin", False):
            messagebox.showwarning("Uyarı", "Varsayılan listeler kaldırılamaz!")
            return

        # En az bir liste kalmalı
        if len(self.meta["lists"]) <= 1:
            messagebox.showwarning("Uyarı", "En az bir liste olmalı!")
            return

        # Onay iste
        answer = messagebox.askyesno(
            "Onay",
            f"'{current_name}' listesi kalıcı olarak silinecek.\n\nEmin misiniz?"
        )
        
        if not answer:
            return

        # Liste dosyasını sil
        list_path = self.current_list_path()
        if os.path.exists(list_path):
            try:
                os.remove(list_path)
            except Exception as e:
                messagebox.showerror("Hata", f"Liste dosyası silinirken hata oluştu:\n{e}")
                return

        # Metadata'dan kaldır
        self.meta["lists"] = [it for it in self.meta["lists"] if it["id"] != current_id]
        
        # İlk listeyi seç
        if self.meta["lists"]:
            self.meta["selected"] = self.meta["lists"][0]["id"]
        
        save_lists_meta(self.meta)

        # UI'ı güncelle
        self.list_names = [it["name"] for it in self.meta["lists"]]
        self.list_id_by_name = {it["name"]: it["id"] for it in self.meta["lists"]}
        self.list_combo.configure(values=self.list_names)
        
        if self.meta["lists"]:
            self.selected_list_var.set(self.meta["lists"][0]["name"])
        
        self.refresh_lists()
        self._set_info(f"🗑 '{current_name}' listesi kaldırıldı", "danger")

    # ================================
    # Seçileni kaldır (bulunduğu yerden)
    # ================================
    def delete_selected_anywhere(self):
        which, movie = self._get_selected_anywhere()
        if not which or not movie:
            messagebox.showwarning("Uyarı", "Kaldırmak için listeden veya izlenenlerden bir film seç.")
            return

        # Orijinal film adını çıkar (⭐, 📅, 📝 ikonları olmadan)
        original_movie = self._extract_original_movie_name(movie)

        if which == "pool":
            if not messagebox.askyesno("Onay", f"'{original_movie}' listeden tamamen silinsin mi?"):
                return
            
            p = self.current_list_path()
            items = read_file(p)
            items = remove_ci(items, original_movie)
            write_file(p, items)
            self.refresh_lists()
            self._set_info(f"🗑 '{original_movie}' seçili listeden kaldırıldı.", "danger")
        else:
            # İzlenenlerden kaldırma - orijinal listeye geri dön
            movie_key = get_movie_key(original_movie)
            target_list_id = self.watch_history.get(movie_key)
            
            if target_list_id:
                target_list_name = next((it["name"] for it in self.meta["lists"] if it["id"] == target_list_id), "bilinmeyen liste")
                answer = messagebox.askyesno(
                    "İzlenenlerden Çıkar",
                    f"'{original_movie}' izlenenlerden çıkarılsın ve '{target_list_name}' listesine geri eklensin mi?"
                )
            else:
                answer = messagebox.askyesno(
                    "İzlenenlerden Çıkar",
                    f"'{original_movie}' izlenenlerden çıkarılsın ve seçili listeye geri eklensin mi?"
                )
            
            if not answer:
                return
            
            # DOĞRUDAN dosya okuma
            target_normalized = normalize_movie(original_movie)
            
            with open(WATCHED_FILE, "r", encoding="utf-8") as f:
                all_lines = [line.strip() for line in f.readlines() if line.strip()]
            
            print(f"🔍 ÖNCE: {len(all_lines)} film var")
            
            # Filmi temizle
            cleaned_lines = []
            for line in all_lines:
                if normalize_movie(line) != target_normalized:
                    cleaned_lines.append(line)
            
            print(f"🔍 SONRA: {len(cleaned_lines)} film kaldı")
            print(f"🔍 Silindi mi? {len(all_lines) - len(cleaned_lines) > 0}")
            
            # DOĞRUDAN dosya yazma
            with open(WATCHED_FILE, "w", encoding="utf-8") as f:
                for line in cleaned_lines:
                    f.write(line + "\n")
            
            # TÜM verileri temizle (puan, not, izlenme tarihi, geçmiş)
            if movie_key in self.watch_dates:
                del self.watch_dates[movie_key]
                save_watch_dates(self.watch_dates)
            
            if movie_key in self.ratings:
                del self.ratings[movie_key]
                save_ratings(self.ratings)
            
            if movie_key in self.notes:
                del self.notes[movie_key]
                save_notes(self.notes)
            
            if movie_key in self.watch_history:
                del self.watch_history[movie_key]
                save_watch_history(self.watch_history)
            
            # Önbellekleri yeniden yükle (refresh_lists bunları kullanacak)
            self.watch_dates = load_watch_dates()
            self.ratings = load_ratings()
            self.notes = load_notes()
            self.watch_history = load_watch_history()
            
            # FORCE: Dosyayı tekrar oku ve kontrol et
            final_watched = read_file(WATCHED_FILE)
            print(f"🔍 DEBUG: İzlenenler listesi: {len(final_watched)} film")
            print(f"🔍 DEBUG: '{original_movie}' listede var mı? {any(normalize_movie(m) == normalize_movie(original_movie) for m in final_watched)}")
            
            # Orijinal listeye veya şu anki listeye geri ekle
            if target_list_id:
                target_path = list_file_path(target_list_id, self.meta)
                if os.path.exists(target_path):
                    items = read_file(target_path)
                    if not contains_ci(items, original_movie):
                        items.append(original_movie)
                        write_file(target_path, items)
                    target_list_name = next((it["name"] for it in self.meta["lists"] if it["id"] == target_list_id), "bilinmeyen liste")
                    self.refresh_lists()
                    self._set_info(f"↩ '{original_movie}' izlenenlerden çıkarıldı ve '{target_list_name}' listesine geri eklendi.", "info")
                    return
            
            # Liste bulunamazsa şu anki listeye ekle
            p = self.current_list_path()
            items = read_file(p)
            if not contains_ci(items, original_movie):
                items.append(original_movie)
                write_file(p, items)
            
            self.refresh_lists()
            self._set_info(f"↩ '{original_movie}' izlenenlerden çıkarıldı ve seçili listeye geri eklendi.", "info")

    
    # ================================
    # Poster (Afiş) - TMDb (otomatik)
    # ================================
    
    def _tmdb_key(self) -> str:
        return ((self.settings.get("tmdb_api_key") or "").strip() or TMDB_API_KEY)

    
    def _poster_db_init(self):
        try:
            with sqlite3.connect(POSTER_DB_FILE, timeout=30) as con:
                con.execute(
                    """
                    CREATE TABLE IF NOT EXISTS posters (
                        movie_key TEXT PRIMARY KEY,
                        img BLOB NOT NULL,
                        updated_at INTEGER NOT NULL
                    )
                    """
                )
                con.commit()
        except Exception:
            pass

    def _poster_db_get(self, movie_key: str) -> bytes | None:
        try:
            with sqlite3.connect(POSTER_DB_FILE, timeout=30) as con:
                cur = con.execute("SELECT img FROM posters WHERE movie_key = ?", (movie_key,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception:
            return None

    def _poster_db_set(self, movie_key: str, img_bytes: bytes) -> None:
        try:
            ts = int(time.time())
            with sqlite3.connect(POSTER_DB_FILE, timeout=30) as con:
                con.execute(
                    "INSERT OR REPLACE INTO posters (movie_key, img, updated_at) VALUES (?, ?, ?)",
                    (movie_key, sqlite3.Binary(img_bytes), ts),
                )
                con.commit()
        except Exception:
            pass

    def _parse_title_year(self, movie: str):
        s = movie.strip()
        m = re.match(r"^(.*)\((\d{4})\)\s*$", s)
        if m:
            return m.group(1).strip(), m.group(2)
        return s, None

    def _tmdb_search(self, title: str, year: str | None):
        key = self._tmdb_key()
        if not key:
            return None

        params = {
            "api_key": key,
            "query": title,
            "include_adult": "false",
            "language": "tr-TR",
        }
        if year:
            params["year"] = year

        url = "https://api.themoviedb.org/3/search/movie?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FilmSec/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read().decode("utf-8"))
            results = data.get("results") or []
            if not results:
                return None
            return results[0]
        except Exception:
            return None

    def _download_poster_bytes(self, movie: str) -> bytes | None:
        key = self._tmdb_key()
        if not key:
            return None

        title, year = self._parse_title_year(movie)
        result = self._tmdb_search(title, year)
        if not result:
            return None

        poster_path = result.get("poster_path")
        if not poster_path:
            return None

        img_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

        try:
            req = urllib.request.Request(img_url, headers={"User-Agent": "FilmSec/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read()
        except Exception:
            return None

    def _get_poster_bytes(self, movie: str) -> bytes | None:
        movie = (movie or "").strip()
        if not movie:
            return None

        movie_key = get_movie_key(movie)

        # RAM cache
        b = self.poster_mem_cache.get(movie_key)
        if b:
            return b

        # DB cache
        b = self._poster_db_get(movie_key)
        if b:
            self.poster_mem_cache[movie_key] = b
            return b

        return None

    def _ensure_poster_cached(self, movie: str) -> bool:
        movie = (movie or "").strip()
        if not movie:
            return False

        movie_key = get_movie_key(movie)
        if self._get_poster_bytes(movie):
            return True

        b = self._download_poster_bytes(movie)
        if not b:
            return False

        self._poster_db_set(movie_key, b)
        self.poster_mem_cache[movie_key] = b
        return True

    def _start_poster_prefetch_for_current_list(self):
        key = self._tmdb_key()
        if not key:
            return

        movies = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)
        movies = [m for m in movies if not contains_ci(watched, m)]

        if not movies:
            return

        # yeni bir jenerasyon başlat
        self.poster_prefetch_gen += 1
        gen = self.poster_prefetch_gen

        self.poster_prefetching = True
        self.poster_img_label.configure(image="", text="⏳ Listeniz hazırlanıyor...\nLütfen bekleyin.")
        self._set_info("⏳ Listeniz hazırlanıyor, lütfen bekleyin…", "info")

        def worker():
            for mv in movies:
                # iptal edildi mi?
                if gen != self.poster_prefetch_gen:
                    break
                try:
                    # zaten varsa geç
                    if self._get_poster_bytes(mv):
                        continue
                    self._ensure_poster_cached(mv)
                    time.sleep(0.05)
                except Exception:
                    pass

            def done():
                if gen != self.poster_prefetch_gen:
                    return
                self.poster_prefetching = False
                # Seçili film varsa afişi çiz
                try:
                    sel = self._get_selected("pool") or self._get_selected("watched")
                    if sel:
                        self.update_poster_preview(self._extract_original_movie_name(sel))
                    else:
                        self.poster_img_label.configure(image="", text="🎬 Bir film seç")
                except Exception:
                    pass
                self._set_info("✅ Liste hazır.", "success")

            try:
                self.after(0, done)
            except Exception:
                pass

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _request_poster_for_movie_async(self, movie: str):
        movie = (movie or "").strip()
        if not movie:
            return

        movie_key = get_movie_key(movie)

        def worker():
            ok = self._ensure_poster_cached(movie)

            def done():
                # halen aynı film seçiliyken güncelle
                cur = (self.poster_title_var.get() or "").strip()
                if normalize_movie(cur) != normalize_movie(movie):
                    return
                if ok:
                    self.update_poster_preview(movie)
                else:
                    self.poster_img_label.configure(image="", text="Afiş bulunamadı")

            try:
                self.after(0, done)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def update_poster_preview(self, movie: str):
        movie = (movie or "").strip()
        self.poster_title_var.set(movie)

        if not movie:
            self.poster_img_label.configure(image="", text="🎬 Bir film seç")
            self.poster_photo = None
            self.current_poster_bytes = None
            return

        if Image is None or ImageTk is None:
            self.poster_img_label.configure(image="", text="(Afiş için Pillow gerekli)\npython -m pip install pillow")
            self.poster_photo = None
            self.current_poster_bytes = None
            return

        key = self._tmdb_key()
        if not key:
            self.poster_img_label.configure(image="", text="TMDb anahtarı yok")
            self.poster_photo = None
            self.current_poster_bytes = None
            return

        b = self._get_poster_bytes(movie)
        if not b:
            # list hazırlanırken tıklayınca UI donmasın
            self.poster_img_label.configure(image="", text="⏳ Afiş hazırlanıyor...")
            self.poster_photo = None
            self.current_poster_bytes = None
            self._request_poster_for_movie_async(movie)
            return

        self.current_poster_bytes = b

        try:
            img = Image.open(io.BytesIO(b))
            target_w = 260
            w, h = img.size
            if w and h:
                target_h = max(80, int(h * (target_w / w)))
                img = img.resize((target_w, target_h))

            photo = ImageTk.PhotoImage(img)
            self.poster_photo = photo
            self.poster_img_label.configure(image=photo, text="")
        except Exception:
            self.poster_img_label.configure(image="", text="Afiş yüklenemedi")
            self.poster_photo = None
            self.current_poster_bytes = None

    def _poster_hold_start(self, event):
        b = getattr(self, "current_poster_bytes", None)
        if not b:
            return
        if Image is None or ImageTk is None:
            return

        try:
            img = Image.open(io.BytesIO(b))
        except Exception:
            return

        # Ekrana sığacak şekilde büyüt
        max_w, max_h = 520, 780
        w, h = img.size
        scale = min(max_w / max(w, 1), max_h / max(h, 1), 1.0)
        nw, nh = int(w * scale), int(h * scale)
        if nw > 0 and nh > 0:
            img = img.resize((nw, nh))

        if self.poster_preview_win is None or not self.poster_preview_win.winfo_exists():
            win = tk.Toplevel(self)
            win.wm_overrideredirect(True)
            win.wm_attributes("-topmost", True)
            try:
                win.wm_attributes("-alpha", 0.96)
            except Exception:
                pass
            self.poster_preview_win = win
            self.poster_preview_label = tb.Label(win, padding=2)
            self.poster_preview_label.pack()

        self.poster_preview_imgtk = ImageTk.PhotoImage(img)
        self.poster_preview_label.configure(image=self.poster_preview_imgtk)

        self._poster_hold_move(event)

    def _poster_hold_move(self, event):
        if self.poster_preview_win is None or not self.poster_preview_win.winfo_exists():
            return

        win = self.poster_preview_win
        try:
            win.update_idletasks()
        except Exception:
            pass

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        try:
            ww = win.winfo_width() or win.winfo_reqwidth()
            wh = win.winfo_height() or win.winfo_reqheight()
        except Exception:
            ww, wh = 420, 640

        pad = 18
        margin = 10

        x = event.x_root + pad
        y = event.y_root + pad

        if x + ww + margin > sw:
            x = event.x_root - ww - pad
        if y + wh + margin > sh:
            y = event.y_root - wh - pad

        x = max(margin, min(x, sw - ww - margin))
        y = max(margin, min(y, sh - wh - margin))

        win.geometry(f"+{x}+{y}")

    def _poster_hold_end(self, event=None):
        if self.poster_preview_win is not None and self.poster_preview_win.winfo_exists():
            self.poster_preview_win.destroy()
        self.poster_preview_win = None
        self.poster_preview_imgtk = None


    def open_data_dir(self):
        try:
            if os.name == "nt":
                os.startfile(DATA_DIR)
            elif sys_platform() == "darwin":
                os.system(f'open "{DATA_DIR}"')
            else:
                os.system(f'xdg-open "{DATA_DIR}"')
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör açılamadı: {e}")


if __name__ == "__main__":
    FilmSecApp().mainloop()
