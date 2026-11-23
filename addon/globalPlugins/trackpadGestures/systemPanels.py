# Trackpad Gestures for NVDA - which system panel each edge swipe reaches.
# Windows-only parts (registry, version) are kept in readLayout(); actionFor() is pure.

import sys

from .edges import edgeOfName

TASKBAR_EDGES = {0: "left", 1: "top", 2: "right", 3: "bottom"}


class Layout(object):
	def __init__(self, windows=11, taskbarEdge="bottom", centred=True):
		self.windows = windows
		self.taskbarEdge = taskbarEdge
		self.centred = centred

	def describe(self):
		return "Windows %d, taskbar on the %s, %s" % (
			self.windows, self.taskbarEdge, "centred" if self.centred else "left aligned")


def _windowsVersion():
	try:
		import winVersion
		ver = winVersion.getWinVer()
		build = ver.build
	except Exception:
		build = sys.getwindowsversion().build
	return 11 if build >= 22000 else 10


def readLayout():
	"""Reads the taskbar position and alignment from the registry."""
	import winreg
	layout = Layout(windows=_windowsVersion())
	explorer = r"Software\Microsoft\Windows\CurrentVersion\Explorer"
	try:
		with winreg.OpenKey(winreg.HKEY_CURRENT_USER, explorer + r"\StuckRects3") as k:
			data, _kind = winreg.QueryValueEx(k, "Settings")
			layout.taskbarEdge = TASKBAR_EDGES.get(data[12], "bottom")
	except Exception:
		layout.taskbarEdge = "bottom"
	if layout.windows >= 11:
		try:
			with winreg.OpenKey(winreg.HKEY_CURRENT_USER, explorer + r"\Advanced") as k:
				value, _kind = winreg.QueryValueEx(k, "TaskbarAl")
				layout.centred = value != 0
		except Exception:
			layout.centred = True  # Windows 11's own default
	else:
		layout.centred = False  # Windows 10 taskbars are always left aligned
	return layout


# Actions: start, apps, tray (taskbar); ribbon, notifications, quickSettings, widgets (free edges).
TASKBAR_ORDER = {"start": "start", "middle": "apps", "end": "tray"}
TOP_ORDER = {"start": "ribbon", "middle": "notifications", "end": "quickSettings"}


def actionFor(name, part, layout):
	"""Which action an edge swipe does for this desktop layout, or None for nothing there.

	part is where along the edge the swipe started ('start', 'middle' or 'end'). For the top and
	bottom edges it is also in the name; for the left and right edges it comes from the detector.
	"""
	edge, namePart = edgeOfName(name)
	part = namePart or part or "middle"
	taskbar = layout.taskbarEdge
	if edge == taskbar:
		# Horizontal taskbar: left corner, middle, right corner.
		# Vertical taskbar: top corner, middle, bottom corner.
		return TASKBAR_ORDER[part]
	# The three top actions go on the top edge, or on the bottom edge if the taskbar is at the top.
	freeHorizontal = "bottom" if taskbar == "top" else "top"
	if edge == freeHorizontal:
		return TOP_ORDER[part]
	if edge == "left":
		return "widgets"
	if edge == "right":
		return "notifications"
	return None
