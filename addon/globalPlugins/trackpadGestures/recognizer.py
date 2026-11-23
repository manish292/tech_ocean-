# Trackpad Gestures for NVDA - gesture recognizer.
# Pure Python, no NVDA or Windows imports, so it can be tested anywhere.
#
# Input: "frames" = dict of contactId -> (u, v) where u and v are 0..1
# (u = left to right, v = top to bottom). An empty dict means all fingers are up.
# Output: gesture names such as "swipeRight", "doubleTap", "2fingerSwipeUp",
# "swipeUpThenLeft", "longPress", plus explore callbacks.

import math
import time

TAP_MAX_MOVE = 0.06        # in touchpad widths
TAP_MAX_TIME_ONE = 0.30    # seconds
TAP_MAX_TIME_MULTI = 0.45
MULTI_TAP_WINDOW = 0.35    # time allowed between taps of a double/triple tap
SWIPE_MIN = 0.14
SWIPE_MAX_TIME = 1.2
EXPLORE_DELAY = 0.35       # hold still this long to start exploring
LONG_PRESS_TIME = 0.5
CORNER_MIN = 0.08
EXPLORE_INTERVAL = 0.05
SESSION_GIVE_UP = 3.0      # no reports for this long: forget the touch

DIRECTIONS = ("Up", "Down", "Left", "Right")
TAP_WORDS = {1: "Tap", 2: "DoubleTap", 3: "TripleTap"}
EDGES = ("Top", "Bottom", "Left", "Right")
EDGE_SIZE = 0.22  # a two-finger double tap this close to an edge gets an edge name


def _dist(a, b):
	return math.hypot(b[0] - a[0], b[1] - a[1])


def _direction(dx, dy):
	if abs(dx) >= abs(dy):
		return "Right" if dx > 0 else "Left"
	return "Down" if dy > 0 else "Up"


def allGestureNames():
	"""Every gesture name the recognizer can produce."""
	names = ["tap", "doubleTap", "tripleTap", "longPress"]
	names += ["swipe" + d for d in DIRECTIONS]
	names += ["swipe%sThen%s" % (a, b) for a in DIRECTIONS for b in DIRECTIONS if a != b]
	for n in (2, 3, 4):
		names += ["%dfinger%s" % (n, w) for w in TAP_WORDS.values()]
		names += ["%dfingerSwipe%s" % (n, d) for d in DIRECTIONS]
		names.append("%dfingerLongPress" % n)
	# Zones: the same gesture made near one edge of the touchpad.
	names += ["doubleTap" + e for e in EDGES]
	for n in (2, 3, 4):
		names += ["%dfingerDoubleTap%s" % (n, e) for e in EDGES]
		names += ["%dfingerLongPress%s" % (n, e) for e in EDGES]
	return names


def baseName(name):
	"""doubleTapTop -> doubleTap; other names are returned unchanged."""
	for e in EDGES:
		if name.endswith(e) and ("DoubleTap" in name or "LongPress" in name or name.startswith("doubleTap")):
			return name[:-len(e)]
	return name


def zoneOf(name):
	for e in EDGES:
		if baseName(name) != name and name.endswith(e):
			return e
	return ""


def edgeOf(u, v):
	if v < EDGE_SIZE:
		return "Top"
	if v > 1 - EDGE_SIZE:
		return "Bottom"
	if u < EDGE_SIZE:
		return "Left"
	if u > 1 - EDGE_SIZE:
		return "Right"
	return ""


def tapName(fingers, count):
	word = TAP_WORDS[min(count, 3)]
	if fingers == 1:
		return word[0].lower() + word[1:]
	return "%dfinger%s" % (fingers, word)


class _Contact(object):
	__slots__ = ("start", "startUV", "last", "lastUV", "maxDist")

	def __init__(self, pos, uv):
		self.start = pos
		self.startUV = uv
		self.last = pos
		self.lastUV = uv
		self.maxDist = 0.0


class _Session(object):
	def __init__(self, now, followsTap):
		self.t0 = now
		self.lastTime = now
		self.contacts = {}
		self.maxFingers = 0
		self.path = []
		self.exploring = False
		self.followsTap = followsTap
		self.current = 0
		self.fired = False


class Recognizer(object):

	def __init__(self, onGesture, onExplore=None, exploreEnabled=lambda: True, clock=time.monotonic):
		self.onGesture = onGesture
		self.onExplore = onExplore
		self.exploreEnabled = exploreEnabled
		self.clock = clock
		self._session = None
		self._pending = None  # [fingers, count, endTime]
		self._lastExplore = 0.0

	@property
	def touching(self):
		return self._session is not None

	# ----- input -----

	def feed(self, contacts, aspect=0.6, now=None):
		if now is None:
			now = self.clock()
		s = self._session
		if not contacts:
			if s is not None:
				self._endSession(now)
			return
		if s is not None and now - s.lastTime > SESSION_GIVE_UP and set(contacts) - set(s.contacts):
			# We missed the lift report of an old touch; drop it quietly.
			self._session = s = None
		if s is None:
			s = self._startSession(now)
		s.lastTime = now
		for cid, (u, v) in contacts.items():
			pos = (u, v * aspect)
			c = s.contacts.get(cid)
			if c is None:
				c = s.contacts[cid] = _Contact(pos, (u, v))
			c.last = pos
			c.lastUV = (u, v)
			c.maxDist = max(c.maxDist, _dist(c.start, pos))
		s.maxFingers = max(s.maxFingers, len(contacts))
		s.current = len(contacts)
		self._multiHold(s, now)
		if s.maxFingers == 1 and len(contacts) == 1:
			c = s.contacts[next(iter(contacts))]
			s.path.append(c.last)
			self._explore(s, c, now)

	def tick(self, now=None):
		"""Call regularly (about every 40 ms)."""
		if now is None:
			now = self.clock()
		s = self._session
		if s is not None:
			if now - s.lastTime > SESSION_GIVE_UP:
				self._session = None
				return
			self._multiHold(s, now)
			if s.maxFingers == 1 and len(s.contacts) == 1:
				self._explore(s, next(iter(s.contacts.values())), now)
		elif self._pending is not None and now - self._pending[2] > MULTI_TAP_WINDOW:
			self._flushPending()

	# ----- internals -----

	def _explore(self, s, c, now):
		if not s.exploring:
			if (
				s.followsTap is None
				and now - s.t0 >= EXPLORE_DELAY
				and c.maxDist < SWIPE_MIN * 0.8
				and self.exploreEnabled()
			):
				s.exploring = True
				self._lastExplore = 0.0
				if self.onExplore:
					self.onExplore(c.lastUV[0], c.lastUV[1], True)
					self._lastExplore = now
			return
		if self.onExplore and now - self._lastExplore >= EXPLORE_INTERVAL:
			self._lastExplore = now
			self.onExplore(c.lastUV[0], c.lastUV[1], False)

	def _multiHold(self, s, now):
		"""Two to four fingers held still: fires once, while the fingers are still down."""
		if (
			not s.fired
			and 2 <= s.maxFingers <= 4
			and s.current == s.maxFingers
			and now - s.t0 >= LONG_PRESS_TIME
			and all(c.maxDist < TAP_MAX_MOVE * 1.5 for c in s.contacts.values())
		):
			s.fired = True
			self._flushPending()
			cs = list(s.contacts.values())
			u = sum(c.startUV[0] for c in cs) / len(cs)
			v = sum(c.startUV[1] for c in cs) / len(cs)
			self.onGesture("%dfingerLongPress%s" % (s.maxFingers, edgeOf(u, v)))

	def _startSession(self, now):
		followsTap = None
		if self._pending is not None:
			if now - self._pending[2] <= MULTI_TAP_WINDOW:
				followsTap = self._pending
			else:
				self._flushPending()
		self._session = _Session(now, followsTap)
		return self._session

	def _flushPending(self):
		p = self._pending
		self._pending = None
		if p is not None:
			name = tapName(p[0], p[1])
			if p[1] == 2:
				name += edgeOf(*p[3])
			self.onGesture(name)

	def _endSession(self, now):
		s = self._session
		self._session = None
		if s.fired:
			return
		result = self._classify(s)
		kind = result[0] if result else None
		if kind == "tap":
			n = result[1]
			cs = list(s.contacts.values())
			centre = (sum(c.startUV[0] for c in cs) / len(cs), sum(c.startUV[1] for c in cs) / len(cs))
			p = self._pending
			if p is not None and s.followsTap is p and p[0] == n:
				p[1] += 1
				p[2] = now
				if p[1] >= 3:
					self._flushPending()
			else:
				self._flushPending()
				self._pending = [n, 1, now, centre]
			return
		if kind == "hold":
			p = self._pending
			if p is not None and s.followsTap is p and p[0] == 1 and p[1] == 1:
				self._pending = None
				self.onGesture("longPress")
				return
		self._flushPending()
		if kind == "gesture":
			self.onGesture(result[1])

	def _classify(self, s):
		dur = s.lastTime - s.t0
		n = s.maxFingers
		contacts = list(s.contacts.values())
		if not contacts or n > 4:
			return None
		if n == 1:
			c = contacts[0]
			if s.exploring:
				return None
			if c.maxDist < TAP_MAX_MOVE:
				if dur <= TAP_MAX_TIME_ONE:
					return ("tap", 1)
				if dur >= LONG_PRESS_TIME:
					return ("hold",)
				return None
			if dur > SWIPE_MAX_TIME or len(s.path) < 2:
				return None
			return self._classifyPath(s.path)
		# Two, three or four fingers.
		if all(c.maxDist < TAP_MAX_MOVE * 1.5 for c in contacts) and dur <= TAP_MAX_TIME_MULTI:
			return ("tap", n)
		if dur > SWIPE_MAX_TIME:
			return None
		dx = sum(c.last[0] - c.start[0] for c in contacts) / len(contacts)
		dy = sum(c.last[1] - c.start[1] for c in contacts) / len(contacts)
		if math.hypot(dx, dy) >= SWIPE_MIN * 0.8:
			return ("gesture", "%dfingerSwipe%s" % (n, _direction(dx, dy)))
		return None

	def _classifyPath(self, path):
		start, end = path[0], path[-1]
		far = max(path, key=lambda p: _dist(start, p))
		farDist = _dist(start, far)
		if farDist < SWIPE_MIN:
			return None
		chord = _dist(start, end)
		if chord < farDist * 0.5:
			# Out and back, like "up then down".
			corner = far
		else:
			# Find the point furthest from the straight line start-end.
			ex, ey = end[0] - start[0], end[1] - start[1]
			length = math.hypot(ex, ey) or 1e-9

			def offLine(p):
				return abs((p[0] - start[0]) * ey - (p[1] - start[1]) * ex) / length
			corner = max(path, key=offLine)
			if offLine(corner) < CORNER_MIN:
				return ("gesture", "swipe" + _direction(ex, ey))
		seg1 = (corner[0] - start[0], corner[1] - start[1])
		seg2 = (end[0] - corner[0], end[1] - corner[1])
		if math.hypot(*seg1) >= CORNER_MIN and math.hypot(*seg2) >= CORNER_MIN:
			d1, d2 = _direction(*seg1), _direction(*seg2)
			if d1 != d2:
				return ("gesture", "swipe%sThen%s" % (d1, d2))
		if chord >= SWIPE_MIN:
			return ("gesture", "swipe" + _direction(end[0] - start[0], end[1] - start[1]))
		return None
