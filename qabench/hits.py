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

#: Comma-separated JSON body keys whose VALUE discriminates the control, for an
#: app that dispatches many operations through one path.
#:
#: ana-log is the case that needed it: all 55 of its write actions post to
#: `POST /api/actions/<category>` with `{"function": "<name>", ...}` in the body.
#: A path-based recording cannot tell them apart at all — its judgeable subset was
#: ZERO — so the measure had nothing to say about a whole project rather than
#: saying something weak.
#:
#: Off unless set, and the key is named by the repo rather than guessed: a
#: recorder that rummaged through every body looking for something
#: discriminating would invent a different answer per project.
BODY_KEYS_ENV = "QABENCH_RECORD_BODY_KEYS"

#: {"METHOD path", ...} for the current process.
_seen: set = set()
_installed = False


def _body_discriminator(request) -> str:
    """`#<value>` for the first configured body key present, else "".

    Reads the request's OWN body bytes, which httpx has already encoded, so this
    sees exactly what the server will. Anything unparseable is not an error here:
    a recorder must never fail a suite, and a body it cannot read simply does not
    discriminate.
    """
    keys = [k for k in os.environ.get(BODY_KEYS_ENV, "").split(",") if k]
    if not keys:
        return ""
    try:
        raw = request.content
        if not raw or len(raw) > 200_000:
            return ""
        body = json.loads(raw)
        if not isinstance(body, dict):
            return ""
        for key in keys:
            value = body.get(key)
            if isinstance(value, str) and value:
                return "#" + value
    except Exception:
        return ""
    return ""


def record(method: str, path: str, status: int = 0, location: str = "",
           host: str = "") -> None:
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
    # TAB-separated trailer so a path containing a space cannot shift the fields,
    # and so an older two-field row still parses.
    _seen.add(f"{method.upper()} {path} {int(status)}\t{location}\t{host}")


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
            record(request.method, request.url.path + _body_discriminator(request),
                   response.status_code,
                   location=response.headers.get("location", ""),
                   host=request.url.host or "")
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
                record(request.method, request.url.path + _body_discriminator(request),
                       response.status_code,
                       location=response.headers.get("location", ""),
                       host=request.url.host or "")
            except Exception:
                pass
            return response

        httpx.AsyncClient.send = asend
    except AttributeError:
        pass
    return True


#: The recording's own format, because a row's SHAPE decides which questions it
#: can answer and the reader could not tell an old file from a new one.
#:
#: 1 — "METHOD path" only. Cannot answer "accepted".
#: 2 — "METHOD path STATUS". Cannot answer "accepted" for a redirect, because
#:     whether a 303 went to a login page is the whole question.
#: 3 — "METHOD path STATUS\tLocation\tHost". Answers it.
#:
#: Measured 2026-09-13 on IGA: its committed recording was format 2, and reading
#: it with the current `_acted` turned every 3xx into "never accepted" — 3
#: never-accepted mutating controls became 20. That looked exactly like a
#: product finding and was a fact about the file's age. `POST /admin/courses/create`
#: had recorded 303, 307, 403 and 422 and no Location column to judge the 303 by.
FORMAT = 3


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
    doc = {"format": FORMAT, "recorded": sorted(_seen), "count": len(_seen)}
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


#: Below this, the app ACTED on the request. At or above it, the app refused,
#: and a refusal says nothing about whether the control works.
#: What counts as the app having ACTED on the request.
#:
#: 2xx only, and that is a correction. The first version used `status < 400`,
#: which counts every redirect — and in these apps a redirect is ambiguous by
#: construction. Measured on my8200, 2026-09-13:
#:
#:     POST /admin/crm/2  unauthenticated  ->  303  Location: /login?next=...
#:
#: byte-identical in status to a successful form post. 42 of my8200's 220 write
#: targets and 78 of tharros' 381 were credited ONLY by a 3xx, and 13 of
#: tharros' only by 307/308 — where the handler never processed the body at all,
#: so those were outright false hits. tharros reporting "103 judgeable, 103
#: accepted, 0 never accepted" was the signature of a saturated measure, not a
#: covered application.
#:
#: A 3xx can still earn credit, but only on evidence rather than on its number:
#: it must carry a Location that is not a sign-in bounce, and 307/308 never
#: qualify because they are re-issued before the body is read.
ACCEPTED_MIN, ACCEPTED_MAX = 200, 300

#: Paths a redirect lands on that mean "you are not signed in", not "done".
#: Declared rather than guessed: a repo that signs in somewhere else says so.
LOGIN_ENV = "QABENCH_LOGIN_PATHS"
DEFAULT_LOGIN_PATHS = ("/login", "/signin", "/sign-in", "/auth/login", "/accounts/login")

#: Hosts whose traffic belongs to the app under test. Without this every
#: third-party call a test makes can credit a control that shares its path —
#: my8200's own recording carries six Google Cloud Storage rows
#: (`DELETE /storage/v1/b/bucket/o/daily/old.gz 204`), and nothing distinguished
#: them from the app's own writes.
HOSTS_ENV = "QABENCH_RECORD_HOSTS"


#: Query parameters that mean "come back here after you sign in". Their presence
#: is what makes a redirect to a login page a REFUSAL: the app is bouncing the
#: caller and remembering where they were going.
#:
#: Without this the rule was "any redirect to a login path is a refusal", and that
#: is wrong for every flow whose SUCCESS ends at the login page. Measured on
#: my8200, 2026-09-13: `POST /reset/<token>` answered `303 -> /login?reset=1` —
#: the password reset WORKED, and the register counted the control as never once
#: accepted. A false negative that reads as a defect, which is the same cost as
#: the false positive this whole line of work started from.
BOUNCE_PARAMS = ("next=", "next_url=", "redirect=", "redirect_to=", "return=",
                 "return_to=", "returnTo=", "continue=", "from=")


def _is_login_bounce(location: str) -> bool:
    """Whether this redirect is the app REFUSING, rather than a flow finishing.

    A login path plus a "come back after signing in" parameter, or a login path
    with no query at all. A login path carrying anything else is the end of a
    flow — a reset, a logout, an email change — and the app acted.

    Deliberately not "any query means success": `/login?next=/admin/x` is the
    commonest refusal there is, and a rule that read it as a flow finishing would
    credit every unauthenticated probe in the estate.
    """
    target, _, query = (location or "").partition("?")
    target = target.rstrip("/")
    if not target:
        return False
    at_login = any(target.endswith(p.rstrip("/")) or target == p.rstrip("/")
                   for p in _login_paths())
    if not at_login:
        return False
    if not query:
        return True
    return any(b in query for b in BOUNCE_PARAMS)


def _login_paths() -> tuple:
    declared = tuple(p for p in os.environ.get(LOGIN_ENV, "").split(",") if p)
    return declared or DEFAULT_LOGIN_PATHS


def _acted(status: int, location: str) -> bool:
    """Did the app ACT on this request, as opposed to answering it?"""
    if ACCEPTED_MIN <= status < ACCEPTED_MAX:
        return True
    if status in (307, 308):
        return False            # re-issued before the body was read
    if 300 <= status < 400:
        if not (location or ""):
            return False        # a redirect with no Location decides nothing
        return not _is_login_bounce(location)
    return False


class StaleRecording(RuntimeError):
    """A recording whose rows cannot answer the question being asked of them."""


def _inferred_format(rows) -> int:
    """The format of a file that does not declare one, from its rows' shape.

    Every recording committed before 2026-09-13 is undeclared, and guessing is
    better than assuming the newest: a file whose rows carry no tab cannot have
    a Location in it, whatever it claims.
    """
    if not rows:
        return FORMAT          # nothing to misread
    if any("\t" in r for r in rows):
        return 3
    head = rows[0].rsplit(" ", 1)
    return 2 if len(head) == 2 and head[1].isdigit() else 1


def read(path, accepted_only: bool = True) -> set:
    """The recorded hits as "METHOD path", or an empty set if none recorded yet.

    A DIRECTORY unions every *.json recording inside it, one file per tier: the
    unit and integration tiers are separate commands, and a single file meant the
    second overwrote the first — a control driven in integration then read as
    never accepted, so work done looked like no progress.

    A repo with no recording is not in a failing state — it has not opted in.
    Callers must report the difference rather than treating "unknown" as "no".

    `accepted_only` keeps only the requests the app ACTED on (see `_acted`),
    which is the default because a probe asserting a route refuses is not an
    exercise of the control. Pass False to see everything the suite touched,
    refusals included — the opposite question, and the one that says which routes
    nothing has ever so much as knocked on.

    When QABENCH_RECORD_HOSTS names the app's hosts, traffic to any other host is
    dropped: a third party sharing a path must not credit a control.
    """
    p = Path(path)
    if p.is_dir():
        out: set = set()
        for f in sorted(p.glob("*.json")):
            out |= read(f, accepted_only=accepted_only)
        return out
    if not p.exists():
        return set()
    hosts = tuple(h for h in os.environ.get(HOSTS_ENV, "").split(",") if h)
    doc = json.loads(p.read_text(encoding="utf-8"))
    rows = doc.get("recorded", [])

    # **A RECORDING TOO OLD TO ANSWER THIS QUESTION IS REFUSED, not reinterpreted.**
    # The reader already knew about a recording made before statuses; it did not
    # know about one made before Locations, and a bare 3xx from such a file fell
    # through `_acted` as "not accepted". Silent, plausible, and wrong in the
    # direction that reads as a product regression: IGA's 3 never-accepted
    # mutating controls became 20 on a pin bump alone.
    #
    # The TOUCHED question is still answerable from an old file — it needs only
    # the path — so only `accepted_only` refuses. Re-record; do not soften this.
    if accepted_only and int(doc.get("format", _inferred_format(rows))) < FORMAT:
        raise StaleRecording(
            f"{p} is recording format {doc.get('format', _inferred_format(rows))}, "
            f"and the accepted/not-accepted question needs {FORMAT}: a redirect "
            f"cannot be judged without its Location, so every 3xx in this file "
            f"would silently read as NEVER ACCEPTED. Treat this as DID NOT RUN "
            f"and re-record (`make hits`). Reading it for TOUCHED is fine.")

    out = set()
    for row in rows:
        head, _, trailer = row.partition("\t")
        location, _, host = trailer.partition("\t")
        parts = head.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].isdigit():
            where, status = parts[0], int(parts[1])
        else:                                   # a recording made before statuses
            where, status = head, 0
        if hosts and host and host not in hosts:
            continue
        if accepted_only and not _acted(status, location):
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
