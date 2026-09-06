"""`qabench report` — the morning's one row per project. It must go RED when a
night did not run on a morning after a scheduled one, when the night was red,
when production does not answer with the commit the night swept, or when it
cannot read — and stay green on an off-day morning and on a healthy estate.
Every fetch is faked here; the live command reads gh and /health.
"""
from datetime import datetime, timedelta, timezone

from qabench import report

MON = datetime(2026, 9, 7, 6, 30, tzinfo=timezone.utc)      # a Monday morning: Sunday night was scheduled for 0-4
SAT = datetime(2026, 9, 5, 6, 30, tzinfo=timezone.utc)      # a Saturday morning: Friday night is off for 0-4 and 1-5? (Friday = 5)

P = {"name": "x", "repo": "o/r", "night_workflow": "qa-nightly.yml", "main": "main",
     "production": "https://p/health", "staging": "https://s/health", "cron_days": "0-4", "window_h": 30}


def _run(sha="a" * 40, conclusion="success", hours_ago=3.0, now=MON):
    return {"head_sha": sha, "status": "completed", "conclusion": conclusion,
            "created_at": (now - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")}


def _row(**kw):
    fetch_run = kw.pop("run", lambda repo, wf: _run())
    tip = kw.pop("tip", "a" * 40)
    health = kw.pop("health", {"https://p/health": "a" * 12, "https://s/health": "a" * 12})
    now = kw.pop("now", MON)
    rel = kw.pop("rel", "diverged")
    return report.row_for(P, now, fetch_run=fetch_run, fetch_tip=lambda r, b: tip, fetch_health=lambda u: health.get(u),
                          fetch_compare=lambda repo, base, head: rel)


def test_a_healthy_estate_is_green():
    r = _row()
    assert r["red"] == [] and r["night"] == "success" and r["production"] == "aaaaaaaa"


def test_a_night_that_did_not_fire_on_a_scheduled_morning_is_red():
    r = _row(run=lambda repo, wf: _run(hours_ago=50))
    assert any("schedule did not fire" in x for x in r["red"]), r


def test_the_same_gap_on_an_off_day_morning_is_not_red():
    # Saturday morning: Friday (5) is not in 0-4, so no night was due
    r = _row(run=lambda repo, wf: _run(hours_ago=50, now=SAT), now=SAT)
    assert r["red"] == [], r


def test_a_red_night_is_red():
    r = _row(run=lambda repo, wf: _run(conclusion="failure"))
    assert any("was failure" in x for x in r["red"])


def test_production_serving_a_build_off_the_swept_line_is_red():
    r = _row(health={"https://p/health": "b" * 12, "https://s/health": "a" * 12}, rel="diverged")
    assert any("not on the line" in x for x in r["red"]), r


def test_production_older_than_the_last_green_night_means_the_promote_did_not_happen():
    r = _row(health={"https://p/health": "b" * 12, "https://s/health": "a" * 12}, rel="behind")
    assert any("OLDER" in x for x in r["red"]), r


def test_production_promoted_by_hand_after_the_night_is_a_note_not_red():
    r = _row(health={"https://p/health": "b" * 12, "https://s/health": "a" * 12}, rel="ahead")
    assert r["red"] == [] and any("promoted by hand" in n for n in r["notes"]), r


def test_an_environment_that_cannot_name_its_build_is_red_not_unknown():
    r = _row(health={"https://s/health": "a" * 12})
    assert any("production does not name its commit" in x for x in r["red"])


def test_an_unreadable_workflow_is_red_on_a_scheduled_morning():
    r = _row(run=lambda repo, wf: None)
    assert any("could not read" in x for x in r["red"])


def test_staging_behind_main_is_a_note_not_a_verdict():
    r = _row(tip="c" * 40, health={"https://p/health": "a" * 12, "https://s/health": "a" * 12})
    assert r["red"] == [] and any("staging serves" in n for n in r["notes"])


def test_the_table_carries_every_row_and_the_verdict():
    rows = [_row(), _row(run=lambda repo, wf: _run(conclusion="failure"))]
    text = report.render(rows)
    assert text.count("\n") == 3 and "RED — last night was failure" in text and "| ok" in text
