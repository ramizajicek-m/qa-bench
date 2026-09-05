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
pip install "git+https://github.com/ramizajicek-m/qa-bench@v0.1.7"
python -m playwright install --with-deps chromium
```

## The manifest block

```yaml
bench:
  version: 0.1.7                         # asserted against the installed kit
  origin_env: QA_BASE_URL                # the staging URL; production hosts are refused
  health: /health                        # must return JSON with `commit`
  roles: [owner, staff]
  credentials:
    password_env: "QA_{ROLE}_PASSWORD"   # {ROLE} upper, {role} lower
    email_env: "QA_{ROLE}_EMAIL"         # or email_template: "qa-{role}@example.com"
    keychain_service: "myapp-qa-{role}"  # laptop fallback, optional
  login: { path: /login, fields: {email: email, password: password}, cookies: [session, csrf_token], csrf_cookie: csrf_token, csrf_field: _csrf }   # csrf_field only when the form is CSRF-protected
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

## Run

```
QA_BASE_URL=https://staging.example.com QA_EXPECT_SHA=$GITHUB_SHA python -m qabench nightly
python -m qabench stage pages_by_role --roles owner --only /admin
python -m qabench show
```

## Its own tests

`tests/` boots a two-role FastAPI app and plants one defect per test — a removed guard, a script that dies after render, a 3000px element, a 500, a dead secret — and asserts the stage names it. The kit is not believed until it has gone red for the right reason.
