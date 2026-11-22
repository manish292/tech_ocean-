# Trackpad Gestures for NVDA

Use your laptop's touchpad the way you use TalkBack on an Android phone, or VoiceOver's Trackpad Commander on a Mac: swipe, tap and hold with one to four fingers to move around Windows with the NVDA screen reader.

Windows does not give screen readers access to touchpad fingers; it turns them into mouse movement, which is of little use without sight. This add-on reads each finger directly from the touchpad and turns your movements into screen reader gestures, so the touchpad becomes a second way to work alongside the keyboard.

Version 0.5.0 · Windows 10 and 11 · NVDA 2023.1 or later

## What it does

- **TalkBack-style gestures**: swipe right and left for the next and previous item, double tap to activate, double tap and hold for the context menu, two-part swipes such as up then left for home, and touch and hold to explore what is under your finger.
- **Next item that fits**: files in a folder, Excel cells, lines in Word, web pages and dialogs each move the way you would expect.
- **Reading controls**, as in TalkBack: swipe up and down by characters, words and lines (using NVDA's review cursor, like the numpad), headings, links, form fields, table cells, panes, the taskbar, Excel sheets, PowerPoint slides or speech rate. Choose, remove and reorder them in settings.
- **Work gestures** for Word, Excel and PowerPoint: selection mode, copy, paste, undo, redo, save, the ribbon, panes, and a two-finger long press to get back to your document from anywhere.
- **Edge swipes for the system panels**, like VoiceOver: swipe in from an edge for the Start button, taskbar, system tray, notifications, quick settings and widgets. The add-on finds your taskbar by itself.
- **Zones**: the same tap near the top, bottom, left or right edge can do something different.
- **80 gestures**, every one of which can be given any command in the add-on's settings, sorted by number of fingers.
- **No accidental pointer movement**: while gestures are on, the touchpad does not move the pointer or click, and Windows' own three and four finger gestures are switched off, then put back when you finish.
- Turn it on and off at any time with **NVDA+Shift+G**.

## Requirements

- Windows 10 or Windows 11.
- A precision touchpad. Most laptops from 2018 onwards have one. To check, press Windows+R, type `ms-settings:devices-touchpad` and press Enter, then press Tab and listen for "Your PC has a precision touchpad".
- NVDA 2023.1 or later, installed (not the portable version).

## Install

1. Download the latest `.nvda-addon` file from the [Releases](../../releases) page.
2. Press Enter on the file in File Explorer. NVDA asks whether to install it; choose Yes, then restart NVDA.
3. Press NVDA+Shift+G. A high beep means gestures are on.

## First gestures to try

| Gesture | What it does |
| --- | --- |
| Swipe right or left with one finger | Next or previous item |
| Double tap | Activate |
| Swipe up then down | Next reading control |
| Swipe down or up | Move by the reading control |
| Two-finger tap | Stop speech |
| Two-finger long press (hold half a second) | Back to the application you are working in |
| Swipe up from the bottom middle of the touchpad (taskbar at the bottom) | Taskbar; the same swipe again opens the app |
| Four-finger double tap | Turn gestures off |

Turn on NVDA's input help with NVDA+1 to hear the name and command of each gesture you make, without running it. Press NVDA+1 again to turn it off.

## Documentation

- [User guide](docs/user-guide.md): everything about using the add-on, including Word, Excel and PowerPoint.
- [All gestures](docs/gestures.md): every gesture and its default command.
- [How it works](docs/how-it-works.md): how the add-on reads the touchpad and recognises gestures.
- [Developer guide](docs/developer-guide.md): building, testing and changing the add-on.
- [Changelog](CHANGELOG.md).

The same user guide opens from NVDA: NVDA menu, Tools, Add-on store (Manage add-ons in NVDA 2023.1), Installed add-ons, Trackpad Gestures, then the Help button.

## Linux version

Setu Trackpad Gestures brings the same gestures to the Orca screen reader on Linux. The gesture recognizer (`recognizer.py`) and edge swipe detector (`edges.py`) are shared between the two, so a gesture works the same way on both.

## Building and testing

```
python tests/run_tests.py
python build.py
```

The tests run without NVDA or Windows. See the [developer guide](docs/developer-guide.md).

## Status

The add-on is used daily by its author on his own laptop. It has not yet been tried on many different touchpads. If a gesture is not recognised well on yours, please open an issue with your laptop model and, if possible, the lines from the NVDA log (NVDA+F1) that start with "Trackpad Gestures".

## Author

Manish Pawar.

## License

Copyright (C) 2026 Manish Pawar.

This add-on is free software, licensed under the GNU General Public License, version 2, the same license as NVDA. You may use, share and change it under the terms in the [LICENSE](LICENSE) file. It comes with no warranty.
