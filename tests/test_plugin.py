import sys, types, builtins
builtins._ = lambda s: s
class Any(types.ModuleType):
    def __getattr__(self, n):
        if n.startswith("__"): raise AttributeError(n)
        return type(n, (object,), {"__init__": lambda self,*a,**k: None, "__getattr__": lambda self,n: (lambda *a,**k: None)})
for m in ["addonHandler","api","browseMode","core","globalPluginHandler","globalVars","inputCore","keyboardHandler","queueHandler","speech","tones","ui","wx","gui","gui.settingsDialogs","logHandler","NVDAObjects","scriptHandler"]:
    sys.modules[m]=Any(m)
def _script(description=None, gesture=None, gestures=None, **k):
    def deco(f):
        g=list(gestures or [])
        if gesture: g.append(gesture)
        f.gestures=g; f.__doc__=description; return f
    return deco
sys.modules["scriptHandler"].script=_script
import enum
cT=types.ModuleType("controlTypes")
cT.Role=enum.Enum("Role","LISTITEM LIST TREEVIEWITEM TREEVIEW MENUITEM CHECKMENUITEM RADIOMENUITEM MENU POPUPMENU RADIOBUTTON DATAITEM TAB TABLECELL ROWHEADER COLUMNHEADER MENUBAR DOCUMENT RICHEDIT")
cT.State=enum.Enum("State","EDITABLE MULTILINE")
sys.modules["controlTypes"]=cT
class Conf(dict): pass
cfg=types.ModuleType("config"); cfg.conf=Conf(); cfg.conf.spec={}
sys.modules["config"]=cfg
sys.path.insert(0,"addon/globalPlugins")
import trackpadGestures as tg
spec=cfg.conf.spec["trackpadGestures"]
print(spec["readingControlOrder"][:80]); print(spec["readingControlsOff"])
def setconf(order,off): cfg.conf["trackpadGestures"]={"readingControlOrder":order,"readingControlsOff":off}
setconf([c[0] for c in tg.READING_CONTROLS],[c[0] for c in tg.READING_CONTROLS if not c[2]])
print("enabled:",tg.enabledControls())
setconf(["panes","items","lines"],["characters"])  # user order, a removed one, and newer ones missing
print("custom:",tg.enabledControls()[:6])
print(tg.GESTURE_LABELS["2fingerdoubletaptop"], "|", tg.GESTURE_LABELS["swipelefthenright"] if "swipelefthenright" in tg.GESTURE_LABELS else tg.GESTURE_LABELS["swipeleftthenright"])
# every gesture bound in scripts must be a real gesture name
import re
src=open("addon/globalPlugins/trackpadGestures/__init__.py").read()
bound=re.findall(r'"tp:(\w+)"',src)
missing=[b for b in bound if b.lower() not in tg.GESTURE_LABELS]
dups=[b for b in set(bound) if bound.count(b)>1]
print("bound:",len(bound),"unknown:",missing,"duplicates:",dups)

sys.modules["inputCore"].normalizeGestureIdentifier=lambda s: s.lower()
for fl, secs in tg.gestureTree():
    print(fl, [(k, len(n)) for k,n in secs])
print([tg._humanize(n) for n in ("longPress","doubleTapTop","3fingerLongPressLeft","2fingerDoubleTap","swipeUpThenLeft")])
missing=[sn for _,names in tg.COMMAND_GROUPS for sn in names if not hasattr(tg.GlobalPlugin,"script_"+sn)]
unlisted=[a[7:] for a in dir(tg.GlobalPlugin) if a.startswith("script_") and a[7:] not in {sn for _,n in tg.COMMAND_GROUPS for sn in n}]
print("missing:",missing,"not in list:",unlisted)
d=tg.defaultBindings(); print("defaults:",len(d), d.get("tp:2fingerlongpress"), d.get("tp:2fingerdoubletaptop"))
total=sum(len(n) for _,s in tg.gestureTree() for _,n in s); print("in tree:",total)
