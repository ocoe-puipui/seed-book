# Seed Book (AI image browser) - User Manual

**Language:** [日本語](./manual.ja.md) | English

## Table of Contents
1. [UI Names and Roles](#1-ui-names-and-roles)
2. [Basic Usage](#2-basic-usage)
3. [Albums (Virtual Folders)](#3-albums-virtual-folders)
4. [Settings Screen](#4-settings-screen)
5. [Folder Image Sync Rules](#5-folder-image-sync-rules)
6. [Data Backup and Migration](#6-data-backup-and-migration)
7. [Known Limitations](#7-known-limitations)

---

## 1. UI Names and Roles

<img width="1311" height="1071" alt="UI1" src="./design/screenshots/ui_main_light.png" />


The app has two panes — the "List Display Area" on the left and the "Edit Area" on the right — plus a "Settings" screen.

### 1.1 List Display Area (Left Side)
* **Search / Settings row:**
  * **Search field:** Filters images by any keyword.
  * **Settings button (gear icon):** Opens the settings dialogs.
* **Import / Sync row:**
  * **Import Folder:** Imports all images directly inside a chosen folder.
  * **Import Images:** Imports individually selected image files.
  * **Sync button (🔄):** Rescans the current folder state.
* **Folder/Album toggle row:**
  * Switches between the normal image list and album view (see [3. Albums](#3-albums-virtual-folders)). In album view, a "Create an Album" button also appears.
* **Sort / Display toggle row:**
  * **Sort / Ascending-Descending toggle:** "By Filename" (actual file name) and "By Name" (the app's own "Name" field) are separate options.
  * **List/Grid toggle:** Switches between list and grid (thumbnail) view.
  * **Group by folder toggle:** Groups images by folder.
* **Grid size row** (grid view only): Choose thumbnail size — Small, Medium, or Large.
* **Bottom of the list:**
  * **Library info:** Number of imported folders/images and last sync time ("Not synced" if never run).
  * **Delete button:** Removes selected images from the list.

### 1.2 Edit Area (Right Side)
* **File name / Name row:** Edit the file name and display name.
* **Preview area:**
  * Preview size: Hidden / Standard / Compact / Full Screen ("Hidden" frees up room for metadata editing).
  * Star rating (★); navigate previous/next image.
* **Save / Slideshow row:**
  * **Save Changes** / **Save As** (saves as a separate file).
  * **Start/Stop Slideshow:** Cycles through images automatically; speed is adjustable.
* **Memo field:** Free-text per-image memo at the top of the edit area, used only within the app (no effect on prompt metadata) and fully searchable.
* **Metadata editing fields:** Below the memo field, in order: Model Used / Checkpoint, Prompt, Negative Prompt, Other Parameters / Metadata / EXIF Info. Each field (including memo) has Show/Hide, Copy, and Clear buttons on its heading row.

---

## 2. Basic Usage

### 2.1 Importing Images

**Supported formats:** PNG / JPG / JPEG / WEBP (on by default); GIF / BMP / TIFF (optional, enabled via checkboxes at the bottom of the import screen). A show/hide button at the left of that checkbox row can collapse it for more list space.

* **Import Folder:** Imports images directly inside the chosen folder (subfolders excluded). Choose import order — filename, reverse filename, creation date, or modification date, each ascending/descending. An "Also import images with identical content" checkbox (off by default) lets identical-content images be imported as separate records even under different filenames. This confirmation screen can be set, in Settings, to "Ask every time" or "Reuse last settings."
* **Import Images:** Imports individually chosen images via a file dialog — useful for importing only part of a folder.
* **Sync (🔄):** Rescans previously imported folders for newly added images. See [5. Folder Image Sync Rules](#5-folder-image-sync-rules).

Images imported with "Also import images with identical content" become separate, independently managed records — editing one (rating, name, prompt) does not affect the other, even though they look identical.

### 2.2 Supported Metadata Types

Generative AI metadata (e.g. prompts) is auto-detected by tool:

| Tool | Support Status |
|---|---|
| Stable Diffusion WebUI (Automatic1111 / Forge) | Automatically separates prompt, negative prompt, and other parameters |
| NovelAI | Same as above |
| ComfyUI | Workflow structures vary too widely for automatic extraction; the entire workflow (LoRA, batch size, etc.) is saved as-is in "Other Parameters / Metadata / EXIF Info" |

Six additional fields — Steps, Sampler, Scheduler, CFG scale, Seed, Size — can be shown individually below "Model Used" (toggle each in Settings; hidden by default).

**Camera EXIF:** If no AI generation parameters are found and the format supports EXIF (JPEG/TIFF/WEBP, etc.), the app reads camera EXIF data (manufacturer, model, date/time, exposure, F-number, ISO, focal length, GPS, etc.) into "Other Parameters / Metadata / EXIF Info," with a note in the prompt field. PNG, GIF, and BMP don't support EXIF this way.

### 2.3 Viewing and Organizing Images

* **Preview:** Selecting an image shows it on the right in one of four modes — Hidden, Standard, Compact, Full Screen. Full-screen still supports navigation and slideshow. Drag the preview out to an external app (e.g. Finder) to copy it. Click the preview to focus it, then use ←/→ to navigate (requires a click first, so focus won't shift accidentally from fields like search).
* **Star rating:** Hover to preview, click to set 0–5; click the same star again to clear.
* **Search:** Typing filters images across the "Name" field, actual file name (with extension), folder name, path, rating, creation/edit/import timestamps, file size, prompt, negative prompt, other metadata, and memo.
  * **AND:** space-separated keywords (`cat sunset`)
  * **OR:** `cat OR dog`
  * **Exclusion:** `-outdoor` excludes matches
  * **Phrase:** `"Untitled Folder 2"` matches as one unit
  * **Rating filter:** `star1`–`star5`, `★★★`, or a number like `3`
  * **Date range filter:** prefix `c:` (created) / `m:` (edited) / `i:` (imported), ranges joined by `..`, one side optional, at year/month/day granularity:
    * `c:2026-07` — created in July 2026
    * `c:2026-07-01..2026-07-31` — creation date in range
    * `i:2026-07-30..` — imported on/after July 30, 2026
    * `m:..2026-07` — edited on/before July 2026
    * Combines with other keywords as AND (e.g. `cat c:2026-07`)
  * Case and full-width/half-width differences are treated as equivalent.
  * Images in **collapsed** folders (under Group by Folder) are excluded from search — the heading shows "(excluded from search while collapsed)"; expand the folder to include them.
  * "No results" messaging varies by view: centered "0 search results" in normal list view; shown below each expanded folder's heading in grouped view; and, if all folders are collapsed, a one-time popup — "Please open the folder you want to search."
* **Sort:** By name, creation date, edit date, import date/time, rating, or file size, with independent ascending/descending toggle. The last sort setting persists across restarts. In list view, supplementary info matching the sort type (creation date, edit date, import date, or file size) is shown below the file name (creation date shown when sorting by name or rating).
* **List/Grid view:** In grid view, choose thumbnail size Small/Medium/Large ("Large" also shows location and creation date under each thumbnail).
* **Group by folder:** Groups images under folder headings in list view (disables grid view while active). Headings show folder name and image count. Click a heading to collapse/expand (▼/▶). **Right-click** a heading for "Edit folder order" (drag-and-drop reordering). **Drag** a heading onto Finder to copy the whole folder (always a copy, never moves/deletes the original). "Batch export images in folder (sequential rename)..." copies the folder's database-registered images to a chosen destination, renamed sequentially per the auto-numbering rule (unregistered stray files are excluded). "Set folder-specific auto-numbering..." overrides the app-wide prefix/digits/suffix for that folder (unchecking restores the default); this override applies to new imports and to "Batch rename"/"Batch export" on that folder's images. "Remove folder from database..." removes the folder and its images from the database (files on disk are untouched) and excludes it from future sync until re-imported via "Import Folder." Group view state, expand/collapse state, and folder order persist until next launch.

### 2.4 Viewing and Editing Metadata

* The Memo, Model Used / Checkpoint, Prompt, Negative Prompt, and Other Parameters / Metadata / EXIF Info fields show creation-time (or EXIF) data plus your memo.
* Each field's heading row has Show/Hide, Copy, and Clear buttons. Clearing or editing isn't finalized until "Save Changes" (safe from accidental changes).
* A bulk show/hide button at top right toggles all five editing fields plus the import-format checkbox row at once.
* "File Name" is the real file name; "Name" is an app-only display name — freely editable, duplicable, and usable like a search tag. New imports get an auto-numbered "Name" by default (e.g. CG_00001).

### 2.5 Saving, Duplicating, and Deleting Edits

* **Save Changes:** Saves name, rating, prompt, etc. With multiple images selected, you can batch-save just the rating.
* **Save As:** Saves edits as a new copy elsewhere, leaving the original untouched.
* **Edit lock:** Right-click an image → "Lock editing" to disable deletion and info changes, protecting against accidental edits.
* **Batch rename:** Select multiple images, right-click → "Batch rename selected images (sequential)...". Uses the Settings auto-numbering rule (prefix, digits, suffix) and renames only the **database "Name" field** — **the actual file name is unchanged** (use Batch export for that). Folder-specific rules take priority where set. Numbering starts at 1 via a counter dedicated to this operation (separate from the import counter); with `{folder name}` in prefix/suffix, numbering restarts per folder. Locked images are excluded. A confirmation popup previews example names first.
* **Batch export (sequential rename):** Right-click (multi-select supported) → "Batch export selected images (sequential rename)...". Choose a destination to create renamed **copies** (actual file names, including extension) per the auto-numbering rule, leaving originals untouched. Uses the same counter/`{folder name}` behavior as batch rename. Called "export" rather than "copy" to distinguish it from a plain Finder drag-and-drop (which keeps original names).
* With "Show edit screen when renaming" on, the confirm/edit screen labels rows "Current Name"/"New Name" (batch rename) or "Current File Name"/"New File Name" (batch export), clarifying which target is affected.
* **Delete:** "Remove selected images from list" removes them from the app only — files on disk are untouched, and deleted images won't reappear after a later "Sync" (see [5. Folder Image Sync Rules](#5-folder-image-sync-rules)).

### 2.6 Slideshow

"Slideshow" starts automatic playback, speed adjustable 0.5x–2x in 0.25 steps. If a search filter is active, only filtered images play.

### 2.7 Reading Mode (Spread View)

Displays two images from the same folder side by side, full-screen, like an open book. Launched from a button next to "Full Screen" in the preview area.

* **Requirements:** Available with "Group by folder" enabled, or while viewing images inside an album (otherwise grayed out).
* **Order:** Always "name order," regardless of the app's current sort.
* **Reading direction:** Toggle "Left-bound" (left to right) or "Right-bound" (right to left); toggling in spread view applies only to that session — change the default in Settings.
* **Page navigation:** Slider bar (moves by spread), first/last jump buttons, ←/→ keys, or clicking the screen's left/right edges (~15% width). Arrow/edge direction follows the current reading direction, not physical left/right (in right-bound mode, → goes back and ← advances).
* **Background toggle:** Button at the slider bar's left end switches dark/light background, independent of the app theme; remembered next time.
* **Center-aligned display:** Next button toggles page layout — normally each page is centered in its area; enabling this butts the pages together at screen center, like a real book/e-reader. Remembered next time.
* **Reading direction indicator:** ▶ Left-bound / ◀ Right-bound shown at top right.
* View-only — no editing. Press Esc or the exit button to leave.

---

## 3. Albums (Virtual Folders)

### 3.1 What Albums Are

Added in v1.4: group images into virtual "Albums" independent of disk folder structure. An image can belong to multiple albums. Normal list view and album view are mutually exclusive — switch via the toggle button (folder/album icon) at the top of the list.

### 3.2 Creating an Album

"Create an Album" opens a dialog combining the album name with that album's own auto-numbering rule.

* Enter a name (defaults to "Seed Book {next number}," freely editable).
* "Set a rule specific to this album" configures a prefix/digit count/append text used only by this album (off by default, in which case the app-wide default rule applies).
* Prefix/append fields support `{album name}` and `{date}` (today, YYYYMMDD) placeholders.
* Change the rule later via the header's right-click menu ("Album-Specific Auto-Numbering").

### 3.3 Adding Images to an Album

* **Right-click menu:** On an image (in the list or an album), choose "Add to Album" (pick existing) or "Create New Album..." (create on the spot). An auto-numbering rule enabled at creation applies immediately, even to a single image.
* **Drag-and-drop:** Drag images onto an album's header row in the sidebar.
* Both methods work the same with multiple images selected.

### 3.4 Working with an Album's Header Row

Behaves like the image list's "Group by folder" display.

* Click a header to expand/collapse (▼/▶).
* Right-click a header (or its "⋯" icon) for:
  * **Edit Order:** Reorder albums via drag-and-drop.
  * **Rename:** Change the album's name.
  * **Expand All / Collapse All.**
  * **Export Album Images as Renamed Copies (Sequential):** Copies the album's images to a chosen folder, renamed per its numbering rule.
  * **Album-Specific Auto-Numbering:** Set/change/clear this album's rule (see [3.2](#32-creating-an-album)).
  * **Delete Album:** Deletes the album container only — images inside are not deleted.

### 3.5 Where the Album-Specific Rule Applies

Once set, an album's rule takes priority for:

* "Export Album Images as Renamed Copies (Sequential)"
* "Bulk Rename Selected" and "Export Selected as Renamed Copies (Sequential)" on images inside that album (even for a single image)

It's independent of folder-specific and app-wide rules — never both applied to one operation. Albums can't be import sources, so they never affect import numbering.

### 3.6 Exporting to Finder and Filename Handling

Drag an album, or images inside one, onto Finder to export. Since albums have no real folder on disk, they're materialized into a temporary folder at drag time and handed to Finder.

**Original filenames are preserved and no numbering rule applies.** For numbered copies, use "Export Album Images as Renamed Copies (Sequential)" ([3.4](#34-working-with-an-albums-header-row)) instead.

### 3.7 Works with Search and Sorting

In album view, search filters within the currently open album (showing "No results found" or "Collapsed albums are excluded from search" below the header, as appropriate). Sort type and order carry over to album view.

---

## 4. Settings Screen

Opened from the gear icon at the top right.

<img width="296" height="537" alt="UI4" src="./design/screenshots/ui_settings_dark.png" />



* **Auto-numbering / Renaming:** "Auto-number on new import" toggles the feature. Off: the file name (minus extension) is used as "Name." On: set prefix, digit count, and suffix — numbering is independent per prefix+suffix combination and never reuses deleted numbers. Prefix/suffix support `{folder name}` and `{date}` (YYYYMMDD) placeholders, restarting numbering when either changes (Japanese UI shows `{フォルダ名}`/`{日付}`; behavior is identical either way). Clicking "Placeholders: {date} {folder name}" inserts into whichever field last had focus, with a separating "_" (trailing when inserted into a prefix, leading into a suffix). "Save auto-numbering rule" requires confirming a popup before it takes effect for future imports. "Reset numbering" resets the current combination's counter to 1 (confirmed first, since it may cause duplicate names). "Show edit screen when renaming" opens a review screen before batch rename/export, listing original → new names; selecting a row loads it into the "Name" field for editing, reflected back into the list. Duplicate or empty names are highlighted red and block execution. Off, the confirmation popup just shows a few example names.
* **Displayed fields:** Toggle Steps, Sampler, Scheduler, CFG scale, Seed, and Size individually.
* **Appearance mode:** Auto (follow OS) / Dark / Light. Also toggle panel arrangement — Standard (search/list left) or Reversed (search/list right); the settings button stays top right either way.
  * Both are also toggleable via buttons at the top right of the window (next to the bulk show/hide button), without opening Settings — the panel button flips standard/reversed each press, and the appearance button cycles Auto → Dark → Light → Auto (icons make the current state clear). These share state with the Settings screen equivalents.
* **Display language:** Auto (follow OS) / Japanese / English. Takes effect on next launch (requires restart). "Auto" uses Japanese if the OS is set to Japanese, English otherwise.
* **Folder import order:** Confirm order every import, or reuse the last-used order automatically.
* **Reading mode defaults:** Default reading direction (Left-bound/Right-bound) and whether center-aligned display starts on (see [2.7](#27-reading-mode-spread-view)).
* **Database:**
  * **View/switch active database:** Select from the list, click "Switch Database" to restart and switch automatically. The folder icon opens the database storage folder in Finder (Explorer on Windows).
  * **Create Database:** Create additional databases inside `~/Library/Application Support/AIImageViewer/` (`image_metadata.db`, `image_metadata2.db`, ...). Creating one doesn't switch to it — select it from the list to activate.
  * **Image list (CSV):** Exports the active database's image list, as "basic info only" or "including prompt and other metadata."
  * **Sync history (CSV):** Exports the sync history log (missing folders/images, import errors). See [5.6](#56-sync-history).
  * **Reset Database:** Deletes all image/folder records from the active database (files on disk and app settings are preserved).
  * **When no database is found:** At launch, if no database file exists at the default location (first launch, or a deleted file), a selection popup appears: "Create a new empty database" (default — fine for first-time use), "Choose a different database in the same storage folder," or "Load from an external backup file." Loading an external file validates it, copies it into the default storage location as a new database, and confirms. See [6. Data Backup and Migration](#6-data-backup-and-migration) for details.
    A "Load sample data" checkbox appears only when "Create a new empty database" is selected — it imports dummy sample images (not real AI-generated content) so you can try import and metadata display; delete them like any other image afterward.
* **Reset all these settings:** Restores naming rules, displayed fields, and theme settings to defaults (auto-numbering counters are not reset).

---

## 5. Folder Image Sync Rules

Folders imported via "Import Folder" have their paths remembered and can be rescanned with the "🔄 Sync" button. This section covers the logic involved.

"Name" here means the folder/file's original name — not the app's internal Name field (e.g. CG001).

### 5.1 Conditions for Being Included in Re-sync

The sole condition: the path must exactly match the absolute path remembered at import.

Outside the app (e.g. in Finder):

* Renaming a folder → path changes → excluded
* Moving a folder → path changes → excluded
* Same for renaming/moving an individual image file

💡 "Renamed" and "moved" both reduce to the same state: "no longer matches the remembered path."

### 5.2 How Excluded Images Appear in the Image List

The app checks whether registered files exist at their recorded paths (at launch and on "Sync"), and the list reflects the result.

* A missing file is not shown in the image list.
* This updates automatically as soon as the folder changes, even without pressing Sync.
* The database record isn't deleted yet at this point — merely hidden.
* A temporary status-bar notice appears: "○○ image file(s) could not be found and are not being shown (an external drive may not be connected)" — a hint for cases where files just live on an unmounted drive.

### 5.3 Handling in the Database (Important)

"🔄 Sync" both imports new images and permanently deletes database records for images that no longer exist.

| Timing | Image list display | Database record |
|---|---|---|
| Immediately after path change (before Sync) | Not shown | Still present (hidden) |
| After running "Sync" | Not shown | Deleted (cannot be undone) |

Once Sync runs, any images with an invalid path at that moment are permanently deleted.

### 5.4 How to Restore (Undo)

**Pattern A — Sync not yet run:** Restoring the folder's name/location makes the images reappear automatically next time the list opens. No re-import needed.

**Pattern B — Sync already run:** Records are already deleted, so restoring the folder alone won't bring them back — re-import via "Import Folder" or "Import Images." This registers them as new images, losing:
* Rating (★)
* Edit lock state
* Any custom "Name" (a new auto-numbered name is assigned)
* Saved edits such as prompts

### 5.5 Summary (In Short)
* Before pressing Sync, moving/renaming a folder is fully reversible.
* After pressing Sync, any images with an invalid path at that time are permanently gone.
* If you're mid-move/rename, avoid pressing Sync until you've restored the folder.

### 5.6 Sync History
Each "Sync" automatically records any folders/images not found, or import errors.

* **Popup only on first occurrence:** Recurring identical issues show a popup only once; later occurrences are logged silently, not popped up again.
* **Re-warned if it recurs:** Once a folder reappears even briefly, the warning state resets — if it goes missing again, you're warned again (accounts for intentional moves or drive plug/unplug).
* **Viewing history:** "History" on the sync results popup shows date/time, type, target path, and details; only the latest record is kept per identical entry.
* **Exporting to CSV:** From the history dialog, or "Sync History (CSV)" in Settings.
* **Retention:** Up to 500 most recent entries; older ones are deleted automatically.

---

## 6. Data Backup and Migration

### 6.1 About the Selection Dialog When No Database Is Found
At launch, if no database file exists at the default location (first launch, or a deleted file), a selection popup appears (see [4. Settings Screen](#4-settings-screen)).

**For normal use, choose "Create a new empty database"** — the default; first-time users can just press OK. "Choose a different database in the same storage folder" and "Load from an external backup file" are special cases for restoring previously used data.

### 6.2 Database Storage Location
App data (registered images, prompts, ratings, settings) is stored at:

```
~/Library/Application Support/AIImageViewer/
```

This folder holds `image_metadata.db` (default) and any additional databases you create (`image_metadata2.db`, ...). **Image files themselves are not stored here** (they stay in their original import folders). Back up and migrate this folder's contents.

### 6.3 How to Back Up
1. In Finder, "Go" → "Go to Folder...", enter `~/Library/Application Support/AIImageViewer/`.
2. Copy the folder's contents (`.db` files) to an external drive, cloud storage, or similar.

Back up periodically, or before/after major editing work.

### 6.4 Notes on Uninstalling / Reinstalling the App
Deleting the app (`.app`) does not delete the `~/Library/Application Support/AIImageViewer/` folder. Reinstalling on the same Mac and user account finds your existing database automatically.

To delete everything including your data, manually delete this folder too.

### 6.5 Migrating to a Different Environment (a Different Mac or User Account)
1. On the source machine, copy the `.db` files from `~/Library/Application Support/AIImageViewer/` (see 6.3).
2. Launch the app once on the destination machine (the "no database found" dialog appears).
3. Choose "Load from an external backup file" and select the copied `.db` file.
4. Once loaded, it's duplicated as a new database with a confirmation notice.

**Note:** Image files aren't included in the database. Unless the source import folders exist at the same paths on the destination machine, the image list will show "missing files." Where possible, migrate both the image folders and the database together.

---

## 7. Known Limitations

**Drag-and-drop import is temporarily disabled**

Importing images by dragging them from an external app (e.g. Finder) directly into the image list is temporarily disabled due to unstable behavior. Use "Import Folder" or "Import Images" instead.
