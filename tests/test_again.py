exec(open("tests/test_plugin.py").read().split("for fl, secs")[0])
sys.modules["inputCore"].normalizeGestureIdentifier=lambda s: s.lower()
class _NIA(Exception): pass
sys.modules["inputCore"].NoInputGestureAction=_NIA
class _M:
    @staticmethod
    def executeGesture(g): pass
sys.modules["inputCore"].manager=_M
g=tg.GlobalPlugin.__new__(tg.GlobalPlugin)
g._edgeState={"name":"edgeSwipeBottom"}
g._onGesture("edgeSwipeBottom","middle"); print("same swipe keeps state:", g._edgeState is not None)
g._onGesture("swipeRight"); print("other gesture cancels:", g._edgeState is None)
g._edgeState={"name":"edgeSwipeBottom"}; g._onGesture("edgeSwipeBottomRight","end"); print("different edge cancels:", g._edgeState is None)
