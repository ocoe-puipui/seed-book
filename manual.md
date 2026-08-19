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


This app consists of two panes — the "List Display Area" on the left and the "Edit Area" on the right — plus a "Settings" screen.

### 1.1 List Display Area (Left Side)
* **Search / Settings row:**
  * **Search field:** Filters images by any keyword.
  * **Settings button (gear icon):** Opens the app's various settings dialogs.
* **Import / Sync row:**
  * **Import Folder:** Imports all images inside a specified folder at once.
  * **Import Images:** Imports specified individual image files.
  * **Sync button (🔄 icon):** Syncs with the current state of the folder.
* **Folder/Album toggle row:**
  * **Folder / Album toggle button:** Switches between the normal image list view and album view (see [3. Albums (Virtual Folders)](#3-albums-virtual-folders)). While in album view, a "Create an Album" button is also shown.
* **Sort / Display toggle row:**
  * **Sort / Ascending-Descending toggle:** Changes the display order of the image list. "By Filename" (based on the actual file name) and "By Name" (based on the app's own "Name" field) are separate, distinct options.
  * **List/Grid display toggle button:** Switches between list view and grid (thumbnail) view.
  * **Group by folder toggle button:** Switches to grouping images by folder.
* **Grid size selection row** (shown only while in grid view):
  * Choose thumbnail size from "Small," "Medium," or "Large."
* **Bottom of the list:**
  * **Library info:** Shows the number of imported folders and images, and the date/time of the last sync (displays "Not synced" if a sync has never been run).
  * **Delete button:** Removes the selected images from the list.

### 1.2 Edit Area (Right Side)
* **File name / Name row:** Edit the image's file name and display name.
* **Preview area:**
  * Change the preview size (Hidden / Standard / Compact / Full Screen). Choosing "Hidden" hides the image preview, giving you more room for the metadata editing area.
  * Assign a star rating (★).
  * Navigate to the previous / next image.
* **Save / Slideshow row:**
  * **Save Changes:** Saves your edits.
  * **Save As:** Saves as a separate file.
  * **Start/Stop Slideshow:** Runs a slideshow that automatically cycles through images. Playback speed can also be adjusted.
* **Memo field:** A free-text memo field for each image, located at the top of the edit area. This information is used only within the app and has no effect whatsoever on metadata such as prompts. Its contents are also searchable.
* **Metadata editing fields:**
  * Below the memo field, you can view and edit AI-image-specific information in this order: "Model Used / Checkpoint," "Prompt," "Negative Prompt," and "Other Parameters / Metadata / EXIF Info."
  * Each field, including the memo field, has a "Show/Hide button," "Copy," and "Clear this field" available on its heading row.

---

## 2. Basic Usage

### 2.1 Importing Images

**Supported formats:** PNG / JPG / JPEG / WEBP (enabled by default), GIF / BMP / TIFF (optional, disabled by default; can be enabled via checkboxes at the bottom of the import screen). The show/hide button at the left edge of this checkbox row can also be used to temporarily collapse the row, giving the list display area more room.

* **Import Folder:** When you select a folder, the images directly inside it are imported together (subfolder contents are not included). At import time, you can choose the import order from filename order, reverse filename order, creation date order, or modification date order (each ascending or descending). A "Also import images with identical content" checkbox (off by default) at the bottom of the same screen lets you choose whether to deliberately import images whose content is exactly identical (even if the filenames differ) as separate records. This confirmation screen itself can be switched, from the settings screen, between "Ask every time" and "Automatically use the same settings as last time."
* **Import Images:** Imports individually selected images from a file selection dialog. Useful when you want to import only some images rather than an entire folder.
* **Sync (🔄):** Rescans previously imported folders and imports any newly added images. For detailed sync rules, see "[5. Folder Image Sync Rules](#5-folder-image-sync-rules)."

**About importing images with identical content:** Images imported with "Also import images with identical content" turned on are registered as separate, independent images. They will look the same (thumbnail/preview), but their rating, name, and prompt edits are managed individually — changing one will not affect the other.

### 2.2 Supported Metadata Types

Generative AI information embedded in images (such as prompts) is automatically detected based on the type of tool used.

| Tool | Support Status |
|---|---|
| Stable Diffusion WebUI (Automatic1111 / Forge) | Automatically separates and displays the prompt, negative prompt, and other parameters |
| NovelAI | Same as above |
| ComfyUI | Because workflow structures vary widely, automatic prompt extraction is not performed. The entire workflow (including settings such as LoRA and batch size) is saved as-is in the "Other Parameters / Metadata / EXIF Info" field |

In addition, the six items Steps, Sampler, Scheduler, CFG scale, Seed, and Size can be displayed as individual fields below the "Model Used" field (whether each is shown can be toggled per item in the settings screen; hidden by default).

**About EXIF information from camera photos:** If none of the AI generation parameters above are found, and the format inherently carries EXIF data (JPEG/TIFF/WEBP, etc.), the app automatically reads camera-derived EXIF information — manufacturer, model, date/time taken, exposure time, F-number, ISO sensitivity, focal length, GPS coordinates, and so on — and displays it, formatted, in the "Other Parameters / Metadata / EXIF Info" field (the prompt field will show a note explaining this). PNG, GIF, and BMP do not support EXIF reading via this method.

### 2.3 Viewing and Organizing Images

* **Preview:** Selecting an image displays it on the right side. You can switch among four display modes: "Hidden," "Standard," "Compact," and "Full Screen." "Hidden" is used when you want to hide the preview image and expand the metadata editing area. Even in full-screen mode, you can still navigate between images, run the slideshow, and adjust playback speed. You can also drag and drop the preview image out to an external app such as Finder to extract (copy) it. Once you click the preview area to give it focus, you can then also navigate to the previous/next image using the left/right arrow keys (this only activates after a click, so focus won't shift accidentally from other input fields such as the search box).
* **Star rating:** Hovering over the stars previews the rating; clicking sets a rating from 0 to 5. Clicking the same star again clears the rating.
* **Search:** Typing a keyword into the search field filters the images. The following fields are searched together (across the board):
  * The "Name" field, the actual file name (including extension), folder name, location (path), rating, creation/edit/import dates and times, file size, prompt, negative prompt, other metadata, and the memo field
  * **AND search:** Entering multiple space-separated keywords narrows results to images containing all of them (e.g., `cat sunset`).
  * **OR search:** Placing `OR` between keywords matches images containing either one (e.g., `cat OR dog`).
  * **Exclusion search:** Prefixing a keyword with `-` excludes images containing that term (e.g., `cat -outdoor`).
  * **Phrase search:** Enclosing text in `"..."` treats a phrase containing spaces as a single unit (e.g., `"Untitled Folder 2"`).
  * **Filter by rating:** You can filter by rating using `star1` through `star5`, star marks like `★★★`, or numeric values like `3`.
  * **Filter by date range:** Specify the type of date with a prefix (`c:` created / `m:` edited / `i:` imported). Ranges are separated with `..`, and you can specify only one side of the range, at year, year-month, or year-month-day granularity.
    * `c:2026-07` … images created in July 2026
    * `c:2026-07-01..2026-07-31` … creation date within the range
    * `i:2026-07-30..` … imported on or after July 30, 2026
    * `m:..2026-07` … edited on or before July 2026
    * Combined with other keywords, this becomes an AND condition (e.g., `cat c:2026-07`).
  * Differences in uppercase/lowercase and full-width/half-width characters are automatically treated as equivalent, so either form produces the same results.
  * Note that images in folders that are **collapsed** under "Group by Folder" display are excluded from search (the heading row shows "(excluded from search while collapsed)"). To search them, click the heading to expand the folder.
  * The message shown when a search returns no matching images differs depending on the display mode. In all cases, the folder heading (folder icon) remains visible.
    * **Normal list view:** "0 search results" is shown in the center of the list.
    * **Group by folder view:** "0 search results" is shown below the heading of any open (expanded) folder.
    * **When all folders are collapsed:** Since no folder is searchable, a one-time popup appears saying "Please open the folder you want to search" (opening a folder or clearing the search will cause it to be shown again next time).
* **Sort:** You can sort by name, creation date, edit date, import date/time, rating, or file size, with ascending/descending toggled independently via a separate button. The last-used sort setting is remembered even after restarting the app. In list view, supplementary information (creation date, edit date, import date, or file size) matching the selected sort type is shown below the file name (creation date is shown when sorting by name or rating).
* **List/Grid view:** Switches between list view and thumbnail grid view. In grid view, you can choose the thumbnail size from "Small," "Medium," or "Large" (choosing "Large" also shows the location and creation date below each thumbnail).
* **Group by folder:** While in list view, you can group images under headings by folder (while enabled, switching to grid view is not available). The heading row shows the folder name and the number of images in that folder (as a number only). Clicking a heading row collapses/expands that folder's image list (▼ indicates expanded, ▶ indicates collapsed). **Right-clicking** a heading row shows an "Edit folder order" menu, letting you reorder folders via drag and drop. **Dragging and dropping** a heading row onto an external app such as Finder copies the entire folder (the real folder on disk) — as with dragging out a preview image, this is always a "copy" only; the original folder is never moved or deleted. Choosing "Batch export images in folder (sequential rename)..." from the right-click menu lets you specify a destination folder and copy the folder's images that are registered in the database, renaming them sequentially according to the auto-numbering rule (files not registered in the database that happen to be present are excluded). Choosing "Set folder-specific auto-numbering..." lets you override the app-wide default prefix, digit count, and suffix for that folder specifically (unchecking the checkbox restores the default). This override takes priority not only for newly imported images, but also when running "Batch rename selected images" or "Batch export" on images in that folder. Choosing "Remove folder from database..." removes that folder and its images from the database together (the actual files on disk are not deleted). After removal, the folder no longer appears in the image list and is also excluded from future sync (auto rescan). Importing it again via "Import Folder" brings it back into the sync target set. The on/off state of group view, its collapsed/expanded state, and folder order are all remembered until the next launch.

### 2.4 Viewing and Editing Metadata

* In the "Memo," "Model Used / Checkpoint," "Prompt," "Negative Prompt," and "Other Parameters / Metadata / EXIF Info" fields on the right, you can view and edit information generated at creation time (or EXIF information, in the case of camera photos) as well as your memo.
* Three buttons on each field's heading row let you "toggle show/hide," "copy," and "clear this field," respectively. Clearing a field or editing a prompt is not finalized until you click "Save Changes" (so accidental operations are safe).
* The bulk show/hide button at the top right of the screen lets you show or hide all five of these editing fields, plus the import-format checkbox row, together at once.
* "File Name" is the actual file name on your computer, while "Name" is a display name used only within the app. "Name" can be freely changed independently of the actual file name, can be duplicated, and can even be used like a search tag. Newly imported images are, by default, given an auto-numbered "Name" (e.g., CG_00001).

### 2.5 Saving, Duplicating, and Deleting Edits

* **Save Changes:** Saves edits such as name, rating, and prompt. When multiple images are selected, you can batch-save just the rating.
* **Save As:** Leaves the original file unchanged and saves your edits as a new copy at a location you specify.
* **Edit lock:** Right-clicking an image lets you "Lock editing." While locked, deletion and information changes (name, rating, prompt, etc.) are disabled, protecting the image from accidental edits.
* **Batch rename:** Selecting multiple images and right-clicking shows "Batch rename selected images (sequential)...". This uses the auto-numbering rule (prefix, digit count, suffix) from the settings screen as-is, and aligns only the **"Name" field in the database** to a sequential numbering. **The actual file name on your computer is not changed** (if you also want to align the actual file name, use "Batch export" instead). For images in a folder that has folder-specific auto-numbering set, that folder's rule takes priority. Numbers are assigned starting from 1 using a temporary counter dedicated to this operation, and do not affect the auto-numbering counter used at import time. If the prefix or suffix includes `{folder name}`, numbering starts from 1 separately for each folder. Images with edit lock enabled are excluded. Before execution, a confirmation popup is shown with example resulting names.
* **Batch export (sequential rename):** Right-clicking an image (multiple selection supported) shows "Batch export selected images (sequential rename)...". Choosing a destination folder creates copies whose **actual file names** are renamed sequentially according to the auto-numbering rule (including extension), leaving the original files untouched. This uses the same temporary counter and `{folder name}` support as batch rename, so the behavior is conceptually the same. The wording "export" rather than "copy" is used to distinguish this from dragging and dropping onto Finder (which duplicates files under their original names).
* When "Show edit screen when renaming" is on, the confirmation/edit screen shows "Current Name" / "New Name" for batch rename, and "Current File Name" / "New File Name" for batch export, making it clear which target (the database "Name" or the actual file name) is being changed in each case.
* **Delete:** Clicking "Remove selected images from list" excludes the images from the app's list. The actual image files on your computer are not deleted. Deleted images do not automatically reappear even after a subsequent "Sync" (for details, see "[5. Folder Image Sync Rules](#5-folder-image-sync-rules)").

### 2.6 Slideshow

The "Slideshow" button starts automatic playback. Playback speed can be adjusted from 0.5x to 2x in increments of 0.25. Starting a slideshow while a search filter is active will cycle through only the filtered images.

### 2.7 Reading Mode (Spread View)

A mode that displays two images from the same folder as the selected image side by side, full-screen, like an open book. It is launched from a dedicated button next to the "Full Screen" button in the preview area.

* **Requirements:** Available while "Group by folder" display is enabled, or while viewing images inside an album in album view (the button is grayed out otherwise).
* **Order:** Regardless of the app's current sort setting, images are always displayed in "name order."
* **Reading direction:** You can switch between "Left-bound (read left to right)" and "Right-bound (read right to left)." Changes made via the toggle button while in spread view apply only for that session; change the default from the settings screen.
* **Page navigation:** Supported via the slider bar at the bottom of the screen (moves by spread), jump buttons to the first/last spread, the left/right arrow keys, and clicking the left/right edges of the screen (about 15% of the width). The direction that the arrow keys or edge clicks advance/go back follows the current "reading direction," not the physical left/right of the screen (in right-bound mode, the → key goes back and the ← key advances).
* **Background toggle:** The button at the left end of the slider bar switches the reading mode background between dark and light. This is independent of the app's overall theme setting and is remembered the next time you open this mode.
* **Center-aligned display:** The button next to the background toggle button switches how the left and right pages are arranged. Normally, each page is centered within its display area; turning this on displays the left and right pages butted together at the center of the screen, as in an actual book or e-reader. This setting is saved each time you toggle it and remembered the next time you open this mode.
* **Current reading direction indicator:** The current reading direction (▶ Left-bound / ◀ Right-bound) is always shown at the top right of the screen.
* This mode is view-only; editing of prompts and other data is not possible. Press "Esc" or the exit button to return to normal display.

---

## 3. Albums (Virtual Folders)

### 3.1 What Albums Are

A feature (added in v1.4) that lets you freely group images into virtual "Albums," independent of your actual folder structure on disk. A single image can belong to multiple albums at once. The normal image list view and album view are mutually exclusive — use the toggle button at the top of the list (folder icon / album icon) to switch between them.

### 3.2 Creating an Album

Clicking "Create an Album" opens a dialog that combines the album name field with a setting for that album's own auto-numbering rule.

* Enter an album name (defaults to "Seed Book {next number}," but can be changed freely).
* Checking "Set a rule specific to this album" lets you configure an auto-numbering rule (prefix, digit count, append text) used only by this album, right on the spot. It's off by default, in which case the app-wide default rule (from the "Auto-Numbering / Renaming" section in Settings) is used.
* The prefix/append fields support the `{album name}` and `{date}` (today's date, YYYYMMDD) placeholders.
* The rule can always be changed later from the header's right-click menu ("Album-Specific Auto-Numbering").

### 3.3 Adding Images to an Album

* **Via the right-click menu:** Right-click an image (in the normal list or inside an album) and choose "Add to Album" to pick an existing album, or "Create New Album..." to create one on the spot while adding. If you enable the auto-numbering rule in the creation dialog, it will be applied immediately even if you're only adding a single image.
* **Via drag-and-drop:** You can also drag images directly onto an album's header row in the sidebar to add them.
* Both methods work the same way with multiple images selected at once.

### 3.4 Working with an Album's Header Row

Album view behaves the same way as the image list's "Group by folder" display.

* Click a header row to expand or collapse that album's images (shown via ▼/▶).
* Right-click a header row (or click the faint "⋯" icon at its right edge) to open its menu:
  * **Edit Order:** Reorder albums via drag-and-drop.
  * **Rename:** Change the album's name.
  * **Expand All / Collapse All:** Expand or collapse every currently shown album at once.
  * **Export Album Images as Renamed Copies (Sequential):** Copies the album's images to a folder you choose, renaming them sequentially according to the numbering rule.
  * **Album-Specific Auto-Numbering:** Set, change, or clear this album's own numbering rule (see [3.2](#32-creating-an-album)).
  * **Delete Album:** Deletes the album itself (the images inside it are not deleted — only the "container" is removed).

### 3.5 Where the Album-Specific Rule Applies

Once set, an album's own auto-numbering rule takes priority in:

* "Export Album Images as Renamed Copies (Sequential)" from the header menu
* "Bulk Rename Selected" and "Export Selected as Renamed Copies (Sequential)" when selecting images inside that album (this works even with a single image selected)

It is fully independent of folder-specific rules and the app-wide default rule — the two are never both applied to the same operation. Since an album can never be an import source, it has no effect on numbering during import.

### 3.6 Exporting to Finder and How Filenames Are Handled

You can also drag an album, or images inside an expanded album, directly onto Finder (Explorer) to export them. Since an album has no real folder on disk, it is materialized into a temporary folder at drag time and handed to Finder as a regular folder.

With this method, **the original filenames are preserved as-is and no numbering rule is applied.** If you want a numbered copy, use "Export Album Images as Renamed Copies (Sequential)" described in [3.4](#34-working-with-an-albums-header-row) instead.

### 3.7 Works with Search and Sorting

While in album view, the search box filters images within whichever album is currently open (as with the normal image list, "No results found" or "Collapsed albums are excluded from search" is shown below the header as appropriate). Sort type and ascending/descending order also carry over to album view.

---

## 4. Settings Screen

Opened from the gear icon at the top right of the screen.

<img width="296" height="537" alt="UI4" src="./design/screenshots/ui_settings_dark.png" />



* **Auto-numbering / Renaming:** The "Auto-number on new import" checkbox toggles the feature itself on/off. When off, the actual file name (minus extension) is used as-is for "Name" instead of auto-numbering. When on, you can set the prefix, digit count, and a suffix string appended at the end. Numbering is independent for each prefix+suffix combination, and numbers are not reused even after deletion. The prefix and suffix can include the placeholders `{folder name}` (the source import folder's name) and `{date}` (today's date, YYYYMMDD); when the folder or date changes, numbering is automatically managed as a separate sequence (if inserted from the Japanese UI, these appear as `{フォルダ名}`/`{日付}`, but the meaning and behavior are identical, and both notations work regardless of the display language). Clicking the "Placeholders: {date} {folder name}" link inserts the placeholder, with a "_" separator, directly into whichever prefix/suffix field last had the cursor (no manual typing needed). Inserting into the prefix field appends a trailing "_" (e.g., `{folder name}_`), while inserting into the suffix field prepends a leading "_" (e.g., `_{date}`). Clicking "Save auto-numbering rule" shows a confirmation popup asking "Save the new rule? (This will apply to numbering for new imports from now on)," which is not finalized until you choose "Yes." "Reset numbering" lets you reset the number for the current combination back to 1 (since this could cause duplicate names with past images, a confirmation is shown before proceeding). Turning on "Show edit screen when renaming" opens an edit screen before batch rename or batch export runs, letting you review a list of the names that will be generated (original file name / new name). Selecting a row in the list loads that row's name into the "Name" field below, and edits made there are reflected back into the list (this is not a method of editing table cells directly). Rows with duplicate or empty names are highlighted in red, and execution is blocked until resolved. When this option is off, execution proceeds as before, with the confirmation popup simply showing a few example names.
* **Displayed fields:** Individually toggle the display of Steps, Sampler, Scheduler, CFG scale, Seed, and Size via checkboxes per item.
* **Appearance mode:** Choose from "Auto (follow OS setting)," "Dark," or "Light." In the same group, you can also toggle the left/right panel arrangement ("Standard" = search/list on the left, "Reversed" = search/list on the right). Even when reversed, the settings button remains fixed at the top right of the window.
  * Both of these can also be toggled with one click from buttons at the top right of the window (the two buttons next to the bulk show/hide button), without opening the settings screen. The panel-reverse button toggles between standard and reversed each time it's pressed, and the appearance-mode button cycles through "Auto → Dark → Light → Auto…" each time it's pressed (a dedicated icon is shown for "Auto" while following the OS, and an icon matching the current look is shown for fixed Dark/Light, so the current state is clear at a glance). This setting shares the same underlying value as the corresponding item in the settings screen, so changing it from either place updates both.
* **Display language:** Choose the app's display language from "Auto (follow OS language setting)," "Japanese," or "English." Your choice takes effect starting the next time you launch the app (an app restart is required; it does not apply immediately at the point of switching). If you choose "Auto," the UI will be in Japanese if the OS language setting is Japanese, and in English otherwise.
* **Folder import order:** Choose whether to confirm the order every time you import a folder, or to automatically use the order used last time.
* **Reading mode defaults:** Choose the default reading direction ("Left-bound" or "Right-bound") and whether center-aligned display is on by default (for how to use reading mode itself, see "[2.7 Reading Mode (Spread View)](#27-reading-mode-spread-view)").
* **Database:**
  * **View/switch the currently active database:** Select from the list and click "Switch Database" to have the app automatically restart and switch. Clicking the folder icon to the right of the display opens the folder where database files are stored, in Finder (Explorer on Windows).
  * **Create Database:** You can create multiple databases for different purposes, inside the app's data storage folder (`~/Library/Application Support/AIImageViewer/`) (`image_metadata.db`, `image_metadata2.db`, ...). After confirmation, a new empty database is created (creating one does not switch to it automatically — select it from the list again to switch).
  * **Image list (CSV):** Exports a list of images registered in the currently active database to a CSV file. You can choose "basic info only" or "include prompt and other metadata."
  * **Sync history (CSV):** Exports the history of folders/images not found, or import errors, recorded during "Sync" operations, to a CSV file. For details, see "[5.6 Sync History](#56-sync-history)."
  * **Reset Database:** Deletes all image and remembered folder information from the currently active database. The actual image files on your computer, and other app settings, are preserved.
  * **When no database is found:** If, at app launch, no database file is found at the default storage location (`~/Library/Application Support/AIImageViewer/`) — such as on first launch, or if the file was deleted directly — the app does not automatically create a new one; instead a selection popup is shown. You can choose from "Create a new empty database" (selected by default; if this is your first time using the app, you can simply proceed with this), "Choose a different database in the same storage folder," or "Load from an external backup file." If you load an external file, its validity is checked, it is then copied as a new database into the default storage location, and you are notified accordingly. For detailed backup/migration steps, see "[6. Data Backup and Migration](#6-data-backup-and-migration)."
    A "Load sample data" checkbox is shown only when "Create a new empty database" is selected. Checking it also imports pre-prepared sample images (not actual AI-generated images, but dummy images created to let you try out import and metadata-display behavior), so you can try out how the app works. They can be deleted like any other image once no longer needed.
* **Reset all these settings:** Restores naming rules, displayed fields, theme settings, and so on to their defaults (the auto-numbering counters themselves are not reset).

---

## 5. Folder Image Sync Rules

Folders imported via "Import Folder" have their paths remembered, and can be rescanned using the "🔄 Sync" button. This section summarizes the judgment logic and behavior involved.

Note that "name," as used in this explanation, refers to the original name of a folder or file — not the app's internal name field (the auto-numbered display such as CG001, CG002).

### 5.1 Conditions for Being Included in Re-sync

The sole condition is whether the path exactly matches the absolute path that was remembered at import time.

Using Finder as an example of operations performed outside this application:

* If you rename a folder → the path changes, so it becomes excluded
* If you move a folder to a different location → the path changes, so it becomes excluded
* The same applies if you rename or move an image file itself

💡 Both "renamed" and "moved" ultimately amount to the same single state: "no longer matches the remembered path."

### 5.2 How Excluded Images Appear in the Image List

The app checks whether registered image files actually exist at their recorded paths (checked at launch and when "Sync" is run, with the list display based on the result).

* If a file does not exist, that image is not shown in the image list
* This is reflected automatically as soon as you change the folder, even without pressing the "Sync" button
* However, at this point the database record has not yet been deleted (it is merely "hidden" temporarily)
* When images are missing and excluded from the list, a temporary notice appears in the status bar at the bottom of the screen: "○○ image file(s) could not be found and are not being shown (an external drive may not be connected)." This is meant to help you notice cases where images stored on an external drive merely appear to be missing because the drive isn't connected.

### 5.3 Handling in the Database (Important)

The "🔄 Sync" button not only imports new images but also plays the role of permanently deleting, from the database, records for images that no longer exist.

| Timing | Image list display | Database record |
|---|---|---|
| Immediately after path change (sync not yet run) | Not shown | Still present (merely hidden temporarily) |
| After running "Sync" | Not shown | Deleted (cannot be undone) |

Once "Sync" has been run even once, any images whose path is invalid at that time are permanently deleted.

### 5.4 How to Restore (Undo)

#### Pattern A: "Sync" has not yet been run
Restoring the folder's name/location to how it was will automatically make the images reappear the next time you open the image list. No re-import operation is needed.

#### Pattern B: "Sync" has already been run
Because the database records have already been deleted, restoring the folder will not bring them back automatically. You will need to re-import using "Import Folder" or "Import Images."

In that case, the following information is lost and the images are registered anew as new images:
* Rating (★)
* Edit lock state
* Any custom name you had set in the "Name" field (a new auto-numbered name will be assigned)
* Saved edits such as prompts

### 5.5 Summary (In Short)
* As long as you don't press the sync button, moving or renaming a folder is fully reversible — the images come back once you restore it.
* Once you press "Sync," any images with an invalid path at that time are permanently deleted, with no way back.
* While you're planning to move or rename a folder, it's safest not to press "Sync" until you've restored it.

### 5.6 Sync History
Each time you press the "Sync" button, any folders/images that could not be found, or import errors, are automatically recorded.

* **Popup shown only on first occurrence:** While the same issue persists (the same folder not found, the same import error content), the popup warning is shown only the first time. From the second occurrence onward, no popup is shown — it is only recorded in the history (so you won't be shown the same warning popup endlessly on every sync).
* **Warned again if the issue recurs:** Once a folder is found again even briefly, the warning state is reset. If it then goes missing again, you will be warned again via popup (this behavior accounts for intentional folder moves, or plugging/unplugging external drives).
* **Viewing the history:** Clicking the "History" button on the sync results popup shows a list of previously recorded sync history (date/time, type, target path, details). Only the most recent record is kept for identical entries.
* **Exporting to CSV:** You can export to a CSV file from within the history dialog, or from "Sync History (CSV)" in the settings screen.
* **Retention:** Up to the most recent 500 history entries are kept; anything beyond that is automatically deleted starting with the oldest.

---

## 6. Data Backup and Migration

### 6.1 About the Selection Dialog When No Database Is Found
If, at app launch, no database file is found at the default storage location (such as on first launch, or if the file was deleted directly), a selection popup is shown (see the explanation in "[4. Settings Screen](#4-settings-screen)" for details).

**For normal use, choose "Create a new empty database."** This is the default selection, and if you're using the app for the first time, you can simply press "OK" as-is. "Choose a different database in the same storage folder" and "Load from an external backup file" are special-case options intended only for when you want to restore previously used data.

### 6.2 Database Storage Location
This app's data (registered image information, prompts, ratings, settings, etc.) is stored in the following folder:

```
~/Library/Application Support/AIImageViewer/
```

Inside this folder are `image_metadata.db` (the default database) and, if you've created additional ones, files such as `image_metadata2.db`. **The image files themselves are not stored here** (the app manages them in place, in their original import folders). What you need to back up and migrate is the contents of this folder.

### 6.3 How to Back Up
1. From the Finder menu, choose "Go" → "Go to Folder...", then enter and open `~/Library/Application Support/AIImageViewer/`.
2. Copy the contents of the folder (the `.db` files, such as `image_metadata.db`) to any location of your choice, such as an external drive or cloud storage.

It's recommended to back up periodically, or before and after major editing work.

### 6.4 Notes on Uninstalling / Reinstalling the App
Deleting the app itself (the `.app`) does not automatically delete the `~/Library/Application Support/AIImageViewer/` folder mentioned above. If you reinstall and launch on the same Mac under the same user account, your existing database will still be found and you can continue using the app as before.

If you want to delete everything, including your data, you must manually delete this folder in addition to the app itself.

### 6.5 Migrating to a Different Environment (a Different Mac or a Different User Account)
1. On the source machine, follow the steps in 5.3 above to copy the contents (`.db` files) of `~/Library/Application Support/AIImageViewer/`.
2. Launch this app once on the destination machine (the "no database found" selection dialog will appear).
3. In the dialog, choose "Load from an external backup file" and specify the `.db` file you copied.
4. Once loading completes, it is duplicated as a new database and a notification is shown.

**Note:** The image files themselves are not included in the database. Unless you also set up the source import folders with the same path structure on the destination machine, "missing files" will remain in the image list. Where possible, migrate both the image folders and the database together.

---

## 7. Known Limitations

**Drag-and-drop import is temporarily disabled**

The ability to import images by dragging and dropping them directly from an external app (such as Finder) into the image list has been temporarily disabled due to unstable behavior. Please use the "Import Folder" or "Import Images" buttons to import images instead.
