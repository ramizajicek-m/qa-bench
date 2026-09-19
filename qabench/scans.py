"""scans — the standard scanners, one version for six projects, advisory until a project is clean.

    python -m qabench scans                      # the `scans:` block of qa/manifest.yml
    python -m qabench scans --advisory           # findings printed, exit 0 (the adoption step)
    python -m qabench scans --json

WHY IN THE KIT. On 2026-09-19 anat ran gitleaks, pip-audit, schemathesis and
mutmut; the other five ran none of them — the research that chose them landed
in one repo (docs/methodology.md §2). These are off-the-shelf tools; nothing
here reimplements them. The kit's job is ONE pinned version of each, verified
by sha256 before it runs (a scanner fetched unpinned is code nobody reviewed,
running with the repo's secrets in reach), the same flags everywhere, and the
estate's exit contract: 0 clean · 1 findings · 3 a scanner could not run (never
read as clean).

  gitleaks   secrets in the tree and its history (redacted in the output — a
             scan that prints the secret it found is the leak)
  pip-audit  known vulnerabilities in every pinned requirements file
  squawk     Postgres migrations that lock tables or break running code
             (only migrations changed since `scans.since`, default origin/main~20,
             so a project's history does not bury a new one)

Manifest:

    scans:
      requirements: [requirements.txt, requirements-dev.txt]
      migrations: "migrations/*.sql"
      advisory: true            # drop once the first findings are triaged
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

import yaml

#: (url, sha256) per platform — measured by downloading each asset on 2026-09-19.
BINARIES = {
    "gitleaks": {
        "version": "8.30.1",
        ("Linux", "aarch64"): ("https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_arm64.tar.gz",
                               "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080"),
        ("Linux", "x86_64"): ("https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz",
                              "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"),
        ("Darwin", "arm64"): ("https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_darwin_arm64.tar.gz",
                              "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5"),
    },
    "squawk": {
        "version": "2.65.0",
        ("Linux", "aarch64"): ("https://github.com/sbdchd/squawk/releases/download/v2.65.0/squawk-linux-arm64",
                               "df11165f09629da80319e51434a6e4d2f27825801769879e15011d0091218bee"),
        ("Linux", "x86_64"): ("https://github.com/sbdchd/squawk/releases/download/v2.65.0/squawk-linux-x64",
                              "9b7b2b9529a469647e32c6346e8d5a8a760857cbe2ee94ccb37f60e408babffb"),
        ("Darwin", "arm64"): ("https://github.com/sbdchd/squawk/releases/download/v2.65.0/squawk-darwin-arm64",
                              "05b140108aaa04404ed8a0e600dc83ab5c678cac929e621df6f08eb189bdfe5f"),
    },
}
CACHE = Path(os.environ.get("QABENCH_TOOLS") or Path(tempfile.gettempdir()) / "qabench-tools")


def fetch(tool: str) -> Path:
    """The pinned binary, downloaded once, refused if its sha256 differs."""
    spec = BINARIES[tool]
    key = (platform.system(), platform.machine())
    if key not in spec:
        raise RuntimeError(f"no pinned {tool} for {key}")
    url, digest = spec[key]
    dest = CACHE / f"{tool}-{spec['version']}"
    if dest.exists():
        return dest
    CACHE.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as r:
        blob = r.read()
    got = hashlib.sha256(blob).hexdigest()
    if got != digest:
        raise RuntimeError(f"{tool} download sha256 {got[:16]}… is not the pinned {digest[:16]}… — refusing to run it")
    if url.endswith(".tar.gz"):
        with tarfile.open(fileobj=__import__("io").BytesIO(blob)) as t:
            member = next(m for m in t.getmembers() if Path(m.name).name == tool)
            dest.write_bytes(t.extractfile(member).read())
    else:
        dest.write_bytes(blob)
    dest.chmod(0o755)
    return dest


def run_gitleaks(root: Path) -> dict:
    exe = fetch("gitleaks")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        report = Path(f.name)
    p = subprocess.run([str(exe), "git", str(root), "--no-banner", "--redact", "--report-format", "json",
                        "--report-path", str(report), "--exit-code", "1"], capture_output=True, text=True)
    if p.returncode not in (0, 1):
        return {"ran": False, "why": (p.stderr or p.stdout)[-300:]}
    found = json.loads(report.read_text() or "[]")
    report.unlink(missing_ok=True)
    return {"ran": True, "findings": [f"{x.get('RuleID')} {x.get('File')}:{x.get('StartLine')} ({x.get('Commit', '')[:8]})"
                                      for x in found]}


def exact_pins(text: str) -> tuple[list[str], int]:
    """(the `name==version` lines, how many other requirement lines there were)."""
    lines = [l.split("#")[0].strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    pinned = [l for l in lines if "==" in l and not l.startswith("-") and "@" not in l]
    return pinned, len(lines) - len(pinned)


def run_pip_audit(root: Path, files: list[str]) -> dict:
    if not shutil.which("pip-audit") and subprocess.run([sys.executable, "-m", "pip_audit", "--version"],
                                                        capture_output=True).returncode != 0:
        return {"ran": False, "why": "pip-audit is not installed (the kit's `scans` extra)"}
    findings, audited, skipped = [], [], {}
    for name in files:
        path = root / name
        if not path.exists():
            continue
        audited.append(name)
        # Only exact pins can be audited without resolving (a git URL, `-r`,
        # `-e` or a range makes pip-audit refuse the whole file); what is left
        # out is counted, so a file of URLs does not read as clean.
        pinned, skipped[name] = exact_pins(path.read_text(encoding="utf-8"))
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
            tmp.write("\n".join(pinned) + "\n")
        p = subprocess.run([sys.executable, "-m", "pip_audit", "-r", tmp.name, "--format", "json", "--progress-spinner", "off",
                            "--disable-pip", "--no-deps"], capture_output=True, text=True)
        Path(tmp.name).unlink(missing_ok=True)
        try:
            doc = json.loads(p.stdout)
        except ValueError:
            return {"ran": False, "why": f"{name}: {(p.stderr or p.stdout)[-300:]}"}
        for dep in doc.get("dependencies", []):
            for v in dep.get("vulns", []):
                findings.append(f"{name}: {dep['name']} {dep.get('version')} {v['id']} (fix: {', '.join(v.get('fix_versions') or ['none'])})")
    if not audited:
        return {"ran": False, "why": f"none of {files} exists"}
    return {"ran": True, "findings": findings, "audited": audited,
            "note": "; ".join(f"{n}: {k} line(s) not an exact pin, not audited" for n, k in skipped.items() if k) or ""}


def changed_migrations(root: Path, pattern: str, since: str) -> list[Path]:
    p = subprocess.run(["git", "-C", str(root), "diff", "--name-only", since, "--", pattern], capture_output=True, text=True)
    return sorted(root / f for f in p.stdout.split() if (root / f).exists())


def run_squawk(root: Path, pattern: str, since: str) -> dict:
    files = changed_migrations(root, pattern, since)
    if not files:
        return {"ran": True, "findings": [], "note": f"no migration matching {pattern} changed since {since}"}
    exe = fetch("squawk")
    p = subprocess.run([str(exe), "--reporter", "json", *map(str, files)], capture_output=True, text=True)
    try:
        doc = json.loads(p.stdout or "[]")
    except ValueError:
        return {"ran": False, "why": (p.stderr or p.stdout)[-300:]}
    items = doc if isinstance(doc, list) else doc.get("violations", [])
    return {"ran": True, "findings": [f"{Path(v.get('file', '?')).name}:{v.get('line', '?')} {v.get('rule_name') or v.get('rule')}"
                                      for v in items], "checked": [f.name for f in files]}


def run(argv: list[str]) -> int:
    root = Path(argv[argv.index("--repo") + 1] if "--repo" in argv else ".").resolve()
    mpath = root / "qa" / "manifest.yml"
    doc = (yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}) or {}
    cfg = doc.get("scans") or {}
    advisory = "--advisory" in argv or bool(cfg.get("advisory"))
    results = {}
    for name, fn in (("gitleaks", lambda: run_gitleaks(root)),
                     ("pip-audit", lambda: run_pip_audit(root, cfg.get("requirements") or ["requirements.txt"])),
                     ("squawk", (lambda: run_squawk(root, cfg["migrations"], cfg.get("since", "origin/main~20")))
                      if cfg.get("migrations") else None)):
        if fn is None:
            continue
        try:
            results[name] = fn()
        except Exception as ex:  # noqa: BLE001 — a scanner that could not run is exit 3, and says why
            results[name] = {"ran": False, "why": f"{type(ex).__name__}: {str(ex)[:200]}"}
    if "--json" in argv:
        print(json.dumps(results, indent=1))
    else:
        for name, r in results.items():
            if not r["ran"]:
                print(f"{name:10} DID NOT RUN — {r['why']}")
            else:
                print(f"{name:10} {len(r['findings'])} finding(s)" + (f" — {r['note']}" if r.get("note") else ""))
                for f in r["findings"][:30]:
                    print(f"    {f}")
    not_run = [n for n, r in results.items() if not r["ran"]]
    found = sum(len(r.get("findings", [])) for r in results.values())
    if found and advisory:
        print(f"ADVISORY: {found} finding(s) reported, not failing — drop `advisory` once they are triaged")
    if not_run:
        return 3
    return 1 if (found and not advisory) else 0
