# Developer guide

How to build, test and change Trackpad Gestures for NVDA. Read [how it works](how-it-works.md) first.

## Repository layout

```
addon/                          the add-on, exactly as packaged
  manifest.ini                  name, version, NVDA versions supported
  doc/en/readme.html            the help NVDA opens from the Add-on Store
  globalPlugins/trackpadGestures/
    __init__.py                 NVDA plugin: commands, reading controls, settings
    rawinput.py                 touchpad reading and pointer blocking (Windows)
    recognizer.py               gesture recognizer (shared with the Linux version)
    edges.py                    edge swipe detector (shared with the Linux version)
    systemPanels.py             taskbar layout and edge swipe actions
    winGestures.py              Windows' own touchpad gestures off and on
docs/                           this documentation
tests/                          tests that run without NVDA or Windows
build.py                        builds the .nvda-addon file
```

## Requirements

- Python 3 for building and testing. Nothing else is needed: the tests use small stand-ins for NVDA's modules.
- For trying the add-on: Windows 10 or 11 with a precision touchpad, and NVDA 2023.1 or later.

## Building

From the repository folder:

```
python build.py
```

This writes `trackpadGestures-<version>.nvda-addon`, using the version in `addon/manifest.ini`. Press Enter on the file in File Explorer to install it in NVDA.

## Testing

```
python tests/run_tests.py
```

It runs every test and prints one line per file. Any failure is printed in full.

| Test | Checks |
| --- | --- |
| `test_rec.py` | Every gesture the recognizer reports, from simulated finger movements |
| `test_edges.py` | Every edge swipe rule, including the exact 5% and 40% limits, and that the recognizer reports nothing for an edge swipe |
| `test_plugin.py` | Reading controls, gesture names, and that every `tp:` binding is a real gesture |
| `test_panels.py` | The edge swipe action for each taskbar position, Windows 10 and 11 keys, and the settings sections |
| `test_again.py` | That another gesture cancels "the same edge swipe again" |

What the tests cannot check: reading a real touchpad, NVDA's speech, focus moving in other applications, and the settings window as a screen reader reads it. Those need a laptop with NVDA. When testing there, NVDA+1 (input help) shows which gesture the add-on recognised without running its command, and NVDA+F1 opens the log; every message from the add-on starts with "Trackpad Gestures".

## Shared files

`recognizer.py` and `edges.py` are used unchanged by Setu Trackpad Gestures, the Linux version for Orca. Keep them free of NVDA, Orca, Windows and Linux imports. A change to either should be made in both projects at the same time, and `test_rec.py` and `test_edges.py` should pass in both.

`edges.py` reads one internal attribute of the recognizer, `_session`, to make it forget an edge swipe. If the recognizer is restructured, keep that attribute or change `EdgeDetector._forget` to match.

## Common changes

### Change what a gesture does by default

Each command is a method named `script_<name>` in `GlobalPlugin`, with an `@script` decorator. Its `gesture=` or `gestures=` lists its default gestures as `tp:<gestureName>`:

```python
@script(description=_("Reads the status bar (page, word count, cell)"), gesture="tp:swipeUpThenRight")
def script_statusBar(self, gesture):
    self._run("reportStatusLine", gesture=gesture)
```

Gesture names are listed by `allGestureNames()` in `recognizer.py` and `EDGE_NAMES` in `edges.py`. `test_plugin.py` fails if a binding names a gesture that does not exist.

### Add a command

1. Add a `script_<name>` method with a `description`. The description is what users hear in input help and see in the gesture list.
2. Add its name to the right group in `COMMAND_GROUPS`, so it appears in the settings. `test_plugin.py` reports any command missing from the groups.
3. To press a key, use `self._key("control+s")`; to run an NVDA command, use `self._run("nvdaScriptName", gesture=gesture)`.

### Add a gesture

New gestures belong in the recognizer (or a new shared detector like `edges.py`), so both versions get them. Add the name to its list of names, then add a test that produces it from simulated finger movement. The settings gesture list sorts names by the number in front (`2finger...`) and by kind, using `_kind` in `__init__.py`.

### Add a reading control

Add an entry to `READING_CONTROLS` in `__init__.py` (id, label, on by default, app it belongs to or `None`), then handle the id in `_moveByControl`. Users who have already saved an order get new controls at the end of their list.

## Releasing

1. Update `version` in `addon/manifest.ini`, and `lastTestedNVDAVersion` if you tested a newer NVDA.
2. Add a section to `CHANGELOG.md`, and a "What is new" section to `addon/doc/en/readme.html`.
3. Convert the help to the user guide: `pandoc addon/doc/en/readme.html -f html -t gfm --wrap=none -o docs/user-guide.md`.
4. Regenerate `docs/gestures.md` if gestures or default commands changed.
5. Run the tests, build, install on a real laptop, and try the changed gestures with input help and the log.
6. Tag the release (for example `v0.5.0`) and attach the `.nvda-addon` file to the GitHub release.

## Code style

The code follows NVDA's add-on conventions: tabs for indentation, translatable text wrapped in `_()`, comments for translators above user-facing strings, and messages to the log prefixed with "Trackpad Gestures". User-facing text is written for screen reader and keyboard users: it never refers to colours, positions on the screen or clicking.
