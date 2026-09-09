# qabench

The comprehensive QA tier as one package, driven by a project's `qa/manifest.yml`. Six projects run this instead of six copies that drift.

What it proves, against a **running deployment** (it never boots the app):

| stage | proves |
|---|---|
| `smoke` | the deployment answers `/health` with a commit (and it is the SHA the run was asked about); every role can sign in — a dead credential exits 3 and names the variable; a wrong password is refused |
| `pages_by_role` | every page × every role × every viewport (desk and phone): the HTTP status equals the declared guard, zero console errors, zero failed requests, no sideways scroll; a session lost mid-sweep fails the role instead of reading green |
| `endpoints_by_role` | every GET API route × every role: no 500, the declared gate is the real gate, a customer role never passes auth on a staff route |
| `nightly` | runs the three, then the project's own `stages_extra`; the verdict depends on each stage having RUN (a ledger exists) and DECIDED something; writes `nightly.json` with `swept_sha` for the promote step |

Exit codes everywhere: `0` proven · `1` failed · `3` nothing failed but something did not run — and 3 is never reported as 0.

## Install

```
pip install "git+https://github.com/ramizajicek-m/qa-bench@v0.1.13"
python -m playwright install --with-deps chromium
```

## The manifest block

```yaml
bench:
  version: 0.1.13                        # asserted against the installed kit
  origin_env: QA_BASE_URL                # the staging URL; production hosts are refused
  health: /health                        # must return JSON with `commit`
  roles: [owner, staff]
  credentials:
    password_env: "QA_{ROLE}_PASSWORD"   # {ROLE} upper, {role} lower
    email_env: "QA_{ROLE}_EMAIL"         # or email_template: "qa-{role}@example.com"
    keychain_service: "myapp-qa-{role}"  # laptop fallback, optional
  login: { path: /login, fields: {email: email, password: password}, cookies: [session, csrf_token], csrf_cookie: csrf_token, csrf_field: _csrf }   # csrf_field only when the form is CSRF-protected
  # an app that signs in with a JSON POST instead of a form (ana-log):
  # login: { kind: json, path: /api/auth/login, body: {email: email, password: password}, expect: 200, page: /login, cookies: [analog_refresh], bearer: accessToken, bearer_browser: cookie }
  viewports: [[1440, 900], [390, 844]]
  pages: { include_prefixes: ["/admin"], exclude_prefixes: ["/admin/api/"], sideways_allow: { "/admin/audit": "wide table; fix owed" } }   # known phone-width offenders, a ratchet
  api:   { include_prefixes: ["/api/"], exclude_paths: ["/api/stream"], portal_roles: [customer], portal_prefixes: ["/api/portal"] }
  ignore_console: ["favicon"]            # each entry justified in a comment
  routes: scripts.qa.route_matrix:collect        # -> [{path, methods, admits: {role: bool}}]
  ids:    scripts.qa.route_matrix:resolve_ids    # (owner httpx client) -> {param: id}
  stages_extra:
    - [message_gallery, [scripts/qa/message_gallery.py]]   # must write <shots>/message_gallery.json
  heartbeat: { key: qa_nightly, cadence_h: 30, stamp: scripts.qa.heartbeat:stamp }
```

### `login`

| key | form (default) | json |
|---|---|---|
| `kind` | `form` — one form-encoded POST to `path` | `json` — a JSON body to `path` |
| `path` | the form's action | the endpoint |
| `fields` | form field → credential (`{email: email, password: password}`) | ignored |
| `body` | ignored | JSON key → credential; `{email: email, password: password}` sends `{"email": …, "password": …}` |
| `expect` | not asserted (a form answers its redirect) | the status of a successful login, default 200 |
| `page` | the sign-in page a signed-out browser lands on — default `path` | required in practice: `path` is an endpoint the browser never lands on, so without it a lost session reads as the route |
| `cookies` | the cookies a login must set; the first is the session | same |
| `csrf_cookie` / `csrf_field` | the pair a protected form demands back | refused — there is no form to fetch a token from |
| `bearer` | refused | the key (dotted for nesting) under which the login answers a bearer token, e.g. `accessToken`; every httpx request the stages make then carries `Authorization: Bearer …`, and a 200 without the token is not a login |
| `bearer_browser` | — | with `bearer`, required: `header` installs the token on the browser context for every navigation and fetch (a server that gates pages by bearer); `cookie` installs nothing — the app's own script mints its token from the planted cookie (ana-log's SPA calls `/api/auth/refresh` on load) |

Both kinds prove the same thing and are judged by one rule (`core.login_accepted`): the first named cookie was set, and with `bearer` the token was answered too. A status alone is not a login — a JSON endpoint answers 200 with no session when it wants a second factor — and the smoke stage's "a wrong password is refused" uses the same rule in the other direction. The cookies the POST set are planted in the browser context the page stages drive, whichever kind set them, each at the path the server scoped it to (ana-log's refresh cookie lives under `/api` and is rotated on every refresh; a copy at `/` would sit beside the rotated one and the server would read the revoked one).

`bearer_browser` is not defaulted because the two modes are not interchangeable: in Chromium a context extra header OVERRIDES the same header the page's own `fetch` sets (measured 2026-09-07), so `header` on an app that refreshes its own token would clobber every later token with the stale first one. An app whose session outlives its access token (ana-log: 15 minutes) should also set `session_ttl_s` below that lifetime, so a later stage signs in again rather than probing with an expired token.

## Run

```
QA_BASE_URL=https://staging.example.com QA_EXPECT_SHA=$GITHUB_SHA python -m qabench nightly
python -m qabench stage pages_by_role --roles owner --only /admin
python -m qabench show
```

## Release evidence

Push CI for an unchanged full SHA may use `--immutable-push-evidence`: its
successful required jobs remain valid across a weekend or operational hold.
Night/deployed checks retain the freshness limit and reject that flag. Both
still require the newest eligible run and current attempt, so a failed rerun
cannot fall back to older success.

`python qabench/release_gate.py` is a stdlib-only reader for deployment workflows. Run it from a checkout of this kit pinned to a full commit, before introducing production credentials. It never deploys or waits for another job. Example:

```sh
python qabench/release_gate.py --repo owner/project --sha "$CANDIDATE_SHA" \
  --workflow qa-nightly.yml --branch main --event schedule --event workflow_dispatch \
  --required staging_is_healthy --required bench --max-age-hours 30
```

The candidate must already be resolved to a full SHA. Required names are exact displayed job names: enumerate every expected matrix member, such as `browser (phone)` and `browser (desktop)`, rather than a prefix. The caller owns this contract and must include every necessary tier and a staging-target proof job where a workflow supports multiple targets. Existing branch-eligibility checks remain required. Workflows that execute a different checkout from their own GitHub head SHA (Anat's current scheduled bench) need candidate-bound evidence or a matching dispatch contract before using this gate.

The reader selects the latest eligible run for this workflow/SHA/branch/event set, never the latest successful one. Automated callers can bind `--run-id` and `--attempt`; a superseding run or rerun refuses. It reads every page of the current attempt's jobs and requires each prerequisite to have completed successfully. The enclosing nightly may still be dispatching its promotion job, preventing a recursive wait. GitHub can carry successful jobs into a failed-only rerun: these count only when the current attempt's API includes them, they belong to the same run/SHA and their own completion evidence remains fresh. A fresh retry cannot rejuvenate stale successful jobs. The JSON result names the actual job IDs and attempts. Exit codes: 0 accepted, 1 refused, 3 evidence unavailable.

The estate report rejects literal `unknown` build identities, compares staging against `staging_branch` when configured, and prints valid JSON even when all projects are healthy. A queued night has a default 0.5-hour deadline; active execution has a default 3-hour deadline measured from `run_started_at`, so fresh retries do not inherit the original run's age. Projects can set `queue_deadline_h` and `run_deadline_h` separately. These are observation deadlines, not evidence that a cancelled/failed job was repaired; a full release-flow ownership ledger remains separate work.

## Its own tests

`tests/` boots a two-role FastAPI app and plants one defect per test — a removed guard, a script that dies after render, a 3000px element, a 500, a dead secret — and asserts the stage names it. The kit is not believed until it has gone red for the right reason.
