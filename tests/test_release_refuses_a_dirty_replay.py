"""scripts/release.py refuses a release while the mutation replay has a stale or surviving record."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _release():
    spec = importlib.util.spec_from_file_location("release", ROOT / "scripts" / "release.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_dirty_replay_refuses_before_anything_is_bumped(monkeypatch, capsys):
    rel = _release()
    monkeypatch.setattr(rel, "sh", lambda *a: "" if a[:2] == ("git", "status") else "v0.0.1")
    monkeypatch.setattr(rel, "replay_clean", lambda: False)
    touched = []
    monkeypatch.setattr(Path, "write_text", lambda self, *a, **k: touched.append(self))
    assert rel.main(["9.9.9", "t"]) == 1
    assert touched == [], "the version was bumped although the replay was dirty"
    assert "mutate --replay is not clean" in capsys.readouterr().err


def test_replay_clean_is_the_replay_exit_code(monkeypatch):
    rel = _release()
    seen = {}

    class R:
        returncode = 1

    def fake_run(args, **kw):
        seen["args"] = args
        return R()

    monkeypatch.setattr(rel.subprocess, "run", fake_run)
    assert rel.replay_clean() is False
    assert seen["args"][-3:] == ["mutate", "--replay", "qa/mutations.json"]
    R.returncode = 0
    assert rel.replay_clean() is True
