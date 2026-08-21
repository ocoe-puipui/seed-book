# -*- coding: utf-8 -*-
"""
表示言語切り替え（日本語／English）のための最小限の基盤モジュール。

設計方針:
- 外部の翻訳ライブラリ（gettext/Babel等）には依存せず、Python辞書で文字列を管理する
  （v1.3.0での検討: 対応言語が日本語・英語の2言語のみのスコープでは、辞書方式の方が
  ライセンス表記の追加やビルド成果物の増量が発生せず、既存の「アイコンをSVG文字列として
  コードに埋め込む」設計思想とも一貫性があるため）。
- 表示言語の設定は database.get_setting("language", "auto") / set_setting(...) を通じて
  永続化する（既存の theme_mode 設定と同じ仕組み）。
- "auto" が選択されている場合は、OSのロケールを見て日本語環境なら "ja"、それ以外は
  "en" にフォールバックする。
- 現時点（Step1）ではこのモジュール自体と土台の配線のみを用意し、実際の文言の移行は
  Step2以降で段階的に行う。未登録のキーを tr() で呼び出した場合は、キー名をそのまま
  返す（開発中に未翻訳箇所を発見しやすくするため）。
"""

import locale


SUPPORTED_LANGUAGES = ["ja", "en"]
DEFAULT_LANGUAGE = "ja"

HELP_TEXT_JA = """Seed Book - ヘルプ

このヘルプは簡易版です。より詳しい操作方法は、下のリンクからGitHubのマニュアルをご覧ください。
マニュアルと同じ章構成にしてあるので、詳しく知りたい項目があれば同じ番号の章を探してください。

【目次】
1. アプリのUI名称と役割
2. 基本的な使い方（取り込み・編集・検索・並び替え）
3. アルバム（仮想フォルダ）機能
4. 設定画面
5. フォルダ画像の同期ルール
6. データのバックアップ・移行
7. 既知の制限事項

【1. アプリのUI名称と役割】
・画面左側が「リスト表示エリア」、右側が「編集エリア」です
・各ボタン・欄の詳しい名称と役割はマニュアルをご覧ください

【2. 基本的な使い方】
・「フォルダを取り込む」「画像ファイルを取り込む」から画像を追加できます
・対応形式: PNG / JPG / JPEG / WEBP / GIF / BMP / TIFF（選択可）
・「同期」ボタンで、取り込み済みフォルダの増減を再スキャンできます
・画像を選択すると、右側で名前・評価・プロンプト等を編集できます
・「変更を保存」を押すまでは、編集内容は確定しません
・右クリックメニューから、画像ごとに編集をロック/解除できます
・検索欄のキーワードで、名前・ファイル名・フォルダ名・場所（パス）・評価・日時・サイズ・プロンプト等をまとめて検索できます
・スペース区切りは AND 検索（すべて含む）です
・「 OR 」で「どちらか一方」、語の先頭に「 - 」を付けると「除外」になります（例: 猫 -屋外 ）
・"..." で囲むと、スペースを含む語をひとまとまりとして検索します
・評価は「 star3 」や「 ★★★ 」で絞り込めます
・期間で絞り込むには、作成 c: ／編集 m: ／取り込み i: の書式を使います
　例) c:2026-07 （ 2026 年 7 月に作成） ／ c:2026-07-01..2026-07-31 ／ i:2026-07-30.. （以降） ／ m:..2026-07 （以前）
・大文字/小文字・全角/半角は自動的に同一視されます
・並べ替えの種類（名前・日付・評価・ファイルサイズ等）と昇順/降順は別々に切り替えられます
・グリッド表示ではサムネイルサイズ（小/中/大）を選べます
・「フォルダ別グループ表示」ボタンで、フォルダごとに画像をまとめて表示できます

【3. アルバム（仮想フォルダ）機能】
・実フォルダとは別に、画像を横断的にまとめられる「アルバム」を作成できます（1枚の画像を複数のアルバムに所属させることも可能です）
・画面左側のフォルダ/アルバム切り替えボタンで表示を切り替えます（画像リストとアルバム表示は同時には使えません）
・画像の右クリックメニュー「アルバムに追加」、またはアルバム見出しへ画像をドラッグ&ドロップして追加できます
・アルバムの見出しを右クリックすると、並び順の編集・名前の変更・すべて開く/折りたたむ・一括書き出し（連番リネーム）・アルバム専用の自動採番設定・削除ができます
・アルバム専用の自動採番ルールは、そのアルバムの一括書き出し時のみに使われます（画像の取り込み時の採番には影響しません）
・アルバムやアルバム内の画像は、Finder等へドラッグ&ドロップして書き出せます（アルバムは実フォルダを持たないため、書き出し時に一時フォルダへコピーしてから渡します）。この方法では元のファイル名のまま渡され、採番ルールは適用されません。採番ルールを適用したい場合は、見出しの右クリックメニューにある「一括で書き出す（連番でリネーム）」をご利用ください
・アルバム表示中も、検索欄で開いているアルバム内の画像を絞り込めます

【4. 設定画面】
・画面右上の歯車アイコンから開きます
・自動採番のルール、表示項目、外観モード（ダーク/ライト）、フォルダ取り込み時の順序、読書モードの既定設定、データベースの管理などを行えます
・詳しい各項目の説明はマニュアルをご覧ください

【5. フォルダ画像の同期ルール】
・リストから削除した画像は、再度「同期」しても自動では復活しません
・復活させたい場合は、「フォルダを取り込む」「画像ファイルを取り込む」で明示的に選び直してください

【6. データのバックアップ・移行】
・データベースは `~/Library/Application Support/AIImageViewer/` に保存されています（画像ファイル自体はここには含まれません）
・アプリの削除・再インストール、別のMacへの移行時にも安全にデータを引き継げます。詳しい手順はマニュアルをご覧ください

【7. 既知の制限事項】
・ドラッグ&ドロップでの取り込みは一時的に無効化中です
・フォルダ別グループ表示で、表示中の画像を含むフォルダを折りたたんだ後、画像送り（前へ/次へ）が反応しないことがあります
"""

HELP_TEXT_EN = """Seed Book - Help

This is a quick-reference help. For more detailed instructions, see the GitHub manual via the link below.
It uses the same chapter structure as the manual, so if you want more detail on a topic, look for the chapter with the same number.

[Table of Contents]
1. UI Names and Roles
2. Basic Usage (Import / Edit / Search / Sort)
3. Albums (Virtual Folders)
4. Settings
5. Folder Image Sync Rules
6. Data Backup / Migration
7. Known Limitations

[1. UI Names and Roles]
- The left side of the screen is the "List Area", and the right side is the "Edit Area"
- See the manual for detailed names and roles of each button/field

[2. Basic Usage]
- Add images using "Import Folder" or "Import Images"
- Supported formats: PNG / JPG / JPEG / WEBP / GIF / BMP / TIFF (selectable)
- Use the "Sync" button to rescan imported folders for additions/removals
- Selecting an image lets you edit its name, rating, prompt, etc. on the right
- Edits are not finalized until you click "Save Changes"
- You can lock/unlock editing per image from the right-click menu
- The search box searches across name, filename, folder name, location (path), rating, dates, size, prompt, and more
- Space-separated terms are an AND search (must contain all terms)
- Use " OR " for "either one", and prefix a word with " - " to exclude it (e.g. cat -outdoor)
- Enclose a phrase in "..." to search for it as a single term including spaces
- Ratings can be filtered with "star3" or "★★★"
- To filter by date range, use the c: (created) / m: (edited) / i: (imported) syntax
  e.g. c:2026-07 (created in July 2026) / c:2026-07-01..2026-07-31 / i:2026-07-30.. (on or after) / m:..2026-07 (on or before)
- Uppercase/lowercase and full-width/half-width characters are automatically treated as equivalent
- The sort type (name, date, rating, file size, etc.) and ascending/descending order can be toggled independently
- In grid view, you can choose the thumbnail size (small/medium/large)
- Use the "Group by Folder" button to display images grouped by folder

[3. Albums (Virtual Folders)]
- You can create "albums" that group images across different real folders (a single image can belong to multiple albums)
- Use the Folder/Album toggle on the left side to switch views (the image list and album view can't be used at the same time)
- Add images via the right-click menu "Add to Album", or by dragging images onto an album header
- Right-clicking an album header lets you: reorder albums, rename, expand/collapse all, bulk-export with sequential renaming, set an album-specific auto-numbering rule, or delete the album
- An album's auto-numbering rule only applies to that album's bulk export (it does not affect numbering at import time)
- Albums and images inside an expanded album can be dragged out to Finder etc. Since albums have no real folder, the images are copied to a temporary folder at export time. This method keeps the original filenames as-is and does not apply the naming rule; use "Export Album Images as Renamed Copies (Sequential)..." from the header's right-click menu if you want the naming rule applied
- While viewing albums, the search box still filters images within the currently open album(s)

[4. Settings]
- Open it from the gear icon in the top-right corner
- Manage auto-numbering rules, display fields, appearance mode (dark/light), folder import order, reading mode defaults, database management, and more
- See the manual for detailed descriptions of each option

[5. Folder Image Sync Rules]
- Images removed from the list do not automatically come back even if you "Sync" again
- To bring them back, explicitly re-select them via "Import Folder" or "Import Images"

[6. Data Backup / Migration]
- The database is stored at `~/Library/Application Support/AIImageViewer/` (this does not include the image files themselves)
- Your data can be safely carried over when uninstalling/reinstalling the app or moving to another Mac. See the manual for detailed steps

[7. Known Limitations]
- Drag-and-drop import is temporarily disabled
- In folder-grouped view, after collapsing a folder that contains the currently displayed image, prev/next image navigation may stop responding correctly
"""

STRINGS = {
    "ja": {
        "language.auto": "自動",
        "language.auto_tooltip": "OSの言語設定に追従します",
        "language.ja": "日本語",
        "language.en": "English",
        "language.group_title": "表示言語",
        "language.restart_notice": "再起動後に反映されます",

        "common.button.close": "閉じる",
        "common.button.cancel": "キャンセル",
        "common.button.save": "保存",
        "common.button.choose_file": "ファイルを選択...",
        "common.label.prefix": "プレフィックス",
        "common.label.digits": "桁数",
        "common.label.append": "アペンド",
        "common.label.name": "名前",
        "common.placeholder.optional_blank": "空欄でも可",
        "common.tooltip.copy": "コピー",
        "common.title.error": "エラー",
        "common.title.warning": "警告",
        "common.title.confirm": "確認",
        "common.title.saved": "保存しました",
        "common.title.save_complete": "保存完了",
        "common.title.reset_done": "リセットしました",
        "common.title.export_complete": "エクスポート完了",
        "common.title.please_select": "選択してください",
        "common.title.copy": "コピー",
        "common.title.locked": "編集ロック中",
        "common.title.no_folders": "フォルダがありません",
        "common.title.bulk_rename": "一括リネーム",
        "common.title.about_search": "検索について",
        "common.title.import_result": "取り込み結果",
        "common.title.import_cancelled": "取り込みを中断しました",
        "common.title.partial_errors": "一部エラーあり",
        "common.title.import_complete": "取り込み完了",
        "common.title.no_import_format_selected": "取り込み形式が未選択です",
        "common.title.sync": "同期",
        "common.title.sync_cancelled": "同期を中断しました",

        "dialog.csv_save_title": "CSVの保存先を選択",
        "dialog.csv_filter": "CSVファイル (*.csv)",

        "dialog.sync_history.title": "同期履歴",
        "dialog.sync_history.header_datetime": "日時",
        "dialog.sync_history.header_type": "種別",
        "dialog.sync_history.header_path": "対象パス",
        "dialog.sync_history.header_detail": "内容",
        "dialog.sync_history.empty": "記録されている同期履歴はまだありません。",
        "dialog.sync_history.export_button": "CSVに書き出す",

        "dialog.rename_table.execute_button": "この内容で実行",
        "dialog.rename_table.warning_duplicate_or_empty": "同じ名前、または空の名前があるため実行できません。修正してください。",
        "dialog.rename_table.column_current_name": "現在の名前",
        "dialog.rename_table.column_new_name": "変更後の名前",
        "dialog.rename_table.column_current_filename": "現在のファイル名",
        "dialog.rename_table.column_new_filename": "変更後のファイル名",
        "dialog.rename_table.hint_default": "行を選択すると下の欄で名前を編集できます。",
        "dialog.rename_table.hint_filename": "行を選択すると下の欄でファイル名を編集できます（拡張子は自動付加）。",
        "dialog.rename_table.hint_name_field_warning": "画像の「名前」欄（アプリ内表示名）を上書きします。実ファイル名は変更されません。",
        "dialog.rename_table.title_export": "書き出す名前を確認・編集",
        "dialog.rename_table.title_bulk": "一括リネームする名前を確認・編集",
        "dialog.rename_table.locked_skip_note": "（編集ロック中の {count} 件は対象外です）",
        "dialog.rename_table.locked_skip_note_newline": "\n（編集ロック中の {count} 件は対象外です）",
        "dialog.rename_table.naming_rule_note": "命名ルールの変更は、設定（歯車）→「自動採番・リネーム」、または見出しを右クリック→「命名ルール」から。",

        "reading.title": "読書モード",
        "reading.tooltip.theme_toggle": "読書モードの背景（ダーク/ライト）を切り替え",
        "reading.tooltip.center_align_toggle": "中央詰め表示（左右のページを画面中央で突き合わせる）を切り替え",
        "reading.tooltip.jump_first": "最初の見開きへ",
        "reading.tooltip.jump_last": "最後の見開きへ",
        "reading.button.pattern_a": " 左開き",
        "reading.tooltip.pattern_a": "左開き（左から右へ読む）に切り替え",
        "reading.button.pattern_b": " 右開き",
        "reading.tooltip.pattern_b": "右開き（右から左へ読む）に切り替え",
        "reading.indicator.pattern_a": "▶ 左開き",
        "reading.indicator.pattern_b": "◀ 右開き",
        "reading.button.exit": " 読書モードを終了（Escキーでも可）",
        "reading.tooltip.theme_toggle_to_light": "ライト表示に切り替え",
        "reading.tooltip.theme_toggle_to_dark": "ダーク表示に切り替え",
        "reading.label.load_failed": "画像を読み込めません",

        "fullscreen.title": "AI Image Viewer - 全画面プレビュー",
        "fullscreen.button.exit": " 全画面を終了（Escキーでも可）",
        "notify.title.fullscreen": "全画面プレビュー",
        "notify.fullscreen_select_first": "先に画像を選択してください。",

        "dialog.import_order.title": "取り込み順序の確認",
        "dialog.import_order.question": "フォルダ内の画像を、どの順序で取り込みますか？",
        "dialog.import_order.filename_asc": "ファイル名順（記号 > 数字 > 英字 > かな > 漢字）",
        "dialog.import_order.filename_desc": "ファイル名逆順",
        "dialog.import_order.created_asc": "作成日時順（昇順・古い順）",
        "dialog.import_order.created_desc": "作成日時順（降順・新しい順）",
        "dialog.import_order.modified_asc": "更新日時順（昇順・古い順）",
        "dialog.import_order.modified_desc": "更新日時順（降順・新しい順）",
        "dialog.import_order.allow_duplicates_checkbox": "中身が同じ画像も取り込む",
        "dialog.import_order.allow_duplicates_tooltip": "ファイル名ではなく、画像の中身（内容）が完全に一致する場合の判定です。\nオフの場合、内容が同じ画像はスキップされます。",
        "dialog.import_order.ok_button": "この順序で取り込む",

        "dialog.csv_export_options.title": "CSVエクスポート",
        "dialog.csv_export_options.question": "エクスポートする項目の範囲を選んでください。",
        "dialog.csv_export_options.radio_basic": "基本情報のみ（名前・ファイル名・場所・評価・日付など）",
        "dialog.csv_export_options.radio_full": "基本情報 + プロンプト等（プロンプト・ネガティブプロンプト・使用モデル・その他パラメータ/EXIF情報）",
        "dialog.csv_export_options.next_button": "次へ（保存先を選択）",
        "csv.header.name": "名前",
        "csv.header.filename": "ファイル名",
        "csv.header.location": "場所",
        "csv.header.rating": "評価",
        "csv.header.created_at": "作成日時",
        "csv.header.updated_at": "編集日時",
        "csv.header.imported_at": "取り込み日時",
        "csv.header.locked": "編集ロック",
        "csv.header.prompt": "プロンプト",
        "csv.header.negative_prompt": "ネガティブプロンプト",
        "csv.header.model": "使用モデル",
        "csv.header.other_params": "その他パラメータ/EXIF情報",
        "csv.value.locked": "ロック中",

        "help.title": "ヘルプ",
        "help.manual_link": 'より詳しい操作マニュアルは <a href="{MANUAL_URL}">こちら（GitHub）</a> をご覧ください。',
        "help.text": HELP_TEXT_JA,

        "dialog.folder_naming_rule.title": "フォルダ専用の自動採番 - {folder_name}",
        "dialog.folder_naming_rule.placeholder_hint": "{フォルダ名}・{日付} が使えます",
        "dialog.folder_naming_rule.override_checkbox": "このフォルダ専用のルールを使う",
        "dialog.folder_naming_rule.preview_using_global": "このフォルダはアプリ全体の既定ルールを使います（設定画面の「自動採番・リネーム」参照）。",
        "dialog.folder_naming_rule.preview_prefix": "このフォルダへの新規取り込み（次回以降）: ",
        "dialog.folder_naming_rule.prefix_empty_warning": "プレフィックスを空にすることはできません。",
        "dialog.folder_naming_rule.hint": "フォルダ「{folder_name}」専用の自動採番ルールです。新規に取り込む画像だけでなく、このフォルダの画像を一括リネーム・一括で書き出す際にも、このルールが優先して使われます。",
        "dialog.folder_naming_rule.sample_folder_name": "サンプルフォルダ",

        "dialog.folder_order.title": "フォルダの並び順を編集",
        "dialog.folder_order.intro": "ドラッグ&ドロップで、フォルダ別グループ表示での並び順を変更できます。",
        "dialog.folder_order.save_button": "この順序で保存",

        "dialog.album_naming_rule.title": "アルバム専用の自動採番 - {album_name}",
        "dialog.album_naming_rule.hint": "アルバム「{album_name}」専用の自動採番ルールです。このアルバムの画像を一括で書き出す際に、このルールが優先して使われます（アルバムは取り込み元にはならないため、新規取り込みには使われません）。",
        "dialog.album_naming_rule.override_checkbox": "このアルバム専用のルールを使う",
        "dialog.album_naming_rule.placeholder_hint": "{アルバム名}・{日付} が使えます",
        "dialog.album_naming_rule.preview_prefix": "このアルバムを一括で書き出す際の例: ",

        "dialog.properties.title_album": "アルバムのプロパティ - {name}",
        "dialog.properties.title_folder": "フォルダのプロパティ - {name}",
        "dialog.properties.name_label": "アルバムの名前",
        "dialog.properties.color_label": "色",
        "dialog.properties.color_none": "未設定",
        "dialog.properties.color_default_note": "※未設定は既定色（{color_name}）で表示",
        "dialog.properties.color_default_folder": "青",
        "dialog.properties.color_default_album": "グレー",
        "dialog.properties.naming_section_label": "自動採番ルール",
        "dialog.properties.name_empty_warning": "名前を空にすることはできません。",

        "dialog.album_order.title": "アルバムの並び順を編集",
        "dialog.album_order.intro": "ドラッグ&ドロップで、アルバム一覧での並び順を変更できます。",
        "dialog.album_order.save_button": "この順序で保存",

        "settings.title": "設定",
        "settings.button.release_notes": " リリースノート 🐈",
        "settings.tooltip.release_notes": "GitHubの更新履歴ページをブラウザで開きます",
        "settings.theme.title": "外観",
        "settings.theme.auto": "自動",
        "settings.theme.auto_tooltip": "macOSの設定に追従します",
        "settings.theme.dark": "ダーク固定",
        "settings.theme.light": "ライト固定",
        "settings.panel.standard": "標準",
        "settings.panel.standard_tooltip": "検索・リストを左に表示します",
        "settings.panel.mirrored": "反転",
        "settings.panel.mirrored_tooltip": "検索・リストを右に表示します",

        "settings.import_order.title": "取り込み順序",
        "settings.import_order.always_confirm": "毎回確認",
        "settings.import_order.auto_last_used": "前回の順序を使用",

        "settings.naming.title": "自動採番・リネーム",
        "settings.naming.auto_number_checkbox": "取り込み時に自動採番",
        "settings.naming.auto_number_checkbox_tooltip": "オン: これまで通り、新規取り込み画像の「名前」に自動採番（例: CG_00001）を付与します\nオフ: 自動採番を付与せず、実際のファイル名（拡張子を除く）をそのまま「名前」として取り込みます",
        "settings.naming.show_edit_dialog_checkbox": "リネーム前に編集画面を表示",
        "settings.naming.show_edit_dialog_checkbox_tooltip": "オン: 「選択画像を一括リネーム」「一括で書き出す」の実行前に、\n　　　生成される名前を1件ずつ確認・修正できる編集画面を開きます\nオフ: これまで通り、確認ポップアップのみで即座に実行します",
        "settings.naming.prefix_tooltip": "{フォルダ名}・{日付} が使えます（取り込み元フォルダ名／今日の日付に置き換わります）",
        "settings.naming.digits_range": "（1〜6桁）",
        "settings.naming.save_button": "ルールを保存",
        "settings.naming.save_tooltip": "プレフィックス・桁数・アペンドの設定を保存します",
        "settings.naming.reset_counter_button": "採番のリセット",
        "settings.naming.reset_counter_tooltip": "現在のプレフィックス＋アペンドの組み合わせの番号を1に戻します",
        "settings.naming.preview_prefix": "プレビュー: ",
        "settings.naming.save_done_body": "自動採番ルールを保存しました。次回以降の新規取り込みから適用されます。",
        "settings.naming.reset_counter_done_body": "採番カウンタをリセットしました。",
        "settings.naming.prefix_empty_warning": "プレフィックスを空にすることはできません。",
        "settings.naming.save_confirm.body": "新しいルールを保存してもいいですか？\n(次回以降の新規取り込みの採番から適用されます)",
        "settings.naming.reset_counter_confirm.body": "プレフィックスとアペンドの採番をリセットします。\n\n現在のプレフィックス：　{prefix}　\n現在のアペンド：　{append}　\n\n\nこの操作は取り消せません。よろしいですか？",

        "settings.display_fields.title": "表示項目",
        "settings.display_fields.title_tooltip": "プロンプト等の表示欄に追加する生成パラメータ",
        "settings.reading_defaults.title": "読書モードの既定設定",
        "settings.reading_defaults.pattern_a": "左開き",
        "settings.reading_defaults.pattern_a_tooltip": "左から右へ読みます",
        "settings.reading_defaults.pattern_b": "右開き",
        "settings.reading_defaults.pattern_b_tooltip": "右から左へ読みます",
        "settings.reading_defaults.center_align_checkbox": "既定で中央揃え表示",
        "settings.reset.button": " 設定をリセット",
        "settings.reset.tooltip": "設定を初期値（既定）に戻します（画像データは変更されません）",
        "settings.reset.done_body": "設定を初期値に戻しました。設定画面を開き直すと反映されます。",
        "settings.reset.confirm.title": "設定をリセット",
        "settings.reset.confirm.body": "【 リセットされる項目（カッコ内が既定）】\n　\n・自動採番を使用する（オン）\n・プレフィックス名とアペンド名（CG_ ／ 空欄）\n・外観モード（自動）\n・生成パラメータの表示項目（オフ）\n・フォルダ取り込み時の順序（毎回確認）\n・読書モード（左開き、中央詰め表示オフ）\n・表示モード（フォルダ）、表示形式（リスト）、サムネイルサイズ（中）、プレビューサイズ（標準）\n・編集エリアの表示状態と並び順（すべて非表示、既定の並び順）\n\n　\n\n【 リセットされない項目 】\n　\n・データベースの情報\n・保存（更新）済みの画像データの情報\n\n　\n\nこの操作は取り消せません。よろしいですか？",

        "settings.database.title": "データベース",
        "settings.database.current_label": "使用中: {db_name}",
        "settings.database.open_folder_tooltip": "データベースの保存フォルダを開く",
        "settings.database.create_button": " 作成",
        "settings.database.create_tooltip": "新しいデータベースを作成します\n（例: image_metadata2.db）",
        "settings.database.switch_button": "変更",
        "settings.database.switch_tooltip": "選択したデータベースに切り替えます（アプリが再起動します）",
        "settings.database.export_images_csv_button": " 画像一覧（CSV）",
        "settings.database.export_images_csv_tooltip": "現在使用中のデータベースの画像一覧をCSVファイルに書き出します",
        "settings.database.export_sync_history_button": " 同期履歴（CSV）",
        "settings.database.export_sync_history_tooltip": "同期時に見つからなかったフォルダ・画像や、取り込みエラーの履歴をCSVファイルに書き出します",
        "settings.database.reset_button": " データベースをリセット",
        "settings.database.reset_tooltip": "現在使用中のデータベースから、画像・フォルダの情報をすべて削除します（実際の画像ファイルは削除されません）",
        "settings.database.reset_done_body": "選択中のデータベースをリセットしました。",
        "settings.database.already_in_use_body": "既にこのデータベースを使用中です。",
        "settings.database.already_reset.title": "リセットの必要はありません",
        "settings.database.already_reset.body": "現在、データベースに登録されている画像・フォルダはありません。\nすでにリセットされた状態です。",
        "settings.database.reset_confirm.title": "選択中のデータベースをリセット　\n",
        "settings.database.reset_confirm.body": "【 リセットされる項目 】\n　\n　・選択中のデータベース内のデータ\n（画像 {images} 件・フォルダ {folders} 件など。PCの実際の画像データは削除されません）\n\n　\n\n【 リセットされない項目 】\n　\n　・更新や保存した画像ファイルやその情報\n　・アプリの設定\n　・自動採番を使用する\n　・プレフィックス名とアペンド名\n　・外観モード\n　・生成パラメータの表示項目\n　・フォルダ取り込み時の順序\n　・読書モード\n\n　\n\nこの操作は取り消せません。よろしいですか？",
        "settings.database.switch_confirm.title": "データベースの切り替え",
        "settings.database.switch_confirm.body": "「{db_name}」に切り替えるには、アプリの再起動が必要です。\n保存していない編集内容があれば失われます。\n\n切り替えて再起動しますか？",
        "settings.language.switch_confirm.title": "表示言語の切り替え",
        "settings.language.switch_confirm.body": "表示言語を「{lang}」に切り替えるには、アプリの再起動が必要です。\n保存していない編集内容があれば失われます。\n\n切り替えて再起動しますか？",
        "settings.database.create_confirm.title": "新しいデータベースの作成",
        "settings.database.create_confirm.body": "新しいデータベース「{db_name}」を作成します。\n\nよろしいですか？",
        "settings.database.create_done.title": "作成しました",
        "settings.database.create_done.body": "新しいデータベース「{db_name}」を作成しました。\n\nこのデータベースに切り替えるには、上の一覧から選択して「データベースを変更」ボタンを押してください（切り替えるとアプリが再起動します）。",
        "settings.database.no_sync_history.title": "同期履歴",
        "settings.database.no_sync_history.body": "記録されている同期履歴はまだありません。",

        "dialog.db_missing.title": "データベースが見つかりません",
        "dialog.db_missing.create_new_radio": "新しい空のデータベースを作成する",
        "dialog.db_missing.sample_data_checkbox": "サンプルデータを読み込む",
        "dialog.db_missing.choose_existing_radio": "同じ保存先フォルダ内の別のデータベースを選ぶ",
        "dialog.db_missing.choose_external_radio": "外部のバックアップファイルを指定して読み込む",
        "dialog.db_missing.no_selection": "（未選択）",
        "dialog.db_missing.select_existing_warning": "既存のデータベースを選んでください。",
        "dialog.db_missing.select_file_warning": "読み込むファイルを選んでください。",
        "dialog.db_missing.info": "既定の保存先にデータベースファイルが見つかりませんでした。\n（初回起動、またはファイルが削除された場合に表示されます）\n\nどうしますか？",
        "dialog.db_missing.browse_file_title": "バックアップデータベースファイルを選択",
        "dialog.db_missing.browse_file_filter": "SQLiteデータベース (*.db)",
        "dialog.db_missing.import_failed.title": "読み込みに失敗しました",
        "dialog.db_missing.import_done.title": "読み込みました",
        "dialog.db_missing.import_done.body": "新しいデータベースを作成しデータをコピーしました。データベース名は {db_name} です。",
        "dialog.db_missing.sample_import_failed.title": "サンプル画像の追加に失敗しました",

        "main.tooltip.toggle_all_fields_hide": "すべての編集欄・取り込み形式欄をまとめて非表示にする",
        "main.tooltip.toggle_all_fields_hide_all": "見出しも含めてすべて非表示にし、プレビューをさらに拡大する",
        "main.tooltip.toggle_all_fields_show": "すべての編集欄・取り込み形式欄をまとめて表示する",
        "main.tooltip.help": "ヘルプ（基本的な操作方法を表示します）",
        "main.tooltip.settings": "設定",
        "main.search.placeholder": "スペース区切りで複数検索可能（星は star1〜5）",
        "main.search.hint_tooltip": "検索の書き方（OR検索・除外・期間指定など）をヘルプで見る",
        "main.button.import_folder": " フォルダを取り込む",
        "main.tooltip.import_folder": "フォルダを選択し、直下の画像をまとめて取り込みます（サブフォルダは対象外）\n対応形式: PNG / JPG / JPEG / WEBP / GIF / BMP / TIFF（選択可）",
        "main.button.import_files": " 画像を取り込む",
        "main.tooltip.import_files": "画像ファイルを個別に選択して取り込みます（複数選択可）",
        "main.tooltip.sync": "取り込み済みフォルダを同期（増減を反映）\nこれまでに取り込んだフォルダを再スキャンし、新規追加された画像を取り込み、\n削除・移動された画像をリストから取り除きます。",
        "main.tooltip.expand_all_groups": "すべて展開",
        "main.tooltip.collapse_all_groups": "すべて閉じる",
        "main.tooltip.expand_collapse_empty": "対象がありません",
        "main.sort.by_name": "並べ替え：名前順",
        "main.sort.by_created": "並べ替え：作成日順",
        "main.sort.by_edited": "並べ替え：編集日順",
        "main.sort.by_imported": "並べ替え：取り込み日時順",
        "main.sort.by_rating": "並べ替え：評価順",
        "main.sort.by_filesize": "並べ替え：ファイルサイズ順",
        "main.sort.by_filename": "並べ替え：ファイル名順",
        "main.sort.by_album_name": "並べ替え：アルバム名順",
        "main.sort.no_album": "（未所属）",
        "main.label.edited_only": "編集: {value}",
        "csv.sync_history.col_datetime": "日時",
        "csv.sync_history.col_category": "種別",
        "csv.sync_history.col_target_path": "対象パス",
        "csv.sync_history.col_detail": "内容",
        "dialog.sync_result.history_button": "履歴",
        "progress.cancel_button": "キャンセル",
        "progress.import.title": "画像取り込みの進捗",
        "progress.import.initial_scan": "画像をスキャン中...",
        "progress.import.initial_importing": "画像を取り込み中...",
        "progress.sync.title": "同期の進捗",
        "progress.sync.initial": "フォルダを同期中...",
        "progress.label.processing": "処理中 ({current} / {total} 件):\n{file_name}",
        "progress.label.scanning_folder": "フォルダをスキャン中:\n{folder}",
        "main.tooltip.sync_button": "取り込み済みフォルダを同期（増減を反映）\nこれまでに取り込んだフォルダを再スキャンし、新規追加された画像を取り込み、\n削除・移動された画像をリストから取り除きます。",
        "main.preview_info.created": "作成: {value}",
        "main.preview_info.edited": "（編集: {value}）",
        "main.preview_info.imported": "取り込み: {value}",
        "main.preview_info.imported_none": "取り込み: —",
        "main.preview_info.rating": "評価: {stars}",
        "main.preview_info.rating_none": "評価: —",
        "main.preview_info.size": "サイズ: {value}",
        "main.preview_info.albums": "アルバム: {names}",
        "main.preview_info.albums_none": "アルバム: —",
        "main.preview_info.selected_count": "{count}件選択中",
        "main.fullscreen.name_filename": "名前: {name}　ファイル名: {filename}",
        "main.tooltip.sort_direction_asc": "並び順を昇順/降順で切り替え（現在: 昇順）",
        "main.tooltip.sort_direction_desc": "並び順を昇順/降順で切り替え（現在: 降順）",
        "main.tooltip.view_toggle_to_grid": "グリッド表示に切替",
        "main.tooltip.view_toggle_to_list": "リスト表示に切替",
        "main.tooltip.group_toggle_enable": "フォルダ別にグループ表示（有効にすると、フォルダの見出しを右クリックして並び順を変更できます）",
        "main.tooltip.group_toggle_disable": "グループ表示を解除",
        "main.tooltip.view_toggle_disabled_grouped": "フォルダ別グループ表示中はグリッド表示に切り替えられません",
        "main.tooltip.group_toggle_disabled_grid": "フォルダ別グループ表示はリスト表示でのみ利用できます",
        "main.tooltip.view_toggle_disabled_album": "アルバム表示中はグリッド表示に切り替えられません",
        "main.tooltip.group_toggle_disabled_album": "アルバム表示中はフォルダ別グループ表示を切り替えられません",
        "main.button.grid_small": " 小",
        "main.tooltip.grid_small": "サムネイルを小さいサイズで表示",
        "main.button.grid_medium": " 中",
        "main.tooltip.grid_medium": "サムネイルを中くらいのサイズで表示",
        "main.button.grid_large": " 大",
        "main.tooltip.grid_large": "サムネイルを大きいサイズで表示",
        "main.label.empty_state": "画像を取り込んでください",
        "main.label.drag_hover": "画像またはフォルダをここにドラッグ&ドロップしてください",
        "main.label.no_search_results": "検索結果は 0 件です",
        "main.album_header.note_collapsed_search": "（折りたたみ中は検索対象外）",
        "main.folder_header.note_collapsed_search": "（折りたたみ中は検索対象外）",
        "main.label.gif_note": "※ GIF は1コマ目を静止画として表示",
        "main.tooltip.format_gif": "GIF は現行バージョンでは再生できません（1コマ目を静止画として表示します）",
        "main.tooltip.format_tiff": "TIFF（.tif / .tiff）に対応します",
        "main.button.delete_selected": " 選択した画像をリストから削除",
        "main.button.delete_selected_with_count": " {count} 件の画像をリストから削除",
        "main.button.delete_none": " 削除",
        "main.button.delete_folder": " フォルダ「{folder_name}」を削除",
        "main.button.delete_album": " アルバム「{album_name}」を削除",
        "main.button.remove_from_album_selected": " アルバムから削除",
        "main.button.remove_from_album_count": " {count} 件をアルバムから削除",
        "main.tooltip.delete": "リストから除外します（パソコン上の画像ファイルは削除されません）",
        "main.tooltip.theme_toggle": "外観モードを切り替え（現在: {mode}）",
        "main.tooltip.panel_flip_mirrored": "パネル配置を反転（現在: 反転表示）",
        "main.tooltip.panel_flip_standard": "パネル配置を反転（現在: 標準表示）",
        "main.tooltip.language_toggle": "表示言語を切り替え（現在: {lang}）",

        "metadata.filename.header": "ファイル名",
        "metadata.filename.tooltip": "パソコン上の実際のファイル名です。変更すると「変更を保存」時にファイル自体の名前が変わります。",
        "metadata.filename.multi_selected": "[複数選択中]",
        "metadata.name.header": "名前",
        "metadata.name.tooltip": "実際のファイル名とは別の、アプリ内だけの名前です。自由に変更・重複可能なので、検索用のタグのような使い方もできます（初期値は自動採番）。",
        "metadata.name.multi_selected": "[複数選択中 - 評価のみ変更可能]",
        "metadata.preview.button_hidden": " 非表示",
        "metadata.preview.tooltip_hidden": "プレビューを非表示にして、メタデータ編集エリアを広げます",
        "metadata.preview.button_standard": " 標準",
        "metadata.preview.tooltip_standard": "プレビューを標準サイズで表示",
        "metadata.preview.button_compact": " コンパクト",
        "metadata.preview.tooltip_compact": "プレビューをコンパクトサイズで表示",
        "metadata.preview.button_fullscreen": " 全画面",
        "metadata.preview.tooltip_fullscreen": "プレビューを全画面で表示",
        "metadata.preview.select_prompt": "画像を選択してください",
        "metadata.preview.load_failed": "画像の読み込みに失敗しました",
        "metadata.tooltip.reading_mode": "読書モード（見開き表示）\n「フォルダ別グループ表示」を有効にしている時のみ利用できます",
        "metadata.tooltip.preview_pin_off": "プレビューを固定表示にする\n（編集欄をスクロールしてもプレビューが追従しなくなります）",
        "metadata.tooltip.preview_pin_on": "プレビューの固定表示を解除する\n（編集欄と一緒にスクロールするようになります）",
        "metadata.tooltip.star_rating": "クリックで評価（星0〜5）を設定できます。評価済みの星をもう一度クリックすると解除されます。",
        "metadata.tooltip.prev_image": "前の画像へ",
        "metadata.tooltip.next_image": "次の画像へ",
        "metadata.button.save": " 変更を保存",
        "metadata.button.save_plain": "変更を保存",
        "metadata.button.save_selected_ratings": " 選択した {count} 件の評価（★）を一括保存",
        "metadata.button.saved_confirmation": " 保存しました",
        "metadata.tooltip.save_locked": "この画像はロックされているため編集できません",
        "metadata.tooltip.unsaved": "未保存の変更があります",
        "metadata.tooltip.section_move_up": "この項目を1つ上へ移動",
        "metadata.tooltip.section_move_down": "この項目を1つ下へ移動",
        "metadata.button.save_as_new": " 別名で保存",
        "metadata.tooltip.save_as_new": "オリジナルは変更せず、現在の内容（表示名・評価・プロンプト等）を持つ\n新しいコピーとして、指定した場所に保存します。",
        "metadata.button.slideshow_idle": "▶  スライドショー",
        "metadata.button.slideshow_start_action": "▶  スライドショー開始",
        "metadata.button.slideshow_stop": "■  スライドショー停止",
        "metadata.tooltip.slideshow": "自動で画像を再生するスライドショーを開始します",
        "metadata.tooltip.speed": "再生速度を変更（0.5倍〜2倍）",
        "metadata.memo.header": "メモ",
        "metadata.memo.placeholder": "検索対象になります",
        "metadata.model.header": "使用モデル / チェックポイント",
        "metadata.prompt.header": "プロンプト",
        "metadata.negative_prompt.header": "ネガティブプロンプト",
        "metadata.other_params.header": "その他パラメータ / メタデータ / EXIF情報",
        "metadata.tooltip.section_toggle_show": "編集フォームを表示する",
        "metadata.tooltip.section_toggle_hide": "編集フォームを非表示にする",
        "metadata.tooltip.clear_field": "この欄をクリア（「変更を保存」を押すまでは確定しません）",
        "metadata.tooltip.copy_seed": "Seedの値をコピー",

        "menu.reveal_finder": "Finderで表示",
        "menu.reveal_explorer": "エクスプローラーで表示",
        "menu.reveal_file_manager": "ファイルマネージャーで表示",
        "menu.unlock_edit": "編集ロックを解除",
        "menu.lock_edit": "編集をロック",
        "menu.copy_file": "ファイルをコピー",
        "menu.copy_file_path": "ファイルパスをコピー",
        "menu.bulk_rename": "選択画像を一括リネーム（連番）...",
        "menu.bulk_copy_renamed": "選択画像を一括で書き出す（連番でリネーム）...",
        "menu.folder_edit_order": "フォルダの並び順を編集...",
        "menu.folder_copy_renamed": "フォルダ内の画像を一括で書き出す（連番でリネーム）...",
        "menu.folder_naming_rule": "フォルダ専用の自動採番を設定...",
        "menu.folder_properties": "プロパティ...",
        "menu.folder_delete": "フォルダをデータベースから削除...",
        "menu.expand_all_folders": "すべてのフォルダを開く",
        "menu.collapse_all_folders": "すべてのフォルダを折りたたむ",
        "menu.add_to_album": "アルバムに追加",
        "menu.add_to_album_new": "新しいアルバムを作成...",
        "menu.remove_from_album": "このアルバムから削除",
        "menu.delete_from_list": "リストから削除...",
        "browse_mode.button.images": "フォルダ",
        "browse_mode.button.albums": "アルバム",
        "browse_mode.tooltip.images": "通常の画像リスト表示に切り替える",
        "browse_mode.tooltip.albums": "アルバム表示に切り替える",
        "album.button.create": "アルバムを作成する",
        "album.tooltip.add": "新しいアルバムを作成",
        "album.dialog.create.title": "新しいアルバム",
        "album.dialog.create.label": "アルバム名を入力してください",
        "album.dialog.create.naming_hint": "このアルバムの画像を一括で書き出す際の自動採番ルールです（作成後も見出しの右クリックメニューから変更できます）。オフの場合はアプリ全体の既定ルールを使います。",
        "album.dialog.create.preview_prefix_rename": "追加する画像はこの名前にリネームされます: ",
        "album.dialog.create.confirm_button": "作成",
        "album.dialog.create.name_empty_warning": "アルバム名を入力してください。",
        "album.dialog.rename.title": "アルバム名の変更",
        "album.dialog.rename.label": "新しいアルバム名を入力してください",
        "album.menu.rename": "名前を変更",
        "album.menu.delete": "アルバムを削除",
        "album.confirm.delete.title": "アルバムの削除",
        "album.confirm.delete.body": "アルバム「{name}」を削除しますか？\n（アルバム内の画像自体は削除されません）",
        "album.confirm.remove_images.title": "アルバムから削除",
        "album.confirm.remove_images.body": "選択された {count} 件をこのアルバムから外しますか？\n（画像自体はアプリのリストからは削除されず、他のアルバムへの所属もそのまま残ります）",
        "album.notify.added": "{count} 件の画像を「{name}」に追加しました",
        "album.notify.added_count": "{count} 件の画像をアルバムに追加しました",
        "album.notify.removed_count": "{count} 件の画像をアルバムから外しました",
        "album.notify.naming_rule_saved": "「{name}」専用の自動採番を保存しました",
        "menu.album_edit_order": "アルバムの並び順を編集...",
        "menu.album_copy_renamed": "アルバム内の画像を一括で書き出す（連番でリネーム）...",
        "menu.album_naming_rule": "アルバム専用の自動採番を設定...",
        "menu.album_properties": "プロパティ...",
        "menu.album_delete": "アルバムを削除...",
        "menu.expand_all_albums": "すべてのアルバムを開く",
        "menu.collapse_all_albums": "すべてのアルバムを折りたたむ",

        "status.files_copied": "{count} 件のファイルをコピーしました（Cmd+V / Ctrl+V で貼り付け可能）",
        "status.file_path_copied": "ファイルパスをコピーしました",
        "status.sequence_rename_export_done": "{context}{count} 件を連番でリネームして書き出しました。",
        "status.sequence_rename_export_errors_suffix": " 失敗 {count} 件（詳細はツールチップ参照）",
        "status.sequence_rename_export_error_item": "{name} → {new_name}（同名ファイルが既に存在）",
        "status.sequence_rename_export_error_item_exc": "{name}: {error}",
        "status.bulk_rename_done": "{count} 件の「名前」欄を変更しました。",
        "status.rating_saved_with_locked_skipped": "ロック中の {count} 件を除き、評価を保存しました",
        "status.rating_saved": "評価を保存しました",
        "status.changes_saved": "変更を保存しました",
        "main.library_status": "フォルダ：{folders}　画像：{images}　最新の同期：{last_sync}",
        "main.library_status.not_synced": "未同期",
        "main.library_status_album": "アルバム：{albums}　画像：{images}",
        "main.folder_header.tooltip_collapsed": "クリックして画像一覧を表示・ドラッグでフォルダごとコピー（元のファイル名のまま。採番ルールを使うには右クリック「一括で書き出す」）",
        "main.folder_header.tooltip_expanded": "クリックして画像一覧を折りたたむ・ドラッグでフォルダごとコピー（元のファイル名のまま。採番ルールを使うには右クリック「一括で書き出す」）",
        "album.header.tooltip_collapsed": "クリックして画像一覧を表示・ドラッグでFinder等へ書き出し（元のファイル名のまま。採番ルールを使うには右クリック「一括で書き出す」）",
        "album.header.tooltip_expanded": "クリックして画像一覧を折りたたむ・ドラッグでFinder等へ書き出し（元のファイル名のまま。採番ルールを使うには右クリック「一括で書き出す」）",
        "main.list_item.location_line": "場所: .../{parent_dir}/",
        "main.list_item.locked_note": "🔒 編集ロック中\n",
        "main.button.delete_selected_count": " {count} 件の画像をリストから削除",
        "main.button.save_selected_ratings": " 選択した {count} 件の評価（★）を一括保存",
        "main.multi_select.filename_placeholder": "[複数選択中]",
        "main.multi_select.name_placeholder": "[複数選択中 - 評価のみ変更可能]",
        "common.title.sync_complete": "同期完了",
        "common.title.sync_complete_partial_errors": "同期完了（一部エラーあり）",
        "confirm.delete_locked_blocked.body": "選択中に編集ロックされた画像が {count} 件含まれているため、削除できません。\n右クリックメニューからロックを解除してから、もう一度お試しください。",
        "confirm.delete_images.title": "画像の削除確認",
        "confirm.delete_images.body": "選択された {count} 件の画像をアプリのリストから削除しますか? パソコン内のオリジナル画像ファイルは削除されません。",
        "dialog.choose_export_dest_title": "書き出し先フォルダを選択",
        "dialog.export_subfolder.title": "サブフォルダを作成しますか？",
        "dialog.export_subfolder.body": "書き出し先の中に「{name}」という名前のフォルダを作成し、その中に書き出しますか？",
        "dialog.export_subfolder.button_create": "フォルダを作成し書き出す",
        "dialog.export_subfolder.button_direct": "直接書き出す",
        "notify.export_subfolder_create_failed": "サブフォルダの作成に失敗しました:\n{error}",
        "confirm.bulk_rename_selected.title": "選択画像を一括リネーム",
        "confirm.bulk_rename_selected.body": "{count} 件の画像の「名前」欄を、設定済みの自動採番ルールで一括変更しますか？\nパソコン上の実ファイル名は変更されません。\n\n例: {preview}{skip_note}",
        "confirm.folder_delete.title": "フォルダをデータベースから削除",
        "confirm.folder_delete.body": "フォルダ「{folder_name}」（画像 {count} 件）をデータベースから削除しますか？\n\n・画像リストから表示されなくなり、以後の同期（自動再スキャン）の対象からも外れます\n・ディスク上の実ファイルは削除されません\n・改めて「フォルダを取り込む」で取り込み直せば、再び同期対象になります",

        "progress.import_title": "画像取り込みの進捗",
        "progress.sync_title": "同期の進捗",
        "progress.processing_item": "処理中 ({current} / {total} 件):\n{file_name}",
        "progress.scanning_folder": "フォルダをスキャン中:\n{folder}",

        "notify.csv_write_failed": "CSVの書き込みに失敗しました:\n{error}",
        "notify.sync_history_export_done": "{count} 件の同期履歴をCSVに書き出しました。\n\n{save_path}",
        "notify.export_images_done": "{count} 件の画像情報をCSVに書き出しました。\n\n{save_path}",
        "notify.title.sync_history": "同期履歴",
        "notify.db_load_failed": "データベースの読み込みに失敗しました:\n{error}",
        "notify.save_locked_body": "この画像はロックされているため、変更を保存できません。\n右クリックメニューからロックを解除してください。",
        "notify.name_empty_warning": "名前を空にすることはできません。",
        "notify.filename_empty_warning": "ファイル名を空にすることはできません。",
        "notify.original_file_missing": "元のファイルが見つからないため、ファイル名は変更できませんでした。",
        "notify.filename_conflict": "同じ名前のファイルが既に存在するため、ファイル名は変更できませんでした:\n{new_filename}\n\n他の変更内容は保存されませんでした。",
        "notify.rename_failed": "ファイル名の変更に失敗しました:\n{error}\n\n他の変更内容は保存されませんでした。",
        "notify.select_image_warning": "画像を選択してください。",
        "notify.original_image_missing": "元の画像ファイルが見つかりません。",
        "notify.display_name_empty_warning": "ファイル表示名を空にすることはできません。",
        "notify.file_copy_failed": "ファイルのコピーに失敗しました:\n{error}",
        "notify.duplicate_path_warning": "指定した保存先には既に同じパスの画像が登録されています。",
        "notify.save_as_new_done": "新しいコピーを保存し、DBに登録しました:\n{dest_path}",
        "notify.folder_path_unresolved": "フォルダの実パスを特定できませんでした。",
        "notify.no_images_in_db": "現在、データベースに取り込まれている画像がありません。",
        "notify.copy_target_not_found": "コピー対象の画像が見つかりませんでした。",
        "notify.bulk_rename_all_locked": "選択した画像はすべて編集ロック中のため、リネームできません。",
        "notify.file_manager_open_failed": "ファイルマネージャーを開けませんでした:\n{error}",
        "notify.search_all_collapsed": "すべてのフォルダが折りたたまれています。\n折りたたみ中のフォルダは検索対象外です。検索したいフォルダを開いてください。",
        "notify.search_all_albums_collapsed": "すべてのアルバムが折りたたまれています。\n折りたたみ中のアルバムは検索対象外です。検索したいアルバムを開いてください。",
        "notify.body.cancelled_with_summary": "キャンセルされたため処理を中断しました。\n\n{summary}",
        "sync.error_summary_suffix": "\n\n【発生したエラー内容】\n{error_log}",
        "notify.import_partial_errors_body": "処理完了しました。\n\n{summary}\n\n【発生したエラー内容】\n{error_log}",
        "notify.import_complete_body": "すべての画像が正常に取り込まれました！\n\n{summary}",
        "notify.no_import_format_selected_body": "リスト下部の形式チェックボックス（PNG・JPG など）で、取り込みたい形式にチェックを入れてください。",
        "notify.no_supported_images_found": "対応する画像ファイル（PNG/JPG/WEBP）が見つかりませんでした。",
        "notify.import_drag_drop_done_body": "ドラッグ&ドロップで画像を取り込みました！\n\n{summary}",
        "notify.sync_no_folders": "まだ取り込んだフォルダがありません。\n先に「フォルダを取り込む」を実行してください。",
        "import.summary.inserted": "新規登録: {count} 件",
        "import.summary.duplicates": "重複によりスキップ: {count} 件",
        "import.summary.total": "全体: {count} 件",
        "sync.summary.target_folders": "対象フォルダ: {count} 件",
        "sync.summary.inserted": "新規追加: {count} 件",
        "sync.summary.duplicates_with_scanned": "重複によりスキップ: {duplicates} 件（スキャン合計: {scanned} 件）",
        "sync.summary.removed": "削除・移動を検出: {count} 件",
        "sync.summary.missing_folders_warning": "\n\n⚠ 以下のフォルダが見つからなかったため、スキャンをスキップしました:\n{folders}",
        "sync.summary.missing_folders_note": "\n（このフォルダについては、見つかるようになるまで次回以降のポップアップ表示を省略します。詳細は「履歴」から確認できます）",
    },
    "en": {
        "language.auto": "Auto",
        "language.auto_tooltip": "Follows the OS language setting",
        "language.ja": "Japanese",
        "language.en": "English",
        "language.group_title": "Language",
        "language.restart_notice": "Restart required to apply.",

        # --- Common (shared buttons/titles used in multiple places) ---
        "common.button.close": "Close",
        "common.button.cancel": "Cancel",
        "common.button.save": "Save",
        "common.button.choose_file": "Choose File...",
        "common.label.prefix": "Prefix",
        "common.label.digits": "Digits",
        "common.label.append": "Append",
        "common.label.name": "Name",
        "common.placeholder.optional_blank": "Optional",
        "common.tooltip.copy": "Copy",
        "common.title.error": "Error",
        "common.title.warning": "Warning",
        "common.title.confirm": "Confirm",
        "common.title.saved": "Saved",
        "common.title.save_complete": "Save Complete",
        "common.title.reset_done": "Reset Complete",
        "common.title.export_complete": "Export Complete",
        "common.title.please_select": "Please Select",
        "common.title.copy": "Copy",
        "common.title.locked": "Locked for Editing",
        "common.title.no_folders": "No Folders",
        "common.title.bulk_rename": "Bulk Rename",
        "common.title.about_search": "About Search",
        "common.title.import_result": "Import Result",
        "common.title.import_cancelled": "Import Cancelled",
        "common.title.partial_errors": "Some Errors Occurred",
        "common.title.import_complete": "Import Complete",
        "common.title.no_import_format_selected": "No Import Format Selected",
        "common.title.sync": "Sync",
        "common.title.sync_cancelled": "Sync Cancelled",

        # --- Common CSV file dialogs ---
        "dialog.csv_save_title": "Choose CSV Save Location",
        "dialog.csv_filter": "CSV Files (*.csv)",

        # --- Sync history dialog ---
        "dialog.sync_history.title": "Sync History",
        "dialog.sync_history.header_datetime": "Date/Time",
        "dialog.sync_history.header_type": "Type",
        "dialog.sync_history.header_path": "Target Path",
        "dialog.sync_history.header_detail": "Details",
        "dialog.sync_history.empty": "No sync history has been recorded yet.",
        "dialog.sync_history.export_button": "Export to CSV",

        # --- Sequential rename preview table dialog ---
        "dialog.rename_table.execute_button": "Run With These Names",
        "dialog.rename_table.warning_duplicate_or_empty": "Cannot proceed: some names are duplicated or empty. Please fix them.",
        "dialog.rename_table.column_current_name": "Current Name",
        "dialog.rename_table.column_new_name": "New Name",
        "dialog.rename_table.column_current_filename": "Current Filename",
        "dialog.rename_table.column_new_filename": "New Filename",
        "dialog.rename_table.hint_default": "Select a row to edit its name below.",
        "dialog.rename_table.hint_filename": "Select a row to edit its filename below (extension added automatically).",
        "dialog.rename_table.hint_name_field_warning": "This overwrites each image's \"Name\" field (in-app display name). Filenames on disk are unchanged.",
        "dialog.rename_table.title_export": "Confirm/Edit Names to Export",
        "dialog.rename_table.title_bulk": "Confirm/Edit Names to Bulk Rename",
        "dialog.rename_table.locked_skip_note": " ({count} locked item(s) excluded)",
        "dialog.rename_table.locked_skip_note_newline": "\n({count} locked item(s) excluded)",
        "dialog.rename_table.naming_rule_note": "To change the naming rule: Settings (gear) → \"Auto-Numbering / Rename\", or right-click a header → \"Naming Rule\".",

        # --- Reading mode (spread view) ---
        "reading.title": "Reading Mode",
        "reading.tooltip.theme_toggle": "Toggle reading mode background (dark/light)",
        "reading.tooltip.center_align_toggle": "Toggle center alignment (align left/right pages at the screen center)",
        "reading.tooltip.jump_first": "Go to first spread",
        "reading.tooltip.jump_last": "Go to last spread",
        "reading.button.pattern_a": " Left-bound",
        "reading.tooltip.pattern_a": "Switch to left-bound (read left to right)",
        "reading.button.pattern_b": " Right-bound",
        "reading.tooltip.pattern_b": "Switch to right-bound (read right to left)",
        "reading.indicator.pattern_a": "▶ Left-bound",
        "reading.indicator.pattern_b": "◀ Right-bound",
        "reading.button.exit": " Exit Reading Mode (Esc also works)",
        "reading.tooltip.theme_toggle_to_light": "Switch to light display",
        "reading.tooltip.theme_toggle_to_dark": "Switch to dark display",
        "reading.label.load_failed": "Unable to load image",

        # --- Fullscreen preview ---
        "fullscreen.title": "AI Image Viewer - Fullscreen Preview",
        "fullscreen.button.exit": " Exit Fullscreen (Esc also works)",
        "notify.title.fullscreen": "Fullscreen Preview",
        "notify.fullscreen_select_first": "Please select an image first.",

        # --- Import order confirmation dialog ---
        "dialog.import_order.title": "Confirm Import Order",
        "dialog.import_order.question": "In what order should the images in the folder be imported?",
        "dialog.import_order.filename_asc": "By filename (symbols > numbers > letters > kana > kanji)",
        "dialog.import_order.filename_desc": "By filename (reverse)",
        "dialog.import_order.created_asc": "By creation date (ascending, oldest first)",
        "dialog.import_order.created_desc": "By creation date (descending, newest first)",
        "dialog.import_order.modified_asc": "By modified date (ascending, oldest first)",
        "dialog.import_order.modified_desc": "By modified date (descending, newest first)",
        "dialog.import_order.allow_duplicates_checkbox": "Also import images with identical content",
        "dialog.import_order.allow_duplicates_tooltip": "This checks whether the image content (not the filename) is exactly identical.\nWhen off, images with identical content are skipped.",
        "dialog.import_order.ok_button": "Import in This Order",

        # --- CSV export scope dialog ---
        "dialog.csv_export_options.title": "Export CSV",
        "dialog.csv_export_options.question": "Choose which fields to include in the export.",
        "dialog.csv_export_options.radio_basic": "Basic info only (name, filename, location, rating, dates, etc.)",
        "dialog.csv_export_options.radio_full": "Basic info + prompt data (prompt, negative prompt, model used, other parameters/EXIF info)",
        "dialog.csv_export_options.next_button": "Next (Choose Save Location)",
        "csv.header.name": "Name",
        "csv.header.filename": "Filename",
        "csv.header.location": "Location",
        "csv.header.rating": "Rating",
        "csv.header.created_at": "Created",
        "csv.header.updated_at": "Edited",
        "csv.header.imported_at": "Imported",
        "csv.header.locked": "Locked",
        "csv.header.prompt": "Prompt",
        "csv.header.negative_prompt": "Negative Prompt",
        "csv.header.model": "Model",
        "csv.header.other_params": "Other Parameters/EXIF Info",
        "csv.value.locked": "Locked",

        # --- Help dialog ---
        "help.title": "Help",
        "help.manual_link": 'For more detailed instructions, see <a href="{MANUAL_URL}">the manual on GitHub</a>.',
        "help.text": HELP_TEXT_EN,

        # --- Folder-specific auto-numbering dialog ---
        "dialog.folder_naming_rule.title": "Folder-Specific Auto-Numbering - {folder_name}",
        "dialog.folder_naming_rule.placeholder_hint": "You can use {folder name} and {date}",
        "dialog.folder_naming_rule.override_checkbox": "Use a rule specific to this folder",
        "dialog.folder_naming_rule.preview_using_global": "This folder uses the app-wide default rule (see \"Auto-Numbering / Renaming\" in Settings).",
        "dialog.folder_naming_rule.preview_prefix": "New imports to this folder (from now on): ",
        "dialog.folder_naming_rule.prefix_empty_warning": "The prefix cannot be empty.",
        "dialog.folder_naming_rule.hint": "A folder-specific auto-numbering rule for \"{folder_name}\". This rule takes priority not only for newly imported images, but also when bulk-renaming or bulk-exporting images in this folder.",
        "dialog.folder_naming_rule.sample_folder_name": "Sample Folder",

        # --- Folder order dialog ---
        "dialog.folder_order.title": "Edit Folder Order",
        "dialog.folder_order.intro": "Drag and drop to change the order of folders in folder-grouped display.",
        "dialog.folder_order.save_button": "Save This Order",

        "dialog.album_naming_rule.title": "Album-Specific Auto-Numbering - {album_name}",
        "dialog.album_naming_rule.hint": "An album-specific auto-numbering rule for \"{album_name}\". This rule takes priority when bulk-exporting images from this album (it is never used for new imports, since albums cannot be an import source).",
        "dialog.album_naming_rule.override_checkbox": "Use a rule specific to this album",
        "dialog.album_naming_rule.placeholder_hint": "{album name} and {date} are available",
        "dialog.album_naming_rule.preview_prefix": "Example when bulk-exporting this album: ",

        # --- Properties dialog (v1.4.1 stage 5+. Consolidates "Rename" and "Set Auto-Numbering" for folders/albums) ---
        "dialog.properties.title_album": "Album Properties - {name}",
        "dialog.properties.title_folder": "Folder Properties - {name}",
        "dialog.properties.name_label": "Album Name",
        "dialog.properties.color_label": "Color",
        "dialog.properties.color_none": "None",
        "dialog.properties.color_default_note": "* \"None\" shows as the default ({color_name})",
        "dialog.properties.color_default_folder": "blue",
        "dialog.properties.color_default_album": "gray",
        "dialog.properties.naming_section_label": "Auto-Numbering Rule",
        "dialog.properties.name_empty_warning": "The name cannot be empty.",

        "dialog.album_order.title": "Edit Album Order",
        "dialog.album_order.intro": "Drag and drop to change the order of albums in the album list.",
        "dialog.album_order.save_button": "Save This Order",

        # --- Settings dialog: overall / appearance ---
        "settings.title": "Settings",
        "settings.button.release_notes": " Release Notes 🐈",
        "settings.tooltip.release_notes": "Opens the GitHub release history page in your browser",
        "settings.theme.title": "Appearance",
        "settings.theme.auto": "Auto",
        "settings.theme.auto_tooltip": "Follows the macOS setting",
        "settings.theme.dark": "Always Dark",
        "settings.theme.light": "Always Light",
        "settings.panel.standard": "Standard",
        "settings.panel.standard_tooltip": "Search/list shown on the left",
        "settings.panel.mirrored": "Mirrored",
        "settings.panel.mirrored_tooltip": "Search/list shown on the right",

        # --- Settings dialog: folder import order ---
        "settings.import_order.title": "Import Order",
        "settings.import_order.always_confirm": "Always ask",
        "settings.import_order.auto_last_used": "Use last order",

        # --- Settings dialog: auto-numbering / renaming ---
        "settings.naming.title": "Auto-Numbering / Renaming",
        "settings.naming.auto_number_checkbox": "Auto-number on import",
        "settings.naming.auto_number_checkbox_tooltip": "On: As before, newly imported images get an auto-numbered \"Name\" (e.g. CG_00001)\nOff: No auto-numbering; the actual filename (without extension) is used as the \"Name\" as-is",
        "settings.naming.show_edit_dialog_checkbox": "Edit before renaming",
        "settings.naming.show_edit_dialog_checkbox_tooltip": "On: Before running \"Bulk Rename Selected\" or \"Bulk Export\",\n      opens an edit screen to review/adjust each generated name\nOff: As before, runs immediately after just a confirmation popup",
        "settings.naming.prefix_tooltip": "You can use {folder name} and {date} (replaced with the source folder name / today's date)",
        "settings.naming.digits_range": "(1-6 digits)",
        "settings.naming.save_button": "Save Rule",
        "settings.naming.save_tooltip": "Saves the prefix, digit count, and append settings",
        "settings.naming.reset_counter_button": "Reset Numbering",
        "settings.naming.reset_counter_tooltip": "Resets the number for the current prefix + append combination back to 1",
        "settings.naming.preview_prefix": "Preview: ",
        "settings.naming.save_done_body": "The auto-numbering rule has been saved. It will apply to new imports from now on.",
        "settings.naming.reset_counter_done_body": "The numbering counter has been reset.",
        "settings.naming.prefix_empty_warning": "The prefix cannot be empty.",
        "settings.naming.save_confirm.body": "Save the new rule?\n(It will apply to numbering for new imports from now on.)",
        "settings.naming.reset_counter_confirm.body": "This resets the numbering for the current prefix and append.\n\nCurrent prefix:  {prefix}  \nCurrent append:  {append}  \n\n\nThis cannot be undone. Are you sure?",

        # --- Settings dialog: display fields / reading mode defaults / reset ---
        "settings.display_fields.title": "Display Fields",
        "settings.display_fields.title_tooltip": "Generation parameters to add below the model field",
        "settings.reading_defaults.title": "Reading Mode Defaults",
        "settings.reading_defaults.pattern_a": "Left-bound",
        "settings.reading_defaults.pattern_a_tooltip": "Read left to right",
        "settings.reading_defaults.pattern_b": "Right-bound",
        "settings.reading_defaults.pattern_b_tooltip": "Read right to left",
        "settings.reading_defaults.center_align_checkbox": "Center-align by default",
        "settings.reset.button": " Reset Settings",
        "settings.reset.tooltip": "Resets settings to their defaults (image data is not affected)",
        "settings.reset.done_body": "Settings have been reset to their defaults. Reopen the Settings dialog to see the change.",
        "settings.reset.confirm.title": "Reset Settings",
        "settings.reset.confirm.body": "[ Items that will be reset (defaults in parentheses) ]\n \n- Use auto-numbering (On)\n- Prefix and append names (CG_ / blank)\n- Appearance mode (Auto)\n- Generation parameter display fields (Off)\n- Folder import order (Ask every time)\n- Reading mode (Left-bound, center-align off)\n- Browse mode (Folders), view mode (List), grid tile size (Medium), preview size (Standard)\n- Edit area display state and section order (all hidden, default order)\n\n \n\n[ Items that will NOT be reset ]\n \n- Database information\n- Saved/updated image data information\n\n \n\nThis cannot be undone. Are you sure?",

        # --- Settings dialog: database ---
        "settings.database.title": "Database",
        "settings.database.current_label": "In use: {db_name}",
        "settings.database.open_folder_tooltip": "Open the database's storage folder",
        "settings.database.create_button": " Create",
        "settings.database.create_tooltip": "Creates a new database\n(e.g. image_metadata2.db)",
        "settings.database.switch_button": "Switch",
        "settings.database.switch_tooltip": "Switches to the selected database (the app will restart)",
        "settings.database.export_images_csv_button": " Image List (CSV)",
        "settings.database.export_images_csv_tooltip": "Exports the image list of the currently used database to a CSV file",
        "settings.database.export_sync_history_button": " Sync History (CSV)",
        "settings.database.export_sync_history_tooltip": "Exports the history of folders/images not found during sync, and import errors, to a CSV file",
        "settings.database.reset_button": " Reset Database",
        "settings.database.reset_tooltip": "Deletes all image and folder information from the currently used database (actual image files are not deleted)",
        "settings.database.reset_done_body": "The selected database has been reset.",
        "settings.database.already_in_use_body": "This database is already in use.",
        "settings.database.already_reset.title": "No Need to Reset",
        "settings.database.already_reset.body": "There are currently no images or folders registered in the database.\nIt is already in a reset state.",
        "settings.database.reset_confirm.title": "Reset Selected Database \n",
        "settings.database.reset_confirm.body": "[ Items that will be reset ]\n \n- Data in the currently selected database\n({images} image(s), {folders} folder(s), etc. Actual image files on your PC will not be deleted)\n\n \n\n[ Items that will NOT be reset ]\n \n- Updated/saved image files and their information\n- App settings\n- Whether auto-numbering is used\n- Prefix and append names\n- Appearance mode\n- Generation parameter display fields\n- Folder import order\n- Reading mode\n\n \n\nThis cannot be undone. Are you sure?",
        "settings.database.switch_confirm.title": "Switch Database",
        "settings.database.switch_confirm.body": "Switching to \"{db_name}\" requires restarting the app.\nAny unsaved edits will be lost.\n\nSwitch and restart?",
        "settings.language.switch_confirm.title": "Switch Display Language",
        "settings.language.switch_confirm.body": "Switching the display language to \"{lang}\" requires restarting the app.\nAny unsaved edits will be lost.\n\nSwitch and restart?",
        "settings.database.create_confirm.title": "Create New Database",
        "settings.database.create_confirm.body": "This will create a new database named \"{db_name}\".\n\nAre you sure?",
        "settings.database.create_done.title": "Created",
        "settings.database.create_done.body": "Created a new database named \"{db_name}\".\n\nTo switch to this database, select it from the list above and click \"Switch Database\" (the app will restart when you switch).",
        "settings.database.no_sync_history.title": "Sync History",
        "settings.database.no_sync_history.body": "No sync history has been recorded yet.",

        # --- Database not found dialog ---
        "dialog.db_missing.title": "Database Not Found",
        "dialog.db_missing.create_new_radio": "Create a new empty database",
        "dialog.db_missing.sample_data_checkbox": "Load sample data",
        "dialog.db_missing.choose_existing_radio": "Choose another database in the same storage folder",
        "dialog.db_missing.choose_external_radio": "Specify and load an external backup file",
        "dialog.db_missing.no_selection": "(none selected)",
        "dialog.db_missing.select_existing_warning": "Please choose an existing database.",
        "dialog.db_missing.select_file_warning": "Please choose a file to load.",
        "dialog.db_missing.info": "No database file was found in the default storage location.\n(This appears on first launch, or if the file was deleted.)\n\nWhat would you like to do?",
        "dialog.db_missing.browse_file_title": "Choose Backup Database File",
        "dialog.db_missing.browse_file_filter": "SQLite Database (*.db)",
        "dialog.db_missing.import_failed.title": "Load Failed",
        "dialog.db_missing.import_done.title": "Loaded",
        "dialog.db_missing.import_done.body": "Created a new database and copied the data. The database name is {db_name}.",
        "dialog.db_missing.sample_import_failed.title": "Failed to Add Sample Images",

        # --- Main window: top bar ---
        "main.tooltip.toggle_all_fields_hide": "Hide all edit fields and import format fields at once",
        "main.tooltip.toggle_all_fields_hide_all": "Hide the section headers too, and enlarge the preview further",
        "main.tooltip.toggle_all_fields_show": "Show all edit fields and import format fields at once",
        "main.tooltip.help": "Help (shows basic instructions)",
        "main.tooltip.settings": "Settings",
        "main.search.placeholder": "Space-separated for multiple terms (stars: star1-5)",
        "main.search.hint_tooltip": "See Help for search syntax (OR search, exclusion, date ranges, etc.)",
        "main.button.import_folder": " Import Folder",
        "main.tooltip.import_folder": "Select a folder and import all the images directly inside it (subfolders are not included)\nSupported formats: PNG / JPG / JPEG / WEBP / GIF / BMP / TIFF (selectable)",
        "main.button.import_files": " Import Images",
        "main.tooltip.import_files": "Select individual image files to import (multiple selection allowed)",
        "main.tooltip.sync": "Sync imported folders (reflect additions/removals)\nRe-scans previously imported folders, imports newly added images,\nand removes deleted/moved images from the list.",
        "main.tooltip.expand_all_groups": "Expand all",
        "main.tooltip.collapse_all_groups": "Collapse all",
        "main.tooltip.expand_collapse_empty": "Nothing to expand/collapse",
        "main.sort.by_name": "Sort: By Name",
        "main.sort.by_created": "Sort: By Creation Date",
        "main.sort.by_edited": "Sort: By Edited Date",
        "main.sort.by_imported": "Sort: By Import Date",
        "main.sort.by_rating": "Sort: By Rating",
        "main.sort.by_filesize": "Sort: By File Size",
        "main.sort.by_filename": "Sort: By Filename",
        "main.sort.by_album_name": "Sort: By Album Name",
        "main.sort.no_album": "(No album)",
        "main.label.edited_only": "Edited: {value}",
        "csv.sync_history.col_datetime": "Date/Time",
        "csv.sync_history.col_category": "Category",
        "csv.sync_history.col_target_path": "Target path",
        "csv.sync_history.col_detail": "Detail",
        "dialog.sync_result.history_button": "History",
        "progress.cancel_button": "Cancel",
        "progress.import.title": "Import progress",
        "progress.import.initial_scan": "Scanning images...",
        "progress.import.initial_importing": "Importing images...",
        "progress.sync.title": "Sync progress",
        "progress.sync.initial": "Syncing folders...",
        "progress.label.processing": "Processing ({current} / {total}):\n{file_name}",
        "progress.label.scanning_folder": "Scanning folder:\n{folder}",
        "main.tooltip.sync_button": "Sync imported folders (reflect additions/removals)\nRe-scans previously imported folders, imports newly added images,\nand removes deleted or moved images from the list.",
        "main.preview_info.created": "Created: {value}",
        "main.preview_info.edited": " (Edited: {value})",
        "main.preview_info.imported": "Imported: {value}",
        "main.preview_info.imported_none": "Imported: —",
        "main.preview_info.rating": "Rating: {stars}",
        "main.preview_info.rating_none": "Rating: —",
        "main.preview_info.size": "Size: {value}",
        "main.preview_info.albums": "Albums: {names}",
        "main.preview_info.albums_none": "Albums: —",
        "main.preview_info.selected_count": "{count} selected",
        "main.fullscreen.name_filename": "Name: {name}   Filename: {filename}",
        "main.tooltip.sort_direction_asc": "Toggle ascending/descending order (currently: ascending)",
        "main.tooltip.sort_direction_desc": "Toggle ascending/descending order (currently: descending)",
        "main.tooltip.view_toggle_to_grid": "Switch to grid view",
        "main.tooltip.view_toggle_to_list": "Switch to list view",
        "main.tooltip.group_toggle_enable": "Group by folder (once enabled, right-click a folder heading to change its order)",
        "main.tooltip.group_toggle_disable": "Turn off grouped display",
        "main.tooltip.view_toggle_disabled_grouped": "Cannot switch to grid view while folder-grouped display is active",
        "main.tooltip.group_toggle_disabled_grid": "Folder-grouped display is only available in list view",
        "main.tooltip.view_toggle_disabled_album": "Cannot switch to grid view while album display is active",
        "main.tooltip.group_toggle_disabled_album": "Folder-grouped display cannot be toggled while album display is active",
        "main.button.grid_small": " Small",
        "main.tooltip.grid_small": "Show thumbnails at a small size",
        "main.button.grid_medium": " Medium",
        "main.tooltip.grid_medium": "Show thumbnails at a medium size",
        "main.button.grid_large": " Large",
        "main.tooltip.grid_large": "Show thumbnails at a large size",
        "main.label.empty_state": "Please import some images",
        "main.label.drag_hover": "Drag and drop images or a folder here",
        "main.label.no_search_results": "No search results",
        "main.album_header.note_collapsed_search": "(Collapsed albums are excluded from search)",
        "main.folder_header.note_collapsed_search": "(Collapsed folders are excluded from search)",
        "main.label.gif_note": "* For GIFs, the first frame is shown as a still image",
        "main.tooltip.format_gif": "GIFs cannot be played in the current version (the first frame is shown as a still image)",
        "main.tooltip.format_tiff": "TIFF (.tif / .tiff) is supported",
        "main.button.delete_selected": " Remove Selected Images From List",
        "main.button.delete_selected_with_count": " Remove {count} Image(s) From List",
        "main.button.delete_none": " Delete",
        "main.button.delete_folder": " Delete Folder \"{folder_name}\"",
        "main.button.delete_album": " Delete Album \"{album_name}\"",
        "main.button.remove_from_album_selected": " Remove From Album",
        "main.button.remove_from_album_count": " Remove {count} From Album",
        "main.tooltip.delete": "Removes from the list (the actual image files on disk are not deleted)",
        "main.tooltip.theme_toggle": "Toggle appearance mode (currently: {mode})",
        "main.tooltip.panel_flip_mirrored": "Flip panel layout (currently: mirrored)",
        "main.tooltip.panel_flip_standard": "Flip panel layout (currently: standard)",
        "main.tooltip.language_toggle": "Switch display language (currently: {lang})",

        # --- Metadata edit area ---
        "metadata.filename.header": "Filename",
        "metadata.filename.tooltip": "This is the actual filename on disk. Changing it and clicking \"Save Changes\" will rename the file itself.",
        "metadata.filename.multi_selected": "[Multiple Selected]",
        "metadata.name.header": "Name",
        "metadata.name.tooltip": "A name used only within the app, separate from the actual filename. You can freely change it (duplicates allowed) and use it like a search tag (defaults to auto-numbering).",
        "metadata.name.multi_selected": "[Multiple Selected - Only Rating Can Be Changed]",
        "metadata.preview.button_hidden": " Hidden",
        "metadata.preview.tooltip_hidden": "Hide the preview to give the metadata edit area more room",
        "metadata.preview.button_standard": " Standard",
        "metadata.preview.tooltip_standard": "Show the preview at standard size",
        "metadata.preview.button_compact": " Compact",
        "metadata.preview.tooltip_compact": "Show the preview at compact size",
        "metadata.preview.button_fullscreen": " Fullscreen",
        "metadata.preview.tooltip_fullscreen": "Show the preview in fullscreen",
        "metadata.preview.select_prompt": "Please select an image",
        "metadata.preview.load_failed": "Failed to load the image",
        "metadata.tooltip.reading_mode": "Reading mode (spread view)\nOnly available when \"Group by Folder\" is enabled",
        "metadata.tooltip.preview_pin_off": "Pin the preview in place\n(The preview will no longer scroll along with the edit fields)",
        "metadata.tooltip.preview_pin_on": "Unpin the preview\n(It will scroll together with the edit fields again)",
        "metadata.tooltip.star_rating": "Click to set a rating (0-5 stars). Click an already-set star again to clear it.",
        "metadata.tooltip.prev_image": "Previous image",
        "metadata.tooltip.next_image": "Next image",
        "metadata.button.save": " Save Changes",
        "metadata.button.save_plain": "Save Changes",
        "metadata.button.save_selected_ratings": " Save Ratings (★) for {count} Selected",
        "metadata.button.saved_confirmation": " Saved",
        "metadata.tooltip.save_locked": "This image is locked and cannot be edited",
        "metadata.tooltip.unsaved": "You have unsaved changes",
        "metadata.tooltip.section_move_up": "Move this section up",
        "metadata.tooltip.section_move_down": "Move this section down",
        "metadata.button.save_as_new": " Save As New",
        "metadata.tooltip.save_as_new": "Saves a new copy at the location you choose, without changing the original,\nwith the current content (display name, rating, prompt, etc.).",
        "metadata.button.slideshow_idle": "▶  Slideshow",
        "metadata.button.slideshow_start_action": "▶  Start Slideshow",
        "metadata.button.slideshow_stop": "■  Stop Slideshow",
        "metadata.tooltip.slideshow": "Starts a slideshow that automatically plays through the images",
        "metadata.tooltip.speed": "Change playback speed (0.5x-2x)",
        "metadata.memo.header": "Memo",
        "metadata.memo.placeholder": "Included in search",
        "metadata.model.header": "Model / Checkpoint Used",
        "metadata.prompt.header": "Prompt",
        "metadata.negative_prompt.header": "Negative Prompt",
        "metadata.other_params.header": "Other Parameters / Metadata / EXIF Info",
        "metadata.tooltip.section_toggle_show": "Show the edit form",
        "metadata.tooltip.section_toggle_hide": "Hide the edit form",
        "metadata.tooltip.clear_field": "Clear this field (not finalized until you click \"Save Changes\")",
        "metadata.tooltip.copy_seed": "Copy Seed value",

        # --- Right-click context menu (images/folders) ---
        "menu.reveal_finder": "Show in Finder",
        "menu.reveal_explorer": "Show in Explorer",
        "menu.reveal_file_manager": "Show in File Manager",
        "menu.unlock_edit": "Unlock Editing",
        "menu.lock_edit": "Lock Editing",
        "menu.copy_file": "Copy File",
        "menu.copy_file_path": "Copy File Path",
        "menu.bulk_rename": "Bulk Rename Selected (Sequential)...",
        "menu.bulk_copy_renamed": "Export Selected as Renamed Copies (Sequential)...",
        "menu.folder_edit_order": "Edit Folder Order...",
        "menu.folder_copy_renamed": "Export Folder Images as Renamed Copies (Sequential)...",
        "menu.folder_naming_rule": "Set Folder-Specific Auto-Numbering...",
        "menu.folder_properties": "Properties...",
        "menu.folder_delete": "Remove Folder From Database...",
        "menu.expand_all_folders": "Expand All Folders",
        "menu.collapse_all_folders": "Collapse All Folders",
        "menu.add_to_album": "Add to Album",
        "menu.add_to_album_new": "Create New Album...",
        "menu.remove_from_album": "Remove from This Album",
        "menu.delete_from_list": "Remove from List...",
        "browse_mode.button.images": "Folders",
        "browse_mode.button.albums": "Albums",
        "browse_mode.tooltip.images": "Switch to the normal image list view",
        "browse_mode.tooltip.albums": "Switch to album view",
        "album.button.create": "Create an Album",
        "album.tooltip.add": "Create a new album",
        "album.dialog.create.title": "New Album",
        "album.dialog.create.label": "Enter an album name",
        "album.dialog.create.naming_hint": "Auto-numbering rule used when bulk-exporting images from this album (can be changed later from the header's right-click menu). When off, the app-wide default rule is used.",
        "album.dialog.create.preview_prefix_rename": "Images you add will be renamed to: ",
        "album.dialog.create.confirm_button": "Create",
        "album.dialog.create.name_empty_warning": "Please enter an album name.",
        "album.dialog.rename.title": "Rename Album",
        "album.dialog.rename.label": "Enter a new album name",
        "album.menu.rename": "Rename",
        "album.menu.delete": "Delete Album",
        "album.confirm.delete.title": "Delete Album",
        "album.confirm.delete.body": "Delete album \"{name}\"?\n(The images themselves will not be deleted.)",
        "album.confirm.remove_images.title": "Remove From Album",
        "album.confirm.remove_images.body": "Remove the selected {count} image(s) from this album?\n(The images themselves stay in the app's list, and any other album memberships are unaffected.)",
        "album.notify.added": "Added {count} image(s) to \"{name}\"",
        "album.notify.added_count": "Added {count} image(s) to the album",
        "album.notify.removed_count": "Removed {count} image(s) from the album",
        "album.notify.naming_rule_saved": "Saved auto-numbering rule specific to \"{name}\"",
        "menu.album_edit_order": "Edit Album Order...",
        "menu.album_copy_renamed": "Export Album Images as Renamed Copies (Sequential)...",
        "menu.album_naming_rule": "Set Album-Specific Auto-Numbering...",
        "menu.album_properties": "Properties...",
        "menu.album_delete": "Delete Album...",
        "menu.expand_all_albums": "Expand All Albums",
        "menu.collapse_all_albums": "Collapse All Albums",

        # --- Status bar transient messages ---
        "status.files_copied": "Copied {count} file(s) (paste with Cmd+V / Ctrl+V)",
        "status.file_path_copied": "File path copied",
        "status.sequence_rename_export_done": "{context}Exported {count} item(s) with sequential renaming.",
        "status.sequence_rename_export_errors_suffix": " Failed: {count} (see tooltip for details)",
        "status.sequence_rename_export_error_item": "{name} → {new_name} (a file with that name already exists)",
        "status.sequence_rename_export_error_item_exc": "{name}: {error}",
        "status.bulk_rename_done": "Changed the \"Name\" field for {count} item(s).",
        "status.rating_saved_with_locked_skipped": "Saved rating, excluding {count} locked item(s)",
        "status.rating_saved": "Rating saved",
        "status.changes_saved": "Changes saved",
        "main.library_status": "Folders: {folders}   Images: {images}   Last synced: {last_sync}",
        "main.library_status.not_synced": "Not synced yet",
        "main.library_status_album": "Albums: {albums}   Images: {images}",
        "main.folder_header.tooltip_collapsed": "Click to show images · Drag to copy the whole folder (original filenames are kept as-is; right-click \"Export as Renamed Copies\" to apply the naming rule)",
        "main.folder_header.tooltip_expanded": "Click to collapse images · Drag to copy the whole folder (original filenames are kept as-is; right-click \"Export as Renamed Copies\" to apply the naming rule)",
        "album.header.tooltip_collapsed": "Click to show images · Drag to export to Finder etc. (original filenames are kept as-is; right-click \"Export as Renamed Copies\" to apply the naming rule)",
        "album.header.tooltip_expanded": "Click to collapse images · Drag to export to Finder etc. (original filenames are kept as-is; right-click \"Export as Renamed Copies\" to apply the naming rule)",
        "main.list_item.location_line": "Location: .../{parent_dir}/",
        "main.list_item.locked_note": "🔒 Locked for editing\n",
        "main.button.delete_selected_count": " Remove {count} Image(s) From List",
        "main.button.save_selected_ratings": " Save Rating (★) for {count} Selected",
        "main.multi_select.filename_placeholder": "[Multiple Selected]",
        "main.multi_select.name_placeholder": "[Multiple Selected - Rating Only]",
        "common.title.sync_complete": "Sync Complete",
        "common.title.sync_complete_partial_errors": "Sync Complete (With Some Errors)",
        "confirm.delete_locked_blocked.body": "Cannot delete: the selection includes {count} locked image(s).\nUnlock them from the right-click menu and try again.",
        "confirm.delete_images.title": "Confirm Delete Images",
        "confirm.delete_images.body": "Remove the selected {count} image(s) from the app's list? The original image files on disk will not be deleted.",
        "dialog.choose_export_dest_title": "Choose Export Destination Folder",
        "dialog.export_subfolder.title": "Create a Subfolder?",
        "dialog.export_subfolder.body": "Create a folder named \"{name}\" inside the destination and export into it?",
        "dialog.export_subfolder.button_create": "Create Folder and Export",
        "dialog.export_subfolder.button_direct": "Export Directly",
        "notify.export_subfolder_create_failed": "Failed to create the subfolder:\n{error}",
        "confirm.bulk_rename_selected.title": "Bulk Rename Selected Images",
        "confirm.bulk_rename_selected.body": "Bulk-change the \"Name\" field of {count} image(s) using the configured auto-numbering rule?\nThe actual filenames on disk will not be changed.\n\nExample: {preview}{skip_note}",
        "confirm.folder_delete.title": "Remove Folder From Database",
        "confirm.folder_delete.body": "Remove folder \"{folder_name}\" ({count} image(s)) from the database?\n\n- It will no longer appear in the image list, and will be excluded from future sync (auto rescan)\n- The actual files on disk will not be deleted\n- Import it again with \"Import Folder\" to make it a sync target again",

        # --- Progress dialogs ---
        "progress.import_title": "Import Progress",
        "progress.sync_title": "Sync Progress",
        "progress.processing_item": "Processing ({current} / {total}):\n{file_name}",
        "progress.scanning_folder": "Scanning folder:\n{folder}",

        # --- Notification popups (body text) ---
        "notify.csv_write_failed": "Failed to write the CSV file:\n{error}",
        "notify.sync_history_export_done": "Exported {count} sync history entries to CSV.\n\n{save_path}",
        "notify.export_images_done": "Exported {count} image entries to CSV.\n\n{save_path}",
        "notify.title.sync_history": "Sync History",
        "notify.db_load_failed": "Failed to load the database:\n{error}",
        "notify.save_locked_body": "This image is locked, so changes cannot be saved.\nUnlock it from the right-click menu.",
        "notify.name_empty_warning": "The name cannot be empty.",
        "notify.filename_empty_warning": "The filename cannot be empty.",
        "notify.original_file_missing": "The filename could not be changed because the original file was not found.",
        "notify.filename_conflict": "The filename could not be changed because a file with the same name already exists:\n{new_filename}\n\nOther changes were not saved.",
        "notify.rename_failed": "Failed to rename the file:\n{error}\n\nOther changes were not saved.",
        "notify.select_image_warning": "Please select an image.",
        "notify.original_image_missing": "The original image file could not be found.",
        "notify.display_name_empty_warning": "The display name cannot be empty.",
        "notify.file_copy_failed": "Failed to copy the file:\n{error}",
        "notify.duplicate_path_warning": "An image with the same path is already registered at the specified destination.",
        "notify.save_as_new_done": "Saved the new copy and registered it in the database:\n{dest_path}",
        "notify.folder_path_unresolved": "Could not determine the folder's actual path.",
        "notify.no_images_in_db": "There are currently no images imported into the database.",
        "notify.copy_target_not_found": "No images to copy were found.",
        "notify.bulk_rename_all_locked": "All selected images are locked for editing, so they cannot be renamed.",
        "notify.file_manager_open_failed": "Could not open the file manager:\n{error}",
        "notify.search_all_collapsed": "All folders are collapsed.\nCollapsed folders are excluded from search. Please expand the folders you want to search.",
        "notify.search_all_albums_collapsed": "All albums are collapsed.\nCollapsed albums are excluded from search. Please expand the albums you want to search.",
        "notify.body.cancelled_with_summary": "The process was interrupted because it was cancelled.\n\n{summary}",
        "sync.error_summary_suffix": "\n\n[Errors Encountered]\n{error_log}",
        "notify.import_partial_errors_body": "Processing complete.\n\n{summary}\n\n[Errors Encountered]\n{error_log}",
        "notify.import_complete_body": "All images were imported successfully!\n\n{summary}",
        "notify.no_import_format_selected_body": "Check the format checkboxes at the bottom of the list (e.g. PNG, JPG) for the formats you want to import.",
        "notify.no_supported_images_found": "No supported image files (PNG/JPG/WEBP) were found.",
        "notify.import_drag_drop_done_body": "Images were imported via drag and drop!\n\n{summary}",
        "notify.sync_no_folders": "No folders have been imported yet.\nRun \"Import Folder\" first.",
        "import.summary.inserted": "Newly registered: {count}",
        "import.summary.duplicates": "Skipped (duplicates): {count}",
        "import.summary.total": "Total: {count}",
        "sync.summary.target_folders": "Target folders: {count}",
        "sync.summary.inserted": "Newly added: {count}",
        "sync.summary.duplicates_with_scanned": "Skipped (duplicates): {duplicates} (scanned total: {scanned})",
        "sync.summary.removed": "Removed/moved detected: {count}",
        "sync.summary.missing_folders_warning": "\n\n⚠ The following folders were not found, so scanning was skipped:\n{folders}",
        "sync.summary.missing_folders_note": "\n(Popups for this folder will be skipped until it is found again. See \"History\" for details.)",
    },
}


def detect_os_language():
    """OSのロケールから "ja" か "en" を判定する。判定できない場合は DEFAULT_LANGUAGE を返す。"""
    try:
        lang_code, _ = locale.getlocale()
        if not lang_code:
            lang_code = locale.getdefaultlocale()[0]
        if lang_code and lang_code.lower().startswith("ja"):
            return "ja"
        if lang_code and lang_code.lower().startswith("en"):
            return "en"
    except Exception:
        pass
    return DEFAULT_LANGUAGE


def resolve_language(setting_value):
    """設定値（"auto"/"ja"/"en"）から、実際に使用する言語コードを決定する。"""
    if setting_value in SUPPORTED_LANGUAGES:
        return setting_value
    return detect_os_language()


def tr(key, lang):
    """文字列キーを、指定言語の文言に変換する。
    未登録のキーはそのままキー名を返す（未翻訳箇所を発見しやすくするため）。"""
    table = STRINGS.get(lang, STRINGS[DEFAULT_LANGUAGE])
    return table.get(key, STRINGS[DEFAULT_LANGUAGE].get(key, key))
