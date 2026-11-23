# Edge swipe detection, shared by Trackpad Gestures for NVDA and Setu Trackpad Gestures (Orca).
# Pure Python: no NVDA, Orca, Windows or Linux imports.
#
# EdgeDetector sits in front of recognizer.Recognizer and offers the same three things the
# touchpad listener uses: feed(contacts, aspect, now), tick(now) and touching. Every frame goes on
# to the recognizer as normal. When a one-finger touch ends and qualifies as an edge swipe, the
# recognizer is told to forget that touch, so it does not also report a swipe or a tap, and
# onEdge(name, part) is called instead.
#
#   recognizer = Recognizer(onGesture, onExplore, exploreEnabled)
#   detector = EdgeDetector(recognizer, onEdge)
#   listener = TouchpadListener(detector)   # instead of TouchpadListener(recognizer)
#
# Contacts are {contactId: (u, v)} with u, v from 0 to 1 (u left to right, v top to bottom).
# aspect is the touchpad's height divided by its width.
#
# Rules for an edge swipe:
# - One finger only, from touch down to lift.
# - Starts within the outer EDGE_BAND (10%) of the touchpad: top, bottom, left or right band.
# - Moves inward (down from the top, up from the bottom, right from the left edge, left from the
#   right edge) by at least MIN_INWARD (5%) and at most MAX_INWARD (40%) of the touchpad along that
#   direction, in under MAX_TIME (0.8 seconds), with the inward movement larger than the sideways
#   movement. Inward and sideways are compared in real distance on the pad, using aspect.
# - On the top and bottom edges, a start in the left CORNER (28%) is the left corner, in the right
#   28% the right corner, otherwise the middle.
# Longer swipes that start near an edge stay normal swipes, and taps near an edge are unchanged.

EDGE_BAND = 0.10
MIN_INWARD = 0.05
MAX_INWARD = 0.40
MAX_TIME = 0.8
CORNER = 0.28

EDGE_NAMES = (
	"edgeSwipeTopLeft", "edgeSwipeTop", "edgeSwipeTopRight",
	"edgeSwipeBottomLeft", "edgeSwipeBottom", "edgeSwipeBottomRight",
	"edgeSwipeLeft", "edgeSwipeRight",
)

# part: where along the edge the swipe started.
# "start" = left (top and bottom edges) or top (left and right edges); "end" = right or bottom.
PARTS = ("start", "middle", "end")


def partAlong(position):
	if position < CORNER:
		return "start"
	if position > 1 - CORNER:
		return "end"
	return "middle"


def edgeName(edge, part):
	"""edge is 'top', 'bottom', 'left' or 'right'."""
	if edge in ("left", "right"):
		return "edgeSwipe" + edge.capitalize()
	suffix = {"start": "Left", "middle": "", "end": "Right"}[part]
	return "edgeSwipe" + edge.capitalize() + suffix


def edgeOfName(name):
	"""edgeSwipeTopRight -> ('top', 'end'); edgeSwipeLeft -> ('left', None)."""
	rest = name[len("edgeSwipe"):]
	for edge in ("Top", "Bottom"):
		if rest.startswith(edge):
			tail = rest[len(edge):]
			return edge.lower(), {"Left": "start", "": "middle", "Right": "end"}[tail]
	return rest.lower(), None


def classify(start, end, duration, aspect):
	"""Returns (name, part) for a one-finger touch from start to end (u, v), or None."""
	if duration >= MAX_TIME:
		return None
	u0, v0 = start
	du, dv = end[0] - u0, end[1] - v0
	candidates = []
	# (edge, inward fraction of the pad, inward real distance, sideways real distance, position along edge)
	if v0 < EDGE_BAND:
		candidates.append(("top", dv, dv * aspect, abs(du), u0))
	if v0 > 1 - EDGE_BAND:
		candidates.append(("bottom", -dv, -dv * aspect, abs(du), u0))
	if u0 < EDGE_BAND:
		candidates.append(("left", du, du, abs(dv) * aspect, v0))
	if u0 > 1 - EDGE_BAND:
		candidates.append(("right", -du, -du, abs(dv) * aspect, v0))
	best = None
	for edge, inward, inwardReal, sideReal, along in candidates:
		if MIN_INWARD <= inward <= MAX_INWARD and inwardReal > sideReal:
			if best is None or inwardReal > best[1]:
				best = (edge, inwardReal, along)
	if best is None:
		return None
	edge, _real, along = best
	part = partAlong(along)
	return edgeName(edge, part), part


class _Touch(object):
	__slots__ = ("t0", "cid", "start", "last", "single")

	def __init__(self, now, contacts):
		self.t0 = now
		self.single = len(contacts) == 1
		self.cid = next(iter(contacts)) if self.single else None
		self.start = contacts[self.cid] if self.single else None
		self.last = self.start


class EdgeDetector(object):

	def __init__(self, recognizer, onEdge):
		self.recognizer = recognizer
		self.onEdge = onEdge
		self._touch = None

	@property
	def touching(self):
		return self._touch is not None or self.recognizer.touching

	def feed(self, contacts, aspect=0.6, now=None):
		if now is None:
			now = self.recognizer.clock()
		t = self._touch
		if contacts:
			if t is None:
				self._touch = _Touch(now, contacts)
			elif t.single:
				if len(contacts) != 1 or t.cid not in contacts:
					t.single = False  # a second finger, or a different finger
				else:
					t.last = contacts[t.cid]
			self.recognizer.feed(contacts, aspect, now)
			return
		# All fingers lifted.
		self._touch = None
		if t is not None and t.single:
			result = classify(t.start, t.last, now - t.t0, aspect)
			if result:
				self._forget()
				self.onEdge(*result)
				return
		self.recognizer.feed(contacts, aspect, now)

	def tick(self, now=None):
		self.recognizer.tick(now)

	def _forget(self):
		# The recognizer keeps the current touch in _session; dropping it means no swipe or tap is
		# reported for this touch. An earlier tap still waiting for a possible double tap is kept.
		self.recognizer._session = None
