exec(open("tests/test_plugin.py").read().split("for fl, secs")[0])
sys.modules["inputCore"].normalizeGestureIdentifier=lambda s: s.lower()
from trackpadGestures import systemPanels as sp
from trackpadGestures.edges import EDGE_NAMES
bad=0
def check(label, got, want):
    global bad; ok=got==want; bad+=not ok; print("OK " if ok else "BAD", label, got)
L=sp.Layout
names=["edgeSwipeTopLeft","edgeSwipeTop","edgeSwipeTopRight","edgeSwipeBottomLeft","edgeSwipeBottom","edgeSwipeBottomRight"]
check("bottom taskbar, Win11", [sp.actionFor(n,None,L(11,"bottom")) for n in names]+[sp.actionFor("edgeSwipeLeft","middle",L(11,"bottom")), sp.actionFor("edgeSwipeRight","start",L(11,"bottom"))],
      ["ribbon","notifications","quickSettings","start","apps","tray","widgets","notifications"])
check("top taskbar: taskbar on top, top actions move to bottom", [sp.actionFor(n,None,L(11,"top")) for n in names],
      ["start","apps","tray","ribbon","notifications","quickSettings"])
check("left taskbar: vertical order on the left edge", [sp.actionFor("edgeSwipeLeft",p,L(10,"left")) for p in ("start","middle","end")], ["start","apps","tray"])
check("left taskbar: top still free, bottom has nothing", ([sp.actionFor(n,None,L(10,"left")) for n in names[:3]], sp.actionFor("edgeSwipeBottom",None,L(10,"left"))),
      (["ribbon","notifications","quickSettings"], None))
check("right taskbar", [sp.actionFor("edgeSwipeRight",p,L(11,"right")) for p in ("start","middle","end")]+[sp.actionFor("edgeSwipeLeft","middle",L(11,"right"))], ["start","apps","tray","widgets"])
g=tg.GlobalPlugin.__new__(tg.GlobalPlugin)
check("Win10 keys", [g._edgeKey(a, L(10)) for a in ("notifications","quickSettings","widgets","apps","tray","ribbon")], ["windows+a","windows+a","windows+tab","windows+t","windows+b","alt"])
check("Win11 keys", [g._edgeKey(a, L(11)) for a in ("notifications","quickSettings","widgets")], ["windows+n","windows+a","windows+w"])
one=dict(tg.gestureTree()[0][1])
check("One finger sections", [k for k,_ in tg.gestureTree()[0][1]], ["Taps, swipes and holds","Two-part swipes (angular)","Zones near the edges","Edge swipes (system panels)"])
check("edge section items", one["Edge swipes (system panels)"], list(EDGE_NAMES))
check("other fingers have no edge section", ["Edge swipes (system panels)" in dict(t[1]) for t in tg.gestureTree()[1:]], [False,False,False])
check("spoken names", [tg.GESTURE_LABELS[n.lower()] for n in ("edgeSwipeTopRight","edgeSwipeBottom","edgeSwipeLeft")],
      ["swipe down from the top right corner","swipe up from the bottom edge","swipe right from the left edge"])
d=tg.defaultBindings()
check("default command on all 8", sorted({d.get("tp:"+n.lower()) for n in EDGE_NAMES}), ["edgePanel"])
check("description", tg.scriptDescription("edgePanel"), "Goes to the system panel item at that edge; the same swipe again opens it")
check("total gestures in tree", sum(len(n) for _,s in tg.gestureTree() for _,n in s), 80)
print("bad:", bad)
