import sqlite3
import os
import re
import glob
import json
import shutil
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_SUPPORT_DIR = os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "AIImageViewer"
)
DB_FILENAME_PATTERN = re.compile(r"^image_metadata(\d*)\.db$")

DB_NAME = "image_metadata.db"

_db_dir_ready = False


def get_db_dir():
    """データベース・設定ポインタの保存先ディレクトリを返す（無ければ作成し、
    旧保存先＝プロジェクトフォルダから未移行のファイルがあれば自動コピーする）。
    移行はコピーのみで、旧ファイルは削除しない（万一の際にすぐ元に戻せるようにするため）。"""
    global _db_dir_ready
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)

    if not _db_dir_ready:
        _db_dir_ready = True
        try:
            existing_new = glob.glob(os.path.join(APP_SUPPORT_DIR, "image_metadata*.db"))
            if not existing_new:
                legacy_dbs = glob.glob(os.path.join(PROJECT_DIR, "image_metadata*.db"))
                for legacy_path in legacy_dbs:
                    filename = os.path.basename(legacy_path)
                    if DB_FILENAME_PATTERN.match(filename):
                        shutil.copy2(legacy_path, os.path.join(APP_SUPPORT_DIR, filename))

                legacy_pointer = os.path.join(PROJECT_DIR, "current_db.txt")
                new_pointer = os.path.join(APP_SUPPORT_DIR, "current_db.txt")
                if os.path.exists(legacy_pointer) and not os.path.exists(new_pointer):
                    shutil.copy2(legacy_pointer, new_pointer)
        except OSError as e:
            print(f"Database migration warning: {e}")

    return APP_SUPPORT_DIR


def _db_path():
    """現在の DB_NAME に対応するデータベースファイルの絶対パスを返す（内部用）。"""
    return os.path.join(get_db_dir(), DB_NAME)


def _current_db_pointer_path():
    """current_db.txt（現在使用中のDBファイル名を記録するポインタ）の絶対パスを返す。"""
    return os.path.join(get_db_dir(), "current_db.txt")


def list_available_databases():
    """データベース保存先にある、命名規則（image_metadata.db, image_metadata2.db, ...）に
    一致するデータベースファイルの一覧を、ファイル名のみ・番号順で返す。"""
    found = []
    for path in glob.glob(os.path.join(get_db_dir(), "image_metadata*.db")):
        filename = os.path.basename(path)
        if DB_FILENAME_PATTERN.match(filename):
            found.append(filename)

    def sort_key(name):
        num_part = DB_FILENAME_PATTERN.match(name).group(1)
        return int(num_part) if num_part else 1

    return sorted(found, key=sort_key)


def get_next_available_db_filename():
    """まだ使われていない次のデータベースファイル名（例: image_metadata2.db）を返す（作成はしない）。"""
    existing = set(list_available_databases())
    if "image_metadata.db" not in existing:
        return "image_metadata.db"
    n = 2
    while f"image_metadata{n}.db" in existing:
        n += 1
    return f"image_metadata{n}.db"


def resolve_current_db_name():
    """起動時に使用するデータベースファイル名を決定し、DB_NAME に反映する。
    ポインタファイル（current_db.txt）に記録されたファイル名があればそれを使い、
    無ければこれまで通り image_metadata.db を使う（既存ユーザーの挙動は変わらない）。"""
    global DB_NAME
    pointer_path = _current_db_pointer_path()
    if os.path.exists(pointer_path):
        try:
            with open(pointer_path, "r", encoding="utf-8") as f:
                recorded_name = f.read().strip()
            if recorded_name and DB_FILENAME_PATTERN.match(recorded_name):
                DB_NAME = recorded_name
                return DB_NAME
        except OSError:
            pass
    DB_NAME = "image_metadata.db"
    return DB_NAME


def set_current_db_name(filename):
    """使用するデータベースファイルを切り替える（ポインタファイルの更新のみ）。
    実際に反映するには、呼び出し側でアプリを再起動すること。"""
    with open(_current_db_pointer_path(), "w", encoding="utf-8") as f:
        f.write(filename)


def get_current_db_path():
    """現在使用中のデータベースファイルの絶対パスを返す。
    保存先を直接参照したいUI側のコードは、この関数を経由すること。
    保存先は get_db_dir()（~/Library/Application Support/AIImageViewer）に統一されている
    （2026-08-04〜。それ以前はプロジェクトフォルダ内だった）。"""
    return os.path.join(get_db_dir(), DB_NAME)


def create_new_database_slot():
    """まだ使われていない番号で、新しい空のデータベースファイルを作成する（切り替えは行わない）。
    戻り値は作成したファイル名。"""
    global DB_NAME
    filename = get_next_available_db_filename()
    original_db_name = DB_NAME
    try:
        DB_NAME = filename
        init_db()
    finally:
        DB_NAME = original_db_name
    return filename


def import_external_database(source_path):
    """外部のバックアップ用データベースファイルを検証したうえで、まだ使われていない番号の
    新しいスロットとして既定の保存先（get_db_dir()）へコピーする（切り替えは行わない）。
    コピー後は init_db() 相当のマイグレーション処理を通し、このアプリの現在のスキーマに揃える。

    source_path が有効なこのアプリのデータベースでない場合（imagesテーブルが無い等）は
    ValueError を送出する。戻り値はコピー後の（このアプリ内での）ファイル名。"""
    global DB_NAME
    try:
        check_conn = sqlite3.connect(source_path)
        check_cursor = check_conn.cursor()
        check_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
        has_images_table = check_cursor.fetchone() is not None
        check_conn.close()
    except sqlite3.Error:
        raise ValueError("選択されたファイルは有効なデータベースファイルとして開けませんでした。")

    if not has_images_table:
        raise ValueError("選択されたファイルは、このアプリのデータベース形式ではありません。")

    filename = get_next_available_db_filename()
    target_path = os.path.join(get_db_dir(), filename)
    shutil.copy2(source_path, target_path)

    original_db_name = DB_NAME
    try:
        DB_NAME = filename
        init_db()
    finally:
        DB_NAME = original_db_name

    return filename


DEFAULT_APP_SETTINGS = {
    "sequence_prefix": "CG_",
    "sequence_digits": "5",
    "sequence_append": "",
    "show_param_steps": "0",
    "show_param_sampler": "0",
    "show_param_scheduler": "0",
    "show_param_cfg_scale": "0",
    "show_param_seed": "0",
    "show_param_size": "0",
    "theme_mode": "auto",
    "import_order_mode": "confirm",
    "last_import_order": "filename_asc",
    "allow_duplicate_content": "0",
    "last_sort_index": "0",
    "last_sort_dir": "ASC",
    "last_group_mode": "none",
    "collapsed_folders": "[]",
    "use_sequential_naming": "1",
    "rename_show_edit_dialog": "0",
    "reading_mode_default_pattern": "A",
    "reading_mode_theme": "dark",
    "reading_mode_center_align": "0",
    "folder_group_order": "[]",
    "browse_mode": "images",
    "view_mode": "list",
    "grid_tile_size": "medium",
    "preview_size_mode": "standard",
    "metadata_fields_display": "",
    "metadata_section_order": "",
}


def init_db():
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            prompt TEXT,
            negative_prompt TEXT,
            other_metadata TEXT,
            rating INTEGER DEFAULT 0,
            file_mtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("PRAGMA table_info(images)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "updated_at" not in existing_columns:
        cursor.execute("ALTER TABLE images ADD COLUMN updated_at TIMESTAMP")
        cursor.execute("UPDATE images SET updated_at = created_at WHERE updated_at IS NULL")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE
        )
    """)

    cursor.execute("PRAGMA table_info(folders)")
    existing_folder_columns = [col[1] for col in cursor.fetchall()]
    if "color" not in existing_folder_columns:
        cursor.execute("ALTER TABLE folders ADD COLUMN color TEXT")

    cursor.execute("PRAGMA table_info(images)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "file_hash" not in existing_columns:
        cursor.execute("ALTER TABLE images ADD COLUMN file_hash TEXT")
    
    cursor.execute("DROP INDEX IF EXISTS idx_images_file_hash")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_file_hash_lookup ON images(file_hash)")
    
    cursor.execute("PRAGMA table_info(images)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "imported_at" not in existing_columns:
        cursor.execute("ALTER TABLE images ADD COLUMN imported_at TIMESTAMP")
        cursor.execute("UPDATE images SET imported_at = created_at WHERE imported_at IS NULL")
    
    cursor.execute("PRAGMA table_info(images)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "created_at" in existing_columns and "file_mtime" not in existing_columns:
        cursor.execute("ALTER TABLE images RENAME COLUMN created_at TO file_mtime")
    
    cursor.execute("PRAGMA table_info(images)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "file_size" not in existing_columns:
        cursor.execute("ALTER TABLE images ADD COLUMN file_size INTEGER")
        cursor.execute("SELECT id, file_path FROM images WHERE file_size IS NULL")
        rows_to_backfill = cursor.fetchall()
        for img_id, f_path in rows_to_backfill:
            if f_path and os.path.exists(f_path):
                try:
                    size = os.path.getsize(f_path)
                    cursor.execute("UPDATE images SET file_size = ? WHERE id = ?", (size, img_id))
                except OSError:
                    pass
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS excluded_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE
        )
    """)
    
    cursor.execute("PRAGMA table_info(images)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "is_locked" not in existing_columns:
        cursor.execute("ALTER TABLE images ADD COLUMN is_locked INTEGER DEFAULT 0")
        cursor.execute("UPDATE images SET is_locked = 0 WHERE is_locked IS NULL")

    cursor.execute("PRAGMA table_info(images)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "memo" not in existing_columns:
        cursor.execute("ALTER TABLE images ADD COLUMN memo TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            category TEXT,
            target_path TEXT,
            detail TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_alert_state (
            category TEXT,
            target_path TEXT,
            warned INTEGER DEFAULT 0,
            PRIMARY KEY (category, target_path)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folder_naming_rules (
            folder_path TEXT PRIMARY KEY,
            prefix TEXT,
            digits INTEGER,
            append TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS album_images (
            album_id INTEGER NOT NULL,
            image_id INTEGER NOT NULL,
            added_at TEXT,
            PRIMARY KEY (album_id, image_id),
            FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("PRAGMA table_info(albums)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "color" not in existing_columns:
        cursor.execute("ALTER TABLE albums ADD COLUMN color TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS album_naming_rules (
            album_id INTEGER PRIMARY KEY,
            prefix TEXT,
            digits INTEGER,
            append TEXT
        )
    """)

    for key, value in DEFAULT_APP_SETTINGS.items():
        cursor.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def add_folder(folder_path):
    """取り込み済みフォルダとしてパスを記憶する（重複は無視する）"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO folders (path) VALUES (?)", (folder_path,))
    conn.commit()
    conn.close()

def get_all_folders():
    """記憶している取り込み済みフォルダのパス一覧を返す"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM folders ORDER BY path ASC")
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows

def get_folder_color(folder_path):
    """指定フォルダ（実パス）の識別色を返す。未設定またはフォルダ未登録の場合はNone
    （v1.4.1〜、フォルダ見出しアイコンの色分け機能用。albums.colorと同じ考え方）。"""
    if not folder_path:
        return None
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT color FROM folders WHERE path = ?", (folder_path,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_folder_color(folder_path, color):
    """指定フォルダ（実パス）の識別色を保存する（color=Noneで未設定に戻す）。
    folders テーブルにまだ行が無い場合（通常は起こらないが念のため）は新規作成する。"""
    if not folder_path:
        return
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO folders (path, color) VALUES (?, ?) "
        "ON CONFLICT(path) DO UPDATE SET color = excluded.color",
        (folder_path, color)
    )
    conn.commit()
    conn.close()

def delete_folder_and_images(folder_path):
    """指定フォルダ（実パス）を「取り込み済みフォルダ」一覧から削除し、
    そのフォルダ直下に登録されている画像レコードもあわせて削除する。
    以降このフォルダは同期（sync_folders）の対象から外れるが、folders テーブルの
    行を消すだけなので、同じフォルダを改めて「フォルダを取り込む」で取り込めば
    add_folder() により再度同期対象に戻る。
    戻り値: 削除した画像の件数"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_path FROM images")
    rows = cursor.fetchall()
    target_ids = [img_id for img_id, f_path in rows if os.path.dirname(f_path) == folder_path]

    if target_ids:
        cursor.executemany("DELETE FROM images WHERE id = ?", [(i,) for i in target_ids])
        cursor.executemany("DELETE FROM album_images WHERE image_id = ?", [(i,) for i in target_ids])

    cursor.execute("DELETE FROM folders WHERE path = ?", (folder_path,))
    cursor.execute(
        "DELETE FROM sync_alert_state WHERE target_path = ? AND category IN ('folder_missing', 'import_error')",
        (folder_path,)
    )

    conn.commit()
    conn.close()
    return len(target_ids)

def remove_missing_images():
    """ディスク上に存在しなくなった画像のレコードをDBから削除する。
    削除したファイルパスの一覧を返す（呼び出し側で件数が必要な場合は len() を使う。
    2026-08-14〜: 同期履歴への記録用に、件数だけでなくパス一覧を返すよう変更）。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_path FROM images")
    rows = cursor.fetchall()

    missing = [(img_id, f_path) for img_id, f_path in rows if not os.path.exists(f_path)]

    if missing:
        cursor.executemany("DELETE FROM images WHERE id = ?", [(i,) for i, _ in missing])
        cursor.executemany("DELETE FROM album_images WHERE image_id = ?", [(i,) for i, _ in missing])
        conn.commit()

    conn.close()
    return [f_path for _, f_path in missing]


MAX_SYNC_HISTORY_ROWS = 500


def add_sync_history_entry(category, target_path, detail):
    """同期処理で検出した問題（フォルダ/画像が見つからない、取り込みエラー等）を1件、履歴に記録する。
    category: "folder_missing" / "image_missing" / "import_error" のいずれか。

    - タイムスタンプは SQLite の CURRENT_TIMESTAMP（UTC基準）ではなく、Pythonのローカル時刻
      （datetime.now()）を使う。CURRENT_TIMESTAMPをそのまま使うと、日本（UTC+9）では
      記録時刻が実際より9時間過去に見えてしまうため（2026-08-14 修正）。
    - 同一の (category, target_path, detail) の組み合わせは「同じ問題の繰り返し」とみなし、
      既存の記録を削除してから最新の1件のみを記録し直す（一覧が同じ内容で埋まらないようにするため）。
    - 上限（MAX_SYNC_HISTORY_ROWS）を超えた分は、古いものから自動的に削除する。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM sync_history WHERE category = ? AND target_path = ? AND detail = ?",
        (category, target_path, detail)
    )
    cursor.execute(
        "INSERT INTO sync_history (timestamp, category, target_path, detail) VALUES (?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), category, target_path, detail)
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM sync_history")
    total = cursor.fetchone()[0]
    if total > MAX_SYNC_HISTORY_ROWS:
        overflow = total - MAX_SYNC_HISTORY_ROWS
        cursor.execute(
            "DELETE FROM sync_history WHERE id IN (SELECT id FROM sync_history ORDER BY id ASC LIMIT ?)",
            (overflow,)
        )
        conn.commit()

    conn.close()


def get_sync_history(limit=None):
    """同期履歴を新しい順で返す。各要素は (timestamp, category, target_path, detail) のタプル。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    query = "SELECT timestamp, category, target_path, detail FROM sync_history ORDER BY id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows


def is_alert_warned(category, target_path):
    """指定した (category, target_path) について、既に一度ポップアップで警告済みかどうかを返す。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "SELECT warned FROM sync_alert_state WHERE category = ? AND target_path = ?",
        (category, target_path)
    )
    row = cursor.fetchone()
    conn.close()
    return bool(row and row[0])


def set_alert_warned(category, target_path, warned):
    """指定した (category, target_path) の警告済み状態を更新する。
    warned=True: 今回ポップアップで警告した（次回からは履歴のみに記録する）。
    warned=False: 問題が解消された（次に同じ問題が起きたら、改めてポップアップで警告する）。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sync_alert_state (category, target_path, warned) VALUES (?, ?, ?) "
        "ON CONFLICT(category, target_path) DO UPDATE SET warned = excluded.warned",
        (category, target_path, 1 if warned else 0)
    )
    conn.commit()
    conn.close()

def insert_image(file_path, file_name, prompt, negative_prompt, other_metadata, file_mtime, file_hash=None, file_size=None, allow_duplicate_content=False):
    """新しい画像をデータベースに登録する。
    file_path が重複している場合は、常に登録をスキップし False を返す（パスの重複はそもそも同じファイルのため）。
    file_hash が既存の別画像と一致する場合（内容が同一の画像の重複コピー）は、allow_duplicate_content が
    False（既定）の場合のみ登録をスキップする。True の場合は、内容が重複していても別レコードとして登録する。
    実際に新規登録できた場合は True を返す。
    
    file_mtime: ファイル自体の更新日時（mtime）。画面上は便宜的に「作成日時」として表示される。
    file_size: ファイルサイズ（バイト単位）。ファイルサイズ順の並び替えに使う。
    """
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    try:
        if not allow_duplicate_content and file_hash:
            cursor.execute("SELECT 1 FROM images WHERE file_hash = ? LIMIT 1", (file_hash,))
            if cursor.fetchone():
                return False
        
        cursor.execute("""
            INSERT OR IGNORE INTO images (file_path, file_name, prompt, negative_prompt, other_metadata, file_mtime, updated_at, file_hash, imported_at, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (file_path, file_name, prompt, negative_prompt, other_metadata, file_mtime, file_mtime, file_hash, file_size))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Database insert error: {e}")
        raise e
    finally:
        conn.close()

def get_all_file_paths():
    """DBに登録済みの全ファイルパスをsetで返す（取り込み・同期時の重複スキップ高速化用）"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM images")
    paths = {row[0] for row in cursor.fetchall()}
    conn.close()
    return paths

def add_excluded_path(file_path):
    """削除された画像のパスを「同期の除外リスト」に記録する（重複は無視する）"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO excluded_paths (file_path) VALUES (?)", (file_path,))
    conn.commit()
    conn.close()

def remove_excluded_path(file_path):
    """明示的な再取り込み時に、除外リストからパスを解除する"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM excluded_paths WHERE file_path = ?", (file_path,))
    conn.commit()
    conn.close()

def get_excluded_paths():
    """除外リストに載っている全パスをsetで返す（同期時のスキップ判定用）"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM excluded_paths")
    paths = {row[0] for row in cursor.fetchall()}
    conn.close()
    return paths

def set_locked(image_ids, locked):
    """指定した画像ID群のロック状態をまとめて設定する（locked: True/False）"""
    if not image_ids:
        return
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.executemany(
        "UPDATE images SET is_locked = ? WHERE id = ?",
        [(1 if locked else 0, img_id) for img_id in image_ids]
    )
    conn.commit()
    conn.close()

def get_locked_ids(image_ids):
    """指定した画像ID群のうち、実際にロックされているものだけをsetで返す"""
    if not image_ids:
        return set()
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in image_ids)
    cursor.execute(f"SELECT id FROM images WHERE id IN ({placeholders}) AND is_locked = 1", list(image_ids))
    locked = {row[0] for row in cursor.fetchall()}
    conn.close()
    return locked

def get_setting(key, default=None):
    """アプリ設定を1件取得する。存在しなければ default を返す"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    """アプリ設定を1件保存する（既存なら上書き）"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO app_settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value))
    )
    conn.commit()
    conn.close()

def resolve_naming_placeholders(text, folder_name=None, album_name=None):
    """プレフィックス／アペンド欄で使えるプレースホルダーを実際の値に置換する。
    {フォルダ名} / {folder name}: 取り込み・書き出し対象のフォルダ名（不明な場合は空文字）
    {アルバム名} / {album name}: アルバム起点の操作（アルバム専用の自動採番）対象のアルバム名
    （不明な場合は空文字。2026-08-20〜追加。アルバムは複数の実フォルダにまたがり得るため、
    アルバム起点の操作では{フォルダ名}の代わりにこちらを使う想定）
    {日付} / {date}: 今日の日付（YYYYMMDD）
    表示言語（日本語UI／英語UI）に関わらず、どちらの表記のプレースホルダーも同じ意味として
    解決する（v1.3.0〜、英語UI対応に伴い、UI言語をまたいでも命名ルールが壊れないようにするため）。
    採番（インポート時）・一括リネーム・連番コピーのいずれからも共通で使う想定（2026-08-15〜）。"""
    if not text:
        return text
    today_str = datetime.now().strftime("%Y%m%d")
    resolved = text.replace("{日付}", today_str).replace("{date}", today_str)
    resolved = resolved.replace("{フォルダ名}", folder_name or "").replace("{folder name}", folder_name or "")
    resolved = resolved.replace("{アルバム名}", album_name or "").replace("{album name}", album_name or "")
    return resolved

def get_folder_naming_rule(folder_path):
    """指定フォルダ（実パス）専用の命名ルール上書き設定を返す。
    未設定の場合は None（＝アプリ全体の既定ルールを使う）を返す。
    戻り値は {"prefix": str, "digits": int, "append": str} の辞書。"""
    if not folder_path:
        return None
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "SELECT prefix, digits, append FROM folder_naming_rules WHERE folder_path = ?",
        (folder_path,)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return {"prefix": row[0] or "", "digits": int(row[1]) if row[1] else 5, "append": row[2] or ""}

def set_folder_naming_rule(folder_path, prefix, digits, append):
    """指定フォルダ専用の命名ルール上書きを保存する（既存があれば更新）。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO folder_naming_rules (folder_path, prefix, digits, append) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(folder_path) DO UPDATE SET prefix = excluded.prefix, digits = excluded.digits, append = excluded.append",
        (folder_path, prefix, digits, append)
    )
    conn.commit()
    conn.close()

def clear_folder_naming_rule(folder_path):
    """指定フォルダ専用の命名ルール上書きを削除し、アプリ全体の既定ルールに戻す。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM folder_naming_rules WHERE folder_path = ?", (folder_path,))
    conn.commit()
    conn.close()

def get_all_albums():
    """全アルバムを、並び順（sort_order→作成順）でリストで返す。
    戻り値の各要素は {"id", "name", "sort_order", "image_count", "color"} の辞書。
    color は未設定の場合 None（v1.4.1 段階3〜、色ドット表示機能用）。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.name, a.sort_order, COUNT(ai.image_id), a.color
        FROM albums a
        LEFT JOIN album_images ai ON ai.album_id = a.id
        GROUP BY a.id
        ORDER BY a.sort_order, a.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "sort_order": r[2], "image_count": r[3], "color": r[4]} for r in rows]

def set_album_color(album_id, color):
    """アルバムの識別色を設定する（v1.4.1 段階3〜）。color は "#rrggbb" 形式の文字列、または
    未設定に戻す場合は None を渡す。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE albums SET color = ? WHERE id = ?", (color, album_id))
    conn.commit()
    conn.close()

def add_album(name):
    """新しいアルバムを作成し、作成したアルバムのidを返す。
    並び順（sort_order）は既存の最大値+1とし、常に一覧の末尾に追加する。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM albums")
    next_order = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO albums (name, sort_order, created_at) VALUES (?, ?, ?)",
        (name, next_order, datetime.now().isoformat())
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def rename_album(album_id, new_name):
    """アルバム名を変更する。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE albums SET name = ? WHERE id = ?", (new_name, album_id))
    conn.commit()
    conn.close()

def delete_album(album_id):
    """アルバムを削除する（アルバム内の画像自体は削除しない。あくまで「入れ物」を消すだけ）。
    sqlite3はFOREIGN KEY制約を既定で強制しないため、album_images・album_naming_rulesの
    紐付けも明示的に消す。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM album_images WHERE album_id = ?", (album_id,))
    cursor.execute("DELETE FROM album_naming_rules WHERE album_id = ?", (album_id,))
    cursor.execute("DELETE FROM albums WHERE id = ?", (album_id,))
    conn.commit()
    conn.close()

def get_album_name(album_id):
    """指定idのアルバム名を返す。存在しない場合はNone
    （{アルバム名}プレースホルダーの解決や、通知文言の組み立てに使う）。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM albums WHERE id = ?", (album_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_album_naming_rule(album_id):
    """指定アルバム専用の命名ルール上書き設定を返す。未設定の場合はNone
    （＝アプリ全体の既定ルールを使う）を返す。戻り値は {"prefix", "digits", "append"} の辞書。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "SELECT prefix, digits, append FROM album_naming_rules WHERE album_id = ?",
        (album_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return {"prefix": row[0] or "", "digits": int(row[1]) if row[1] else 5, "append": row[2] or ""}

def set_album_naming_rule(album_id, prefix, digits, append):
    """指定アルバム専用の命名ルール上書きを保存する（既存があれば更新）。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO album_naming_rules (album_id, prefix, digits, append) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(album_id) DO UPDATE SET prefix = excluded.prefix, digits = excluded.digits, append = excluded.append",
        (album_id, prefix, digits, append)
    )
    conn.commit()
    conn.close()

def clear_album_naming_rule(album_id):
    """指定アルバム専用の命名ルール上書きを削除し、アプリ全体の既定ルールに戻す。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM album_naming_rules WHERE album_id = ?", (album_id,))
    conn.commit()
    conn.close()

def set_album_order(ordered_album_ids):
    """アルバム一覧の並び順をまとめて更新する（サイドバーでの手動並べ替え用）。
    ordered_album_ids はアルバムidのリストで、先頭が一覧の最上部になる。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.executemany(
        "UPDATE albums SET sort_order = ? WHERE id = ?",
        [(order, album_id) for order, album_id in enumerate(ordered_album_ids)]
    )
    conn.commit()
    conn.close()

def add_images_to_album(album_id, image_ids):
    """複数の画像を、まとめて指定アルバムに追加する（既に追加済みの画像はそのまま・重複エラーにしない）。"""
    if not image_ids:
        return
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.executemany(
        "INSERT OR IGNORE INTO album_images (album_id, image_id, added_at) VALUES (?, ?, ?)",
        [(album_id, image_id, now_str) for image_id in image_ids]
    )
    conn.commit()
    conn.close()

def remove_images_from_album(album_id, image_ids):
    """複数の画像を、まとめて指定アルバムから外す（画像自体・他のアルバムへの所属には影響しない）。"""
    if not image_ids:
        return
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.executemany(
        "DELETE FROM album_images WHERE album_id = ? AND image_id = ?",
        [(album_id, image_id) for image_id in image_ids]
    )
    conn.commit()
    conn.close()

def get_album_image_ids(album_id):
    """指定アルバムに所属する画像idの集合（set）を返す。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT image_id FROM album_images WHERE album_id = ?", (album_id,))
    rows = cursor.fetchall()
    conn.close()
    return {r[0] for r in rows}

def get_all_album_memberships():
    """全画像のアルバム所属を一括取得し、{image_id: [{"id", "name", "color"}, ...]} の辞書で返す
    （v1.4.1 段階3〜、色ドット表示・段階4のホバーオーバーレイ用）。画像リスト構築のたびに
    画像1件ごとDB問い合わせするのを避けるため、一覧構築の直前に1回だけ呼び出してマップ化する想定。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ai.image_id, a.id, a.name, a.color FROM album_images ai
        JOIN albums a ON a.id = ai.album_id
        ORDER BY a.sort_order, a.id
    """)
    rows = cursor.fetchall()
    conn.close()
    result = {}
    for image_id, album_id, name, color in rows:
        result.setdefault(image_id, []).append({"id": album_id, "name": name, "color": color})
    return result

def get_albums_for_image(image_id):
    """指定画像が所属している全アルバムを [{"id", "name", "color"}, ...] で返す（右クリックメニューの
    チェック表示・複数所属の確認用、および画像リストの色ドット表示用）。"""
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.name, a.color FROM albums a
        JOIN album_images ai ON ai.album_id = a.id
        WHERE ai.image_id = ?
        ORDER BY a.sort_order, a.id
    """, (image_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "color": r[2]} for r in rows]

def peek_next_sequence_number(prefix, append):
    """指定したプレフィックス＋アペンドの組み合わせで、次に採番される番号を取得する（消費しない・設定画面のプレビュー用）。
    まだ一度も使われていない組み合わせの場合は 1 を返す。
    """
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    counter_key = f"next_sequence_number::{prefix}::{append}"
    cursor.execute("SELECT value FROM app_settings WHERE key = ?", (counter_key,))
    row = cursor.fetchone()
    conn.close()
    return int(row[0]) if row else 1

def generate_next_sequential_name(folder_name=None, folder_path=None):
    """新規取り込み画像の「名前」欄に使う連番（例: CG_00001）を生成する。
    プレフィックス・桁数・アペンド（末尾に付与する任意文字列）は、folder_path（取り込み元の
    実フォルダパス）専用の上書きルール（folder_naming_rules）があればそれを優先し、
    無ければ app_settings のアプリ全体の既定ルールを使う（未設定なら CG_, 5桁, アペンドなし）。
    このフォルダ単位の上書きは、以後の新規取り込みにのみ適用され、既存ファイルへは影響しない
    （2026-08-15〜）。

    プレフィックス・アペンドに {フォルダ名}／{日付} のプレースホルダーが含まれる場合、
    folder_name（取り込み元フォルダ名）と今日の日付で置換してから採番する（2026-08-15〜）。
    置換後の文字列を基に採番カウンタを分けるため、フォルダや日付が異なれば自動的に別の連番として管理される。

    採番カウンタは「プレフィックス＋アペンド」の組み合わせごとに独立して管理する。
    例えば CG_00001_A と CG_00001_B はアペンドが異なるため、それぞれ 1 から採番される。
    同じ組み合わせに戻した場合は、その組み合わせで前回まで進んだ番号から再開する
    （画像を削除しても番号は再利用しない＝欠番のまま進む）。
    """
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()

    folder_rule = None
    if folder_path:
        cursor.execute(
            "SELECT prefix, digits, append FROM folder_naming_rules WHERE folder_path = ?",
            (folder_path,)
        )
        folder_rule = cursor.fetchone()

    if folder_rule is not None:
        prefix, digits, append = folder_rule[0] or "", int(folder_rule[1]) if folder_rule[1] else 5, folder_rule[2] or ""
    else:
        cursor.execute("SELECT value FROM app_settings WHERE key = 'sequence_prefix'")
        row = cursor.fetchone()
        prefix = row[0] if row else "CG_"

        cursor.execute("SELECT value FROM app_settings WHERE key = 'sequence_digits'")
        row = cursor.fetchone()
        digits = int(row[0]) if row else 5

        cursor.execute("SELECT value FROM app_settings WHERE key = 'sequence_append'")
        row = cursor.fetchone()
        append = row[0] if row else ""

    prefix = resolve_naming_placeholders(prefix, folder_name)
    append = resolve_naming_placeholders(append, folder_name)

    counter_key = f"next_sequence_number::{prefix}::{append}"
    cursor.execute("SELECT value FROM app_settings WHERE key = ?", (counter_key,))
    row = cursor.fetchone()
    if row:
        next_num = int(row[0])
    else:
        cursor.execute("SELECT value FROM app_settings WHERE key = 'next_sequence_number'")
        legacy_row = cursor.fetchone()
        if legacy_row:
            next_num = int(legacy_row[0])
            cursor.execute("DELETE FROM app_settings WHERE key = 'next_sequence_number'")
        else:
            next_num = 1
    
    name = f"{prefix}{next_num:0{digits}d}{append}"
    
    cursor.execute(
        "INSERT INTO app_settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (counter_key, str(next_num + 1))
    )
    conn.commit()
    conn.close()
    return name

def get_collapsed_folders():
    """折りたたんでいるフォルダ名の一覧（set）を返す。設定が壊れている・未設定の場合は空集合を返す。"""
    raw = get_setting("collapsed_folders", "[]")
    try:
        names = json.loads(raw)
        if isinstance(names, list):
            return {str(x) for x in names}
    except (json.JSONDecodeError, TypeError):
        pass
    return set()


def set_collapsed_folders(folder_names):
    """折りたたんでいるフォルダ名の一覧を保存する。"""
    set_setting("collapsed_folders", json.dumps(sorted(folder_names), ensure_ascii=False))


def get_collapsed_albums():
    """折りたたんでいるアルバムidの一覧（set）を返す（get_collapsed_foldersと同じ考え方。
    2026-08-20〜：アルバム表示も画像リスト側と同様、前回の展開/折りたたみ状態を記憶するように）。"""
    raw = get_setting("collapsed_albums", "[]")
    try:
        ids = json.loads(raw)
        if isinstance(ids, list):
            return {int(x) for x in ids}
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return set()


def set_collapsed_albums(album_ids):
    """折りたたんでいるアルバムidの一覧を保存する。"""
    set_setting("collapsed_albums", json.dumps(sorted(album_ids), ensure_ascii=False))


def get_album_totals():
    """アルバム表示中のリスト下部ステータス用に、「アルバムの総数」「アルバムに所属する
    画像の総数（重複所属分は1件として数える）」を返す（2026-08-20〜）。
    フォルダ表示側のステータスとは異なり、同期日時は概念上存在しないため含めない。"""
    conn = sqlite3.connect(get_current_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM albums")
    album_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT image_id) FROM album_images")
    image_count = cursor.fetchone()[0]
    conn.close()
    return album_count, image_count


def get_folder_group_order():
    """フォルダ別グループ表示での、フォルダの並び順（フォルダ名のリスト）を返す。
    設定が壊れている・未設定の場合は空リストを返す（呼び出し側でアルファベット順にフォールバックする）。"""
    raw = get_setting("folder_group_order", "[]")
    try:
        order = json.loads(raw)
        if isinstance(order, list):
            return [str(x) for x in order]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def set_folder_group_order(folder_names):
    """フォルダ別グループ表示での、フォルダの並び順を保存する。"""
    set_setting("folder_group_order", json.dumps(list(folder_names), ensure_ascii=False))


def get_database_stats():
    """初期化前の確認表示用に、現在DBに登録されている件数の概要を返す。
    画像レコード・記憶されているフォルダの件数のみを対象とする（アプリ設定は対象外）。
    """
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM images")
    image_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM folders")
    folder_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM excluded_paths")
    excluded_count = cursor.fetchone()[0]
    conn.close()
    return {"images": image_count, "folders": folder_count, "excluded": excluded_count}

def reset_database():
    """画像ライブラリのデータ（画像レコード・記憶されたフォルダ・除外リスト）をすべて削除する。
    アプリの設定（連番命名規則・テーマ設定等、app_settings）は保持したままにする。
    実ファイル自体は一切削除しない（あくまでこのアプリの管理データのみを初期化する）。
    """
    conn = sqlite3.connect(_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM images")
    cursor.execute("DELETE FROM folders")
    cursor.execute("DELETE FROM excluded_paths")
    cursor.execute("DELETE FROM sync_history")
    cursor.execute("DELETE FROM sync_alert_state")
    cursor.execute("DELETE FROM album_images")
    conn.commit()
    conn.close()

def reset_settings_to_defaults():
    """命名規則・表示項目・テーマなど、DEFAULT_APP_SETTINGS に登録されている設定項目をすべて
    既定値に戻す。next_sequence_number（連番の採番カウンタ）はここでは対象外とし、
    途中まで進んだ番号が巻き戻って既存の名前と衝突することがないようにする。
    """
    for key, value in DEFAULT_APP_SETTINGS.items():
        set_setting(key, value)

def reset_sequence_counter():
    """現在保存されているプレフィックス＋アペンドの組み合わせに対する採番カウンタを1にリセットする。
    過去に同じ名前（プレフィックス・番号・アペンドが一致）の画像が存在していても一切考慮せず、
    次に生成される番号は必ず1から始まる。呼び出し元（設定画面）で、その旨を利用者に警告すること。
    """
    prefix = get_setting("sequence_prefix", "CG_")
    append = get_setting("sequence_append", "")
    counter_key = f"next_sequence_number::{prefix}::{append}"
    set_setting(counter_key, "1")
