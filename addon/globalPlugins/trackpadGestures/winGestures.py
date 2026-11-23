# Trackpad Gestures for NVDA - turns Windows' own three and four finger touchpad
# gestures off while trackpad gestures are on, and puts them back afterwards.
# These are the same settings as Settings > Bluetooth & devices > Touchpad.

import ctypes
import threading
import winreg

from logHandler import log

KEY = r"Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad"
VALUES = ("ThreeFingerSlideEnabled", "ThreeFingerTapEnabled", "FourFingerSlideEnabled", "FourFingerTapEnabled")
MISSING = "missing"


def _notifyWindows():
	"""Tell Windows the settings changed (in the background so NVDA never waits)."""
	def run():
		try:
			user32 = ctypes.WinDLL("user32")
			fn = user32.SendMessageTimeoutW
			fn.argtypes = (ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_wchar_p,
				ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p)
			fn.restype = ctypes.c_ssize_t
			HWND_BROADCAST, WM_SETTINGCHANGE, SMTO_ABORTIFHUNG = 0xFFFF, 0x001A, 0x0002
			fn(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "PrecisionTouchPad", SMTO_ABORTIFHUNG, 500, None)
		except Exception:
			log.debugWarning("Trackpad Gestures: settings broadcast failed", exc_info=True)
	threading.Thread(target=run, name="TrackpadGesturesNotify", daemon=True).start()


def turnOff():
	"""Sets all four gestures to Nothing. Returns the old values as 'name=value;...'."""
	saved = []
	try:
		with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, KEY, 0, winreg.KEY_READ | winreg.KEY_WRITE) as k:
			for name in VALUES:
				try:
					old, kind = winreg.QueryValueEx(k, name)
					saved.append("%s=%s" % (name, int(old)) if kind == winreg.REG_DWORD else "%s=%s" % (name, MISSING))
				except FileNotFoundError:
					saved.append("%s=%s" % (name, MISSING))
				winreg.SetValueEx(k, name, 0, winreg.REG_DWORD, 0)
	except Exception:
		log.error("Trackpad Gestures: could not turn off Windows gestures", exc_info=True)
		return ""
	_notifyWindows()
	return ";".join(saved)


def restore(saved):
	"""Puts back the values returned by turnOff."""
	if not saved:
		return
	try:
		with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, KEY, 0, winreg.KEY_WRITE) as k:
			for item in saved.split(";"):
				name, _sep, value = item.partition("=")
				if name not in VALUES:
					continue
				if value == MISSING:
					try:
						winreg.DeleteValue(k, name)
					except FileNotFoundError:
						pass
				else:
					winreg.SetValueEx(k, name, 0, winreg.REG_DWORD, int(value))
	except Exception:
		log.error("Trackpad Gestures: could not restore Windows gestures", exc_info=True)
		return
	_notifyWindows()
