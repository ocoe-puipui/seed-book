import sys
import os
import re
import unicodedata
import calendar
import csv
import sqlite3
import subprocess
import platform
import shutil
from collections import OrderedDict
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                               QVBoxLayout, QPushButton, QFileDialog, QListWidget,
                               QListWidgetItem, QLabel, QTextEdit, QSplitter, QScrollArea, QMessageBox, QLineEdit, QComboBox, QProgressDialog,
                               QMenu, QAbstractItemView, QSizePolicy, QDialog, QSpinBox, QRadioButton, QGroupBox, QButtonGroup, QStyle, QCheckBox, QStackedWidget, QFrame, QSlider, QGridLayout, QSpacerItem, QStyledItemDelegate, QLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtGui import QPixmap, QIcon, QDrag, QGuiApplication, QColor, QDesktopServices, QPainter, QFontMetrics, QFont
from PySide6.QtCore import QSize, Qt, QTimer, QMimeData, QUrl, QEvent, Signal, QByteArray, QRect, QPoint, QStandardPaths
from PySide6.QtSvg import QSvgRenderer

import database
import importer
import i18n
from version import APP_VERSION


def get_resource_dir():
    """バンドルされたリソース（サンプル画像など）の場所を返す。
    PyInstallerで.app化された場合はsys._MEIPASS（同梱データの展開・配置先）を、
    それ以外（python3 main.pyでの直接実行）はこのファイルと同じディレクトリを返す。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_sample_data_dir():
    """同梱しているサンプル画像（AI生成画像を模したダミー画像、取り込み方法のお試し用）の場所。"""
    return os.path.join(get_resource_dir(), "sample_data")


def get_default_export_dir():
    """CSV等のエクスポート時、保存先ダイアログを開く既定のフォルダを返す。
    何も指定しない場合、Qtはプロセスの実行時カレントディレクトリ（.app化時はアプリ本体の
    場所など、実行のたびに変わりうる不定な場所）を初期表示にしてしまうため、常に
    デスクトップ（取得できない環境ではホームフォルダ）を明示的に指定する
    （2026-08-14〜）。"""
    desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
    if desktop and os.path.isdir(desktop):
        return desktop
    return os.path.expanduser("~")


DARK_COLORS = {
    "window_bg": "#2e2e2e",
    "input_bg": "#222222",
    "input_border": "#555555",
    "input_text": "#ffffff",
    "button_bg": "#444444",
    "button_border": "#666666",
    "button_hover": "#555555",
    "button_text": "#ffffff",
    "list_bg": "#222222",
    "list_border": "#444444",
    "list_item_border": "#2a2a2a",
    "list_text": "#eeeeee",
    "group_header_bg": "#3a3a3a",
    "divider_color": "#4d4d4d",
    "preview_bg": "#1e1e1e",
    "preview_border": "#444444",
    "preview_text": "#888888",
    "label_text": "#e0e0e0",
    "scroll_bg": "#333333",
    "accent_bg": "#2b5797",
    "accent_text": "#ffffff",
    "danger_bg": "#ce352c",
    "danger_text": "#ffffff",
    "caution_bg": "#ed2c3a",
    "caution_text": "#ffffff",
    "export_bg": "#2e7d4f",
    "export_text": "#ffffff",
    "model_text": "#5fd7ff",
    "prompt_text": "#eeeeee",
    "metadata_text": "#aaaaaa",
    "copy_btn_bg": "#444444",
    "copy_btn_text": "#cccccc",
    "menu_bg": "#222222",
    "menu_text": "#ffffff",
    "menu_border": "#555555",
    "speed_btn_bg": "#ffffff",
    "speed_btn_text": "#222222",
    "speed_btn_border": "#999999",
}

LIGHT_COLORS = {
    "window_bg": "#f0f0f0",
    "input_bg": "#ffffff",
    "input_border": "#c0c0c0",
    "input_text": "#222222",
    "button_bg": "#e4e4e4",
    "button_border": "#b5b5b5",
    "button_hover": "#d5d5d5",
    "button_text": "#222222",
    "list_bg": "#ffffff",
    "list_border": "#c0c0c0",
    "list_item_border": "#e5e5e5",
    "list_text": "#222222",
    "group_header_bg": "#e2e2e2",
    "divider_color": "#d0d0d0",
    "preview_bg": "#e6e6e6",
    "preview_border": "#c0c0c0",
    "preview_text": "#777777",
    "label_text": "#222222",
    "scroll_bg": "#e8e8e8",
    "accent_bg": "#2b5797",
    "accent_text": "#ffffff",
    "danger_bg": "#ce352c",
    "danger_text": "#ffffff",
    "caution_bg": "#ed2c3a",
    "caution_text": "#ffffff",
    "export_bg": "#1e8449",
    "export_text": "#ffffff",
    "model_text": "#0a6ea1",
    "prompt_text": "#222222",
    "metadata_text": "#555555",
    "copy_btn_bg": "#e4e4e4",
    "copy_btn_text": "#333333",
    "menu_bg": "#ffffff",
    "menu_text": "#222222",
    "menu_border": "#c0c0c0",
    "speed_btn_bg": "#ffffff",
    "speed_btn_text": "#222222",
    "speed_btn_border": "#999999",
}

GRID_SIZE_PRESETS = {
    "small": (60, 80, 100),
    "medium": (90, 112, 132),
    "large": (140, 165, 195),
}


SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_XXL = 30

FONT_SIZE_HEADING = 13
FONT_SIZE_BODY = 12
FONT_SIZE_CAPTION = 11

ICON_SIZE_MD = 14
ICON_SIZE_LG = 16
ICON_SIZE_XL = 20

STAR_SPACING = 1
PREVIEW_SIDE_PADDING = 64
THUMBNAIL_CACHE_LIMIT = 4000

SVG_ICON_COLOR = "#8a8a8a"
SVG_ICON_COLOR_ON_ACCENT = "#ffffff"

SVG_ICONS = {
    "chevron_left": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M560-240 320-480l240-240 56 56-184 184 184 184-56 56Z"/></svg>',
    "chevron_right": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M504-480 320-664l56-56 240 240-240 240-56-56 184-184Z"/></svg>',
    "delete": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"/></svg>',
    "content_copy": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M760-200H320q-33 0-56.5-23.5T240-280v-560q0-33 23.5-56.5T320-920h280l240 240v400q0 33-23.5 56.5T760-200ZM560-640v-200H320v560h440v-360H560ZM160-40q-33 0-56.5-23.5T80-120v-560h80v560h440v80H160Zm160-800v200-200 560-560Z"/></svg>',
    
    "settings": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="m370-80-16-128q-13-5-24.5-12T307-235l-119 50L78-375l103-78q-1-7-1-13.5v-27q0-6.5 1-13.5L78-585l110-190 119 50q11-8 23-15t24-12l16-128h220l16 128q13 5 24.5 12t22.5 15l119-50 110 190-103 78q1 7 1 13.5v27q0 6.5-2 13.5l103 78-110 190-118-50q-11 8-23 15t-24 12L590-80H370Zm70-80h79l14-106q31-8 57.5-23.5T639-327l99 41 39-68-86-65q5-14 7-29.5t2-31.5q0-16-2-31.5t-7-29.5l86-65-39-68-99 42q-22-23-48.5-38.5T533-694l-13-106h-79l-14 106q-31 8-57.5 23.5T321-633l-99-41-39 68 86 64q-5 15-7 30t-2 32q0 16 2 31t7 30l-86 65 39 68 99-42q22 23 48.5 38.5T427-266l13 106Zm42-180q58 0 99-41t41-99q0-58-41-99t-99-41q-59 0-99.5 41T342-480q0 58 40.5 99t99.5 41Zm-2-140Z"/></svg>',
    "directory_sync": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M212-239q-43-48-67.5-110T120-480q0-150 105-255t255-105v-80l200 150-200 150v-80q-91 0-155.5 64.5T260-480q0 46 17.5 86t47.5 70l-113 85ZM480-40 280-190l200-150v80q91 0 155.5-64.5T700-480q0-46-17.5-86T635-636l113-85q43 48 67.5 110T840-480q0 150-105 255T480-120v80Z"/></svg>',
    "folder": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h240l80 80h320q33 0 56.5 23.5T880-640v400q0 33-23.5 56.5T800-160H160Zm0-80h640v-400H447l-80-80H160v480Zm0 0v-480 480Z"/></svg>',
    "arrow_upward": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M440-240v-368L296-464l-56-56 240-240 240 240-56 56-144-144v368h-80Z"/></svg>',
    "arrow_downward": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M480-240 240-480l56-56 144 144v-368h80v368l144-144 56 56-240 240Z"/></svg>',
    
    "grid_view": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                 '<rect x="4" y="4" width="7" height="7" rx="1" fill="{color}"/>'
                 '<rect x="13" y="4" width="7" height="7" rx="1" fill="{color}"/>'
                 '<rect x="4" y="13" width="7" height="7" rx="1" fill="{color}"/>'
                 '<rect x="13" y="13" width="7" height="7" rx="1" fill="{color}"/></svg>',
    "view_list": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                 '<rect x="4" y="5" width="16" height="3" rx="1" fill="{color}"/>'
                 '<rect x="4" y="10.5" width="16" height="3" rx="1" fill="{color}"/>'
                 '<rect x="4" y="16" width="16" height="3" rx="1" fill="{color}"/></svg>',


    "import_folder": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h240l80 80h320q33 0 56.5 23.5T880-640H447l-80-80H160v480l96-320h684L837-217q-8 26-29.5 41.5T760-160H160Zm84-80h516l72-240H316l-72 240Zm0 0 72-240-72 240Zm-84-400v-80 80Z"/></svg>',
    "import_files": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M480-480ZM200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h320v80H200v560h560v-320h80v320q0 33-23.5 56.5T760-120H200Zm40-160h480L570-480 450-320l-90-120-120 160Zm440-320v-80h-80v-80h80v-80h80v80h80v80h-80v80h-80Z"/></svg>',
    "save": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M840-680v480q0 33-23.5 56.5T760-120H200q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h480l160 160Zm-80 34L646-760H200v560h560v-446ZM565-275q35-35 35-85t-35-85q-35-35-85-35t-85 35q-35 35-35 85t35 85q35 35 85 35t85-35ZM240-560h360v-160H240v160Zm-40-86v446-560 114Z"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M382-240 154-468l57-57 171 171 367-367 57 57-424 424Z"/></svg>',
    "save_as_new": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h480l160 160v212q-19-8-39.5-10.5t-40.5.5v-169L647-760H200v560h240v80H200Zm0-640v560-560ZM520-40v-123l221-220q9-9 20-13t22-4q12 0 23 4.5t20 13.5l37 37q8 9 12.5 20t4.5 22q0 11-4 22.5T863-260L643-40H520Zm300-263-37-37 37 37ZM580-100h38l121-122-18-19-19-18-122 121v38Zm141-141-19-18 37 37-18-19ZM240-560h360v-160H240v160Zm240 320h4l116-115v-5q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35Z"/></svg>',
    "slideshow": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="m380-300 280-180-280-180v360ZM200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/></svg>',
    "reset_settings": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M520-330v-60h160v60H520Zm60 210v-50h-60v-60h60v-50h60v160h-60Zm100-50v-60h160v60H680Zm40-110v-160h60v50h60v60h-60v50h-60Zm111-280h-83q-26-88-99-144t-169-56q-117 0-198.5 81.5T200-480q0 72 32.5 132t87.5 98v-110h80v240H160v-80h94q-62-50-98-122.5T120-480q0-75 28.5-140.5t77-114q48.5-48.5 114-77T480-840q129 0 226.5 79.5T831-560Z"/></svg>',
    "reset_database": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M446-446Zm106-95Zm-106 95Zm106-95Zm-106 95Zm106-95ZM791-56 56-791l56-57 736 736-57 56Zm-311-64q-151 0-255.5-46.5T120-280v-400q0-26 17.5-49.5T187-773l252 252q-72-3-133-18t-106-40v120q51 29 123 44t157 15q20 0 39-.5t38-2.5l70 70q-34 7-71 10t-76 3q-85 0-157-15t-123-44v99q9 29 97.5 54.5T480-200q64 0 128.5-13T715-245l58 58q-49 31-125.5 49T480-120Zm350-123-70-70v-66q-11 6-22 11t-23 10l-61-61q30-8 56.5-17.5T760-459v-120q-41 23-94 37t-116 19l-76-76q44 0 92-7t89.5-18.5q41.5-11.5 70-26T760-679q-11-29-100.5-55T480-760q-37 0-75.5 5T331-742l-66-66q45-15 100-23.5t115-8.5q149 0 254.5 47T840-680v400q0 10-2.5 19t-7.5 18Z"/></svg>',
    "help": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M513.5-254.5Q528-269 528-290t-14.5-35.5Q499-340 478-340t-35.5 14.5Q428-311 428-290t14.5 35.5Q457-240 478-240t35.5-14.5ZM442-394h74q0-33 7.5-52t42.5-52q26-26 41-49.5t15-56.5q0-56-41-86t-97-30q-57 0-92.5 30T342-618l66 26q5-18 22.5-39t53.5-21q32 0 48 17.5t16 38.5q0 20-12 37.5T506-526q-44 39-54 59t-10 73Zm38 314q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z"/></svg>',
    "release_notes": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M280-280h280v-80H280v80Zm0-160h400v-80H280v80Zm0-160h400v-80H280v80Zm-80 480q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/></svg>',
    "preview_standard": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h640q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160Zm0-80h640v-480H160v480Zm0 0v-480 480Z"/></svg>',
    "preview_compact": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M200-240q-33 0-56.5-23.5T120-320v-320q0-33 23.5-56.5T200-720h560q33 0 56.5 23.5T840-640v320q0 33-23.5 56.5T760-240H200Zm0-80h560v-320H200v320Zm0 0v-320 320Z"/></svg>',
    "preview_fullscreen": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M120-120v-320h80v184l504-504H520v-80h320v320h-80v-184L256-200h184v80H120Z"/></svg>',
    "preview_hidden": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="m644-428-58-58q9-47-27-88t-93-32l-58-58q17-8 34.5-12t37.5-4q75 0 127.5 52.5T660-500q0 20-4 37.5T644-428ZM792-56 671-177q-42 18-86 27.5t-91 9.5q-149 0-266-82.5T61-437q19-53 51-98t70-83l-88-88 56-56 736 736-56 56Zm-522-522q-24 24-45.5 51T183-462q22 68 90 137t172 87q11 0 22-1t21-3l-46-46q-8 2-16 3t-16 1q-75 0-127.5-52.5T230-462q0-8 1-16t3-16l-46-46Z"/></svg>',
    "preview_fullscreen_exit": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="m136-80-56-56 264-264H160v-80h320v320h-80v-184L136-80Zm344-400v-320h80v184l264-264 56 56-264 264h184v80H480Z"/></svg>',
    "grid_small": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M200-200h80v-80h-80v80Zm160 0h80v-80h-80v80Zm160 0h80v-80h-80v80Zm160 0h80v-80h-80v80ZM200-680h80v-80h-80v80Zm0 160h80v-80h-80v80Zm0 160h80v-80h-80v80Zm160-320h80v-80h-80v80Zm0 160h80v-80h-80v80Zm0 160h80v-80h-80v80Zm160-320h80v-80h-80v80Zm0 160h80v-80h-80v80Zm0 160h80v-80h-80v80Zm160-320h80v-80h-80v80Zm0 160h80v-80h-80v80Zm0 160h80v-80h-80v80ZM200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Z"/></svg>',
    "grid_medium": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h133v-133H200v133Zm213 0h134v-133H413v133Zm214 0h133v-133H627v133ZM200-413h133v-134H200v134Zm213 0h134v-134H413v134Zm214 0h133v-134H627v134ZM200-627h133v-133H200v133Zm213 0h134v-133H413v133Zm214 0h133v-133H627v133Z"/></svg>',
    "grid_large": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M120-520v-320h320v320H120Zm0 400v-320h320v320H120Zm400-400v-320h320v320H520Zm0 400v-320h320v320H520ZM200-600h160v-160H200v160Zm400 0h160v-160H600v160Zm0 400h160v-160H600v160Zm-400 0h160v-160H200v160Zm400-400Zm0 240Zm-240 0Zm0-240Z"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M784-120 532-372q-30 24-69 38t-83 14q-109 0-184.5-75.5T120-580q0-109 75.5-184.5T380-840q109 0 184.5 75.5T640-580q0 44-14 83t-38 69l252 252-56 56ZM380-400q75 0 127.5-52.5T560-580q0-75-52.5-127.5T380-760q-75 0-127.5 52.5T200-580q0 75 52.5 127.5T380-400Z"/></svg>',
    "group_by_folder": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M120-120q-33 0-56.5-23.5T40-200v-520h80v520h680v80H120Zm160-160q-33 0-56.5-23.5T200-360v-440q0-33 23.5-56.5T280-880h200l80 80h280q33 0 56.5 23.5T920-720v360q0 33-23.5 56.5T840-280H280Zm0-80h560v-360H527l-80-80H280v440Zm0 0v-440 440Z"/></svg>',


    "file_name": '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="{color}"><path d="M480-186.67q0-98-69.67-167.66Q340.67-424 242.67-424q0 98 69.66 167.67Q382-186.67 480-186.67Zm43.67-231q17-17 17-43.66v-7.34q8 6.67 17.5 9 9.5 2.34 19.16 2.34 26.67 0 43.67-17t17-43.38q0-20.29-9.17-33.96-9.16-13.66-24.83-23 15.67-6 24.83-21.26 9.17-15.26 9.17-35.61Q638-658 621-675t-43.67-17q-9.66 0-19.16 2.33-9.5 2.34-17.5 9V-688q0-26.67-17-43.67t-43.67-17q-26.67 0-43.67 17t-17 43.67v7.33q-8-6.66-17.5-9-9.5-2.33-19.16-2.33Q356-692 339-675t-17 43.38q0 20.29 8.83 34.29 8.84 14 25.17 22.66Q339.67-568 330.83-553 322-538 322-518q0 26.67 17 43.67t43.67 17q9.66 0 19.5-2.34 9.83-2.33 17.16-9v7.34q0 26.66 17 43.66 17 17 43.67 17t43.67-17Zm-95.34-105.16q-21-20.84-21-51.84 0-30.47 21.14-51.57 21.14-21.09 51.67-21.09t51.53 21.09q21 21.1 21 51.57 0 31-21.14 51.84Q510.39-502 479.86-502t-51.53-20.83ZM480-186.67q98 0 167.67-69.66Q717.33-326 717.33-424q-98 0-167.66 69.67Q480-284.67 480-186.67ZM146.67-80q-27 0-46.84-19.83Q80-119.67 80-146.67v-666.66q0-27 19.83-46.84Q119.67-880 146.67-880h666.66q27 0 46.84 19.83Q880-840.33 880-813.33v666.66q0 27-19.83 46.84Q840.33-80 813.33-80H146.67Zm0-66.67h666.66v-666.66H146.67v666.66Zm0 0v-666.66 666.66Z"/></svg>',
    "name": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M240-440h360v-80H240v80Zm0-120h360v-80H240v80Zm-80 400q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h640q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160Zm0-80h640v-480H160v480Zm0 0v-480 480Z"/></svg>',
    "model": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M280-280h280v-80H280v80Zm0-160h400v-80H280v80Zm0-160h400v-80H280v80Zm-80 480q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/></svg>',
    "negative_prompt": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M280-280h280v-80H280v80Zm0-160h400v-80H280v80Zm0-160h400v-80H280v80Zm-80 480q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/></svg>',
    "parameters": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M280-280h280v-80H280v80Zm0-160h400v-80H280v80Zm0-160h400v-80H280v80Zm-80 480q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/></svg>',
    "sort": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M120-240v-80h240v80H120Zm0-200v-80h480v80H120Zm0-200v-80h720v80H120Z"/></svg>',
    "created_date": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z"/></svg>',
    "edited_date": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M480-120q-75 0-140.5-28.5t-114-77q-48.5-48.5-77-114T120-480q0-75 28.5-140.5t77-114q48.5-48.5 114-77T480-840q82 0 155.5 35T760-706v-94h80v240H600v-80h110q-41-56-101-88t-129-32q-117 0-198.5 81.5T200-480q0 117 81.5 198.5T480-200q105 0 183.5-68T756-440h82q-15 137-117.5 228.5T480-120Zm112-192L440-464v-216h80v184l128 128-56 56Z"/></svg>',
    "imported_date": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h200v80H160v480h640v-480H600v-80h200q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160Zm320-184L280-544l56-56 104 104v-304h80v304l104-104 56 56-200 200Z"/></svg>',
    "rating_sort": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="m354-287 126-76 126 77-33-144 111-96-146-13-58-136-58 135-146 13 111 97-33 143ZM233-120l65-281L80-590l288-25 112-265 112 265 288 25-218 189 65 281-247-149-247 149Zm247-350Z"/></svg>',
    "filesize_sort": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M240-360h60v-180h40v120h60v-120h40v180h60v-200q0-17-11.5-28.5T460-600H280q-17 0-28.5 11.5T240-560v200Zm300 0h60v-60h80q17 0 28.5-11.5T720-460v-100q0-17-11.5-28.5T680-600H540v240Zm60-120v-60h60v60h-60ZM200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/></svg>',
    "close_dialog": '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="{color}"><path d="m251.33-204.67-46.66-46.66L433.33-480 204.67-708.67l46.66-46.66L480-526.67l228.67-228.66 46.66 46.66L526.67-480l228.66 228.67-46.66 46.66L480-433.33 251.33-204.67Z"/></svg>',
    "prompt": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M280-280h280v-80H280v80Zm0-160h400v-80H280v80Zm0-160h400v-80H280v80Zm-80 480q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/></svg>',
    "confirm": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="M453-280h60v-240h-60v240Zm50.5-323.2q9.5-9.2 9.5-22.8 0-14.45-9.48-24.22-9.48-9.78-23.5-9.78t-23.52 9.78Q447-640.45 447-626q0 13.6 9.48 22.8 9.48 9.2 23.5 9.2t23.52-9.2ZM480.27-80q-82.74 0-155.5-31.5Q252-143 197.5-197.5t-86-127.34Q80-397.68 80-480.5t31.5-155.66Q143-709 197.5-763t127.34-85.5Q397.68-880 480.5-880t155.66 31.5Q709-817 763-763t85.5 127Q880-563 880-480.27q0 82.74-31.5 155.5Q817-252 763-197.68q-54 54.31-127 86Q563-80 480.27-80Zm.23-60Q622-140 721-239.5t99-241Q820-622 721.19-721T480-820q-141 0-240.5 98.81T140-480q0 141 99.5 240.5t241 99.5Zm-.5-340Z"/></svg>',
    "reading_mode": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="M248-300q53.57 0 104.28 12.5Q403-275 452-250v-427q-45-30-97.62-46.5Q301.76-740 248-740q-38 0-74.5 9.5T100-707v434q31-14 70.5-20.5T248-300Zm264 50q50-25 98-37.5T712-300q38 0 78.5 6t69.5 16v-429q-34-17-71.82-25-37.82-8-76.18-8-54 0-104.5 16.5T512-677v427Zm-30 90q-51-38-111-58.5T248-239q-36.54 0-71.77 9T106-208q-23.1 11-44.55-3Q40-225 40-251v-463q0-15 7-27.5T68-761q42-20 87.39-29.5 45.4-9.5 92.61-9.5 63 0 122.5 17T482-731q51-35 109.5-52T712-800q46.87 0 91.93 9.5Q849-781 891-761q14 7 21.5 19.5T920-714v463q0 27.89-22.5 42.45Q875-194 853-208q-34-14-69.23-22.5Q748.54-239 712-239q-63 0-121 21t-109 58ZM276-489Z"/></svg>',
    "dark_mode": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="M480-120q-150 0-255-105T120-480q0-150 105-255t255-105q8 0 17 .5t23 1.5q-36 32-56 79t-20 99q0 90 63 153t153 63q52 0 99-18.5t79-51.5q1 12 1.5 19.5t.5 14.5q0 150-105 255T480-120Zm0-60q109 0 190-67.5T771-406q-25 11-53.67 16.5Q688.67-384 660-384q-114.69 0-195.34-80.66Q384-545.31 384-660q0-24 5-51.5t18-62.5q-98 27-162.5 109.5T180-480q0 125 87.5 212.5T480-180Zm-4-297Z"/></svg>',
    "light_mode": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="M579-381q41-41 41-99t-41-99q-41-41-99-41t-99 41q-41 41-41 99t41 99q41 41 99 41t99-41Zm-240.5 42.5Q280-397 280-480t58.5-141.5Q397-680 480-680t141.5 58.5Q680-563 680-480t-58.5 141.5Q563-280 480-280t-141.5-58.5ZM200-450H40v-60h160v60Zm720 0H760v-60h160v60ZM450-760v-160h60v160h-60Zm0 720v-160h60v160h-60ZM262-658l-100-97 43-44 96 100-39 41Zm494 496-98-100 41-41 99 98-42 43Zm-99-537 98-99 44 42-99 98-43-41ZM162-205l99-98 42 42-98 99-43-43Zm318-275Z"/></svg>',
    "align_center": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="M450-80v-800h60v800h-60Zm120-210v-380h100v380H570Zm-280 0v-380h100v380H290Z"/></svg>',
    "lock": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="M220-80q-24.75 0-42.37-17.63Q160-115.25 160-140v-434q0-24.75 17.63-42.38Q195.25-634 220-634h70v-96q0-78.85 55.61-134.42Q401.21-920 480.11-920q78.89 0 134.39 55.58Q670-808.85 670-730v96h70q24.75 0 42.38 17.62Q800-598.75 800-574v434q0 24.75-17.62 42.37Q764.75-80 740-80H220Zm0-60h520v-434H220v434Zm314.5-162.03Q557-324.06 557-355q0-30-22.67-54.5t-54.5-24.5q-31.83 0-54.33 24.5t-22.5 55q0 30.5 22.67 52.5t54.5 22q31.83 0 54.33-22.03ZM350-634h260v-96q0-54.17-37.88-92.08-37.88-37.92-92-37.92T388-822.08q-38 37.91-38 92.08v96ZM220-140v-434 434Z"/></svg>',
    "unlock": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="M220-634h390v-96q0-54.17-37.88-92.08-37.88-37.92-92-37.92T388-822.08q-38 37.91-38 92.08h-60q0-79 55.61-134.5 55.6-55.5 134.5-55.5 78.89 0 134.39 55.58Q670-808.85 670-730v96h70q24.75 0 42.38 17.62Q800-598.75 800-574v434q0 24.75-17.62 42.37Q764.75-80 740-80H220q-24.75 0-42.37-17.63Q160-115.25 160-140v-434q0-24.75 17.63-42.38Q195.25-634 220-634Zm0 494h520v-434H220v434Zm314.5-162.03Q557-324.06 557-355q0-30-22.67-54.5t-54.5-24.5q-31.83 0-54.33 24.5t-22.5 55q0 30.5 22.67 52.5t54.5 22q31.83 0 54.33-22.03ZM220-140v-434 434Z"/></svg>',
    "all_folder_close": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="m870-189-50-50v-441H456l-60-60h-77l-60-60h162l60 60h339q23 0 41.5 18.5T880-680v460q0 8-2.5 16t-7.5 15Zm-8 161L730-160H140q-24 0-42-18.5T80-220v-520q0-23 18-41.5t42-18.5h34l60 60h-94v520h530L56-834l42-42L904-70l-42 42ZM410-480Zm160-10Z"/></svg>',
    "all_folder_open": '<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="{color}"><path d="M140-160q-23 0-41.5-18.5T80-220v-520q0-23 18.5-41.5T140-800h281l60 60h339q23 0 41.5 18.5T880-680H455l-60-60H140v520l102-400h698L833-206q-6 24-22 35t-41 11H140Zm63-60h572l84-340H287l-84 340Zm0 0 84-340-84 340Zm-63-460v-60 60Z"/></svg>',
    "hide_form": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="m356-160-56-56 180-180 180 180-56 56-124-124-124 124Zm124-404L300-744l56-56 124 124 124-124 56 56-180 180Z"/></svg>',
    "show_form": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M120-240v-80h720v80H120Zm0-200v-80h720v80H120Zm0-200v-80h720v80H120Z"/></svg>',

    "dock_to_right": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M180-120q-24.75 0-42.37-17.63Q120-155.25 120-180v-600q0-24.75 17.63-42.38Q155.25-840 180-840h600q24.75 0 42.38 17.62Q840-804.75 840-780v600q0 24.75-17.62 42.37Q804.75-120 780-120H180Zm147-60v-600H180v600h147Zm60 0h393v-600H387v600Zm-60 0H180h147Z"/></svg>',
    "dock_to_left": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M180-120q-24.75 0-42.37-17.63Q120-155.25 120-180v-600q0-24.75 17.63-42.38Q155.25-840 180-840h600q24.75 0 42.38 17.62Q840-804.75 840-780v600q0 24.75-17.62 42.37Q804.75-120 780-120H180Zm453-60h147v-600H633v600Zm-60 0v-600H180v600h393Zm60 0h147-147Z"/></svg>',

    "night_sight_auto": '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="{color}"><path d="M440-190q59 0 110.5-27.5T641-290q-129-8-220-95.5T330-600q0-17 2.5-34.5T338-669q-65 36-106.5 96T190-440q0 104.17 72.92 177.08Q335.83-190 440-190Zm0 60q-129 0-219.5-90.5T130-440q0-129 90.5-219.5T440-750q-26 32-38 70.5T390-600q0 104.17 72.92 177.08Q535.83-350 640-350q26 0 52-5.5t50-16.5q-24 106-108.5 174T440-130Zm118-394 125.54-356H762l126 356h-72l-28.3-80H658.3L630-524h-72Zm116-130h98l-49-155-49 155ZM421-387Z"/></svg>',
}


def normalize_search_text(text):
    """検索の照合を安定させるための正規化。
    全角/半角・大文字/小文字・濁点結合などの表記ゆれを吸収する。
    - Unicode NFKC で全角英数記号→半角、半角カナ→全角カナ等に統一
    - 小文字化
    これを検索インデックス生成と検索語入力の両方に必ず通すことで、
    「全角で入れると出ない」「大文字だと出ない」といった取りこぼしを防ぐ。"""
    if not text:
        return ""
    return unicodedata.normalize("NFKC", str(text)).lower()


def build_size_search_tokens(file_size):
    """ファイルサイズを検索でヒットしやすい複数表記に展開する。
    生のバイト数に加え、"1.5mb" のような単位付き表記や整数丸めも含める。
    例: 1572864 → "1572864 1.5mb 2mb 1536kb"。"""
    if file_size is None:
        return ""
    try:
        size = float(file_size)
    except (TypeError, ValueError):
        return ""
    tokens = [str(int(size))]
    kb = size / 1024
    mb = kb / 1024
    if kb >= 0.1:
        tokens.append(f"{kb:.1f}kb")
        tokens.append(f"{int(round(kb))}kb")
    if mb >= 0.1:
        tokens.append(f"{mb:.1f}mb")
        tokens.append(f"{int(round(mb))}mb")
    return " ".join(tokens)


def render_svg_icon(icon_name, color=SVG_ICON_COLOR, size=24):
    """SVG_ICONSに登録したアイコンを、指定した色・サイズでラスタライズしQIconとして返す。
    見つからない名前を渡した場合は空のQIconを返す（呼び出し側でのクラッシュを避けるため）。"""
    svg_template = SVG_ICONS.get(icon_name)
    if not svg_template:
        return QIcon()
    svg_data = svg_template.replace("{color}", color)
    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def create_icon_label_row(icon_name, text, icon_size=16, heading=False):
    """アイコン＋テキストラベルを横に並べた、クリック不可の表示用ウィジェットを作る。
    フォーム名・フィールド名にアイコンを添える際の共通部品。
    heading=True の場合は見出し用のフォントサイズを適用する。"""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING_XS)
    
    lbl_icon = QLabel()
    icon = render_svg_icon(icon_name, size=icon_size)
    lbl_icon.setPixmap(icon.pixmap(icon_size, icon_size))
    lbl_icon.setFixedSize(icon_size, icon_size)
    
    lbl_text = QLabel(text)
    if heading:
        lbl_text.setObjectName("lbl_section_heading")
    
    layout.addWidget(lbl_icon)
    layout.addWidget(lbl_text)
    return container


def show_confirm_dialog(parent, title, text, buttons=None, default_button=None, min_width=None):
    """はい/いいえ等の選択を伴う確認ポップアップを表示する。
    アイコンは標準アイコンではなく、指定のSVG（確認アイコン）に統一する。
    min_width を指定すると、その幅を下回らないようウィンドウを広げる（文章が折り返さないようにするため）。
    戻り値は押されたボタン（QMessageBox.Yes / QMessageBox.No 等）。"""
    if buttons is None:
        buttons = QMessageBox.Yes | QMessageBox.No
    if default_button is None:
        default_button = QMessageBox.No
    
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(buttons)
    box.setDefaultButton(default_button)
    box.setIconPixmap(render_svg_icon("confirm", size=48).pixmap(48, 48))
    theme_source = parent
    if theme_source is not None and not hasattr(theme_source, "theme_colors") and hasattr(theme_source, "main_app"):
        theme_source = theme_source.main_app
    if theme_source is not None and hasattr(theme_source, "theme_colors") and hasattr(theme_source, "build_stylesheet"):
        box.setStyleSheet(theme_source.build_stylesheet(theme_source.theme_colors))
    if min_width:
        box_layout = box.layout()
        spacer = QSpacerItem(min_width, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        box_layout.addItem(spacer, box_layout.rowCount(), 0, 1, box_layout.columnCount())
    return box.exec()


def show_notification(parent, title, text, min_width=None):
    """情報・警告・エラーを知らせる通知ポップアップ（OKのみ）を表示する。
    OS標準の種類別アイコン（！三角・i丸・×赤）はテーマや役割ごとにバラバラで
    見た目が揃わないため、アプリ内で共通のSVGアイコン（confirm）に統一し、
    確認ダイアログ（show_confirm_dialog）と同じ外観にする。
    従来の QMessageBox.information / warning / critical の置き換え用。
    戻り値は使わない前提（fire-and-forget）。"""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.Ok)
    box.setDefaultButton(QMessageBox.Ok)
    box.setIconPixmap(render_svg_icon("confirm", size=48).pixmap(48, 48))
    theme_source = parent
    if theme_source is not None and not hasattr(theme_source, "theme_colors") and hasattr(theme_source, "main_app"):
        theme_source = theme_source.main_app
    if theme_source is not None and hasattr(theme_source, "theme_colors") and hasattr(theme_source, "build_stylesheet"):
        box.setStyleSheet(theme_source.build_stylesheet(theme_source.theme_colors))
    if min_width:
        box_layout = box.layout()
        spacer = QSpacerItem(min_width, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        box_layout.addItem(spacer, box_layout.rowCount(), 0, 1, box_layout.columnCount())
    return box.exec()


SYNC_HISTORY_CATEGORY_LABELS = {
    "folder_missing": "フォルダが見つからない",
    "image_missing": "画像ファイルが見つからない",
    "import_error": "取り込みエラー",
}


def write_sync_history_csv(save_path, rows):
    """同期履歴の行データ（database.get_sync_history()の戻り値）をCSVファイルに書き出す。
    文字コードはUTF-8 with BOMとし、WindowsのExcelで開いても文字化けしないようにする。"""
    with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["日時", "種別", "対象パス", "内容"])
        for timestamp, category, target_path, detail in rows:
            writer.writerow([timestamp, SYNC_HISTORY_CATEGORY_LABELS.get(category, category), target_path, detail])


class SyncHistoryDialog(QDialog):
    """同期処理で検出された「フォルダ／画像が見つからない」「取り込みエラー」の履歴一覧を表示するダイアログ。
    直近 database.MAX_SYNC_HISTORY_ROWS 件まで保持され、それを超えると古いものから自動的に削除される。
    同期結果のポップアップにある「履歴」ボタン、および設定画面の「同期履歴をエクスポート」からも開ける。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_app_ref = parent
        if self._main_app_ref is not None and not hasattr(self._main_app_ref, "tr") and hasattr(self._main_app_ref, "main_app"):
            self._main_app_ref = self._main_app_ref.main_app
        self.setWindowTitle(self.tr("dialog.sync_history.title"))
        self.setMinimumSize(700, 480)
        self.resize(900, 560)

        self.rows = database.get_sync_history()

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)

        if self.rows:
            table = QTableWidget(len(self.rows), 4)
            table.setHorizontalHeaderLabels([
                self.tr("dialog.sync_history.header_datetime"),
                self.tr("dialog.sync_history.header_type"),
                self.tr("dialog.sync_history.header_path"),
                self.tr("dialog.sync_history.header_detail"),
            ])
            table.horizontalHeader().setStretchLastSection(True)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setAlternatingRowColors(True)
            table.verticalHeader().setVisible(False)

            for row_idx, (timestamp, category, target_path, detail) in enumerate(self.rows):
                table.setItem(row_idx, 0, QTableWidgetItem(str(timestamp or "")))
                table.setItem(row_idx, 1, QTableWidgetItem(SYNC_HISTORY_CATEGORY_LABELS.get(category, category)))
                table.setItem(row_idx, 2, QTableWidgetItem(target_path or ""))
                table.setItem(row_idx, 3, QTableWidgetItem(detail or ""))

            table.resizeColumnsToContents()
            layout.addWidget(table)
        else:
            lbl_empty = QLabel(self.tr("dialog.sync_history.empty"))
            lbl_empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_empty)

        btn_row = QHBoxLayout()
        btn_export = QPushButton(self.tr("dialog.sync_history.export_button"))
        btn_export.clicked.connect(self.export_history_csv)
        btn_export.setEnabled(bool(self.rows))
        btn_close = QPushButton(self.tr("common.button.close"))
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_export)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        theme_source = parent
        if theme_source is not None and not hasattr(theme_source, "theme_colors") and hasattr(theme_source, "main_app"):
            theme_source = theme_source.main_app
        if theme_source is not None and hasattr(theme_source, "theme_colors") and hasattr(theme_source, "build_stylesheet"):
            self.setStyleSheet(theme_source.build_stylesheet(theme_source.theme_colors))

    def tr(self, key):
        if self._main_app_ref is not None and hasattr(self._main_app_ref, "tr"):
            return self._main_app_ref.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)

    def export_history_csv(self):
        default_path = os.path.join(get_default_export_dir(), "sync_history.csv")
        save_path, _ = QFileDialog.getSaveFileName(self, self.tr("dialog.csv_save_title"), default_path, "CSVファイル (*.csv)")
        if not save_path:
            return
        try:
            write_sync_history_csv(save_path, self.rows)
        except Exception as e:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.csv_write_failed").format(error=e))
            return
        show_notification(self, self.tr("common.title.export_complete"), self.tr("notify.sync_history_export_done").format(count=len(self.rows), save_path=save_path))


class SequenceRenamePreviewDialog(QDialog):
    """「リネーム時に編集画面を表示する」がオンの場合に、一括リネーム／一括で書き出す
    実行前に開く確認・編集ダイアログ（シンプル版）。
    生成された名前（拡張子を除く）を1件ずつ一覧表示する。表自体はダブルクリックでは
    編集させず（QTableWidgetの標準セル編集は、選択中の行の背景色とエディタの配色が
    噛み合わず文字が読めなくなる問題があったため、2026-08-15に廃止）、代わりに
    行を選択すると、下の「名前」欄（他の設定画面と同じ、見た目が確実なQLineEdit）に
    値が読み込まれ、そこで編集した内容がテーブルへ反映される方式にしている。
    同じ名前が複数行にあると赤系でハイライトし、解消するまでOKボタンを無効化する。"""
    def __init__(self, parent, title, rows, extra_note="", column_labels=None, hint_text=None):
        super().__init__(parent)
        self._main_app_ref = parent
        if self._main_app_ref is not None and not hasattr(self._main_app_ref, "tr") and hasattr(self._main_app_ref, "main_app"):
            self._main_app_ref = self._main_app_ref.main_app
        self.setWindowTitle(title)
        self.setMinimumSize(560, 400)
        self.resize(640, 460)

        if column_labels is None:
            column_labels = (self.tr("dialog.rename_table.column_current_name"), self.tr("dialog.rename_table.column_new_name"))

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)

        if hint_text is None:
            hint_text = self.tr("dialog.rename_table.hint_default")
        if extra_note:
            hint_text += extra_note
        lbl_hint = QLabel(hint_text)
        lbl_hint.setWordWrap(True)
        layout.addWidget(lbl_hint)

        self.table = QTableWidget(len(rows), 2)
        self.table.setHorizontalHeaderLabels(list(column_labels))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        for row_idx, (old_label, new_base) in enumerate(rows):
            item_old = QTableWidgetItem(old_label)
            item_old.setFlags(item_old.flags() & ~Qt.ItemIsEditable)
            item_new = QTableWidgetItem(new_base)
            item_new.setFlags(item_new.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, item_old)
            self.table.setItem(row_idx, 1, item_new)

        layout.addWidget(self.table)

        edit_row = QHBoxLayout()
        lbl_edit = QLabel(self.tr("common.label.name"))
        lbl_edit.setFixedWidth(50)
        self.txt_selected_name = QLineEdit()
        self.txt_selected_name.setEnabled(False)
        self.txt_selected_name.textEdited.connect(self._apply_selected_name)
        edit_row.addWidget(lbl_edit)
        edit_row.addWidget(self.txt_selected_name)
        layout.addLayout(edit_row)

        self.table.itemSelectionChanged.connect(self._load_selected_name)

        self.lbl_warning = QLabel("")
        self.lbl_warning.setObjectName("lbl_import_format_note")
        layout.addWidget(self.lbl_warning)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = QPushButton(self.tr("common.button.cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton(self.tr("dialog.rename_table.execute_button"))
        self.btn_ok.setObjectName("btn_save")
        self.btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_ok)
        layout.addLayout(btn_row)

        self.table.selectRow(0)
        self._validate_duplicates()

        theme_source = parent
        if theme_source is not None and not hasattr(theme_source, "theme_colors") and hasattr(theme_source, "main_app"):
            theme_source = theme_source.main_app
        if theme_source is not None and hasattr(theme_source, "theme_colors") and hasattr(theme_source, "build_stylesheet"):
            self.setStyleSheet(theme_source.build_stylesheet(theme_source.theme_colors))

    def tr(self, key):
        if self._main_app_ref is not None and hasattr(self._main_app_ref, "tr"):
            return self._main_app_ref.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)

    def _load_selected_name(self):
        """テーブルの選択行が変わったら、その行の現在の名前を下の入力欄に読み込む。"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.txt_selected_name.setEnabled(False)
            self.txt_selected_name.clear()
            return
        row = rows[0].row()
        self.txt_selected_name.setEnabled(True)
        self.txt_selected_name.blockSignals(True)
        self.txt_selected_name.setText(self.table.item(row, 1).text())
        self.txt_selected_name.blockSignals(False)

    def _apply_selected_name(self, text):
        """下の入力欄で編集した内容を、選択中の行のテーブル表示へそのまま反映する。"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        self.table.item(row, 1).setText(text)
        self._validate_duplicates()

    def _validate_duplicates(self):
        """「変更後の名前」列に重複がないか確認し、あれば該当行を赤系背景で示してOKを無効化する。"""
        values = [self.table.item(r, 1).text().strip() for r in range(self.table.rowCount())]
        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1

        has_problem = False
        for r, v in enumerate(values):
            item = self.table.item(r, 1)
            if not v:
                item.setBackground(QColor("#e2725b"))
                has_problem = True
            elif counts[v] > 1:
                item.setBackground(QColor("#e2725b"))
                has_problem = True
            else:
                item.setBackground(QColor(0, 0, 0, 0))

        self.btn_ok.setEnabled(not has_problem)
        self.lbl_warning.setText(self.tr("dialog.rename_table.warning_duplicate_or_empty") if has_problem else "")

    def get_new_names(self):
        """行の並び順のまま、編集後の「変更後の名前」一覧を返す。"""
        return [self.table.item(r, 1).text().strip() for r in range(self.table.rowCount())]


def show_sync_result_dialog(parent, title, text):
    """同期処理の結果を知らせるポップアップ。通常の通知（show_notification）と異なり、
    「履歴」ボタンから、これまでに記録された同期履歴（SyncHistoryDialog）をその場で開ける。"""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    btn_history = box.addButton("履歴", QMessageBox.ActionRole)
    btn_ok = box.addButton(QMessageBox.Ok)
    box.setDefaultButton(btn_ok)
    box.setIconPixmap(render_svg_icon("confirm", size=48).pixmap(48, 48))
    theme_source = parent
    if theme_source is not None and not hasattr(theme_source, "theme_colors") and hasattr(theme_source, "main_app"):
        theme_source = theme_source.main_app
    if theme_source is not None and hasattr(theme_source, "theme_colors") and hasattr(theme_source, "build_stylesheet"):
        box.setStyleSheet(theme_source.build_stylesheet(theme_source.theme_colors))
    box.exec()
    if box.clickedButton() == btn_history:
        SyncHistoryDialog(parent).exec()


class FlowLayout(QLayout):
    """子ウィジェットを左から並べ、幅が足りなくなったら自動的に次の段へ折り返すレイアウト。
    ウィンドウ（ペイン）が広いときは1段の横一列で表示し、狭いときだけ多段になる可変表示を実現する。
    Qt公式の Flow Layout サンプルを参考にした実装。"""

    def __init__(self, parent=None, margin=0, hspacing=6, vspacing=6, center=False):
        super().__init__(parent)
        self._items = []
        self._hspacing = hspacing
        self._vspacing = vspacing
        self._center = center
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(left, top, -right, -bottom)
        y = effective.y()

        def place_row(row_items, row_y, row_height):
            if not row_items:
                return
            total_w = sum(it.sizeHint().width() for it in row_items) + self._hspacing * (len(row_items) - 1)
            if self._center:
                start_x = effective.x() + max(0, (effective.width() - total_w) // 2)
            else:
                start_x = effective.x()
            cx = start_x
            for it in row_items:
                if not test_only:
                    it.setGeometry(QRect(QPoint(cx, row_y), it.sizeHint()))
                cx += it.sizeHint().width() + self._hspacing

        row = []
        row_width = 0
        line_height = 0
        for item in self._items:
            w = item.sizeHint().width()
            h = item.sizeHint().height()
            added = w if not row else row_width + self._hspacing + w
            if row and added > effective.width():
                if not test_only:
                    place_row(row, y, line_height)
                y += line_height + self._vspacing
                row = [item]
                row_width = w
                line_height = h
            else:
                row.append(item)
                row_width = added
                line_height = max(line_height, h)
        if row and not test_only:
            place_row(row, y, line_height)
        return y + line_height - rect.y() + bottom


class CenteredComboBox(QComboBox):
    """選択中の項目のテキストを中央揃えで表示するコンボボックス。
    通常のQComboBoxは表示テキストが左端に寄ってしまうため、内部の行編集を
    読み取り専用にした上で中央揃えにし、クリック時は通常どおりドロップダウンを開く。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setAlignment(Qt.AlignCenter)
        self.lineEdit().installEventFilter(self)
        self.setInsertPolicy(QComboBox.NoInsert)

    def eventFilter(self, obj, event):
        if obj is self.lineEdit() and event.type() == QEvent.MouseButtonPress:
            self.showPopup()
            return True
        return super().eventFilter(obj, event)


class ImageListWidget(QListWidget):
    """通常のQListWidgetに加え、選択中の画像をFinder/エクスプローラーへ
    ドラッグ＆ドロップで“コピー専用”で渡せるようにしたリストウィジェット。
    オリジナル画像を誤って移動・削除してしまわないよう、常にコピー動作に固定する。
    また、外部（Finder等）から画像ファイルやフォルダをドラッグ＆ドロップして
    直接取り込めるように、外部ファイルのドロップも受け付ける。"""
    filesDropped = Signal(list)
    dragHoverChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setAcceptDrops(False)
        self._folder_drag_start_pos = None
        self._folder_drag_dir = None
        self.empty_overlay = QLabel("", self)
        self.empty_overlay.setObjectName("lbl_search_empty_overlay")
        self.empty_overlay.setAlignment(Qt.AlignCenter)
        self.empty_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.empty_overlay.hide()

    def set_empty_overlay(self, text):
        """一致0件メッセージの表示/非表示。text が空なら隠す。"""
        if text:
            self.empty_overlay.setText(text)
            self._reposition_empty_overlay()
            self.empty_overlay.show()
            self.empty_overlay.raise_()
        else:
            self.empty_overlay.hide()

    def _reposition_empty_overlay(self):
        """オーバーレイをビューポート全体に追従させる。"""
        vp = self.viewport()
        self.empty_overlay.setGeometry(vp.geometry())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.empty_overlay.isVisible():
            self._reposition_empty_overlay()

    def mimeData(self, items):
        mime = QMimeData()
        urls = []
        for item in items:
            f_path = item.data(Qt.UserRole + 1)
            if f_path and os.path.exists(f_path):
                urls.append(QUrl.fromLocalFile(f_path))
        mime.setUrls(urls)
        return mime

    def startDrag(self, supportedActions):
        """ドラッグ操作を独自に実行し、アクションを「コピー」のみに限定する。
        Qtの既定動作ではCmd（Ctrl）キーの有無で移動/コピーが切り替わるが、
        ここでは常にコピーのみを許可することで、オリジナルファイルが
        ドロップ先へ「移動」されて元の場所から消えてしまう事故を防ぐ。"""
        items = self.selectedItems()
        if not items:
            return
        
        drag = QDrag(self)
        drag.setMimeData(self.mimeData(items))
        
        first_icon = items[0].icon()
        if not first_icon.isNull():
            drag.setPixmap(first_icon.pixmap(64, 64))
        
        drag.exec(Qt.CopyAction, Qt.CopyAction)

    def mousePressEvent(self, event):
        """フォルダ見出し行の上で押された場合、その実フォルダのパスを覚えておく
        （見出し行は選択不可のため、通常のitemドラッグ機構は使えない）。"""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item is not None and item.data(Qt.UserRole) is None and item.data(Qt.UserRole + 8) is not None:
                self._folder_drag_start_pos = event.pos()
                self._folder_drag_dir = item.data(Qt.UserRole + 15)
            else:
                self._folder_drag_start_pos = None
                self._folder_drag_dir = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """フォルダ見出し行からのドラッグ距離がしきい値を超えたら、実フォルダを
        Finder等へ「コピー専用」でドラッグ開始する。"""
        if (self._folder_drag_start_pos is not None and self._folder_drag_dir
                and event.buttons() & Qt.LeftButton):
            if (event.pos() - self._folder_drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                folder_dir = self._folder_drag_dir
                self._folder_drag_start_pos = None
                self._folder_drag_dir = None
                if os.path.isdir(folder_dir):
                    mime = QMimeData()
                    mime.setUrls([QUrl.fromLocalFile(folder_dir)])
                    drag = QDrag(self)
                    drag.setMimeData(mime)
                    drag.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon).pixmap(48, 48))
                    drag.exec(Qt.CopyAction, Qt.CopyAction)
                return
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        """外部（Finder等）からのファイル/フォルダのドラッグを受け付ける"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.dragHoverChanged.emit(True)
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        """ドロップせずにドラッグがリスト外に出た場合、通常表示に戻す"""
        self.dragHoverChanged.emit(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """外部からドロップされたファイル/フォルダのパスを取り出し、シグナルで通知する"""
        mime = event.mimeData()
        if mime.hasUrls():
            paths = [url.toLocalFile() for url in mime.urls() if url.isLocalFile()]
            paths = [p for p in paths if p]
            if paths:
                event.setDropAction(Qt.CopyAction)
                event.accept()
                self.dragHoverChanged.emit(False)
                self.filesDropped.emit(paths)
                return
        self.dragHoverChanged.emit(False)
        super().dropEvent(event)


class FolderHeaderDelegate(QStyledItemDelegate):
    """フォルダ別グループ表示の「見出し行」だけを自前描画するデリゲート。
    画像行は既定の描画（super）にそのまま委ねる。

    QListWidget に適用している QSS（color: list_text）は、既定デリゲートの
    テキスト描画色を一律に固定するため、setForeground() やリッチテキストによる
    部分的な色分けが効かない。そこで見出し行のみを手描きし、
      ・フォルダ名（太字・通常色）と 件数（数字のみ・薄いグレー）を描き分ける（2.2）
      ・「折りたたみ中は検索対象外」の注記を、フォルダ名の下段に小さめ・薄めで出す（2.1）
    を実現する。描画に必要な値は QListWidgetItem のロールから受け取る:
      UserRole   : 画像ID（見出し行では None）… 見出し判定に使用
      UserRole+8 : フォルダ名
      UserRole+12: 件数（int）
      UserRole+13: 注記文字列（無い場合は空）
      UserRole+14: インジケータ（▶ / ▼）
    """

    def __init__(self, app):
        super().__init__(app)
        self._app = app

    def _is_header(self, index):
        return index.data(Qt.UserRole) is None and index.data(Qt.UserRole + 8) is not None

    def _fonts(self, option):
        name_font = QFont(option.font)
        name_font.setBold(True)
        name_font.setPixelSize(FONT_SIZE_BODY)
        count_font = QFont(option.font)
        count_font.setBold(False)
        count_font.setPixelSize(FONT_SIZE_BODY)
        note_font = QFont(option.font)
        note_font.setBold(False)
        note_font.setPixelSize(FONT_SIZE_CAPTION)
        return name_font, count_font, note_font

    def sizeHint(self, option, index):
        if not self._is_header(index):
            return super().sizeHint(option, index)
        name_font, _count_font, note_font = self._fonts(option)
        note = index.data(Qt.UserRole + 13) or ""
        h = QFontMetrics(name_font).height()
        if note:
            h += QFontMetrics(note_font).height()
        h += 2 * SPACING_XS
        base = super().sizeHint(option, index)
        return QSize(base.width(), max(base.height(), h))

    def paint(self, painter, option, index):
        if not self._is_header(index):
            super().paint(painter, option, index)
            return

        painter.save()
        rect = option.rect

        colors = getattr(self._app, "theme_colors", None) or {}
        header_bg = colors.get("group_header_bg")
        if header_bg:
            painter.fillRect(rect, QColor(header_bg))
        elif index.data(Qt.BackgroundRole) is not None:
            painter.fillRect(rect, index.data(Qt.BackgroundRole))

        folder_name = index.data(Qt.UserRole + 8) or ""
        count = index.data(Qt.UserRole + 12)
        count = 0 if count is None else int(count)
        note = index.data(Qt.UserRole + 13) or ""
        indicator = index.data(Qt.UserRole + 14) or "▼"

        name_font, count_font, note_font = self._fonts(option)
        fm_name = QFontMetrics(name_font)
        fm_count = QFontMetrics(count_font)
        fm_note = QFontMetrics(note_font)

        name_color = QColor(colors.get("list_text", "#dddddd"))
        dim_color = QColor(colors.get("metadata_text", "#888888"))

        pad = SPACING_SM
        gap = SPACING_XS

        primary_h = fm_name.height()
        note_h = fm_note.height() if note else 0
        top = rect.top() + max(0, (rect.height() - (primary_h + note_h)) // 2)
        x = rect.left() + pad

        icon = index.data(Qt.DecorationRole)
        icon_size = 16
        if icon is not None and not icon.isNull():
            pm = icon.pixmap(icon_size, icon_size)
            iy = top + max(0, (primary_h - icon_size) // 2)
            painter.drawPixmap(x, iy, pm)
            x += icon_size + gap

        painter.setFont(name_font)
        painter.setPen(name_color)
        ind_w = fm_name.horizontalAdvance(indicator)
        painter.drawText(QRect(x, top, ind_w, primary_h), Qt.AlignLeft | Qt.AlignVCenter, indicator)
        x += ind_w + gap

        name_w = fm_name.horizontalAdvance(folder_name)
        painter.drawText(QRect(x, top, name_w, primary_h), Qt.AlignLeft | Qt.AlignVCenter, folder_name)
        x += name_w + gap * 2

        painter.setFont(count_font)
        painter.setPen(dim_color)
        count_text = f"（{count}）"
        count_w = fm_count.horizontalAdvance(count_text)
        painter.drawText(QRect(x, top, count_w, primary_h), Qt.AlignLeft | Qt.AlignVCenter, count_text)

        if note:
            painter.setFont(note_font)
            painter.setPen(dim_color)
            note_x = rect.left() + pad
            note_w = max(0, rect.right() - note_x - pad)
            painter.drawText(QRect(note_x, top + primary_h, note_w, note_h),
                             Qt.AlignLeft | Qt.AlignVCenter, note)

        painter.restore()


class StarRatingWidget(QWidget):
    """マウスオーバーで星を先読みハイライトし、クリックで評価を確定する5段階の星評価ウィジェット。
    星0個（デフォルト）はすべてグレー表示。"""
    ratingChanged = Signal(int)

    def __init__(self, parent=None, max_stars=5):
        super().__init__(parent)
        self.max_stars = max_stars
        self.rating = 0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(STAR_SPACING)
        
        self.star_labels = []
        for i in range(1, max_stars + 1):
            lbl = QLabel("★")
            lbl.setObjectName("star_label")
            lbl.setProperty("filled", False)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(22, 26)
            font = lbl.font()
            font.setPointSize(15)
            lbl.setFont(font)
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.setMouseTracking(True)
            lbl.installEventFilter(self)
            self.star_labels.append(lbl)
            layout.addWidget(lbl)

    def set_rating(self, value, emit_signal=False):
        self.rating = max(0, min(self.max_stars, value))
        self._update_display(self.rating)
        if emit_signal:
            self.ratingChanged.emit(self.rating)

    def _update_display(self, filled_count):
        for i, lbl in enumerate(self.star_labels, start=1):
            lbl.setProperty("filled", i <= filled_count)
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

    def eventFilter(self, obj, event):
        if obj in self.star_labels:
            index = self.star_labels.index(obj) + 1
            if event.type() in (QEvent.Enter, QEvent.MouseMove):
                self._update_display(index)
                return False
            elif event.type() == QEvent.MouseButtonRelease:
                if index == self.rating:
                    self.set_rating(0, emit_signal=True)
                else:
                    self.set_rating(index, emit_signal=True)
                return False
        return super().eventFilter(obj, event)

    def leaveEvent(self, event):
        self._update_display(self.rating)
        super().leaveEvent(event)


class PreviewLabel(QLabel):
    """プレビュー画像表示用のQLabel。
    通常のQLabelは、表示中のpixmapの内容に応じてsizeHint()が変動する。これがExpanding
    ポリシーと組み合わさると、「画像送り→pixmap設定→sizeHint変化→レイアウト割り当ても変化」という
    フィードバックループになり、標準サイズ表示の画像が送るたびに徐々に肥大化するバグの原因になっていた。
    sizeHintをminimumSize基準の固定値にすることでこのループを断ち切りつつ、Expandingポリシー自体は
    維持することで、全画面表示など「空いた領域を埋める」動作は引き続き正しく機能するようにする。

    また、表示中の画像をFinder等の外部アプリへドラッグ＆ドロップで取り出せるようにする
    （画像リストの既存ドラッグ実装と同様、常に「コピー」のみを許可し、元ファイルを
    誤って移動してしまう事故を防ぐ）。main_app を保持し、ドラッグ開始時に
    main_app.current_preview_path を参照する。

    プレビューエリアを一度クリックしてフォーカスを与えると、以後は左右キーで
    前後の画像に送れる（2026-08-14〜）。QLabelは既定でフォーカスを受け取らないため、
    setFocusPolicy(Qt.ClickFocus) でクリック時のみフォーカスを持てるようにしている
    （常時ホバーで反応する方式ではなく、検索欄等から意図せずフォーカスを奪わないよう、
    明示的なクリックを条件にする方針とした）。"""
    def __init__(self, *args, main_app=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_app = main_app
        self._drag_start_pos = None
        self.setFocusPolicy(Qt.ClickFocus)

    def sizeHint(self):
        return self.minimumSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (self._drag_start_pos is not None and event.buttons() & Qt.LeftButton
                and self.main_app is not None):
            current_pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if (current_pos - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                f_path = getattr(self.main_app, "current_preview_path", None)
                if f_path and os.path.exists(f_path):
                    self._drag_start_pos = None
                    mime = QMimeData()
                    mime.setUrls([QUrl.fromLocalFile(f_path)])
                    drag = QDrag(self)
                    drag.setMimeData(mime)
                    pixmap = self.pixmap()
                    if pixmap is not None and not pixmap.isNull():
                        drag.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    drag.exec(Qt.CopyAction, Qt.CopyAction)
                    return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.main_app is not None and event.key() == Qt.Key_Left:
            self.main_app.prev_image()
        elif self.main_app is not None and event.key() == Qt.Key_Right:
            self.main_app.next_image()
        else:
            super().keyPressEvent(event)


READING_MODE_THEMES = {
    "dark": {
        "bg": "#000000",
        "control_bar_bg": "rgba(20, 20, 20, 220)",
        "button_bg": "#333333",
        "button_hover": "#4a4a4a",
        "button_text": "#ffffff",
        "indicator_bg": "rgba(0, 0, 0, 150)",
        "indicator_text": "#ffffff",
    },
    "light": {
        "bg": "#f2f2f2",
        "control_bar_bg": "rgba(230, 230, 230, 230)",
        "button_bg": "#dcdcdc",
        "button_hover": "#c9c9c9",
        "button_text": "#222222",
        "indicator_bg": "rgba(255, 255, 255, 210)",
        "indicator_text": "#222222",
    },
}


class ReadingModeWindow(QWidget):
    """見開き表示（読書モード）。選択した画像と同じフォルダ内の画像を、本のように2枚並べて全画面表示する。
    閲覧専用（このモード中の編集は不可）。パターンA（左開き）/ B（右開き）を切り替え可能で、
    切り替えはこのセッション限りの一時的なものとし、設定画面の既定値は変更しない。
    
    ページの並び順は、アプリの現在の並べ替え設定に関わらず、常に「名前順」で固定する
    （評価順などのままでは、見開きとして成立しないため）。
    
    背景（ダーク/ライト）は、アプリ本体のテーマ設定とは独立した専用の設定として持ち、
    次回もこのモードを開いた時に記憶される。
    """
    def __init__(self, main_app, image_rows, start_index):
        super().__init__()
        self.main_app = main_app
        self.image_rows = image_rows
        self.pattern = database.get_setting("reading_mode_default_pattern", "A")
        self.theme = database.get_setting("reading_mode_theme", "dark")
        self.center_align = database.get_setting("reading_mode_center_align", "0") == "1"
        self._pixmap_cache = {}
        
        self.spread_start = start_index - (start_index % 2)
        
        self.setWindowTitle(self.tr("reading.title"))
        self.setFocusPolicy(Qt.StrongFocus)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        image_row_layout = QHBoxLayout()
        image_row_layout.setContentsMargins(0, 0, 0, 0)
        image_row_layout.setSpacing(0)
        self.lbl_left = QLabel()
        self.lbl_right = QLabel()
        if self.center_align:
            self.lbl_left.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lbl_right.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        else:
            self.lbl_left.setAlignment(Qt.AlignCenter)
            self.lbl_right.setAlignment(Qt.AlignCenter)
        image_row_layout.addWidget(self.lbl_left, 1)
        image_row_layout.addWidget(self.lbl_right, 1)
        layout.addLayout(image_row_layout, 1)
        
        self.control_bar = QWidget()
        control_layout = QHBoxLayout(self.control_bar)
        control_layout.setContentsMargins(SPACING_LG, SPACING_SM, SPACING_LG, SPACING_SM)
        control_layout.setSpacing(SPACING_SM)
        
        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setIconSize(QSize(16, 16))
        self.btn_theme_toggle.setToolTip(self.tr("reading.tooltip.theme_toggle"))
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        control_layout.addWidget(self.btn_theme_toggle)

        self.btn_center_align_toggle = QPushButton()
        self.btn_center_align_toggle.setIconSize(QSize(16, 16))
        self.btn_center_align_toggle.setToolTip(self.tr("reading.tooltip.center_align_toggle"))
        self.btn_center_align_toggle.clicked.connect(self.toggle_center_align)
        control_layout.addWidget(self.btn_center_align_toggle)

        self.btn_jump_first = QPushButton()
        self.btn_jump_first.setIconSize(QSize(16, 16))
        self.btn_jump_first.setToolTip(self.tr("reading.tooltip.jump_first"))
        self.btn_jump_first.clicked.connect(self.jump_to_first)
        control_layout.addWidget(self.btn_jump_first)
        
        self.slider = QSlider(Qt.Horizontal)
        total_spreads = max(1, (len(self.image_rows) + 1) // 2)
        self.slider.setMinimum(0)
        self.slider.setMaximum(max(0, total_spreads - 1))
        self.slider.setValue(self.spread_start // 2)
        self.slider.valueChanged.connect(self.on_slider_changed)
        control_layout.addWidget(self.slider, 1)
        
        self.btn_jump_last = QPushButton()
        self.btn_jump_last.setIconSize(QSize(16, 16))
        self.btn_jump_last.setToolTip(self.tr("reading.tooltip.jump_last"))
        self.btn_jump_last.clicked.connect(self.jump_to_last)
        control_layout.addWidget(self.btn_jump_last)

        self.btn_pattern_a = QPushButton(self.tr("reading.button.pattern_a"))
        self.btn_pattern_a.setIconSize(QSize(14, 14))
        self.btn_pattern_a.setToolTip(self.tr("reading.tooltip.pattern_a"))
        self.btn_pattern_a.clicked.connect(lambda: self.set_pattern("A"))
        control_layout.addWidget(self.btn_pattern_a)

        self.btn_pattern_b = QPushButton(self.tr("reading.button.pattern_b"))
        self.btn_pattern_b.setIconSize(QSize(14, 14))
        self.btn_pattern_b.setToolTip(self.tr("reading.tooltip.pattern_b"))
        self.btn_pattern_b.clicked.connect(lambda: self.set_pattern("B"))
        control_layout.addWidget(self.btn_pattern_b)

        self.btn_exit = QPushButton(self.tr("reading.button.exit"))
        self.btn_exit.setIconSize(QSize(14, 14))
        self.btn_exit.clicked.connect(self.close)
        control_layout.addWidget(self.btn_exit)
        
        layout.addWidget(self.control_bar)
        
        self.lbl_pattern_indicator = QLabel(self)
        
        self.apply_theme()
        self.update_pattern_indicator()
        self.showFullScreen()
        QTimer.singleShot(0, self.update_spread_display)

    def tr(self, key):
        if hasattr(self.main_app, "tr"):
            return self.main_app.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)

    def apply_theme(self):
        """背景・コントロールバー・各ボタン・パターン表示ラベルの配色を、現在のテーマ（dark/light）で統一する。
        アイコンの色も、背景とのコントラストが保てるようテーマに合わせて再生成する。"""
        c = READING_MODE_THEMES[self.theme]
        
        self.setStyleSheet(f"background-color: {c['bg']};")
        self.lbl_left.setStyleSheet(f"background-color: {c['bg']}; color: {c['button_text']};")
        self.lbl_right.setStyleSheet(f"background-color: {c['bg']}; color: {c['button_text']};")
        self.control_bar.setStyleSheet(f"background-color: {c['control_bar_bg']};")
        
        self._control_button_style = (
            f"QPushButton {{ background-color: {c['button_bg']}; color: {c['button_text']}; "
            f"border: none; border-radius: 4px; padding: 6px 10px; }}"
            f"QPushButton:hover {{ background-color: {c['button_hover']}; }}"
        )
        icon_color = c['button_text']
        
        self.btn_theme_toggle.setIcon(render_svg_icon("light_mode" if self.theme == "dark" else "dark_mode", size=16, color=icon_color))
        self.btn_theme_toggle.setToolTip(self.tr("reading.tooltip.theme_toggle_to_light") if self.theme == "dark" else self.tr("reading.tooltip.theme_toggle_to_dark"))
        self.btn_theme_toggle.setStyleSheet(self._control_button_style)
        
        active_style = (
            "QPushButton { background-color: #2b5797; color: #ffffff; border: none; border-radius: 4px; padding: 6px 10px; font-weight: bold; }"
        )
        self.btn_center_align_toggle.setIcon(render_svg_icon("align_center", size=16, color="#ffffff" if self.center_align else icon_color))
        self.btn_center_align_toggle.setStyleSheet(active_style if self.center_align else self._control_button_style)
        
        self.btn_jump_first.setIcon(render_svg_icon("chevron_left", size=16, color=icon_color))
        self.btn_jump_first.setStyleSheet(self._control_button_style)
        self.btn_jump_last.setIcon(render_svg_icon("chevron_right", size=16, color=icon_color))
        self.btn_jump_last.setStyleSheet(self._control_button_style)
        self.btn_exit.setIcon(render_svg_icon("preview_fullscreen_exit", size=14, color=icon_color))
        self.btn_exit.setStyleSheet(self._control_button_style)
        
        self.lbl_pattern_indicator.setStyleSheet(
            f"background-color: {c['indicator_bg']}; color: {c['indicator_text']}; "
            f"padding: 6px 14px; border-radius: 6px; font-weight: bold;"
        )
        
        self._update_pattern_button_styles()

    def toggle_theme(self):
        """読書モードの背景テーマを切り替える。アプリ本体のテーマとは独立しており、設定として保存される。"""
        self.theme = "light" if self.theme == "dark" else "dark"
        database.set_setting("reading_mode_theme", self.theme)
        self.apply_theme()

    def toggle_center_align(self):
        """左右のページの揃え位置を切り替える。
        通常表示: それぞれのページを担当エリア内で中央揃え（左右均等に余白）。
        中央詰め表示: 左ページは右揃え、右ページは左揃えにすることで、あぶれた余白を画面の外側だけに
        追いやり、2枚のページが画面中央でぴったり合わさる、本を開いたような見た目にする。
        設定として保存され、次回もこのモードを開いた時に記憶される。"""
        self.center_align = not self.center_align
        database.set_setting("reading_mode_center_align", "1" if self.center_align else "0")
        if self.center_align:
            self.lbl_left.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lbl_right.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        else:
            self.lbl_left.setAlignment(Qt.AlignCenter)
            self.lbl_right.setAlignment(Qt.AlignCenter)
        self.apply_theme()

    def _update_pattern_button_styles(self):
        c = READING_MODE_THEMES[self.theme]
        active_style = (
            "QPushButton { background-color: #2b5797; color: #ffffff; border: none; border-radius: 4px; padding: 6px 10px; font-weight: bold; }"
        )
        icon_color = c['button_text']
        self.btn_pattern_a.setIcon(render_svg_icon("chevron_right", size=14, color="#ffffff" if self.pattern == "A" else icon_color))
        self.btn_pattern_b.setIcon(render_svg_icon("chevron_left", size=14, color="#ffffff" if self.pattern == "B" else icon_color))
        self.btn_pattern_a.setStyleSheet(active_style if self.pattern == "A" else self._control_button_style)
        self.btn_pattern_b.setStyleSheet(active_style if self.pattern == "B" else self._control_button_style)

    def update_pattern_indicator(self):
        text = self.tr("reading.indicator.pattern_a") if self.pattern == "A" else self.tr("reading.indicator.pattern_b")
        self.lbl_pattern_indicator.setText(text)
        self.lbl_pattern_indicator.adjustSize()
        self.reposition_pattern_indicator()

    def reposition_pattern_indicator(self):
        margin = SPACING_LG
        x = self.width() - self.lbl_pattern_indicator.width() - margin
        self.lbl_pattern_indicator.move(max(0, x), margin)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reposition_pattern_indicator()
        self.update_spread_display()

    def get_original_pixmap(self, index):
        if index not in self._pixmap_cache:
            _, file_path = self.image_rows[index]
            self._pixmap_cache[index] = QPixmap(file_path) if os.path.exists(file_path) else QPixmap()
        return self._pixmap_cache[index]

    def set_page_label(self, label, index):
        if index is None:
            label.clear()
            return
        pixmap = self.get_original_pixmap(index)
        if pixmap.isNull():
            label.setText(self.tr("reading.label.load_failed"))
            return
        target_size = label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return
        scaled = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled)

    def get_left_right_indices(self):
        """現在の見開き（spread_start, spread_start+1）を、パターンに応じて左右に振り分ける。
        パターンA（左開き）: 若い番号を左、次を右。パターンB（右開き）: 若い番号を右、次を左。"""
        first = self.spread_start
        second = self.spread_start + 1 if self.spread_start + 1 < len(self.image_rows) else None
        if self.pattern == "A":
            return first, second
        else:
            return second, first

    def update_spread_display(self):
        left_idx, right_idx = self.get_left_right_indices()
        self.set_page_label(self.lbl_left, left_idx)
        self.set_page_label(self.lbl_right, right_idx)
        self.slider.blockSignals(True)
        self.slider.setValue(self.spread_start // 2)
        self.slider.blockSignals(False)

    def set_pattern(self, pattern):
        """パターンを切り替える。表示中の2枚はそのまま、左右の位置だけ入れ替える
        （このセッション限りの一時的な変更。設定画面の既定値は変更しない）。"""
        if self.pattern == pattern:
            return
        self.pattern = pattern
        self._update_pattern_button_styles()
        self.update_pattern_indicator()
        self.update_spread_display()

    def advance_spread(self):
        next_start = self.spread_start + 2
        if next_start < len(self.image_rows):
            self.spread_start = next_start
            self.update_spread_display()

    def go_back_spread(self):
        if self.spread_start - 2 >= 0:
            self.spread_start -= 2
            self.update_spread_display()

    def jump_to_first(self):
        self.spread_start = 0
        self.update_spread_display()

    def jump_to_last(self):
        total = len(self.image_rows)
        if total == 0:
            return
        self.spread_start = total - 1 if total % 2 == 1 else max(0, total - 2)
        self.update_spread_display()

    def on_slider_changed(self, value):
        self.spread_start = value * 2
        self.update_spread_display()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        if event.key() == Qt.Key_Right:
            self.advance_spread() if self.pattern == "A" else self.go_back_spread()
        elif event.key() == Qt.Key_Left:
            self.go_back_spread() if self.pattern == "A" else self.advance_spread()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        edge_ratio = 0.15
        x = event.position().x() if hasattr(event, "position") else event.x()
        width = self.width()
        if x <= width * edge_ratio:
            self.go_back_spread() if self.pattern == "A" else self.advance_spread()
        elif x >= width * (1 - edge_ratio):
            self.advance_spread() if self.pattern == "A" else self.go_back_spread()
        else:
            super().mousePressEvent(event)


class FullscreenPreviewWindow(QWidget):
    """画像プレビューを全画面表示するための独立ウィンドウ。
    画面送り・再生速度・スライドショーのボタンは、メインウィンドウのものを
    そのまま一時的に取り込んで表示するため、ロジックの重複がない。"""
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.setWindowFlag(Qt.Window)
        self.setWindowTitle(self.tr("fullscreen.title"))

    def tr(self, key):
        if hasattr(self.main_app, "tr"):
            return self.main_app.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.main_app.refresh_preview_pixmap()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.main_app.exit_fullscreen_preview()
        elif event.key() == Qt.Key_Left:
            self.main_app.prev_image()
        elif event.key() == Qt.Key_Right:
            self.main_app.next_image()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        event.accept()
        self.main_app.exit_fullscreen_preview()


GITHUB_REPO_URL = "https://github.com/ocoe-puipui/seed-book"
MANUAL_URL_EN = "https://github.com/ocoe-puipui/seed-book/blob/main/manual.md"
MANUAL_URL_JA = "https://github.com/ocoe-puipui/seed-book/blob/main/manual.ja.md"


def get_manual_url(lang):
    """表示言語に応じて、案内するマニュアル（manual.md=英語／manual.ja.md=日本語）のURLを返す。"""
    return MANUAL_URL_JA if lang == "ja" else MANUAL_URL_EN

IMPORT_ORDER_OPTIONS = [
    ("filename_asc", "ファイル名順（記号 > 数字 > 英字 > かな > 漢字）"),
    ("filename_desc", "ファイル名逆順"),
    ("created_asc", "作成日時順（昇順・古い順）"),
    ("created_desc", "作成日時順（降順・新しい順）"),
    ("modified_asc", "更新日時順（昇順・古い順）"),
    ("modified_desc", "更新日時順（降順・新しい順）"),
]


class ImportOrderDialog(QDialog):
    """フォルダ取り込み時に、取り込む順序を確認するダイアログ。
    選ばれた順序のキー（IMPORT_ORDER_OPTIONSのキー）は selected_order に格納される。
    また、内容が同一の画像を取り込むかどうかは allow_duplicate_content に格納される。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_app_ref = parent
        if self._main_app_ref is not None and not hasattr(self._main_app_ref, "tr") and hasattr(self._main_app_ref, "main_app"):
            self._main_app_ref = self._main_app_ref.main_app
        self.setWindowTitle(self.tr("dialog.import_order.title"))
        self.setMinimumWidth(380)
        self.selected_order = "filename_asc"
        self.allow_duplicate_content = False

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)

        layout.addWidget(QLabel(self.tr("dialog.import_order.question")))

        order_labels = {
            "filename_asc": self.tr("dialog.import_order.filename_asc"),
            "filename_desc": self.tr("dialog.import_order.filename_desc"),
            "created_asc": self.tr("dialog.import_order.created_asc"),
            "created_desc": self.tr("dialog.import_order.created_desc"),
            "modified_asc": self.tr("dialog.import_order.modified_asc"),
            "modified_desc": self.tr("dialog.import_order.modified_desc"),
        }
        self.radio_group = QButtonGroup(self)
        self.radio_buttons = {}
        for key, _label in IMPORT_ORDER_OPTIONS:
            radio = QRadioButton(order_labels.get(key, _label))
            if key == "filename_asc":
                radio.setChecked(True)
            self.radio_group.addButton(radio)
            self.radio_buttons[key] = radio
            layout.addWidget(radio)

        layout.addSpacing(SPACING_SM)

        self.chk_allow_duplicates = QCheckBox(self.tr("dialog.import_order.allow_duplicates_checkbox"))
        self.chk_allow_duplicates.setToolTip(self.tr("dialog.import_order.allow_duplicates_tooltip"))
        self.chk_allow_duplicates.setChecked(database.get_setting("allow_duplicate_content", "0") == "1")
        layout.addWidget(self.chk_allow_duplicates)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton(self.tr("dialog.import_order.ok_button"))
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.tr("common.button.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        if parent is not None and hasattr(parent, "theme_colors") and hasattr(parent, "build_stylesheet"):
            self.setStyleSheet(parent.build_stylesheet(parent.theme_colors))

    def tr(self, key):
        if self._main_app_ref is not None and hasattr(self._main_app_ref, "tr"):
            return self._main_app_ref.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)

    def accept(self):
        for key, radio in self.radio_buttons.items():
            if radio.isChecked():
                self.selected_order = key
                break
        self.allow_duplicate_content = self.chk_allow_duplicates.isChecked()
        super().accept()


class CsvExportOptionsDialog(QDialog):
    """CSVエクスポート時に、含める項目の範囲を選ぶダイアログ。
    選択結果は include_meta（True/False）に格納される。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_app_ref = parent
        if self._main_app_ref is not None and not hasattr(self._main_app_ref, "tr") and hasattr(self._main_app_ref, "main_app"):
            self._main_app_ref = self._main_app_ref.main_app
        self.setWindowTitle(self.tr("dialog.csv_export_options.title"))
        self.setMinimumWidth(380)
        self.include_meta = False

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)

        layout.addWidget(QLabel(self.tr("dialog.csv_export_options.question")))

        self.radio_basic = QRadioButton(self.tr("dialog.csv_export_options.radio_basic"))
        self.radio_full = QRadioButton(self.tr("dialog.csv_export_options.radio_full"))
        self.radio_basic.setChecked(True)

        self.radio_group = QButtonGroup(self)
        self.radio_group.addButton(self.radio_basic)
        self.radio_group.addButton(self.radio_full)

        layout.addWidget(self.radio_basic)
        layout.addWidget(self.radio_full)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton(self.tr("dialog.csv_export_options.next_button"))
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.tr("common.button.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        if parent is not None and hasattr(parent, "theme_colors") and hasattr(parent, "build_stylesheet"):
            self.setStyleSheet(parent.build_stylesheet(parent.theme_colors))

    def tr(self, key):
        if self._main_app_ref is not None and hasattr(self._main_app_ref, "tr"):
            return self._main_app_ref.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)

    def accept(self):
        self.include_meta = self.radio_full.isChecked()
        super().accept()


class HelpDialog(QDialog):
    """ヘルプ表示ダイアログ。QMessageBoxではなく専用のQDialogにすることで、
    不要なアイコンを表示せず、GitHubの詳細マニュアルへのリンクも追加できるようにする。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_app_ref = parent
        if self._main_app_ref is not None and not hasattr(self._main_app_ref, "tr") and hasattr(self._main_app_ref, "main_app"):
            self._main_app_ref = self._main_app_ref.main_app
        self.setWindowTitle(self.tr("help.title"))
        self.setMinimumSize(560, 540)
        self.resize(840, 810)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)

        lbl_text = QLabel(self.tr("help.text"))
        lbl_text.setWordWrap(True)
        lbl_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl_text.setContentsMargins(SPACING_SM, SPACING_SM, SPACING_SM, SPACING_SM)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(lbl_text)
        layout.addWidget(scroll)

        _lang = getattr(self._main_app_ref, "current_lang", i18n.DEFAULT_LANGUAGE)
        lbl_manual_link = QLabel(self.tr("help.manual_link").format(MANUAL_URL=get_manual_url(_lang)))
        lbl_manual_link.setOpenExternalLinks(True)
        lbl_manual_link.setWordWrap(True)
        layout.addWidget(lbl_manual_link)

        btn_close = QPushButton(self.tr("common.button.close"))
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        if parent is not None and hasattr(parent, "theme_colors") and hasattr(parent, "build_stylesheet"):
            self.setStyleSheet(parent.build_stylesheet(parent.theme_colors))

    def tr(self, key):
        if self._main_app_ref is not None and hasattr(self._main_app_ref, "tr"):
            return self._main_app_ref.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)


class FolderNamingRuleDialog(QDialog):
    """フォルダ見出しの右クリックメニューから開く、フォルダ専用の自動採番の設定ダイアログ。
    設定画面の「自動採番・リネーム」と同じ項目（プレフィックス・桁数・アペンド）を、
    このフォルダだけ別の値で上書きできる。チェックボックスがオフの間はアプリ全体の既定ルールを使う。
    オンの場合、以後このフォルダへ新規に取り込む画像だけでなく、この画像リストからの
    「選択画像を一括リネーム」「一括で書き出す」でも、このフォルダの画像には常にこのルールが
    優先して適用される（2026-08-15〜）。"""
    def __init__(self, parent, folder_name, folder_dir):
        super().__init__(parent)
        self._main_app_ref = parent
        if self._main_app_ref is not None and not hasattr(self._main_app_ref, "tr") and hasattr(self._main_app_ref, "main_app"):
            self._main_app_ref = self._main_app_ref.main_app
        self.folder_dir = folder_dir
        self.setWindowTitle(self.tr("dialog.folder_naming_rule.title").format(folder_name=folder_name))
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)

        existing_rule = database.get_folder_naming_rule(folder_dir)

        lbl_hint = QLabel(self.tr("dialog.folder_naming_rule.hint").format(folder_name=folder_name))
        lbl_hint.setWordWrap(True)
        layout.addWidget(lbl_hint)

        grid = QGridLayout()
        grid.setHorizontalSpacing(SPACING_SM)
        grid.setVerticalSpacing(SPACING_SM)

        default_prefix = database.get_setting("sequence_prefix", "CG_")
        default_digits = int(database.get_setting("sequence_digits", "5"))
        default_append = database.get_setting("sequence_append", "")

        lbl_prefix = QLabel(self.tr("common.label.prefix"))
        lbl_prefix.setFixedWidth(90)
        self.txt_prefix = QLineEdit((existing_rule or {}).get("prefix", default_prefix))
        self.txt_prefix.setToolTip(self.tr("dialog.folder_naming_rule.placeholder_hint"))
        grid.addWidget(lbl_prefix, 0, 0)
        grid.addWidget(self.txt_prefix, 0, 1)

        lbl_digits = QLabel(self.tr("common.label.digits"))
        lbl_digits.setFixedWidth(90)
        self.spn_digits = QSpinBox()
        self.spn_digits.setRange(1, 6)
        self.spn_digits.setButtonSymbols(QSpinBox.NoButtons)
        self.spn_digits.setFixedWidth(45)
        self.spn_digits.setValue((existing_rule or {}).get("digits", default_digits))
        grid.addWidget(lbl_digits, 1, 0)
        grid.addWidget(self.spn_digits, 1, 1)

        lbl_append = QLabel(self.tr("common.label.append"))
        lbl_append.setFixedWidth(90)
        self.txt_append = QLineEdit((existing_rule or {}).get("append", default_append))
        self.txt_append.setPlaceholderText(self.tr("common.placeholder.optional_blank"))
        self.txt_append.setToolTip(self.tr("dialog.folder_naming_rule.placeholder_hint"))
        grid.addWidget(lbl_append, 2, 0)
        grid.addWidget(self.txt_append, 2, 1)

        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        self.lbl_preview = QLabel()
        self.lbl_preview.setWordWrap(True)
        layout.addWidget(self.lbl_preview)

        self.chk_override = QCheckBox(self.tr("dialog.folder_naming_rule.override_checkbox"))
        self.chk_override.setChecked(existing_rule is not None)
        self.chk_override.toggled.connect(self._update_enabled_state)
        self.txt_prefix.textChanged.connect(self._update_preview)
        self.spn_digits.valueChanged.connect(self._update_preview)
        self.txt_append.textChanged.connect(self._update_preview)
        self._update_enabled_state()
        self._update_preview()

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.chk_override)
        btn_row.addStretch()
        btn_cancel = QPushButton(self.tr("common.button.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton(self.tr("common.button.save"))
        btn_save.setObjectName("btn_save")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        if parent is not None and hasattr(parent, "theme_colors") and hasattr(parent, "build_stylesheet"):
            self.setStyleSheet(parent.build_stylesheet(parent.theme_colors))

    def tr(self, key):
        if self._main_app_ref is not None and hasattr(self._main_app_ref, "tr"):
            return self._main_app_ref.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)

    def _update_enabled_state(self):
        enabled = self.chk_override.isChecked()
        self.txt_prefix.setEnabled(enabled)
        self.spn_digits.setEnabled(enabled)
        self.txt_append.setEnabled(enabled)
        self._update_preview()

    def _update_preview(self):
        if not self.chk_override.isChecked():
            self.lbl_preview.setText(self.tr("dialog.folder_naming_rule.preview_using_global"))
            return
        sample_folder_name = os.path.basename(self.folder_dir) if self.folder_dir else self.tr("dialog.folder_naming_rule.sample_folder_name")
        prefix = database.resolve_naming_placeholders(self.txt_prefix.text(), sample_folder_name)
        append = database.resolve_naming_placeholders(self.txt_append.text(), sample_folder_name)
        digits = self.spn_digits.value()
        next_num = database.peek_next_sequence_number(prefix, append)
        examples = [f"{prefix}{n:0{digits}d}{append}" for n in range(next_num, next_num + 2)]
        self.lbl_preview.setText(self.tr("dialog.folder_naming_rule.preview_prefix") + " , ".join(examples))

    def _save(self):
        if self.chk_override.isChecked():
            prefix = self.txt_prefix.text().strip()
            if not prefix:
                show_notification(self, self.tr("common.title.warning"), self.tr("dialog.folder_naming_rule.prefix_empty_warning"))
                return
            database.set_folder_naming_rule(self.folder_dir, prefix, self.spn_digits.value(), self.txt_append.text())
        else:
            database.clear_folder_naming_rule(self.folder_dir)
        self.accept()


class FolderOrderDialog(QDialog):
    """フォルダ別グループ表示での、フォルダの並び順を編集するダイアログ。
    フォルダ名だけが並んだシンプルな一覧の中で、ドラッグ&ドロップにより並び替えられる
    （画像本体を含む複雑な一覧ではなく、専用の小さな一覧として独立させることで、
    実装・操作両面のリスクを抑えている）。"""
    def __init__(self, main_app, folder_names):
        super().__init__(main_app)
        self.main_app = main_app
        self.setWindowTitle(self.tr("dialog.folder_order.title"))
        self.setMinimumSize(420, 420)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)
        
        lbl_intro = QLabel(self.tr("dialog.folder_order.intro"))
        lbl_intro.setWordWrap(True)
        layout.addWidget(lbl_intro)

        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        ordered_names = main_app.get_ordered_folder_names(folder_names)
        for name in ordered_names:
            self.list_widget.addItem(QListWidgetItem(name))
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        btn_save = QPushButton(self.tr("dialog.folder_order.save_button"))
        btn_save.clicked.connect(self.save_order)
        btn_cancel = QPushButton(self.tr("common.button.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        if hasattr(main_app, "theme_colors") and hasattr(main_app, "build_stylesheet"):
            self.setStyleSheet(main_app.build_stylesheet(main_app.theme_colors))

    def tr(self, key):
        return self.main_app.tr(key)

    def save_order(self):
        order = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        database.set_folder_group_order(order)
        self.accept()


class SettingsDialog(QDialog):
    """歯車アイコンから開く設定ダイアログ。自動採番ルール・外観モード・ヘルプ・リリースノートをまとめる。"""

    def tr(self, key):
        return self.main_app.tr(key)

    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app
        self.setWindowTitle(self.tr("settings.title"))
        self.setMinimumWidth(480)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(SPACING_LG)
        
        info_layout = QHBoxLayout()
        self.btn_release_notes = QPushButton(self.tr("settings.button.release_notes"))
        self.btn_release_notes.setIcon(render_svg_icon("release_notes", size=16))
        self.btn_release_notes.setIconSize(QSize(16, 16))
        self.btn_release_notes.setToolTip(self.tr("settings.tooltip.release_notes"))
        self.btn_release_notes.clicked.connect(self.open_release_notes)
        self.btn_release_notes.setVisible(False)
        info_layout.addWidget(self.btn_release_notes)
        layout.addLayout(info_layout)
        
        theme_group = QGroupBox(self.tr("settings.theme.title"))
        theme_group_layout = QVBoxLayout(theme_group)
        theme_group_layout.setSpacing(SPACING_SM)

        theme_layout = QHBoxLayout()

        self.radio_theme_auto = QRadioButton(self.tr("settings.theme.auto"))
        self.radio_theme_dark = QRadioButton(self.tr("settings.theme.dark"))
        self.radio_theme_light = QRadioButton(self.tr("settings.theme.light"))
        
        self.theme_button_group = QButtonGroup(self)
        self.theme_button_group.addButton(self.radio_theme_auto)
        self.theme_button_group.addButton(self.radio_theme_dark)
        self.theme_button_group.addButton(self.radio_theme_light)
        
        current_theme_mode = database.get_setting("theme_mode", "auto")
        if current_theme_mode == "dark":
            self.radio_theme_dark.setChecked(True)
        elif current_theme_mode == "light":
            self.radio_theme_light.setChecked(True)
        else:
            self.radio_theme_auto.setChecked(True)
        
        self.radio_theme_auto.toggled.connect(lambda checked: checked and self.set_theme_mode("auto"))
        self.radio_theme_dark.toggled.connect(lambda checked: checked and self.set_theme_mode("dark"))
        self.radio_theme_light.toggled.connect(lambda checked: checked and self.set_theme_mode("light"))
        
        theme_layout.addWidget(self.radio_theme_auto)
        theme_layout.addWidget(self.radio_theme_dark)
        theme_layout.addWidget(self.radio_theme_light)
        theme_group_layout.addLayout(theme_layout)

        panel_layout_row = QHBoxLayout()

        self.radio_panel_standard = QRadioButton(self.tr("settings.panel.standard"))
        self.radio_panel_mirrored = QRadioButton(self.tr("settings.panel.mirrored"))

        self.panel_layout_button_group = QButtonGroup(self)
        self.panel_layout_button_group.addButton(self.radio_panel_standard)
        self.panel_layout_button_group.addButton(self.radio_panel_mirrored)

        current_panel_layout = database.get_setting("panel_layout", "standard")
        if current_panel_layout == "mirrored":
            self.radio_panel_mirrored.setChecked(True)
        else:
            self.radio_panel_standard.setChecked(True)

        self.radio_panel_standard.toggled.connect(lambda checked: checked and self.set_panel_layout_mode("standard"))
        self.radio_panel_mirrored.toggled.connect(lambda checked: checked and self.set_panel_layout_mode("mirrored"))

        panel_layout_row.addWidget(self.radio_panel_standard)
        panel_layout_row.addWidget(self.radio_panel_mirrored)
        theme_group_layout.addLayout(panel_layout_row)

        layout.addWidget(theme_group)

        current_lang_setting = database.get_setting("language", "auto")
        lang_group = QGroupBox(self.tr("language.group_title"))
        lang_group_layout = QVBoxLayout(lang_group)
        lang_group_layout.setSpacing(SPACING_SM)

        lang_layout = QHBoxLayout()
        resolved_lang = i18n.resolve_language(current_lang_setting)
        self.radio_lang_auto = QRadioButton(self.tr("language.auto"))
        self.radio_lang_ja = QRadioButton(self.tr("language.ja"))
        self.radio_lang_en = QRadioButton(self.tr("language.en"))

        self.lang_button_group = QButtonGroup(self)
        self.lang_button_group.addButton(self.radio_lang_auto)
        self.lang_button_group.addButton(self.radio_lang_ja)
        self.lang_button_group.addButton(self.radio_lang_en)

        if current_lang_setting == "ja":
            self.radio_lang_ja.setChecked(True)
        elif current_lang_setting == "en":
            self.radio_lang_en.setChecked(True)
        else:
            self.radio_lang_auto.setChecked(True)

        self.radio_lang_auto.toggled.connect(lambda checked: checked and self.set_language_mode("auto"))
        self.radio_lang_ja.toggled.connect(lambda checked: checked and self.set_language_mode("ja"))
        self.radio_lang_en.toggled.connect(lambda checked: checked and self.set_language_mode("en"))

        lang_layout.addWidget(self.radio_lang_auto)
        lang_layout.addWidget(self.radio_lang_ja)
        lang_layout.addWidget(self.radio_lang_en)
        lang_group_layout.addLayout(lang_layout)

        lang_notice = QLabel(self.tr("language.restart_notice"))
        lang_notice.setWordWrap(True)
        lang_group_layout.addWidget(lang_notice)

        layout.addWidget(lang_group)

        import_order_group = QGroupBox(self.tr("settings.import_order.title"))
        import_order_layout = QHBoxLayout(import_order_group)
        
        self.radio_import_order_confirm = QRadioButton(self.tr("settings.import_order.always_confirm"))
        self.radio_import_order_auto = QRadioButton(self.tr("settings.import_order.auto_last_used"))
        
        self.import_order_button_group = QButtonGroup(self)
        self.import_order_button_group.addButton(self.radio_import_order_confirm)
        self.import_order_button_group.addButton(self.radio_import_order_auto)
        
        current_import_order_mode = database.get_setting("import_order_mode", "confirm")
        if current_import_order_mode == "auto":
            self.radio_import_order_auto.setChecked(True)
        else:
            self.radio_import_order_confirm.setChecked(True)
        
        self.radio_import_order_confirm.toggled.connect(lambda checked: checked and database.set_setting("import_order_mode", "confirm"))
        self.radio_import_order_auto.toggled.connect(lambda checked: checked and database.set_setting("import_order_mode", "auto"))
        
        import_order_layout.addWidget(self.radio_import_order_confirm)
        import_order_layout.addWidget(self.radio_import_order_auto)
        layout.addWidget(import_order_group)
        
        seq_group = QGroupBox(self.tr("settings.naming.title"))
        seq_layout = QVBoxLayout(seq_group)

        seq_checkbox_row = QHBoxLayout()

        self.chk_sequential_naming = QCheckBox(self.tr("settings.naming.auto_number_checkbox"))
        self.chk_sequential_naming.setToolTip(self.tr("settings.naming.auto_number_checkbox_tooltip"))
        self.chk_sequential_naming.setChecked(database.get_setting("use_sequential_naming", "1") == "1")
        self.chk_sequential_naming.toggled.connect(
            lambda checked: database.set_setting("use_sequential_naming", "1" if checked else "0")
        )
        seq_checkbox_row.addWidget(self.chk_sequential_naming)

        self.chk_rename_show_edit_dialog = QCheckBox(self.tr("settings.naming.show_edit_dialog_checkbox"))
        self.chk_rename_show_edit_dialog.setToolTip(self.tr("settings.naming.show_edit_dialog_checkbox_tooltip"))
        self.chk_rename_show_edit_dialog.setChecked(database.get_setting("rename_show_edit_dialog", "0") == "1")
        self.chk_rename_show_edit_dialog.toggled.connect(
            lambda checked: database.set_setting("rename_show_edit_dialog", "1" if checked else "0")
        )
        seq_checkbox_row.addWidget(self.chk_rename_show_edit_dialog)
        seq_checkbox_row.addStretch()
        seq_layout.addLayout(seq_checkbox_row)

        seq_grid = QGridLayout()
        seq_grid.setHorizontalSpacing(SPACING_SM)
        seq_grid.setVerticalSpacing(SPACING_SM)

        lbl_prefix = QLabel(self.tr("common.label.prefix"))
        lbl_prefix.setFixedWidth(90)
        self.txt_prefix = QLineEdit(database.get_setting("sequence_prefix", "CG_"))
        self.txt_prefix.setFixedWidth(120)
        self.txt_prefix.setToolTip(self.tr("settings.naming.prefix_tooltip"))
        self.txt_prefix.installEventFilter(self)
        seq_grid.addWidget(lbl_prefix, 0, 0)
        seq_grid.addWidget(self.txt_prefix, 0, 1)

        digits_spacer = QWidget()
        digits_spacer.setFixedWidth(0)
        seq_grid.addWidget(digits_spacer, 0, 2)

        lbl_digits = QLabel(self.tr("common.label.digits"))
        seq_grid.addWidget(lbl_digits, 0, 3)
        self.spn_digits = QSpinBox()
        self.spn_digits.setRange(1, 6)
        self.spn_digits.setValue(int(database.get_setting("sequence_digits", "5")))
        self.spn_digits.setButtonSymbols(QSpinBox.NoButtons)
        self.spn_digits.setFixedWidth(45)
        seq_grid.addWidget(self.spn_digits, 0, 4)

        lbl_digits_range = QLabel(self.tr("settings.naming.digits_range"))
        lbl_digits_range.setObjectName("lbl_import_format_note")
        seq_grid.addWidget(lbl_digits_range, 0, 5)

        seq_grid.setColumnStretch(6, 1)
        seq_layout.addLayout(seq_grid)

        append_row = QHBoxLayout()
        append_row.setSpacing(SPACING_SM)

        lbl_append = QLabel(self.tr("common.label.append"))
        lbl_append.setFixedWidth(90)
        self.txt_append = QLineEdit(database.get_setting("sequence_append", ""))
        self.txt_append.setFixedWidth(120)
        self.txt_append.setPlaceholderText(self.tr("common.placeholder.optional_blank"))
        self.txt_append.setToolTip(self.tr("settings.naming.prefix_tooltip"))
        self.txt_append.installEventFilter(self)
        append_row.addWidget(lbl_append, 0, Qt.AlignVCenter)
        append_row.addWidget(self.txt_append, 0, Qt.AlignVCenter)

        self._last_focused_naming_field = self.txt_append

        if self.main_app.current_lang == "en":
            _placeholder_link_text = 'Placeholders: <a href="date">{date}</a>　<a href="folder">{folder name}</a>'
        else:
            _placeholder_link_text = 'プレースホルダー: <a href="date">{日付}</a>　<a href="folder">{フォルダ名}</a>'
        lbl_placeholder_links = QLabel(_placeholder_link_text)
        lbl_placeholder_links.setTextFormat(Qt.RichText)
        lbl_placeholder_links.linkActivated.connect(self.insert_naming_placeholder)
        append_row.addWidget(lbl_placeholder_links, 0, Qt.AlignVCenter)
        append_row.addStretch()
        seq_layout.addLayout(append_row)
        
        self.lbl_seq_preview = QLabel()
        self.lbl_seq_preview.setWordWrap(True)
        seq_layout.addWidget(self.lbl_seq_preview)
        self.txt_prefix.textChanged.connect(self.update_sequence_preview)
        self.spn_digits.valueChanged.connect(self.update_sequence_preview)
        self.txt_append.textChanged.connect(self.update_sequence_preview)
        self.update_sequence_preview()
        
        seq_button_row = QHBoxLayout()
        self.btn_save_sequence = QPushButton(self.tr("settings.naming.save_button"))
        self.btn_save_sequence.setToolTip(self.tr("settings.naming.save_tooltip"))
        self.btn_save_sequence.clicked.connect(self.save_sequence_settings)
        seq_button_row.addWidget(self.btn_save_sequence)
        
        self.btn_reset_sequence_counter = QPushButton(self.tr("settings.naming.reset_counter_button"))
        self.btn_reset_sequence_counter.setObjectName("btn_delete")
        self.btn_reset_sequence_counter.setToolTip(self.tr("settings.naming.reset_counter_tooltip"))
        self.btn_reset_sequence_counter.clicked.connect(self.reset_sequence_counter)
        seq_button_row.addWidget(self.btn_reset_sequence_counter)
        seq_layout.addLayout(seq_button_row)
        
        layout.addWidget(seq_group)
        
        display_group = QGroupBox(self.tr("settings.display_fields.title"))
        display_layout = QGridLayout(display_group)
        
        self.display_item_checkboxes = {}
        display_items = [
            ("Steps", "show_param_steps"),
            ("Sampler", "show_param_sampler"),
            ("Scheduler", "show_param_scheduler"),
            ("CFG scale", "show_param_cfg_scale"),
            ("Seed", "show_param_seed"),
            ("Size", "show_param_size"),
        ]
        items_per_row = 3
        for index, (label, setting_key) in enumerate(display_items):
            checkbox = QCheckBox(label)
            checkbox.setChecked(database.get_setting(setting_key, "0") == "1")
            checkbox.toggled.connect(lambda checked, key=setting_key: self.toggle_display_item(key, checked))
            display_layout.addWidget(checkbox, index // items_per_row, index % items_per_row)
            self.display_item_checkboxes[setting_key] = checkbox
        
        layout.addWidget(display_group)
        
        reading_mode_group = QGroupBox(self.tr("settings.reading_defaults.title"))
        reading_mode_layout = QVBoxLayout(reading_mode_group)
        
        reading_mode_direction_row = QHBoxLayout()
        self.radio_reading_pattern_a = QRadioButton(self.tr("settings.reading_defaults.pattern_a"))
        self.radio_reading_pattern_b = QRadioButton(self.tr("settings.reading_defaults.pattern_b"))
        
        self.reading_pattern_button_group = QButtonGroup(self)
        self.reading_pattern_button_group.addButton(self.radio_reading_pattern_a)
        self.reading_pattern_button_group.addButton(self.radio_reading_pattern_b)
        
        current_reading_pattern = database.get_setting("reading_mode_default_pattern", "A")
        if current_reading_pattern == "B":
            self.radio_reading_pattern_b.setChecked(True)
        else:
            self.radio_reading_pattern_a.setChecked(True)
        
        self.radio_reading_pattern_a.toggled.connect(lambda checked: checked and database.set_setting("reading_mode_default_pattern", "A"))
        self.radio_reading_pattern_b.toggled.connect(lambda checked: checked and database.set_setting("reading_mode_default_pattern", "B"))
        
        reading_mode_direction_row.addWidget(self.radio_reading_pattern_a)
        reading_mode_direction_row.addWidget(self.radio_reading_pattern_b)
        reading_mode_layout.addLayout(reading_mode_direction_row)
        
        self.chk_reading_center_align = QCheckBox(self.tr("settings.reading_defaults.center_align_checkbox"))
        self.chk_reading_center_align.setChecked(database.get_setting("reading_mode_center_align", "0") == "1")
        self.chk_reading_center_align.toggled.connect(
            lambda checked: database.set_setting("reading_mode_center_align", "1" if checked else "0")
        )
        reading_mode_layout.addWidget(self.chk_reading_center_align)
        
        layout.addWidget(reading_mode_group)
        
        self.btn_reset_settings = QPushButton(self.tr("settings.reset.button"))
        self.btn_reset_settings.setIcon(render_svg_icon("reset_settings", size=16, color="#ed2c3a"))
        self.btn_reset_settings.setIconSize(QSize(16, 16))
        self.btn_reset_settings.setObjectName("btn_delete")
        self.btn_reset_settings.setToolTip(self.tr("settings.reset.tooltip"))
        self.btn_reset_settings.clicked.connect(self.reset_settings)
        reset_settings_row = QHBoxLayout()
        reset_settings_row.setContentsMargins(SPACING_SM, 0, SPACING_SM, 0)
        reset_settings_row.addWidget(self.btn_reset_settings)
        layout.addLayout(reset_settings_row)
        
        db_group = QGroupBox(self.tr("settings.database.title"))
        db_layout = QVBoxLayout(db_group)
        
        db_current_row = QHBoxLayout()
        db_current_row.addWidget(QLabel(self.tr("settings.database.current_label").format(db_name=database.DB_NAME)))
        db_current_row.addStretch(1)
        self.btn_open_db_folder = QPushButton()
        self.btn_open_db_folder.setIcon(render_svg_icon("all_folder_open", size=16))
        self.btn_open_db_folder.setIconSize(QSize(16, 16))
        self.btn_open_db_folder.setFixedSize(28, 28)
        self.btn_open_db_folder.setToolTip(self.tr("settings.database.open_folder_tooltip"))
        self.btn_open_db_folder.clicked.connect(
            lambda: self.main_app.reveal_in_file_manager([database.get_current_db_path()])
        )
        db_current_row.addWidget(self.btn_open_db_folder)
        db_layout.addLayout(db_current_row)

        switch_row = QHBoxLayout()
        self.cmb_db_slots = CenteredComboBox()
        self.cmb_db_slots.setFixedHeight(32)
        self.cmb_db_slots.addItems(database.list_available_databases())
        current_index = self.cmb_db_slots.findText(database.DB_NAME)
        if current_index >= 0:
            self.cmb_db_slots.setCurrentIndex(current_index)
        switch_row.addWidget(self.cmb_db_slots, 1)

        self.btn_create_db = QPushButton(self.tr("settings.database.create_button"))
        self.btn_create_db.setFixedHeight(32)
        self.btn_create_db.setToolTip(self.tr("settings.database.create_tooltip"))
        self.btn_create_db.clicked.connect(self.create_database)
        switch_row.addWidget(self.btn_create_db, 1)

        self.btn_switch_db = QPushButton(self.tr("settings.database.switch_button"))
        self.btn_switch_db.setFixedHeight(32)
        self.btn_switch_db.setToolTip(self.tr("settings.database.switch_tooltip"))
        self.btn_switch_db.clicked.connect(self.switch_database)
        switch_row.addWidget(self.btn_switch_db, 1)
        db_layout.addLayout(switch_row)

        export_row = QHBoxLayout()
        self.btn_export_csv = QPushButton(self.tr("settings.database.export_images_csv_button"))
        self.btn_export_csv.setObjectName("btn_export")
        self.btn_export_csv.setToolTip(self.tr("settings.database.export_images_csv_tooltip"))
        self.btn_export_csv.clicked.connect(self.export_csv)
        export_row.addWidget(self.btn_export_csv, 1)

        self.btn_export_sync_history = QPushButton(self.tr("settings.database.export_sync_history_button"))
        self.btn_export_sync_history.setObjectName("btn_export")
        self.btn_export_sync_history.setToolTip(self.tr("settings.database.export_sync_history_tooltip"))
        self.btn_export_sync_history.clicked.connect(self.export_sync_history_csv)
        export_row.addWidget(self.btn_export_sync_history, 1)
        db_layout.addLayout(export_row)

        self.btn_reset_database = QPushButton(self.tr("settings.database.reset_button"))
        self.btn_reset_database.setIcon(render_svg_icon("reset_database", size=16, color="#ed2c3a"))
        self.btn_reset_database.setIconSize(QSize(16, 16))
        self.btn_reset_database.setObjectName("btn_delete")
        self.btn_reset_database.setToolTip(self.tr("settings.database.reset_tooltip"))
        self.btn_reset_database.clicked.connect(self.reset_database)
        db_layout.addWidget(self.btn_reset_database)
        
        layout.addWidget(db_group)
        
        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)
        
        screen = self.screen() or QGuiApplication.primaryScreen()
        default_h = self.main_app.height() if self.main_app.height() > 0 else 600
        if screen is not None:
            default_h = min(default_h, int(screen.availableGeometry().height() * 0.9))
        self.resize(max(self.sizeHint().width(), 480), default_h)
        
        self.setStyleSheet(self.main_app.build_stylesheet(self.main_app.theme_colors))

    def eventFilter(self, obj, event):
        """プレフィックス／アペンド欄のフォーカス状態を記録する（insert_naming_placeholder用）。
        プレースホルダーのリンクをクリックした時点では、既にリンク側へフォーカスが移って
        しまっているため、直近にどちらへフォーカスしていたかをここで覚えておく必要がある。"""
        if event.type() == QEvent.FocusIn and obj in (self.txt_prefix, self.txt_append):
            self._last_focused_naming_field = obj
        return super().eventFilter(obj, event)

    def insert_naming_placeholder(self, href):
        """プレースホルダーのリンクがクリックされた際、直前にフォーカスしていた
        プレフィックス／アペンド欄のカーソル位置にプレースホルダー文字列を挿入する。
        どちらもフォーカスしていなかった場合は、既定でアペンド欄に挿入する。
        区切りが分かりやすいよう、「_」を付加して挿入する。挿入先によって位置を変える：
        プレフィックス欄は数字の前に来るため後ろに「_」（例: {フォルダ名}_）、
        アペンド欄は数字の後に来るため前に「_」（例: _{日付}）を付ける。"""
        target = self._last_focused_naming_field if self._last_focused_naming_field in (self.txt_prefix, self.txt_append) else self.txt_append
        placeholder = ("{date}" if href == "date" else "{folder name}") if self.main_app.current_lang == "en" else ("{日付}" if href == "date" else "{フォルダ名}")
        token = f"{placeholder}_" if target is self.txt_prefix else f"_{placeholder}"
        target.insert(token)
        target.setFocus()

    def update_sequence_preview(self):
        sample_folder_name = "サンプルフォルダ"
        prefix = database.resolve_naming_placeholders(self.txt_prefix.text(), sample_folder_name)
        digits = self.spn_digits.value()
        append = database.resolve_naming_placeholders(self.txt_append.text(), sample_folder_name)
        next_num = database.peek_next_sequence_number(prefix, append)
        examples = [f"{prefix}{n:0{digits}d}{append}" for n in range(next_num, next_num + 2)]
        self.lbl_seq_preview.setText(self.tr("settings.naming.preview_prefix") + " , ".join(examples))

    def save_sequence_settings(self):
        prefix = self.txt_prefix.text().strip()
        if not prefix:
            show_notification(self, self.tr("common.title.warning"), self.tr("settings.naming.prefix_empty_warning"))
            return
        reply = show_confirm_dialog(
            self,
            self.tr("common.title.confirm"),
            self.tr("settings.naming.save_confirm.body"),
        )
        if reply != QMessageBox.Yes:
            return
        database.set_setting("sequence_prefix", prefix)
        database.set_setting("sequence_digits", self.spn_digits.value())
        database.set_setting("sequence_append", self.txt_append.text())
        self.update_sequence_preview()
        show_notification(self, self.tr("common.title.saved"), self.tr("settings.naming.save_done_body"))

    def reset_sequence_counter(self):
        """現在のプレフィックス＋アペンドの組み合わせの採番カウンタを1に戻す。
        過去に同じ名前の画像が存在していても考慮しないことを、実行前に明示する。"""
        prefix = database.get_setting("sequence_prefix", "CG_")
        append = database.get_setting("sequence_append", "")
        
        reply = show_confirm_dialog(
            self, self.tr("settings.naming.reset_counter_button"),
            self.tr("settings.naming.reset_counter_confirm.body").format(prefix=prefix, append=append)
        )
        if reply != QMessageBox.Yes:
            return
        
        database.reset_sequence_counter()
        self.update_sequence_preview()
        show_notification(self, self.tr("common.title.reset_done"), self.tr("settings.naming.reset_counter_done_body"))

    def reset_database(self):
        """画像ライブラリのデータをリセットする。実行前に、削除される内容を明示して確認を取る。
        既にデータが空の場合は、その旨を伝えて処理を行わない。"""
        stats = database.get_database_stats()
        
        if stats["images"] == 0 and stats["folders"] == 0 and stats["excluded"] == 0:
            show_notification(
                self, self.tr("settings.database.already_reset.title"),
                self.tr("settings.database.already_reset.body")
            )
            return

        reply = show_confirm_dialog(
            self, self.tr("settings.database.reset_confirm.title"),
            self.tr("settings.database.reset_confirm.body").format(images=stats['images'], folders=stats['folders']),
            min_width=560
        )
        if reply != QMessageBox.Yes:
            return
        
        database.reset_database()
        self.main_app.load_images_from_db()
        self.main_app.txt_search.clear()
        show_notification(self, self.tr("common.title.reset_done"), self.tr("settings.database.reset_done_body"))

    def switch_database(self):
        """選択したデータベースに切り替える（ポインタファイルを更新し、アプリを再起動する）。"""
        selected = self.cmb_db_slots.currentText()
        if not selected:
            return
        if selected == database.DB_NAME:
            show_notification(self, self.tr("common.title.confirm"), self.tr("settings.database.already_in_use_body"))
            return
        reply = show_confirm_dialog(
            self, self.tr("settings.database.switch_confirm.title"),
            self.tr("settings.database.switch_confirm.body").format(db_name=selected)
        )
        if reply != QMessageBox.Yes:
            return
        database.set_current_db_name(selected)
        self.main_app.restart_app()

    def create_database(self):
        """新しい空のデータベースを、データベースの保存フォルダ内に作成する。
        作成前に確認を挟み、「いいえ」の場合はファイル自体を作らない。
        作成後は自動で切り替えたりせず、一覧から選んで「切り替える」ボタンを押す必要がある旨を案内する。"""
        next_name = database.get_next_available_db_filename()
        reply = show_confirm_dialog(
            self, self.tr("settings.database.create_confirm.title"),
            self.tr("settings.database.create_confirm.body").format(db_name=next_name)
        )
        if reply != QMessageBox.Yes:
            return

        new_name = database.create_new_database_slot()
        self.cmb_db_slots.clear()
        self.cmb_db_slots.addItems(database.list_available_databases())
        self.cmb_db_slots.setCurrentIndex(self.cmb_db_slots.findText(new_name))
        show_notification(
            self, self.tr("settings.database.create_done.title"),
            self.tr("settings.database.create_done.body").format(db_name=new_name)
        )

    def export_csv(self):
        """データベースに登録されている画像の一覧をCSVファイルに書き出す。
        エクスポートする項目の範囲は、ダイアログで基本情報のみ/メタ情報込みを選べる。
        文字コードはUTF-8 with BOMとし、WindowsのExcelで開いても文字化けしないようにする。"""
        options_dialog = CsvExportOptionsDialog(self)
        if options_dialog.exec() != QDialog.Accepted:
            return
        include_meta = options_dialog.include_meta
        
        default_path = os.path.join(get_default_export_dir(), "images.csv")
        save_path, _ = QFileDialog.getSaveFileName(self, self.tr("dialog.csv_save_title"), default_path, self.tr("dialog.csv_filter"))
        if not save_path:
            return
        
        try:
            conn = sqlite3.connect(database.get_current_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_name, file_path, rating, file_mtime, updated_at, imported_at, is_locked,
                       prompt, negative_prompt, other_metadata
                FROM images ORDER BY file_name COLLATE NOCASE ASC
            """)
            rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.db_load_failed").format(error=e))
            return
        
        try:
            with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                base_headers = [self.tr("csv.header.name"), self.tr("csv.header.filename"), self.tr("csv.header.location"),
                                self.tr("csv.header.rating"), self.tr("csv.header.created_at"), self.tr("csv.header.updated_at"),
                                self.tr("csv.header.imported_at"), self.tr("csv.header.locked")]
                if include_meta:
                    writer.writerow(base_headers + [self.tr("csv.header.prompt"), self.tr("csv.header.negative_prompt"),
                                                      self.tr("csv.header.model"), self.tr("csv.header.other_params")])
                else:
                    writer.writerow(base_headers)
                
                for row in rows:
                    file_name, file_path, rating, file_mtime, updated_at, imported_at, is_locked, prompt, neg_prompt, others = row
                    folder = os.path.dirname(file_path)
                    actual_filename = os.path.basename(file_path)
                    lock_text = self.tr("csv.value.locked") if is_locked else ""
                    
                    if include_meta:
                        model_name = self.main_app.extract_model_name(others) if others else ""
                        writer.writerow([file_name, actual_filename, folder, rating, file_mtime, updated_at, imported_at, lock_text,
                                          prompt or "", neg_prompt or "", model_name, others or ""])
                    else:
                        writer.writerow([file_name, actual_filename, folder, rating, file_mtime, updated_at, imported_at, lock_text])
        except Exception as e:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.csv_write_failed").format(error=e))
            return
        
        show_notification(self, self.tr("common.title.export_complete"), self.tr("notify.export_images_done").format(count=len(rows), save_path=save_path))

    def export_sync_history_csv(self):
        """同期履歴（見つからなかったフォルダ・画像、取り込みエラー）をCSVファイルに書き出す。
        同期結果のポップアップにある「履歴」ダイアログからも同じ内容をエクスポートできる。"""
        rows = database.get_sync_history()
        if not rows:
            show_notification(self, self.tr("settings.database.no_sync_history.title"), self.tr("settings.database.no_sync_history.body"))
            return

        default_path = os.path.join(get_default_export_dir(), "sync_history.csv")
        save_path, _ = QFileDialog.getSaveFileName(self, self.tr("dialog.csv_save_title"), default_path, self.tr("dialog.csv_filter"))
        if not save_path:
            return

        try:
            write_sync_history_csv(save_path, rows)
        except Exception as e:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.csv_write_failed").format(error=e))
            return

        show_notification(self, self.tr("common.title.export_complete"), self.tr("notify.sync_history_export_done").format(count=len(rows), save_path=save_path))

    def toggle_display_item(self, setting_key, checked):
        """生成パラメータの個別表示項目のオン/オフを即座に保存し、現在選択中の画像の表示に反映する"""
        database.set_setting(setting_key, "1" if checked else "0")
        if self.main_app.current_image_id is not None:
            self.main_app.on_image_selected()

    def reset_settings(self):
        """命名ルール・表示項目・テーマなど、このアプリの設定をすべて既定値に戻す。
        画像ライブラリのデータ（画像・フォルダ等）や、自動採番のカウンタ自体には影響しない。"""
        reply = show_confirm_dialog(
            self, self.tr("settings.reset.confirm.title"),
            self.tr("settings.reset.confirm.body"),
            min_width=560
        )
        if reply != QMessageBox.Yes:
            return
        
        database.reset_settings_to_defaults()
        self.main_app.apply_theme()
        show_notification(self, self.tr("common.title.reset_done"), self.tr("settings.reset.done_body"))
        self.accept()
        if self.main_app.current_image_id is not None:
            self.main_app.on_image_selected()

    def set_theme_mode(self, mode):
        database.set_setting("theme_mode", mode)
        self.main_app.apply_theme()
        self.setStyleSheet(self.main_app.build_stylesheet(self.main_app.theme_colors))

    def set_panel_layout_mode(self, mode):
        database.set_setting("panel_layout", mode)
        self.main_app.apply_panel_layout(mode)

    def set_language_mode(self, mode):
        """表示言語設定を保存する。
        Step1時点ではUI文言の動的切り替えは未実装のため、変更は次回起動時から反映される
        （設定ダイアログ内の案内ラベルでもその旨を表示している）。"""
        database.set_setting("language", mode)

    def open_release_notes(self):
        QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL))


class DatabaseMissingDialog(QDialog):
    """既定の保存先に、現在使用するはずのデータベースファイルが存在しない場合に表示するダイアログ。
    初回起動時、または利用者がファイルを直接削除した場合に表示される
    （アプリ内の「選択中のデータベースをリセット」はテーブルの中身を空にするだけでファイルは
    残るため、ここには来ない）。
    「新規作成」を勝手に行わず、必ず利用者に選ばせることが目的。閉じるボタン（×）で閉じた場合は
    安全側として「新規作成」扱いにする。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_app_ref = parent
        if self._main_app_ref is not None and not hasattr(self._main_app_ref, "tr") and hasattr(self._main_app_ref, "main_app"):
            self._main_app_ref = self._main_app_ref.main_app
        self.setWindowTitle(self.tr("dialog.db_missing.title"))
        self.setModal(True)
        self.result_mode = "new"  # "new" / "existing" / "external"
        self.selected_existing = None
        self.external_path = None
        self.use_sample_data = False

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)

        lbl_info = QLabel(self.tr("dialog.db_missing.info"))
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        self.radio_new = QRadioButton(self.tr("dialog.db_missing.create_new_radio"))
        self.radio_new.setChecked(True)
        layout.addWidget(self.radio_new)

        sample_row = QHBoxLayout()
        sample_row.addSpacing(24)
        self.chk_sample_data = QCheckBox(self.tr("dialog.db_missing.sample_data_checkbox"))
        self._sample_data_available = os.path.isdir(get_sample_data_dir())
        self.chk_sample_data.setEnabled(self._sample_data_available)
        sample_row.addWidget(self.chk_sample_data, 1)
        layout.addLayout(sample_row)

        other_dbs = database.list_available_databases()
        self.radio_existing = QRadioButton(self.tr("dialog.db_missing.choose_existing_radio"))
        self.radio_existing.setEnabled(bool(other_dbs))
        layout.addWidget(self.radio_existing)

        existing_row = QHBoxLayout()
        existing_row.addSpacing(24)
        self.cmb_existing = CenteredComboBox()
        self.cmb_existing.addItems(other_dbs)
        self.cmb_existing.setEnabled(False)
        existing_row.addWidget(self.cmb_existing, 1)
        layout.addLayout(existing_row)

        self.radio_external = QRadioButton(self.tr("dialog.db_missing.choose_external_radio"))
        layout.addWidget(self.radio_external)

        external_row = QHBoxLayout()
        external_row.addSpacing(24)
        self.lbl_external_path = QLabel(self.tr("dialog.db_missing.no_selection"))
        self.lbl_external_path.setWordWrap(True)
        btn_browse = QPushButton(self.tr("common.button.choose_file"))
        btn_browse.setEnabled(False)
        btn_browse.clicked.connect(self.browse_external_file)
        self.btn_browse = btn_browse
        external_row.addWidget(self.lbl_external_path, 1)
        external_row.addWidget(btn_browse)
        layout.addLayout(external_row)

        def _update_enabled():
            self.cmb_existing.setEnabled(self.radio_existing.isChecked())
            self.btn_browse.setEnabled(self.radio_external.isChecked())
            self.chk_sample_data.setEnabled(self.radio_new.isChecked() and self._sample_data_available)

        self.radio_new.toggled.connect(_update_enabled)
        self.radio_existing.toggled.connect(_update_enabled)
        self.radio_external.toggled.connect(_update_enabled)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.on_ok)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

        self.resize(max(self.sizeHint().width(), 460), self.sizeHint().height())

    def tr(self, key):
        if self._main_app_ref is not None and hasattr(self._main_app_ref, "tr"):
            return self._main_app_ref.tr(key)
        return i18n.tr(key, i18n.DEFAULT_LANGUAGE)

    def browse_external_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("dialog.db_missing.browse_file_title"), get_default_export_dir(), self.tr("dialog.db_missing.browse_file_filter")
        )
        if path:
            self.external_path = path
            self.lbl_external_path.setText(path)

    def on_ok(self):
        if self.radio_existing.isChecked():
            selected = self.cmb_existing.currentText()
            if not selected:
                show_notification(self, self.tr("common.title.please_select"), self.tr("dialog.db_missing.select_existing_warning"))
                return
            self.result_mode = "existing"
            self.selected_existing = selected
        elif self.radio_external.isChecked():
            if not self.external_path:
                show_notification(self, self.tr("common.title.please_select"), self.tr("dialog.db_missing.select_file_warning"))
                return
            self.result_mode = "external"
        else:
            self.result_mode = "new"
            self.use_sample_data = self.chk_sample_data.isChecked()
        self.accept()

    def closeEvent(self, event):
        self.result_mode = "new"
        super().closeEvent(event)


class AIImageViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seed Book")
        self.setGeometry(100, 100, 1200, 850)

        self.current_lang = i18n.detect_os_language()

        database.resolve_current_db_name()
        self._resolve_missing_database()
        database.init_db()
        if getattr(self, "_pending_sample_import", False):
            self._import_sample_data()

        self.current_lang = i18n.resolve_language(database.get_setting("language", "auto"))

        self.statusBar().setContentsMargins(SPACING_LG, 0, SPACING_LG, 6)
        self.status_message_label = QLabel("")
        self.status_message_label.setAlignment(Qt.AlignCenter)
        self.statusBar().addWidget(self.status_message_label, 1)
        self._status_message_timer = QTimer(self)
        self._status_message_timer.setSingleShot(True)
        self._status_message_timer.timeout.connect(lambda: self.status_message_label.setText(""))

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        self.main_layout.setSpacing(SPACING_SM)

        self.btn_toggle_all_fields = QPushButton()
        self.btn_toggle_all_fields.setIcon(render_svg_icon("hide_form", size=18))
        self.btn_toggle_all_fields.setIconSize(QSize(18, 18))
        self.btn_toggle_all_fields.setObjectName("btn_settings")
        self.btn_toggle_all_fields.setFixedSize(32, 32)
        self.btn_toggle_all_fields.setToolTip(self.tr("main.tooltip.toggle_all_fields_hide"))
        self.btn_toggle_all_fields.clicked.connect(self.toggle_all_optional_fields)

        self.btn_panel_flip = QPushButton()
        self.btn_panel_flip.setIconSize(QSize(18, 18))
        self.btn_panel_flip.setObjectName("btn_settings")
        self.btn_panel_flip.setFixedSize(32, 32)
        self.btn_panel_flip.clicked.connect(self.toggle_panel_layout)

        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setIconSize(QSize(18, 18))
        self.btn_theme_toggle.setObjectName("btn_settings")
        self.btn_theme_toggle.setFixedSize(32, 32)
        self.btn_theme_toggle.clicked.connect(self.cycle_theme_mode)

        self.btn_help = QPushButton()
        self.btn_help.setIcon(render_svg_icon("help", size=18))
        self.btn_help.setIconSize(QSize(18, 18))
        self.btn_help.setObjectName("btn_settings")
        self.btn_help.setFixedSize(32, 32)
        self.btn_help.setToolTip(self.tr("main.tooltip.help"))
        self.btn_help.clicked.connect(self.open_help_dialog)

        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(render_svg_icon("settings", size=22))
        self.btn_settings.setIconSize(QSize(22, 22))
        self.btn_settings.setObjectName("btn_settings")
        self.btn_settings.setFixedSize(40, 32)
        self.btn_settings.setToolTip(self.tr("main.tooltip.settings"))
        self.btn_settings.clicked.connect(self.open_settings_dialog)

        self.lbl_app_version = QLabel(f"v{APP_VERSION}")
        self.lbl_app_version.setObjectName("lbl_app_version")

        self.top_bar_layout = QHBoxLayout()
        self.top_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.top_bar_layout.addWidget(self.lbl_app_version)
        self.top_bar_layout.addStretch()
        self.top_bar_layout.addWidget(self.btn_toggle_all_fields)
        self.top_bar_layout.addWidget(self.btn_panel_flip)
        self.top_bar_layout.addWidget(self.btn_theme_toggle)
        self.top_bar_layout.addWidget(self.btn_help)
        self.top_bar_layout.addWidget(self.btn_settings)
        self.main_layout.addLayout(self.top_bar_layout)

        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.main_layout.addLayout(self.content_layout)

        self.splitter = QSplitter(Qt.Horizontal)
        self.content_layout.addWidget(self.splitter)

        self.panel_layout_mode = database.get_setting("panel_layout", "standard")

        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(SPACING_MD)
        
        self.search_layout = QHBoxLayout()
        self.search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_layout.setSpacing(SPACING_SM)
        self.txt_search = QLineEdit()
        self.txt_search.setFixedHeight(32)
        self.txt_search.setPlaceholderText(self.tr("main.search.placeholder"))
        self.txt_search.addAction(render_svg_icon("search", size=16), QLineEdit.LeadingPosition)
        self._search_debounce = QTimer(self)
        self._search_debounce.setSingleShot(True)
        self._search_debounce.setInterval(150)
        self._search_debounce.timeout.connect(self.filter_images)
        self.txt_search.textChanged.connect(lambda *_: self._search_debounce.start())
        
        self.search_layout.addWidget(self.txt_search)
        self.left_layout.addLayout(self.search_layout)
        
        self.import_sync_layout = QHBoxLayout()
        self.import_sync_layout.setContentsMargins(0, 0, 0, 0)
        self.import_sync_layout.setSpacing(SPACING_MD)
        
        self.btn_import_folder = QPushButton(self.tr("main.button.import_folder"))
        self.btn_import_folder.setIcon(render_svg_icon("import_folder", size=18))
        self.btn_import_folder.setIconSize(QSize(18, 18))
        self.btn_import_folder.setFixedHeight(38)
        self.btn_import_folder.setToolTip(self.tr("main.tooltip.import_folder"))
        self.btn_import_folder.clicked.connect(self.open_folder_dialog)

        self.btn_import_files = QPushButton(self.tr("main.button.import_files"))
        self.btn_import_files.setIcon(render_svg_icon("import_files", size=18))
        self.btn_import_files.setIconSize(QSize(18, 18))
        self.btn_import_files.setFixedHeight(38)
        self.btn_import_files.setToolTip(self.tr("main.tooltip.import_files"))
        self.btn_import_files.clicked.connect(self.open_file_dialog)
        
        self.btn_sync = QPushButton()
        self.btn_sync.setIcon(render_svg_icon("directory_sync", size=18))
        self.btn_sync.setIconSize(QSize(18, 18))
        self.btn_sync.setObjectName("btn_view_toggle")
        self.btn_sync.setFixedSize(40, 38)
        self.btn_sync.setToolTip("取り込み済みフォルダを同期（増減を反映）\nこれまでに取り込んだフォルダを再スキャンし、新規追加された画像を取り込み、\n削除・移動された画像をリストから取り除きます。")
        self.btn_sync.clicked.connect(self.sync_folders)
        
        self.import_sync_layout.addWidget(self.btn_import_folder, 1)
        self.import_sync_layout.addWidget(self.btn_import_files, 1)
        self.import_sync_layout.addWidget(self.btn_sync)
        self.left_layout.addLayout(self.import_sync_layout)
        
        self.sort_view_layout = QHBoxLayout()
        self.sort_view_layout.setContentsMargins(0, 0, 0, 0)
        self.sort_view_layout.setSpacing(SPACING_MD)
        
        self.lbl_sort_icon = QLabel()
        self.lbl_sort_icon.setPixmap(render_svg_icon("sort", size=18).pixmap(18, 18))
        self.lbl_sort_icon.setFixedSize(18, 18)
        self.lbl_sort_icon.setToolTip("並べ替え")
        
        self.cmb_sort = CenteredComboBox()
        self.cmb_sort.setObjectName("cmb_sort")
        self.cmb_sort.setFixedHeight(38)
        self.cmb_sort.addItem(render_svg_icon("name", size=16), self.tr("main.sort.by_name"))
        self.cmb_sort.addItem(render_svg_icon("created_date", size=16), self.tr("main.sort.by_created"))
        self.cmb_sort.addItem(render_svg_icon("edited_date", size=16), self.tr("main.sort.by_edited"))
        self.cmb_sort.addItem(render_svg_icon("imported_date", size=16), self.tr("main.sort.by_imported"))
        self.cmb_sort.addItem(render_svg_icon("rating_sort", size=16), self.tr("main.sort.by_rating"))
        self.cmb_sort.addItem(render_svg_icon("filesize_sort", size=16), self.tr("main.sort.by_filesize"))
        self.cmb_sort.currentIndexChanged.connect(self.on_sort_changed)
        
        self.btn_sort_direction = QPushButton()
        self.btn_sort_direction.setIcon(render_svg_icon("arrow_upward", size=18))
        self.btn_sort_direction.setIconSize(QSize(18, 18))
        self.btn_sort_direction.setObjectName("btn_view_toggle")
        self.btn_sort_direction.setFixedSize(40, 38)
        self.btn_sort_direction.setToolTip(self.tr("main.tooltip.sort_direction_asc"))
        self.btn_sort_direction.clicked.connect(self.toggle_sort_direction)
        
        self.btn_view_toggle = QPushButton()
        self.btn_view_toggle.setIcon(render_svg_icon("grid_view", size=16))
        self.btn_view_toggle.setIconSize(QSize(16, 16))
        self.btn_view_toggle.setObjectName("btn_view_toggle")
        self.btn_view_toggle.setFixedSize(40, 38)
        self.btn_view_toggle.setToolTip(self.tr("main.tooltip.view_toggle_to_grid"))
        self.btn_view_toggle.clicked.connect(self.toggle_view_mode)
        
        self.group_mode = "none"
        self.collapsed_folders = set()
        self.btn_group_toggle = QPushButton()
        self.btn_group_toggle.setIcon(render_svg_icon("group_by_folder", size=18))
        self.btn_group_toggle.setIconSize(QSize(18, 18))
        self.btn_group_toggle.setObjectName("btn_view_toggle")
        self.btn_group_toggle.setFixedSize(40, 38)
        self.btn_group_toggle.setToolTip(self.tr("main.tooltip.group_toggle_enable"))
        self.btn_group_toggle.clicked.connect(self.toggle_group_mode)
        
        self.sort_view_layout.addWidget(self.lbl_sort_icon)
        self.sort_view_layout.addWidget(self.cmb_sort, 1)
        self.sort_view_layout.addWidget(self.btn_sort_direction)
        self.sort_view_layout.addWidget(self.btn_view_toggle)
        self.sort_view_layout.addWidget(self.btn_group_toggle)
        
        self.left_layout.addLayout(self.sort_view_layout)
        
        self.grid_size_layout = QHBoxLayout()
        self.grid_size_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_size_layout.setSpacing(SPACING_SM)
        self.grid_size_layout.addStretch()
        
        self.grid_tile_size = "medium"
        
        self.btn_grid_small = QPushButton(self.tr("main.button.grid_small"))
        self.btn_grid_small.setIcon(render_svg_icon("grid_small", size=14))
        self.btn_grid_small.setIconSize(QSize(14, 14))
        self.btn_grid_small.setObjectName("btn_preview_size")
        self.btn_grid_small.setFixedSize(72, 26)
        self.btn_grid_small.setToolTip(self.tr("main.tooltip.grid_small"))
        self.btn_grid_small.clicked.connect(lambda: self.set_grid_tile_size("small"))
        
        self.btn_grid_medium = QPushButton(self.tr("main.button.grid_medium"))
        self.btn_grid_medium.setIcon(render_svg_icon("grid_medium", size=14))
        self.btn_grid_medium.setIconSize(QSize(14, 14))
        self.btn_grid_medium.setObjectName("btn_preview_size_active")
        self.btn_grid_medium.setFixedSize(72, 26)
        self.btn_grid_medium.setToolTip(self.tr("main.tooltip.grid_medium"))
        self.btn_grid_medium.clicked.connect(lambda: self.set_grid_tile_size("medium"))
        
        self.btn_grid_large = QPushButton(self.tr("main.button.grid_large"))
        self.btn_grid_large.setIcon(render_svg_icon("grid_large", size=14))
        self.btn_grid_large.setIconSize(QSize(14, 14))
        self.btn_grid_large.setObjectName("btn_preview_size")
        self.btn_grid_large.setFixedSize(72, 26)
        self.btn_grid_large.setToolTip(self.tr("main.tooltip.grid_large"))
        self.btn_grid_large.clicked.connect(lambda: self.set_grid_tile_size("large"))
        
        self.grid_size_buttons = {
            "small": self.btn_grid_small,
            "medium": self.btn_grid_medium,
            "large": self.btn_grid_large,
        }
        
        self.grid_size_layout.addWidget(self.btn_grid_small)
        self.grid_size_layout.addWidget(self.btn_grid_medium)
        self.grid_size_layout.addWidget(self.btn_grid_large)
        
        self.grid_size_widget = QWidget()
        self.grid_size_widget.setLayout(self.grid_size_layout)
        self.grid_size_widget.setVisible(False)
        self.left_layout.addWidget(self.grid_size_widget)
        
        self.image_list = ImageListWidget()
        self.image_list.setObjectName("image_list")
        self.image_list.setItemDelegate(FolderHeaderDelegate(self))
        self.image_list.setIconSize(QSize(60, 60))
        self.image_list.setViewMode(QListWidget.ListMode)
        self.image_list.setWordWrap(True)
        self.image_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.image_list.itemSelectionChanged.connect(self.on_image_selected)
        self.image_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self.show_image_context_menu)
        self.image_list.itemClicked.connect(self.on_image_list_item_clicked)
        self.image_list.filesDropped.connect(self.handle_dropped_paths)
        self.image_list.dragHoverChanged.connect(self.on_drag_hover_changed)
        
        self.lbl_empty_state = QLabel(self.tr("main.label.empty_state"))
        self.lbl_empty_state.setObjectName("lbl_placeholder_state")
        self.lbl_empty_state.setAlignment(Qt.AlignCenter)
        
        self.lbl_drag_hover = QLabel(self.tr("main.label.drag_hover"))
        self.lbl_drag_hover.setObjectName("lbl_placeholder_state")
        self.lbl_drag_hover.setAlignment(Qt.AlignCenter)
        self.lbl_drag_hover.setWordWrap(True)
        
        self.image_list_stack = QStackedWidget()
        self.image_list_stack.addWidget(self.image_list)
        self.image_list_stack.addWidget(self.lbl_empty_state)
        self.image_list_stack.addWidget(self.lbl_drag_hover)
        self.left_layout.addWidget(self.image_list_stack)
        
        self.lbl_library_status = QLabel("")
        self.lbl_library_status.setObjectName("lbl_library_status")
        self.lbl_library_status.setAlignment(Qt.AlignCenter)
        self.lbl_library_status.setContentsMargins(0, 6, 0, 0)
        self.left_layout.addWidget(self.lbl_library_status)
        
        self.import_format_container = QWidget()
        _fmt_row = QHBoxLayout(self.import_format_container)
        _fmt_row.setContentsMargins(0, 0, 0, 0)
        _fmt_row.setSpacing(SPACING_XS)

        self.btn_toggle_import_formats = QPushButton()
        self.btn_toggle_import_formats.setIcon(render_svg_icon("hide_form", size=14))
        self.btn_toggle_import_formats.setIconSize(QSize(14, 14))
        self.btn_toggle_import_formats.setObjectName("btn_copy")
        self.btn_toggle_import_formats.setFixedSize(22, 22)
        self.btn_toggle_import_formats.setToolTip(self.tr("main.tooltip.import_formats_hide"))
        self.btn_toggle_import_formats.clicked.connect(self.toggle_import_format_visibility)
        _fmt_row.addWidget(self.btn_toggle_import_formats, 0, Qt.AlignTop)

        self.import_format_body = QWidget()
        _fmt_outer = QVBoxLayout(self.import_format_body)
        _fmt_outer.setContentsMargins(0, 0, 0, 0)
        _fmt_outer.setSpacing(SPACING_SM)

        format_defs = [
            ("png",  "PNG",  (".png",),         True,  ""),
            ("jpg",  "JPG",  (".jpg",),         True,  ""),
            ("jpeg", "JPEG", (".jpeg",),        True,  ""),
            ("webp", "WEBP", (".webp",),        True,  ""),
            ("gif",  "GIF",  (".gif",),         False, self.tr("main.tooltip.format_gif")),
            ("bmp",  "BMP",  (".bmp",),         False, ""),
            ("tiff", "TIFF", (".tif", ".tiff"), False, self.tr("main.tooltip.format_tiff")),
        ]
        self.import_format_checks = {}
        _fmt_flow = FlowLayout(hspacing=SPACING_SM, vspacing=SPACING_XS, center=True)
        for _key, _label, _exts, _default_on, _tip in format_defs:
            _chk = QCheckBox(_label)
            _chk.setChecked(database.get_setting(f"import_ext_{_key}", "1" if _default_on else "0") == "1")
            if _tip:
                _chk.setToolTip(_tip)
            _chk.toggled.connect(lambda checked, k=_key: self._on_import_format_toggled(k, checked))
            self.import_format_checks[_key] = (_chk, _exts)
            _fmt_flow.addWidget(_chk)
        _fmt_outer.addLayout(_fmt_flow)

        _fmt_note = QLabel(self.tr("main.label.gif_note"))
        _fmt_note.setObjectName("lbl_import_format_note")
        _fmt_note.setAlignment(Qt.AlignCenter)
        _fmt_note.setWordWrap(True)
        _fmt_outer.addWidget(_fmt_note)

        _fmt_row.addWidget(self.import_format_body, 1)
        self.left_layout.addWidget(self.import_format_container)

        _import_format_visible = database.get_setting("import_format_visible", "0") == "1"
        self.import_format_body.setVisible(_import_format_visible)
        if _import_format_visible:
            self.btn_toggle_import_formats.setIcon(render_svg_icon("hide_form", size=14))
            self.btn_toggle_import_formats.setToolTip(self.tr("main.tooltip.import_formats_hide"))
        else:
            self.btn_toggle_import_formats.setIcon(render_svg_icon("show_form", size=14))
            self.btn_toggle_import_formats.setToolTip(self.tr("main.tooltip.import_formats_show"))
        
        self.btn_delete = QPushButton(self.tr("main.button.delete_selected"))
        self.btn_delete.setIcon(render_svg_icon("delete", size=16, color="#ed2c3a"))
        self.btn_delete.setIconSize(QSize(16, 16))
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.setFixedHeight(40)
        self.btn_delete.setToolTip(self.tr("main.tooltip.delete"))
        self.btn_delete.clicked.connect(self.delete_image_from_db)
        self.left_layout.addWidget(self.btn_delete)
        
        self.right_container = QWidget()
        self.right_container_layout = QVBoxLayout(self.right_container)
        self.right_container_layout.setContentsMargins(SPACING_XXL, 0, 0, 0)
        self.right_container_layout.setSpacing(SPACING_LG)
        
        self.meta_edit_layout = QHBoxLayout()
        self.meta_edit_layout.setContentsMargins(0, 0, 0, 0)
        self.meta_edit_layout.setSpacing(0)
        
        self.lbl_filename_title = create_icon_label_row("file_name", self.tr("metadata.filename.header"), icon_size=16)
        self.lbl_filename_title.setFixedWidth(80)
        self.txt_filename = QLineEdit()
        self.txt_filename.setFixedHeight(32)
        self.txt_filename.setToolTip(self.tr("metadata.filename.tooltip"))
        
        self.lbl_name_title = create_icon_label_row("name", self.tr("metadata.name.header"), icon_size=16)
        self.lbl_name_title.setFixedWidth(58)
        self.txt_display_name = QLineEdit()
        self.txt_display_name.setFixedHeight(32)
        self.txt_display_name.setToolTip(self.tr("metadata.name.tooltip"))
        
        self.meta_edit_layout.addWidget(self.lbl_filename_title)
        self.meta_edit_layout.addSpacing(SPACING_MD)
        self.meta_edit_layout.addWidget(self.txt_filename, 1)
        self.meta_edit_layout.addSpacing(SPACING_MD)
        self.meta_edit_layout.addWidget(self.lbl_name_title)
        self.meta_edit_layout.addSpacing(0)
        self.meta_edit_layout.addWidget(self.txt_display_name, 1)

        self.right_container_layout.addLayout(self.meta_edit_layout)
        
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(0, 0, SPACING_XXL - SPACING_LG + 12, 0)
        self.right_layout.setSpacing(SPACING_MD)
        
        self.preview_size_layout = QHBoxLayout()
        self.preview_size_layout.setContentsMargins(PREVIEW_SIDE_PADDING, 0, PREVIEW_SIDE_PADDING, 0)
        self.preview_size_layout.setSpacing(SPACING_SM)
        
        self.btn_preview_hidden = QPushButton(self.tr("metadata.preview.button_hidden"))
        self.btn_preview_hidden.setIcon(render_svg_icon("preview_hidden", size=14))
        self.btn_preview_hidden.setIconSize(QSize(14, 14))
        self.btn_preview_hidden.setObjectName("btn_preview_size")
        self.btn_preview_hidden.setFixedSize(84, 28)
        self.btn_preview_hidden.setToolTip(self.tr("metadata.preview.tooltip_hidden"))
        self.btn_preview_hidden.clicked.connect(lambda: self.set_preview_size_mode("hidden"))

        self.btn_preview_standard = QPushButton(self.tr("metadata.preview.button_standard"))
        self.btn_preview_standard.setIcon(render_svg_icon("preview_standard", size=14))
        self.btn_preview_standard.setIconSize(QSize(14, 14))
        self.btn_preview_standard.setObjectName("btn_preview_size_active")
        self.btn_preview_standard.setFixedSize(84, 28)
        self.btn_preview_standard.setToolTip(self.tr("metadata.preview.tooltip_standard"))
        self.btn_preview_standard.clicked.connect(lambda: self.set_preview_size_mode("standard"))
        
        self.btn_preview_compact = QPushButton(self.tr("metadata.preview.button_compact"))
        self.btn_preview_compact.setIcon(render_svg_icon("preview_compact", size=14))
        self.btn_preview_compact.setIconSize(QSize(14, 14))
        self.btn_preview_compact.setObjectName("btn_preview_size")
        self.btn_preview_compact.setFixedSize(108, 28)
        self.btn_preview_compact.setToolTip(self.tr("metadata.preview.tooltip_compact"))
        self.btn_preview_compact.clicked.connect(lambda: self.set_preview_size_mode("compact"))
        
        self.btn_preview_fullscreen = QPushButton(self.tr("metadata.preview.button_fullscreen"))
        self.btn_preview_fullscreen.setIcon(render_svg_icon("preview_fullscreen", size=14))
        self.btn_preview_fullscreen.setIconSize(QSize(14, 14))
        self.btn_preview_fullscreen.setObjectName("btn_preview_size")
        self.btn_preview_fullscreen.setFixedSize(96, 28)
        self.btn_preview_fullscreen.setToolTip(self.tr("metadata.preview.tooltip_fullscreen"))
        self.btn_preview_fullscreen.clicked.connect(self.enter_fullscreen_preview)
        
        self.btn_reading_mode = QPushButton()
        self.btn_reading_mode.setIcon(render_svg_icon("reading_mode", size=16))
        self.btn_reading_mode.setIconSize(QSize(16, 16))
        self.btn_reading_mode.setObjectName("btn_preview_size")
        self.btn_reading_mode.setFixedSize(36, 28)
        self.btn_reading_mode.setToolTip(self.tr("metadata.tooltip.reading_mode"))
        self.btn_reading_mode.setEnabled(False)
        self.btn_reading_mode.clicked.connect(self.open_reading_mode)
        
        self.preview_size_buttons = [self.btn_preview_hidden, self.btn_preview_standard, self.btn_preview_compact]
        self.preview_size_layout.addWidget(self.btn_preview_hidden)
        self.preview_size_layout.addWidget(self.btn_preview_standard)
        self.preview_size_layout.addWidget(self.btn_preview_compact)
        self.preview_size_layout.addWidget(self.btn_preview_fullscreen)
        self.preview_size_layout.addWidget(self.btn_reading_mode)
        
        self.preview_size_layout.addStretch()
        
        self.star_rating = StarRatingWidget()
        self.star_rating.setToolTip(self.tr("metadata.tooltip.star_rating"))
        self.preview_size_layout.addWidget(self.star_rating)
        
        self.preview_size_container = QWidget()
        self.preview_size_container.setLayout(self.preview_size_layout)
        self.preview_size_container.setFixedHeight(28)
        
        self.preview_size_mode = "standard"
        
        self.lbl_preview = PreviewLabel(self.tr("metadata.preview.select_prompt"), main_app=self)
        self.lbl_preview.setObjectName("lbl_preview")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setMinimumSize(360, 420)
        self.lbl_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.btn_prev_image = QPushButton()
        self.btn_prev_image.setIcon(render_svg_icon("chevron_left", size=20))
        self.btn_prev_image.setIconSize(QSize(20, 20))
        self.btn_prev_image.setObjectName("btn_nav_image")
        self.btn_prev_image.setFixedSize(40, 40)
        self.btn_prev_image.setToolTip(self.tr("metadata.tooltip.prev_image"))
        self.btn_prev_image.clicked.connect(self.prev_image)
        
        self.btn_next_image = QPushButton()
        self.btn_next_image.setIcon(render_svg_icon("chevron_right", size=20))
        self.btn_next_image.setIconSize(QSize(20, 20))
        self.btn_next_image.setObjectName("btn_nav_image")
        self.btn_next_image.setFixedSize(40, 40)
        self.btn_next_image.setToolTip(self.tr("metadata.tooltip.next_image"))
        self.btn_next_image.clicked.connect(self.next_image)
        
        self.preview_layout = QHBoxLayout()
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_layout.setSpacing(SPACING_MD)
        self.preview_layout.addWidget(self.btn_prev_image)
        self.preview_layout.addWidget(self.lbl_preview, 1)
        self.preview_layout.addWidget(self.btn_next_image)
        self.right_layout.addLayout(self.preview_layout, 20)
        self.preview_layout_stretch_index = self.right_layout.count() - 1

        self.slideshow_layout = QHBoxLayout()
        self.slideshow_layout.setContentsMargins(0, 0, 0, 0)
        self.slideshow_layout.setSpacing(SPACING_MD)
        
        self.btn_save = QPushButton(self.tr("metadata.button.save"))
        self.btn_save.setIcon(render_svg_icon("save", size=16))
        self.btn_save.setIconSize(QSize(16, 16))
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setFixedHeight(36)
        self.btn_save.clicked.connect(self.save_metadata_changes)
        
        self.btn_save_as_new = QPushButton(self.tr("metadata.button.save_as_new"))
        self.btn_save_as_new.setIcon(render_svg_icon("save_as_new", size=16))
        self.btn_save_as_new.setIconSize(QSize(16, 16))
        self.btn_save_as_new.setFixedHeight(36)
        self.btn_save_as_new.setToolTip(self.tr("metadata.tooltip.save_as_new"))
        self.btn_save_as_new.clicked.connect(self.save_as_new_copy)
        
        self.btn_slideshow = QPushButton(self.tr("metadata.button.slideshow_idle"))
        self.btn_slideshow.setObjectName("btn_slideshow_idle")
        self.btn_slideshow.setFixedHeight(36)
        self.btn_slideshow.setToolTip(self.tr("metadata.tooltip.slideshow"))
        self.btn_slideshow.clicked.connect(self.toggle_slideshow)
        
        self.slideshow_speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
        self.slideshow_speed = 1.0
        self.slideshow_base_interval_sec = 3
        
        self.btn_speed = QPushButton("1.0x")
        self.btn_speed.setObjectName("btn_speed")
        self.btn_speed.setFixedSize(64, 36)
        self.btn_speed.setToolTip(self.tr("metadata.tooltip.speed"))
        self.btn_speed.clicked.connect(self.show_speed_menu)
        
        self.slideshow_layout.addWidget(self.btn_save, 3)
        self.slideshow_layout.addWidget(self.btn_save_as_new, 3)
        self.slideshow_layout.addWidget(self.btn_slideshow, 2)
        self.slideshow_layout.addWidget(self.btn_speed)
        self.slideshow_container = QWidget()
        self.slideshow_container.setLayout(self.slideshow_layout)
        self.slideshow_container.setFixedHeight(36)

        self.right_layout.addWidget(self.create_divider())
        self.txt_memo = QLineEdit()
        self.txt_memo.setObjectName("txt_memo")
        self.txt_memo.setPlaceholderText(self.tr("metadata.memo.placeholder"))
        header_layout, self.btn_clear_memo, self.btn_toggle_memo = self.create_section_header(self.tr("metadata.memo.header"), self.txt_memo, icon_name="release_notes")
        self.right_layout.addLayout(header_layout)
        self.right_layout.addWidget(self.txt_memo)

        self.right_layout.addWidget(self.create_divider())
        self.txt_model = QTextEdit()
        self.txt_model.setObjectName("txt_model")
        self.txt_model.setMaximumHeight(35)
        self.txt_model.setReadOnly(True)
        header_layout, self.btn_clear_model, self.btn_toggle_model = self.create_section_header(self.tr("metadata.model.header"), self.txt_model, icon_name="model")
        self.right_layout.addLayout(header_layout)
        self.right_layout.addWidget(self.txt_model)
        
        self.generation_params_container = QWidget()
        self.generation_params_layout = QHBoxLayout(self.generation_params_container)
        self.generation_params_layout.setContentsMargins(30, 0, 0, 0)
        self.generation_params_layout.setSpacing(0)
        self.generation_params_container.setVisible(False)
        self.right_layout.addWidget(self.generation_params_container)
        
        self.right_layout.addWidget(self.create_divider())
        self.txt_prompt = QTextEdit()
        self.txt_prompt.setObjectName("txt_prompt")
        self.txt_prompt.setMaximumHeight(105)
        header_layout, self.btn_clear_prompt, self.btn_toggle_prompt = self.create_section_header(self.tr("metadata.prompt.header"), self.txt_prompt, icon_name="prompt")
        self.right_layout.addLayout(header_layout)
        self.right_layout.addWidget(self.txt_prompt)
        
        self.right_layout.addWidget(self.create_divider())
        self.txt_neg_prompt = QTextEdit()
        self.txt_neg_prompt.setObjectName("txt_prompt")
        self.txt_neg_prompt.setMaximumHeight(105)
        header_layout, self.btn_clear_neg_prompt, self.btn_toggle_neg_prompt = self.create_section_header(self.tr("metadata.negative_prompt.header"), self.txt_neg_prompt, icon_name="negative_prompt")
        self.right_layout.addLayout(header_layout)
        self.right_layout.addWidget(self.txt_neg_prompt)
        
        self.right_layout.addWidget(self.create_divider())
        self.txt_metadata = QTextEdit()
        self.txt_metadata.setObjectName("txt_metadata")
        self.txt_metadata.setMaximumHeight(125)
        header_layout, self.btn_clear_metadata, self.btn_toggle_metadata = self.create_section_header(self.tr("metadata.other_params.header"), self.txt_metadata, icon_name="parameters")
        self.right_layout.addLayout(header_layout)
        self.right_layout.addWidget(self.txt_metadata)

        self.right_layout.addStretch(1)
        
        for field_widget, toggle_btn in [
            (self.txt_memo, self.btn_toggle_memo),
            (self.txt_model, self.btn_toggle_model),
            (self.txt_prompt, self.btn_toggle_prompt),
            (self.txt_neg_prompt, self.btn_toggle_neg_prompt),
            (self.txt_metadata, self.btn_toggle_metadata),
        ]:
            field_widget.setVisible(False)
            toggle_btn.setIcon(render_svg_icon("show_form", size=14))
            toggle_btn.setToolTip(self.tr("metadata.tooltip.section_toggle_show"))
        
        self.right_scroll.setWidget(self.right_widget)
        self.right_container_layout.addWidget(self.preview_size_container)
        self.right_container_layout.addWidget(self.right_scroll)
        self.right_container_layout.addWidget(self.slideshow_container)
        
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_container)
        self.apply_panel_layout(self.panel_layout_mode)
        self.current_image_id = None
        
        saved_sort_index = int(database.get_setting("last_sort_index", "0"))
        self.sort_index = saved_sort_index
        saved_sort_dir = database.get_setting("last_sort_dir", "ASC")
        sort_expr_map = {
            0: "file_name COLLATE NOCASE",
            1: "file_mtime",
            2: "COALESCE(updated_at, file_mtime)",
            3: "COALESCE(imported_at, file_mtime)",
            4: "rating",
            5: "COALESCE(file_size, 0)",
        }
        self.sort_expr = sort_expr_map.get(saved_sort_index, "file_name COLLATE NOCASE")
        self.sort_dir = saved_sort_dir if saved_sort_dir in ("ASC", "DESC") else "ASC"
        
        self.cmb_sort.blockSignals(True)
        self.cmb_sort.setCurrentIndex(saved_sort_index)
        self.cmb_sort.blockSignals(False)
        if self.sort_dir == "DESC":
            self.btn_sort_direction.setIcon(render_svg_icon("arrow_downward", size=18))
            self.btn_sort_direction.setIconSize(QSize(18, 18))
            self.btn_sort_direction.setToolTip(self.tr("main.tooltip.sort_direction_desc"))
        
        self.view_mode = "list"
        self._thumbnail_cache = OrderedDict()
        self._path_exists_cache = {}
        self._all_collapsed_warning_shown = False
        
        self.collapsed_folders = database.get_collapsed_folders()
        if database.get_setting("last_group_mode", "none") == "folder":
            self.group_mode = "folder"
            self.btn_group_toggle.setObjectName("btn_group_toggle_active")
            self.btn_group_toggle.setToolTip(self.tr("main.tooltip.group_toggle_disable"))
            self.btn_group_toggle.setIcon(render_svg_icon("group_by_folder", size=18, color=SVG_ICON_COLOR_ON_ACCENT))
            self._repolish(self.btn_group_toggle)
            self.btn_reading_mode.setEnabled(True)
            self.btn_view_toggle.setEnabled(False)
            self.btn_view_toggle.setToolTip(self.tr("main.tooltip.view_toggle_disabled_grouped"))
        
        self.timer = QTimer(self)
        self.timer.setInterval(int(self.slideshow_base_interval_sec * 1000 / self.slideshow_speed))
        self.timer.timeout.connect(self.next_image)
        
        self.apply_theme()
        try:
            QGuiApplication.styleHints().colorSchemeChanged.connect(self.on_system_theme_changed)
        except Exception as e:
            print(f"外観モードの自動検出に対応していません（固定テーマで動作します）: {e}")
        
        self.load_images_from_db()

    def tr(self, key):
        return i18n.tr(key, self.current_lang)

    def is_system_dark_mode(self):
        """macOSの現在の外観モード（ダーク/ライト）を判定する。判定できない場合はダークモードを既定にする。"""
        try:
            scheme = QGuiApplication.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Light:
                return False
            if scheme == Qt.ColorScheme.Dark:
                return True
        except Exception:
            pass
        return True

    def on_system_theme_changed(self, *_args):
        """OSの外観モードが変更された時に呼ばれ、テーマを再適用する"""
        self.apply_theme()

    def apply_theme(self):
        """現在の外観モード設定（自動/ダーク固定/ライト固定）に応じたテーマを構築し、ウィンドウ全体に適用する"""
        theme_mode = database.get_setting("theme_mode", "auto")
        if theme_mode == "dark":
            self.is_dark = True
        elif theme_mode == "light":
            self.is_dark = False
        else:
            self.is_dark = self.is_system_dark_mode()
        self.theme_colors = DARK_COLORS if self.is_dark else LIGHT_COLORS
        self.setStyleSheet(self.build_stylesheet(self.theme_colors))
        
        for widget_name in ("btn_slideshow", "btn_save", "btn_preview_hidden", "btn_preview_standard", "btn_preview_compact",
                            "btn_grid_small", "btn_grid_medium", "btn_grid_large", "btn_group_toggle"):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                self._repolish(widget)
        
        caution_color = self.theme_colors['caution_bg']
        for widget_name, icon_name in (("btn_delete", "delete"), ("btn_reset_database", "reset_database"),
                                        ("btn_reset_settings", "reset_settings")):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                widget.setIcon(render_svg_icon(icon_name, size=16, color=caution_color))
        
        image_list = getattr(self, "image_list", None)
        if image_list is not None:
            image_list.viewport().update()
        
        fullscreen_window = getattr(self, "fullscreen_window", None)
        if fullscreen_window is not None:
            fullscreen_window.setStyleSheet(self.build_stylesheet(self.theme_colors))

        self._update_theme_toggle_icon()

    def cycle_theme_mode(self):
        """上部バーの外観モードボタン用。クリックのたびに 自動→ダーク→ライト→自動… と
        1クリックで巡回する（設定画面の3択ラジオボタンと同じ設定項目を共有する）。"""
        cycle_order = ["auto", "dark", "light"]
        current_mode = database.get_setting("theme_mode", "auto")
        current_index = cycle_order.index(current_mode) if current_mode in cycle_order else 0
        new_mode = cycle_order[(current_index + 1) % len(cycle_order)]
        database.set_setting("theme_mode", new_mode)
        self.apply_theme()

    def _update_theme_toggle_icon(self):
        """外観モードボタンのアイコン・ツールチップを更新する。
        「自動（システムに追従）」の時だけ専用アイコン（night_sight_auto）を表示し、
        ダーク固定／ライト固定の時は、今実際に表示されている見た目（dark_mode/light_mode）を
        そのまま表示する（2026-08-14〜。当初は自動時もdark_mode/light_modeを流用していたが、
        「追従中」であることが見た目だけでは分かりづらいとのフィードバックを受けて変更した）。"""
        btn = getattr(self, "btn_theme_toggle", None)
        if btn is None:
            return
        mode = database.get_setting("theme_mode", "auto")
        if mode == "auto":
            btn.setIcon(render_svg_icon("night_sight_auto", size=18))
        else:
            btn.setIcon(render_svg_icon("dark_mode" if self.is_dark else "light_mode", size=18))
        mode_labels = {
            "auto": self.tr("settings.theme.auto"),
            "dark": self.tr("settings.theme.dark"),
            "light": self.tr("settings.theme.light"),
        }
        btn.setToolTip(self.tr("main.tooltip.theme_toggle").format(mode=mode_labels.get(mode, mode)))

    def _repolish(self, widget):
        """objectName等を動的に変更した後、スタイルを再評価させて即座に反映させる"""
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def get_menu_stylesheet(self):
        """現在のテーマ色を使ったQMenu用スタイルシートを返す（速度メニュー・右クリックメニュー共通）"""
        c = self.theme_colors
        return f"""
            QMenu {{ background-color: {c['menu_bg']}; color: {c['menu_text']}; border: 1px solid {c['menu_border']}; }}
            QMenu::item {{ padding: 6px 20px 6px 12px; }}
            QMenu::icon {{ padding-left: 14px; padding-right: 10px; }}
            QMenu::item:selected {{ background-color: {c['accent_bg']}; color: {c['accent_text']}; }}
        """

    def build_stylesheet(self, c):
        """アプリ全体のスタイルシートを、指定されたカラーパレットから組み立てる"""
        return f"""
            QMainWindow, QWidget {{
                background-color: {c['window_bg']};
                color: {c['label_text']};
                font-family: 'Helvetica Neue', Arial, sans-serif;
            }}
            QScrollArea {{ background-color: {c['scroll_bg']}; border: none; }}
            QLabel {{ color: {c['label_text']}; font-weight: bold; font-size: {FONT_SIZE_BODY}px; background-color: transparent; }}
            QLabel#lbl_section_heading {{ font-size: {FONT_SIZE_HEADING}px; }}
            QGroupBox {{
                color: {c['label_text']}; font-weight: bold; font-size: {FONT_SIZE_HEADING}px;
                border: 1px solid {c['input_border']}; border-radius: 6px; margin-top: {SPACING_SM}px; padding-top: {SPACING_SM}px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: {SPACING_SM}px; padding: 0 {SPACING_XS}px; }}
            
            QLineEdit, QTextEdit {{
                background-color: {c['input_bg']}; color: {c['input_text']};
                border: 1px solid {c['input_border']}; border-radius: 6px; padding: 6px;
                selection-background-color: {c['accent_bg']}; selection-color: {c['accent_text']};
            }}
            
            QSpinBox {{
                background-color: {c['input_bg']}; color: {c['input_text']};
                border: 1px solid {c['input_border']}; border-radius: 6px; padding: 4px;
            }}
            
            QPushButton {{
                background-color: {c['button_bg']}; color: {c['button_text']};
                border: 1px solid {c['button_border']}; border-radius: 6px;
                font-weight: bold; padding: 6px 10px;
            }}
            QPushButton:hover {{ background-color: {c['button_hover']}; }}
            
            QComboBox {{
                background-color: {c['input_bg']}; color: {c['input_text']};
                border: 1px solid {c['input_border']}; border-radius: 6px; padding-left: 8px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {c['menu_bg']}; color: {c['menu_text']};
                border: 1px solid {c['menu_border']}; outline: none;
                selection-background-color: {c['accent_bg']}; selection-color: {c['accent_text']};
            }}
            QComboBox#cmb_sort {{ font-weight: bold; }}
            
            QPushButton#btn_preview_size {{ font-size: {FONT_SIZE_CAPTION}px; padding: 4px 8px; }}
            QPushButton#btn_preview_size_active {{
                font-size: {FONT_SIZE_CAPTION}px; padding: 4px 8px;
                background-color: {c['accent_bg']}; color: {c['accent_text']}; border: none;
            }}
            
            QLabel#star_label[filled="false"] {{ color: #999999; background-color: transparent; }}
            QLabel#star_label[filled="true"] {{ color: #f5c518; background-color: transparent; }}
            
            QListWidget#image_list {{
                background-color: {c['list_bg']}; color: {c['list_text']};
                border: 1px solid {c['list_border']}; border-radius: 6px;
            }}
            QListWidget#image_list::item {{ border-bottom: 1px solid {c['list_item_border']}; padding: 9px 8px; }}
            QListWidget#image_list::item:selected {{ background-color: {c['accent_bg']}; color: {c['accent_text']}; }}

            QTableWidget {{
                background-color: {c['list_bg']}; color: {c['list_text']};
                alternate-background-color: {c['input_bg']};
                border: 1px solid {c['list_border']}; border-radius: 6px;
                gridline-color: {c['list_item_border']};
            }}
            QTableWidget::item {{ padding: 6px; color: {c['list_text']}; }}
            QTableWidget::item:selected {{ background-color: {c['accent_bg']}; color: {c['accent_text']}; }}
            QHeaderView::section {{
                background-color: {c['menu_bg']}; color: {c['menu_text']};
                border: none; border-bottom: 1px solid {c['list_border']}; border-right: 1px solid {c['list_item_border']};
                padding: 6px 8px; font-weight: bold;
            }}
            
            QLabel#lbl_preview {{
                border: 1px solid {c['preview_border']}; background-color: {c['preview_bg']};
                color: {c['preview_text']}; border-radius: 6px; font-weight: normal;
            }}
            
            QPushButton#btn_delete {{
                background-color: {c['button_bg']}; color: {c['caution_bg']};
                border: 1.5px solid {c['caution_bg']}; border-radius: 6px;
            }}
            QPushButton#btn_delete:hover {{ background-color: {c['button_hover']}; }}
            QPushButton#btn_export {{ background-color: {c['export_bg']}; color: {c['export_text']}; border: none; }}
            QPushButton#btn_nav_image {{ border-radius: 20px; font-size: {ICON_SIZE_LG}px; }}
            QPushButton#btn_view_toggle {{ font-size: {ICON_SIZE_MD}px; }}
            QPushButton#btn_settings {{ font-size: {ICON_SIZE_XL}px; padding: 0px; }}
            QPushButton#btn_group_toggle_active {{
                font-size: {ICON_SIZE_MD}px; background-color: {c['accent_bg']}; color: {c['accent_text']}; border: none;
            }}
            
            QPushButton#btn_slideshow_idle {{ background-color: {c['accent_bg']}; color: {c['accent_text']}; border: none; }}
            QPushButton#btn_slideshow_active {{ background-color: {c['danger_bg']}; color: {c['danger_text']}; border: none; }}
            QPushButton#btn_save_multi {{ background-color: {c['accent_bg']}; color: {c['accent_text']}; border: none; }}
            
            QPushButton#btn_speed {{
                background-color: {c['speed_btn_bg']}; color: {c['speed_btn_text']};
                border: 1px solid {c['speed_btn_border']};
            }}
            
            QTextEdit#txt_model {{ color: {c['model_text']}; font-weight: bold; }}
            QTextEdit#txt_prompt {{ color: {c['prompt_text']}; font-weight: normal; }}
            QTextEdit#txt_metadata {{ color: {c['metadata_text']}; font-weight: normal; }}
            QLabel#lbl_generation_params {{ color: {c['metadata_text']}; font-weight: normal; font-size: {FONT_SIZE_HEADING}px; }}
            QLabel#lbl_app_version {{ color: #999999; font-weight: normal; font-size: {FONT_SIZE_BODY}px; }}
            QLabel#lbl_placeholder_state {{
                color: #999999; font-weight: normal; font-size: {FONT_SIZE_BODY}px;
                background-color: {c['input_bg']}; border: 1px solid {c['input_border']}; border-radius: 6px;
            }}
            QLabel#lbl_search_empty_overlay {{
                color: {c['metadata_text']}; font-weight: normal; font-size: {FONT_SIZE_BODY}px;
                background-color: transparent; border: none;
            }}
            QLabel#lbl_library_status {{
                color: {c['metadata_text']}; font-weight: normal; font-size: {FONT_SIZE_CAPTION}px;
                background-color: transparent; border: none;
            }}
            QLabel#lbl_import_format_note {{
                color: {c['metadata_text']}; font-weight: normal; font-size: {FONT_SIZE_CAPTION}px;
                background-color: transparent; border: none;
            }}
            QFrame#divider_line {{ background-color: {c['divider_color']}; border: none; }}
            
            QPushButton#btn_copy {{
                background-color: {c['copy_btn_bg']}; color: {c['copy_btn_text']};
                font-size: {FONT_SIZE_BODY}px; padding: 0px; border-radius: 4px;
            }}
            QPushButton#btn_copy_done {{
                background-color: {c['accent_bg']}; color: {c['accent_text']};
                font-size: {FONT_SIZE_BODY}px; padding: 0px; border-radius: 4px;
            }}
        """

    def create_divider(self):
        """画像リストの項目間の罫線と同じ考え方の、薄い横線を作る（QFrame）。
        ダークモードでは背景に同化しないよう、リスト罫線より明るい専用色（divider_color）を使う。"""
        line = QFrame()
        line.setObjectName("divider_line")
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        return line

    def create_section_header(self, title_text, target_widget, icon_name=None):
        """タイトルラベル・表示/非表示切替ボタン・コピーボタン・クリアボタンを並べた見出し行を作成する。
        icon_name を指定した場合は、同名アイコン＋テキスト（【】無し）の見出しにする。
        指定しない場合は、従来通り【】付きのプレーンテキスト見出しにする。
        ボタンは「表示/非表示切替 → コピー → クリア」の順に並び、間隔は12px。
        戻り値は (layout, btn_clear, btn_toggle) のタプル。"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, SPACING_XS)
        layout.setSpacing(12)
        
        if icon_name:
            label = create_icon_label_row(icon_name, title_text, icon_size=16, heading=True)
        else:
            label = QLabel(f"【{title_text}】")
            label.setObjectName("lbl_section_heading")
        
        btn_toggle = QPushButton()
        btn_toggle.setIcon(render_svg_icon("hide_form", size=14))
        btn_toggle.setIconSize(QSize(14, 14))
        btn_toggle.setObjectName("btn_copy")
        btn_toggle.setFixedSize(26, 22)
        btn_toggle.setToolTip(self.tr("metadata.tooltip.section_toggle_hide"))
        btn_toggle.clicked.connect(lambda: self.toggle_metadata_field_visibility(target_widget, btn_toggle))
        
        btn_copy = QPushButton()
        btn_copy.setIcon(render_svg_icon("content_copy", size=14))
        btn_copy.setIconSize(QSize(14, 14))
        btn_copy.setObjectName("btn_copy")
        btn_copy.setFixedSize(26, 22)
        btn_copy.setToolTip(self.tr("common.tooltip.copy"))
        btn_copy.clicked.connect(lambda: self.copy_text_to_clipboard(target_widget, btn_copy))
        
        btn_clear = QPushButton()
        btn_clear.setIcon(render_svg_icon("delete", size=14))
        btn_clear.setIconSize(QSize(14, 14))
        btn_clear.setObjectName("btn_copy")
        btn_clear.setFixedSize(26, 22)
        btn_clear.setToolTip(self.tr("metadata.tooltip.clear_field"))
        btn_clear.clicked.connect(lambda: (
            target_widget.clear(),
            self.autosize_metadata_field(target_widget) if hasattr(target_widget, "document") else None
        ))
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(btn_toggle)
        layout.addWidget(btn_copy)
        layout.addWidget(btn_clear)
        
        return layout, btn_clear, btn_toggle

    def copy_text_to_clipboard(self, source_widget, btn):
        """テキストエリア（QTextEdit）または1行入力欄（QLineEdit、メモ欄など）の内容を
        クリップボードにコピーし、ボタンに完了フィードバックを表示する"""
        text = source_widget.toPlainText() if hasattr(source_widget, "toPlainText") else source_widget.text()
        QApplication.clipboard().setText(text)

        btn.setIcon(QIcon())
        btn.setText("✓")
        btn.setObjectName("btn_copy_done")
        self._repolish(btn)
        QTimer.singleShot(1000, lambda: self.reset_copy_button(btn))

    def toggle_import_format_visibility(self):
        """取り込み対象の画像形式チェックボックス欄を一時的に非表示/再表示する（切り替えボタン自体は常に表示のまま）。
        この欄の表示/非表示状態は他の5つの編集フォームと異なり、次回起動時も維持する
        （2026-08-16〜。初期状態（未設定時）は非表示）。"""
        now_visible = not self.import_format_body.isVisible()
        self.import_format_body.setVisible(now_visible)
        database.set_setting("import_format_visible", "1" if now_visible else "0")
        if now_visible:
            self.btn_toggle_import_formats.setIcon(render_svg_icon("hide_form", size=14))
            self.btn_toggle_import_formats.setToolTip(self.tr("main.tooltip.import_formats_hide"))
        else:
            self.btn_toggle_import_formats.setIcon(render_svg_icon("show_form", size=14))
            self.btn_toggle_import_formats.setToolTip(self.tr("main.tooltip.import_formats_show"))

    def toggle_all_optional_fields(self):
        """メタデータ編集欄（使用モデル・プロンプト・ネガティブプロンプト・その他パラメータ）と
        取り込み形式欄を、まとめて表示/非表示に切り替える。1つでも表示中の項目があればまとめて
        非表示にし、すべて非表示の場合はまとめて表示する。"""
        field_pairs = [
            (self.txt_model, self.btn_toggle_model),
            (self.txt_prompt, self.btn_toggle_prompt),
            (self.txt_neg_prompt, self.btn_toggle_neg_prompt),
            (self.txt_metadata, self.btn_toggle_metadata),
            (self.txt_memo, self.btn_toggle_memo),
        ]
        any_visible = any(w.isVisible() for w, _ in field_pairs) or self.import_format_body.isVisible()
        target_visible = not any_visible

        for widget, btn in field_pairs:
            if widget.isVisible() != target_visible:
                self.toggle_metadata_field_visibility(widget, btn)
        if self.import_format_body.isVisible() != target_visible:
            self.toggle_import_format_visibility()

        if target_visible:
            self.btn_toggle_all_fields.setIcon(render_svg_icon("hide_form", size=18))
            self.btn_toggle_all_fields.setToolTip(self.tr("main.tooltip.toggle_all_fields_hide"))
        else:
            self.btn_toggle_all_fields.setIcon(render_svg_icon("show_form", size=18))
            self.btn_toggle_all_fields.setToolTip(self.tr("main.tooltip.toggle_all_fields_show"))

    def toggle_metadata_field_visibility(self, target_widget, btn_toggle):
        """使用モデル・プロンプト・ネガティブプロンプト・その他パラメータの編集フォームを一時的に非表示/再表示する。
        非表示にした分の高さは、残っている表示中のフォームに均等に配分する。"""
        now_visible = not target_widget.isVisible()
        target_widget.setVisible(now_visible)

        if target_widget is self.txt_model:
            has_content = self.generation_params_layout.count() > 0
            self.generation_params_container.setVisible(now_visible and has_content)

        if now_visible:
            btn_toggle.setIcon(render_svg_icon("hide_form", size=14))
            btn_toggle.setToolTip(self.tr("metadata.tooltip.section_toggle_hide"))
        else:
            btn_toggle.setIcon(render_svg_icon("show_form", size=14))
            btn_toggle.setToolTip("編集フォームを表示する")
        
        self.autosize_all_metadata_fields()

    def autosize_metadata_field(self, widget, max_height=160, min_height=40):
        """QTextEditの表示中の内容量に応じて、高さを前後1〜2行程度の余白になるよう自動調整する。
        内容が多い場合はmax_heightで頭打ちにし、それ以上は欄内スクロールで見る形にする。"""
        viewport_width = widget.viewport().width()
        widget.document().setTextWidth(viewport_width if viewport_width > 0 else 300)
        content_height = widget.document().size().height()
        line_height = QFontMetrics(widget.font()).height()
        padding = line_height * 1.5
        target_height = int(content_height + padding)
        target_height = max(min_height, min(target_height, max_height))
        widget.setMinimumHeight(target_height)
        widget.setMaximumHeight(target_height)

    def autosize_all_metadata_fields(self):
        """使用モデル・プロンプト・ネガティブプロンプト・その他パラメータの高さを、
        それぞれの内容量に応じて自動調整する（非表示の欄は対象外）。"""
        field_max_heights = [
            (self.txt_model, 60),
            (self.txt_prompt, 160),
            (self.txt_neg_prompt, 160),
            (self.txt_metadata, 180),
        ]
        for widget, max_h in field_max_heights:
            if widget.isVisible():
                self.autosize_metadata_field(widget, max_height=max_h)

    def reset_copy_button(self, btn):
        """コピーボタンの見た目を元に戻す"""
        btn.setText("")
        btn.setIcon(render_svg_icon("content_copy", size=14))
        btn.setIconSize(QSize(14, 14))
        btn.setObjectName("btn_copy")
        self._repolish(btn)

    def extract_model_name(self, metadata_text):
        if not metadata_text:
            return "Unknown Model"
        match = re.search(r'Model:\s*([^,]+)', metadata_text)
        if match:
            return match.group(1).strip()
        match_hash = re.search(r'Model hash:\s*([^,]+)', metadata_text)
        if match_hash:
            return f"Hash: {match_hash.group(1).strip()}"
        return "Unknown Model"

    def extract_generation_params(self, metadata_text):
        """その他メタデータの生テキストから、Steps/Sampler/Scheduler/CFG scale/Seed/Sizeを抽出する。
        生成ツールによって書式が微妙に異なるため、抽出できない項目は空文字のまま返す
        （その他メタデータ側には元の生テキストがそのまま残るため、情報が失われることはない）。"""
        params = {"Steps": "", "Sampler": "", "Scheduler": "", "CFG scale": "", "Seed": "", "Size": ""}
        if not metadata_text:
            return params
        
        patterns = {
            "Steps": r'Steps:\s*([^,]+)',
            "Sampler": r'Sampler:\s*([^,]+)',
            "Scheduler": r'Scheduler:\s*([^,]+)',
            "CFG scale": r'CFG scale:\s*([^,]+)',
            "Seed": r'Seed:\s*([^,]+)',
            "Size": r'Size:\s*([^,]+)',
        }
        for label, pattern in patterns.items():
            match = re.search(pattern, metadata_text)
            if match:
                params[label] = match.group(1).strip()
        return params

    def clear_generation_params_display(self):
        """生成パラメータ表示行の中身をすべて取り除き、非表示にする。"""
        while self.generation_params_layout.count():
            item = self.generation_params_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.generation_params_container.setVisible(False)

    def copy_seed_to_clipboard(self, value, btn):
        """Seedの値だけをクリップボードにコピーし、ボタンに完了フィードバックを表示する"""
        QApplication.clipboard().setText(value)
        btn.setIcon(QIcon())
        btn.setText("✓")
        btn.setObjectName("btn_copy_done")
        self._repolish(btn)
        QTimer.singleShot(1000, lambda: self.reset_copy_button(btn))

    def update_generation_params_display(self, metadata_text):
        """設定で表示がオンになっている生成パラメータだけを、使用モデル欄の下に1行で表示する。
        該当する項目が抽出できなかった/オフにされている場合は、その項目を省略する。
        Seedのみ、値の右横に小さなコピーボタンを表示する。"""
        params = self.extract_generation_params(metadata_text)

        field_settings = [
            ("Steps", "show_param_steps"),
            ("Sampler", "show_param_sampler"),
            ("Scheduler", "show_param_scheduler"),
            ("CFG scale", "show_param_cfg_scale"),
            ("Seed", "show_param_seed"),
            ("Size", "show_param_size"),
        ]

        self.clear_generation_params_display()

        has_parts = False
        for label, setting_key in field_settings:
            if database.get_setting(setting_key, "0") == "1" and params.get(label):
                if has_parts:
                    sep = QLabel("  |  ")
                    sep.setObjectName("lbl_generation_params")
                    self.generation_params_layout.addWidget(sep)

                value = params[label]
                lbl = QLabel(f"{label}: {value}")
                lbl.setObjectName("lbl_generation_params")
                self.generation_params_layout.addWidget(lbl)
                has_parts = True

                if label == "Seed":
                    btn_copy_seed = QPushButton()
                    btn_copy_seed.setIcon(render_svg_icon("content_copy", size=12))
                    btn_copy_seed.setIconSize(QSize(12, 12))
                    btn_copy_seed.setObjectName("btn_copy")
                    btn_copy_seed.setFixedSize(22, 20)
                    btn_copy_seed.setToolTip(self.tr("metadata.tooltip.copy_seed"))
                    btn_copy_seed.clicked.connect(
                        lambda checked=False, v=value, b=btn_copy_seed: self.copy_seed_to_clipboard(v, b)
                    )
                    self.generation_params_layout.addWidget(btn_copy_seed)

        if has_parts:
            self.generation_params_layout.addStretch(1)
            self.generation_params_container.setVisible(self.txt_model.isVisible())
        else:
            self.generation_params_container.setVisible(False)

    def open_folder_naming_rule_dialog(self, folder_name, folder_dir):
        """フォルダ見出しの右クリックメニューから、そのフォルダ専用の命名ルール上書きダイアログを開く。"""
        if not folder_dir:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.folder_path_unresolved"))
            return
        dialog = FolderNamingRuleDialog(self, folder_name, folder_dir)
        if dialog.exec() == QDialog.Accepted:
            self.show_status_message(f"フォルダ「{folder_name}」の命名ルールを保存しました", 5000)

    def open_folder_order_dialog(self):
        """現在データベースに存在するフォルダの一覧を取得し、並び替えダイアログを開く。
        設定画面のボタン、画像リストでフォルダの見出し行を右クリックした時のメニュー、
        両方から呼ばれる共通処理。"""
        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT file_path FROM images")
        rows = cursor.fetchall()
        conn.close()
        folder_names = sorted({os.path.basename(os.path.dirname(path)) for (path,) in rows})
        
        if not folder_names:
            show_notification(self, self.tr("common.title.no_folders"), self.tr("notify.no_images_in_db"))
            return
        
        dialog = FolderOrderDialog(self, folder_names)
        if dialog.exec() == QDialog.Accepted:
            if self.group_mode == "folder":
                selected_id = self.current_image_id
                self.load_images_from_db()
                self.filter_images()
                self.select_item_by_id(selected_id)

    def get_ordered_folder_names(self, folder_names):
        """フォルダ別グループ表示での並び順を返す。保存されている並び順（folder_group_order設定）を
        優先し、そこに含まれていない（新しく取り込まれた等の）フォルダは、末尾にアルファベット順で追加する。"""
        saved_order = database.get_folder_group_order()
        folder_set = set(folder_names)
        ordered = [f for f in saved_order if f in folder_set]
        saved_set = set(saved_order)
        remaining = sorted([f for f in folder_names if f not in saved_set], key=lambda s: s.lower())
        return ordered + remaining

    def _path_exists(self, path, recheck=False):
        """ファイルの実在をキャッシュ付きで判定する。
        recheck=True のとき、または未知のパスのときだけ実際に os.path.exists を呼び、
        それ以外は前回の結果を再利用する。外部ドライブ上の大量画像に対して
        並べ替え・グループ切替のたびに全件 os.path.exists する重さを避けるための仕組み。"""
        if recheck or path not in self._path_exists_cache:
            self._path_exists_cache[path] = os.path.exists(path)
        return self._path_exists_cache[path]

    def load_images_from_db(self, recheck_existence=None):
        """DBから画像を読み込み、リストを再構築する。
        recheck_existence: True=ファイル実在を実スキャンしてキャッシュ更新（起動時・同期時に使用）。
        None（既定）=キャッシュが空の初回だけ実スキャンし、以降の再読込（並べ替え・グループ切替など）は
        キャッシュを再利用する。未知パス（新規取り込み分）は都度チェックされる。"""
        if recheck_existence is None:
            recheck_existence = not self._path_exists_cache
        self.image_list.clear()
        
        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, file_path, file_name, prompt, negative_prompt, other_metadata, rating, file_mtime, updated_at, is_locked, imported_at, file_size, memo FROM images ORDER BY {self.sort_expr} {self.sort_dir}, file_name COLLATE NOCASE ASC")
        rows = cursor.fetchall()
        conn.close()
        
        icon_px = GRID_SIZE_PRESETS[self.grid_tile_size][0] if self.view_mode == "grid" else 60
        
        existing_rows = [row for row in rows if self._path_exists(row[1], recheck=recheck_existence)]
        missing_count = len(rows) - len(existing_rows)
        
        use_grouping = (self.group_mode == "folder" and self.view_mode == "list")
        
        if use_grouping:
            groups = {}
            group_order = []
            for row in existing_rows:
                parent_dir = os.path.basename(os.path.dirname(row[1]))
                if parent_dir not in groups:
                    groups[parent_dir] = []
                    group_order.append(parent_dir)
                groups[parent_dir].append(row)
            
            for folder_name in self.get_ordered_folder_names(group_order):
                folder_rows = groups[folder_name]
                folder_dir = os.path.dirname(folder_rows[0][1])
                self.image_list.addItem(self.build_folder_header_item(folder_name, len(folder_rows), folder_dir))
                is_collapsed = folder_name in self.collapsed_folders
                for row in folder_rows:
                    list_item = self.build_image_list_item(row, icon_px)
                    self.image_list.addItem(list_item)
                    if is_collapsed:
                        list_item.setHidden(True)
        else:
            for row in existing_rows:
                self.image_list.addItem(self.build_image_list_item(row, icon_px))
        
        self._current_image_count = len(existing_rows)
        self._library_folder_count = len({os.path.dirname(row[1]) for row in existing_rows})
        self.update_list_placeholder_visibility()
        self._update_missing_files_notice(missing_count)
        self._update_library_status()

    def _on_import_format_toggled(self, key, checked):
        """取り込み形式チェックボックスの状態を設定に保存する（再起動後も保持）。
        これは「取り込み専用」のフィルタで、表示中のリストの絞り込みには影響しない。"""
        database.set_setting(f"import_ext_{key}", "1" if checked else "0")

    def _get_selected_import_extensions(self):
        """チェックされている取り込み形式から、importer に渡す拡張子タプルを作る。
        1つも選ばれていない場合は None を返し、呼び出し側で「選択なし」として扱う。"""
        exts = []
        for _key, (chk, chk_exts) in self.import_format_checks.items():
            if chk.isChecked():
                exts.extend(chk_exts)
        return tuple(exts) if exts else None

    def _update_library_status(self):
        """リスト下部に、取り込み済みの「フォルダ数・画像数・最後に同期した日時」を表示する。
        同期日時は「同期」実行時のみ更新され、一度も同期していなければ「未同期」と表示する。"""
        folders = getattr(self, "_library_folder_count", 0)
        images = getattr(self, "_current_image_count", 0)
        last_sync = database.get_setting("last_sync_datetime", "") or self.tr("main.library_status.not_synced")
        self.lbl_library_status.setText(
            self.tr("main.library_status").format(folders=folders, images=images, last_sync=last_sync)
        )

    def show_status_message(self, text, duration=4000):
        """画面下部中央に一時メッセージを表示する（__init__で用意したstatus_message_label経由。
        中央寄せにすることで、QStatusBar標準の左寄せ表示より目に留まりやすくしている）。"""
        self.status_message_label.setText(text)
        self._status_message_timer.start(duration)

    def _update_missing_files_notice(self, missing_count):
        """ファイルが見つからず一覧から除外された画像の件数を、ステータスバーに控えめに案内する。
        外部ドライブ未接続などで画像が黙って消えると「消えた」と誤解されるため、
        件数を明示して原因（未接続の可能性）に気づけるようにする。0件のときは何も出さない。"""
        if missing_count > 0:
            self.show_status_message(
                f"{missing_count} 件の画像ファイルが見つからないため表示していません（外付けドライブ未接続の可能性があります）。",
                9000,
            )

    def update_list_placeholder_visibility(self):
        """画像が1件も登録されていない場合、リスト本体の代わりに案内メッセージを表示する。
        ドラッグ中はこの判定より優先してドラッグ中メッセージが表示される（on_drag_hover_changed側で制御）。
        判定には「実際にDBへ登録されている画像の総数」を使う（load_images_from_dbで更新）。
        画像行そのものの有無で判定すると、フォルダを折りたたんで画像行が0件になった際に、
        見出し行は存在するのに「空」と誤判定されてしまうため。"""
        has_items = getattr(self, "_current_image_count", 0) > 0
        if self.image_list_stack.currentWidget() is self.lbl_drag_hover:
            return
        if has_items:
            self.image_list_stack.setCurrentWidget(self.image_list)
        else:
            self.image_list_stack.setCurrentWidget(self.lbl_empty_state)

    def on_drag_hover_changed(self, is_hovering):
        """外部からのドラッグがリスト上に入った/出た時に、案内メッセージの表示を切り替える"""
        if is_hovering:
            self.image_list_stack.setCurrentWidget(self.lbl_drag_hover)
        else:
            self.update_list_placeholder_visibility()

    def build_folder_header_item(self, folder_name, count, folder_dir=None):
        """フォルダ別グループ表示の見出し行を作成する（選択不可）。
        絵文字ではなく、実際のフォルダアイコンをテキストの横に表示する。
        行全体をクリックすると、そのフォルダの画像一覧を折りたたみ/展開できる
        （setItemWidgetでボタンを埋め込む方式は、行幅の追従が不安定だったため採用しない）。
        folder_dir（実フォルダの絶対パス）は、この見出しをFinder等へドラッグ&ドロップした際に
        フォルダごとコピーするために保持しておく（ImageListWidgetのmousePress/mouseMoveで使用）。"""
        is_collapsed = folder_name in self.collapsed_folders
        indicator = "▶" if is_collapsed else "▼"
        item = QListWidgetItem("")
        item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        item.setToolTip(self.tr("main.folder_header.tooltip_collapsed") if is_collapsed else self.tr("main.folder_header.tooltip_expanded"))
        item.setData(Qt.UserRole + 8, folder_name)
        item.setData(Qt.UserRole + 12, count)
        item.setData(Qt.UserRole + 13, "")
        item.setData(Qt.UserRole + 14, indicator)
        item.setData(Qt.UserRole + 15, folder_dir)
        item.setFlags(Qt.ItemIsEnabled)
        c = self.theme_colors
        item.setBackground(QColor(c['group_header_bg']))
        item.setForeground(QColor(c['list_text']))
        return item

    def on_image_list_item_clicked(self, item):
        """画像リストの項目がクリックされた際、フォルダ見出し行であれば折りたたみ/展開を切り替える"""
        if item.data(Qt.UserRole) is None:
            folder_name = item.data(Qt.UserRole + 8)
            if folder_name:
                self.toggle_folder_collapsed(folder_name)

    def toggle_folder_collapsed(self, folder_name):
        """指定したフォルダの画像一覧の表示/非表示を切り替える（フォルダ別グループ表示中のみ意味を持つ）"""
        if folder_name in self.collapsed_folders:
            self.collapsed_folders.discard(folder_name)
        else:
            self.collapsed_folders.add(folder_name)
        database.set_collapsed_folders(self.collapsed_folders)
        
        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)

    def build_image_list_item(self, row, icon_px):
        """1件分の画像データからQListWidgetItemを組み立てる（通常表示・グループ表示共通）"""
        img_id, f_path, f_name, prompt, neg_prompt, others, rating, file_mtime, updated_at, is_locked, imported_at, file_size, memo = row
        parent_dir = os.path.basename(os.path.dirname(f_path))
        date_line = self.format_date_line(file_mtime, updated_at)
        detail_line = self.format_sort_detail_line(getattr(self, "sort_index", 0), file_mtime, updated_at, imported_at, file_size, date_line)
        
        stars = "★" * rating if rating > 0 else ""
        lock_prefix = "🔒 " if is_locked else ""
        star_prefix = f"{lock_prefix}[{stars}] " if stars else lock_prefix
        
        location_line = self.tr("main.list_item.location_line").format(parent_dir=parent_dir)
        if self.view_mode == "grid":
            if self.grid_tile_size == "large":
                display_text = f"{star_prefix}{f_name}\n{location_line}\n{detail_line}"
            else:
                display_text = f"{star_prefix}{f_name}"
        else:
            display_text = f"{star_prefix}{f_name}\n{location_line}\n{detail_line}"

        item = QListWidgetItem(display_text)
        lock_note = self.tr("main.list_item.locked_note") if is_locked else ""
        item.setToolTip(f"{lock_note}{f_name}\n{location_line}\n{date_line}")
        icon = self.get_cached_icon(f_path, icon_px)
        if icon is not None:
            item.setIcon(icon)
        
        item.setData(Qt.UserRole, img_id)
        item.setData(Qt.UserRole + 1, f_path)
        item.setData(Qt.UserRole + 2, f_name.lower())
        item.setData(Qt.UserRole + 3, (prompt if prompt else "").lower())
        item.setData(Qt.UserRole + 4, (others if others else "").lower())
        item.setData(Qt.UserRole + 5, f"star{rating}" if rating > 0 else "star0")
        item.setData(Qt.UserRole + 6, (neg_prompt if neg_prompt else "").lower())
        item.setData(Qt.UserRole + 7, bool(is_locked))
        item.setData(Qt.UserRole + 9, parent_dir)
        item.setData(Qt.UserRole + 10, os.path.basename(f_path).lower())
        rating_tokens = f"star{rating} {'★' * rating} {rating}" if rating > 0 else "star0"
        search_blob = " ".join([
            f_name or "",
            os.path.basename(f_path).lower(),
            f_path or "",
            parent_dir or "",
            prompt or "", neg_prompt or "", others or "",
            memo or "",
            rating_tokens,
            file_mtime or "", updated_at or "", imported_at or "",
            build_size_search_tokens(file_size),
        ])
        item.setData(Qt.UserRole + 11, normalize_search_text(search_blob))
        item.setData(Qt.UserRole + 15, file_mtime or "")
        item.setData(Qt.UserRole + 16, updated_at or "")
        item.setData(Qt.UserRole + 17, imported_at or "")
        item.setData(Qt.UserRole + 18, f_name or "")
        return item

    def format_date_line(self, file_mtime, updated_at):
        """「作成日時（編集日時）」の表示用テキストを組み立てる。
        file_mtime は実体としてはファイルの更新日時（mtime）だが、画面表示上は「作成:」として扱う。
        編集されていない（file_mtimeと編集日時が同じ）場合は編集日時を省略する。"""
        created_short = (file_mtime or "")[:16]  # "YYYY-MM-DD HH:MM"
        updated_short = (updated_at or "")[:16]
        
        if updated_short and updated_short != created_short:
            return f"作成: {created_short}（編集: {updated_short}）"
        return f"作成: {created_short}"

    def format_sort_detail_line(self, sort_index, file_mtime, updated_at, imported_at, file_size, date_line):
        """リスト各行の下段に出す補足情報を、現在の並べ替え種別に合わせて組み立てる。
        上段のファイル名は常時表示のまま、下段だけをソートキーの実値に切り替える。
          0=名前順 / 4=評価順 … 従来どおり作成(編集)日時（date_line）を流用
          1=作成日順 … 作成日時 / 2=編集日順 … 編集日時 / 3=取り込み日順 … 取り込み日時
          5=サイズ順 … 人間可読のファイルサイズ
        値が無い場合は「—」を表示する。"""
        if sort_index == 1:
            v = (file_mtime or "")[:16]
            return f"作成: {v}" if v else "作成: —"
        if sort_index == 2:
            v = (updated_at or "")[:16]
            return f"編集: {v}" if v else "編集: —"
        if sort_index == 3:
            v = (imported_at or "")[:16]
            return f"取り込み: {v}" if v else "取り込み: —"
        if sort_index == 5:
            return f"サイズ: {self._format_file_size(file_size)}"
        return date_line

    def _format_file_size(self, size):
        """バイト数を人間が読みやすい単位（B/KB/MB/GB）に整形する。値が無ければ「—」。"""
        if size is None:
            return "—"
        try:
            size = float(size)
        except (TypeError, ValueError):
            return "—"
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024

    def get_cached_icon(self, file_path, icon_px):
        """サムネイルアイコンをキャッシュから取得する。無い場合やファイル更新時のみ生成し直す。
        並び替え・表示切替・保存のたびに毎回ディスクから画像を読み直すのを避け、動作を軽くするための最適化。
        """
        try:
            mtime = os.path.getmtime(file_path)
        except OSError:
            return None
        
        cache_key = (file_path, mtime, icon_px)
        cached = self._thumbnail_cache.get(cache_key)
        if cached is not None:
            self._thumbnail_cache.move_to_end(cache_key)
            return cached
        
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return None
        
        icon_pixmap = pixmap.scaled(icon_px, icon_px, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon = QIcon(icon_pixmap)
        
        self._thumbnail_cache[cache_key] = icon
        self._thumbnail_cache.move_to_end(cache_key)
        while len(self._thumbnail_cache) > THUMBNAIL_CACHE_LIMIT:
            self._thumbnail_cache.popitem(last=False)
        
        return icon

    def _parse_search_query(self, raw):
        """検索文字列を解析して (period_filters, or_groups) を返す。

        - まず全角空白を半角へ、NFKC正規化＋小文字化して表記ゆれを吸収。
        - 期間トークン c:/m:/i: を取り出す（作成/編集/取り込み）。範囲は '..' 区切り、
          片側省略可、粒度は年/年月/年月日。例: c:2024-01-01..2024-03-31, m:2024, i:..2024-12
        - 残りの語は AND 結合。ただし 'OR'(大小問わず) で挟まれた語群は OR グループになる。
          先頭 '-' は除外（NOT）。'"..."' で囲むとスペースを含む語を1語として扱う。

        戻り値:
          period_filters: [(field, start, end), ...]  field は 'file_mtime'|'updated_at'|'imported_at'
          or_groups: [[term, ...], ...]  各内側リストはOR、外側同士はAND。
                     term は (is_negated: bool, text: str)
        """
        text = normalize_search_text(raw.replace("　", " "))
        quoted = []
        def _stash(m):
            quoted.append(m.group(1))
            return f"\x00{len(quoted)-1}\x00"
        text = re.sub(r'"([^"]+)"', _stash, text)

        period_map = {"c": "file_mtime", "m": "updated_at", "i": "imported_at"}
        period_filters = []
        tokens = []
        for tok in text.split():
            m = re.match(r'^(-?)([cmi]):(.*)$', tok)
            if m and m.group(3):
                key, val = m.group(2), m.group(3)
                start, end = self._parse_period_range(val)
                if start or end:
                    period_filters.append((period_map[key], start, end))
                    continue
            tokens.append(tok)

        or_groups = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok == "or" and or_groups:
                if i + 1 < len(tokens):
                    nxt = tokens[i + 1]
                    or_groups[-1].append(self._make_term(nxt, quoted))
                    i += 2
                    continue
                i += 1
                continue
            or_groups.append([self._make_term(tok, quoted)])
            i += 1
        return period_filters, or_groups

    def _make_term(self, tok, quoted):
        """1トークンを (is_negated, text) に変換。プレースホルダは元の引用語へ戻す。"""
        neg = False
        if tok.startswith("-") and len(tok) > 1:
            neg = True
            tok = tok[1:]
        m = re.fullmatch(r"\x00(\d+)\x00", tok)
        if m:
            tok = quoted[int(m.group(1))]
        return (neg, tok)

    def _parse_period_range(self, val):
        """'2024-01-01..2024-03-31' / '2024-01..' / '..2024' / '2024' を
        (start, end) の文字列（'YYYY-MM-DD HH:MM:SS' と比較できる前提の前方一致下限/上限）に変換する。
        粒度に応じて start は下限、end は上限へ丸める。"""
        def _norm(d, is_end):
            d = d.strip()
            if not d:
                return None
            parts = d.split("-")
            try:
                if len(parts) == 1:
                    y = int(parts[0])
                    return f"{y:04d}-01-01 00:00:00" if not is_end else f"{y:04d}-12-31 23:59:59"
                if len(parts) == 2:
                    y, mo = int(parts[0]), int(parts[1])
                    if not is_end:
                        return f"{y:04d}-{mo:02d}-01 00:00:00"
                    last = calendar.monthrange(y, mo)[1]
                    return f"{y:04d}-{mo:02d}-{last:02d} 23:59:59"
                y, mo, da = int(parts[0]), int(parts[1]), int(parts[2])
                return f"{y:04d}-{mo:02d}-{da:02d} " + ("00:00:00" if not is_end else "23:59:59")
            except (ValueError, IndexError):
                return None
        if ".." in val:
            a, b = val.split("..", 1)
            return _norm(a, False), _norm(b, True)
        return _norm(val, False), _norm(val, True)

    def _item_matches_query(self, item, period_filters, or_groups):
        """1つの画像アイテムが、解析済みクエリ（期間＋OR/AND/NOT）に一致するか。"""
        blob = item.data(Qt.UserRole + 11) or ""
        for field, start, end in period_filters:
            role = {"file_mtime": 15, "updated_at": 16, "imported_at": 17}[field]
            dt = item.data(Qt.UserRole + role) or ""
            if not dt:
                return False
            if start and dt < start:
                return False
            if end and dt > end:
                return False
        for group in or_groups:
            group_ok = False
            for (neg, word) in group:
                present = word in blob
                if neg:
                    if not present:
                        group_ok = True
                else:
                    if present:
                        group_ok = True
            if not group_ok:
                return False
        return True

    def filter_images(self):
        search_raw = self.txt_search.text().replace("　", " ").strip().lower()
        if not search_raw:
            self.image_list.set_empty_overlay("")
            self._all_collapsed_warning_shown = False
            for i in range(self.image_list.count()):
                item = self.image_list.item(i)
                if item.data(Qt.UserRole) is None:
                    self._refresh_folder_header_text(item, searching=False)
                    item.setHidden(False)
                    continue
                if self.group_mode == "folder" and item.data(Qt.UserRole + 9) in self.collapsed_folders:
                    continue
                item.setHidden(False)
            return
            
        period_filters, or_groups = self._parse_search_query(self.txt_search.text())
        visible_match_count = 0
        per_folder_match = {}
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            if item.data(Qt.UserRole) is None:
                continue
            
            match_all = self._item_matches_query(item, period_filters, or_groups)
            
            folder_of_item = item.data(Qt.UserRole + 9)
            is_folded_away = self.group_mode == "folder" and folder_of_item in self.collapsed_folders
            if match_all and not is_folded_away:
                item.setHidden(False)
                visible_match_count += 1
                if folder_of_item is not None:
                    per_folder_match[folder_of_item] = per_folder_match.get(folder_of_item, 0) + 1
            else:
                item.setHidden(True)
        
        header_count = 0
        collapsed_header_count = 0
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            if item.data(Qt.UserRole) is None:
                folder_name = item.data(Qt.UserRole + 8) or ""
                is_collapsed = self.group_mode == "folder" and folder_name in self.collapsed_folders
                header_count += 1
                if is_collapsed:
                    collapsed_header_count += 1
                self._refresh_folder_header_text(item, searching=True,
                                                 match_count=per_folder_match.get(folder_name, 0))
                item.setHidden(False)

        all_collapsed = (self.group_mode == "folder" and header_count > 0
                         and collapsed_header_count == header_count)
        if all_collapsed:
            self.image_list.set_empty_overlay("")
            if not self._all_collapsed_warning_shown:
                self._all_collapsed_warning_shown = True
                show_notification(self, self.tr("common.title.about_search"), self.tr("notify.search_all_collapsed"))
            return
        self._all_collapsed_warning_shown = False

        if visible_match_count == 0 and self.group_mode != "folder":
            self.image_list.set_empty_overlay("検索結果は 0 件です")
        else:
            self.image_list.set_empty_overlay("")

    def _refresh_folder_header_text(self, item, searching, match_count=None):
        """フォルダ見出し行の表示文言を、現在の折りたたみ状態・検索状態に合わせて再構成する。
        検索中は、そのフォルダの状態に応じて見出し下段の注記を出し分ける:
          ・折りたたみ中 … 「（折りたたみ中は検索対象外）」
          ・開いていて一致0件（match_count==0） … 「検索結果は 0 件です」
        match_count=None のとき（件数を渡さない呼び出し）は0件注記を付けない。"""
        folder_name = item.data(Qt.UserRole + 8) or ""
        is_collapsed = self.group_mode == "folder" and folder_name in self.collapsed_folders
        indicator = "▶" if is_collapsed else "▼"
        if searching and is_collapsed:
            note = "（折りたたみ中は検索対象外）"
        elif searching and match_count == 0:
            note = "検索結果は 0 件です"
        else:
            note = ""
        item.setData(Qt.UserRole + 13, note)
        item.setData(Qt.UserRole + 14, indicator)

    def show_image_context_menu(self, pos):
        """画像リストの右クリックメニュー：
        画像の行では Finder（等）で表示・ファイル/パスのコピー、
        フォルダの見出し行では「フォルダの並び順を編集」を表示する。
        フォルダ別グループ表示が有効な間は、どこを右クリックしても
        「すべてのフォルダを開く/折りたたむ」を利用できる。"""
        item = self.image_list.itemAt(pos)
        
        if item is None:
            if self.group_mode == "folder":
                menu = QMenu(self)
                menu.setStyleSheet(self.get_menu_stylesheet())
                self._add_folder_expand_collapse_actions(menu)
                menu.exec(self.image_list.viewport().mapToGlobal(pos))
            return
        
        if item.data(Qt.UserRole) is None:
            folder_name = item.data(Qt.UserRole + 8) or ""
            folder_dir = item.data(Qt.UserRole + 15)
            folder_count = item.data(Qt.UserRole + 12) or 0
            menu = QMenu(self)
            menu.setStyleSheet(self.get_menu_stylesheet())
            action_edit_order = menu.addAction(render_svg_icon("sort", size=16), self.tr("menu.folder_edit_order"))
            menu.addSeparator()
            self._add_folder_expand_collapse_actions(menu)
            menu.addSeparator()
            action_copy_renamed = menu.addAction(render_svg_icon("content_copy", size=16), self.tr("menu.folder_copy_renamed"))
            menu.addSeparator()
            action_naming_rule = menu.addAction(render_svg_icon("release_notes", size=16), self.tr("menu.folder_naming_rule"))
            menu.addSeparator()
            action_delete_folder = menu.addAction(render_svg_icon("delete", size=16), self.tr("menu.folder_delete"))
            chosen = menu.exec(self.image_list.viewport().mapToGlobal(pos))
            if chosen == action_edit_order:
                self.open_folder_order_dialog()
            elif chosen == action_naming_rule:
                self.open_folder_naming_rule_dialog(folder_name, folder_dir)
            elif chosen == action_copy_renamed:
                self.copy_folder_with_sequence_rename(folder_name, folder_dir)
            elif chosen == action_delete_folder:
                self.delete_folder_from_database(folder_name, folder_dir, folder_count)
            return
        
        if item not in self.image_list.selectedItems():
            self.image_list.setCurrentItem(item)
        
        selected_items = self.image_list.selectedItems()
        file_paths = [it.data(Qt.UserRole + 1) for it in selected_items]
        file_paths = [fp for fp in file_paths if fp and os.path.exists(fp)]
        if not file_paths:
            return
        
        system = platform.system()
        if system == "Darwin":
            reveal_label = self.tr("menu.reveal_finder")
        elif system == "Windows":
            reveal_label = self.tr("menu.reveal_explorer")
        else:
            reveal_label = self.tr("menu.reveal_file_manager")
        
        menu = QMenu(self)
        menu.setStyleSheet(self.get_menu_stylesheet())
        count_suffix = f"（{len(file_paths)} 件）" if len(file_paths) > 1 else ""
        action_reveal = menu.addAction(render_svg_icon("folder", size=16), f"{reveal_label}{count_suffix}")
        menu.addSeparator()

        anchor_locked = bool(item.data(Qt.UserRole + 7))
        if anchor_locked:
            action_lock_toggle = menu.addAction(render_svg_icon("unlock", size=16), f"{self.tr('menu.unlock_edit')}{count_suffix}")
        else:
            action_lock_toggle = menu.addAction(render_svg_icon("lock", size=16), f"{self.tr('menu.lock_edit')}{count_suffix}")

        if self.group_mode == "folder":
            menu.addSeparator()
            self._add_folder_expand_collapse_actions(menu)

        menu.addSeparator()
        action_copy_file = menu.addAction(render_svg_icon("content_copy", size=16), f"{self.tr('menu.copy_file')}{count_suffix}{self.tr('menu.copy_file_suffix')}")
        action_copy_path = menu.addAction(render_svg_icon("content_copy", size=16), self.tr("menu.copy_file_path"))

        action_bulk_rename = None
        menu.addSeparator()
        if len(selected_items) > 1:
            action_bulk_rename = menu.addAction(render_svg_icon("release_notes", size=16), f"{self.tr('menu.bulk_rename')}{count_suffix}")
        action_copy_renamed = menu.addAction(render_svg_icon("content_copy", size=16), f"{self.tr('menu.bulk_copy_renamed')}{count_suffix}")

        chosen = menu.exec(self.image_list.viewport().mapToGlobal(pos))

        if chosen == action_reveal:
            self.reveal_in_file_manager(file_paths)
        elif chosen == action_copy_file:
            self.copy_files_to_clipboard(file_paths)
            self.show_status_message(self.tr("status.files_copied").format(count=len(file_paths)), 5000)
        elif chosen == action_copy_path:
            QApplication.clipboard().setText("\n".join(file_paths))
            self.show_status_message(self.tr("status.file_path_copied"), 4000)
        elif chosen == action_copy_renamed:
            self.copy_files_with_sequence_rename(file_paths)
        elif action_bulk_rename is not None and chosen == action_bulk_rename:
            self.bulk_rename_selected(selected_items)
        elif chosen == action_lock_toggle:
            self.toggle_lock_selected(selected_items, not anchor_locked)

    def copy_folder_with_sequence_rename(self, folder_name, folder_dir):
        """フォルダ見出しの右クリックメニューから、そのフォルダ内でDBに登録されている画像を
        連番リネームしながら指定フォルダへコピーする（削除機能と同様、DB登録済みの画像のみを対象とし、
        フォルダ内に紛れた未登録ファイルは含めない）。"""
        if not folder_dir:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.folder_path_unresolved"))
            return
        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM images")
        rows = cursor.fetchall()
        conn.close()
        file_paths = [f_path for (f_path,) in rows if os.path.dirname(f_path) == folder_dir]
        self.copy_files_with_sequence_rename(file_paths, context_label=f"フォルダ「{folder_name}」: ")

    def delete_folder_from_database(self, folder_name, folder_dir, folder_count):
        """フォルダ見出しの右クリックメニューから、フォルダ（実フォルダ）と、その中の画像を
        まとめてデータベースから削除する。ディスク上の実ファイルは削除しない（DB登録の解除のみ）。
        削除後、このフォルダは同期（sync_folders）の対象からも外れる。同じフォルダを
        改めて「フォルダを取り込む」で取り込めば、再び同期対象に戻る。"""
        if not folder_dir:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.folder_path_unresolved"))
            return

        reply = show_confirm_dialog(
            self, self.tr("confirm.folder_delete.title"),
            self.tr("confirm.folder_delete.body").format(folder_name=folder_name, count=folder_count)
        )
        if reply != QMessageBox.Yes:
            return

        deleted_count = database.delete_folder_and_images(folder_dir)

        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)
        self.show_status_message(f"フォルダ「{folder_name}」と画像 {deleted_count} 件をデータベースから削除しました", 5000)

    def _add_folder_expand_collapse_actions(self, menu):
        """「すべてのフォルダを開く/折りたたむ」の2項目をメニューに追加する。
        フォルダ別グループ表示が有効な間、右クリックした場所を問わず共通で使う。"""
        action_expand_all = menu.addAction(render_svg_icon("all_folder_open", size=16), self.tr("menu.expand_all_folders"))
        action_collapse_all = menu.addAction(render_svg_icon("all_folder_close", size=16), self.tr("menu.collapse_all_folders"))
        action_expand_all.triggered.connect(self.expand_all_folders)
        action_collapse_all.triggered.connect(self.collapse_all_folders)

    def expand_all_folders(self):
        """フォルダ別グループ表示のすべてのフォルダを展開する（折りたたみ状態をすべて解除）。"""
        if not self.collapsed_folders:
            return
        self.collapsed_folders.clear()
        database.set_collapsed_folders(self.collapsed_folders)
        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)

    def collapse_all_folders(self):
        """フォルダ別グループ表示の、現在表示されているすべてのフォルダを折りたたむ。"""
        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM images")
        rows = cursor.fetchall()
        conn.close()
        all_folder_names = {os.path.basename(os.path.dirname(path)) for (path,) in rows if os.path.exists(path)}
        if not all_folder_names:
            return
        self.collapsed_folders = all_folder_names
        database.set_collapsed_folders(self.collapsed_folders)
        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)

    def _build_sequence_names(self, folder_dirs):
        """一括リネーム／連番コピーで共通利用する、連番ファイル名の一覧を作る。
        folder_dirs: 各対象ファイルの実フォルダの絶対パスを並べたリスト。
        フォルダ専用の自動採番（folder_naming_rules）が設定されていればそれを優先し、
        無ければアプリ全体の既定ルールを使う（2026-08-15〜。フォルダ専用ルールは、新規取り込みだけでなく
        既存画像の一括リネーム・一括で書き出すにも同じ優先順位で適用される）。
        {フォルダ名}プレースホルダーは各フォルダの実際のフォルダ名で解決する。
        解決後の (プレフィックス, アペンド) の組み合わせごとに1から独立して連番を振る
        （このカウンタは一時的なもので、取り込み時の永続カウンタには影響しない）。
        戻り値は folder_dirs と同じ並び順・同じ件数の新しいベース名（拡張子なし）のリスト。"""
        default_prefix = database.get_setting("sequence_prefix", "CG_")
        default_digits = int(database.get_setting("sequence_digits", "5"))
        default_append = database.get_setting("sequence_append", "")

        counters = {}
        new_names = []
        for folder_dir in folder_dirs:
            folder_name = os.path.basename(folder_dir) if folder_dir else ""
            rule = database.get_folder_naming_rule(folder_dir) if folder_dir else None
            if rule is not None:
                prefix_raw, digits, append_raw = rule["prefix"], rule["digits"], rule["append"]
            else:
                prefix_raw, digits, append_raw = default_prefix, default_digits, default_append

            prefix = database.resolve_naming_placeholders(prefix_raw, folder_name)
            append = database.resolve_naming_placeholders(append_raw, folder_name)
            key = (prefix, append)
            n = counters.get(key, 1)
            counters[key] = n + 1
            new_names.append(f"{prefix}{n:0{digits}d}{append}")
        return new_names

    def copy_files_with_sequence_rename(self, file_paths, context_label=""):
        """選択画像／フォルダ内の画像を、設定済みの自動採番ルールで連番リネームしつつ、
        指定したフォルダへ書き出す（元ファイルはそのまま・そのままの名前でコピーするだけの
        Finderドラッグ&ドロップとは違い、名前を採番形式に揃えたコピーを作りたい場合に使う）。"""
        file_paths = [fp for fp in file_paths if fp and os.path.exists(fp)]
        if not file_paths:
            show_notification(self, self.tr("common.title.copy"), self.tr("notify.copy_target_not_found"))
            return

        dest_dir = QFileDialog.getExistingDirectory(self, self.tr("dialog.choose_export_dest_title"), get_default_export_dir())
        if not dest_dir:
            return

        folder_dirs = [os.path.dirname(fp) for fp in file_paths]
        new_names = self._build_sequence_names(folder_dirs)

        if database.get_setting("rename_show_edit_dialog", "0") == "1":
            rows = [(os.path.basename(fp), name) for fp, name in zip(file_paths, new_names)]
            dialog = SequenceRenamePreviewDialog(
                self, self.tr("dialog.rename_table.title_export"), rows,
                column_labels=(self.tr("dialog.rename_table.column_current_filename"), self.tr("dialog.rename_table.column_new_filename")),
                hint_text=self.tr("dialog.rename_table.hint_filename")
            )
            if dialog.exec() != QDialog.Accepted:
                return
            new_names = dialog.get_new_names()

        copied_count = 0
        errors = []
        for f_path, new_base in zip(file_paths, new_names):
            ext = os.path.splitext(f_path)[1]
            new_path = os.path.join(dest_dir, new_base + ext)
            if os.path.exists(new_path):
                errors.append(self.tr("status.sequence_rename_export_error_item").format(name=os.path.basename(f_path), new_name=f"{new_base}{ext}"))
                continue
            try:
                shutil.copy2(f_path, new_path)
                copied_count += 1
            except OSError as e:
                errors.append(self.tr("status.sequence_rename_export_error_item_exc").format(name=os.path.basename(f_path), error=e))

        msg = self.tr("status.sequence_rename_export_done").format(context=context_label, count=copied_count)
        if errors:
            msg += self.tr("status.sequence_rename_export_errors_suffix").format(count=len(errors))
            self.status_message_label.setToolTip("\n".join(errors))
        else:
            self.status_message_label.setToolTip("")
        self.show_status_message(msg, 6000)

    def bulk_rename_selected(self, selected_items):
        """複数選択した画像を、設定済みの自動採番ルール（プレフィックス・桁数・アペンド）で
        一括してリネームする。対象は常に「名前」欄（DB上の表示名）のみで、
        パソコン上の実ファイル名は変更しない（2026-08-15〜。以前はディスク上の実ファイルも
        リネームしていたが、「DB内でのリネームは名前欄のみを対象とする」方針に変更した。
        実ファイル名も揃えたい場合は「一括で書き出す（連番でリネーム）」を使う）。

        - 番号は、この一括リネーム専用の一時的なカウンタで1から採番する（インポート時の
          永続カウンタ〈peek_next_sequence_number等〉には影響しない）
        - プレフィックス・アペンドに{フォルダ名}が含まれる場合、選択画像の実フォルダごとに
          解決した上で、フォルダ（＝解決後の組み合わせ）ごとに別々に1から採番する
          （フォルダ専用の自動採番が設定されていれば、そちらが優先される）
        - 編集ロック中の画像は対象外（他の一括操作と同じ挙動）
        - リスト表示中の並び順をそのまま採番順として使う"""
        selected_items = sorted(selected_items, key=lambda it: self.image_list.row(it))

        locked_items = [it for it in selected_items if bool(it.data(Qt.UserRole + 7))]
        target_items = [it for it in selected_items if not bool(it.data(Qt.UserRole + 7))]
        if not target_items:
            show_notification(self, self.tr("common.title.bulk_rename"), self.tr("notify.bulk_rename_all_locked"))
            return

        target_paths = [it.data(Qt.UserRole + 1) for it in target_items]
        current_names = [it.data(Qt.UserRole + 18) or "" for it in target_items]
        folder_dirs = [os.path.dirname(fp) for fp in target_paths]
        new_names = self._build_sequence_names(folder_dirs)

        if database.get_setting("rename_show_edit_dialog", "0") == "1":
            rows = list(zip(current_names, new_names))
            skip_note = self.tr("dialog.rename_table.locked_skip_note").format(count=len(locked_items)) if locked_items else ""
            dialog = SequenceRenamePreviewDialog(
                self, self.tr("dialog.rename_table.title_bulk"), rows, extra_note=skip_note,
                column_labels=(self.tr("dialog.rename_table.column_current_name"), self.tr("dialog.rename_table.column_new_name"))
            )
            if dialog.exec() != QDialog.Accepted:
                return
            new_names = dialog.get_new_names()
        else:
            preview = "、".join(new_names[:3])
            if len(new_names) > 3:
                preview += " ..."
            skip_note = self.tr("dialog.rename_table.locked_skip_note_newline").format(count=len(locked_items)) if locked_items else ""
            reply = show_confirm_dialog(
                self, self.tr("confirm.bulk_rename_selected.title"),
                self.tr("confirm.bulk_rename_selected.body").format(count=len(target_items), preview=preview, skip_note=skip_note)
            )
            if reply != QMessageBox.Yes:
                return

        plan = list(zip(target_items, new_names))  # (item, new_name)

        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        renamed_count = 0
        for it, new_base in plan:
            image_id = it.data(Qt.UserRole)
            cursor.execute(
                "UPDATE images SET file_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_base, image_id)
            )
            renamed_count += 1
        conn.commit()
        conn.close()

        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)

        self.show_status_message(self.tr("status.bulk_rename_done").format(count=renamed_count), 6000)

    def toggle_lock_selected(self, selected_items, locked):
        """選択中の画像のロック状態を一括で切り替える"""
        image_ids = [it.data(Qt.UserRole) for it in selected_items]
        database.set_locked(image_ids, locked)
        
        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)
        
        action_label = "ロックしました" if locked else "ロックを解除しました"
        self.show_status_message(f"{len(image_ids)} 件の画像を{action_label}", 4000)

    def reveal_in_file_manager(self, file_paths):
        """選択中の画像の保存場所をOS標準のファイルマネージャー（Finder等）で開く"""
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["open", "-R"] + file_paths)
            elif system == "Windows":
                for fp in file_paths:
                    subprocess.run(["explorer", f"/select,{fp}"])
            else:
                parent_dirs = {os.path.dirname(fp) for fp in file_paths}
                for d in parent_dirs:
                    subprocess.run(["xdg-open", d])
        except Exception as e:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.file_manager_open_failed").format(error=e))

    def copy_files_to_clipboard(self, file_paths):
        """選択中の画像ファイル自体をクリップボードにコピーする（Finder等に貼り付け可能）"""
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(fp) for fp in file_paths])
        QApplication.clipboard().setMimeData(mime)

    def resolve_import_order(self):
        """フォルダ取り込み時に使う順序と、重複画像を許可するかどうかを決定する。
        設定が「毎回確認」ならダイアログを表示して選ばせる（キャンセルされたらNoneを返す）。
        「自動選択」なら前回使用した設定をそのまま返す（ダイアログは表示しない）。
        戻り値は (順序, 重複を許可するか) のタプル、キャンセル時は None。
        """
        mode = database.get_setting("import_order_mode", "confirm")
        if mode == "auto":
            order = database.get_setting("last_import_order", "filename_asc")
            allow_duplicate_content = database.get_setting("allow_duplicate_content", "0") == "1"
            return order, allow_duplicate_content
        
        dialog = ImportOrderDialog(self)
        if dialog.exec() == QDialog.Accepted:
            database.set_setting("last_import_order", dialog.selected_order)
            database.set_setting("allow_duplicate_content", "1" if dialog.allow_duplicate_content else "0")
            return dialog.selected_order, dialog.allow_duplicate_content
        return None

    def open_folder_dialog(self):
        """フォルダ選択ダイアログを開き、選択されたフォルダ内の画像を取り込む（進捗ダイアログ表示付き）"""
        folder = QFileDialog.getExistingDirectory(self, "画像フォルダを選択", get_default_export_dir())
        if not folder:
            return
        
        result = self.resolve_import_order()
        if result is None:
            return
        import_order, allow_duplicate_content = result

        progress = QProgressDialog("画像をスキャン中...", "キャンセル", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("画像取り込みの進捗")
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.resize(450, 120)

        def update_progress(current, total, file_name):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(f"処理中 ({current} / {total} 件):\n{file_name}")
            QApplication.processEvents()

        result = importer.import_images_from_folder(
            folder,
            progress_callback=update_progress,
            cancel_check=progress.wasCanceled,
            skip_excluded=False,
            order=import_order,
            allow_duplicate_content=allow_duplicate_content,
            allowed_extensions=self._get_selected_import_extensions(),
        )
        progress.close()
        
        database.add_folder(folder)
        
        self.load_images_from_db()
        self.txt_search.clear()

        if result["total"] == 0:
            show_notification(self, self.tr("common.title.import_result"), result["error_log"])
            return
        
        summary = (
            f"新規登録: {result['inserted']} 件\n"
            f"重複によりスキップ: {result['duplicates']} 件\n"
            f"全体: {result['total']} 件"
        )
        if result["cancelled"]:
            show_notification(self, self.tr("common.title.import_cancelled"), self.tr("notify.body.cancelled_with_summary").format(summary=summary))
        elif result["error_log"]:
            show_notification(self, self.tr("common.title.partial_errors"), self.tr("notify.import_partial_errors_body").format(summary=summary, error_log=result["error_log"]))
        else:
            show_notification(self, self.tr("common.title.import_complete"), self.tr("notify.import_complete_body").format(summary=summary))

    def open_file_dialog(self):
        """ファイル選択ダイアログを開き、個別に選んだ画像ファイルを取り込む（フォルダ丸ごとではなく選んだ分のみ）"""
        selected_exts = self._get_selected_import_extensions()
        if selected_exts is None:
            show_notification(self, self.tr("common.title.no_import_format_selected"),
                              "取り込む画像形式が1つも選択されていません。\n"
                              "リスト下部の形式チェックボックス（PNG・JPG など）で、取り込みたい形式にチェックを入れてください。")
            return
        _filter = "画像ファイル (" + " ".join(f"*{e}" for e in selected_exts) + ")"
        files, _ = QFileDialog.getOpenFileNames(
            self, "取り込む画像ファイルを選択（複数選択可）", get_default_export_dir(),
            _filter
        )
        if not files:
            return

        progress = QProgressDialog("画像を取り込み中...", "キャンセル", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("画像取り込みの進捗")
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.resize(450, 120)

        def update_progress(current, total, file_name):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(f"処理中 ({current} / {total} 件):\n{file_name}")
            QApplication.processEvents()

        result = importer.import_images_from_filelist(
            files,
            progress_callback=update_progress,
            cancel_check=progress.wasCanceled,
            skip_excluded=False,
            allow_duplicate_content=database.get_setting("allow_duplicate_content", "0") == "1",
            allowed_extensions=self._get_selected_import_extensions(),
        )
        progress.close()
        
        
        self.load_images_from_db()
        self.txt_search.clear()

        if result["total"] == 0:
            show_notification(self, self.tr("common.title.import_result"), result["error_log"])
            return
        
        summary = (
            f"新規登録: {result['inserted']} 件\n"
            f"重複によりスキップ: {result['duplicates']} 件\n"
            f"全体: {result['total']} 件"
        )
        if result["cancelled"]:
            show_notification(self, self.tr("common.title.import_cancelled"), self.tr("notify.body.cancelled_with_summary").format(summary=summary))
        elif result["error_log"]:
            show_notification(self, self.tr("common.title.partial_errors"), self.tr("notify.import_partial_errors_body").format(summary=summary, error_log=result["error_log"]))
        else:
            show_notification(self, self.tr("common.title.import_complete"), self.tr("notify.import_complete_body").format(summary=summary))

    def handle_dropped_paths(self, paths):
        """画像リストへドラッグ&ドロップされた外部のファイル・フォルダを取り込む。
        フォルダはフォルダ単位で取り込み・同期対象として記憶し、個別ファイルはファイル単位で取り込む。"""
        folders = [p for p in paths if os.path.isdir(p)]
        files = [p for p in paths if os.path.isfile(p)]
        
        if not folders and not files:
            return
        
        import_order = "filename_asc"
        allow_duplicate_content = database.get_setting("allow_duplicate_content", "0") == "1"
        if folders:
            result = self.resolve_import_order()
            if result is None:
                return
            import_order, allow_duplicate_content = result
        
        progress = QProgressDialog("画像を取り込み中...", "キャンセル", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("画像取り込みの進捗")
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.resize(450, 120)
        
        def update_progress(current, total, file_name):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(f"処理中 ({current} / {total} 件):\n{file_name}")
            QApplication.processEvents()
        
        total_inserted = 0
        total_duplicates = 0
        total_scanned = 0
        error_logs = []
        was_cancelled = False
        
        for folder in folders:
            progress.setLabelText(f"フォルダをスキャン中:\n{folder}")
            result = importer.import_images_from_folder(
                folder,
                progress_callback=update_progress,
                cancel_check=progress.wasCanceled,
                skip_excluded=False,
                order=import_order,
                allow_duplicate_content=allow_duplicate_content,
                allowed_extensions=self._get_selected_import_extensions(),
            )
            database.add_folder(folder)
            total_inserted += result["inserted"]
            total_duplicates += result["duplicates"]
            total_scanned += result["total"]
            if result["error_log"]:
                error_logs.append(result["error_log"])
            if result["cancelled"]:
                was_cancelled = True
                break
        
        if files and not was_cancelled:
            result = importer.import_images_from_filelist(
                files,
                progress_callback=update_progress,
                cancel_check=progress.wasCanceled,
                skip_excluded=False,
                allow_duplicate_content=allow_duplicate_content,
                allowed_extensions=self._get_selected_import_extensions(),
            )
            total_inserted += result["inserted"]
            total_duplicates += result["duplicates"]
            total_scanned += result["total"]
            if result["error_log"]:
                error_logs.append(result["error_log"])
            if result["cancelled"]:
                was_cancelled = True
        
        progress.close()
        
        self.load_images_from_db()
        self.txt_search.clear()
        
        if total_scanned == 0:
            show_notification(self, self.tr("common.title.import_result"), self.tr("notify.no_supported_images_found"))
            return
        
        summary = (
            f"新規登録: {total_inserted} 件\n"
            f"重複によりスキップ: {total_duplicates} 件\n"
            f"全体: {total_scanned} 件"
        )
        if was_cancelled:
            show_notification(self, self.tr("common.title.import_cancelled"), self.tr("notify.body.cancelled_with_summary").format(summary=summary))
        elif error_logs:
            show_notification(self, self.tr("common.title.partial_errors"), self.tr("notify.import_partial_errors_body").format(summary=summary, error_log="\n".join(error_logs)))
        else:
            show_notification(self, self.tr("common.title.import_complete"), self.tr("notify.import_drag_drop_done_body").format(summary=summary))

    def open_settings_dialog(self):
        """歯車アイコンから設定ダイアログを開く"""
        dialog = SettingsDialog(self)
        dialog.exec()

    def open_help_dialog(self):
        """ヘルプアイコンからヘルプダイアログを開く（2026-08-09以降、メインウィンドウ側に配置）"""
        dialog = HelpDialog(self)
        dialog.exec()

    def sync_folders(self):
        """取り込み済みフォルダを再スキャンし、画像の増減をDBに反映する。

        フォルダが見つからない・取り込みエラーが起きた等の問題は、同じ問題が続く限り
        ポップアップでは初回のみ警告し、2回目以降は履歴（同期履歴ダイアログ、
        database.sync_history）にのみ記録する。一度でも解消（フォルダが見つかる／
        エラーが起きなくなる）すれば警告状態がリセットされ、再発時はまた警告される
        （2026-08-14〜、database.is_alert_warned / set_alert_warned で管理）。"""
        folders = database.get_all_folders()

        if not folders:
            show_notification(self, self.tr("common.title.sync"), self.tr("notify.sync_no_folders"))
            return

        valid_folders = [f for f in folders if os.path.isdir(f)]
        missing_folders = [f for f in folders if not os.path.isdir(f)]

        newly_missing_folders = []
        for folder in missing_folders:
            database.add_sync_history_entry(
                "folder_missing", folder,
                "同期対象フォルダが見つかりませんでした（移動または削除された可能性があります）"
            )
            if not database.is_alert_warned("folder_missing", folder):
                newly_missing_folders.append(folder)
                database.set_alert_warned("folder_missing", folder, True)
        for folder in valid_folders:
            if database.is_alert_warned("folder_missing", folder):
                database.set_alert_warned("folder_missing", folder, False)

        progress = QProgressDialog("フォルダを同期中...", "キャンセル", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("同期の進捗")
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.resize(450, 120)

        def update_progress(current, total, file_name):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(f"処理中 ({current} / {total} 件):\n{file_name}")
            QApplication.processEvents()

        total_scanned = 0
        total_inserted = 0
        total_duplicates = 0
        newly_reported_errors = []
        was_cancelled = False

        for folder in valid_folders:
            progress.setLabelText(f"フォルダをスキャン中:\n{folder}")
            result = importer.import_images_from_folder(
                folder,
                progress_callback=update_progress,
                cancel_check=progress.wasCanceled,
                skip_excluded=True,
                allow_duplicate_content=database.get_setting("allow_duplicate_content", "0") == "1",
                allowed_extensions=self._get_selected_import_extensions(),
            )
            total_scanned += result["total"]
            total_inserted += result["inserted"]
            total_duplicates += result["duplicates"]

            if result["error_log"]:
                database.add_sync_history_entry("import_error", folder, result["error_log"])
                if not database.is_alert_warned("import_error", folder):
                    newly_reported_errors.append(result["error_log"])
                    database.set_alert_warned("import_error", folder, True)
            else:
                if database.is_alert_warned("import_error", folder):
                    database.set_alert_warned("import_error", folder, False)

            if result["cancelled"]:
                was_cancelled = True
                break

        removed_paths = database.remove_missing_images()
        removed_count = len(removed_paths)
        for path in removed_paths:
            database.add_sync_history_entry("image_missing", path, "同期時にファイルが見つからなかったため、登録を削除しました")

        database.set_setting("last_sync_datetime", datetime.now().strftime("%Y-%m-%d %H:%M"))

        progress.close()

        self.load_images_from_db(recheck_existence=True)
        self.txt_search.clear()

        result_msg = (
            f"対象フォルダ: {len(valid_folders)} 件\n"
            f"新規追加: {total_inserted} 件\n"
            f"重複によりスキップ: {total_duplicates} 件（スキャン合計: {total_scanned} 件）\n"
            f"削除・移動を検出: {removed_count} 件"
        )
        if newly_missing_folders:
            result_msg += "\n\n⚠ 以下のフォルダが見つからなかったため、スキャンをスキップしました:\n" + "\n".join(newly_missing_folders)
            result_msg += "\n（このフォルダについては、見つかるようになるまで次回以降のポップアップ表示を省略します。詳細は「履歴」から確認できます）"

        if was_cancelled:
            show_sync_result_dialog(self, self.tr("common.title.sync_cancelled"), self.tr("notify.body.cancelled_with_summary").format(summary=result_msg))
        elif newly_reported_errors:
            result_msg += self.tr("sync.error_summary_suffix").format(error_log="\n".join(newly_reported_errors))
            show_sync_result_dialog(self, self.tr("common.title.sync_complete_partial_errors"), result_msg)
        else:
            show_sync_result_dialog(self, self.tr("common.title.sync_complete"), result_msg)

    def on_image_selected(self):
        selected_items = self.image_list.selectedItems()
        if not selected_items:
            return
            
        if len(selected_items) > 1:
            self.btn_delete.setText(self.tr("main.button.delete_selected_count").format(count=len(selected_items)))
            self.btn_save.setText(self.tr("main.button.save_selected_ratings").format(count=len(selected_items)))
            self.btn_save.setObjectName("btn_save_multi")
            self.btn_save.setIcon(render_svg_icon("save", size=16, color=SVG_ICON_COLOR_ON_ACCENT))
            self._repolish(self.btn_save)

            self.txt_filename.setEnabled(False)
            self.txt_filename.setText(self.tr("main.multi_select.filename_placeholder"))
            self.txt_display_name.setEnabled(False)
            self.txt_display_name.setText(self.tr("main.multi_select.name_placeholder"))
            self.txt_prompt.setEnabled(False)
            self.txt_neg_prompt.setEnabled(False)
            self.txt_metadata.setEnabled(False)
            self.txt_memo.setEnabled(False)
            self.txt_memo.setText("")
            self.btn_clear_model.setEnabled(False)
            self.btn_clear_prompt.setEnabled(False)
            self.btn_clear_neg_prompt.setEnabled(False)
            self.btn_clear_metadata.setEnabled(False)
            self.btn_clear_memo.setEnabled(False)
            self.clear_generation_params_display()
            
            item = selected_items[0]
            f_path = item.data(Qt.UserRole + 1)
            self.current_preview_path = f_path
            self.refresh_preview_pixmap()
            return

        self.txt_filename.setEnabled(True)
        self.txt_display_name.setEnabled(True)
        self.txt_prompt.setEnabled(True)
        self.txt_neg_prompt.setEnabled(True)
        self.txt_metadata.setEnabled(True)
        self.txt_memo.setEnabled(True)
        self.btn_clear_memo.setEnabled(True)

        self.btn_delete.setText(self.tr("main.button.delete_selected"))
        self.btn_save.setText(self.tr("metadata.button.save"))
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setIcon(render_svg_icon("save", size=16, color=SVG_ICON_COLOR))
        self._repolish(self.btn_save)
        
        item = selected_items[0]
        img_id = item.data(Qt.UserRole)
        f_path = item.data(Qt.UserRole + 1)
        is_locked = bool(item.data(Qt.UserRole + 7))
        
        self.current_image_id = img_id
        
        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT file_name, prompt, negative_prompt, other_metadata, rating, memo FROM images WHERE id = ?", (img_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            f_name, prompt, neg_prompt, others, rating, memo = row
            self.txt_filename.setText(os.path.basename(f_path))
            self.txt_display_name.setText(f_name)
            self.star_rating.set_rating(rating if rating <= 5 else 0)
            self.txt_prompt.setPlainText(prompt if prompt else "")
            self.txt_neg_prompt.setPlainText(neg_prompt if neg_prompt else "")
            self.txt_metadata.setPlainText(others if others else "")
            self.txt_memo.setText(memo if memo else "")
            self.txt_model.setPlainText(self.extract_model_name(others))
            self.update_generation_params_display(others)
            QTimer.singleShot(0, self.autosize_all_metadata_fields)
        
        self.txt_filename.setEnabled(not is_locked)
        self.txt_display_name.setEnabled(not is_locked)
        self.star_rating.setEnabled(not is_locked)
        self.txt_prompt.setEnabled(not is_locked)
        self.txt_neg_prompt.setEnabled(not is_locked)
        self.txt_metadata.setEnabled(not is_locked)
        self.txt_memo.setEnabled(not is_locked)
        self.btn_clear_model.setEnabled(not is_locked)
        self.btn_clear_prompt.setEnabled(not is_locked)
        self.btn_clear_neg_prompt.setEnabled(not is_locked)
        self.btn_clear_metadata.setEnabled(not is_locked)
        self.btn_clear_memo.setEnabled(not is_locked)
        self.btn_save.setEnabled(not is_locked)
        self.btn_save.setToolTip(self.tr("metadata.tooltip.save_locked") if is_locked else "")
            
        self.current_preview_path = f_path
        self.refresh_preview_pixmap()

    def _flash_save_button(self):
        """「変更を保存」ボタンを押した直後、一瞬「✓ 保存しました」表示に切り替えて、
        保存されたことが視覚的に分かりやすいようにする（ステータスバーのメッセージと
        合わせて手応えを補強するための演出）。単一選択／複数選択どちらの表示状態からでも、
        一定時間後に元のラベル・アイコンへ自動的に戻す。"""
        is_multi = self.btn_save.objectName() == "btn_save_multi"
        original_text = self.btn_save.text()
        icon_color = SVG_ICON_COLOR_ON_ACCENT if is_multi else SVG_ICON_COLOR

        self.btn_save.setFixedWidth(self.btn_save.width())

        self.btn_save.setText(" 保存しました")
        self.btn_save.setIcon(render_svg_icon("check", size=16, color=icon_color))
        self._repolish(self.btn_save)

        def _restore():
            if is_multi:
                self.btn_save.setIcon(render_svg_icon("save", size=16, color=SVG_ICON_COLOR_ON_ACCENT))
            else:
                self.btn_save.setIcon(render_svg_icon("save", size=16, color=SVG_ICON_COLOR))
            self.btn_save.setText(original_text)
            self._repolish(self.btn_save)
            self.btn_save.setMinimumWidth(0)
            self.btn_save.setMaximumWidth(16777215)

        QTimer.singleShot(1200, _restore)

    def save_metadata_changes(self):
        selected_items = self.image_list.selectedItems()
        if not selected_items:
            return
            
        rating = self.star_rating.rating
        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        
        if len(selected_items) > 1:
            image_ids = [item.data(Qt.UserRole) for item in selected_items]
            locked_ids = database.get_locked_ids(image_ids)
            
            for item in selected_items:
                img_id = item.data(Qt.UserRole)
                if img_id in locked_ids:
                    continue
                cursor.execute("UPDATE images SET rating = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (rating, img_id))
            conn.commit()
            conn.close()
            
            selected_indices = [self.image_list.row(item) for item in selected_items]
            self.load_images_from_db()
            for idx in selected_indices:
                if idx < self.image_list.count():
                    self.image_list.item(idx).setSelected(True)
            
            if locked_ids:
                self.show_status_message(self.tr("status.rating_saved_with_locked_skipped").format(count=len(locked_ids)), 5000)
            else:
                self.show_status_message(self.tr("status.rating_saved"), 4000)
            self._flash_save_button()
            return

        if self.current_image_id is None:
            conn.close()
            return
        
        if database.get_locked_ids([self.current_image_id]):
            conn.close()
            show_notification(self, self.tr("common.title.locked"), self.tr("notify.save_locked_body"))
            return
            
        new_name = self.txt_display_name.text().strip()
        new_filename = self.txt_filename.text().strip()
        prompt = self.txt_prompt.toPlainText()
        neg_prompt = self.txt_neg_prompt.toPlainText()
        others = self.txt_metadata.toPlainText()
        memo = self.txt_memo.text()

        if not new_name:
            show_notification(self, self.tr("common.title.warning"), self.tr("notify.name_empty_warning"))
            conn.close()
            return
        if not new_filename:
            show_notification(self, self.tr("common.title.warning"), self.tr("notify.filename_empty_warning"))
            conn.close()
            return
        
        cursor.execute("SELECT file_path FROM images WHERE id = ?", (self.current_image_id,))
        row = cursor.fetchone()
        current_path = row[0] if row else None
        
        if current_path and os.path.basename(current_path) != new_filename:
            if not os.path.exists(current_path):
                show_notification(self, self.tr("common.title.error"), self.tr("notify.original_file_missing"))
                conn.close()
                return
            
            old_dir = os.path.dirname(current_path)
            old_ext = os.path.splitext(current_path)[1]
            if not os.path.splitext(new_filename)[1]:
                new_filename += old_ext
            new_path = os.path.join(old_dir, new_filename)
            
            if os.path.exists(new_path):
                show_notification(self, self.tr("common.title.warning"), self.tr("notify.filename_conflict").format(new_filename=new_filename))
                conn.close()
                return
            
            try:
                os.rename(current_path, new_path)
            except Exception as e:
                show_notification(self, self.tr("common.title.error"), self.tr("notify.rename_failed").format(error=e))
                conn.close()
                return
            
            cursor.execute("UPDATE images SET file_path = ? WHERE id = ?", (new_path, self.current_image_id))
            
        cursor.execute("""
            UPDATE images
            SET file_name = ?, rating = ?, prompt = ?, negative_prompt = ?, other_metadata = ?, memo = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_name, rating, prompt, neg_prompt, others, memo, self.current_image_id))
        conn.commit()
        conn.close()
        
        current_row = self.image_list.currentRow()
        self.load_images_from_db()
        self.image_list.setCurrentRow(current_row)

        self.show_status_message(self.tr("status.changes_saved"), 4000)
        self._flash_save_button()

    def delete_image_from_db(self):
        selected_items = self.image_list.selectedItems()
        if not selected_items:
            return

        locked_items = [item for item in selected_items if bool(item.data(Qt.UserRole + 7))]
        if locked_items:
            show_notification(
                self, self.tr("common.title.locked"),
                self.tr("confirm.delete_locked_blocked.body").format(count=len(locked_items))
            )
            return
            
        count = len(selected_items)
        reply = show_confirm_dialog(
            self, self.tr("confirm.delete_images.title"),
            self.tr("confirm.delete_images.body").format(count=count)
        )
        
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect(database.get_current_db_path())
            cursor = conn.cursor()
            for item in selected_items:
                img_id = item.data(Qt.UserRole)
                f_path = item.data(Qt.UserRole + 1)
                cursor.execute("DELETE FROM images WHERE id = ?", (img_id,))
                if f_path:
                    cursor.execute("INSERT OR IGNORE INTO excluded_paths (file_path) VALUES (?)", (f_path,))
            conn.commit()
            conn.close()
            
            self.load_images_from_db()
            self.lbl_preview.setText(self.tr("metadata.preview.select_prompt"))
            self.txt_model.clear()
            self.clear_generation_params_display()
            self.txt_prompt.clear()
            self.txt_neg_prompt.clear()
            self.txt_metadata.clear()
            self.txt_filename.clear()
            self.txt_display_name.clear()
            self.star_rating.set_rating(0)
            self.current_image_id = None
            self.btn_delete.setText(self.tr("main.button.delete_selected"))
            self.btn_save.setText(self.tr("metadata.button.save"))
            self.btn_save.setObjectName("btn_save")
            self.btn_save.setIcon(render_svg_icon("save", size=16, color=SVG_ICON_COLOR))
            self._repolish(self.btn_save)
            self.txt_search.clear()

    def show_speed_menu(self):
        """再生速度（0.5倍〜2倍、0.25刻み）を選択するメニューを表示する"""
        menu = QMenu(self)
        menu.setStyleSheet(self.get_menu_stylesheet())
        actions = {}
        for speed in self.slideshow_speeds:
            label = f"{speed}x" + ("（基準）" if speed == 1.0 else "")
            action = menu.addAction(f"{'✓ ' if speed == self.slideshow_speed else ''}{label}")
            actions[action] = speed
        
        chosen = menu.exec(self.btn_speed.mapToGlobal(self.btn_speed.rect().bottomLeft()))
        if chosen is not None and chosen in actions:
            self.slideshow_speed = actions[chosen]
            self.btn_speed.setText(f"{self.slideshow_speed}x")
            if self.timer.isActive():
                self.timer.setInterval(int(self.slideshow_base_interval_sec * 1000 / self.slideshow_speed))

    def save_as_new_copy(self):
        """オリジナルのファイル・DBレコードは変更せず、現在編集中の内容（表示名・評価・
        プロンプト等）を持つ新しいコピーとして、ユーザーが指定した場所に画像を保存する。"""
        if self.current_image_id is None:
            show_notification(self, self.tr("common.title.please_select"), self.tr("notify.select_image_warning"))
            return
        
        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM images WHERE id = ?", (self.current_image_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row or not os.path.exists(row[0]):
            show_notification(self, self.tr("common.title.error"), self.tr("notify.original_image_missing"))
            return
        original_path = row[0]
        
        new_name = self.txt_display_name.text().strip()
        if not new_name:
            show_notification(self, self.tr("common.title.warning"), self.tr("notify.display_name_empty_warning"))
            return
        
        ext = os.path.splitext(original_path)[1]
        suggested_name = new_name if new_name.lower().endswith(ext.lower()) else new_name + ext
        suggested_path = os.path.join(get_default_export_dir(), suggested_name)
        dest_path, _ = QFileDialog.getSaveFileName(self, "新しい場所に画像のコピーを保存", suggested_path, f"Image Files (*{ext})")
        if not dest_path:
            return
        
        try:
            shutil.copy2(original_path, dest_path)
        except Exception as e:
            show_notification(self, self.tr("common.title.error"), self.tr("notify.file_copy_failed").format(error=e))
            return
        
        try:
            dest_file_size = os.path.getsize(dest_path)
        except OSError:
            dest_file_size = None
        
        rating = self.star_rating.rating
        prompt = self.txt_prompt.toPlainText()
        neg_prompt = self.txt_neg_prompt.toPlainText()
        others = self.txt_metadata.toPlainText()
        memo = self.txt_memo.text()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO images (file_path, file_name, prompt, negative_prompt, other_metadata, memo, rating, file_mtime, updated_at, file_hash, imported_at, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
            """, (dest_path, new_name, prompt, neg_prompt, others, memo, rating, now_str, now_str, now_str, dest_file_size))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            show_notification(self, self.tr("common.title.warning"), self.tr("notify.duplicate_path_warning"))
            return
        conn.close()
        
        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)
        
        show_notification(self, self.tr("common.title.save_complete"), self.tr("notify.save_as_new_done").format(dest_path=dest_path))

    def toggle_slideshow(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_slideshow.setText("▶  スライドショー開始")
            self.btn_slideshow.setObjectName("btn_slideshow_idle")
            self._repolish(self.btn_slideshow)
        else:
            if not self.image_list.selectedItems() and self.image_list.count() > 0:
                self.image_list.setCurrentRow(0)
            self.timer.setInterval(int(self.slideshow_base_interval_sec * 1000 / self.slideshow_speed))
            self.timer.start()
            self.btn_slideshow.setText("■  スライドショー停止")
            self.btn_slideshow.setObjectName("btn_slideshow_active")
            self._repolish(self.btn_slideshow)

    def select_item_by_id(self, img_id):
        """並び替え/表示切替の後に、選択されていた画像を再選択する"""
        if img_id is None:
            return
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            if item.data(Qt.UserRole) == img_id:
                self.image_list.setCurrentItem(item)
                break

    def on_sort_changed(self, index):
        """並び替えの種類（名前・作成日・編集日・取り込み日時・評価・ファイルサイズ）を切り替える。
        昇順/降順は cmb_sort とは独立して btn_sort_direction ボタンで切り替える。"""
        sort_expr_map = {
            0: "file_name COLLATE NOCASE",
            1: "file_mtime",
            2: "COALESCE(updated_at, file_mtime)",
            3: "COALESCE(imported_at, file_mtime)",
            4: "rating",
            5: "COALESCE(file_size, 0)",
        }
        self.sort_expr = sort_expr_map[index]
        self.sort_index = index
        database.set_setting("last_sort_index", str(index))
        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)

    def toggle_sort_direction(self):
        """並び替えの昇順/降順を切り替える"""
        self.sort_dir = "DESC" if self.sort_dir == "ASC" else "ASC"
        database.set_setting("last_sort_dir", self.sort_dir)
        if self.sort_dir == "ASC":
            self.btn_sort_direction.setIcon(render_svg_icon("arrow_upward", size=18))
            self.btn_sort_direction.setIconSize(QSize(18, 18))
            self.btn_sort_direction.setToolTip(self.tr("main.tooltip.sort_direction_asc"))
        else:
            self.btn_sort_direction.setIcon(render_svg_icon("arrow_downward", size=18))
            self.btn_sort_direction.setIconSize(QSize(18, 18))
            self.btn_sort_direction.setToolTip(self.tr("main.tooltip.sort_direction_desc"))
        
        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)

    def toggle_view_mode(self):
        """グリッド表示とリスト表示を切り替える（アイコンのみのボタン）"""
        selected_id = self.current_image_id
        
        if self.view_mode == "list":
            self.view_mode = "grid"
            self.image_list.setViewMode(QListWidget.IconMode)
            self.image_list.setFlow(QListWidget.LeftToRight)
            self.image_list.setResizeMode(QListWidget.Adjust)
            self.image_list.setMovement(QListWidget.Static)
            self.apply_grid_tile_size()
            self.image_list.setSpacing(SPACING_SM)
            self.btn_view_toggle.setIcon(render_svg_icon("view_list", size=16))
            self.btn_view_toggle.setIconSize(QSize(16, 16))
            self.btn_view_toggle.setToolTip(self.tr("main.tooltip.view_toggle_to_list"))
            self.grid_size_widget.setVisible(True)
            self.btn_group_toggle.setEnabled(False)
            self.btn_group_toggle.setToolTip(self.tr("main.tooltip.group_toggle_disabled_grid"))
        else:
            self.view_mode = "list"
            self.image_list.setViewMode(QListWidget.ListMode)
            self.image_list.setFlow(QListWidget.TopToBottom)
            self.image_list.setResizeMode(QListWidget.Adjust)
            self.image_list.setMovement(QListWidget.Static)
            self.image_list.setIconSize(QSize(60, 60))
            self.image_list.setGridSize(QSize())
            self.image_list.setSpacing(SPACING_XS)
            self.btn_view_toggle.setIcon(render_svg_icon("grid_view", size=16))
            self.btn_view_toggle.setIconSize(QSize(16, 16))
            self.btn_view_toggle.setToolTip(self.tr("main.tooltip.view_toggle_to_grid"))
            self.grid_size_widget.setVisible(False)
            self.btn_group_toggle.setEnabled(True)
            self.btn_group_toggle.setToolTip(self.tr("main.tooltip.group_toggle_enable") if self.group_mode == "none" else self.tr("main.tooltip.group_toggle_disable"))
        
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)

    def toggle_group_mode(self):
        """フォルダ別グループ表示のオン/オフを切り替える（リスト表示中のみ有効）"""
        self.group_mode = "none" if self.group_mode == "folder" else "folder"
        database.set_setting("last_group_mode", self.group_mode)
        
        if self.group_mode == "folder":
            self.btn_group_toggle.setObjectName("btn_group_toggle_active")
            self.btn_group_toggle.setToolTip(self.tr("main.tooltip.group_toggle_disable"))
            self.btn_group_toggle.setIcon(render_svg_icon("group_by_folder", size=18, color=SVG_ICON_COLOR_ON_ACCENT))
        else:
            self.btn_group_toggle.setObjectName("btn_view_toggle")
            self.btn_group_toggle.setToolTip(self.tr("main.tooltip.group_toggle_enable"))
            self.btn_group_toggle.setIcon(render_svg_icon("group_by_folder", size=18, color=SVG_ICON_COLOR))
        self._repolish(self.btn_group_toggle)
        self.btn_reading_mode.setEnabled(self.group_mode == "folder")
        
        if self.group_mode == "folder":
            self.btn_view_toggle.setEnabled(False)
            self.btn_view_toggle.setToolTip(self.tr("main.tooltip.view_toggle_disabled_grouped"))
        else:
            self.btn_view_toggle.setEnabled(True)
            self.btn_view_toggle.setToolTip(self.tr("main.tooltip.view_toggle_to_grid"))
        
        selected_id = self.current_image_id
        self.load_images_from_db()
        self.filter_images()
        self.select_item_by_id(selected_id)

    def apply_grid_tile_size(self):
        """現在選択中のサムネイルサイズ（小/中/大）をグリッド表示に適用する"""
        icon_px, tile_w, tile_h = GRID_SIZE_PRESETS[self.grid_tile_size]
        self.image_list.setIconSize(QSize(icon_px, icon_px))
        self.image_list.setGridSize(QSize(tile_w, tile_h))

    def set_grid_tile_size(self, size_name):
        """サムネイルサイズ（小/中/大）を切り替える"""
        self.grid_tile_size = size_name
        
        grid_icon_names = {"small": "grid_small", "medium": "grid_medium", "large": "grid_large"}
        for name, btn in self.grid_size_buttons.items():
            is_active = (name == size_name)
            btn.setObjectName("btn_preview_size_active" if is_active else "btn_preview_size")
            icon_color = SVG_ICON_COLOR_ON_ACCENT if is_active else SVG_ICON_COLOR
            btn.setIcon(render_svg_icon(grid_icon_names[name], size=14, color=icon_color))
            self._repolish(btn)
        
        if self.view_mode == "grid":
            self.apply_grid_tile_size()
            selected_id = self.current_image_id
            self.load_images_from_db()
            self.filter_images()
            self.select_item_by_id(selected_id)

    def apply_panel_layout(self, mode):
        """左右パネルの配置を切り替える。「standard」＝リスト等を左・プレビュー等を右（既定）、
        「mirrored」＝左右反転（プレビュー等を左・リスト等を右）。設定ボタン（btn_settings）は
        splitterの外（main_layout直下の上部バー）にあるため、この切替の影響を受けず、
        常にウィンドウ右上に固定表示される。
        QSplitterは既に追加済みのウィジェットに対してinsertWidget(0, ...)を呼ぶと、
        そのウィジェットを再度先頭へ移動してくれるため、再構築なしで即座に反映できる。"""
        self.panel_layout_mode = mode
        margin = SPACING_XXL
        if mode == "mirrored":
            self.right_container_layout.setContentsMargins(0, 0, margin, 0)
            self.splitter.insertWidget(0, self.right_container)
            self.splitter.setSizes([780, 420])
        else:
            self.right_container_layout.setContentsMargins(margin, 0, 0, 0)
            self.splitter.insertWidget(0, self.left_widget)
            self.splitter.setSizes([420, 780])
        self._update_panel_flip_icon()

    def toggle_panel_layout(self):
        """上部バーのパネル反転ボタン用。standard⇄mirroredをワンクリックで切り替える
        （設定画面のラジオボタンと同じ設定項目・同じ即時反映処理を共有する）。"""
        current_mode = database.get_setting("panel_layout", "standard")
        new_mode = "mirrored" if current_mode == "standard" else "standard"
        database.set_setting("panel_layout", new_mode)
        self.apply_panel_layout(new_mode)

    def _update_panel_flip_icon(self):
        """パネル反転ボタンのアイコン・ツールチップを、現在のパネル配置に合わせて更新する。
        standard（プレビュー等が右側）→ dock_to_right、mirrored（プレビュー等が左側）→ dock_to_left。
        つまりアイコンは「今どちら側に主要パネルが寄っているか」を表す。"""
        btn = getattr(self, "btn_panel_flip", None)
        if btn is None:
            return
        mode = database.get_setting("panel_layout", "standard")
        if mode == "mirrored":
            btn.setIcon(render_svg_icon("dock_to_left", size=18))
            btn.setToolTip(self.tr("main.tooltip.panel_flip_mirrored"))
        else:
            btn.setIcon(render_svg_icon("dock_to_right", size=18))
            btn.setToolTip(self.tr("main.tooltip.panel_flip_standard"))

    def refresh_preview_pixmap(self):
        """self.current_preview_path の画像を、現在の表示サイズに合わせて再描画する。
        通常表示・コンパクト表示ではlbl_previewのウィジェットサイズを、
        全画面表示ではモニター（実際に表示されている画面）のサイズを直接使うことで、
        オリジナル画像の解像度のまま小さく表示されてしまうのを防ぐ。"""
        f_path = getattr(self, "current_preview_path", None)
        if not f_path or not os.path.exists(f_path):
            return
        pixmap = QPixmap(f_path)
        if pixmap.isNull():
            self.lbl_preview.setText("画像の読み込みに失敗しました")
            return
        
        fullscreen_window = getattr(self, "fullscreen_window", None)
        if fullscreen_window is not None:
            screen = fullscreen_window.screen() or QGuiApplication.primaryScreen()
            avail = screen.availableGeometry()
            target_size = QSize(max(avail.width() - 40, 100), max(avail.height() - 100, 100))
        else:
            target_size = self.lbl_preview.size()
            if target_size.width() < 10 or target_size.height() < 10:
                return
        
        scaled_pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_preview.setPixmap(scaled_pixmap)

    def set_preview_size_mode(self, mode):
        """プレビューの表示サイズを「非表示」「標準」「コンパクト」に切り替える（全画面表示は別メソッド）"""
        self.preview_size_mode = mode

        is_hidden = (mode == "hidden")
        self.lbl_preview.setVisible(not is_hidden)
        self.btn_prev_image.setVisible(not is_hidden)
        self.btn_next_image.setVisible(not is_hidden)

        if is_hidden:
            self.right_layout.setStretch(self.preview_layout_stretch_index, 0)
        elif mode == "compact":
            self.lbl_preview.setMinimumSize(250, 295)
            self.lbl_preview.setMaximumSize(250, 295)
            self.right_layout.setStretch(self.preview_layout_stretch_index, 0)
        else:
            self.lbl_preview.setMinimumSize(360, 420)
            self.lbl_preview.setMaximumSize(16777215, 16777215)
            self.right_layout.setStretch(self.preview_layout_stretch_index, 20)

        preview_size_icon_names = {
            self.btn_preview_hidden: "preview_hidden",
            self.btn_preview_standard: "preview_standard",
            self.btn_preview_compact: "preview_compact",
        }
        for btn in self.preview_size_buttons:
            is_active = (btn is self.btn_preview_hidden and mode == "hidden") or \
                        (btn is self.btn_preview_standard and mode == "standard") or \
                        (btn is self.btn_preview_compact and mode == "compact")
            btn.setObjectName("btn_preview_size_active" if is_active else "btn_preview_size")
            icon_color = SVG_ICON_COLOR_ON_ACCENT if is_active else SVG_ICON_COLOR
            btn.setIcon(render_svg_icon(preview_size_icon_names[btn], size=14, color=icon_color))
            self._repolish(btn)

        if not is_hidden:
            QTimer.singleShot(0, self.refresh_preview_pixmap)

    def open_reading_mode(self):
        """読書モード（見開き表示）を開始する。現在選択中の画像と同じフォルダ内の画像を、
        名前順に並べて全画面の見開き表示にする。「フォルダ別グループ表示」が有効な時のみ利用できる
        （ボタン自体もその条件でのみ有効化される）。"""
        if self.group_mode != "folder" or self.current_image_id is None:
            return
        
        conn = sqlite3.connect(database.get_current_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM images WHERE id = ?", (self.current_image_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        current_path = row[0]
        target_folder = os.path.dirname(current_path)
        
        cursor.execute("SELECT id, file_path FROM images ORDER BY file_name COLLATE NOCASE ASC")
        all_rows = cursor.fetchall()
        conn.close()
        
        folder_rows = [(img_id, path) for img_id, path in all_rows if os.path.dirname(path) == target_folder]
        if not folder_rows:
            return
        
        start_index = next((i for i, (img_id, _) in enumerate(folder_rows) if img_id == self.current_image_id), 0)
        
        self.reading_mode_window = ReadingModeWindow(self, folder_rows, start_index)

    def enter_fullscreen_preview(self):
        """画像プレビューを全画面表示にする。前後移動・再生速度・スライドショーのボタンも
        一時的に全画面ウィンドウへ移して、そのまま操作できるようにする。"""
        if getattr(self, "current_preview_path", None) is None:
            show_notification(self, self.tr("notify.title.fullscreen"), self.tr("notify.fullscreen_select_first"))
            return
        
        self.fullscreen_window = FullscreenPreviewWindow(self)

        fs_layout = QVBoxLayout(self.fullscreen_window)
        fs_layout.setContentsMargins(SPACING_SM, SPACING_SM, SPACING_SM, SPACING_SM)
        fs_layout.setSpacing(SPACING_SM)

        self.preview_layout.removeWidget(self.btn_prev_image)
        self.preview_layout.removeWidget(self.lbl_preview)
        self.preview_layout.removeWidget(self.btn_next_image)

        self.btn_prev_image.setVisible(True)
        self.lbl_preview.setVisible(True)
        self.btn_next_image.setVisible(True)

        image_row = QHBoxLayout()
        image_row.setSpacing(SPACING_SM)
        image_row.addWidget(self.btn_prev_image)
        image_row.addWidget(self.lbl_preview, 1)
        image_row.addWidget(self.btn_next_image)
        fs_layout.addLayout(image_row, 1)
        
        self.slideshow_layout.removeWidget(self.btn_slideshow)
        self.slideshow_layout.removeWidget(self.btn_speed)
        
        control_row = QHBoxLayout()
        control_row.setSpacing(SPACING_SM)
        control_row.addStretch()
        control_row.addWidget(self.btn_slideshow)
        control_row.addWidget(self.btn_speed)
        
        self.btn_exit_fullscreen = QPushButton(self.tr("fullscreen.button.exit"))
        self.btn_exit_fullscreen.setIcon(render_svg_icon("preview_fullscreen_exit", size=16))
        self.btn_exit_fullscreen.setIconSize(QSize(16, 16))
        self.btn_exit_fullscreen.setFixedHeight(36)
        self.btn_exit_fullscreen.clicked.connect(self.exit_fullscreen_preview)
        control_row.addWidget(self.btn_exit_fullscreen)
        fs_layout.addLayout(control_row)
        
        self.lbl_preview.setMinimumSize(100, 100)
        self.lbl_preview.setMaximumSize(16777215, 16777215)
        
        self.fullscreen_window.setStyleSheet(self.build_stylesheet(self.theme_colors))
        self.fullscreen_window.showFullScreen()
        QTimer.singleShot(50, self.refresh_preview_pixmap)

    def exit_fullscreen_preview(self):
        """全画面プレビューを終了し、ボタン類を通常画面のレイアウトへ戻す"""
        if not getattr(self, "fullscreen_window", None):
            return
        
        self.slideshow_layout.removeWidget(self.btn_slideshow)
        self.slideshow_layout.removeWidget(self.btn_speed)
        self.slideshow_layout.addWidget(self.btn_slideshow, 2)
        self.slideshow_layout.addWidget(self.btn_speed)
        
        self.preview_layout.removeWidget(self.btn_prev_image)
        self.preview_layout.removeWidget(self.lbl_preview)
        self.preview_layout.removeWidget(self.btn_next_image)
        self.preview_layout.addWidget(self.btn_prev_image)
        self.preview_layout.addWidget(self.lbl_preview, 1)
        self.preview_layout.addWidget(self.btn_next_image)
        
        fs_window = self.fullscreen_window
        self.fullscreen_window = None
        fs_window.close()
        fs_window.deleteLater()
        
        self.set_preview_size_mode(self.preview_size_mode)

    def prev_image(self):
        """前の画像へ移動する。非表示（検索で絞り込まれた／フォルダが折りたたまれた）行や
        見出し行はスキップする。ループ回数をリスト件数で打ち切ることで、
        選択中の行が存在しない（currentRow()が-1）場合でも無限ループにならないようにしている。"""
        count = self.image_list.count()
        if count == 0:
            return
        current_row = self.image_list.currentRow()
        row = current_row - 1 if current_row >= 0 else count - 1
        for _ in range(count):
            if row < 0:
                row = count - 1
            item = self.image_list.item(row)
            if not item.isHidden() and item.data(Qt.UserRole) is not None:
                self.image_list.setCurrentRow(row)
                return
            row -= 1

    def next_image(self):
        """次の画像へ移動する。prev_imageと同様、非表示行・見出し行をスキップし、
        ループ回数をリスト件数で打ち切ることで無限ループを防ぐ。"""
        count = self.image_list.count()
        if count == 0:
            return
        current_row = self.image_list.currentRow()
        row = current_row + 1 if current_row >= 0 else 0
        for _ in range(count):
            if row >= count:
                row = 0
            item = self.image_list.item(row)
            if not item.isHidden() and item.data(Qt.UserRole) is not None:
                self.image_list.setCurrentRow(row)
                return
            row += 1

    def _resolve_missing_database(self):
        """既定の保存先に、現在使用するはずのデータベースファイルが存在しない場合の処理。
        初回起動時、または利用者がファイルを直接削除した場合に該当する
        （init_db()が黙って新規作成してしまう前に、必ずこのメソッドで利用者に選ばせる）。"""
        if os.path.exists(database.get_current_db_path()):
            return

        dialog = DatabaseMissingDialog(self)
        dialog.exec()

        if dialog.result_mode == "existing":
            database.set_current_db_name(dialog.selected_existing)
            database.resolve_current_db_name()
        elif dialog.result_mode == "external":
            try:
                new_filename = database.import_external_database(dialog.external_path)
            except ValueError as e:
                show_notification(self, self.tr("dialog.db_missing.import_failed.title"), str(e))
                return
            database.set_current_db_name(new_filename)
            database.resolve_current_db_name()
            display_name = os.path.splitext(new_filename)[0]
            show_notification(
                self, self.tr("dialog.db_missing.import_done.title"),
                self.tr("dialog.db_missing.import_done.body").format(db_name=display_name)
            )
        else:
            self._pending_sample_import = dialog.use_sample_data

    def _import_sample_data(self):
        """初回セットアップ時、任意で選ばれたサンプル画像を取り込む。
        同梱されているサンプル画像（sample_data/フォルダ、AI生成画像を模したダミー画像で
        著作権上の問題はない）を、Application Support配下の専用フォルダへコピーしたうえで
        （＝以後は通常の画像と同じく自由に削除・編集できる実データとして扱う）、
        既存の「フォルダを取り込む」処理と同じ経路でDBへ登録する。"""
        src_dir = get_sample_data_dir()
        if not os.path.isdir(src_dir):
            return

        dest_dir = os.path.join(database.get_db_dir(), "sample_images")
        try:
            if not os.path.isdir(dest_dir):
                shutil.copytree(src_dir, dest_dir)
            importer.import_images_from_folder(dest_dir)
        except OSError as e:
            show_notification(self, self.tr("dialog.db_missing.sample_import_failed.title"), str(e))

    def restart_app(self):
        """アプリを再起動する。データベースの切り替え後、内部状態
        （サムネイルキャッシュ、フォルダの折りたたみ状態等）を確実にリセットするために、
        アプリ内で即座に切り替えるのではなく、プロセスごと再起動する方式を採る。"""
        python = sys.executable
        os.execv(python, [python] + sys.argv)

    def closeEvent(self, event):
        """メインウィンドウを閉じる際、全画面プレビュー・読書モードが開いていれば一緒に閉じる。
        これらは独立したトップレベルウィンドウとして作られているため、メインウィンドウを閉じても
        自動的には閉じない（特に複数の仮想デスクトップ環境で、別のデスクトップに残り続けてしまう
        原因になっていた）。"""
        if getattr(self, "fullscreen_window", None) is not None:
            self.fullscreen_window.close()
        if getattr(self, "reading_mode_window", None) is not None:
            self.reading_mode_window.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIImageViewerApp()
    window.show()
    sys.exit(app.exec())
