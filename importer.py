import os
import hashlib
from PIL import Image, ExifTags
from datetime import datetime
import database


def _format_gps(gps_ifd):
    """GPS IFD（度分秒形式）を "緯度, 経度" の10進表記に変換する。取得できない場合は空文字。"""
    try:
        def to_decimal(dms, ref):
            degrees, minutes, seconds = dms
            value = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
            if ref in ('S', 'W'):
                value = -value
            return value

        lat = gps_ifd.get(2)
        lat_ref = gps_ifd.get(1)
        lon = gps_ifd.get(4)
        lon_ref = gps_ifd.get(3)
        if lat and lon and lat_ref and lon_ref:
            lat_dec = to_decimal(lat, lat_ref)
            lon_dec = to_decimal(lon, lon_ref)
            return f"{lat_dec:.6f}, {lon_dec:.6f}"
    except Exception:
        pass
    return ""


def _format_exif(img):
    """カメラ由来のEXIF情報を、「その他パラメータ / メタデータ / EXIF情報」欄向けの
    読みやすいテキストに整形する。主要なタグのみを抜き出し、値が取得できない項目は省略する。"""
    try:
        exif = img.getexif()
    except Exception:
        return ""
    if not exif:
        return ""

    def _get(tag_id):
        value = exif.get(tag_id)
        if value in (None, ""):
            return None
        return value

    lines = []
    maker = _get(271)
    if maker:
        lines.append(f"メーカー: {maker}")
    model = _get(272)
    if model:
        lines.append(f"機種: {model}")
    dt = _get(36867) or _get(306)
    if dt:
        lines.append(f"撮影日時: {dt}")
    exposure = _get(33434)
    if exposure:
        lines.append(f"露出時間: {exposure}秒")
    fnumber = _get(33437)
    if fnumber:
        lines.append(f"F値: F{fnumber}")
    iso = _get(34855)
    if iso:
        lines.append(f"ISO感度: {iso}")
    focal = _get(37386)
    if focal:
        lines.append(f"焦点距離: {focal}mm")
    software = _get(305)
    if software:
        lines.append(f"編集ソフト: {software}")

    try:
        gps_ifd = exif.get_ifd(0x8825)
    except Exception:
        gps_ifd = None
    if gps_ifd:
        gps_text = _format_gps(gps_ifd)
        if gps_text:
            lines.append(f"GPS座標: {gps_text}")

    return "\n".join(lines)


def extract_ai_metadata(file_path):
    """画像から生成AIのメタデータ（プロンプト等）を抽出する関数"""
    prompt = ""
    negative_prompt = ""
    other_metadata = ""
    
    try:
        with Image.open(file_path) as img:
            info = img.info
            
            if 'parameters' in info:
                params = info['parameters']
                other_metadata = params
                
                if "Negative prompt:" in params:
                    parts = params.split("Negative prompt:")
                    prompt = parts[0].strip()
                    neg_and_others = parts[1].split("\n")
                    negative_prompt = neg_and_others[0].strip()
                else:
                    prompt = params.split("\n")[0].strip()
                    
            elif 'Description' in info:
                prompt = info['Description']
                if 'Comment' in info:
                    other_metadata = info['Comment']
            
            elif 'workflow' in info or 'prompt' in info:
                parts = []
                if 'prompt' in info:
                    parts.append(f"[ComfyUI prompt（実行用APIフォーマット）]\n{info['prompt']}")
                if 'workflow' in info:
                    parts.append(f"[ComfyUI workflow（ワークフロー全体）]\n{info['workflow']}")
                other_metadata = "\n\n".join(parts)
                prompt = ("ComfyUI形式の画像です。ワークフローの構成が多岐にわたるため、"
                          "プロンプトの自動抽出には対応していません。"
                          "「その他パラメータ / メタデータ / EXIF情報」欄でワークフロー全文をご確認ください。")

            else:
                exif_text = _format_exif(img)
                if exif_text:
                    other_metadata = exif_text
                    prompt = ("この画像にはAI生成パラメータは見つかりませんでした。"
                              "「その他パラメータ / メタデータ / EXIF情報」欄で撮影情報（EXIF）をご確認ください。")

            if not prompt and not negative_prompt:
                prompt = "No prompt found (Normal image or metadata stripped)"

    except Exception as e:
        print(f"Metadata extraction error: {e}")
        prompt = "Error reading metadata"
        
    return prompt, negative_prompt, other_metadata

def compute_file_hash(file_path, chunk_size=65536):
    """ファイルの内容からSHA256ハッシュを計算する（内容が同一の重複画像を検出するため）"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

DEFAULT_IMPORT_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')


def _normalize_extensions(allowed_extensions):
    """取り込み対象の拡張子タプルを整える。None のときは既定（PNG/JPG/JPEG/WEBP）。
    大文字小文字を問わずに判定できるよう小文字化し、先頭のドットを保証する。"""
    if allowed_extensions is None:
        return DEFAULT_IMPORT_EXTENSIONS
    normalized = tuple(
        (e if e.startswith('.') else '.' + e).lower()
        for e in allowed_extensions
    )
    return normalized


def import_images_from_folder(folder_path, progress_callback=None, cancel_check=None, skip_excluded=True, order="filename_asc", allow_duplicate_content=False, allowed_extensions=None):
    """フォルダ内をスキャンしてデータベースに登録する。
    サブフォルダは対象外とし、指定フォルダの直下にあるファイルのみを取り込む。
    
    progress_callback(current, total, file_name): 進捗を通知するコールバック
    cancel_check(): 呼び出すたびに True/False を返す関数。True ならその時点で処理を中断する
    order: 取り込み順序。sort_files_by_order() が受け付けるキーのいずれか。
    allow_duplicate_content: True の場合、内容が同一の画像（file_hashが既存と一致）でも別レコードとして取り込む。
    allowed_extensions: 取り込み対象とする拡張子の並び（例: ('.png', '.gif')）。None なら既定の PNG/JPG/JPEG/WEBP。
    
    戻り値は以下のキーを持つ辞書:
      inserted: 新規に登録できた件数
      duplicates: 内容が同一の画像が既に別パスで登録済みだったためスキップした件数
      skipped_existing: 既にDBに登録済みのパスだったため処理をスキップした件数（高速化のため再解析しない）
      total: フォルダ内で見つかった対象ファイルの総数
      error_log: エラーメッセージのサマリー
      cancelled: 途中でキャンセルされたかどうか
    """
    valid_extensions = _normalize_extensions(allowed_extensions)
    
    all_files = []
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.lower().endswith(valid_extensions):
                    all_files.append(entry.path)
    except OSError as e:
        return {
            "inserted": 0, "duplicates": 0, "skipped_existing": 0, "total": 0,
            "error_log": f"フォルダの読み込みに失敗しました: {e}",
            "cancelled": False,
        }
    
    if not all_files:
        return {
            "inserted": 0, "duplicates": 0, "skipped_existing": 0, "total": 0,
            "error_log": "指定されたフォルダに、取り込む対象として選択された形式の画像ファイルが見つかりませんでした（サブフォルダは対象外です）。",
            "cancelled": False,
        }
    
    all_files = sort_files_by_order(all_files, order)
    
    return _import_file_list(all_files, progress_callback=progress_callback, cancel_check=cancel_check, skip_excluded=skip_excluded, allow_duplicate_content=allow_duplicate_content)


def get_file_creation_time(path):
    """ファイルの作成日時を取得する。macOSではst_birthtimeを使用し、
    利用できない環境（Linux等、birthtimeを保持しないファイルシステム）ではst_ctime
    （メタデータ変更時刻。真の作成日時ではないが最も近い代替値）で代用する。"""
    stat_result = os.stat(path)
    return getattr(stat_result, "st_birthtime", stat_result.st_ctime)


def sort_files_by_order(file_paths, order):
    """指定された並び順でファイルパスのリストを並べ替える。
    order: 'filename_asc' / 'filename_desc' / 'created_asc' / 'created_desc' / 'modified_asc' / 'modified_desc'
    未知のキーが渡された場合はファイル名順にフォールバックする。
    """
    if order == "filename_desc":
        return sorted(file_paths, key=lambda p: os.path.basename(p), reverse=True)
    elif order == "created_asc":
        return sorted(file_paths, key=get_file_creation_time)
    elif order == "created_desc":
        return sorted(file_paths, key=get_file_creation_time, reverse=True)
    elif order == "modified_asc":
        return sorted(file_paths, key=os.path.getmtime)
    elif order == "modified_desc":
        return sorted(file_paths, key=os.path.getmtime, reverse=True)
    else:
        return sorted(file_paths, key=lambda p: os.path.basename(p))


def import_images_from_filelist(file_paths, progress_callback=None, cancel_check=None, skip_excluded=True, allow_duplicate_content=False, allowed_extensions=None):
    """ユーザーが個別に選択した画像ファイルの一覧をデータベースに登録する。
    フォルダをまるごと取り込むのではなく、選んだファイルだけを対象にする点が
    import_images_from_folder との違い。戻り値の形式は同じ。
    allowed_extensions: 取り込み対象とする拡張子の並び。None なら既定の PNG/JPG/JPEG/WEBP。
    """
    valid_extensions = _normalize_extensions(allowed_extensions)
    valid_files = [fp for fp in file_paths if fp.lower().endswith(valid_extensions)]
    
    if not valid_files:
        return {
            "inserted": 0, "duplicates": 0, "skipped_existing": 0, "total": 0,
            "error_log": "選択されたファイルの中に、取り込む対象として選択された形式の画像がありませんでした。",
            "cancelled": False,
        }
    
    return _import_file_list(valid_files, progress_callback=progress_callback, cancel_check=cancel_check, skip_excluded=skip_excluded, allow_duplicate_content=allow_duplicate_content)


def _import_file_list(file_paths, progress_callback=None, cancel_check=None, skip_excluded=True, allow_duplicate_content=False):
    """指定されたファイルパスの一覧をデータベースに登録する共通処理。
    フォルダ取り込み・個別ファイル取り込みの両方から呼ばれる。
    
    skip_excluded: True の場合、削除済み画像の除外リスト（excluded_paths）に載っている
    ファイルをスキップする（「同期」で使用）。False の場合はスキップせず、逆に
    除外リストに載っていればそこから解除して取り込む（明示的な「取り込む」操作で使用）。
    
    allow_duplicate_content: True の場合、内容が同一の画像（file_hashが既存と一致）でも
    別レコードとして取り込む。False（既定）の場合は、内容が同一の画像はスキップする。
    """
    total_count = len(file_paths)
    
    existing_paths = database.get_all_file_paths()
    excluded_paths = database.get_excluded_paths() if skip_excluded else set()
    
    inserted_count = 0
    duplicate_count = 0
    skipped_existing_count = 0
    error_messages = []
    cancelled = False
    
    for idx, file_path in enumerate(file_paths):
        if cancel_check and cancel_check():
            cancelled = True
            break
        
        if progress_callback:
            progress_callback(idx + 1, total_count, os.path.basename(file_path))
        
        if not skip_excluded:
            database.remove_excluded_path(file_path)
        
        if file_path in existing_paths:
            skipped_existing_count += 1
            continue
        
        if skip_excluded and file_path in excluded_paths:
            skipped_existing_count += 1
            continue
            
        try:
            if database.get_setting("use_sequential_naming", "1") == "1":
                _folder_dir = os.path.dirname(file_path)
                file_name = database.generate_next_sequential_name(
                    folder_name=os.path.basename(_folder_dir), folder_path=_folder_dir
                )
            else:
                file_name = os.path.splitext(os.path.basename(file_path))[0]
            prompt, neg_prompt, others = extract_ai_metadata(file_path)
            file_hash = compute_file_hash(file_path)
            
            stat = os.stat(file_path)
            file_mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            file_size = stat.st_size
            
            was_inserted = database.insert_image(
                file_path=file_path,
                file_name=file_name,
                prompt=prompt,
                negative_prompt=neg_prompt,
                other_metadata=others,
                file_mtime=file_mtime,
                file_hash=file_hash,
                file_size=file_size,
                allow_duplicate_content=allow_duplicate_content,
            )
            if was_inserted:
                inserted_count += 1
            else:
                duplicate_count += 1
        except Exception as e:
            err_msg = f"ファイル {os.path.basename(file_path)} の登録失敗: {str(e)}"
            print(err_msg)
            error_messages.append(err_msg)
            
    err_summary = "\n".join(error_messages[:5]) if error_messages else ""
    if len(error_messages) > 5:
        err_summary += f"\n他 {len(error_messages) - 5} 件のエラー"
        
    return {
        "inserted": inserted_count,
        "duplicates": duplicate_count,
        "skipped_existing": skipped_existing_count,
        "total": total_count,
        "error_log": err_summary,
        "cancelled": cancelled,
    }
