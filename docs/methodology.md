# Methodology — what the industry already knows about finding our defects, and why our earlier research did not hold

Written 2026-09-19 from a review of every defect a PERSON found in ana-log since August (120 rows: Israel 35, Rami 24, Shahar 19, Meir 18, Chilik 11, others 13), anat's earlier catalogue work (`anat-agent/docs/qa-taxonomy-map.md`, 2026-09-10; `docs/the-suite-is-the-qa-team.md`, 2026-08-23) and a web survey of testing literature, standards and tools, every tool verified alive against its repository on 2026-09-19. This is the record whose absence was the first cause: the same survey had been done once before, landed in one repo, and nothing said it had been done.

## 1. What people find, measured — the 120 rows

`benchmarks/escaped.yml` holds every row with its mechanism, fix commit, owning check, shape and ODC trigger. The shape totals:

| shape | rows | share | what it is |
|---|---|---|---|
| (d) two correct halves | 30 | 25 % | a key is served and nothing reads it; the API affords it and the UI does not offer it; their descriptor says `link`/`qr`/`filter` and our renderer has no case. Ten instances of ONE shape. |
| (h) other | 29 | 24 % | stale recorded decision 5 · decision taken instead of question asked 3 · absent or unreachable control 5 · a spec we held and never read 2 · an instrument with no subject 5 · copy 5 · a domain rule only a person knows 4 |
| (c) device / physical | 18 | 15 % | every browser journey ran at 1600×1000 in one headless Chromium; printer paper, camera field of view, a popup after `await`, pinch-zoom, a phone's vertical budget |
| (e) environment | 13 | 11 % | a green health over a closed door, a stale mirror, deployments skipped |
| (a) sequence | 9 | 7.5 % | save-then-where, choose-then-type, double tap |
| (f) genuine UX request | 9 | 7.5 % | the only class we WANT people to report |
| (b) rare data shape | 6 | 5 % | vacuous fixtures — `'א' * n`, a warehouse with no street |
| (g) permission / scope | 6 | 5 % | SuperAdmin passes every gate |

The other diagnosis on the table — "sequences and rare data shapes; build a control × rule matrix per screen" — is one eighth of it.

## 2. Why the earlier research did not hold — five checkable causes

1. **It landed in one repo.** `hypothesis`, `schemathesis`, `mutmut` are pinned in anat-agent and in none of the other five (measured 2026-09-19). The hand-over note says "copy the files by hand". The kit got none of it.
2. **Tools were adopted as frozen baselines.** 618 axe violations, 352 surviving mutants, 26 server errors — each a shrink-only ratchet with no burn-down date. A ratchet says "no new defects", never "no defects".
3. **Gaps were written "owed" and nobody owned them.** The taxonomy map lists *double submit, back button, refresh mid-write, unicode/RTL* as "no mechanical form yet". A week later Meir and Israel reported exactly those (ACT-04: a double tap was two POSTs).
4. **The tools were aimed at the server.** Schemathesis over GET `/api`; Hypothesis over one unit-tier flow. About 80 % of what people find is in the browser, on the device, or between two layers.
5. **Our own yield measurement was ignored.** The 08-23 note measured it: guards written from a plan's list — 0 defects in ~20 hours; hand-rolled scanners — 0; comparing literals against real data — 4 in 4 hours; an independent reviewer — 5; a real browser with a real gesture — 2 per ten-minute pass. Its conclusion: *every failed guard was written by the same author with the same mental model as the code.* We kept writing guards from lists; ana-log's `qa/ui-standard.yml` read 108 of 109 "implemented" while ACT-04 was live, because one test on one component satisfied the row.

So "better" is not another catalogue. It is four changes to how knowledge becomes enforcement: everything lands in this kit; the finder is independent of the author and works in a real browser; the QA system is itself measured (seeded-fault recall, escape rate) and investment follows measured yield; "implemented" means every surface, and "owed" has an owner and a date.

## 3. Techniques that target the shapes above, with the evidence

Ranked by the rows they would have caught. "Under-sold" notes what a generic survey says about each, which is how it was skipped last time.

| technique | shape | evidence | source |
|---|---|---|---|
| **Consumption census** — every served key read, every read key served | (d) | Azure HotOS'19: 21 % of high-severity cloud incidents are two parties disagreeing about a data format | https://people.cs.uchicago.edu/~shanlu/paper/hotos19_azure.pdf |
| **Stateful model-based testing** (QuickCheck state machines, Hypothesis `RuleBasedStateMachine`, fast-check commands) | (a) | Volvo/AUTOSAR: 200+ issues from 3,000 pages of spec at 5–8× less effort; Dropbox sync; ICSE 2024 practitioner study — strength is stateful code. Under-sold as "random inputs for pure functions". | https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quviq-testing.pdf · https://ieeexplore.ieee.org/document/7107466/ · https://dropbox.tech/infrastructure/-testing-our-new-sync-engine · https://dl.acm.org/doi/10.1145/3597503.3639581 · https://hypothesis.readthedocs.io/en/latest/stateful.html |
| **Quickstrom** — stateful PBT of the browser with temporal logic; found bugs in almost half of TodoMVC reference apps | (a) | PLDI 2022. Project is dormant (no release, last push 2024-08); mine it for the specification style. | https://arxiv.org/abs/2203.11532 |
| **Sequence covering arrays** (NIST) — every t-way ORDERING of N events in a tiny suite | (a) | failure reports involving event sequences were mostly "A before B", not adjacency. Almost never mentioned in surveys. | https://csrc.nist.gov/projects/automated-combinatorial-testing-for-software/combinatorial-methods-in-testing/event-sequence-testing · https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=906770 |
| **Combinatorial (t-way) coverage over state factors** | (a)(b)(g) | NIST interaction rule: 2-way covers ~93 %, 3-way ~98 %, nothing observed above 6-way. Pairwise is necessary, not sufficient. | https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=913805 · https://dl.acm.org/doi/10.1109/TSE.2004.24 · https://cse.unl.edu/~myra/papers/YuanCohenMemon.pdf |
| **Schema-derived API fuzzing** (Schemathesis) | (b)(d) | ICSE 2022, 8 tools × 16 services: only tool finding defects in 4 targets, 1.4–4.5× more unique defects | https://arxiv.org/abs/2112.10328 |
| **Random / monkey UI exploration with invariants after every step** | (a), absent controls | Android Monkey beat sophisticated tools on coverage (ASE 2015); Sapienz at Facebook: ~75 % of reported crashes fixed — because of the trace/video attached; Themis: 18 of 52 real bugs found by no tool, so exploration is a floor | https://arxiv.org/abs/1503.07217 · https://link.springer.com/chapter/10.1007/978-3-319-99241-9_1 · https://tingsu.github.io/files/fse21-themis.pdf |
| **Metamorphic testing** — relations where no oracle exists | (b) | filter∘sort = sort∘filter; list total = detail sum; print twice = identical | https://dl.acm.org/doi/10.1145/3143561 |
| **Differential testing** self-vs-self (two code paths that must agree) | (d) | McKeeman 1998 | https://www.cs.tufts.edu/comp/150FP/archive/bill-mckeeman/DifferentailTesting.pdf |
| **Mutation testing, diff-based** | vacuous guards | Google: 150k findings in review, usefulness 20 %→80 % with arid-line suppression; Just et al. — mutant detection correlates with real-fault detection | https://research.google.com/pubs/archive/46584.pdf · https://homes.cs.washington.edu/~rjust/publ/mutants_real_faults_fse_2014.pdf |
| **Exploratory heuristics** — Hendrickson cheat sheet, Bach SFDIPOT, Whittaker tours | (b)(c)(h) | Platform and Time are the guidewords that ask about the printer before the customer does | https://www.ministryoftesting.com/articles/test-heuristics-cheat-sheet · https://www.satisfice.com/download/heuristic-test-strategy-model |
| **ODC triggers** — classify escapes by what EXPOSED them, not by feature | all | the histogram tells you which verification activity is missing | https://dl.acm.org/doi/10.1109/32.177364 · https://www.chillarege.com/content/why-are-odc-triggers-fundamental-software-test-measurement |
| **Fault seeding** — measure a suite's recall against known defects | the QA system itself | classic; nothing in the estate has ever had it | Just et al. above; Yuan OSDI'14 (77 % of production failures reproducible by a unit test, ≤3 input events) https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-yuan.pdf |
| **Canarying / real devices** | (c) | the physical class has no literature; SRE Workbook ch.16 is the honest control | https://sre.google/workbook/canarying-releases/ |

## 4. Requirement catalogues to adopt as DATA, per quality dimension

ISO/IEC 25010:2023 (9 characteristics, 41 sub-characteristics; free mirror https://quality.arc42.org/standards/iso-25010) is the completeness frame: map C1–C12 onto it and the empty cells are the backlog. Per dimension, the one catalogue worth adopting:

| dimension | adopt | size | why this one |
|---|---|---|---|
| security | **OWASP ASVS 5.0, Level 2** — https://github.com/OWASP/ASVS | 345 total; L1 70 + L2 183 = 253 (secondary-sourced) | free, machine-readable JSON/CSV, every line "Verify that…"; start V6 auth, V8 authz, V3 session. Companions: WSTG for procedure, API Top 10 (API1/3/5 are the three tenant shapes), CWE Top 25 for weighting |
| UI / accessibility | **WCAG 2.2 A+AA** — https://www.w3.org/TR/WCAG22/ + ARIA APG behaviour tables https://www.w3.org/WAI/ARIA/apg/ | 56 criteria; APG ~27–30 patterns | pass/fail-phrased; 2.5.8 target size 24 px, 2.4.11 focus not obscured. GDS measured automated tools at ~30 % of issues — axe is a floor |
| inputs | **Big List of Naughty Strings** — https://github.com/minimaxir/big-list-of-naughty-strings | ~500 | executable as parametrised input; the RTL-override/bidi subset is our exposure |
| RTL | W3C i18n checker + bidi authoring techniques — https://validator.w3.org/i18n-checker/ · https://www.w3.org/TR/i18n-html-tech-bidi/ | — | logical CSS properties, `bdi` around mixed-direction values |
| performance | SRE Workbook SLOs (one availability + one latency per app) + Core Web Vitals (LCP 2.5 s, INP 200 ms, CLS 0.1) + k6's six load shapes | 2 + 3 + 6 | numbers that stay true for a one-engineer shop |
| database | **squawk** migration rules (https://squawkhq.com) + `pg_stat_statements` p95 diff | ~25–30 rules | strong_migrations' list for raw SQL |
| operability | Susan Fowler's production-readiness 8 standards (checklist mirrored free) + 12-factor + OpenTelemetry semconv | ~60–80 items | the only itemised yes/no list; Google's PRR checklist is not public |
| billing | no public catalogue exists. Ledger invariants under Hypothesis (debits = credits; append-only; balance = replay; integer minor units) + GitHub Scientist-style dual run | 6–7 invariants | https://martinfowler.com/apsupp/accounting.pdf · https://github.com/github/scientist |
| labels | **GS1 General Specifications** rows for our symbology (quiet zone, X-dimension, height) + print-and-scan on the real printer | ~10 rows | ISO 15415/15416 grading needs a verifier we will not buy |
| requirements | **Example Mapping** — https://cucumber.io/blog/bdd/example-mapping-introduction/ | a 25-minute session | rules, examples and red question cards BEFORE the build; the only public practice that answers "is what they asked what we test" |

Each catalogue enters through the requirement × surface rule (§6): a row is implemented on ALL surfaces it applies to, or it is partial with an owner and a date.

## 5. Tools — verified alive 2026-09-19, adopt before build

| need | adopt | verdict |
|---|---|---|
| API fuzz + schema conformance, incl. writes against the sandbox | Schemathesis 4.27 (in-process ASGI) | ADOPT — highest yield per hour |
| undefined template variables | Jinja `StrictUndefined` | ADOPT, 15 min per app |
| accessibility incl. tap targets | `@axe-core/playwright`, WCAG 2.2 rules + `target-size` | ADOPT |
| a second engine | Playwright WebKit — ships aarch64 builds for Ubuntu 22.04+/Debian 12+ (the branded `chrome` channel is what fails on ARM64) | ADOPT. Caveats: `BarcodeDetector` is Chromium-only (Safari has none), fake-camera flags are Chromium-only, pinch-zoom and popup heuristics differ from real iOS |
| real iOS | BrowserStack / TestMu real-device Playwright, one nightly job | ADOPT, manual-trigger, before any warehouse rollout |
| label round trip | zxing-cpp 3.1 + pyzbar (better multi-code recall) + pypdf + pdfplumber | WRAP |
| sequence engine with shrinking | Hypothesis `RuleBasedStateMachine` driving playwright-python | ADOPT as the spine; gremlins.js (dormant but one dependency-free file) as the cheap chaos lane |
| covering arrays | covertable 3.2 (pure Python) or Microsoft PICT | ADOPT. Sequence covering arrays: no Python library — ~60 lines from the NIST paper, BUILD |
| exploration → regression spec | Playwright Test Agents (first-party, GA 1.60) | ADOPT |
| row factories | polyfactory 3.3 | ADOPT |
| SAST / deps / secrets | semgrep, bandit, pip-audit, osv-scanner, trivy, gitleaks, trufflehog | ADOPT |
| DAST | OWASP ZAP baseline + API scan (last release 2025-12 — watch), nuclei | ADOPT nightly |
| mutation | mutmut 3.8 (diff-scoped), Stryker for the SPA | ADOPT on money modules |
| coverage that matters | coverage.py branch + diff-cover on the PR; monocart + Playwright V8 coverage for "client code e2e never ran" (Chromium only) | ADOPT |
| templates / RTL / links | djLint, stylelint logical-properties, html-validate, eslint-plugin-jsx-a11y, lychee | ADOPT |
| heartbeats / synthetics | healthchecks.io; Checkly (Playwright-native; free hobby tier) or Uptime Kuma self-hosted | ADOPT |
| tenancy at the database | pgTAP | ADOPT where RLS exists |

Rejected — dead, archived or wrong fit, so nobody re-researches them: Optic (archived), Dredd (archived), ts-prune (→ knip), Crawljax (2023), Quickstrom (dormant), ReDeCheck / viser / Galen (dead), Lost Pixel (sunset 2026-04), `nplusone` (2018), `todo-or-die` (2021), Pact (needs a programmatic consumer; five of six apps are Jinja), ISO 29119 (paid process standard), NIST ACTS (Java, email-gated; PICT/covertable instead).

Genuinely no off-the-shelf answer — build these and only these: payload read-coverage via JS `Proxy` (SPA) and a recording-`Undefined` context census (Jinja); text clipping / 0-px control / sibling-overlap / vertical-budget layout probe; t-way sequence covering generator; expiring-decision linter; SQLAlchemy/psycopg query-budget fixture; deploy-SHA / migration-head / freshness / "a person can sign in" probe that VOTES; ISO 15416-style print grading (decode-at-DPI as the proxy).

## 6. The four rules this kit enforces from here

1. **One home.** Instruments, stages, wrappers and QA dev-dependency pins live in `qabench/`; a QA dependency pinned in a project and absent from the kit is a conformance finding.
2. **Independent finder.** A nightly exploration by an actor that did not write the code, in a real browser, as a non-privileged persona, briefed with the requester's words and the heuristic packs — never with the author's tests.
3. **The QA system is measured.** `benchmarks/escaped.yml` is the seeded-fault benchmark; recall per shape is recorded weekly; the escape rate and the ODC trigger histogram are computed estate-wide by `qabench escapes`; an instrument with no finds and no seeded catches in six weeks is removed.
4. **Requirement × surface; owed rows expire.** A row is implemented when its evidence prints `walked N of M` from a universe enumerator; every partial, ratchet baseline and recorded decision carries an owner and a review date, and the kit fails past it.

## 7. Meir's UI standard (109 ids) against its sources — and the lines it does not cover

The `ui-standard` skill is the estate's UI catalogue: 109 numbered requirements in 13 families, adopted by every project through `qa/ui-standard.yml`. It is well-formed — each row is a testable assertion — and it is mostly a re-statement of public sources, which matters for two reasons: the source gives the row an authority Meir's name alone does not, and the source's NEIGHBOURING lines are the ones he left out. Family by family:

| family | rows | where the rows come from | rows with no public source (Meir's own, product rules) |
|---|---|---|---|
| GEN | 5 | Nielsen heuristics 1 (visibility), 3 (undo), 4 (consistency), 5 (error prevention), 9 (recover from errors); GEN-05 is Hendrickson's *Interruptions* | — |
| NAV | 9 | Hendrickson web tests (back button, bookmarkable URL, reload); GOV.UK breadcrumb and back-link patterns; Nielsen 6 (recognition) | NAV-04 state preservation on return, NAV-09 no new tab — product rules |
| FRM | 13 | WCAG 3.3.1/3.3.2/3.3.3 (errors, labels, suggestions), 2.4.3 (focus order); ARIA APG combobox and dialog focus; GOV.UK form, error-summary and date patterns; MDN `inputmode`; Material text-field states (disabled vs removed) | FRM-13 dependent fields — Hendrickson *Variable analysis* |
| ACT | 11 | ACT-04 double submit — CWE-799/837, Hendrickson *twice*; ACT-07 dirty-form warning — GOV.UK; ACT-08 — WCAG 3.3.4 error prevention, Nielsen 5; ACT-10 verb round-trip — Nielsen 2 (match the real world) | ACT-01/02/03/06/09/11 — product rules on where a save lands and how it is confirmed |
| MSG | 7 | WCAG 3.3.1/3.3.3; MSG-06 — WCAG 2.2.1 timing adjustable; MSG-05 incident id — SRE incident practice; MSG-03 language — Nielsen 2 | MSG-02 one hierarchy, MSG-07 one toast |
| LST | 9 | Baymard list/filter guidelines (paid; free articles), GOV.UK filter and pagination patterns; LST-08 sticky headers | LST-06 export = filtered rows and displayed columns |
| SCN | 11 | no public standard exists for camera scanning in a web app; nearest are Zebra/GS1 handheld-scanner behaviour (aimed, one read, beep) and MDN `getUserMedia` failure modes (SCN-08) | all 11 are Meir's — and SCN-01 was the row the field contradicted (a phone camera is not aimed; AL-025) |
| PRT | 11 | PRT-04 — GS1 GenSpecs and ISO/IEC 15416 (print-and-scan is the honest proxy); PRT-05 — CSS `break-inside: avoid`; PRT-10 — W3C bidi techniques; PRT-02 — `@media print` practice | PRT-03 pre-configured label geometry, PRT-06 page furniture, PRT-09 duplicate marking |
| STA | 7 | STA-01 — RAIL / Nielsen 1 (100 ms perceived, 300 ms indicator); STA-02 empty states — GOV.UK; STA-03 — GOV.UK error pages; STA-07 — Nielsen 9 | STA-04 offline retry, STA-06 partial failure isolation |
| MOB | 8 | MOB-01 — Apple HIG 44 pt (WCAG 2.5.8 says 24 px, Material 48 dp); MOB-02 — Hoober's thumb-zone study; MOB-04 — WCAG 1.4.3/1.4.6 contrast; MOB-06/07 — WCAG 1.3.4 orientation, 1.4.10 reflow; MOB-08 — Hendrickson *Interruptions* | MOB-05 wake lock |
| SEC | 6 | ASVS V8 (authorization: SEC-01/02), V3 (session: SEC-03/06), V6 (auth: SEC-04 — OWASP authentication cheat sheet's generic-message rule) | SEC-05 name and role on every screen |
| PRF | 6 | Core Web Vitals (LCP 2.5 s) and RAIL; the numbers are Meir's, the shape (target + ceiling + indicator) is the SRE SLO pattern | — |
| ACC | 6 | WCAG 2.2 AA and IS 5568 (ACC-01), 1.4.3 (ACC-03), 2.1.1 + 2.4.7 (ACC-04), 1.4.1 (ACC-05), 1.4.4 (ACC-06); W3C bidi (ACC-02) | — |

So roughly 70 of 109 rows restate WCAG, Nielsen, Hendrickson, GOV.UK, ASVS or HIG; the rest are product decisions, most of them about where a save lands and how scanning behaves. Two consequences. First, the standard's authority should be cited on the row (a `source:` column in the skill) so a project marking a row N/A knows what it is waiving. Second, and the point of this section: the standard is a UI BEHAVIOUR catalogue, and 75 of the 120 escaped rows are not UI behaviour at all. Held against the 120 and against the heuristic sheets it draws from, these are the lines it does not cover:

| heuristic line (source) | shape it finds | escaped rows it would have owned | where it belongs |
|---|---|---|---|
| **every served key is read; every read key is served** (Azure data-format class; McKeeman differential) | d | AL-001, 009, 018, 021, 026, 032, 038, 047, 062, 068, 072, 073, 099, 102 | C2 contract line + the consumption census; not a UI-* row |
| **every declared enum value has a renderer case** (`displayType`, field `type`, `style`) | d | AL-005, 021, 044, 062, 072 | C2 |
| **every affordance the API has, the UI offers** (filters, actions, targets) | d, absent control | AL-030, 040, 057, 059, 067, 068, 100, 104 | C10 — the only near-miss is LST-01, which names filters and nothing else |
| **no two controls fire the identical request; no verb offered twice** (Nielsen 4 taken one step further) | duplicate affordance | AL-007, AL-060 | C10 |
| **a screen that can add can remove; every route is reachable from a control** (GEN-04 says undo, not remove) | absent control | AL-111, AL-040, AL-030 | C10 |
| **zero / one / many on every child relation; the empty state of a role with nothing** (Hendrickson *Data*) | b | AL-050, AL-023, AL-114 | C4/C5 shape manufacturing |
| **Goldilocks — the longest REAL value, not `'א' * n`; a fixture with every field filled** (Hendrickson; C5) | b | AL-010, AL-011, AL-112 | C5 |
| **the input refuses the impossible — more than ordered, another tenant's product, a negative** (Hendrickson *Boundaries*; ASVS V7) | edge input, g | AL-058, AL-022, AL-110 | C4 — FRM-* covers how an error reads, never WHAT is refused |
| **choose-then-type, sort-then-page, filter-then-select — do A then B** (NIST sequence covering; Hendrickson *Sequences*) | a | AL-033, AL-046, AL-088, AL-098 | C10 sequence engine; ACT-04 is the only "twice" row and covers one control |
| **a second engine and a real device** (SFDIPOT *Platform*) | c | AL-002, 053, 061 | C12 — WebKit beside Chromium; a real iPhone before rollout |
| **the printer's paper, size AND orientation; the scanner's symbology; the camera's field of view** (SFDIPOT *Platform*, asked of a PERSON) | c | AL-006, 014, 015, 016, 025, 108 | `qa/physical.yml` — PRT-03/04 assert the outcome and never ask the question |
| **a rendered width, a clipped word, a 0-px control, the vertical budget for records** (WCAG 1.4.10 reflow, taken to a measurement) | c | AL-037, 041, 048, 051, 054, 092, 105 | C10 layout probe — MOB-* asks for readability, nothing measures it |
| **a deploy under an open tab; a stale mirror; a closed door with a green light** (SFDIPOT *Time*, *Operations*) | e | AL-085, 090, 091, 093, 094, 120 | C7/C8 made to vote — out of a UI standard's scope, and rightly |
| **the role that may not — as data, not as controls** (ASVS V8, API1/API3) | g | AL-086, AL-022, AL-055, AL-114 | C10 role × surface as a DIFFERENTIAL on rows; SEC-01 is about controls |
| **a recorded decision expires; an assumption is a question** (ODC *Design Conformance*) | stale decision | AL-017, 065, 069, 103, 113 | C3 with `review_by` |
| **what a document must SAY, from their spec** (specification by example) | unread spec | AL-045, AL-031 | C5 — PRT-* covers format and never content |
| **the copy is in the product's language, plural agrees, the sentence is conditional on the state** (MSG-03 covers the first only) | copy | AL-042, 043, 074 | C1 copy sweep, both languages |

The standard stays Meir's and stays a UI standard. The lines above are not new UI-* rows; they are contract lines under C2, C4, C5, C7, C10, C12 and the heuristic packs the nightly explorer is briefed with — which is where every one of the 75 non-UI escapes belongs.

## 8. Why the research itself fell short — and the protocol research follows from now on

Sections 1–7 say what failed in the SUITE. This section asks why two rounds of research into the suite (anat 2026-09-10, this one 2026-09-19) did not find it first. Every point below is true of the 2026-09-19 round as well — it is written against ourselves.

| # | what the research did | why that could not find our gaps | what replaces it |
|---|---|---|---|
| 1 | **Started from catalogues** (CWE, ODC, ISO 25010, WCAG) and mapped them onto our twelve checks | A catalogue lists what fails in EVERYONE's software. Our largest class — a descriptor key served and never read, 25 % — exists because of how THIS system is built (a descriptor-driven rebuild of a system we cannot see). No catalogue contains it; the mapping ended "covered" for every class it named and silent about the one it did not. | **Hazard analysis from our own architecture first** (STPA / FMEA over the seams: descriptor → API → client → device → paper → person). Every seam is asked "how can the two sides disagree, and what would notice?" Catalogues second, to fill in. |
| 2 | **Claimed coverage by mapping**: "CWE-799 double submit ↔ C10" | A mapping is a sentence, not a test. Nobody replayed a real escaped defect against the check it was mapped to; ACT-04 read "implemented" while a double tap was two POSTs. | **Falsifiable predictions.** Before any instrument is built, write down which benchmark rows it will catch; then revert each fix and run it. The prediction and the result are both recorded; a miss is a finding about the research. |
| 3 | **The evidence was written by the authors.** The ledger's "why it did not fire" is the explanation of the session that wrote the code and the fix; the 2026-09-19 shape classification was one agent reading that ledger | A self-diagnosis inherits the blind spot that produced the defect (the 08-23 finding, applied to research). Nothing measured whether a second classifier would agree. | **Blind double-coding.** Two classifiers that did not write the code code the same rows without seeing each other's answers; agreement is reported; disagreements are the interesting rows. |
| 4 | **The research question was framed by a hypothesis** — "find techniques for sequences and rare data" | Researchers asked about a class find techniques for that class and return it confirmed. The device class got "no literature" and was nearly dropped, though it is 15 % of what people found. | **Ask the open question first** — "what finds what people find here?" — and only then the per-class questions. |
| 5 | **Researched the literature, not the work** | The printer's paper orientation, the neighbouring QR codes on a sheet, the call that interrupts picking — these were in the warehouse, not on the web. The richest source (Israel's day, Shahar's method) was consulted only after the defect. | **Field observation before the build**: watch one real session of the work the surface serves (on the device, with the paper), and ask the SFDIPOT Platform questions of the person, recorded in `qa/physical.yml`. |
| 6 | **Researcher and builder were the same kind of actor** — the same model family designed the checks, wrote the code and reviewed both | Correlated blind spots: every layer agreed with every other by construction. | **An outside reader of the method**: a human tester (Shahar) or a different model reviews this document against the benchmark, briefed with the rows, not with our conclusions. |
| 7 | **Research ended at a document** | No prediction, no date, no measure — so nothing could show that it had failed until customers did. anat's escape rate was computed and nobody set a target it had to hit. | **Every research round closes with a dated, measurable claim**: "after these instruments, the 30-day escape rate falls from X to under Y by DATE, and recall on the benchmark rises from A to B." `qabench escapes` measures it; a missed claim reopens the research. |
| 8 | **Our own measurement was not the starting point** — the 08-23 yield table said lists find nothing and independent eyes find most | Research added more lists. | **Start every round from the last round's measured yield**, per instrument, before reading anything new. |

The first round of this protocol is run against the 2026-09-19 work itself: an independent blind re-coding of `benchmarks/escaped.yml`, pre-registered catch predictions per instrument, and a seam hazard analysis of one project's architecture. If those disagree with sections 1–7, sections 1–7 are what changes.

## 9. First run of the protocol — the blind re-coding (2026-09-19)

An independent classifier that had not seen sections 1–7, the benchmark's labels or the ledger coded all 121 rows from the FIX COMMITS (code hunks, comments stripped), recording mechanism, ODC trigger, seam, and the cheapest pre-release catcher. Two of its rows touched a ledger excerpt through a diff and are not fully blind. Its table is kept beside the benchmark; the comparison, measured:

**The trigger labels agree 55 % of the time (Cohen's κ 0.48 — moderate).** 16 of the disagreements are rows the blind coder marked high-confidence. So an ODC trigger histogram coded by one person is not yet a reliable instrument: two careful coders put a third of the rows in different buckets, mostly along Design Conformance ↔ Coverage ↔ Interaction ↔ Variation. Consequence: the trigger stays a ledger column, but a codebook with decision rules is owed before its histogram steers investment, and the CATCHER — which the coders were not asked to agree on and which is what decides what to build — is the more actionable field.

**What the independent coding changed in sections 1–7:**

| blind coder's cheapest catcher | rows | what section 1–7 said | correction |
|---|---|---|---|
| A — static census, declared vs consumed | **32** | "two correct halves" 25 % | confirmed and larger: ten of the rows the first coding called *other* are this class. It is the first instrument to build. |
| J — ask or observe the user before building | **18** | spread across *other*, *UX request* and the physical register | **under-weighted.** `requirement→build` is the second-largest seam (19 rows). The first coding had one sentence (Example Mapping) for it. |
| I — an environment probe that votes | 13 | 11 % environment | confirmed |
| G — data-shape generation | 13 | "rare data" 5 % | **under-weighted**: six of the first coding's *other* rows are fixtures that never held the state |
| B — a browser journey asserting the end state | 9 | — | confirmed as C10's job |
| E — layout measurement | 8 | part of "device" | confirmed |
| F — print → rasterise → decode on the real paper | 7 | part of "device" | confirmed; the blind coder notes F only works once the paper and its orientation are KNOWN, which is J |
| D — second engine / real phone | 6 | part of "device" | confirmed |
| C — a generated sequence / second-action test | **5** | 7.5 % and a proposed "sequence engine" | **over-weighted.** Hypothesis-driven Playwright sequences would catch five rows; they move from the build list to the adopt-later list |
| K — an independent exploratory tester | 5 | the explorer | smaller as a unique catcher than argued — though an explorer also performs B, D, E and J-style questioning |
| H — role/tenant differential | 3 | 5 % permission | confirmed |
| L — only the person could know | 2 | ~11 % "stays human" | **the honest ceiling is lower than claimed**: 2 rows, not 13 |

Patterns the independent coder named that no generic catalogue names, now part of this method: a **loader that silently drops declared shapes it does not recognise** (~25 rows — the census's precise target); a value **served and never rendered**; a **physical media chain that converges one fix at a time** (symbology → paper size → driver scaling → orientation → neighbours in the camera's view → labels already on pallets); a **fix that reaches one of N callers**; an **environment correct but stale or of the wrong identity** with every health check green; **rules inferred from data overruled by the owner's knowledge**; **prose promises drifting from code**; **preview-by-default leaking into controls**; and **testability defects** — a QA principal that cannot reach the branch under test, a fake camera that cannot show the property.

**Order of work, re-ranked by this measurement, not by the first plan:** (1) the consumption census; (2) requirement capture — Example Mapping plus `qa/physical.yml` plus "ask the owner before inferring a rule from data", with the question list in the kit; (3) environment probes that vote; (4) data-shape generation; (5) layout probe and print round-trip; (6) the explorer, run as the carrier of B/D/E/J questions rather than as a separate catcher; (7) sequence generation last.

## 10. Second run — a blind seam hazard analysis, graded against a project it had never seen (2026-09-19)

The claim tested: *a hazard analysis built from a system's own architecture predicts what its users report better than industry catalogues do.* An agent read 8200-platform's code (not its ledger, not its git messages) for twelve minutes, covering about a third of 43k lines, and wrote a seam/FMEA hazard list. Then it graded the list against the 31 defects people found there (Ran 10, Rami 2, Gili 21 — two feature requests excluded), with ISO 25010 + WCAG 2.2 + ASVS L2 + Hendrickson's cheat sheet as the control.

| method | predicted (exact + same seam) | missed |
|---|---|---|
| seam hazard analysis | **13 of 31** (4 exact, 9 same seam) | 18 |
| generic catalogues | **5 of 31** (16 more only "arguably" — a heading too broad to aim a check) | 10 flatly |
| either | **16 of 31** | 5 neither |

So the claim holds in a narrow form — **2.6× the catalogue** — and is not enough on its own. What the misses teach, and what changes:

* **14 of the seam method's 18 misses are human-factors defects**: a capability with no way in, visual hierarchy, a double confirmation, a label in words that are not the requester's. FMEA guidewords applied to data seams do not produce "she could not find it" or "those are not her words". This is the same class the blind re-coding called J (§9) — twice now, from two independent directions, the largest thing no automated method reaches is **the requester's words and the requester's task**. The catcher named by both: compare the screen's words and paths against the requester's own words (Tier 4's audit, made per surface), and put a persona-driven explorer in front of every new surface.
* **13 of the 31 came from one tester's round on two NEW modules** that the analysis never read. Defects cluster on new surfaces, which is exactly where a one-off architecture analysis is stalest. Rule: the seam hazard pass is run **per new surface as it lands**, as part of that change — not once per project.
* **The seam method's unique hits are the ones no catalogue can name**: a dedupe branch that drops a returning lead's message; production three migrations behind the code; links built from a domain staging cannot serve. Every one read "no" or "arguably" against the catalogues.
* **It also named five hazards with no ledger row** — outbound messages off by default; UTC `created_at` shown as local time; a proxy collapsing every visitor into one rate-limit bucket; retried WhatsApp webhooks producing duplicate replies; a customer cancelling an appointment already past. Each is either a latent defect or a false positive, and checking them is the test of the method's precision. They are handed to 8200-platform as questions, not fixed here.

Limits, stated: n = 31 on one project; the analyst graded its own list (a second grader would move 2–4 rows); code comments at HEAD describe fixed defects, so "blind" was partly sighted.

**Net method, after two falsification runs:** architecture seam analysis per new surface (the structural third) + a declared-vs-consumed census (the largest automatable class) + the requester's words and task, checked before and after the build by someone other than the author (the largest class nothing automated reaches) + catalogues as the floor under all three. Each claim here carries its measured hit rate; the next round starts from these numbers.
