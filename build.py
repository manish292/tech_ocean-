"""Builds the add-on package: python build.py

Writes trackpadGestures-<version>.nvda-addon next to this file, using the version in addon/manifest.ini.
An .nvda-addon file is a zip of the addon folder, with manifest.ini at the top."""
import os
import re
import zipfile

root = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(root, "addon")
with open(os.path.join(src, "manifest.ini"), encoding="utf-8") as f:
	version = re.search(r"^version\s*=\s*(\S+)", f.read(), re.M).group(1)
out = os.path.join(root, "trackpadGestures-%s.nvda-addon" % version)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
	for folder, dirs, files in os.walk(src):
		dirs[:] = [d for d in dirs if d != "__pycache__"]
		for name in files:
			if name.endswith((".pyc", ".pyo")):
				continue
			path = os.path.join(folder, name)
			z.write(path, os.path.relpath(path, src))
print("Built", os.path.basename(out))
