# ✦ Devers Packer

A lightweight packer that turns any game folder into a single `.dvp` archive — ready to be run by [Devers Launcher](https://github.com/Made-by-One/Devers-Launcher).

![Platform](https://img.shields.io/badge/platform-Windows-white)
[![Release](https://img.shields.io/badge/release-v1.0-white)](https://github.com/Made-by-One/Devers-Packer/releases)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![Made by](https://img.shields.io/badge/Made%20by%20One%20Studio-black)](#)

---

## 🚀 Quick start

1. Download **Devers Packer** from [Releases](https://github.com/Made-by-One/Devers-Packer/releases).
2. Run `Devers Packer.exe`.
3. Pick the game folder — name and `.exe` are filled in automatically.
4. (Optional) Pick a cover — the crop editor will open, drag the handles, apply.
5. Press **PACK INTO .DVP** — the file appears in `output/`.
6. Drop the `.dvp` into [Devers Launcher](https://github.com/Made-by-One/Devers-Launcher)'s `games/` folder.

---

## 📂 Output format

A `.dvp` is a ZIP archive containing:

```
manifest.json      ← name, exe, version, created, size, cover (hex)
<original files>   ← all game files, relative paths preserved
```

Manifest example:

```json
{
  "name": "Astrophobia",
  "exe": "Astrophobia.exe",
  "version": "1.0",
  "created": "2026-09-17 22:06:07",
  "files_count": 1284,
  "total_size": 117849600,
  "cover_data": "89504e470d0a1a0a...",
  "cover_ext": ".png"
}
```

---

## 🌐 Localization

All UI strings live in `localization/*.json`. English is the base; missing keys fall back to `en.json` automatically.

Currently supported:
- 🇬🇧 English (`en.json`)

**Add your language:**

1. Copy `localization/en.json` to `localization/<code>.json` (e.g. `de.json`).
2. Change `_name` to the native language name (`"Deutsch"`).
3. Change `_code` to the language code (`"de"`).
4. Translate any keys you want — untranslated ones fall back to English.
5. Relaunch the app — the language will appear in the dropdown.

---

## 🧱 Two ways to use

### Option 1 — Ready-to-use `.exe` (recommended)

Download the latest `Devers Packer.exe` from [Releases](https://github.com/Made-by-One/Devers-Packer/releases) and run it. No Python installation required.

### Option 2 — Run from source (Windows only)

Requirements:
- **Windows 10 / 11**
- **Python 3.10+** — https://www.python.org/downloads/ (check "Add Python to PATH" during installation)

Steps:

```bat
git clone https://github.com/Made-by-One/Devers-Packer.git
cd Devers-Packer
pip install -r requirements.txt
python packer.py
```

### `requirements.txt`

```
PyQt6>=6.6.0
```

---

## 📂 Project structure

```
Devers-Packer/
├── LICENSE
├── README.md
├── requirements.txt
├── app.ico
├── packer.py
└── localization/
    └── en.json
```

---

## 🔗 Related

- [Devers Launcher](https://github.com/Made-by-One/Devers-Launcher) — runs `.dvp` files created by this packer

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

Made with ✦ by **Made by One Studio**
