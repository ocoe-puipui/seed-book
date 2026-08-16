# -*- mode: python ; coding: utf-8 -*-
# Seed Book（旧称: AI Image Viewer & Manager）用 PyInstaller spec ファイル。
#
# 使い方（お使いのMacのターミナルで、requirements.txt / requirements-build.txt を
# インストール済みのvenvの中で実行すること。Linux等の別OS上ではmac用の.appは作れない）:
#   pyinstaller AIImageViewer.spec
#
# 生成物: dist/Seed Book.app
# （内部の実行ファイル本体の名前は SeedBook。ターミナル・スクリプトでの扱いやすさを
#   考慮し、スペースなしにしている。Finder上の表示名（.appの名前）には影響しない）
#
# 補足:
# - このアプリはアイコン等の画像をコードに埋め込んだSVG文字列として持っており、
#   実行時に外部ファイル（画像・設定ファイル等）をほとんど読み込まない設計だが、
#   sample_data/（初回セットアップ時に任意で取り込めるサンプル画像、著作権上の問題がない
#   ダミー画像）のみ例外的に同梱する（datasで指定。app.pyのget_sample_data_dir()が
#   sys._MEIPASS経由でこの場所を参照する）。
# - データベースの保存先は ~/Library/Application Support/AIImageViewer/ であり、
#   .appバンドルの外なので、ここにも含めない（database.get_db_dir() 参照）。
#
# コード署名・公証について（2026-08-04〜、2026-08-16に公開リポジトリ対応で方式変更）:
# - 証明書名（氏名・Team ID）を公開リポジトリに含めないため、下の codesign_identity は
#   あえて None にしてあり、PyInstallerによるビルド時署名は行わない。
# - 署名は必ずビルド後に、以下のコマンドをお使いのMacのターミナルで直接実行して行うこと
#   （証明書名はコマンドとしてその場で入力するだけなので、リポジトリには残らない）:
#     codesign --deep --force --options runtime \
#       --entitlements entitlements.plist \
#       --sign "Developer ID Application: <氏名> (<Team ID>)" \
#       "dist/Seed Book.app"
#   証明書名は `security find-identity -v -p codesigning` で確認できる。
#   署名の検証:
#     codesign --verify --deep --strict --verbose=2 "dist/Seed Book.app"
# - 公証（notarization）は署名確認後に別途 xcrun notarytool で実施する。

block_cipher = None

# バージョン番号は version.py を単一の管理場所とする（app.py の画面左上表示と共通）。
from version import APP_VERSION

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('sample_data', 'sample_data')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SeedBook',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUIアプリなのでターミナルウィンドウは表示しない
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,  # 署名はビルド後に手動で行う（上記コメント参照）
    entitlements_file='entitlements.plist',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SeedBook',
)

app = BUNDLE(
    coll,
    name='Seed Book.app',
    icon='design/app_icon_source/AppIcon.icns',
    bundle_identifier='com.ocoe-puipui.aiimageviewer',
    info_plist={
        'CFBundleName': 'Seed Book',
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'ocoe-puipui',
    },
)
