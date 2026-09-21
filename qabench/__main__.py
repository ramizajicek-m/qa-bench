"""    python -m qabench nightly [--only a,b] [--except c] [--manifest PATH]
    python -m qabench stage <smoke|pages_by_role|endpoints_by_role|explore> [stage args]
    python -m qabench show          # the resolved config, credentials as presence only
    python -m qabench report [--estate FILE] [--json]   # every project, every morning: did the night run, is production the swept build
    python -m qabench scans [--advisory] [--json]   # gitleaks, pip-audit, squawk at one pinned version
    python -m qabench shapes [--dsn DSN] [--json]   # real records of each risky shape, with the URL to open
    python -m qabench questions <kind...>   # the questions to put to the requester before building
    python -m qabench asked [--changed-since "7 days ago"] [--json]   # every surface's questions answered or owned
    python -m qabench distinct [--repo DIR] [--json]   # a table edited programmatically keeps its rows distinct; the threshold is measured, never chosen
    python -m qabench census [--repo DIR] [--json]   # every declared key reaches every consumer layer, or is exempted with evidence
    python -m qabench population [--repo DIR] [--json]   # every guard sweeps the population it claims over, not the example it was written against
    python -m qabench ran --name NAME [--heavy] [--json] -- COMMAND ...   # --heavy: machine-wide lock, one heavy run at a time; run it without a shell, keep the whole output, and refuse to call a run that did not finish a pass
    python -m qabench delta (--before A.xml | --store DIR --name TIER) --after B.xml   # which failures are NEW on a tier that was already red
    python -m qabench fixpop (--msg FILE | --range A..B) [--advisory]   # a fix commit names the other sites with its shape
    python -m qabench anchors [--repo DIR] [--show]   # prose citing code (path#"literal", path:LINE) still points at it
    python -m qabench hazards [--repo DIR]   # self-matching liveness checks; test runs piped into tail
    python -m qabench inherited FILE --property "<words>" [--declared LIT=why]   # selector literals the property does not contain: a guard for the case, not the class
    python -m qabench decisions [--repo DIR] [--strict]   # every ruling says what observation would prove it wrong
    python -m qabench runners [--estate FILE]   # what every shared runner is running, from which repo, for how long
    python -m qabench elements CLASS [--repo DIR] [--glob P]   # elements carrying a class vs mentions of its name
    python -m qabench escapes [--ledger PATH] [--benchmark PATH] [--days N] [--json]   # escape rate + ODC trigger histogram; red on an unclassified finder
    python -m qabench gap [--repo DIR] [--slug OWNER/NAME] [--workflow F] [--since "1 day ago"] [--json]
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import __version__, anchors, decisions, elements, inherit, runners, delta, fixpop, hazards, scans, census, core, distinct, escapes, gap, manifest, nightly, population, ran as _ran, report, requirements, shapes
from .stages import endpoints_by_role, explore, pages_by_role, smoke

STAGES = {"smoke": smoke.main, "pages_by_role": pages_by_role.main, "endpoints_by_role": endpoints_by_role.main,
          "explore": explore.main}


def _cfg(argv: list[str]) -> manifest.Bench:
    path = Path(argv[argv.index("--manifest") + 1]) if "--manifest" in argv else None
    repo = path.parent.parent if path else Path.cwd()
    cfg = manifest.load(repo, manifest=path)
    if cfg.version and cfg.version != __version__:
        raise SystemExit(f"qa/manifest.yml pins bench.version {cfg.version} but qabench {__version__} is installed — "
                         "install the pinned version or update the pin in the same commit")
    return cfg


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "version":
        print(__version__)
        return 0
    if cmd == "mutate":
        # No manifest and no version pin: this is a hand tool for watching a
        # guard go red, and it must work in a repo mid-edit — which is exactly
        # the state in which `git checkout --` eats your work.
        from qabench import mutate as _mutate
        return _mutate.main(rest)
    if cmd == "runners":                    # the estate's runners, never one repo
        return runners.run(rest)
    if cmd == "report":                     # no manifest, no pin: it reads the estate, not one repo
        return report.run(rest)

    # Tier 4, the portable half: did anything ship untested? Reads git and the CI
    # history, so it needs no per-project data model -- which is why this half
    # generalises and anat's "was it what was asked" half does not.
    if cmd == "gap":
        return gap.run(rest)
    if cmd == "scans":                      # gitleaks, pip-audit, squawk — pinned and verified
        return scans.run(rest)
    if cmd == "shapes":                     # real records with the shapes defects hide in
        return shapes.run(rest)
    if cmd == "questions":                  # what to ask the requester, per kind of surface
        return requirements.run_questions(rest)
    if cmd == "asked":                      # qa/requirements.yml: were they asked, and what did they say
        return requirements.run_asked(rest)
    if cmd == "distinct":                   # reads a table's rows, never a deployment
        return distinct.run(rest)
    if cmd == "census":                     # reads source and descriptors, never a deployment
        return census.run(rest)
    if cmd == "ran":                        # runs a command and judges its completion; no manifest pin
        return _ran.run(rest)
    if cmd == "population":                 # reads the guard register and runs both sides, never a deployment
        return population.run(rest)
    if cmd == "delta":                      # two JUnit reports, never a deployment
        return delta.run(rest)
    if cmd == "fixpop":                     # commit messages, never a deployment
        return fixpop.run(rest)
    if cmd == "anchors":                    # prose against the tree, never a deployment
        return anchors.run(rest)
    if cmd == "hazards":                    # shell and workflow text, never a deployment
        return hazards.run(rest)
    if cmd == "inherited":                  # one guard file against its property, never a deployment
        return inherit.run(rest)
    if cmd == "decisions":                  # qa/decisions.yml, never a deployment
        return decisions.run(rest)
    if cmd == "elements":                   # markup, never a deployment
        return elements.run(rest)
    if cmd == "escapes":                    # reads a ledger or the seeded-fault benchmark, never a deployment
        return escapes.run(rest)
    cfg = _cfg(rest)
    if cmd == "nightly":
        return nightly.run(cfg, rest)
    if cmd == "stage":
        name = rest[0] if rest else ""
        if name not in STAGES:
            raise SystemExit(f"unknown stage {name!r}; one of {', '.join(STAGES)}")
        return core.run_stage(name, STAGES[name], cfg, rest[1:])
    if cmd == "show":
        print(f"qabench {__version__}\norigin   {cfg.origin}\nroles    {', '.join(cfg.roles)}\nroutes   {cfg.routes}\nshots    {cfg.shots}")
        for role in cfg.roles:
            try:
                email, _ = core.credentials(cfg, role)
                print(f"  {role:20s} {email}  <password set>")
            except SystemExit as ex:
                print(f"  {role:20s} MISSING — {ex}")
        return 0
    raise SystemExit(f"unknown command {cmd!r}\n{__doc__}")


if __name__ == "__main__":
    sys.exit(main())
