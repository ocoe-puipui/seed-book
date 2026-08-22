[日本語版はこちら / Japanese README is here](./README.ja.md)

<img width="1311" height="1071" alt="UI1" src="./design/screenshots/ui_main_light.png" />

## Seed Book (AI image browser)
A desktop app for centrally managing and viewing images — mainly AI-generated (e.g. Stable Diffusion) — with their metadata (prompts, negative prompts, model parameters, etc.). Optimized for Stability Matrix output; plays well with other file managers.

> **Why I Built This** — Stability Matrix dumps everything into one "inference" folder with a hard-to-browse preview. I built this to browse large batches comfortably without touching the originals — started as a companion tool, but works as a general image viewer too.
>
> **About Development** — I have no professional programming background; this app is "vibe coded" through dialogue with AI tools (Claude Sonnet) rather than hand-written. Still, every feature is manually tested, verified in a clean account, and properly notarized by Apple.

Detailed usage instructions: [manual.md](./manual.md) ([Japanese manual](./manual.ja.md) also available). Since v1.3.0 the app can also switch its display language (Auto/Japanese/English) from Settings. 📖 Dev notes: [diary](https://ocoe-puipui.github.io/diary/) (Japanese only).

---

## Table of Contents
1. [Technical Stack](#technical-stack)
2. [How to Run the Application](#how-to-run-the-application)
3. [File Structure & Roles](#file-structure--roles)
4. [Features](#features)
5. [Known Limitations](#known-limitations)
6. [Disclaimer](#disclaimer)
7. [License](#license)

---

## Technical Stack
**Language** Python 3.10+ · **GUI** PySide6 (Qt for Python) · **Image Processing** Pillow (PIL) · **Database** SQLite3 · **OS** Cross-platform · **AI Coding Partner** Anthropic's Claude (Sonnet)

---

## How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the App
Navigate to the directory containing the files and run `main.py`.
```bash
python main.py
```

---

## File Structure & Roles
Five core files, cleanly modularized:

| File | Role |
|---|---|
| `main.py` | Entry point — initializes/displays the GUI window. |
| `app.py` | Core logic — UI, events, filtering, sorting, grouping, slideshow, clipboard, theme, settings. |
| `importer.py` | Data extraction — metadata via Pillow, SHA-256 hash, bulk import sync. |
| `database.py` | Database — SQLite3, auto-migrations, integrity checks. |
| `.gitignore` | Exclusions — `venv`, `__pycache__`, `image_metadata*.db`, `current_db.txt` (active-DB pointer). |

---

## Features

#### 1. Sync & Import
- **Differential Auto-Import** — Remembers folder paths, scans only new images on "Sync" (top level only, no subfolders); individual files can also be imported (multi-select). Choose import order (name/creation/modification date, asc/desc); confirm each time (default) or auto-reuse last.
- **Automatic Sequential Naming** — New imports default to an auto sequence number (e.g., `CG_00001`); prefix, digits, and append string are configurable, each combo has its own non-reused counter (manual reset), with `{date}`/`{folder name}` placeholders. Disable to keep real filenames. A per-folder rule (right-click a header in "Group by Folder") overrides the default, including that folder's Bulk Rename/Export.
- **Selectable Import Formats** — PNG/JPG/JPEG/WEBP by default; GIF/BMP/TIFF toggleable (GIF shows first frame); checkbox row hideable. **Duplicate Prevention** compares content via SHA-256 hash, skipping duplicates by default (or optionally importing as separate records), with a cancelable progress dialog for large imports.

#### 2. Viewer
- **Automatic Parameter Separation** — Splits metadata into Prompt, Negative Prompt, and Other Details (Steps, Sampler, Seed, etc.), each toggleable below the model name, with a copy button for Seed. Supports SD WebUI (Automatic1111/Forge), NovelAI, and ComfyUI (varied workflows kept as-is, not auto-extracted).
- **Camera EXIF Display** — For non-AI photos (JPEG/TIFF/WEBP), reads camera EXIF (make, model, date, exposure, F-number, ISO, focal length, GPS) into "Other Parameters" (unsupported: PNG/GIF/BMP). A searchable memo field sits atop the edit area, separate from AI metadata.
- **One-Click Copy & Star Rating** — Copy any prompt field to the clipboard; hover a star to preview, click to set 0–5, click again to clear.
- **Preview Display Modes** — Hidden, Standard, Compact, or Fullscreen (nav/slideshow/speed controls work in fullscreen); the image can be dragged to Finder/Explorer or another app to copy it out.
- **Names vs. Real Files** — The in-app "Name" is editable/reusable (e.g. as a search tag), separate from the actual filename; the real file can also be renamed on disk directly (no duplicates per folder). Edits can be saved as a new copy anywhere, leaving the original untouched.
- **Bulk Rename vs. Bulk Export with Rename** — "Bulk Rename (Sequential)" renumbers only the in-app Name via your naming rule/folder override (**filenames untouched**, locked images skipped, each `{folder name}` group counts from 1). "Bulk Export with Rename (Sequential)" copies originals unchanged into a chosen folder as renamed copies — kept separate to distinguish which name is affected.
- **Metadata Field Controls** — Clear model/prompt/negative prompt/memo/other fields instantly (pending until "Save"), or hide any individually (freed space redistributes; parameter row follows the model field); one button toggles all fields plus the import-format row. A placeholder shows when the list is empty or dragged over (drag-drop import disabled); major buttons/headers use Material Symbols icons, auto-adjusted for theme.

#### 3. UX & OS Integration
- **Drag & Drop / Right-Click** — Drag images to OS folders or apps (only a copy is made); right-click to reveal in Finder/Explorer, copy file/path, or lock/unlock editing per image (locked can't be deleted/modified). Multi-select supported.
- **Theme, Layout & Sync-Safe Deletion** — Dark/Light follows macOS appearance or fixes from Settings; search/import/list sit left or right (Standard/Mirrored) for right- or left-handed use; images removed from the list stay removed after "Sync," returning only via re-import.
- **Settings Dialog (⚙)** — Naming config, parameter display toggles, theme/panel-layout switching, import order, DB reset, CSV export, multi-DB creation/switching (auto-restarts; DBs in `~/Library/Application Support/AIImageViewer/`), full reset; Help/release notes open from the window top.

#### 4. Search, Sort & Slideshow
- **Real-time Filtering & Sorting** — Instant filtering by keyword (name/filename/prompt/negative prompt/metadata) or star rating; sort by name, date, rating, or size, independent asc/desc toggle, instant grid/list switching.
- **Thumbnails & Grouping** — Small/Medium/Large grid tiles (Large shows location/date); list view groups under folder headers, collapse/expand (▼/▶), reorder via drag-drop — state and order persist across restarts.
- **Slideshow Playback** — Timer-based, speed adjustable 0.5x–2x in 0.25 steps; can cycle only the current filter matches.
- **Reading Mode (Two-Page Spread)** — Same-folder images shown side-by-side full-screen like an open book (needs "Group by Folder" or an album). LTR/RTL, page turning via slider/arrow keys/edge clicks, own dark/light toggle, centered. View-only.

#### 5. Albums (Virtual Folders) (v1.4+)
- **Virtual Container Across Real Folders** — Separate from disk structure; one image can belong to multiple albums. List/album views are mutually exclusive, toggled via icon buttons at top. Add images via right-click → "Add to Album," or drag onto an album row.
- **Album List Controls** — Click a header to expand/collapse; right-click (or "⋯") for reorder, rename, expand/collapse all, bulk-export with sequential rename, numbering rule, delete.
- **Album-Specific Auto-Numbering** — Set at creation or later (prefix/digits/append, off by default, `{album name}`/`{date}` placeholders); when set, it takes priority for that album's bulk-rename/export (independent of folder/app-wide rules, never combined).
- **Exporting to Finder** — Drag an album, or images inside one, onto Finder; it's materialized into a temp folder (albums have no disk folder), preserving original filenames (use "Export Album Images as Renamed Copies (Sequential)" for numbering). Search and sorting work within the open album too.

---

## Known Limitations

**Drag & Drop Import Temporarily Disabled** — Dragging files from Finder onto the image list is disabled due to unstable behavior; use "Import Folder"/"Import Images" instead.

---
## Disclaimer

**Purpose** — Developed solely for personal study, research, and image-management workflow enhancement.

**IP** — The author assumes no responsibility for conflicts over third-party tool terms, AI licenses, or IP rights from use of this program; use within relevant laws.

**No Warranty** — Provided "as is," without warranty of any kind; the author is not liable for claims or damages from use of this software.

---
## License

This project's own code is proprietary (All Rights Reserved) for now — see [LICENSE](./LICENSE) (free, freeware-style; not open source yet, but planned). Third-party libraries keep their own licenses — see [THIRD-PARTY-NOTICES.md](./THIRD-PARTY-NOTICES.md) (PySide6/Qt under LGPLv3, Pillow under MIT-CMU).

---
<p>
<img width="700" height="700" alt="UI3" src="./design/screenshots/ui_main_dark.png" /><img width="300" height="700" alt="UI4" src="./design/screenshots/ui_settings_dark.png" />
</p>
<br>
THANKS!
