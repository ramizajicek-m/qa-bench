"""    python -m qabench nightly [--only a,b] [--except c] [--manifest PATH]
    python -m qabench stage <smoke|pages_by_role|endpoints_by_role> [stage args]
    python -m qabench show          # the resolved config, credentials as presence only
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import __version__, core, manifest, nightly
from .stages import endpoints_by_role, pages_by_role, smoke

STAGES = {"smoke": smoke.main, "pages_by_role": pages_by_role.main, "endpoints_by_role": endpoints_by_role.main}


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
