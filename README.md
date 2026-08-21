[日本語版はこちら / Japanese README is here](./README.ja.md)

<img width="1311" height="1071" alt="UI1" src="./design/screenshots/ui_main_light.png" />

## Seed Book (AI image browser)
A desktop app for centrally managing and viewing images—mainly AI-generated ones (e.g. Stable Diffusion)—along with their metadata (prompts, negative prompts, model parameters, etc.). Optimized for Stability Matrix output, and plays well with other file managers.

> **Why I Built This** <br>
> Stability Matrix dumps everything into one "inference" folder, and the default preview was hard to browse. I built this to comfortably browse large batches without ever touching the originals. Started as a Stability Matrix companion, but works fine as a general image viewer too.
>
> **About the Development Process** <br>
> I don't have a professional programming background — this app is "vibe coded," built through dialogue with AI coding tools (Claude Sonnet) rather than writing code myself. Still, nothing ships carelessly: every feature is manually tested, builds are verified in a clean user account, and releases go through proper Apple notarization.

For more detailed usage instructions, see [manual.md](./manual.md) (a [Japanese manual](./manual.ja.md) is also available).<br>
Since v1.3.0, the app itself can also switch its display language (Auto / Japanese / English) from Settings.

📖 Development progress and notes are also shared on the [dev diary](https://ocoe-puipui.github.io/diary/) (Japanese only).

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

**Language** Python 3.10+

**GUI Framework** PySide6 (Qt for Python)

**Image Processing** Pillow (PIL)

**Database** SQLite3

**OS Compatibility** Cross-platform compatible

**AI Coding Partner** Anthropic's Claude (Sonnet)

---

## How to Run the Application
Follow these steps to launch the application locally.

### 1. Install Dependencies
Run the following command in your terminal (or virtual environment) to install the required libraries.

```bash
pip install -r requirements.txt
```

### 2. Launch the App
Navigate to the directory where the files are located and execute `main.py`.

```bash
python main.py
```

---

## File Structure & Roles
This project consists of five core files, cleanly modularized by role:

#### 1. `main.py` (Entry Point)
Initializes and displays the GUI application window.

#### 2. `app.py` (Core Logic)
Handles the entire UI, event handling, real-time filtering, sorting, grouping, slideshow, clipboard integration, theme switching, and the settings dialog.

#### 3. `importer.py` (Data Extraction)
Extracts metadata via Pillow, computes the file's SHA-256 hash, and handles bulk import synchronization.

#### 4. `database.py` (Database)
Manages the SQLite3 database, performing auto-migrations and ensuring data integrity.

#### 5. `.gitignore` (Exclusions)
Specifies files excluded from version control (e.g., `venv`, `__pycache__`, `image_metadata*.db`, and `current_db.txt`, which records the currently active database).

---

## Features

#### 1. Sync & Import

**Differential Auto-Import** <br>
Remembers imported folder paths and scans only new images on "Sync." Both import and sync only scan files directly inside the folder (no subfolders).

**Import Order Confirmation** <br>
Choose import order (name/creation/modification date, ascending or descending). Confirm every time (default) or auto-reuse the last order.

**Individual File Import** <br>
Select and import individual image files (multi-select supported) instead of a whole folder.

**Automatic Sequential Naming** <br>
New imports get an auto-generated sequence number (e.g., CG_00001) instead of the original filename by default. Prefix, digit count, and an optional append string are configurable in Settings; each prefix+append combo has its own counter, and numbers are never reused after deletion (manual reset available). Can be disabled to use the real filename as-is. Prefix/append fields support `{date}` and `{folder name}` placeholders.

**Per-Folder Naming Override** <br>
Right-click a folder header in "Group by Folder" view to set a folder-specific naming rule overriding the app-wide default. Applies to new imports plus "Bulk Rename" and "Bulk Export with Rename" for that folder.

**Selectable Import Formats** <br>
PNG/JPG/JPEG/WEBP enabled by default; GIF/BMP/TIFF toggleable via checkboxes (GIF shows first frame). The checkbox row can be hidden.

**Duplicate Prevention** <br>
Compares file content via **SHA-256 hash**, skipping duplicates regardless of filename. Optionally import duplicates as separate records instead (skipping is default).

**Background Processing** <br>
Shows a real-time, cancelable progress dialog during large imports.

#### 2. Viewer

**Automatic Parameter Separation** <br>
Parses metadata into Prompt, Negative Prompt, and Other Details (Steps, Sampler, Seed, etc.). Steps/Sampler/Scheduler/CFG scale/Seed/Size can also show as individual fields below the model name, each toggleable in Settings, with a dedicated copy button for Seed.

**Supported Formats** <br>
Supports Stable Diffusion WebUI (Automatic1111/Forge), NovelAI, and ComfyUI. ComfyUI workflows vary too much between users for auto-extraction, so the full workflow is preserved as-is in "Other Parameters / Metadata / EXIF Info."

**Camera EXIF Display** <br>
For photos with no AI metadata (JPEG/TIFF/WEBP), reads camera EXIF (make, model, date, exposure, F-number, ISO, focal length, GPS) into the "Other Parameters" field. PNG/GIF/BMP lack native EXIF, so unsupported.

**Per-Image Memo Field** <br>
A free-text, searchable memo field at the top of the edit area, independent of AI metadata.

**One-Click Copy** Pressing the button next to any prompt field copies it to the clipboard.

**Star Rating** <br>
Hover for a live preview, click to set 0–5. Click the same star again to clear it.

**Preview Display Modes** <br>
Hidden, Standard, Compact, or Fullscreen. "Hidden" frees space for editing metadata; navigation/slideshow/speed controls still work in fullscreen.

**Drag Out the Preview Image** <br>
The previewed image can be dragged directly to Finder/Explorer or another app to copy it out.

**Rename Actual Files** <br>
Directly edit and rename the actual file on disk, beyond the in-app "Name" field. Duplicate filenames aren't allowed within the same folder.

**Freely Editable Name** <br>
The in-app "Name" field is independent of the actual filename and reusable across images (e.g., as a search tag).

**Save as New Copy** <br>
Save edits as a new copy at a location of your choice, without touching the original.

**Bulk Rename (In-App "Name" Only)** <br>
Select images, right-click → "Bulk Rename (Sequential)..." to renumber only the in-app "Name" field via your sequential naming rule (or folder override). **Actual filenames are never touched.** Locked images are skipped; each `{folder name}` group counts from 1.

**Bulk Export with Rename (Actual Filenames)** <br>
Select images/a folder header → "Bulk Export with Rename (Sequential)..." to copy originals — unchanged — into a chosen folder with sequentially renamed copies. Kept distinct from Bulk Rename so it's clear which affects the in-app name vs. the real file.

**Clear Metadata Fields** <br>
Instantly clear model, prompt, negative prompt, memo, or other fields. Stays pending until "Save."

**Toggle Metadata Fields** <br>
Temporarily hide memo/model/prompt/negative prompt/other fields individually; freed space distributes evenly among the rest, and the generation-parameter row follows the model field. One button near the top-right toggles all of these plus the import-format checkbox row at once.

**List Placeholder Messages** <br>
Shows a friendly message when the list is empty or files are dragged over it (drag-and-drop import is currently disabled — see below).

**Icon Design** <br>
Major buttons and headers use Google Material Symbols icons, auto-adjusting color for visibility against the current theme and accent backgrounds.

#### 3. UX & OS Integration

**Safe Drag & Drop** Drag images from the app's list to OS folders or other apps — only a copy is made, protecting the original.

**Right-Click Menu** <br>
Reveal in Finder/Explorer, copy the file, or copy its path. Multi-selection supported.

**Dark/Light Theme** <br>
Follows the macOS appearance setting, or fix to Dark/Light from Settings.

**Panel Layout Switching** <br>
Choose whether search/import/list appear on the left or right (Standard/Mirrored) — useful for right- or left-handed workflows.

**Edit Lock** <br>
Lock/unlock editing per image from the right-click menu. Locked images can't be deleted or modified.

**Sync-Safe Deletion** <br>
Images removed from the list stay removed after "Sync," returning only via explicit re-import.

**Settings Dialog (⚙)** <br>
Sequential naming config (toggle, prefix, digits, append, counter reset), parameter display toggles, theme/panel-layout switching, folder import order, database reset, CSV export, multi-database creation/switching, and full settings reset. Help and release notes open from the top of the main window.

**Multiple Database Switching** <br>
Create and switch between multiple databases (`image_metadata.db`, `image_metadata2.db`, ...) from Settings; switching auto-restarts the app. Databases live in `~/Library/Application Support/AIImageViewer/`.

#### 4. Search, Sort & Slideshow

**Real-time Filtering** <br>
Filters the list instantly by keyword (name/filename/prompt/negative prompt/other metadata) or star rating.

**Sorting** <br>
Sort by name, creation/edit/import date, rating, or file size, with independent ascending/descending toggle, plus instant grid/list switching.

**Adjustable Thumbnail Size** <br>
Small/Medium/Large tiles in grid view; Large also shows file location and date.

**Group by Folder** <br>
In list view, images group under folder headers. Click to collapse/expand (▼/▶); right-click to reorder folders via drag-and-drop. ON/OFF, collapsed state, and order are remembered across restarts.

**Slideshow Playback** <br>
Automatic timer-based playback, speed adjustable 0.5x–2x in 0.25 steps; can cycle through only the current search filter's matches.

**Reading Mode (Two-Page Spread View)** <br>
Displays same-folder images side-by-side full-screen like an open book (needs "Group by Folder" or an open album). Supports LTR/RTL direction, page turning via slider/arrow keys/edge clicks, an independent dark/light toggle, and center-aligned display. View-only.

#### 5. Albums (Virtual Folders) (v1.4+)

**A virtual container that groups images across real folders** <br>
Separate from your disk structure, "Albums" let you freely group images; one image can belong to multiple albums. List view and album view are mutually exclusive, toggled via icon buttons at the top.

**Adding images to an album** <br>
Via right-click → "Add to Album" (existing or new), or drag-and-drop onto an album row.

**Set an auto-numbering rule right when you create the album** <br>
The "Create an Album" dialog lets you set an album-specific auto-numbering rule (prefix/digits/append) alongside the name (off by default). Prefix/append support `{album name}` and `{date}` placeholders.

**Album list behaves like folder-grouped view** <br>
Click a header to expand/collapse; right-click (or "⋯") opens: reorder, rename, expand/collapse all, bulk-export with sequential renaming, set numbering rule, delete.

**Album-specific auto-numbering rule** <br>
When set, takes priority for bulk-rename/export within that album (independent of folder or app-wide rules — never combined). Works with a single selected image too.

**Exporting to Finder** <br>
Drag an album, or images inside one, onto Finder — it's materialized into a temp folder since albums have no real disk folder. Preserves original filenames (use "Export Album Images as Renamed Copies (Sequential)" for numbering).

**Works with search and sorting** <br>
The search box filters within the open album; sort type/order apply to album view too.

---

## Known Limitations

**Drag & Drop Import Temporarily Disabled** <br>
Dragging files from Finder onto the image list is disabled due to unstable behavior. Use "Import Folder"/"Import Images" instead.

---
## Disclaimer

**Purpose** <br>
Developed solely for personal study, research, and image-management workflow enhancement.

**Intellectual Property (IP)** <br>
The author assumes no responsibility for conflicts over third-party tool terms, AI licenses, or IP rights arising from use of this program. Use within the scope of relevant laws.

**No Warranty** <br>
Provided "as is" without warranty of any kind. The author is not liable for any claim, damages, or other liability arising from use of this software.

---
## License

This project's own code is proprietary (All Rights Reserved) for now; see [LICENSE](./LICENSE) for the full terms (a free, freeware-style license — not open source yet, but planned for the future). It uses third-party open-source libraries under their own licenses; see [THIRD-PARTY-NOTICES.md](./THIRD-PARTY-NOTICES.md) for details (PySide6/Qt under LGPLv3, Pillow under MIT-CMU).

---
<p>
<img width="700" height="700" alt="UI3" src="./design/screenshots/ui_main_dark.png" /><img width="300" height="700" alt="UI4" src="./design/screenshots/ui_settings_dark.png" />
</p>
<br>
THANKS!
</content>
</invoke>
