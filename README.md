# SPA to CSV Converter

**English** | [한국어](README.ko.md)

A Python/tkinter desktop tool that batch-converts Thermo OMNIC `.spa` FT-IR
spectra to CSV without needing OMNIC installed. Each CSV is written next to its
source file with the same base name, overwriting any existing CSV.

> **▶ Windows users:** a ready-to-run `.exe` is available on the
> [**Releases**](../../releases) page — no Python installation required. Just
> download and double-click.

## Download (executable)

To use it without installing Python, download the matching executable from the
[Releases](../../releases) page and double-click it. Both builds run on
Windows 7 and later.

- **`SPA_to_CSV_x64.exe`** — 64-bit Windows
- **`SPA_to_CSV_x86.exe`** — 32-bit Windows (also runs on 64-bit; pick this if
  unsure, e.g. an older instrument-control PC)

To check your system type: `Settings → System → About → System type` (or right-click
`This PC → Properties`).

> Because the executable is unsigned, Windows SmartScreen may warn you on first
> launch. Click `More info → Run anyway`.

To run from source instead, see below.

## Install and run

Python 3.11+ is required. tkinter ships with typical Windows Python installs.

```powershell
python -m pip install -r requirements.txt
python main.py
```

The default UI language is **English**. Use the menu `Options → Language` to
switch between English and Korean; the title, buttons, and status messages
update instantly. `Options → About` shows the version, author, and GitHub link.

Use `Load Files` to pick multiple SPA files, or `Load Folder` to add every SPA
file in a folder, then press `Start`. As each file finishes it moves out of the
left (source) list into the right (results) list, which shows the finished CSV
name or a per-file failure reason. `Clear Results` empties the right list.
Conversion runs on a thread pool, so large batches finish quickly.

`Load Folder` scans subfolders too, so pointing it at a parent that holds one
subfolder per series (each with OMNIC split output) loads every spectrum in one
step.

> For large batches, prefer `Load Folder`: the `Load Files` dialog is limited by
> Windows to a few hundred files at once, while `Load Folder` has no such limit.
> Already-converted `.csv` files in the folders are ignored, so re-loading a
> folder never re-ingests previous output.

### In-situ series (`.srs`)

For an in-situ series file (`.srs`), split it in OMNIC first (a single
operation) — OMNIC writes each spectrum as an extension-less SPA file such as
`sample0000`, `sample0001`, … in a folder. Then use `Load Folder` on that
folder: the tool recognizes these extension-less files and converts them all
at once. (The `.srs` container is not read directly, because OMNIC reprocesses
the raw single-beam data into absorbance during the split.)

The output CSV matches OMNIC's own CSV export exactly: no header row, two
comma-separated columns (wavenumber, intensity), ascending wavenumber order,
scientific-notation values (`6.499040e+002`), and CRLF line endings. It is a
drop-in replacement for analysis scripts that already consume OMNIC CSVs.

## Building the standalone .exe

You can build a single, console-less executable. Double-click `build_exe.bat`,
or run:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name SPA_to_CSV --noconfirm main.py
```

The build produces `dist\SPA_to_CSV.exe`. That single file runs without a Python
install, and the `--windowed` flag keeps a console window from appearing. Copy
the exe wherever you like and double-click it.

## Supported SPA structure

The parser uses the directory-scan approach common to open SPA readers. It reads
a uint16 entry count at byte 294 and a 16-byte directory starting at byte 304.
Each directory entry holds a key (uint8) at `+0`, the block position (uint32) at
`+2`, and the block length (uint32) at `+6`. **Key 2 is the header block** and
**key 3 is the float32 intensity block**. The header stores the point count,
first wavenumber, and last wavenumber as little-endian values at `+4`, `+16`,
and `+20`. For multi-spectrum files, the first primary spectrum is converted.

## Validation

The output was compared directly against OMNIC's own CSV export using real
instrument files.

- **Spectrometer**: Thermo Scientific Nicolet iS50 FTIR
- **Software**: OMNIC 9.8.372
- For three measured spectra (6,950 points each), this tool's output versus
  OMNIC's exported CSV:
  - **Intensity values: all 6,950 points identical** (including negatives)
  - **Wavenumbers: only 5 of 6,950** differ by 0.001 cm⁻¹ in the 6th
    significant figure (thousands of times smaller than the spectral
    resolution; it stems from OMNIC's internal single-precision x-axis
    reconstruction and has no practical impact)
  - Row order, number formatting, and line endings all match OMNIC's format

## Tests

Synthetic SPA fixtures built in code validate the parser, converter, and
language handling.

```powershell
pytest -q
```

## License

This project is released under the [MIT License](LICENSE).

## Acknowledgment

The SPA binary-format byte offsets were derived from the file-format
documentation in the projects below and cross-checked against each other. No
source code from either project was copied.

- [spectrochempy](https://github.com/spectrochempy/spectrochempy) (`read_omnic`, CeCILL-B) — OMNIC SPA directory/header offset documentation
- [ne0dim/spa2csv](https://github.com/ne0dim/spa2csv) (GPL-3.0) — confirmation of the intensity data block key
