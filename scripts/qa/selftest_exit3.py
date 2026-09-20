"""Known-positive and near-miss for the exit-3 detector, both REAL.

    --fires   a command the dispatch has and no test asserts a 3 for; the
              detector must name it.  `show` is the real one: it prints the
              resolved config and has no test at all.
    --silent  `population`, whose test asserts `== 3` in four places. The
              detector must NOT name it. Real, out of the tree, and it is the
              case a looser detector (any test file mentioning the module)
              would get wrong, because tests/test_population.py also imports
              modules it does not test.
"""
import subprocess, sys

found = set(subprocess.run([sys.executable, "scripts/qa/subj_exit3.py"],
                           capture_output=True, text=True, check=True).stdout.split())
if "--fires" in sys.argv:
    sys.exit(0 if "show" not in found else 1)      # must be absent from the swept set
if "--silent" in sys.argv:
    sys.exit(0 if "population" in found else 1)    # must be present
sys.exit(2)
