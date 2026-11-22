# Changelog

## 0.5.0

- Edge swipes for the system panels, like VoiceOver: a short one-finger swipe in from an edge reaches the Start button, taskbar apps, system tray, ribbon or menu bar, notifications, quick settings and widgets. The first swipe moves focus there; the same swipe again within 20 seconds opens it.
- The edge swipes follow the taskbar: the add-on reads the Windows version and the taskbar's edge and alignment, and adapts to a taskbar at the top or on either side.
- If focus does not reach the taskbar, the add-on says "Could not reach the taskbar" and writes the details to the NVDA log.
- New section "Edge swipes (system panels)" under One finger in the gesture list.
- Edge swipe detection is in its own file, `edges.py`, shared with the Linux version. `recognizer.py` is unchanged.

## 0.4.0

- Gesture list in the add-on's settings, sorted by one, two, three and four fingers, with sections for taps, swipes and holds; two-part swipes; and zones near the edges. Any gesture can be given any command; changes also show in NVDA's Input gestures dialog.
- Zones: double taps with one to four fingers and long presses with two to four fingers near each edge. A zone with no command of its own does the same as the normal gesture.
- New commands: time and date, battery, read clipboard, recognise text on screen (OCR), read current line, read selection, speech mode, volume up, volume down, mute, next track, previous track.

## 0.3.0

- Windows' own three and four finger gestures are turned off while trackpad gestures are on, and put back afterwards, including after NVDA closes unexpectedly.
- Two-finger long press returns to the application you were working in: from the taskbar, tray, desktop or Task View it brings the application back, and inside it leaves the ribbon or menus, or returns from another pane to the document, sheet or list. It leaves dialogs alone.
- Three and four finger long presses are recognised.

## 0.2.2

- Rows and columns are now one reading control, "Table cells": swipe right and left move by cell, swipe down and up move by row. Works in Excel and in tables in Word and web pages.

## 0.2.1

- Characters, words and lines use NVDA's review cursor, like Numpad 1 and 3, 4 and 6, 7 and 9, so they also work with the laptop keyboard layout. A setting switches back to the system cursor.

## 0.2.0

- Swipe right and left choose what "next item" means from where focus is: files and list items, Excel cells, document lines, web page lines, controls.
- New "Items (default)" reading control.
- Reading controls can be turned on and off and reordered in settings.
- New reading controls: panes and panels (F6), taskbar, system tray, table rows and columns, Excel sheets, PowerPoint slides, sentences, controls (Tab), speech rate.
- Two-finger double taps near the edges: ribbon or menu bar, taskbar, Task View, system tray.
- Editing gestures: selection mode, copy, paste, undo, redo, save.

## 0.1.0

- First version: TalkBack-style gestures with one to four fingers on a Windows precision touchpad, read through Windows Raw Input.
- Swipes, taps, double and triple taps, double tap and hold, two-part swipes, and explore by touch.
- The touchpad does not move the pointer or click while gestures are on.
- Turn on and off with NVDA+Shift+G or a four-finger double tap.
