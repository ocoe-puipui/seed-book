2026/08/17 (v1.3.0)

[日本語版はこちら / Japanese README is here](./README.ja.md)

<img width="1311" height="1071" alt="UI1" src="https://github.com/user-attachments/assets/c3fd22de-0f36-4f6f-b675-1a8a1729dab1" />

## Seed Book (AI image browser)
A desktop app for centrally managing and viewing images — mainly AI-generated ones from tools like Stable Diffusion — along with their metadata (prompts, negative prompts, model parameters, etc.). Optimized for Stability Matrix output, but works well alongside any file manager.

> **Why I Built This** <br>
> Stability Matrix dumps generated images into one "inference" folder, and its default preview was hard to browse. This app lets you comfortably preview large batches without ever touching the original files. It also works well as a general-purpose image viewer.
>
> **About the Development Process** <br>
> I'm not a professional programmer. This app is built through "vibe coding" — designing and implementing features via ongoing dialogue with AI, using Anthropic's Claude (Sonnet) as my coding partner. Every feature is still manually tested, verified in a clean separate user account, and notarized through Apple's official process before release.

See [manual.md](./manual.md) for detailed usage (a [Japanese manual](./manual.ja.md) is also available).<br>
Since v1.3.0, the app's display language (Auto / Japanese / English) can be switched from Settings.

📖 Development notes are also shared on the [dev diary](https://ocoe-puipui.github.io/diary/) (Japanese only).

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

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the App
```bash
python main.py
```

---

## File Structure & Roles
Five core files, cleanly modularized by role:

#### 1. `main.py` (Entry Point)
Launches and displays the GUI application window.

#### 2. `app.py` (Core Logic)
Handles the entire PySide6 UI: event handling, filtering, sorting, grouping, slideshow, clipboard, theme switching, and settings.

#### 3. `importer.py` (Data Extraction)
Extracts metadata via Pillow, computes SHA-256 hashes, and handles bulk import sync.

#### 4. `database.py` (Database)
Manages the SQLite3 database with auto-migration and data integrity checks.

#### 5. `.gitignore` (Exclusions)
Excludes `venv`, `__pycache__`, `image_metadata*.db`, and `current_db.txt` (the active-database pointer) from version control.

---

## Features

#### 1. Sync & Import

**Differential Auto-Import** <br>
Remembers imported folder paths and scans only new images on "Sync." Subfolders are excluded.

**Import Order Confirmation** <br>
Choose import order (name / creation / modification date, asc or desc), confirmed every time or reused automatically.

**Individual File Import** <br>
Import selected image files directly, without pulling in a whole folder.

**Automatic Sequential Naming** <br>
New images are auto-named with a sequence number (e.g., CG_00001) by default. Prefix, digit count, and an append string are configurable; each combination has its own independent, never-reused counter (manually resettable). Can be toggled off entirely. Prefix/append fields support `{date}` and `{folder name}` placeholders, insertable via a click.

**Per-Folder Naming Override** <br>
Right-click a folder header (in "Group by Folder" view) to set a folder-specific naming rule, applied to new imports and to Bulk Rename / Bulk Export with Rename alike.

**Selectable Import Formats** <br>
PNG/JPG/JPEG/WEBP by default; GIF/BMP/TIFF optional via checkboxes (with their own show/hide toggle).

**Duplicate Prevention** <br>
Skips duplicates by comparing **SHA-256 hash**, regardless of filename. Can opt in to importing duplicates as separate records.

**Background Processing** <br>
Shows a cancellable real-time progress dialog during large imports.

#### 2. Viewer

**Automatic Parameter Separation** <br>
Parses metadata into Prompt, Negative Prompt, and Other Details. Steps, Sampler, Scheduler, CFG scale, Seed, and Size can also show as individual toggleable fields, with a one-click Seed copy button.

**Supported Formats** <br>
Stable Diffusion WebUI (Automatic1111 / Forge), NovelAI, and ComfyUI. Since ComfyUI workflows vary widely, its full workflow is preserved as-is in "Other Parameters" rather than auto-parsed.

**Camera EXIF Display** <br>
For non-AI photos (JPEG/TIFF/WEBP), automatically reads camera EXIF (make, model, date, exposure, ISO, GPS, etc.) into "Other Parameters." Not supported for PNG/GIF/BMP.

**Per-Image Memo Field** <br>
A free-text memo, independent of AI metadata, also included in search.

**One-Click Copy** Copies any prompt field's content to the clipboard instantly.

**Star Rating** <br>
Hover for a live preview, click to set 0–5 stars; click the same star again to clear.

**Preview Display Modes** <br>
Hidden / Standard / Compact / Fullscreen. Navigation, slideshow, and speed controls work fully even in fullscreen.

**Drag Out the Preview Image** <br>
Drag the previewed image directly to Finder/Explorer or another app to copy it out.

**Rename Actual Files** <br>
Edit and rename the real file on disk directly, in addition to the in-app "Name" field. No duplicate names within a folder.

**Freely Editable Name** <br>
The in-app "Name" field is independent of the actual filename and can be reused across images (e.g., as a tag).

**Save as New Copy** <br>
Save edits as a new copy elsewhere, leaving the original untouched.

**Bulk Rename (In-App "Name" Only)** <br>
Renumber the in-app "Name" for selected images via your naming rule. **Actual filenames are never touched.** Locked images are skipped; each `{folder name}` group counts independently from 1.

**Bulk Export with Rename (Actual Filenames)** <br>
Copy selected images (or a whole folder) to a new location, with the **copies'** filenames sequentially renamed — kept distinct from Bulk Rename above.

**Clear Metadata Fields** <br>
One-click clear for model, prompt, negative prompt, memo, or other fields; pending until "Save."

**Toggle Metadata Fields** <br>
Hide/show individual metadata fields, with freed space redistributed automatically. One button (near settings) toggles all fields plus the import-format checkbox row at once.

**List Placeholder Messages** <br>
Friendly messages for an empty list or drag-over (drag-and-drop import is currently disabled — see Known Limitations).

**Icon Design** <br>
Google Material Symbols-based icons, with colors auto-adjusting for theme and accent-color contrast.

#### 3. UX & OS Integration

**Safe Drag & Drop** Drag images out to OS folders or other apps — only a copy is made, protecting the original.

**Right-Click Menu** <br>
Reveal in Finder/Explorer, copy the file, or copy its path. Supports multi-selection.

**Dark/Light Theme** <br>
Follows macOS appearance automatically, or fix manually in Settings.

**Panel Layout Switching** <br>
Choose left or right placement for search/import/list (Standard / Mirrored) in Settings.

**Edit Lock** <br>
Lock/unlock editing per image from the right-click menu; locked images can't be deleted or modified.

**Sync-Safe Deletion** <br>
Deleted images stay removed after Sync, returning only via explicit re-import.

**Settings Dialog (⚙)** <br>
Covers naming rule configuration, parameter display toggles, theme/panel switching, import order preferences, database reset, CSV export, multi-database management, and full reset. Help and release notes open from the main window's top bar.

**Multiple Database Switching** <br>
Create and switch between multiple databases from Settings (auto-restarts the app). Stored in `~/Library/Application Support/AIImageViewer/`.

#### 4. Search, Sort & Slideshow

**Real-time Filtering** <br>
Filters instantly by keyword (name, filename, prompt, negative prompt, metadata) or star rating.

**Sorting** <br>
By name, creation/edit/import date, rating, or file size, ascending/descending. Grid/list view toggle.

**Adjustable Thumbnail Size** <br>
Small/Medium/Large tiles in grid view; Large also shows location and date.

**Group by Folder** <br>
List view can group by folder header, collapsible via click, reorderable via drag-and-drop. State is remembered across restarts.

**Slideshow Playback** <br>
Automatic timer-based playback, 0.5x–2x speed in 0.25 steps, optionally limited to the current search filter.

**Reading Mode (Two-Page Spread View)** <br>
Displays same-folder images side-by-side full-screen, like an open book (requires "Group by Folder"). Supports L-to-R/R-to-L direction, page turning via slider/arrows/edge-click, independent dark/light background, and a center-aligned spread option. View-only.

---

## Known Limitations

**Drag & Drop Import Temporarily Disabled** <br>
Dragging files from Finder directly onto the image list is disabled due to instability — use the "Import Folder" / "Import Images" buttons instead.

---
## Disclaimer

**Purpose** <br>
Developed solely for personal study, research, and image-management workflow enhancement.

**Intellectual Property (IP)** <br>
The author assumes no responsibility for conflicts with third-party tool terms, AI licenses, or IP rights arising from use of this program. Use within applicable laws and regulations.

**No Warranty** <br>
Provided "as is," without warranty of any kind. The author is not liable for any damages arising from use of this software.

---
## License

This project's own code is proprietary (All Rights Reserved) for now — see [LICENSE](./LICENSE) for full terms (a free, freeware-style license, not open source yet). Third-party open-source libraries retain their own licenses; see [THIRD-PARTY-NOTICES.md](./THIRD-PARTY-NOTICES.md) (PySide6/Qt under LGPLv3, Pillow under MIT-CMU).

---
<p>
<img width="700" height="700" alt="UI3" src="https://github.com/user-attachments/assets/4021a98a-15d2-4e22-8e2c-b1d1f4d2f05d" /><img width="300" height="700" alt="UI4" src="https://github.com/user-attachments/assets/fad7b7a0-0a4d-46b8-acd6-9dc4bcbbd72f" />
</p>
<br>
THANKS!
