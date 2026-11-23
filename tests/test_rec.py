import sys; sys.path.insert(0, "addon/globalPlugins/trackpadGestures")
from recognizer import Recognizer, allGestureNames

def run(script):
    out=[]; ex=[]
    r=Recognizer(out.append, lambda u,v,f: ex.append((round(u,2),round(v,2),f)))
    t=0.0
    for item in script:
        if item[0]=="wait":
            end=t+item[1]
            while t<end: t+=0.04; r.tick(t)
        else:
            frame,dt=item
            t+=dt; r.feed(frame, 0.6, t)
    for _ in range(30): t+=0.04; r.tick(t)
    return out, ex

def stroke(pts, fingers=1, dt=0.01, spread=0.15):
    seq=[]
    for (u,v) in pts:
        seq.append(({i:(u+i*spread*0.3, v) for i in range(fingers)}, dt))
    seq.append(({},dt))
    return seq

def line(a,b,steps=20):
    return [(a[0]+(b[0]-a[0])*k/steps, a[1]+(b[1]-a[1])*k/steps) for k in range(steps+1)]

tap=stroke([(0.5,0.5)]*5)
cases = {
 "swipeRight": stroke(line((0.2,0.5),(0.6,0.5))),
 "swipeLeft": stroke(line((0.6,0.5),(0.2,0.52))),
 "swipeDown": stroke(line((0.5,0.2),(0.5,0.7))),
 "swipeUp": stroke(line((0.5,0.7),(0.5,0.2))),
 "tap": tap,
 "doubleTap": tap+[("wait",0.1)]+tap,
 "tripleTap": tap+[("wait",0.1)]+tap+[("wait",0.1)]+tap,
 "longPress": tap+[("wait",0.1)]+stroke([(0.5,0.5)]*70),
 "swipeUpThenDown": stroke(line((0.5,0.7),(0.5,0.3))+line((0.5,0.3),(0.5,0.7))),
 "swipeUpThenLeft": stroke(line((0.6,0.7),(0.6,0.3))+line((0.6,0.3),(0.2,0.3))),
 "swipeDownThenLeft": stroke(line((0.6,0.3),(0.6,0.8))+line((0.6,0.8),(0.2,0.8))),
 "swipeRightThenDown": stroke(line((0.2,0.3),(0.6,0.3))+line((0.6,0.3),(0.6,0.8))),
 "2fingerTap": stroke([(0.4,0.5)]*5,2),
 "2fingerDoubleTap": stroke([(0.4,0.5)]*5,2)+[("wait",0.1)]+stroke([(0.4,0.5)]*5,2),
 "2fingerSwipeUp": stroke(line((0.4,0.8),(0.4,0.3)),2),
 "3fingerSwipeLeft": stroke(line((0.6,0.5),(0.2,0.5)),3),
 "3fingerTap": stroke([(0.3,0.5)]*5,3),
 "4fingerDoubleTap": stroke([(0.3,0.5)]*5,4)+[("wait",0.1)]+stroke([(0.3,0.5)]*5,4),
 "tap,swipeRight": tap+[("wait",0.1)]+stroke(line((0.2,0.5),(0.6,0.5))),
}
bad=0
for want,sc in cases.items():
    got,_=run(sc)
    ok = ",".join(got)==want
    bad+= not ok
    print("OK " if ok else "BAD", want, "->", got)
# explore: hold still then slide slowly
got,ex=run(stroke([(0.3,0.3)]*50+line((0.3,0.3),(0.8,0.8),100)))
print("explore gestures:",got,"explore calls:",len(ex), ex[0], ex[-1])
assert got==[] and ex and ex[0][2] is True
assert len(set(allGestureNames()))==len(allGestureNames())
print("names:",len(allGestureNames()), "bad:",bad)
def twoTap(u,v):
    return stroke([(u,v)]*5,2,spread=0.0)
for want,sc in {"2fingerDoubleTapTop":twoTap(0.5,0.1)+[("wait",0.1)]+twoTap(0.5,0.1),
                "2fingerDoubleTapBottom":twoTap(0.5,0.9)+[("wait",0.1)]+twoTap(0.5,0.9),
                "2fingerDoubleTapLeft":twoTap(0.1,0.5)+[("wait",0.1)]+twoTap(0.1,0.5),
                "2fingerDoubleTapRight":twoTap(0.9,0.5)+[("wait",0.1)]+twoTap(0.9,0.5),
                "2fingerTripleTap":twoTap(0.5,0.5)+[("wait",0.1)]+twoTap(0.5,0.5)+[("wait",0.1)]+twoTap(0.5,0.5)}.items():
    got,_=run(sc); print("OK " if got==[want] else "BAD", want, got)
for n in (2,3):
    got,_=run(stroke([(0.5,0.5)]*70,n)); print("OK " if got==["%dfingerLongPress"%n] else "BAD", n, "finger long press", got)
got,_=run(stroke([(0.5,0.5)]*8,2)); print("OK " if got==["2fingerTap"] else "BAD", "quick 2 finger tap still a tap", got)
def oneTap(u,v): return stroke([(u,v)]*5)
for want,sc in {"doubleTapLeft": oneTap(0.1,0.5)+[("wait",0.1)]+oneTap(0.1,0.5),
                "3fingerDoubleTapBottom": stroke([(0.3,0.9)]*5,3,spread=0.1)+[("wait",0.1)]+stroke([(0.3,0.9)]*5,3,spread=0.1),
                "2fingerLongPressTop": stroke([(0.5,0.1)]*70,2,spread=0.0)}.items():
    got,_=run(sc); print("OK " if got==[want] else "BAD", want, got)
from recognizer import baseName, zoneOf
assert baseName("2fingerDoubleTapTop")=="2fingerDoubleTap" and baseName("swipeUpThenLeft")=="swipeUpThenLeft" and baseName("doubleTapRight")=="doubleTap"
assert zoneOf("3fingerLongPressLeft")=="Left" and zoneOf("swipeDownThenLeft")==""
print("names:", len(allGestureNames()))
