# User guide: Trackpad Gestures for NVDA, version 0.5

This add-on lets you use TalkBack-style gestures, with one to four fingers, on your laptop's touchpad, the way VoiceOver gestures work on a MacBook trackpad. Turn it on and off whenever you like.

## What is new in version 0.5

- Edge swipes for the system panels, like VoiceOver: a short one-finger swipe in from an edge of the touchpad reaches the Start button, the taskbar, the system tray, the ribbon, notifications, quick settings and widgets. See "Edge swipes for the system panels" below.
- The add-on finds out by itself which Windows version you have and where your taskbar is, and fits the edge swipes to it.
- A new section, "Edge swipes (system panels)", under One finger in the gesture list in settings.

## What was new in version 0.4

- A gesture list in the Trackpad Gestures settings, where you choose what every gesture does. It is sorted by one, two, three and four fingers. Each of these has sections for taps, swipes and holds; two-part (angular) swipes; and zones near the edges.
- More zones: a double tap near any edge with one, two, three or four fingers, and a long press near any edge with two, three or four fingers. A zone you have not given a command does the same as the normal gesture, so nothing changes until you choose.
- New commands you can give to any gesture: time and date, battery, read the clipboard, recognise text on screen (OCR), read the current line, read the selection, speech mode, volume up, volume down, mute, next track and previous track.

## What was new in version 0.3

- Windows' own three and four finger gestures are turned off automatically while trackpad gestures are on, and put back exactly as they were when you turn trackpad gestures off. You no longer need to change them in Touchpad settings. You can switch this off in the settings.
- Two-finger long press (hold two fingers still for half a second): go back to the application you are working in. From the taskbar, system tray, desktop or Task View, it brings that application to the front. Inside the application, it leaves the ribbon or menus (like pressing Escape) and goes back to the document, sheet or file list.
- Three-finger and four-finger long press are also recognised. They have no command yet, so you can give them one in Input gestures.

## What was new in version 0.2

- Swipe right and left now just move to the next and previous item, in a way that suits where you are: files in a folder, menus, lists, Word documents, Excel cells and web pages.
- A new "Items (default)" reading control. It is the first reading control, so swipe up and down also move item by item until you choose another control.
- New reading controls for work: panes and panels (F6), taskbar, system tray, table cells (Excel and tables), Excel sheets, PowerPoint slides, sentences, controls (Tab), and speech rate.
- You can turn each reading control on or off, and change their order, in NVDA Settings.
- Two-finger double taps near the edges of the touchpad: top for the ribbon or menu bar, bottom for the taskbar, left for Task View, right for the system tray.
- Editing gestures: selection mode, copy, paste, undo, redo and save.

## Before you start: check your touchpad

1.  Press Windows+R, type <span class="kbd">ms-settings:devices-touchpad</span> and press Enter.
2.  Press Tab a few times. If you hear "Your PC has a precision touchpad", you are ready.

## Windows' own three and four finger gestures

From version 0.3 the add-on turns these off for you while trackpad gestures are on, and puts them back when you turn trackpad gestures off. If Windows still reacts to three or four finger swipes the first time, sign out of Windows and back in once. If you prefer to change them yourself, uncheck "Turn off Windows' own three and four finger gestures" in the settings and follow these steps:

1.  In the same Touchpad settings page, press Tab until you reach "Three-finger gestures" and press Space or Enter to expand it.
2.  Tab to the "Swipes" combo box and choose "Nothing" with the arrow keys. Then Tab to "Taps" and choose "Nothing".
3.  Do the same under "Four-finger gestures".

## Turning gestures on and off

- NVDA+Shift+G turns gestures on or off. A high beep means on, a low beep means off.
- A four-finger double tap turns gestures off.
- While gestures are on, the touchpad does not move the mouse pointer or click.

## Gestures

### One finger: moving

- Swipe right: next item.
- Swipe left: previous item.
- Swipe down: forward by the current reading control.
- Swipe up: back by the current reading control.
- Swipe up then down: next reading control.
- Swipe down then up: previous reading control.
- Touch and hold still, then slide: explore what is under your finger in the current window.

### One finger: taps

- Tap: speak the current item.
- Double tap: activate (open a file, press a button, follow a link).
- Triple tap: report formatting (font, size, style), useful in Word.
- Double tap and hold: context menu, like long press.

### One finger: two-part swipes

- Down then left: back (previous web page, or Escape elsewhere).
- Up then left: home (show desktop).
- Left then up: switch to the previous app (Alt+Tab).
- Right then down: notifications.
- Down then right: NVDA menu.
- Up then right: read the status bar (page and word count in Word, and so on).
- Left then right: switch between browse mode and focus mode (NVDA+Space).
- Right then left: elements list (NVDA+F7) for headings, links, and comments in Word.
- Left then down: undo.
- Right then up: redo.

### Two fingers

- Tap: stop speech.
- Double tap in the middle: play or pause media.
- Double tap near the top edge: ribbon or menu bar (Alt).
- Double tap near the bottom edge: taskbar (Windows+T).
- Double tap near the left edge: Task View, to choose any open window (Windows+Tab).
- Double tap near the right edge: system tray (Windows+B).
- Triple tap: selection mode on or off.
- Long press (hold still for half a second): go back to the application you are working in, and to its document, sheet or list.
- Swipe up: Page Down. Swipe down: Page Up.
- Swipe left: next tab. Swipe right: previous tab.

### Three fingers

- Tap: NVDA menu.
- Double tap: copy.
- Triple tap: paste.
- Swipe down: read from here. Swipe up: read from the top.
- Swipe right: next reading control. Swipe left: previous reading control.

### Four fingers

- Tap: speak the focused item.
- Double tap: turn trackpad gestures off.
- Swipe right: next pane or panel (F6). Swipe left: previous pane (Shift+F6).
- Swipe up: speak the window title.
- Swipe down: save (Control+S).

## How swipe right and left choose what "next item" means

- Files in a folder, lists, menus, tree views: down and up arrow, so you hear each file or option.
- Tabs, the menu bar, Excel cells and table cells: right and left arrow. In Excel, swipe right and left move along the row.
- Word, Notepad and other documents: line by line.
- Web pages and other browse mode documents: line by line, like the arrow keys.
- Text boxes with one line, and PowerPoint slides: Tab and Shift+Tab. In PowerPoint this moves between the objects on a slide.
- Dialogs and buttons: every item in order, including text that Tab would skip.
- Double tap always activates the item you moved to.

If you prefer one behaviour everywhere, change "Swipe right and left moves by" in the settings.

## Reading controls

Swipe up then down (or three-finger swipe right) to choose a reading control, then swipe down and up to move by it. These are on to begin with:

- Items (default): the same as swipe right and left.
- Characters, Words, Lines: these use NVDA's review cursor, exactly like the numpad review keys. Swipe down is Numpad 3, 6 or 9 (next character, word or line). Swipe up is Numpad 1, 4 or 7 (previous character, word or line). They work with the laptop keyboard layout too. In selection mode they use the real cursor instead, because only the real cursor can select. To always use the real cursor, like the arrow keys, change "Characters, words and lines read with" in the settings.
- Paragraphs: moves the real cursor, like Control+Down Arrow.
- Controls (Tab key): only the things you can press or type into.
- Headings, Links, Form fields, Landmarks: browse mode only. In Word, swipe left then right first to turn on browse mode.
- Table cells: one control for tables. While it is chosen, swipe right and left move cell by cell across the row, and swipe down and up move row by row in the same column. Works in Excel, and in tables in Word and web pages.
- Panes and panels (F6): moves between the main areas of a window, such as Word's ribbon, document and status bar, Excel's sheet and formula area, PowerPoint's slide list, slide and notes, or File Explorer's navigation pane and file list.
- Taskbar: each swipe moves to the next or previous taskbar button. Double tap to open it.
- Sheets: Excel only. Moves to the next or previous worksheet.
- Slides: PowerPoint only. Moves to the next or previous slide.
- Speech rate: swipe down for faster, up for slower.

These are off to begin with, and you can turn them on: Sentences (Word), All objects (object navigation), Buttons, Edit fields, Lists, Tables, Graphics, and System tray.

Excel-only and PowerPoint-only controls are skipped automatically when you are in other apps.

### Adding, removing and reordering reading controls

1.  Press NVDA+N, then P for Preferences, then S for Settings.
2.  In the categories list, choose "Trackpad Gestures" with the arrow keys, then press Tab.
3.  Tab to the "Reading controls" list. Arrow up and down through it. Press Space to check or uncheck a control. Checked means it is in your reading controls.
4.  To change the order, select a control in the list, then Tab to "Move up" or "Move down" and press Space. NVDA tells you the new position. Shift+Tab takes you back to the list.
5.  "Reset reading controls" puts the list back to how it started.
6.  Press Enter on OK to save.

## Working in Word, Excel and PowerPoint

### Word

- Swipe right and left read line by line. Choose Words, Sentences or Paragraphs as the reading control and swipe down and up for finer or bigger steps.
- Selecting text: two-finger triple tap to turn on selection mode. Then every swipe selects as it moves. Three-finger double tap copies, three-finger triple tap pastes. Two-finger triple tap again to turn selection off.
- Headings and links: swipe left then right for browse mode, then use the Headings reading control. Or swipe right then left for the elements list.
- Triple tap for formatting, swipe up then right for page and word count.

### Excel

- Choose the "Table cells" reading control. Swipe right and left move cell by cell, swipe down and up move row by row.
- Choose "Sheets" to move between worksheets.
- Selection mode works here too, to select ranges of cells.

### PowerPoint

- Choose "Slides" and swipe down and up to change slides.
- Swipe right and left move between the objects on a slide.
- Use "Panes and panels", or four-finger swipes, to reach the slide list and the notes.

### Everywhere

- Two-finger double tap near the top edge reaches the ribbon. Then swipe right and left move between ribbon tabs.
- Four-finger swipe down saves.
- Two-finger long press always brings you back: out of the ribbon, out of a pane, or back from the taskbar to your document. In a dialog it tells you so, and leaves the dialog alone.

## Edge swipes for the system panels

Put one finger right at the edge of the touchpad and swipe a short way in, quickly, towards the middle. Each edge reaches a different part of Windows.

### How to make an edge swipe

- Use one finger.
- Start with your finger on the very edge: within the outer tenth of the touchpad. Feeling for the edge with your fingertip first helps.
- Swipe inward, towards the middle, a short distance: more than a twentieth of the touchpad, and less than about two fifths. Keep it quick, under a second, and fairly straight.
- The top and bottom edges each have three places to start: the left corner, the middle and the right corner. The corners are the outer quarter or so at each end of that edge.
- A long swipe that starts near an edge is still a normal swipe, and a tap near an edge is still a tap, so nothing you already use changes.

### First swipe and second swipe

- The first swipe moves focus there. NVDA reads where you landed. For example, the taskbar swipe puts you on the first app button.
- You can then move around with your usual gestures or keys, for example swipe right to the next taskbar button.
- The same edge swipe again, within 20 seconds and while you are still there, opens or activates what has focus, like pressing Enter.
- Any other gesture in between cancels this, so the next edge swipe starts fresh.
- If the add-on cannot get focus to the taskbar, it says "Could not reach the taskbar" and writes the details to the NVDA log. Press NVDA+F1 and search for "Trackpad Gestures" to find them.

### The edge where your taskbar is

- Swipe in from the corner where the taskbar starts: the Start button. Swipe again: the Start menu opens.
- Swipe in from the middle: the taskbar app buttons (Windows+T). Swipe again: the focused app opens.
- Swipe in from the corner where the taskbar ends: the system tray (Windows+B). Swipe again: the focused icon opens.

With the taskbar at the bottom (the usual place), that means: swipe up from the bottom left corner, from the bottom middle, and from the bottom right corner.

### The other edges

- Swipe down from the top left corner: the app's ribbon or menu bar (Alt).
- Swipe down from the top middle: notifications (Windows+N).
- Swipe down from the top right corner: quick settings, such as Wi-Fi, Bluetooth and volume (Windows+A).
- Swipe right from the left edge: Widgets (Windows+W).
- Swipe left from the right edge: the notification centre (Windows+N).

These match the edge swipes on Windows touch screens.

### Automatic taskbar detection

- Every edge swipe checks your Windows version and where your taskbar is, so if you move the taskbar, the swipes follow it straight away.
- Taskbar at the top: the taskbar swipes move to the top edge, and the ribbon, notifications and quick settings swipes move to the bottom edge.
- Taskbar on the left or right side: the taskbar swipes are on that side, in order from the top: swipe in near the top for the Start button, in the middle for the app buttons, and near the bottom for the system tray. Swipes from the other side edge do what they normally do. With a side taskbar, the bottom edge has nothing, and the add-on says "Nothing at this edge".
- Windows 11 lets you centre the taskbar or keep it on the left. Both work the same way here, because the add-on reaches each part with its keyboard shortcut, not by its place on the screen.
- Windows 10 has one Action Center for notifications and quick actions, so the top middle, top right and right edge swipes all open it (Windows+A). The swipe from the left edge opens Task View (Windows+Tab), as a touch screen does on Windows 10.

### Changing what an edge swipe does

Open NVDA Settings, choose the "Trackpad Gestures" category, and in the Gestures tree open "One finger", then "Edge swipes (system panels)". Each edge swipe can be given any command, like other gestures. The default is "Goes to the system panel item at that edge; the same swipe again opens it". With input help on (NVDA+1), an edge swipe is spoken by name, for example "swipe down from the top right corner".

## Choosing what each gesture does

1.  Press NVDA+N, then P for Preferences, then S for Settings. Choose the "Trackpad Gestures" category, then press Tab until you reach the "Gestures" tree.
2.  The tree has four branches: One finger, Two fingers, Three fingers and Four fingers. Press Right Arrow to open a branch and Left Arrow to close it. Inside each are the sections: "Taps, swipes and holds", "Two-part swipes (angular)" (one finger only), "Zones near the edges" and "Edge swipes (system panels)" (one finger only).
3.  Each gesture is read with what it does now, for example "swipe right: Moves to the next item".
4.  On the gesture you want, press Tab to reach "Command for this gesture". Choose a command with the arrow keys. Commands are grouped by their first word: Navigation, Reading, Activating, Editing, Windows and apps, Information, Media and volume, Speech and Trackpad gestures. Choose "Nothing" to make a gesture do nothing.
5.  Shift+Tab takes you back to the tree. "Reset this gesture" puts one gesture back to how it came. "Reset all gestures" puts them all back.
6.  Press Enter on OK to save. Your choices also show in NVDA's Input gestures dialog, and changes made there show here.

Zones: a zone gesture is the same gesture made near the top, bottom, left or right edge of the touchpad, within about one fifth of it. A zone with no command of its own does the same as the normal gesture. For example, "double tap near the left edge" activates, like a normal double tap, until you give it a command.

## Learning and changing gestures

- NVDA+1 turns on input help. Any gesture you make is spoken with what it does, but not carried out. Press NVDA+1 again to turn it off.
- To change a gesture, open NVDA menu, Preferences, Input gestures. Expand "Trackpad Gestures", choose a command, press Add, then make the gesture on the touchpad. Cut and Select all have no gesture yet, so you can give them one here.

## Other settings

- Explore by touch: turn off if holding still starts exploring when you do not want it to.
- Stop the touchpad moving the mouse pointer and clicking: leave on.
- Allow an external mouse: check this if you want a USB mouse to work while gestures are on.

## If something does not work

- Use input help (NVDA+1) to check which gesture the add-on heard.
- Edge double taps: tap close to the edge, within about one fifth of the touchpad.
- Problems are written to the NVDA log. Press NVDA+F1 and search for "Trackpad Gestures".
