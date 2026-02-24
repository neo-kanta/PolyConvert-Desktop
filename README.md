# Universal File Converter

A production-grade, extensible desktop application for converting files. 
Currently supports **DOCX to TXT** conversion, with a scalable plugin architecture for future formats.

## Features
- **Responsive GUI**: Built with standard `tkinter` (`ttk`), scales gracefully.
- **Multilingual**: Supports standard fallback mechanism (en-US, zh-TW).
- **Format Conversion**: Convert `.docx` containing paragraphs, tables, headers, and footers.
- **Table Handling**: Normalizes irregular tables, supports TSV or Pipe formats.
- **Output Chunking**: Split long output into smaller parts for web uploads.
- **Headless CLI**: Automate conversions via command line.
- **Scalable Architecture**: Everything is a plugin. Add PDF, Markdown, or Excel support without touching the core engine.

## Installation for Development

1. **Prerequisites**: Python 3.9+
2. **Install**:
   ```bash
   pip install -e .[dev]
   ```
3. **Run GUI**:
   ```bash
   ufc
   # or
   python src/ufc/app.py
   ```

## CLI Usage

```bash
ufc convert --in-type docx --out-type txt --lang zh-TW --output-dir ./out sample.docx
```
Run `ufc convert --help` to see all available options.

## Testing

Uses `pytest` for unit and end-to-end tests:
```bash
pytest -v tests/
```

## Packaging for Release

You can build a standalone executable using PyInstaller.
1. Make sure PyInstaller is installed (`pip install -e .[build]`).
2. Run the build script:
```bash
python scripts/build_exe.py
```
3. The standalone `.exe` will be located in the `dist` folder.

## Packaging Plan & Security Note
* **Configs**: User config is saved cleanly to `~/.universal_file_converter.json`.
* **Telemetry**: This application contains zero telemetry, analytics, or hidden behavior.
* **Logs**: No log files are left behind maliciously. All operations happen in-memory or are directly written to the user-specified folder.
