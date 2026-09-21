"""`qabench.conformance` — one judge for six manifests, and the kit pin.

The template test six repos copied checked HONESTY (paths exist, ● has evidence)
and never MEANING. These tests hold the judge to the contract: a lie is fatal, a
claim without ran-proof is advisory and visible, and the pin is compared with
the kit that is actually installed — no checkout, no network.
"""
from __future__ import annotations

import subprocess

import pytest
import yaml

from qabench import conformance


def _manifest(**over):
    c = conformance.contract()
    checks = {}
    for cid, rule in c["checks"].items():
        checks[cid] = {"name": rule["name"], "status": "implemented",
                       "evidence": [f"tests/{cid.lower()}.py"], "ran": f"job {cid.lower()}"}
    m = {"project": "fake", "checks": checks}
    for cid, spec in over.items():
        checks[cid] = spec
    return m


def test_a_manifest_that_meets_the_contract_has_no_findings():
    assert conformance.judge(_manifest()) == []


def test_every_check_must_be_present_and_nothing_beyond_the_twelve():
    m = _manifest()
    del m["checks"]["C7"]
    m["checks"]["C13"] = {"name": "x", "status": "absent", "reason": "y"}
    kinds = {(f["check"], f["kind"]) for f in conformance.judge(m)}
    assert ("C7", "missing") in kinds and ("*", "missing") in kinds
    assert all(f["fatal"] for f in conformance.judge(m))


def test_implemented_without_evidence_is_a_lie_and_fatal():
    f = conformance.judge(_manifest(C4={"name": "input rejection sweep", "status": "implemented", "evidence": [], "ran": "x"}))
    assert [x["kind"] for x in f] == ["no_evidence"] and f[0]["fatal"]


def test_implemented_without_ran_proof_is_claimed_not_shown_and_advisory():
    """The contract's rule (c): a ● must name what proves it RAN. Advisory now,
    so six repos can turn it on one at a time. Mutation: drop the `ran` clause
    in judge() and this finds nothing."""
    f = conformance.judge(_manifest(C9={"name": "outbound as recipient", "status": "implemented", "evidence": ["t.py"]}))
    assert len(f) == 1 and f[0]["kind"] == "unproven" and not f[0]["fatal"]
    assert "subject" not in f[0]["text"] and "catalogue size" in f[0]["text"]  # names the contract's ran_proof


def test_partial_must_name_its_gap_with_the_contracts_own_words():
    base = {"name": "journey per surface", "status": "partial", "evidence": ["t.py"], "reason": "no second tenant"}
    f = conformance.judge(_manifest(C10=dict(base)))
    assert [x["kind"] for x in f] == ["partial_unnamed"] and not f[0]["fatal"]
    f = conformance.judge(_manifest(C10=dict(base, missing=["a_word_the_contract_does_not_know"])))
    assert [x["kind"] for x in f] == ["partial_unnamed"]
    assert conformance.judge(_manifest(C10=dict(base, missing=["second_tenant", "stored_row"]))) == []


def test_partial_or_absent_without_a_reason_is_fatal():
    f = conformance.judge(_manifest(C5={"name": "real-artifact corpus", "status": "absent", "evidence": []}))
    assert [x["kind"] for x in f] == ["no_reason"] and f[0]["fatal"]


def test_a_wrong_name_or_status_is_fatal():
    f = conformance.judge(_manifest(C1={"name": "truth", "status": "implemented", "evidence": ["t"], "ran": "x"}))
    assert [x["kind"] for x in f] == ["name"]
    f = conformance.judge(_manifest(C1={"name": "truth register", "status": "done", "evidence": ["t"]}))
    assert [x["kind"] for x in f] == ["status"]


def test_evidence_paths_are_checked_when_a_root_is_given(tmp_path):
    (tmp_path / "tests").mkdir()
    m = _manifest()
    for cid in m["checks"]:
        (tmp_path / "tests" / f"{cid.lower()}.py").write_text("")
    assert conformance.judge(m, root=tmp_path) == []
    (tmp_path / "tests" / "c3.py").unlink()
    f = conformance.judge(m, root=tmp_path)
    assert [x["kind"] for x in f] == ["evidence_missing"] and f[0]["fatal"]


def test_the_matrix_shows_claimed_not_shown_and_unnamed_partials():
    m = _manifest(C9={"name": "outbound as recipient", "status": "implemented", "evidence": ["t.py"]},
                  C10={"name": "journey per surface", "status": "partial", "evidence": ["t.py"], "reason": "r"},
                  C5={"name": "real-artifact corpus", "status": "partial", "evidence": ["t.py"], "reason": "r", "missing": ["stage"]})
    text = conformance.matrix(m, conformance.judge(m))
    lines = {l.split()[1]: l.split()[0] for l in text.splitlines() if l.strip().startswith(("●", "◐", "○"))}
    assert lines["C9"] == "●?" and lines["C10"] == "◐?" and lines["C5"] == "◐" and lines["C1"] == "●"
    assert "missing: stage" in text and "●? 1 claimed without ran-proof" in text and "◐? 1 partial" in text


def test_fatal_filters_to_the_lies():
    m = _manifest(C9={"name": "outbound as recipient", "status": "implemented", "evidence": ["t.py"]},
                  C4={"name": "input rejection sweep", "status": "implemented", "evidence": [], "ran": "x"})
    f = conformance.judge(m)
    assert {x["kind"] for x in f} == {"unproven", "no_evidence"}
    assert [x["kind"] for x in conformance.fatal(f)] == ["no_evidence"]


# --- the pin ------------------------------------------------------------------

COMMIT = "c" * 40


def _repo(tmp_path, *, manifest_version="0.1.40", refs=(COMMIT,)):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "qa").mkdir()
    (tmp_path / "qa" / "manifest.yml").write_text(yaml.safe_dump({"project": "x", "bench": {"version": manifest_version}}))
    (tmp_path / "requirements-dev.txt").write_text("".join(f"qabench @ git+https://x/qa-bench@{r}\n" for r in refs))
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_one_kit_one_commit_and_the_manifest_names_it_is_clean(tmp_path):
    assert conformance.pin_agrees(_repo(tmp_path), installed=("0.1.40", COMMIT)) == []


def test_the_manifest_disagreeing_with_the_installed_kit_is_named(tmp_path):
    """The 2026-09-12 shape: five repos repinned to 0.1.21, manifests left at
    0.1.17, every night red before a page was swept. Mutation: compare `pinned`
    with itself and this passes."""
    out = conformance.pin_agrees(_repo(tmp_path, manifest_version="0.1.36"), installed=("0.1.40", COMMIT))
    assert len(out) == 1 and "0.1.36" in out[0] and "0.1.40" in out[0]


def test_a_pinned_commit_that_is_not_the_installed_one_is_named(tmp_path):
    """No checkout needed: the installed dist knows its own commit. IGA's copy
    resolved the pin through a local checkout 30 commits behind and SKIPPED
    for a week."""
    out = conformance.pin_agrees(_repo(tmp_path, refs=("d" * 40,)), installed=("0.1.40", COMMIT))
    assert len(out) == 1 and "dddddddd" in out[0] and "cccccccc" in out[0]


def test_two_refs_or_a_movable_ref_are_named(tmp_path):
    out = conformance.pin_agrees(_repo(tmp_path, refs=(COMMIT, "v0.1.40")), installed=("0.1.40", COMMIT))
    assert any("more than one" in x for x in out) and any("not a full commit" in x for x in out)


def test_no_ref_at_all_reads_as_did_not_run_not_as_agreement(tmp_path):
    r = _repo(tmp_path, refs=())
    (r / "requirements-dev.txt").write_text("pytest\n")
    subprocess.run(["git", "add", "-A"], cwd=r, check=True)
    out = conformance.pin_agrees(r, installed=("0.1.40", COMMIT))
    assert len(out) == 1 and "DID NOT RUN" in out[0]


def test_no_manifest_pin_or_no_installed_kit_are_each_named(tmp_path):
    r = _repo(tmp_path)
    (r / "qa" / "manifest.yml").write_text("project: x\n")
    assert any("no bench.version" in x for x in conformance.pin_agrees(r, installed=("0.1.40", COMMIT)))
    (tmp_path / "b").mkdir()
    r2 = _repo(tmp_path / "b")
    assert any("not installed" in x for x in conformance.pin_agrees(r2, installed=(None, None)))


def test_the_installed_kit_can_name_itself():
    version, commit = conformance.installed_kit()
    assert version is None or isinstance(version, str)
    assert commit is None or len(commit) == 40


def test_an_install_with_no_ref_at_all_is_named_even_though_it_has_no_pin(tmp_path):
    """anat's shared-bench.yml: `pip install --upgrade "qabench @ git+https://…/qa-bench"`
    on the runner holding staging's secrets. `pin_refs` needs the `@`, so every
    pin guard was green. Mutation: drop the `unpinned_installs` loop and this
    repo reads clean."""
    r = _repo(tmp_path)
    (r / "bench.yml").write_text('      - run: pip install --upgrade "qabench @ git+https://github.com/x/qa-bench"\n')
    subprocess.run(["git", "add", "-A"], cwd=r, check=True)
    out = conformance.pin_agrees(r, installed=("0.1.40", COMMIT))
    assert len(out) == 1 and "bench.yml" in out[0] and "no ref at all" in out[0], out
    # a pinned URL, a commented example and a .git suffix with a ref are not it
    (r / "bench.yml").write_text('      # pip install "qabench @ git+https://github.com/x/qa-bench"\n'
                                 f'      - run: pip install "qabench @ git+https://github.com/x/qa-bench.git@{COMMIT}"\n')
    subprocess.run(["git", "add", "-A"], cwd=r, check=True)
    assert conformance.pin_agrees(r, installed=("0.1.40", COMMIT)) == []


def _enum_manifest(tmp_path, guards=None, witness=True):
    """A manifest declaring an enumeration command, optionally registered."""
    import yaml
    from qabench import conformance
    c = conformance.contract()
    checks = {cid: {"name": r["name"], "status": "absent", "evidence": [], "reason": "not yet"}
              for cid, r in c["checks"].items()}
    m = {"checks": checks, "enumerate_routes": "python3 scripts/routes.py"}
    if guards is not None:
        (tmp_path / "qa").mkdir(exist_ok=True)
        (tmp_path / "qa" / "guards.yml").write_text(yaml.safe_dump({"guards": guards}), encoding="utf-8")
        m["population"] = {"register": "qa/guards.yml"}
    return m


def test_a_declared_enumeration_nothing_runs_is_named(tmp_path):
    """tharros's enumerate_routes printed 4 routes of 216 under its pinned
    framework, with no error; the manifest held a stale copy and nothing ran it.
    Any command a document hands you is untested unless something runs it."""
    from qabench import conformance
    kinds = {f["kind"] for f in conformance.judge(_enum_manifest(tmp_path), root=tmp_path)}
    assert "enumeration_unrun" in kinds


def test_an_enumeration_registered_without_a_witness_is_named(tmp_path):
    from qabench import conformance
    m = _enum_manifest(tmp_path, guards=[{"id": "routes", "population": {"cmd": "python3 scripts/routes.py"}}])
    kinds = {f["kind"] for f in conformance.judge(m, root=tmp_path)}
    assert "enumeration_unwitnessed" in kinds and "enumeration_unrun" not in kinds


def test_an_enumeration_run_and_witnessed_is_clean(tmp_path):
    from qabench import conformance
    m = _enum_manifest(tmp_path, guards=[{"id": "routes", "population": {
        "cmd": "python3 scripts/routes.py",
        "witness": [{"member": "/order/{code}", "why": "the customer surface"}]}}])
    kinds = {f["kind"] for f in conformance.judge(m, root=tmp_path)}
    assert not kinds & {"enumeration_unrun", "enumeration_unwitnessed"}


def test_the_enumeration_findings_are_advisory_first(tmp_path):
    """The estate's adoption rule: provision, verify it passes, then make it fatal."""
    from qabench import conformance
    found = [f for f in conformance.judge(_enum_manifest(tmp_path), root=tmp_path) if f["kind"] == "enumeration_unrun"]
    assert found and not found[0]["fatal"]


def test_a_pasted_copy_of_the_enumeration_is_named(tmp_path):
    """String equality would accept a guard holding its own copy of the
    manifest's command — which passes today and drifts the next time the
    manifest line changes. D4 one file over."""
    from qabench import conformance
    m = _enum_manifest(tmp_path, guards=[{"id": "routes", "population": {
        "cmd": "python3 scripts/routes.py", "witness": [{"member": "/order", "why": "customer"}]}}])
    kinds = {f["kind"] for f in conformance.judge(m, root=tmp_path)}
    assert "enumeration_copied" in kinds


def test_a_guard_that_reads_the_command_from_the_manifest_is_clean(tmp_path):
    from qabench import conformance
    m = _enum_manifest(tmp_path, guards=[{"id": "routes", "population": {
        "cmd_from": "enumerate_routes", "witness": [{"member": "/order", "why": "customer"}]}}])
    kinds = {f["kind"] for f in conformance.judge(m, root=tmp_path)}
    assert not kinds & {"enumeration_unrun", "enumeration_copied", "enumeration_unwitnessed"}


def test_the_production_dispatch_is_never_on_the_run_list():
    """full_remote dispatches the night lane, which on tharros promotes to
    production on green. A widening that read it as a cheap one-line field would
    turn a conformance run into a production deploy."""
    from qabench import conformance
    assert "full_remote" in conformance.NEVER_RUN
    assert "production" in conformance.NEVER_RUN["full_remote"]
    assert not set(conformance.RUN_TO_VERIFY) & set(conformance.NEVER_RUN)


def _lane_manifest(tmp_path, landing=None):
    from qabench import conformance
    c = conformance.contract()
    checks = {cid: {"name": r["name"], "status": "absent", "evidence": [], "reason": "not yet"}
              for cid, r in c["checks"].items()}
    m = {"checks": checks, "full_remote": "gh workflow run qa-nightly.yml"}
    if landing is not None:
        m["landing"] = landing
    return m


def test_a_promotion_lane_that_does_not_say_what_landing_causes_is_named(tmp_path):
    """On tharros a merge to main, documented as the day lane to staging, is
    also a production release that night. Found by reading the workflow."""
    from qabench import conformance
    kinds = {f["kind"] for f in conformance.judge(_lane_manifest(tmp_path), root=tmp_path)}
    assert "landing_unmapped" in kinds


def test_a_landing_chain_pointing_at_missing_files_is_named(tmp_path):
    from qabench import conformance
    m = _lane_manifest(tmp_path, {"event": "push to main", "chain": [".github/workflows/gone.yml"],
                                  "reaches_production": True})
    assert "landing_chain_missing" in {f["kind"] for f in conformance.judge(m, root=tmp_path)}


def test_a_mapped_landing_chain_is_clean(tmp_path):
    from qabench import conformance
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "qa-nightly.yml").write_text("on: workflow_dispatch\n")
    m = _lane_manifest(tmp_path, {"event": "push to main", "chain": [".github/workflows/qa-nightly.yml"],
                                  "trigger": {"kind": "external",
                                              "ref": "~/Library/LaunchAgents run-if-due.sh, NIGHTLY_HOUR=22"},
                                  "reaches_production": True})
    kinds = {f["kind"] for f in conformance.judge(m, root=tmp_path)}
    assert not kinds & {"landing_unmapped", "landing_chain_missing", "landing_trigger_unstated"}


def test_a_chain_that_does_not_say_what_fires_it_is_named(tmp_path):
    """tharros: the first hop is a LaunchAgent, not a workflow — the hop that hid."""
    from qabench import conformance
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "qa-nightly.yml").write_text("on: workflow_dispatch\n")
    m = _lane_manifest(tmp_path, {"event": "push to main", "chain": [".github/workflows/qa-nightly.yml"],
                                  "reaches_production": True})
    assert "landing_trigger_unstated" in {f["kind"] for f in conformance.judge(m, root=tmp_path)}
