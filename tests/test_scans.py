"""`qabench scans` — the scanners' contract, offline.

  1. a binary whose sha256 is not the pinned one is REFUSED, never run;
  2. only exact pins are audited, and the rest are COUNTED (a file of git URLs
     must not read as clean);
  3. exit: a scanner that did not run is 3; findings are 1, or 0 with --advisory;
     clean is 0.
The scanners themselves were run on all six projects when this was written
(2026-09-19): gitleaks clean on ana-log; pip-audit 0/10/11/19/28/47 findings on
ana-log/anat/tharros/iga/eliad/my8200 — the advisory backlog.
"""
from __future__ import annotations

import io

import pytest

from qabench import scans


def test_a_binary_that_is_not_the_pinned_one_is_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(scans, "CACHE", tmp_path)
    monkeypatch.setattr(scans.platform, "system", lambda: "Linux")
    monkeypatch.setattr(scans.platform, "machine", lambda: "aarch64")

    class R(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(scans.urllib.request, "urlopen", lambda url, timeout=0: R(b"not squawk"))
    with pytest.raises(RuntimeError, match="refusing to run it"):
        scans.fetch("squawk")
    assert not list(tmp_path.iterdir())


def test_only_exact_pins_are_audited_and_the_rest_are_counted():
    text = "a==1.0\n# comment\nb>=2\nqabench @ git+https://x/y@abc\n-r other.txt\nc==3 # pinned\n\n"
    pinned, other = scans.exact_pins(text)
    assert pinned == ["a==1.0", "c==3"] and other == 3


@pytest.mark.parametrize(("results", "argv", "code"), [
    ({"gitleaks": {"ran": True, "findings": []}}, [], 0),
    ({"gitleaks": {"ran": True, "findings": ["x"]}}, [], 1),
    ({"gitleaks": {"ran": True, "findings": ["x"]}}, ["--advisory"], 0),
    ({"gitleaks": {"ran": False, "why": "no network"}}, ["--advisory"], 3),
])
def test_the_exit_contract(monkeypatch, tmp_path, results, argv, code):
    monkeypatch.setattr(scans, "run_gitleaks", lambda root: results["gitleaks"])
    monkeypatch.setattr(scans, "run_pip_audit", lambda root, files: {"ran": True, "findings": []})
    assert scans.run(["--repo", str(tmp_path), *argv]) == code


def test_a_diff_that_cannot_run_is_did_not_run_not_clean(tmp_path):
    """A shallow checkout has no origin/main~20; the first version read the failed
    diff's empty output as «no migration changed» — clean, having checked nothing."""
    import subprocess
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    r = scans.run_squawk(tmp_path, "migrations/*.sql", "origin/main~20")
    assert r["ran"] is False and "cannot diff" in r["why"]
