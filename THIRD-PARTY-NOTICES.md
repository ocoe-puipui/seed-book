# Third-Party Notices

This application (Seed Book, an AI image browser) is
built on top of the following third-party open-source components. Each
component remains under its own license, listed below. These licenses are
independent of, and take precedence over, the license in `LICENSE` for the
respective component's code.

Full license texts are included in the `LICENSES/` folder.

---

## PySide6 (Qt for Python)

- **What it is used for:** GUI framework (application windows, widgets,
  drag & drop, clipboard integration, etc.)
- **License:** GNU Lesser General Public License v3.0 (LGPLv3)
- **Project:** https://pypi.org/project/PySide6/ · https://www.qt.io/
- **Full license text:** [`LICENSES/LGPL-3.0.txt`](./LICENSES/LGPL-3.0.txt)
  (which incorporates [`LICENSES/GPL-3.0.txt`](./LICENSES/GPL-3.0.txt) by
  reference)

This application uses PySide6/Qt under the terms of the LGPLv3. PySide6 is
used as an unmodified, dynamically-linked library obtained from PyPI; its
source code is publicly available from the links above. Consistent with
LGPLv3 §4(d)(1), the Qt/PySide6 shared libraries are packaged as separate
files alongside the application (not statically merged into a single
binary), so that they can in principle be replaced with a compatible
version by the user. This application does not modify PySide6/Qt itself.

## Pillow (PIL Fork)

- **What it is used for:** Reading image files and extracting embedded
  metadata (EXIF / PNG text chunks, etc.)
- **License:** MIT-CMU (a.k.a. the "Historical Permission Notice and
  Disclaimer" / HPND-style license used by PIL/Pillow)
- **Project:** https://python-pillow.org/ · https://pypi.org/project/Pillow/
- **Full license text:** [`LICENSES/Pillow-LICENSE.txt`](./LICENSES/Pillow-LICENSE.txt)

## PyInstaller

- **What it is used for:** Build-time only — packages the application into
  a standalone macOS `.app` / `.dmg`. It is **not** included in, or
  distributed as part of, the running application; it is a build tool used
  by the developer.
- **License:** GPLv2+ with a bundled-application exception. PyInstaller's
  license explicitly states that the exception permits distributing the
  programs it builds under any license, without the built program itself
  becoming subject to the GPL.
- **Project:** https://pyinstaller.org/
- No notice or license file is required to be shipped with the built
  application for this reason, but it is listed here for transparency.

## Python Standard Library (`sqlite3`, wrapping SQLite)

- **What it is used for:** Local database storage of image metadata and
  import history.
- **License:** SQLite itself is dedicated to the public domain; the
  `sqlite3` Python module is part of CPython's standard library (PSF
  License).
- No additional notice is required.

---

*This file was last reviewed on 2026-08-13. If dependencies or their
versions change, this file (and the `LICENSES/` folder) should be updated
accordingly.*
