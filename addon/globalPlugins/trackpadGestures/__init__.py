# Trackpad Gestures for NVDA
# Use TalkBack-style gestures (up to four fingers) on a Windows precision touchpad.
# Toggle with NVDA+Shift+G. All gestures can be reassigned in NVDA's Input gestures dialog,
# under the "Trackpad Gestures" category. Reading controls can be added, removed and
# reordered in NVDA Settings, Trackpad Gestures category.

import time

import addonHandler
import api
import browseMode
import config
import controlTypes
import core
import globalPluginHandler
import globalVars
import inputCore
import keyboardHandler
import queueHandler
import speech
import tones
import ui
import wx
from gui import guiHelper
from gui.settingsDialogs import NVDASettingsDialog, SettingsPanel
from logHandler import log
from NVDAObjects import NVDAObject
from scriptHandler import script

from . import systemPanels
from .edges import EDGE_NAMES, EdgeDetector
from .recognizer import EDGES, Recognizer, allGestureNames, baseName, zoneOf

addonHandler.initTranslation()

# ---------------------------------------------------------------------------
# Reading controls: (id, label, on by default, only in this app or None)
# ---------------------------------------------------------------------------
READING_CONTROLS = [
	("items", _("Items (default)"), True, None),
	("characters", _("Characters"), True, None),
	("words", _("Words"), True, None),
	("lines", _("Lines"), True, None),
	("sentences", _("Sentences"), False, None),
	("paragraphs", _("Paragraphs"), True, None),
	("controls", _("Controls (Tab key)"), True, None),
	("objects", _("All objects (object navigation)"), False, None),
	("headings", _("Headings"), True, None),
	("links", _("Links"), True, None),
	("formFields", _("Form fields"), True, None),
	("landmarks", _("Landmarks"), True, None),
	("buttons", _("Buttons"), False, None),
	("editFields", _("Edit fields"), False, None),
	("lists", _("Lists"), False, None),
	("tables", _("Tables"), False, None),
	("graphics", _("Graphics"), False, None),
	("tableCells", _("Table cells: across by cell, down by row (Excel and tables)"), True, None),
	("panes", _("Panes and panels (F6)"), True, None),
	("taskbar", _("Taskbar"), True, None),
	("systemTray", _("System tray"), False, None),
	("sheets", _("Sheets (Excel)"), True, "excel"),
	("slides", _("Slides (PowerPoint)"), True, "powerpnt"),
	("speechRate", _("Speech rate"), True, None),
]
CONTROL_INFO = {c[0]: c for c in READING_CONTROLS}
APP_NAMES = {"excel": "Excel", "powerpnt": "PowerPoint", "winword": "Word"}

QUICK_NAV = {
	"headings": "h", "links": "k", "formFields": "f", "landmarks": "d", "buttons": "b",
	"editFields": "e", "lists": "l", "tables": "t", "graphics": "g",
}
TEXT_KEYS = {
	"characters": ("rightArrow", "leftArrow"),
	"words": ("control+rightArrow", "control+leftArrow"),
	"lines": ("downArrow", "upArrow"),
	"sentences": ("alt+downArrow", "alt+upArrow"),
	"paragraphs": ("control+downArrow", "control+upArrow"),
}
# The same NVDA commands as the numpad review keys:
# Numpad 1/3 characters, Numpad 4/6 words, Numpad 7/9 lines.
REVIEW_SCRIPTS = {
	"characters": ("review_nextCharacter", "review_previousCharacter"),
	"words": ("review_nextWord", "review_previousWord"),
	"lines": ("review_nextLine", "review_previousLine"),
}
SIMPLE_KEYS = {
	"controls": ("tab", "shift+tab"),
	"panes": ("f6", "shift+f6"),
	"taskbar": ("windows+t", "shift+windows+t"),
	"sheets": ("control+pageDown", "control+pageUp"),
	"slides": ("pageDown", "pageUp"),
}
TRAY_CLASSES = ("Shell_TrayWnd", "NotifyIconOverflowWindow", "TopLevelWindowForOverflowXamlIsland")
# Windows that are part of Windows itself, never "the application you are working in".
SHELL_CLASSES = set(TRAY_CLASSES) | {
	"Progman", "WorkerW", "Windows.UI.Core.CoreWindow", "XamlExplorerHostIslandWindow",
	"MultitaskingViewFrame", "TaskSwitcherWnd", "ForegroundStaging", "Shell_SecondaryTrayWnd",
	"#32768", "Xaml_WindowedPopupClass",
}
SHELL_APPS = {"nvda", "shellexperiencehost", "startmenuexperiencehost", "searchhost", "searchapp", "lockapp"}


def _role(name):
	return getattr(controlTypes.Role, name, None)


VERTICAL_ROLES = {_role(n) for n in (
	"LISTITEM", "LIST", "TREEVIEWITEM", "TREEVIEW", "MENUITEM", "CHECKMENUITEM", "RADIOMENUITEM",
	"MENU", "POPUPMENU", "RADIOBUTTON", "DATAITEM",
)} - {None}
HORIZONTAL_ROLES = {_role(n) for n in ("TAB", "TABLECELL", "ROWHEADER", "COLUMNHEADER", "MENUBAR")} - {None}
DOCUMENT_ROLES = {_role(n) for n in ("DOCUMENT", "RICHEDIT")} - {None}
RIBBON_ROLES = {_role(n) for n in (
	"TOOLBAR", "TABCONTROL", "TAB", "MENUBAR", "MENU", "POPUPMENU", "MENUITEM", "CHECKMENUITEM", "RADIOMENUITEM",
)} - {None}
WORK_ROLES = DOCUMENT_ROLES | {_role(n) for n in ("TABLECELL", "LISTITEM", "TREEVIEWITEM", "DATAITEM")} - {None}

CONF = "trackpadGestures"


def _listSpec(ids):
	return "string_list(default=list(%s))" % ", ".join('"%s"' % i for i in ids)


config.conf.spec[CONF] = {
	"enableAtStart": "boolean(default=False)",
	"swipeStyle": "option('smart', 'object', 'tab', default='smart')",
	"blockPointer": "boolean(default=True)",
	"allowExternalMouse": "boolean(default=False)",
	"exploreByTouch": "boolean(default=True)",
	"disableWindowsGestures": "boolean(default=True)",
	"savedWindowsGestures": "string(default='')",
	"textMovement": "option('review', 'caret', default='review')",
	"readingControlOrder": _listSpec([c[0] for c in READING_CONTROLS]),
	"readingControlsOff": _listSpec([c[0] for c in READING_CONTROLS if not c[2]]),
}


def orderedControls():
	"""All control ids in the user's order, with any new ones added at the end."""
	order = [i for i in config.conf[CONF]["readingControlOrder"] if i in CONTROL_INFO]
	return order + [c[0] for c in READING_CONTROLS if c[0] not in order]


def enabledControls():
	off = set(config.conf[CONF]["readingControlsOff"])
	known = set(config.conf[CONF]["readingControlOrder"])
	result = []
	for cid in orderedControls():
		if cid in off:
			continue
		if cid not in known and not CONTROL_INFO[cid][2]:
			continue  # brand-new control that is off by default
		result.append(cid)
	return result or ["items"]


def controlLabel(cid, withApp=False):
	info = CONTROL_INFO[cid]
	return info[1]


_plugin = None


def _words(name):
	out = ""
	for ch in name:
		out += (" " + ch.lower()) if ch.isupper() else ch
	return out.replace("finger", "-finger ").replace("  ", " ").strip()


EDGE_LABELS = {
	"edgeSwipeTopLeft": _("swipe down from the top left corner"),
	"edgeSwipeTop": _("swipe down from the top edge"),
	"edgeSwipeTopRight": _("swipe down from the top right corner"),
	"edgeSwipeBottomLeft": _("swipe up from the bottom left corner"),
	"edgeSwipeBottom": _("swipe up from the bottom edge"),
	"edgeSwipeBottomRight": _("swipe up from the bottom right corner"),
	"edgeSwipeLeft": _("swipe right from the left edge"),
	"edgeSwipeRight": _("swipe left from the right edge"),
}


def allNames():
	return allGestureNames() + list(EDGE_NAMES)


def _humanize(name):
	"""swipeUpThenLeft -> 'swipe up then left', 2fingerDoubleTapTop -> '2-finger double tap near the top edge'."""
	if name in EDGE_LABELS:
		return EDGE_LABELS[name]
	if name == "longPress":
		return _("double tap and hold")
	zone = zoneOf(name)
	if zone:
		return _("%s near the %s edge") % (_words(baseName(name)), zone.lower())
	return _words(name)


def _fingers(name):
	return int(name[0]) if name[0].isdigit() else 1


# Sections of the gesture list in settings.
FINGER_GROUPS = [(1, _("One finger")), (2, _("Two fingers")), (3, _("Three fingers")), (4, _("Four fingers"))]
KIND_GROUPS = [
	("simple", _("Taps, swipes and holds")),
	("angular", _("Two-part swipes (angular)")),
	("zone", _("Zones near the edges")),
	("edge", _("Edge swipes (system panels)")),
]


def _kind(name):
	if name.startswith("edgeSwipe"):
		return "edge"
	if zoneOf(name):
		return "zone"
	if "Then" in name:
		return "angular"
	return "simple"


def gestureTree():
	"""[(finger label, [(kind label, [names])])] in display order."""
	names = allNames()
	tree = []
	for n, label in FINGER_GROUPS:
		sections = []
		for kind, kindLabel in KIND_GROUPS:
			items = [g for g in names if _fingers(g) == n and _kind(g) == kind]
			if items:
				sections.append((kindLabel, items))
		tree.append((label, sections))
	return tree


# Command groups shown in the gesture list, so the command choices are easy to find.
COMMAND_GROUPS = [
	(_("Navigation"), (
		"nextItem", "previousItem", "nextByControl", "previousByControl", "nextControl", "previousControl",
		"currentControl", "nextPane", "previousPane", "back", "nextTab", "previousTab", "scrollForward",
		"scrollBack", "browseMode", "elementsList")),
	(_("Reading"), (
		"speakCurrent", "readFromHere", "readFromTop", "reportFocus", "currentLine", "currentSelection",
		"formatting", "title", "statusBar", "stopSpeech", "ocr")),
	(_("Activating"), ("activate", "longPress")),
	(_("Editing"), ("selectionMode", "copy", "paste", "cut", "selectAll", "undo", "redo", "save")),
	(_("Windows and apps"), (
		"edgePanel", "backToApp", "home", "recentApps", "taskView", "menuBar", "taskbar", "systemTray", "notifications",
		"nvdaMenu")),
	(_("Information"), ("timeDate", "battery", "clipboard")),
	(_("Media and volume"), ("playPause", "nextTrack", "previousTrack", "volumeUp", "volumeDown", "mute")),
	(_("Speech"), ("speechMode",)),
	(_("Trackpad gestures"), ("toggle", "turnOff")),
]


GESTURE_LABELS = {n.lower(): _humanize(n) for n in allNames()}
TASKBAR_CLASSES = ("Shell_TrayWnd", "Shell_SecondaryTrayWnd", "NotifyIconOverflowWindow", "TopLevelWindowForOverflowXamlIsland")
EDGE_AGAIN_SECONDS = 20
EDGE_CHECK_MS = 400
EDGE_ACTION_LABELS = {
	"start": _("the Start button"),
	"apps": _("the taskbar"),
	"tray": _("the system tray"),
	"ribbon": _("the ribbon or menu bar"),
	"notifications": _("notifications"),
	"quickSettings": _("quick settings"),
	"widgets": _("widgets"),
}


class TrackpadGesture(inputCore.InputGesture):
	"""A gesture made on the touchpad. Identifiers look like tp:swiperight."""

	def __init__(self, name):
		super(TrackpadGesture, self).__init__()
		self.name = name

	def _get_identifiers(self):
		return (inputCore.normalizeGestureIdentifier("tp:%s" % self.name),)

	def _get_displayName(self):
		return GESTURE_LABELS.get(self.name.lower(), _humanize(self.name))

	@classmethod
	def getDisplayTextForIdentifier(cls, identifier):
		name = identifier.split(":", 1)[-1]
		# Translators: name of the gesture source shown in the Input gestures dialog.
		return (_("Trackpad"), GESTURE_LABELS.get(name.lower(), name))


try:
	inputCore.registerGestureSource("tp", TrackpadGesture)
except Exception:
	log.debugWarning("Trackpad Gestures: could not register gesture source", exc_info=True)


class _Context(object):
	"""What the user is working in right now."""

	def __init__(self):
		focus = api.getFocusObject()
		self.focus = focus
		try:
			self.app = (focus.appModule.appName or "").lower()
		except Exception:
			self.app = ""
		ti = getattr(focus, "treeInterceptor", None)
		self.browse = isinstance(ti, browseMode.BrowseModeTreeInterceptor) and not ti.passThrough
		try:
			states = focus.states
		except Exception:
			states = set()
		self.role = getattr(focus, "role", None)
		self.editable = controlTypes.State.EDITABLE in states
		self.multiline = controlTypes.State.MULTILINE in states or self.role in DOCUMENT_ROLES
		try:
			parentRole = focus.parent.role if focus.parent else None
		except Exception:
			parentRole = None
		self.inMenuBar = parentRole == _role("MENUBAR")
		self.excelCell = self.app == "excel" and self.role in HORIZONTAL_ROLES
		try:
			fg = api.getForegroundObject()
			self.fgClass = fg.windowClassName if fg else ""
		except Exception:
			self.fgClass = ""


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Trackpad Gestures")

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		global _plugin
		_plugin = self
		self._listener = None
		self._controlId = "items"
		self._navSource = "keys"
		self._selecting = False
		self._exploreObj = None
		self._explorePoint = None
		self._exploreQueued = False
		self._appHwnd = None
		self._workFocus = None
		self._edgeState = None
		self._returnSteps = 0
		if globalVars.appArgs.secure:
			return
		NVDASettingsDialog.categoryClasses.append(TrackpadSettingsPanel)
		if config.conf[CONF]["savedWindowsGestures"] and not config.conf[CONF]["enableAtStart"]:
			# NVDA closed unexpectedly last time while gestures were on: put Windows' gestures back.
			self._restoreWindowsGestures()
		if config.conf[CONF]["enableAtStart"]:
			core.callLater(3000, self._start, True)

	def terminate(self):
		global _plugin
		self._stop()
		try:
			NVDASettingsDialog.categoryClasses.remove(TrackpadSettingsPanel)
		except ValueError:
			pass
		_plugin = None
		super(GlobalPlugin, self).terminate()

	# ----- turning on and off -----

	def _start(self, silent=False):
		if self._listener or globalVars.appArgs.secure:
			return bool(self._listener)
		from . import rawinput
		try:
			pads = rawinput.findTouchpads()
		except Exception:
			log.error("Trackpad Gestures: could not list devices", exc_info=True)
			pads = []
		if not pads:
			# Translators: spoken when no precision touchpad is present.
			ui.message(_("No Windows precision touchpad found. Trackpad gestures cannot start."))
			return False
		rec = Recognizer(self._onGesture, self._onExplore, lambda: config.conf[CONF]["exploreByTouch"])
		detector = EdgeDetector(rec, self._onGesture)
		listener = rawinput.TouchpadListener(detector)
		try:
			log.info("Trackpad Gestures: desktop layout: %s" % systemPanels.readLayout().describe())
		except Exception:
			log.debugWarning("Trackpad Gestures: could not read the desktop layout", exc_info=True)
		self._applySettingsTo(listener)
		if not listener.startAndWait():
			ui.message(_("Trackpad gestures could not start. See the NVDA log for details."))
			return False
		self._listener = listener
		if config.conf[CONF]["disableWindowsGestures"]:
			from . import winGestures
			old = winGestures.turnOff()
			if old and not config.conf[CONF]["savedWindowsGestures"]:
				config.conf[CONF]["savedWindowsGestures"] = old
				self._saveConfig()
		tones.beep(880, 60)
		if not silent:
			ui.message(_("Trackpad gestures on"))
		return True

	def _stop(self):
		listener, self._listener = self._listener, None
		if listener:
			listener.stop()
			self._restoreWindowsGestures()
			return True
		return False

	def _restoreWindowsGestures(self):
		saved = config.conf[CONF]["savedWindowsGestures"]
		if not saved:
			return
		from . import winGestures
		winGestures.restore(saved)
		config.conf[CONF]["savedWindowsGestures"] = ""
		self._saveConfig()

	def _saveConfig(self):
		# Saved straight away so Windows' settings can be put back even if NVDA closes unexpectedly.
		try:
			config.conf.save()
		except Exception:
			log.debugWarning("Trackpad Gestures: could not save config", exc_info=True)

	# ----- remembering the application you work in -----

	def event_foreground(self, obj, nextHandler):
		try:
			app = (obj.appModule.appName or "").lower()
			if obj.windowClassName not in SHELL_CLASSES and app not in SHELL_APPS and obj.windowHandle:
				self._appHwnd = obj.windowHandle
		except Exception:
			pass
		nextHandler()

	def event_gainFocus(self, obj, nextHandler):
		try:
			if self._isWorkFocus(obj):
				self._workFocus = obj
		except Exception:
			pass
		nextHandler()

	def _isWorkFocus(self, obj):
		if obj is None:
			return False
		try:
			fg = api.getForegroundObject()
			if fg is None or fg.windowClassName in SHELL_CLASSES:
				return False
			if obj.role in RIBBON_ROLES:
				return False
			return obj.role in WORK_ROLES or controlTypes.State.EDITABLE in obj.states
		except Exception:
			return False

	def _inRibbonOrMenu(self, focus):
		try:
			chain = list(api.getFocusAncestors()) + [focus]
		except Exception:
			chain = [focus]
		for o in chain:
			try:
				if o.role in RIBBON_ROLES or "ribbon" in (o.name or "").lower():
					return True
			except Exception:
				pass
		return False

	def _inDialog(self, focus):
		try:
			return any(o.role == _role("DIALOG") for o in api.getFocusAncestors())
		except Exception:
			return False

	def _activateWindow(self, hwnd):
		import ctypes
		user32 = ctypes.WinDLL("user32")
		for name, args, res in (
			("IsWindow", (ctypes.c_void_p,), ctypes.c_int),
			("IsIconic", (ctypes.c_void_p,), ctypes.c_int),
			("ShowWindow", (ctypes.c_void_p, ctypes.c_int), ctypes.c_int),
			("SetForegroundWindow", (ctypes.c_void_p,), ctypes.c_int),
			("SwitchToThisWindow", (ctypes.c_void_p, ctypes.c_int), None),
		):
			fn = getattr(user32, name)
			fn.argtypes = args
			fn.restype = res
		if not user32.IsWindow(hwnd):
			return False
		if user32.IsIconic(hwnd):
			user32.ShowWindow(hwnd, 9)  # SW_RESTORE
		if not user32.SetForegroundWindow(hwnd):
			user32.SwitchToThisWindow(hwnd, 1)
		return True

	def _returnToWork(self):
		focus = api.getFocusObject()
		if self._isWorkFocus(focus):
			return  # NVDA has already announced where you are
		if self._returnSteps >= 6:
			ui.message(_("Could not get back to the work area. Try Escape or F6."))
			return
		if self._inDialog(focus):
			ui.message(_("You are in a dialog. Close it or finish it first."))
			return
		if self._inRibbonOrMenu(focus):
			self._key("escape")
		elif self._returnSteps == 0 and self._workFocus is not None:
			try:
				self._workFocus.setFocus()
			except Exception:
				self._key("f6")
		else:
			self._key("f6")
		self._returnSteps += 1
		core.callLater(250, self._returnToWork)

	def _applySettingsTo(self, listener):
		listener.blockPointer = config.conf[CONF]["blockPointer"]
		listener.allowExternalMouse = config.conf[CONF]["allowExternalMouse"]

	def applySettings(self):
		if self._listener:
			self._applySettingsTo(self._listener)
			if config.conf[CONF]["disableWindowsGestures"] and not config.conf[CONF]["savedWindowsGestures"]:
				from . import winGestures
				config.conf[CONF]["savedWindowsGestures"] = winGestures.turnOff()
				self._saveConfig()
			elif not config.conf[CONF]["disableWindowsGestures"]:
				self._restoreWindowsGestures()
		if self._controlId not in enabledControls():
			self._controlId = enabledControls()[0]

	# ----- called from the listener thread -----

	def _onGesture(self, name, part=None):
		state = self._edgeState
		if state is not None and state["name"] != name:
			self._edgeState = None  # any other gesture cancels "the same swipe again"
		gesture = TrackpadGesture(name)
		if baseName(name) != name:
			# A zone with nothing assigned does the same as the normal gesture.
			try:
				assigned = gesture.script is not None
			except Exception:
				assigned = False
			if not assigned:
				gesture = TrackpadGesture(baseName(name))
		gesture.edgePart = part
		try:
			inputCore.manager.executeGesture(gesture)
		except inputCore.NoInputGestureAction:
			pass
		except Exception:
			log.error("Trackpad Gestures: error running %s" % name, exc_info=True)

	def _onExplore(self, u, v, first):
		self._explorePoint = (u, v, first)
		if not self._exploreQueued:
			self._exploreQueued = True
			queueHandler.queueFunction(queueHandler.eventQueue, self._doExplore)

	# ----- helpers (main thread) -----

	def _doExplore(self):
		self._exploreQueued = False
		point, self._explorePoint = self._explorePoint, None
		if not point:
			return
		u, v, first = point
		if first:
			self._exploreObj = None
		fg = api.getForegroundObject()
		try:
			area = fg.location if fg else None
		except Exception:
			area = None
		if not area or area[2] <= 0 or area[3] <= 0:
			area = api.getDesktopObject().location
		left, top, width, height = area
		x = int(left + u * (width - 1))
		y = int(top + v * (height - 1))
		try:
			obj = NVDAObject.objectFromPoint(x, y)
		except Exception:
			obj = None
		if not obj or (self._exploreObj is not None and obj == self._exploreObj):
			return
		self._exploreObj = obj
		self._navSource = "explore"
		api.setNavigatorObject(obj)
		speech.cancelSpeech()
		speech.speakObject(obj, reason=controlTypes.OutputReason.MOUSE)

	def _key(self, name):
		try:
			gesture = keyboardHandler.KeyboardInputGesture.fromName(name)
		except Exception:
			log.error("Trackpad Gestures: unknown key %s" % name, exc_info=True)
			return
		try:
			inputCore.manager.emulateGesture(gesture)
		except AttributeError:
			try:
				inputCore.manager.executeGesture(gesture)
			except inputCore.NoInputGestureAction:
				gesture.send()

	def _textKey(self, name):
		"""Press a movement key, adding Shift when selection mode is on."""
		if self._selecting and not name.startswith("shift+"):
			name = "shift+" + name
		self._navSource = "keys"
		self._key(name)

	def _run(self, *names, gesture=None):
		import globalCommands
		for name in names:
			func = getattr(globalCommands.commands, "script_" + name, None)
			if func:
				func(gesture or TrackpadGesture("internal"))
				return True
		log.debugWarning("Trackpad Gestures: none of %s found" % (names,))
		return False

	def _objectNav(self, forward, gesture):
		self._navSource = "object"
		if forward:
			self._run("navigatorObject_nextInFlow", "navigatorObject_next", gesture=gesture)
		else:
			self._run("navigatorObject_previousInFlow", "navigatorObject_previous", gesture=gesture)

	def _moveItem(self, forward, gesture):
		"""Next or previous item, chosen to suit where the focus is."""
		style = config.conf[CONF]["swipeStyle"]
		i = 0 if forward else 1
		if self._controlId == "tableCells":
			ctx = _Context()
			if ctx.excelCell:
				self._textKey(("rightArrow", "leftArrow")[i])
				return
			if ctx.browse or ctx.app == "winword":
				self._key(("control+alt+rightArrow", "control+alt+leftArrow")[i])
				return
		if style == "tab":
			self._navSource = "keys"
			self._key(("tab", "shift+tab")[i])
			return
		if style == "object":
			self._objectNav(forward, gesture)
			return
		ctx = _Context()
		if ctx.browse:
			self._textKey(("downArrow", "upArrow")[i])
		elif ctx.inMenuBar or ctx.role in HORIZONTAL_ROLES:
			# Tabs, menu bar, table and Excel cells: move sideways.
			self._textKey(("rightArrow", "leftArrow")[i])
		elif ctx.role in VERTICAL_ROLES:
			# Lists (like files in Downloads), trees and menus.
			self._textKey(("downArrow", "upArrow")[i])
		elif ctx.editable and ctx.multiline:
			# Documents in Word, Notepad and similar: line by line.
			self._textKey(("downArrow", "upArrow")[i])
		elif ctx.app == "powerpnt" or ctx.editable:
			self._navSource = "keys"
			self._key(("tab", "shift+tab")[i])
		else:
			# Buttons, check boxes and dialogs: move like Tab, but also read text that Tab skips.
			self._objectNav(forward, gesture)

	def _moveByControl(self, forward, gesture):
		cid = self._controlId
		if cid not in enabledControls():
			cid = self._controlId = enabledControls()[0]
		i = 0 if forward else 1
		ctx = _Context()
		appOnly = CONTROL_INFO[cid][3]
		if appOnly and ctx.app != appOnly:
			ui.message(_("%s only works in %s") % (controlLabel(cid), APP_NAMES.get(appOnly, appOnly)))
			return
		if cid == "items":
			self._moveItem(forward, gesture)
		elif cid == "objects":
			self._objectNav(forward, gesture)
		elif cid == "speechRate":
			self._changeRate(5 if forward else -5)
		elif cid in QUICK_NAV:
			if not ctx.browse:
				if ctx.app in ("winword", "outlook"):
					ui.message(_("Press NVDA+Space, or swipe left then right, to use browse mode first"))
				else:
					ui.message(_("%s only work in browse mode, such as web pages") % controlLabel(cid))
				return
			key = QUICK_NAV[cid]
			self._navSource = "keys"
			self._key(key if forward else "shift+" + key)
		elif cid in TEXT_KEYS:
			useReview = (
				cid in REVIEW_SCRIPTS
				and not self._selecting  # selecting needs the real cursor
				and (config.conf[CONF]["textMovement"] == "review" or not (ctx.browse or ctx.editable or ctx.excelCell))
			)
			if useReview:
				self._navSource = "review"
				self._run(REVIEW_SCRIPTS[cid][i], gesture=gesture)
			else:
				self._textKey(TEXT_KEYS[cid][i])
		elif cid == "tableCells":
			# Vertical swipes: row by row (same column).
			if ctx.excelCell:
				self._textKey(("downArrow", "upArrow")[i])
			else:
				self._key(("control+alt+downArrow", "control+alt+upArrow")[i])
		elif cid == "systemTray":
			if ctx.fgClass in TRAY_CLASSES:
				self._key(("rightArrow", "leftArrow")[i])
			else:
				self._key("windows+b")
		elif cid in SIMPLE_KEYS:
			self._navSource = "keys"
			self._key(SIMPLE_KEYS[cid][i])

	def _changeRate(self, step):
		try:
			import synthDriverHandler
			synth = synthDriverHandler.getSynth()
			synth.rate = max(0, min(100, synth.rate + step))
			try:
				synth.saveSettings()
			except Exception:
				pass
			ui.message(_("Rate %d") % synth.rate)
		except Exception:
			log.error("Trackpad Gestures: could not change rate", exc_info=True)

	def _cycleControl(self, step):
		app = _Context().app
		available = [c for c in enabledControls() if CONTROL_INFO[c][3] in (None, app)]
		if not available:
			return
		if self._controlId in available:
			idx = (available.index(self._controlId) + step) % len(available)
		else:
			idx = 0
		self._controlId = available[idx]
		ui.message(controlLabel(self._controlId))

	# ----- scripts: on and off -----

	@script(description=_("Turns trackpad gestures on or off"), gesture="kb:NVDA+shift+g")
	def script_toggle(self, gesture):
		if self._listener:
			self._stop()
			tones.beep(440, 60)
			ui.message(_("Trackpad gestures off"))
		else:
			self._start()

	@script(description=_("Turns trackpad gestures off"), gesture="tp:4fingerDoubleTap")
	def script_turnOff(self, gesture):
		if self._stop():
			tones.beep(440, 60)
			ui.message(_("Trackpad gestures off"))

	# ----- scripts: moving -----

	@script(description=_("Moves to the next item"), gesture="tp:swipeRight")
	def script_nextItem(self, gesture):
		self._moveItem(True, gesture)

	@script(description=_("Moves to the previous item"), gesture="tp:swipeLeft")
	def script_previousItem(self, gesture):
		self._moveItem(False, gesture)

	@script(description=_("Moves forward by the current reading control"), gesture="tp:swipeDown")
	def script_nextByControl(self, gesture):
		self._moveByControl(True, gesture)

	@script(description=_("Moves back by the current reading control"), gesture="tp:swipeUp")
	def script_previousByControl(self, gesture):
		self._moveByControl(False, gesture)

	@script(
		description=_("Selects the next reading control"),
		gestures=["tp:swipeUpThenDown", "tp:3fingerSwipeRight"],
	)
	def script_nextControl(self, gesture):
		self._cycleControl(1)

	@script(
		description=_("Selects the previous reading control"),
		gestures=["tp:swipeDownThenUp", "tp:3fingerSwipeLeft"],
	)
	def script_previousControl(self, gesture):
		self._cycleControl(-1)

	@script(description=_("Speaks the current reading control"))
	def script_currentControl(self, gesture):
		ui.message(controlLabel(self._controlId))

	@script(description=_("Moves to the next pane or panel (F6)"), gesture="tp:4fingerSwipeRight")
	def script_nextPane(self, gesture):
		self._key("f6")

	@script(description=_("Moves to the previous pane or panel (Shift+F6)"), gesture="tp:4fingerSwipeLeft")
	def script_previousPane(self, gesture):
		self._key("shift+f6")

	# ----- scripts: reading and activating -----

	# ----- edge swipes: system panels -----

	@script(
		description=_("Goes to the system panel item at that edge; the same swipe again opens it"),
		gestures=["tp:%s" % n for n in EDGE_NAMES],
	)
	def script_edgePanel(self, gesture):
		name = getattr(gesture, "name", "")
		if not name.startswith("edgeSwipe"):
			ui.message(_("This command only works with edge swipes"))
			return
		layout = systemPanels.readLayout()
		action = systemPanels.actionFor(name, getattr(gesture, "edgePart", None), layout)
		if action is None:
			ui.message(_("Nothing at this edge"))
			return
		state = self._edgeState
		self._edgeState = None
		if (
			state is not None
			and state["name"] == name
			and state["action"] == action
			and time.monotonic() - state["time"] <= EDGE_AGAIN_SECONDS
			and self._edgeStillThere(state)
		):
			self._edgeOpen(state)
			return
		before = self._foregroundHandle()
		if action == "start":
			if not self._focusStartButton():
				self._key("windows+t")
		else:
			self._key(self._edgeKey(action, layout))
		core.callLater(EDGE_CHECK_MS, self._edgeCheck, name, action, layout, before)

	def _edgeKey(self, action, layout):
		win11 = layout.windows >= 11
		return {
			"apps": "windows+t",
			"tray": "windows+b",
			"ribbon": "alt",
			# Windows 10 has one Action Center (Windows+A) for notifications and quick actions,
			# and its touch screen left-edge swipe opens Task View.
			"notifications": "windows+n" if win11 else "windows+a",
			"quickSettings": "windows+a",
			"widgets": "windows+w" if win11 else "windows+tab",
		}[action]

	def _foregroundHandle(self):
		try:
			fg = api.getForegroundObject()
			return fg.windowHandle if fg else None
		except Exception:
			return None

	def _inTaskbar(self):
		try:
			objs = [api.getForegroundObject(), api.getFocusObject()] + list(api.getFocusAncestors())
		except Exception:
			return False
		for o in objs:
			try:
				if o is not None and o.windowClassName in TASKBAR_CLASSES:
					return True
			except Exception:
				pass
		return False

	def _isStartButton(self, obj):
		try:
			return getattr(obj, "UIAAutomationId", "") == "StartButton" or (obj.name or "").strip().lower() == "start"
		except Exception:
			return False

	def _focusStartButton(self):
		"""Puts focus on the Start button through UI Automation, without opening the Start menu."""
		try:
			import ctypes
			import UIAHandler
			handler = UIAHandler.handler
			if not handler:
				return False
			user32 = ctypes.WinDLL("user32")
			find = user32.FindWindowW
			find.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p)
			find.restype = ctypes.c_void_p
			tray = find("Shell_TrayWnd", None)
			if not tray:
				return False
			client = handler.clientObject
			root = client.ElementFromHandle(tray)
			UIA_AutomationIdPropertyId, TreeScope_Descendants = 30011, 4
			button = root.FindFirst(TreeScope_Descendants, client.CreatePropertyCondition(UIA_AutomationIdPropertyId, "StartButton"))
			if not button:
				return False
			button.SetFocus()
			return True
		except Exception:
			log.debugWarning("Trackpad Gestures: could not focus the Start button", exc_info=True)
			return False

	def _edgeLanded(self, action, before):
		if action in ("start", "apps", "tray"):
			return self._inTaskbar()
		if action == "ribbon":
			return self._inRibbonOrMenu(api.getFocusObject())
		now = self._foregroundHandle()
		return now is not None and now != before

	def _edgeStillThere(self, state):
		action = state["action"]
		if action in ("start", "apps", "tray"):
			return self._inTaskbar()
		if action == "ribbon":
			return self._inRibbonOrMenu(api.getFocusObject())
		return self._foregroundHandle() == state["window"]

	def _edgeCheck(self, name, action, layout, before):
		if self._edgeLanded(action, before):
			self._edgeState = {"name": name, "action": action, "time": time.monotonic(), "window": self._foregroundHandle()}
			return
		try:
			focus = api.getFocusObject()
			fg = api.getForegroundObject()
			details = "focus %r (role %s, window class %s), foreground window class %s" % (
				focus.name, focus.role, focus.windowClassName, fg.windowClassName if fg else None)
		except Exception:
			details = "focus details unavailable"
		log.warning("Trackpad Gestures: edge swipe %s (%s) did not land. Layout: %s. %s" % (
			name, action, layout.describe(), details))
		if action in ("start", "apps", "tray"):
			ui.message(_("Could not reach the taskbar"))
		else:
			ui.message(_("Could not open %s") % EDGE_ACTION_LABELS.get(action, action))

	def _edgeOpen(self, state):
		if state["action"] == "start" and not self._isStartButton(api.getFocusObject()):
			self._key("control+escape")  # opens the Start menu from anywhere on the taskbar
		else:
			self._key("enter")

	@script(
		description=_("Returns to the application you are working in, and to its document, sheet or list"),
		gesture="tp:2fingerLongPress",
	)
	def script_backToApp(self, gesture):
		self._returnSteps = 0
		hwnd = self._appHwnd
		fg = api.getForegroundObject()
		if fg is not None and hwnd and fg.windowHandle == hwnd:
			self._returnToWork()
			return
		if not hwnd or not self._activateWindow(hwnd):
			ui.message(_("No application to return to"))
			return
		core.callLater(400, self._returnToWork)

	@script(description=_("Speaks the current item"), gesture="tp:tap")
	def script_speakCurrent(self, gesture):
		self._run("navigatorObject_current", gesture=gesture)

	@script(description=_("Reports formatting (font, style) at the cursor"), gesture="tp:tripleTap")
	def script_formatting(self, gesture):
		self._run("reportFormatting", gesture=gesture)

	@script(description=_("Activates the current item"), gesture="tp:doubleTap")
	def script_activate(self, gesture):
		ctx = _Context()
		if self._navSource in ("object", "explore"):
			self._run("review_activate", gesture=gesture)
		elif ctx.browse or ctx.role in VERTICAL_ROLES or ctx.inMenuBar:
			self._key("enter")
		else:
			self._run("review_activate", gesture=gesture)

	@script(description=_("Opens the context menu (like long press)"), gesture="tp:longPress")
	def script_longPress(self, gesture):
		self._key("shift+f10")

	@script(description=_("Reads from the current position"), gesture="tp:3fingerSwipeDown")
	def script_readFromHere(self, gesture):
		self._run("sayAll", gesture=gesture)

	@script(description=_("Reads from the top"), gesture="tp:3fingerSwipeUp")
	def script_readFromTop(self, gesture):
		self._key("control+home")
		core.callLater(250, self._run, "sayAll")

	@script(description=_("Speaks the focused item"), gesture="tp:4fingerTap")
	def script_reportFocus(self, gesture):
		self._run("reportCurrentFocus", gesture=gesture)

	@script(description=_("Speaks the window title"), gesture="tp:4fingerSwipeUp")
	def script_title(self, gesture):
		self._run("title", gesture=gesture)

	@script(description=_("Reads the status bar (page, word count, cell)"), gesture="tp:swipeUpThenRight")
	def script_statusBar(self, gesture):
		self._run("reportStatusLine", gesture=gesture)

	@script(description=_("Stops speech"), gesture="tp:2fingerTap")
	def script_stopSpeech(self, gesture):
		speech.cancelSpeech()

	# ----- scripts: system and windows -----

	@script(description=_("Goes back"), gesture="tp:swipeDownThenLeft")
	def script_back(self, gesture):
		self._key("alt+leftArrow" if _Context().browse else "escape")

	@script(description=_("Shows the desktop (home)"), gesture="tp:swipeUpThenLeft")
	def script_home(self, gesture):
		self._key("windows+d")

	@script(description=_("Switches to the previous app"), gesture="tp:swipeLeftThenUp")
	def script_recentApps(self, gesture):
		self._key("alt+tab")

	@script(description=_("Opens notifications"), gesture="tp:swipeRightThenDown")
	def script_notifications(self, gesture):
		self._key("windows+n")

	@script(description=_("Goes to the menu bar or ribbon (Alt)"), gesture="tp:2fingerDoubleTapTop")
	def script_menuBar(self, gesture):
		self._key("alt")

	@script(description=_("Goes to the taskbar"), gesture="tp:2fingerDoubleTapBottom")
	def script_taskbar(self, gesture):
		self._key("windows+t")

	@script(description=_("Opens Task View to choose a window"), gesture="tp:2fingerDoubleTapLeft")
	def script_taskView(self, gesture):
		self._key("windows+tab")

	@script(description=_("Goes to the system tray"), gesture="tp:2fingerDoubleTapRight")
	def script_systemTray(self, gesture):
		self._key("windows+b")

	@script(description=_("Opens the NVDA menu"), gestures=["tp:3fingerTap", "tp:swipeDownThenRight"])
	def script_nvdaMenu(self, gesture):
		self._run("showGui", gesture=gesture)

	@script(description=_("Switches between browse mode and focus mode"), gesture="tp:swipeLeftThenRight")
	def script_browseMode(self, gesture):
		self._key("NVDA+space")

	@script(description=_("Opens the elements list (headings, links, comments)"), gesture="tp:swipeRightThenLeft")
	def script_elementsList(self, gesture):
		self._key("NVDA+f7")

	# ----- scripts: media and scrolling -----

	@script(description=_("Plays or pauses media"), gesture="tp:2fingerDoubleTap")
	def script_playPause(self, gesture):
		self._mediaKey(0xB3)

	@script(description=_("Scrolls forward (Page Down)"), gesture="tp:2fingerSwipeUp")
	def script_scrollForward(self, gesture):
		self._textKey("pageDown")

	@script(description=_("Scrolls back (Page Up)"), gesture="tp:2fingerSwipeDown")
	def script_scrollBack(self, gesture):
		self._textKey("pageUp")

	@script(description=_("Goes to the next tab"), gesture="tp:2fingerSwipeLeft")
	def script_nextTab(self, gesture):
		self._key("control+tab")

	@script(description=_("Goes to the previous tab"), gesture="tp:2fingerSwipeRight")
	def script_previousTab(self, gesture):
		self._key("control+shift+tab")

	# ----- scripts: editing -----

	@script(description=_("Turns selection mode on or off"), gesture="tp:2fingerTripleTap")
	def script_selectionMode(self, gesture):
		self._selecting = not self._selecting
		if self._selecting:
			ui.message(_("Selection on. Swipes now select text."))
		else:
			ui.message(_("Selection off"))

	@script(description=_("Copies (Control+C)"), gesture="tp:3fingerDoubleTap")
	def script_copy(self, gesture):
		self._key("control+c")
		ui.message(_("Copied"))

	@script(description=_("Pastes (Control+V)"), gesture="tp:3fingerTripleTap")
	def script_paste(self, gesture):
		self._key("control+v")

	@script(description=_("Cuts (Control+X)"))
	def script_cut(self, gesture):
		self._key("control+x")

	@script(description=_("Selects all (Control+A)"))
	def script_selectAll(self, gesture):
		self._key("control+a")

	@script(description=_("Undoes (Control+Z)"), gesture="tp:swipeLeftThenDown")
	def script_undo(self, gesture):
		self._key("control+z")

	@script(description=_("Redoes (Control+Y)"), gesture="tp:swipeRightThenUp")
	def script_redo(self, gesture):
		self._key("control+y")

	@script(description=_("Saves (Control+S)"), gesture="tp:4fingerSwipeDown")
	def script_save(self, gesture):
		self._key("control+s")

	# ----- scripts with no gesture yet: assign them in the gesture list -----

	def _mediaKey(self, vk):
		keyboardHandler.KeyboardInputGesture(set(), vk, 0, True).send()

	@script(description=_("Speaks the time and date"))
	def script_timeDate(self, gesture):
		self._run("dateTime", gesture=gesture)

	@script(description=_("Speaks the battery status"))
	def script_battery(self, gesture):
		self._run("say_battery_status", gesture=gesture)

	@script(description=_("Reads the clipboard"))
	def script_clipboard(self, gesture):
		self._run("reportClipboardText", gesture=gesture)

	@script(description=_("Recognises the text on screen (OCR)"))
	def script_ocr(self, gesture):
		self._run("recognizeWithUwpOcr", gesture=gesture)

	@script(description=_("Reads the current line"))
	def script_currentLine(self, gesture):
		self._run("review_currentLine", gesture=gesture)

	@script(description=_("Reads the selected text"))
	def script_currentSelection(self, gesture):
		self._run("reportCurrentSelection", gesture=gesture)

	@script(description=_("Changes the speech mode (talk, beeps, off)"))
	def script_speechMode(self, gesture):
		self._run("speechMode", gesture=gesture)

	@script(description=_("Turns the volume up"))
	def script_volumeUp(self, gesture):
		self._mediaKey(0xAF)

	@script(description=_("Turns the volume down"))
	def script_volumeDown(self, gesture):
		self._mediaKey(0xAE)

	@script(description=_("Mutes or unmutes the volume"))
	def script_mute(self, gesture):
		self._mediaKey(0xAD)

	@script(description=_("Next track"))
	def script_nextTrack(self, gesture):
		self._mediaKey(0xB0)

	@script(description=_("Previous track"))
	def script_previousTrack(self, gesture):
		self._mediaKey(0xB1)


# ---------------------------------------------------------------------------
# Gesture assignments. They are kept in NVDA's own gesture map, so they also show
# in NVDA's Input gestures dialog, and the two always agree.
# ---------------------------------------------------------------------------

def _ident(name):
	return inputCore.normalizeGestureIdentifier("tp:" + name)


def defaultBindings():
	result = {}
	for attr in dir(GlobalPlugin):
		if attr.startswith("script_"):
			for g in getattr(getattr(GlobalPlugin, attr), "gestures", None) or ():
				if g.lower().startswith("tp:"):
					result[inputCore.normalizeGestureIdentifier(g)] = attr[len("script_"):]
	return result


def _isOurs(cls):
	return cls is GlobalPlugin or (
		getattr(cls, "__name__", "") == "GlobalPlugin" and getattr(cls, "__module__", "") == GlobalPlugin.__module__)


def currentBinding(name, defaults):
	ident = _ident(name)
	try:
		for cls, scriptName in inputCore.manager.userGestureMap.getScriptsForGesture(ident):
			if _isOurs(cls):
				return scriptName
	except Exception:
		log.debugWarning("Trackpad Gestures: could not read gesture map", exc_info=True)
	return defaults.get(ident)


def setBinding(name, scriptName, defaults):
	ident = _ident(name)
	gmap = inputCore.manager.userGestureMap
	for cls, old in list(gmap.getScriptsForGesture(ident)):
		if _isOurs(cls):
			try:
				gmap.remove(ident, GlobalPlugin.__module__, "GlobalPlugin", old)
			except Exception:
				log.debugWarning("Trackpad Gestures: could not remove %s" % ident, exc_info=True)
	if scriptName != defaults.get(ident):
		gmap.add(ident, GlobalPlugin.__module__, "GlobalPlugin", scriptName)


def scriptDescription(scriptName):
	func = getattr(GlobalPlugin, "script_%s" % scriptName, None)
	return (getattr(func, "__doc__", None) or scriptName) if func else scriptName


class TrackpadSettingsPanel(SettingsPanel):
	# Translators: title of the settings panel.
	title = _("Trackpad Gestures")

	def makeSettings(self, settingsSizer):
		helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		conf = config.conf[CONF]
		self.enableAtStart = helper.addItem(
			wx.CheckBox(self, label=_("&Turn on trackpad gestures when NVDA starts")))
		self.enableAtStart.SetValue(conf["enableAtStart"])
		self._styles = [
			("smart", _("Smart: suits lists, documents, Excel and web pages")),
			("object", _("Always object navigation (like NVDA touch)")),
			("tab", _("Always Tab and Shift+Tab")),
		]
		self.swipeStyle = helper.addLabeledControl(
			_("Swipe right and left &moves by:"), wx.Choice, choices=[s[1] for s in self._styles])
		keys = [s[0] for s in self._styles]
		self.swipeStyle.SetSelection(keys.index(conf["swipeStyle"]) if conf["swipeStyle"] in keys else 0)

		# Reading controls: check to include, Move up / Move down to reorder.
		self._order = orderedControls()
		enabled = set(enabledControls())
		self.controlsList = helper.addLabeledControl(
			_("&Reading controls (Space to turn on or off):"), wx.CheckListBox,
			choices=[controlLabel(c) for c in self._order])
		for idx, cid in enumerate(self._order):
			self.controlsList.Check(idx, cid in enabled)
		if self._order:
			self.controlsList.SetSelection(0)
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		self.upButton = buttons.addButton(self, label=_("Move &up"))
		self.downButton = buttons.addButton(self, label=_("Move &down"))
		self.resetButton = buttons.addButton(self, label=_("Reset reading controls"))
		self.upButton.Bind(wx.EVT_BUTTON, lambda e: self._move(-1))
		self.downButton.Bind(wx.EVT_BUTTON, lambda e: self._move(1))
		self.resetButton.Bind(wx.EVT_BUTTON, self._reset)
		helper.addItem(buttons)

		self._textModes = [
			("review", _("Review cursor, like Numpad 1 and 3, 4 and 6, 7 and 9")),
			("caret", _("System cursor, like the arrow keys")),
		]
		self.textMovement = helper.addLabeledControl(
			_("Characters, words and lines &read with:"), wx.Choice, choices=[m[1] for m in self._textModes])
		self.textMovement.SetSelection(0 if conf["textMovement"] == "review" else 1)
		self.explore = helper.addItem(
			wx.CheckBox(self, label=_("&Explore by touch (touch and hold, then slide)")))
		self.explore.SetValue(conf["exploreByTouch"])
		self.disableWin = helper.addItem(wx.CheckBox(
			self, label=_("Turn off &Windows' own three and four finger gestures while trackpad gestures are on")))
		self.disableWin.SetValue(conf["disableWindowsGestures"])
		self.blockPointer = helper.addItem(wx.CheckBox(
			self, label=_("&Stop the touchpad moving the mouse pointer and clicking while gestures are on")))
		self.blockPointer.SetValue(conf["blockPointer"])
		self.allowMouse = helper.addItem(wx.CheckBox(
			self, label=_("Allow an external &mouse while gestures are on")))
		self.allowMouse.SetValue(conf["allowExternalMouse"])
		self._makeGestureList(helper)

	# ----- gesture list -----

	def _makeGestureList(self, helper):
		self._defaults = defaultBindings()
		self._pending = {}
		self._commands = [(None, _("Nothing"))]
		for groupLabel, names in COMMAND_GROUPS:
			for sn in names:
				if hasattr(GlobalPlugin, "script_%s" % sn):
					self._commands.append((sn, "%s: %s" % (groupLabel, scriptDescription(sn))))
		self.tree = helper.addLabeledControl(
			_("&Gestures (choose a gesture, then press Tab to choose its command):"), wx.TreeCtrl,
			style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_SINGLE | wx.TR_LINES_AT_ROOT, size=(-1, 260))
		root = self.tree.AddRoot(_("Gestures"))
		self._items = {}
		for fingerLabel, sections in gestureTree():
			fingerItem = self.tree.AppendItem(root, fingerLabel)
			for kindLabel, names in sections:
				kindItem = self.tree.AppendItem(fingerItem, kindLabel)
				for name in names:
					item = self.tree.AppendItem(kindItem, self._itemLabel(name))
					self.tree.SetItemData(item, name)
					self._items[name] = item
		self.command = helper.addLabeledControl(
			_("&Command for this gesture:"), wx.Choice, choices=[c[1] for c in self._commands])
		self.command.Disable()
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		self.resetGestureButton = buttons.addButton(self, label=_("Reset this gesture"))
		self.resetAllButton = buttons.addButton(self, label=_("Reset all gestures"))
		helper.addItem(buttons)
		self.resetGestureButton.Disable()
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self._onGestureSelected)
		self.command.Bind(wx.EVT_CHOICE, self._onCommandChosen)
		self.resetGestureButton.Bind(wx.EVT_BUTTON, self._onResetGesture)
		self.resetAllButton.Bind(wx.EVT_BUTTON, self._onResetAll)

	def _binding(self, name):
		if name in self._pending:
			return self._pending[name]
		return currentBinding(name, self._defaults)

	def _commandLabel(self, name, scriptName):
		if scriptName:
			return scriptDescription(scriptName)
		if baseName(name) != name:
			# Translators: an edge zone with no command of its own.
			return _("nothing of its own, so it does the same as %s") % _humanize(baseName(name))
		return _("nothing")

	def _itemLabel(self, name):
		return "%s: %s" % (_humanize(name), self._commandLabel(name, self._binding(name)))

	def _selectedName(self):
		item = self.tree.GetSelection()
		if not item or not item.IsOk():
			return None
		return self.tree.GetItemData(item)

	def _onGestureSelected(self, evt):
		name = self._selectedName()
		if not name:
			self.command.Disable()
			self.resetGestureButton.Disable()
			return
		self.command.Enable()
		self.resetGestureButton.Enable()
		current = self._binding(name)
		keys = [c[0] for c in self._commands]
		self.command.SetSelection(keys.index(current) if current in keys else wx.NOT_FOUND)

	def _setPending(self, name, scriptName):
		self._pending[name] = scriptName
		self.tree.SetItemText(self._items[name], self._itemLabel(name))

	def _onCommandChosen(self, evt):
		name = self._selectedName()
		idx = self.command.GetSelection()
		if name and idx != wx.NOT_FOUND:
			self._setPending(name, self._commands[idx][0])

	def _onResetGesture(self, evt):
		name = self._selectedName()
		if name:
			self._setPending(name, self._defaults.get(_ident(name)))
			self._onGestureSelected(None)
			ui.message(self._itemLabel(name))

	def _onResetAll(self, evt):
		for name in self._items:
			self._setPending(name, self._defaults.get(_ident(name)))
		self._onGestureSelected(None)
		ui.message(_("All gestures reset. Press OK to save."))

	def _saveGestures(self):
		if not self._pending:
			return
		try:
			for name, scriptName in self._pending.items():
				setBinding(name, scriptName, self._defaults)
			inputCore.manager.userGestureMap.save()
		except Exception:
			log.error("Trackpad Gestures: could not save gestures", exc_info=True)
			ui.message(_("Could not save the gesture changes. See the NVDA log."))
		self._pending = {}

	def _checked(self):
		return {self._order[i] for i in range(len(self._order)) if self.controlsList.IsChecked(i)}

	def _fill(self, checked, select):
		self.controlsList.Set([controlLabel(c) for c in self._order])
		for idx, cid in enumerate(self._order):
			self.controlsList.Check(idx, cid in checked)
		self.controlsList.SetSelection(select)

	def _move(self, step):
		idx = self.controlsList.GetSelection()
		new = idx + step
		if idx < 0 or new < 0 or new >= len(self._order):
			return
		checked = self._checked()
		self._order[idx], self._order[new] = self._order[new], self._order[idx]
		self._fill(checked, new)
		self.controlsList.SetFocus()
		ui.message(_("%s, position %d") % (controlLabel(self._order[new]), new + 1))

	def _reset(self, evt):
		self._order = [c[0] for c in READING_CONTROLS]
		self._fill({c[0] for c in READING_CONTROLS if c[2]}, 0)
		self.controlsList.SetFocus()
		ui.message(_("Reading controls reset"))

	def onSave(self):
		conf = config.conf[CONF]
		conf["enableAtStart"] = self.enableAtStart.GetValue()
		conf["swipeStyle"] = self._styles[max(0, self.swipeStyle.GetSelection())][0]
		conf["exploreByTouch"] = self.explore.GetValue()
		conf["textMovement"] = self._textModes[max(0, self.textMovement.GetSelection())][0]
		conf["blockPointer"] = self.blockPointer.GetValue()
		conf["disableWindowsGestures"] = self.disableWin.GetValue()
		conf["allowExternalMouse"] = self.allowMouse.GetValue()
		checked = self._checked()
		conf["readingControlOrder"] = list(self._order)
		conf["readingControlsOff"] = [c for c in self._order if c not in checked]
		self._saveGestures()
		if _plugin:
			_plugin.applySettings()
