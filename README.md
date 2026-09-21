# qabench

**Every recorded conclusion in a tree is dated, and nothing re-reads any of them.** The instruments below are the enforcement — and `mutate --replay` is only as good as the record, which most projects do not have: a repo with years of "watched red" claims in docstrings and commit messages holds dated assertions only a person can check, so extracting them into a record is a real piece of work rather than a command. An empty record reads exit 3 and says so.

**These instruments answer one question — did the check measure anything? — and there is a second, orthogonal to it: did it measure the right thing?** Corpus floors, known-positives, real near-misses, exact pins and mutation replay are all built for vacuity. None of them touches CRITERION MISMATCH, where the check measures the wrong thing correctly — and a control makes a wrong measurement MORE credible, because it proves the instrument was alive while it pointed elsewhere. A row was implemented for months on four green tests that measured page zoom for a requirement about text zoom, behind a corpus floor that worked perfectly. Reading what a test asserts next to what the row says is the only method that has caught this, and its slowness is not incidental to it.

**A class recurs inside the repair for that class, and the repair is written by whoever just finished describing the shape.** Four instances in one repo in one day (2026-09-20): a census fixed for excluding non-compliant cases, whose replacement excluded two routed pages through a pattern the codebase's chained calls never match; the exemption added in that fix, which was INERT — deleting it left every test green; a census written to replace three hand-picked cases, which went green against a COMMENTED-OUT call, the identical defect the same project had fixed hours earlier; and, in this repository, a usage line that still named neither of the two flags it had just grown, one hour after this kit adopted "every recorded conclusion is dated" as its opening line. All were caught by a mutation or a reviewer; NONE by the author re-reading their own work. That is the answer to "why not just write it in a CLAUDE.md": the rules travelled perfectly and the defects recurred anyway, in the hands of the people who had just written the rule down. Prose informs; only the refusal prevents — a denominator refused BY NAME, a verdict that comes from an artefact, an expired mutation that fails, an exemption that has to be shown load-bearing.

The comprehensive QA tier as one package, driven by a project's `qa/manifest.yml`. Six projects run this instead of six copies that drift.

What it proves, against a **running deployment** (it never boots the app):

| stage | proves |
|---|---|
| `smoke` | the deployment answers `/health` with a commit (and it is the SHA the run was asked about); every role can sign in — a dead credential exits 3 and names the variable; a wrong password is refused |
| `pages_by_role` | every page × every role × every viewport (desk and phone): the HTTP status equals the declared guard, zero console errors, zero failed requests, no sideways scroll; a session lost mid-sweep fails the role instead of reading green |
| `endpoints_by_role` | every GET API route × every role: no 500, the declared gate is the real gate, a customer role never passes auth on a staff route |
| `explore` | the independent explorer (opt-in): per persona, a fresh `claude -p` session that did not write the code drives staging as a non-privileged role, briefed with yesterday's commit subjects and the heuristic packs in `qabench/packs/`, never the author's tests; writes go through a fence that aborts any write to a production or forbidden host and fails the night. A session that visits nothing is `3`; findings are advisory until `explore.blocking` |
| `nightly` | runs the three, then the project's own `stages_extra`; the verdict depends on each stage having RUN (a ledger exists) and DECIDED something; writes `nightly.json` with `swept_sha` for the promote step |

One command reads the GUARDS rather than the product: `population` runs, for every guard in `qa/guards.yml`, the command that enumerates the population it claims over and the command that prints what it actually examined, and names the members in the first and not the second. It exists because twelve defects behind green tests on 2026-09-20 were one shape — a corpus keyed on the example's name (`batch|bulk` in a path) rather than on the property (a route that iterates a collection and reports a count). A population derived by naming is refused; a subject of nothing against a population of something is red, not clean; the population count is pinned and may fall only behind a reason with evidence.

And one wraps a run rather than reading one: `ran -- make test-e2e` executes the command as argv (no shell, so no pipeline can swallow the exit code — `make land | tail -25` reported a failed gate as success), tees the whole output to a file, records what was up on the host, and judges the run on its ARTEFACT OF COMPLETION first and its exit code second. A run that did not finish is INVALID, never a pass: an e2e sweep that died in its login fixture exited 2 with zero `FAILED` lines, and anything grepping for failures calls that green. anat's `scripts/suite_postflight.py` is the reference implementation and the source of the completion shapes.

And one asks whether a table's CONTENTS are still its own: `distinct` compares every pair of rows' free text on a sliding window and names any pair sharing more than a pinned run of characters. A `str.replace` over a tracker, keyed on the last sentence of one row's reason, pasted that reason into twenty-one other rows that ended with the same bookkeeping sentence — and every test over the table stayed green, because all of them asserted shape. A guard that asserts only shape passes over any corruption that preserves shape. The threshold is measured, never chosen: the longest innocent overlap in that table is 219 characters and the leak was 1012, so every run prints the measurement and an unpinned table is told what to pin.

Two commands read the record rather than a deployment: `escapes` (defect escape rate and ODC trigger histogram from the project's ledger, red on a finder it cannot classify) and `gap` (did anything ship untested). The method behind all of it — what finds the defects people find, the catalogues adopted, the tools weighed and rejected — is `docs/methodology.md`; the defects it was measured on, with their fix commits, are `benchmarks/escaped.yml`.

Four commands built from the escapes of 2026-09-21, each for a class that recurred across repos (0.1.55):

- `delta --store DIR --name TIER --after junit.xml` — which failures are NEW since the last run of that tier, and which VANISHED (failing before, absent now: usually stopped running, not fixed). ana-log's browser tier was red for days, so thirty-three new failures from one change arrived unseen; a constant is not a signal. Run it after every tier that writes JUnit.
- `fixpop --msg FILE` (commit-msg hook) / `--range A..B` (CI) — a fix commit carries `Population: <the other sites with this shape>` or `Population: none (searched: <how>)`. anat fixed a hand-picked tier being overwritten and left the fee field beside it with the identical defect for two months. Start with `--advisory`.
- `anchors` — prose that names code must still point at it: `path#"literal"` must resolve, and a `path:LINE` citation must exist, and the code quoted right after it must still be within three lines; line citations are pinned and may only fall. The first estate run found stale citations in anat (37), ana-log (9) and tharros (1).
- `hazards` — a `pgrep -f`/`ps | grep` liveness check that matches its own command line (Makefile recipes and `sh -c`), and a test or landing run piped into `tail`/`head` without `tee` or `pipefail`.

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
  engines: [chromium, webkit]            # default [chromium]; webkit is Safari's engine (install it: playwright install --with-deps webkit)
  pages: { include_prefixes: ["/admin"], exclude_prefixes: ["/admin/api/"], sideways_allow: { "/admin/audit": "wide table; fix owed" } }   # known phone-width offenders, a ratchet
  api:   { include_prefixes: ["/api/"], exclude_paths: ["/api/stream"], portal_roles: [customer], portal_prefixes: ["/api/portal"] }
  ignore_console: ["favicon"]            # each entry justified in a comment
  routes: scripts.qa.route_matrix:collect        # -> [{path, methods, admits: {role: bool}}]
  ids:    scripts.qa.route_matrix:resolve_ids    # (owner httpx client) -> {param: id}
  stages_extra:
    - [message_gallery, [scripts/qa/message_gallery.py]]   # must write <shots>/message_gallery.json
  heartbeat: { key: qa_nightly, cadence_h: 30, stamp: scripts.qa.heartbeat:stamp }
  explore:                               # opt-in; off by default
    enabled: true
    budget_min: 25                       # the whole night's time-box, split across personas
    blocking: false                      # findings fail the night once the first weeks are triaged
    forbid_writes_to: [webapp.legacy.example]   # production hosts are always fenced; add any other live system
    personas:                            # every role must be in bench.roles; never the most privileged
      - { role: staff, viewport: [390, 844], who: "a picker on the warehouse floor, one hand, Hebrew" }
```

Top-level keys the kit also reads: `ledger:` (the calibration ledger `escapes` measures), `people:` (first names of this project's customers and stakeholders, so `escapes` counts their finds as escapes), `sandbox_entity:` (the one tenant a write may touch — the explorer is told it) and `project:`.

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

## The kit pin, and the contract behind the twelve (0.1.40)

`qabench/estate.yml` carries `kit_floor`; `python -m qabench report` reads each project's `bench.version` off its integration branch into a `kit` column and a pin below the floor is a RED row — a register made by an older kit answers a different question while looking identical. In each repo, `qabench.conformance.pin_agrees(ROOT)` asserts without a checkout that the manifest's version equals the INSTALLED kit's, that every `qa-bench@` ref is one full commit, and that it is the installed commit. `qabench/contract.yml` says what `implemented` requires per check, what `partial` may lack (by key, in `missing:`), and what proves it ran (`ran:`); `qabench.conformance.judge(manifest, root)` holds a manifest to it — lies are fatal, `●?` (claimed, no ran-proof) and `◐?` (partial with no named gap) are advisory until the repo turns them on. Every release is tagged: `python scripts/release.py X.Y.Z "title"`.

## Its own tests

Local, inactive acceptance-contract, JUnit, ready-work and escaped-defect tools are documented in [the acceptance draft](docs/acceptance.md). Their new tests are written but not executed; they do not change the current nightly or promotion path.

`tests/` boots a two-role FastAPI app and plants one defect per test — a removed guard, a script that dies after render, a 3000px element, a 500, a dead secret — and asserts the stage names it. The kit is not believed until it has gone red for the right reason.
