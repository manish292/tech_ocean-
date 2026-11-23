"""Runs every test from the repository root: python tests/run_tests.py

The tests need no NVDA and no Windows: the gesture recognizer and edge detector are plain Python,
and the plugin tests use small stand-ins for NVDA's modules. A line starting with BAD is a failure."""
import os
import subprocess
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
failed = False
for name in ("test_rec", "test_edges", "test_plugin", "test_panels", "test_again"):
	result = subprocess.run([sys.executable, os.path.join("tests", name + ".py")], cwd=root,
		capture_output=True, text=True)
	output = result.stdout + result.stderr
	bad = [line for line in output.splitlines() if line.startswith("BAD") or "Traceback" in line]
	passed = sum(1 for line in output.splitlines() if line.startswith("OK"))
	if result.returncode or bad:
		failed = True
		print("FAILED %s" % name)
		print(output)
	else:
		print("passed %s (%d checks)" % (name, passed))
sys.exit(1 if failed else 0)
