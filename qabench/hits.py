"""NAMED IS NOT PRESSED. This is how a control earns the stronger word.

THE WEAKNESS THIS ADDRESSES. `qabench.gestures.driven_by_corpus` asks whether
any file under tests/ MENTIONS a control — its URL, or its id. A docstring
satisfies it. That was a deliberate first step and its own docstring says so,
but it is the weakest evidence standard in the field: Cypress UI Coverage and
pytest-api-cov both require an EXECUTED step to have touched the element before
they count it. A control can be "driven" here and never once have been pressed.

WHAT THIS RECORDS. Every request the test suite actually makes. The suite is
already driving the app through a client; nothing was writing down where. Turn
it on for one run and the result is the set of (METHOD, path) pairs the tests
genuinely exercised — evidence of execution rather than of mention.

    QABENCH_RECORD_HITS=qa/hits.json pytest tests/

WHY IT IS OFF BY DEFAULT. A recorder that always runs is a recorder that slows
every suite and rewrites a tracked file on every invocation, so the file churns
and people stop reading it. It is a deliberate act, like `--rebaseline`.

WHAT IT DOES NOT CLAIM. A recorded POST to `/admin/x/1/delete` proves a TEST
reached that route. It does not prove the control in the template is wired to
it, and it does not prove the stored row changed — that is the journeys' job,
kept separate on purpose so neither can stand in for the other. What it does
kill is the case this exists for: a route that nothing has ever called, sitting
behind a register row that says "driven" because a comment mentions it.

HOW IT HOOKS IN. `httpx.Client.send` is the one place every request goes,
including Starlette/FastAPI's TestClient, which subclasses it. One patch rather
than a fixture each project has to remember to use — a fixture nobody applies is
the failure this whole program keeps finding.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ENV = "QABENCH_RECORD_HITS"

#: {"METHOD path", ...} for the current process.
_seen: set = set()
_installed = False


def record(method: str, path: str, status: int = 0) -> None:
    """One request the suite made, and what the app answered.

    THE STATUS IS NOT DECORATION, and a live run proved it within minutes. IGA's
    register listed six destructive admin controls as driven by nothing. The
    recorder said all six WERE posted to — by `test_every_field_is_accounted_for`,
    which walks the route table posting to every route WITHOUT a CSRF token and
    with required fields missing, asserting each one refuses.

    So the route is reached and nothing has ever successfully deleted anything.
    A request that got a 403 is evidence about the guard, not about the control.
    Counting it as a hit would have replaced a measure that undercounts with one
    that overcounts, which is worse: the first leaves a to-do, the second
    retires it.
    """
    _seen.add(f"{method.upper()} {path} {int(status)}")


def install() -> bool:
    """Patch httpx so every request the suite makes is written down.

    Returns False when httpx is absent or the patch is already in place, so a
    caller can say DID NOT RUN rather than report an empty recording as a clean
    result.
    """
    global _installed
    if _installed:
        return False
    try:
        import httpx
    except ImportError:
        return False

    original = httpx.Client.send

    def send(self, request, *a, **kw):
        response = original(self, request, *a, **kw)
        try:
            record(request.method, request.url.path, response.status_code)
        except Exception:       # never let bookkeeping break a suite
            pass
        return response

    httpx.Client.send = send
    _installed = True

    try:                        # the async client is a separate class
        original_async = httpx.AsyncClient.send

        async def asend(self, request, *a, **kw):
            response = await original_async(self, request, *a, **kw)
            try:
                record(request.method, request.url.path, response.status_code)
            except Exception:
                pass
            return response

        httpx.AsyncClient.send = asend
    except AttributeError:
        pass
    return True


def write(path) -> dict:
    """Persist what was recorded. Refuses to write an empty recording.

    An empty file would be indistinguishable from "the suite drives nothing",
    and would silently mark every control unhit on the next read — a count
    leaping for a reason that looks like a product regression.
    """
    if not _seen:
        raise RuntimeError(
            "the recorder saw no requests at all. Either the suite makes none, "
            "or install() ran after the client was imported and bound. Treat "
            "this as DID NOT RUN; refusing to write an empty hits file.")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc = {"recorded": sorted(_seen), "count": len(_seen)}
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


#: Below this, the app ACTED on the request. At or above it, the app refused,
#: and a refusal says nothing about whether the control works.
ACCEPTED = 400


def read(path, accepted_only: bool = True) -> set:
    """The recorded hits as "METHOD path", or an empty set if none recorded yet.

    A repo with no hits file is not in a failing state — it has not opted in.
    Callers must report the difference rather than treating "unknown" as "no".

    `accepted_only` drops the refusals, which is the default because a probe
    that asserts a route refuses without CSRF is not an exercise of the control.
    Pass False to see everything the suite touched, refusals included — useful
    for the opposite question, which routes no test has ever so much as knocked
    on.
    """
    p = Path(path)
    if not p.exists():
        return set()
    out = set()
    for row in json.loads(p.read_text(encoding="utf-8")).get("recorded", []):
        parts = row.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].isdigit():
            where, status = parts[0], int(parts[1])
        else:                                   # a pre-status recording
            where, status = row, 0
        if accepted_only and status >= ACCEPTED:
            continue
        out.add(where)
    return out


# --- pytest integration ------------------------------------------------------

def pytest_configure(config):            # pragma: no cover - exercised by a live run
    if os.environ.get(ENV):
        install()


def pytest_sessionfinish(session, exitstatus):   # pragma: no cover
    target = os.environ.get(ENV)
    if not target:
        return
    try:
        doc = write(target)
        print(f"\nqabench: recorded {doc['count']} distinct requests -> {target}")
    except RuntimeError as e:
        print(f"\nqabench: {e}")
