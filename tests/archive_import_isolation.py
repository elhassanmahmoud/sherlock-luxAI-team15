"""Check archived unittest import contracts independently of pytest collection."""
import inspect
from pathlib import Path
import subprocess
import sys


_PROBE_ATTRIBUTE = "_sherlock_archive_import_probe"


def assert_isolated_imports(case, prefixes=("torch",)):
    """Rerun this real test in a clean interpreter, retaining its import check.

    The child runs the original setUp/test/tearDown and checks every forbidden
    prefix there. Other tests' imports in the parent cannot affect the result.
    """
    if getattr(sys, _PROBE_ATTRIBUTE, False):
        forbidden = sorted(name for name in sys.modules
                           if any(name == prefix or name.startswith(prefix + ".")
                                  for prefix in prefixes))
        case.assertEqual(forbidden, [], "Forbidden imports in isolated archived test")
        return

    root = Path(__file__).resolve().parents[1]
    source = Path(inspect.getfile(type(case))).resolve()
    probe = """
import runpy
import sys
import unittest

root, source, class_name, method = sys.argv[1:]
sys.path[:0] = [str(__import__('pathlib').Path(source).parent), root]
sys._sherlock_archive_import_probe = True
namespace = runpy.run_path(source)
suite = unittest.TestSuite([namespace[class_name](method)])
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", probe, str(root), str(source),
         type(case).__name__, case._testMethodName],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    case.assertEqual(result.returncode, 0,
                     "Isolated archived test failed:\n" + result.stdout + result.stderr)
