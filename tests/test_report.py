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
    # Updated 2026-09-10: "unreadable" is now the UNREADABLE sentinel rather
    # than None. This test used to pass None and assert "could not read", which
    # IS the conflation the sentinel exists to end — None means the API
    # answered and there are no runs. Both remain RED; they now say different
    # things, and the second assertion holds that half so this change cannot
    # quietly turn a workflow with no runs green.
    r = _row(run=lambda repo, wf: report.UNREADABLE)
    assert any("could not read" in x for x in r["red"])
    absent = _row(run=lambda repo, wf: None)
    assert absent["red"], "a night workflow with no runs at all is still red"


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
    monkeypatch.setattr(report, "row_for", lambda *args, **kw: healthy)
    monkeypatch.setattr(report, "gh_quota", lambda: None)       # no network in a unit test
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


# ---------------------------------------------------------------------------
# A FAILED READ IS NOT A VERDICT — the 2026-09-08/09 incident.
#
# For two mornings this report told six projects they were RED because the
# schedule had "NEVER fired". Every one of those crons had fired; anat's
# thirteen times. `gh` had no usable auth inside the workflow, every call
# failed, and a failed call was indistinguishable from an API that answered
# "no scheduled runs".
#
# The damage was not the wrong sentence — it is that a report reading RED for
# everything, every morning, for the same reason, cannot be read at all. Inside
# those two days of noise sat anat's staging refresh, dead for three weeks, and
# five projects' runners offline for nine hours with their uptime alerts among
# the jobs that never ran. Both would have been obvious against a green board.
# ---------------------------------------------------------------------------

def test_an_unreadable_schedule_does_not_become_a_claim_that_the_cron_never_fired():
    """The exact historical failure. Still RED — a morning nobody can see is not
    a morning that is fine — but it must accuse the instrument, not the cron.

    Mutation: return None instead of UNREADABLE from the fetch and this fails,
    which is the old behaviour verbatim.
    """
    r = _row(sched=lambda repo, wf: report.UNREADABLE)
    assert r["red"], "an unreadable schedule must still be red"
    assert any("could not read the schedule" in x for x in r["red"]), r["red"]
    assert not any("NEVER fired" in x or "never fired" in x for x in r["red"]), (
        "a failed read was reported as a fact about the schedule: " + "; ".join(r["red"]))


def test_a_genuinely_absent_schedule_is_still_named_as_such():
    """The claim the fix must NOT swallow. When the API really does answer with
    no scheduled runs, that is a fact about the project and has to keep being
    reported — otherwise this change trades a false alarm for a blind spot.

    Mutation: make the UNREADABLE branch catch None too — red here.
    """
    r = _row(sched=lambda repo, wf: None)
    assert any("scheduled-run evidence unavailable" in x for x in r["red"]), r["red"]
    assert not any("gh failed" in x for x in r["red"]), r["red"]


def test_the_table_says_question_mark_for_unreadable_and_never_for_absent():
    """The table is what a person actually reads at 06:30. The distinction has
    to survive into the column, not live only in the verdict sentence."""
    unreadable = report.row_for(P, MON, fetch_run=lambda r, w: _run(), fetch_tip=lambda r, b: "a" * 40,
                                fetch_health=lambda u: "a" * 12, fetch_compare=lambda r, b, h: "identical",
                                fetch_scheduled=lambda r, w: report.UNREADABLE)
    absent = report.row_for(P, MON, fetch_run=lambda r, w: _run(), fetch_tip=lambda r, b: "a" * 40,
                            fetch_health=lambda u: "a" * 12, fetch_compare=lambda r, b, h: "identical",
                            fetch_scheduled=lambda r, w: None)
    assert "| ? |" in report.render([unreadable]), report.render([unreadable])
    assert "| never |" in report.render([absent]), report.render([absent])


def test_an_unreadable_night_run_is_not_reported_as_having_no_runs():
    """Same shape on the other fetch: `gh` failing must not read as a project
    whose night workflow has never run."""
    r = _row(run=lambda repo, wf: report.UNREADABLE)
    assert any("could not read the night workflow" in x for x in r["red"]), r["red"]
    assert not any("no runs at all" in x for x in r["red"]), r["red"]


def test_unreadable_is_falsy_so_every_existing_guard_still_treats_it_as_nothing():
    """The sentinel is introduced into code full of `if not d` and `(run or {})`.
    If it were truthy, those would start treating a failed read as real data —
    a worse bug than the one being fixed."""
    assert not report.UNREADABLE
    assert (report.UNREADABLE or {}) == {}


def test_gh_json_returns_unreadable_when_the_command_fails(monkeypatch):
    """The origin of the sentinel: the failure has to be born at the boundary,
    or every caller has to remember to check — and one of them will not."""
    import subprocess as sp

    def boom(*a, **k):
        raise sp.CalledProcessError(1, "gh")

    monkeypatch.setattr(report.subprocess, "run", boom)
    assert report.gh_json("repos/o/r/actions/runs") is report.UNREADABLE


# --- the kit pin as a gate (0.1.40) --------------------------------------------

def _row_with_pin(pin, floor="0.1.40", **kw):
    fetch_pin = lambda repo, branch: pin  # noqa: E731
    fetch_run = kw.pop("run", lambda repo, wf: _run())
    return report.row_for(P, MON, fetch_run=fetch_run, fetch_tip=lambda r, b: "a" * 40,
                          fetch_health=lambda u: "a" * 12, fetch_compare=lambda repo, base, head: "identical",
                          fetch_scheduled=lambda repo, wf: _run(), fetch_pin=fetch_pin, floor=floor)


def test_a_kit_pinned_below_the_floor_is_red():
    """A register made by 0.1.36 answers a different question than one made by
    0.1.39 while looking identical (0.1.35 fixed a count that was always 0).
    Mutation: drop the `_vtuple(pin) < _vtuple(floor)` branch and this passes
    a lagging pin as green."""
    r = _row_with_pin("0.1.36")
    assert any("floor is 0.1.40" in x for x in r["red"]), r
    assert r["kit"] == "0.1.36"


def test_a_kit_at_or_above_the_floor_is_not_red_for_it():
    assert _row_with_pin("0.1.40")["red"] == []
    assert _row_with_pin("0.1.41")["red"] == []
    assert _row_with_pin("0.1.40")["kit"] == "0.1.40"


def test_version_order_is_numeric_not_lexical():
    """0.1.9 < 0.1.10, whatever a string compare thinks."""
    assert _row_with_pin("0.1.9", floor="0.1.10")["red"]
    assert _row_with_pin("0.1.10", floor="0.1.9")["red"] == []


def test_an_unreadable_pin_is_red_and_says_gh_not_the_project():
    r = _row_with_pin(report.UNREADABLE)
    assert any("kit pin" in x and "gh failed" in x for x in r["red"]), r
    assert r["kit"] == "?"


def test_a_manifest_with_no_pin_is_red_because_its_registers_have_no_author():
    r = _row_with_pin(None)
    assert any("no bench.version" in x for x in r["red"]), r
    assert r["kit"] == "none"


def test_without_a_floor_nothing_is_claimed_about_the_kit():
    r = _row()
    assert r["kit"] == "" and r["red"] == []


def test_the_table_carries_the_kit_column():
    text = report.render([_row_with_pin("0.1.36")])
    assert "| kit |" in text.splitlines()[0]
    assert "| 0.1.36 |" in text


def test_gh_reason_names_the_quota_not_a_generic_failure():
    """2026-09-14: six rows read 'gh failed here' with gh authenticated — the
    account's 5,000/h quota was spent and stderr said so; the report ate it."""
    import subprocess as sp
    err = "gh: API rate limit exceeded for user ID 1. If you reach out to GitHub Support…"
    assert "rate limit" in report.gh_reason(err, sp.CalledProcessError(1, "gh"))
    assert "not authenticated" in report.gh_reason("gh: To get started with GitHub CLI, please run: gh auth login\nauthentication required", sp.CalledProcessError(4, "gh"))
    assert "not installed" in report.gh_reason(None, FileNotFoundError("gh"))
    assert "timed out" in report.gh_reason(b"", sp.TimeoutExpired("gh", 60))
    assert "not JSON" in report.gh_reason("", __import__("json").JSONDecodeError("x", "", 0))


def test_a_failed_gh_read_records_its_reason_for_the_morning(monkeypatch):
    import subprocess as sp

    def boom(*a, **k):
        raise sp.CalledProcessError(1, "gh", stderr="gh: API rate limit exceeded for user ID 1.")

    monkeypatch.setattr(report.subprocess, "run", boom)
    report.GH_FAILURES.clear()
    assert report.gh_json("repos/o/r/actions/runs") is report.UNREADABLE
    assert report.GH_FAILURES and "rate limit" in report.GH_FAILURES[-1]["reason"]
    lines = report.gh_failure_lines(report.GH_FAILURES, {"reset": MON})
    assert lines[0].startswith("1 gh read(s) failed") and "resets 06:30 UTC" in lines[1], lines
    report.GH_FAILURES.clear()


def test_no_failures_means_no_tail():
    assert report.gh_failure_lines([], None) == []


def test_kit_pin_reads_bench_version_off_the_manifest_contents(monkeypatch):
    import base64
    body = base64.b64encode(b"project: x\nbench:\n  version: 0.1.36\n").decode()
    monkeypatch.setattr(report, "gh_json", lambda path: {"content": body})
    assert report.kit_pin("o/r", "main") == "0.1.36"
    monkeypatch.setattr(report, "gh_json", lambda path: report.UNREADABLE)
    assert report.kit_pin("o/r", "main") is report.UNREADABLE
    monkeypatch.setattr(report, "gh_json", lambda path: {"message": "Not Found"})
    assert report.kit_pin("o/r", "main") is None
    monkeypatch.setattr(report, "gh_json", lambda path: {"content": base64.b64encode(b"project: x\n").decode()})
    assert report.kit_pin("o/r", "main") is None
