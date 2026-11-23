# Trackpad Gestures for NVDA - reads finger positions from a Windows
# precision touchpad using the Raw Input API, and (optionally) stops the
# touchpad from moving the mouse pointer or clicking while gestures are on.
#
# Everything here runs on its own background thread with its own hidden
# message-only window. Private copies of user32/hid are used so NVDA's own
# ctypes settings are never changed.

import ctypes
import struct
import threading
import time
from ctypes import wintypes

from logHandler import log

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_TIMER = 0x0113
WM_INPUT = 0x00FF
HWND_MESSAGE = wintypes.HWND(-3)
RID_INPUT = 0x10000003
RIDI_PREPARSEDDATA = 0x20000005
RIDI_DEVICEINFO = 0x2000000B
RIM_TYPEHID = 2
RIDEV_REMOVE = 0x00000001
RIDEV_INPUTSINK = 0x00000100
WH_MOUSE_LL = 14
LLMHF_INJECTED = 0x01
HIDP_STATUS_SUCCESS = 0x00110000
HidP_Input = 0

PAGE_GENERIC = 0x01
PAGE_DIGITIZER = 0x0D
USAGE_TOUCHPAD = 0x05
USAGE_X = 0x30
USAGE_Y = 0x31
USAGE_TIP = 0x42
USAGE_CONFIDENCE = 0x47
USAGE_CONTACT_ID = 0x51
USAGE_CONTACT_COUNT = 0x54

TIMER_ID = 1
TIMER_MS = 40
POINTER_GRACE = 0.6  # seconds after a touch during which the pointer stays blocked


class WNDCLASSEXW(ctypes.Structure):
	_fields_ = [
		("cbSize", wintypes.UINT), ("style", wintypes.UINT), ("lpfnWndProc", WNDPROC),
		("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE),
		("hIcon", wintypes.HICON), ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
		("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR), ("hIconSm", wintypes.HICON),
	]


class RAWINPUTDEVICE(ctypes.Structure):
	_fields_ = [
		("usUsagePage", wintypes.USHORT), ("usUsage", wintypes.USHORT),
		("dwFlags", wintypes.DWORD), ("hwndTarget", wintypes.HWND),
	]


class RAWINPUTHEADER(ctypes.Structure):
	_fields_ = [
		("dwType", wintypes.DWORD), ("dwSize", wintypes.DWORD),
		("hDevice", wintypes.HANDLE), ("wParam", wintypes.WPARAM),
	]


class RAWINPUTDEVICELIST(ctypes.Structure):
	_fields_ = [("hDevice", wintypes.HANDLE), ("dwType", wintypes.DWORD)]


class RID_DEVICE_INFO_HID(ctypes.Structure):
	_fields_ = [
		("dwVendorId", wintypes.DWORD), ("dwProductId", wintypes.DWORD), ("dwVersionNumber", wintypes.DWORD),
		("usUsagePage", wintypes.USHORT), ("usUsage", wintypes.USHORT),
	]


class _RID_UNION(ctypes.Union):
	_fields_ = [("hid", RID_DEVICE_INFO_HID), ("_pad", wintypes.DWORD * 6)]


class RID_DEVICE_INFO(ctypes.Structure):
	_fields_ = [("cbSize", wintypes.DWORD), ("dwType", wintypes.DWORD), ("u", _RID_UNION)]


class MSLLHOOKSTRUCT(ctypes.Structure):
	_fields_ = [
		("pt", wintypes.POINT), ("mouseData", wintypes.DWORD), ("flags", wintypes.DWORD),
		("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t),
	]


class HIDP_CAPS(ctypes.Structure):
	_fields_ = [
		("Usage", wintypes.USHORT), ("UsagePage", wintypes.USHORT),
		("InputReportByteLength", wintypes.USHORT), ("OutputReportByteLength", wintypes.USHORT),
		("FeatureReportByteLength", wintypes.USHORT), ("Reserved", wintypes.USHORT * 17),
		("NumberLinkCollectionNodes", wintypes.USHORT),
		("NumberInputButtonCaps", wintypes.USHORT), ("NumberInputValueCaps", wintypes.USHORT),
		("NumberInputDataIndices", wintypes.USHORT),
		("NumberOutputButtonCaps", wintypes.USHORT), ("NumberOutputValueCaps", wintypes.USHORT),
		("NumberOutputDataIndices", wintypes.USHORT),
		("NumberFeatureButtonCaps", wintypes.USHORT), ("NumberFeatureValueCaps", wintypes.USHORT),
		("NumberFeatureDataIndices", wintypes.USHORT),
	]


class HIDP_VALUE_CAPS(ctypes.Structure):
	_fields_ = [
		("UsagePage", wintypes.USHORT), ("ReportID", ctypes.c_ubyte), ("IsAlias", ctypes.c_ubyte),
		("BitField", wintypes.USHORT), ("LinkCollection", wintypes.USHORT),
		("LinkUsage", wintypes.USHORT), ("LinkUsagePage", wintypes.USHORT),
		("IsRange", ctypes.c_ubyte), ("IsStringRange", ctypes.c_ubyte),
		("IsDesignatorRange", ctypes.c_ubyte), ("IsAbsolute", ctypes.c_ubyte),
		("HasNull", ctypes.c_ubyte), ("Reserved", ctypes.c_ubyte),
		("BitSize", wintypes.USHORT), ("ReportCount", wintypes.USHORT),
		("Reserved2", wintypes.USHORT * 5),
		("UnitsExp", wintypes.ULONG), ("Units", wintypes.ULONG),
		("LogicalMin", wintypes.LONG), ("LogicalMax", wintypes.LONG),
		("PhysicalMin", wintypes.LONG), ("PhysicalMax", wintypes.LONG),
		("u", wintypes.USHORT * 8),  # Range.UsageMin/UsageMax or NotRange.Usage
	]


_api = None


class _Api(object):
	"""Private ctypes bindings, so NVDA's shared ctypes.windll objects stay untouched."""

	def __init__(self):
		u = ctypes.WinDLL("user32", use_last_error=True)
		k = ctypes.WinDLL("kernel32", use_last_error=True)
		h = ctypes.WinDLL("hid")
		W = wintypes
		P = ctypes.POINTER

		def f(dll, name, res, *args):
			fn = getattr(dll, name)
			fn.restype = res
			fn.argtypes = args
			setattr(self, name, fn)

		f(u, "RegisterClassExW", W.ATOM, P(WNDCLASSEXW))
		f(u, "UnregisterClassW", W.BOOL, W.LPCWSTR, W.HINSTANCE)
		f(u, "CreateWindowExW", W.HWND, W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, ctypes.c_int, ctypes.c_int,
			ctypes.c_int, ctypes.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID)
		f(u, "DestroyWindow", W.BOOL, W.HWND)
		f(u, "DefWindowProcW", LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
		f(u, "GetMessageW", W.BOOL, P(W.MSG), W.HWND, W.UINT, W.UINT)
		f(u, "TranslateMessage", W.BOOL, P(W.MSG))
		f(u, "DispatchMessageW", LRESULT, P(W.MSG))
		f(u, "PostMessageW", W.BOOL, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
		f(u, "PostQuitMessage", None, ctypes.c_int)
		f(u, "SetTimer", ctypes.c_size_t, W.HWND, ctypes.c_size_t, W.UINT, ctypes.c_void_p)
		f(u, "KillTimer", W.BOOL, W.HWND, ctypes.c_size_t)
		f(u, "RegisterRawInputDevices", W.BOOL, P(RAWINPUTDEVICE), W.UINT, W.UINT)
		f(u, "GetRawInputData", W.UINT, W.HANDLE, W.UINT, ctypes.c_void_p, P(W.UINT), W.UINT)
		f(u, "GetRawInputDeviceInfoW", W.UINT, W.HANDLE, W.UINT, ctypes.c_void_p, P(W.UINT))
		f(u, "GetRawInputDeviceList", W.UINT, ctypes.c_void_p, P(W.UINT), W.UINT)
		f(u, "SetWindowsHookExW", W.HANDLE, ctypes.c_int, HOOKPROC, W.HINSTANCE, W.DWORD)
		f(u, "UnhookWindowsHookEx", W.BOOL, W.HANDLE)
		f(u, "CallNextHookEx", LRESULT, W.HANDLE, ctypes.c_int, W.WPARAM, W.LPARAM)
		f(k, "GetModuleHandleW", W.HMODULE, W.LPCWSTR)
		f(h, "HidP_GetCaps", ctypes.c_long, ctypes.c_void_p, P(HIDP_CAPS))
		f(h, "HidP_GetValueCaps", ctypes.c_long, ctypes.c_int, P(HIDP_VALUE_CAPS), P(W.USHORT), ctypes.c_void_p)
		f(h, "HidP_GetUsageValue", ctypes.c_long, ctypes.c_int, W.USHORT, W.USHORT, W.USHORT, P(W.ULONG),
			ctypes.c_void_p, ctypes.c_void_p, W.ULONG)
		f(h, "HidP_GetUsages", ctypes.c_long, ctypes.c_int, W.USHORT, W.USHORT, P(W.USHORT), P(W.ULONG),
			ctypes.c_void_p, ctypes.c_void_p, W.ULONG)
		f(h, "HidP_MaxUsageListLength", W.ULONG, ctypes.c_int, W.USHORT, ctypes.c_void_p)


def api():
	global _api
	if _api is None:
		_api = _Api()
	return _api


def _ok(status):
	return (status & 0xFFFFFFFF) == HIDP_STATUS_SUCCESS


def findTouchpads():
	"""Return the raw input handles of all precision touchpads."""
	a = api()
	n = wintypes.UINT(0)
	size = ctypes.sizeof(RAWINPUTDEVICELIST)
	if a.GetRawInputDeviceList(None, ctypes.byref(n), size) != 0 or n.value == 0:
		return []
	arr = (RAWINPUTDEVICELIST * n.value)()
	got = a.GetRawInputDeviceList(arr, ctypes.byref(n), size)
	if got == 0xFFFFFFFF:
		return []
	found = []
	for d in arr[:got]:
		if d.dwType != RIM_TYPEHID:
			continue
		info = RID_DEVICE_INFO()
		info.cbSize = ctypes.sizeof(RID_DEVICE_INFO)
		sz = wintypes.UINT(info.cbSize)
		r = a.GetRawInputDeviceInfoW(d.hDevice, RIDI_DEVICEINFO, ctypes.byref(info), ctypes.byref(sz))
		if r in (0, 0xFFFFFFFF):
			continue
		if info.u.hid.usUsagePage == PAGE_DIGITIZER and info.u.hid.usUsage == USAGE_TOUCHPAD:
			found.append(d.hDevice)
	return found


class Touchpad(object):
	"""Knows how to pull finger data out of one touchpad's HID reports."""

	def __init__(self, handle):
		a = self.a = api()
		size = wintypes.UINT(0)
		a.GetRawInputDeviceInfoW(handle, RIDI_PREPARSEDDATA, None, ctypes.byref(size))
		if not size.value:
			raise RuntimeError("no preparsed data")
		self._ppdBuf = ctypes.create_string_buffer(size.value)
		r = a.GetRawInputDeviceInfoW(handle, RIDI_PREPARSEDDATA, self._ppdBuf, ctypes.byref(size))
		if r in (0, 0xFFFFFFFF):
			raise RuntimeError("could not read preparsed data")
		self.ppd = ctypes.cast(self._ppdBuf, ctypes.c_void_p)
		caps = HIDP_CAPS()
		if not _ok(a.HidP_GetCaps(self.ppd, ctypes.byref(caps))):
			raise RuntimeError("HidP_GetCaps failed")
		if caps.UsagePage != PAGE_DIGITIZER or caps.Usage != USAGE_TOUCHPAD:
			raise RuntimeError("not a touchpad")
		n = wintypes.USHORT(caps.NumberInputValueCaps)
		vcaps = (HIDP_VALUE_CAPS * max(1, n.value))()
		if not _ok(a.HidP_GetValueCaps(HidP_Input, vcaps, ctypes.byref(n), self.ppd)):
			raise RuntimeError("HidP_GetValueCaps failed")
		self.countLink = None
		fingers = {}
		for vc in vcaps[:n.value]:
			usages = range(vc.u[0], vc.u[1] + 1) if vc.IsRange else (vc.u[0],)
			link = vc.LinkCollection
			for usage in usages:
				if vc.UsagePage == PAGE_DIGITIZER and usage == USAGE_CONTACT_COUNT:
					if self.countLink is None:
						self.countLink = link
				elif vc.UsagePage == PAGE_DIGITIZER and usage == USAGE_CONTACT_ID:
					fingers.setdefault(link, {})["id"] = True
				elif vc.UsagePage == PAGE_GENERIC and usage in (USAGE_X, USAGE_Y):
					key = "x" if usage == USAGE_X else "y"
					fingers.setdefault(link, {}).setdefault(
						key, (vc.LogicalMin, vc.LogicalMax, vc.PhysicalMin, vc.PhysicalMax))
		self.links = sorted(l for l, f in fingers.items() if "id" in f and "x" in f and "y" in f)
		if not self.links:
			raise RuntimeError("no finger collections found")
		xr = fingers[self.links[0]]["x"]
		yr = fingers[self.links[0]]["y"]
		self.xMin, self.xMax = xr[0], max(xr[1], xr[0] + 1)
		self.yMin, self.yMax = yr[0], max(yr[1], yr[0] + 1)
		w = (xr[3] - xr[2]) if xr[3] > xr[2] else (self.xMax - self.xMin)
		h = (yr[3] - yr[2]) if yr[3] > yr[2] else (self.yMax - self.yMin)
		self.aspect = (float(h) / w) if w > 0 else 0.6
		self.maxUsages = a.HidP_MaxUsageListLength(HidP_Input, PAGE_DIGITIZER, self.ppd) or 32
		# Frame assembly state (some touchpads split one frame over several reports).
		self.frame = {}
		self.remaining = 0
		self.hasConfidence = False

	def _value(self, page, link, usage, rep, length):
		v = wintypes.ULONG(0)
		if _ok(self.a.HidP_GetUsageValue(HidP_Input, page, link, usage, ctypes.byref(v), self.ppd, rep, length)):
			return v.value
		return None

	def parse(self, report):
		"""Returns (contactCount or None, [(id, tip, confident, u, v), ...])."""
		length = len(report)
		buf = (ctypes.c_char * length).from_buffer_copy(report)
		rep = ctypes.cast(buf, ctypes.c_void_p)
		count = None
		if self.countLink is not None:
			count = self._value(PAGE_DIGITIZER, self.countLink, USAGE_CONTACT_COUNT, rep, length)
		out = []
		for link in self.links:
			arr = (wintypes.USHORT * self.maxUsages)()
			ln = wintypes.ULONG(self.maxUsages)
			if not _ok(self.a.HidP_GetUsages(HidP_Input, PAGE_DIGITIZER, link, arr, ctypes.byref(ln), self.ppd, rep, length)):
				continue
			on = set(arr[:ln.value])
			cid = self._value(PAGE_DIGITIZER, link, USAGE_CONTACT_ID, rep, length)
			x = self._value(PAGE_GENERIC, link, USAGE_X, rep, length)
			y = self._value(PAGE_GENERIC, link, USAGE_Y, rep, length)
			if cid is None or x is None or y is None:
				continue
			u = min(1.0, max(0.0, float(x - self.xMin) / (self.xMax - self.xMin)))
			v = min(1.0, max(0.0, float(y - self.yMin) / (self.yMax - self.yMin)))
			out.append((cid, USAGE_TIP in on, USAGE_CONFIDENCE in on, u, v))
		return count, out


class TouchpadListener(threading.Thread):

	def __init__(self, recognizer):
		super(TouchpadListener, self).__init__(name="TrackpadGesturesListener")
		self.daemon = True
		self.recognizer = recognizer
		self.blockPointer = True
		self.allowExternalMouse = False
		self.lastTouch = 0.0
		self.error = None
		self.hwnd = None
		self._ready = threading.Event()
		self._devices = {}
		self._hook = None
		self._wndProc = WNDPROC(self._windowProc)
		self._hookProc = HOOKPROC(self._mouseHook)
		self._className = "NVDATrackpadGestures_%d" % id(self)

	# ----- control from NVDA's main thread -----

	def startAndWait(self, timeout=5.0):
		self.start()
		self._ready.wait(timeout)
		if self.error is None and not self.hwnd:
			self.error = "listener did not start"
		return self.error is None

	def stop(self):
		if self.hwnd:
			api().PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
		self.join(3.0)

	# ----- background thread -----

	def run(self):
		a = api()
		hInst = a.GetModuleHandleW(None)
		try:
			wc = WNDCLASSEXW()
			wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
			wc.lpfnWndProc = self._wndProc
			wc.hInstance = hInst
			wc.lpszClassName = self._className
			if not a.RegisterClassExW(ctypes.byref(wc)):
				raise ctypes.WinError(ctypes.get_last_error())
			hwnd = a.CreateWindowExW(0, self._className, "", 0, 0, 0, 0, 0, HWND_MESSAGE, None, hInst, None)
			if not hwnd:
				raise ctypes.WinError(ctypes.get_last_error())
			rid = RAWINPUTDEVICE(PAGE_DIGITIZER, USAGE_TOUCHPAD, RIDEV_INPUTSINK, hwnd)
			if not a.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE)):
				a.DestroyWindow(hwnd)
				raise ctypes.WinError(ctypes.get_last_error())
			self._hook = a.SetWindowsHookExW(WH_MOUSE_LL, self._hookProc, hInst, 0)
			if not self._hook:
				log.warning("Trackpad Gestures: could not install mouse hook; the pointer will not be blocked")
			a.SetTimer(hwnd, TIMER_ID, TIMER_MS, None)
			self.hwnd = hwnd
		except Exception as e:
			self.error = str(e)
			log.error("Trackpad Gestures: failed to start", exc_info=True)
			self._ready.set()
			a.UnregisterClassW(self._className, hInst)
			return
		self._ready.set()
		msg = wintypes.MSG()
		while a.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
			a.TranslateMessage(ctypes.byref(msg))
			a.DispatchMessageW(ctypes.byref(msg))
		if self._hook:
			a.UnhookWindowsHookEx(self._hook)
			self._hook = None
		a.UnregisterClassW(self._className, hInst)
		self.hwnd = None

	def _windowProc(self, hwnd, msg, wParam, lParam):
		a = api()
		try:
			if msg == WM_INPUT:
				self._onInput(lParam)
			elif msg == WM_TIMER:
				self.recognizer.tick(time.monotonic())
				return 0
			elif msg == WM_CLOSE:
				a.DestroyWindow(hwnd)
				return 0
			elif msg == WM_DESTROY:
				a.KillTimer(hwnd, TIMER_ID)
				rid = RAWINPUTDEVICE(PAGE_DIGITIZER, USAGE_TOUCHPAD, RIDEV_REMOVE, None)
				a.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE))
				a.PostQuitMessage(0)
				return 0
		except Exception:
			log.error("Trackpad Gestures: error in window procedure", exc_info=True)
		return a.DefWindowProcW(hwnd, msg, wParam, lParam)

	def _device(self, handle):
		if handle not in self._devices:
			try:
				self._devices[handle] = Touchpad(handle)
			except Exception as e:
				log.debugWarning("Trackpad Gestures: ignoring device: %s" % e)
				self._devices[handle] = None
		return self._devices[handle]

	def _onInput(self, hRawInput):
		a = api()
		hdrSize = ctypes.sizeof(RAWINPUTHEADER)
		size = wintypes.UINT(0)
		a.GetRawInputData(hRawInput, RID_INPUT, None, ctypes.byref(size), hdrSize)
		if not size.value:
			return
		buf = ctypes.create_string_buffer(size.value)
		if a.GetRawInputData(hRawInput, RID_INPUT, buf, ctypes.byref(size), hdrSize) != size.value:
			return
		hdr = RAWINPUTHEADER.from_buffer(buf)
		if hdr.dwType != RIM_TYPEHID:
			return
		dev = self._device(hdr.hDevice)
		if dev is None:
			return
		raw = buf.raw
		sizeHid, count = struct.unpack_from("<II", raw, hdrSize)
		offset = hdrSize + 8
		now = time.monotonic()
		self.lastTouch = now
		for i in range(count):
			report = raw[offset + i * sizeHid: offset + (i + 1) * sizeHid]
			contactCount, contacts = dev.parse(report)
			self._assemble(dev, contactCount, contacts, now)

	def _assemble(self, dev, contactCount, contacts, now):
		if contactCount is None:
			dev.frame = {}
			dev.remaining = len(contacts)
		elif contactCount > 0:
			dev.frame = {}
			dev.remaining = contactCount
		elif dev.remaining <= 0:
			# Count of zero outside a frame: nothing is touching.
			self.recognizer.feed({}, dev.aspect, now)
			return
		take = contacts[:dev.remaining]
		for cid, tip, confident, u, v in take:
			if confident:
				dev.hasConfidence = True
			if tip and (confident or not dev.hasConfidence):
				dev.frame[cid] = (u, v)
		dev.remaining -= len(take)
		if dev.remaining <= 0:
			self.recognizer.feed(dev.frame, dev.aspect, now)

	def _mouseHook(self, nCode, wParam, lParam):
		try:
			if nCode == 0 and self.blockPointer:
				info = MSLLHOOKSTRUCT.from_address(lParam)
				if not (info.flags & LLMHF_INJECTED):
					if (
						not self.allowExternalMouse
						or self.recognizer.touching
						or time.monotonic() - self.lastTouch < POINTER_GRACE
					):
						return 1
		except Exception:
			pass
		return api().CallNextHookEx(None, nCode, wParam, lParam)
