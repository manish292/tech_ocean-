import sys; sys.path.insert(0, "addon/globalPlugins/trackpadGestures")
from recognizer import Recognizer
from edges import EdgeDetector, classify, EDGE_NAMES, edgeOfName

def run(points, dur=0.3, fingers=1, aspect=0.6, wait_after=0.6):
    out=[]; edges=[]
    r=Recognizer(out.append, None, lambda: True)
    d=EdgeDetector(r, lambda n,p: edges.append((n,p)))
    t=0.0; steps=len(points)
    for (u,v) in points:
        t+=dur/steps
        d.feed({i:(u+i*0.05,v) for i in range(fingers)}, aspect, t)
    t+=0.01; d.feed({}, aspect, t)
    end=t+wait_after
    while t<end: t+=0.04; d.tick(t)
    return out, edges

def line(a,b,n=15): return [(a[0]+(b[0]-a[0])*k/n, a[1]+(b[1]-a[1])*k/n) for k in range(n+1)]
bad=0
def check(label, got, want):
    global bad
    ok = got==want; bad += not ok
    print("OK " if ok else "BAD", label, got)

# The eight edges, each with its part
check("top right corner", run(line((0.85,0.03),(0.85,0.25)))[1], [("edgeSwipeTopRight","end")])
check("top middle", run(line((0.5,0.03),(0.5,0.25)))[1], [("edgeSwipeTop","middle")])
check("top left corner", run(line((0.1,0.05),(0.1,0.30)))[1], [("edgeSwipeTopLeft","start")])
check("bottom left", run(line((0.2,0.97),(0.2,0.75)))[1], [("edgeSwipeBottomLeft","start")])
check("bottom middle", run(line((0.5,0.95),(0.5,0.7)))[1], [("edgeSwipeBottom","middle")])
check("bottom right", run(line((0.8,0.95),(0.8,0.7)))[1], [("edgeSwipeBottomRight","end")])
check("left edge, upper part", run(line((0.03,0.2),(0.2,0.2)))[1], [("edgeSwipeLeft","start")])
check("right edge, middle", run(line((0.97,0.5),(0.8,0.5)))[1], [("edgeSwipeRight","middle")])
# Normal recognizer must not also report anything
check("no swipeDown alongside the edge swipe", run(line((0.5,0.03),(0.5,0.25)))[0], [])
# Limits
check("too short (3%) -> tap stays a tap", run([(0.5,0.03)]*5, dur=0.15), ([ "tap"], []))
check("too long (50%) -> normal swipeDown", run(line((0.5,0.03),(0.5,0.6))), (["swipeDown"], []))
check("too slow (0.9 s) -> not an edge swipe", run(line((0.5,0.03),(0.5,0.25)), dur=0.9)[1], [])
check("start outside the 10% band (12%) -> not an edge", run(line((0.5,0.12),(0.5,0.32)))[1], [])
check("outward (up from the top) -> not an edge", run(line((0.5,0.08),(0.5,0.01)))[1], [])
check("more sideways than inward -> not an edge", run(line((0.4,0.03),(0.7,0.15)))[1], [])
check("two fingers -> not an edge", run(line((0.5,0.03),(0.5,0.25)), fingers=2)[1], [])
# boundary values via classify (aspect 0.6)
check("exactly 5% inward counts", classify((0.5,0.02),(0.5,0.07),0.3,0.6), ("edgeSwipeTop","middle"))
check("exactly 40% inward counts", classify((0.5,0.02),(0.5,0.42),0.3,0.6), ("edgeSwipeTop","middle"))
check("41% does not", classify((0.5,0.02),(0.5,0.43),0.3,0.6), None)
check("corner start goes to the edge it moves away from", classify((0.04,0.04),(0.25,0.06),0.3,0.6), ("edgeSwipeLeft","start"))
check("names", [edgeOfName(n) for n in ("edgeSwipeTopRight","edgeSwipeBottom","edgeSwipeLeft")], [("top","end"),("bottom","middle"),("left",None)])
print("bad:", bad, "names:", len(EDGE_NAMES))
