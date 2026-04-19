# ForbiddenToolkit
### Forbidden Cheese Development

> A swiss-army CTF and security utility tool — offline, no cloud, no subscription.  
> Four tools in one window. Load data. Get answers.

---

## What It Does

ForbiddenToolkit bundles four common security and forensics utilities under one FC-branded interface with ambient audio feedback.

---

## Tools

### Encode / Decode
Supports Base64, Base32, Hex, URL encoding, Binary, and ROT13.  
**Auto Detect** button identifies the encoding type automatically and decodes in one click.  
Manual mode available via dropdown for edge cases.

### Hash ID
Paste any hash string and identify the algorithm.  
Returns all probable types with **Hashcat mode numbers** and **John the Ripper format names** where available.  
Supports MD5, SHA1, SHA256, bcrypt, NTLM, and 30+ others.

### Strings
Load any file — binary, executable, image, document — and extract all printable strings.  
Adjustable minimum length. Live filter box to search results. Export to TXT.

### Exif
Full metadata extraction via ExifTool.  
Works on images, PDFs, Office documents, audio, and video files.  
Returns camera make/model, GPS coordinates, timestamps, software used, and more.

---

## Audio
- Ambient BGM plays at low volume to keep audio hardware warm
- TTS voice feedback announces results, no-match, and errors
- Mute toggle in status bar
- Oops button reinitialises audio engine without restarting

---

## Requirements

| Requirement | Notes |
|---|---|
| Windows 10 or 11 | v1 Windows only. Linux build planned. |
| No Python needed | PyInstaller bundles the runtime |
| ExifTool | Bundled in installer |

**Windows 7/8/XP:** Not tested, not supported in v1. Python 3.x and pygame 2.x both dropped support for these OS versions. Possible with older dependency versions but not a current goal.

---

## Installation

Download `ForbiddenToolkit_Setup_v1.exe` from the [Releases](../../releases) page.  
Run installer → pick install location → done. No wizard, no manual config.

---

## Dependencies (for running from source)

```
pip install hashid Pillow opencv-python pygame
```

ExifTool must be installed separately if running from source:
```
winget install OliverBetz.ExifTool
```

---

## Configuration

`fk_config.ini` is written automatically by the installer.  
If running from source, launch once to generate it, then edit paths manually.  
ExifTool path can also be set via the Browse button in the Exif tab.

---

## Roadmap

**v2 (Windows)**
- Custom icon (ForTools branding)
- Faster audio preload — no cold-start latency
- Improved splash sequence

**Linux build**
- Separate build once Windows version is stable
- `winsound` replaced with pygame audio throughout
- ExifTool Linux binary bundled

---

## Project

**Developer:** Harlan "Bear" McGillem  
**Studio:** Forbidden Cheese Development  
**Portfolio:** [sites.google.com/view/forbidden-cheese](https://sites.google.com/view/forbidden-cheese)  
**Also by FC:** [ForbiddenReader](https://github.com/BearArmD/ForbiddenReader) — offline document-to-speech tool

---

*Built with Python + open source tools. No cloud. No subscription. Just works.*
