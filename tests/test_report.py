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
    sched = kw.pop("sched", lambda repo, wf: _run())          # by default the cron fired tonight
    return report.row_for(P, now, fetch_run=fetch_run, fetch_tip=lambda r, b: tip, fetch_health=lambda u: health.get(u),
                          fetch_compare=lambda repo, base, head: rel, fetch_scheduled=sched)


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


def test_a_hand_dispatched_night_does_not_prove_the_schedule():
    """2026-09-07: three projects had never had a scheduled night; every morning read green off `make night`."""
    r = _row(sched=lambda repo, wf: None)
    assert any("scheduled-run evidence unavailable" in x for x in r["red"]), r


def test_a_schedule_that_stopped_firing_is_red_even_with_a_fresh_hand_run():
    r = _row(sched=lambda repo, wf: _run(hours_ago=60))
    assert any("last fired 60.0h ago" in x for x in r["red"]), r


def test_the_schedule_is_not_judged_on_an_off_day():
    r = _row(run=lambda repo, wf: _run(now=SAT), now=SAT, sched=lambda repo, wf: None)
    assert r["red"] == [], r


def test_literal_unknown_health_is_not_a_build():
    r = _row(health={"https://p/health": "unknown", "https://s/health": "unknown"})
    assert r["production"] == r["staging"] == ""
    assert len(r["red"]) == 2


def test_a_stuck_queue_is_red_before_the_next_morning():
    run = _run(hours_ago=1)
    run.update(status="queued", conclusion=None)
    r = _row(run=lambda *args: run)
    assert any("still queued" in item for item in r["red"])


def test_a_fresh_running_night_is_not_reported_as_stuck():
    run = _run(hours_ago=0.1)
    run.update(status="in_progress", conclusion=None)
    r = _row(run=lambda *args: run)
    assert r["red"] == []
    assert any("still in_progress" in item for item in r["notes"])


def test_staging_is_compared_with_its_own_branch():
    p = P | {"staging_branch": "staging"}
    r = report.row_for(p, MON, fetch_run=lambda *args: _run(),
        fetch_scheduled=lambda *args: _run(),
        fetch_tip=lambda repo, branch: ("b" if branch == "staging" else "a") * 40,
        fetch_health=lambda url: ("b" if url == p["staging"] else "a") * 12,
        fetch_compare=lambda *args: "identical")
    assert r["red"] == [] and r["notes"] == []
    assert r["integration_tip"] == "bbbbbbbb"


def test_a_retry_does_not_inherit_the_original_executions_age():
    run = _run(hours_ago=10)
    run.update(status="in_progress", conclusion=None, run_attempt=2,
               run_started_at=(MON - timedelta(minutes=5)).isoformat())
    r = _row(run=lambda *args: run)
    assert r["red"] == []
    assert any("0.1h running" in item for item in r["notes"])


def test_all_green_json_output_is_parseable(monkeypatch, tmp_path, capsys):
    import json
    estate = tmp_path / "estate.yml"
    estate.write_text("projects: [{name: x}]\n")
    healthy = _row()
    monkeypatch.setattr(report, "row_for", lambda *args: healthy)
    assert report.run(["--json", "--estate", str(estate)]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)[0]["name"] == "x"
    assert "all 1 projects ok" in output.err


def test_a_queued_retry_uses_its_own_age():
    run = _run(hours_ago=10)
    run.update(status="queued", conclusion=None, run_attempt=2,
               run_started_at=(MON - timedelta(minutes=5)).isoformat())
    result = _row(run=lambda *args: run)
    assert result["red"] == []
    assert any("0.1h queued" in item for item in result["notes"])


def test_a_queued_retry_without_current_timestamp_is_unknown():
    run = _run(hours_ago=10)
    run.update(status="queued", conclusion=None, run_attempt=2)
    result = _row(run=lambda *args: run)
    assert any("retry age unavailable" in item for item in result["red"])
    assert not any("10.0h queued" in item for item in result["red"])


def test_an_old_run_retried_today_does_not_report_a_stale_attempt():
    for status in ("queued", "in_progress", "completed"):
        run = _run(hours_ago=70)
        run.update(status=status, conclusion="success" if status == "completed" else None,
                   run_attempt=2, run_started_at=(MON - timedelta(minutes=5)).isoformat())
        result = _row(run=lambda *args: run)
        assert result["red"] == []
        assert result["night_age_h"] == 0.1
