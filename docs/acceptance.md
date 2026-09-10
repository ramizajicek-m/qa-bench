# Qualification update — 10 September 2026

The hold is lifted. All 86 new protocol tests and 60 existing release/report tests passed. Focused real browser/PostgreSQL reports now exist for Anat and my8200, including intended-assertion failures after restoring omitted behavior and restored healthy reruns. Their draft contracts record observed normalized IDs separately from executable `tests` mappings: partial local success cannot satisfy the broader scenario or protected candidate lane. No signing controller, universal resource broker, CI activation, or measured reduction in escaped errors is established by these runs.

Evidence and remaining work are recorded in `/Users/ramizajicek/Documents/testing-coverage-audit-2026-09-09/IMPLEMENTATION.md` and `qualification-2026-09-10/`. The statements below preserve the previous source-only phase.

---

# Local acceptance implementation — 9 September 2026

Status: source draft, independently reviewed in bounded rounds; **no tests executed in this implementation phase**. Nothing here is activated in CI, a manifest, an automation or a deployment. Existing nightly/staging processes are outside this change.

## What is implemented

Subsequent local increment: [shared resource admission](resource-admission.md) adds an inactive host-lease library and source tests. It separates memory admission from Anat's account lock and documents the remaining host/Docker broker and early-entry-point integration. It has not acquired a real lease or executed a test.

| Module | Local behavior | Remaining qualification |
|---|---|---|
| `qabench.acceptance` | Reads a protected-contract digest and authenticated healthy/negative-control evidence, requiring exact candidate, evaluator, session, environment and testcase identities. Distinguishes product failure, surviving mutation and unavailable evidence. | Real project reports, healthy/broken execution, independently provisioned controller and signing boundary. |
| `qabench.junit_evidence` | Parses existing UTF-8 JUnit, validates identity/counts, refuses empty/duplicate/unsupported evidence; retains separately recorded process exit. | Captured reports from each project's actual runner/version. |
| `qabench.pytest_evidence` | Explicitly opt-in plugin records assertion type because pytest JUnit normally omits it. Never auto-loaded. | Real assertion/setup/teardown/interruption qualification with the protected evaluator. |
| `qabench.delivery` | Reads local Git worktrees without fetch, hooks, fsmonitor or locks; compares explicit ready owner/candidate/time against local integration. Two-hour overdue and four-hour escalation thresholds. | Remote integration/deployment observation, independent scheduling/notification, and qualification of the Git reader on actual worktrees. |
| `qabench.outcomes` | Compares completed observation windows, user/staff escapes, severity and exposure; separates reopened episodes from duplicate reports and internal/harness findings. | Complete incident/release source inventory and comparable baseline/follow-up. |

The six files under `contracts/` contain 29 scenario families: 17 historical families plus a fresh business-journey population and delivery obligation for every project. The root-cause and sibling population are part of each contract. **Every executable `tests` mapping is deliberately empty until exact normalized report IDs have been observed.** Candidate test filenames are navigation aids, not coverage. The validator returns unavailable for these draft contracts. They must never be treated as a production gate already passed.

The source audit covers 8 September 18:25 through 9 September 18:25 Israel: 109 worktrees, 28 additional non-merge commits outside integration branches, plus the initial 246 integration-branch commits. These are inventory counts, not unique bugs. Original requirements and the frozen audit are retained at `/Users/ramizajicek/Documents/testing-coverage-audit-2026-09-09/` in `TEST-DESIGN.md`, `BUG-PREVENTION.md` and the project supplements. Those documents, not an inferred implementation rule, govern the proposed outcomes.


The JUnit reader normalized actual project reports without altering them. Picking controls exposed a metadata gap: pytest.raises uses Failed, which the first plugin excluded; allowing every Failed then admitted pytest-timeout. The corrected opt-in plugin checks the originating frame for Failed and leaves unknown plugin/helper origins unqualified. Ten actual child-pytest outcomes explicitly load pytest-timeout 2.4.0; both errors were reproduced red and the corrected related files pass 50 cases. Actual ana-log picking reports using the plugin normalize six intended assertion failures plus three passing controls, then nine restored passes. This is recognized outcome metadata, not independent attestation or proof against every timeout mechanism.

## Evidence protocol and trust boundary

A version-1 contract identifies project, repository, original requirement source, and scenarios with C1–C12 checks, root cause, independently discovered sibling population, expected outcome and exact testcase IDs. Pin its canonical SHA-256 **outside the candidate's control**. Updating the implementation cannot silently shrink the approved requirement.

An envelope is `{"payload": {...}, "hmac_sha256": "..."}`. The signature is HMAC-SHA256 over canonical UTF-8 JSON (sorted keys, compact separators, no nonfinite numbers). The payload identifies full candidate/evaluator commits, contract digest, controller session and environment, start/completion timestamps, and scenario results. Each result includes:

- Healthy and broken runs: independently recorded process exit, raw report SHA-256, unique `classname::name` cases with statuses.
- Mutation: original/changed source digests, patch digest, mechanism and the exact expected failing cases.
- Required cases must execute. Healthy must pass; broken must exit 1 with the intended assertion failures. A skipped case, timeout, setup failure, teardown problem or no-op edit cannot establish detection.

The protected controller must collect and validate raw reports, source/patch digests and exits itself, then sign outside the candidate process. A candidate-controlled XML property or digest string is only a claim. The HMAC validator authenticates what the controller attests; it does not independently inspect a checkout, prove the recorded test is adequate, or build the isolation boundary. No signing service or controller is implemented/deployed in this draft. Local synthetic envelopes in tests exercise protocol decisions only.

A qualified result always contains `production_authorized: false`. Production still needs the existing exact-candidate release gate, complete project contract coverage, merged-tree identity, protected deployment credentials and permitted promotion path. This module alone cannot approve an autonomous release.

The existing release gate distinguishes immutable unchanged-SHA push proof from fresh deployed proof. This draft adds neither a new workflow trigger nor a staging lock. Atomic protection against staging changing during a comprehensive sweep remains an integration requirement.

## Commands for later qualification

These are documented invocation forms, **not commands run during this phase**. From an installed/pinned kit, the module CLIs are:

```text
python -m qabench.acceptance --contract CONTRACT.json --evidence EVIDENCE.json --contract-digest DIGEST --candidate SHA --evaluator SHA --session SESSION --environment ENVIRONMENT
python -m qabench.delivery --repo OWNED_REPO --base LOCAL_INTEGRATION_REF --ledger READY.json
python -m qabench.outcomes --input OBSERVATIONS.json
```

Acceptance reads a minimum-32-byte key from `QA_ACCEPTANCE_ATTESTATION_KEY`; do not pass it in command arguments or expose it to candidate code. JUnit normalization is a library API: `read_report(path, exit_code=controller_recorded_exit)`. The opt-in pytest plugin is `-p qabench.pytest_evidence`; it must be loaded from a protected evaluator package when its observations matter. No package entrypoint auto-enables it.

Readiness input: `version: 1`, `items` containing absolute worktree path, owner, full candidate, and timezone-aware `ready_at`. Optional blocker does not reset the clock. Parking requires reason and expiry. Dirty work or a clean branch without a ready declaration is reported without being declared overdue. A changed head/dirty tree invalidates an earlier readiness declaration. Local ancestry never implies pushed, remotely merged, staged or deployed. Shallow history is unavailable. For safety the current reader conservatively refuses any configured clean/process filter, including a global Git LFS filter that may be unused; it explicitly reports that limitation rather than claiming a dirty/clean result.

Outcome input: version, observation timestamp, explicit project population, baseline/follow-up start/end, observed-project lists, release counts and incidents. Each incident has canonical defect ID, unique episode ID, new/reopened occurrence, project, source, severity, escaped boolean, source reference and report timestamp. Multiple reports of one episode must be deduplicated upstream. Both windows must end by the observation timestamp. Unknown sources/exposure are not zero defects. A measured zero baseline has an absolute rate change and undefined percentage. Rates per release are descriptive; activity mix, tenant/transaction exposure and statistical significance remain separate analysis. No error reduction has been measured.

## Local project changes accompanying this kit

Anat: real payment-plan edit/save/reload for v1/v2 and phone/desktop, preserving milestones and advisory behavior; company-only/named-person supplier create/reopen/edit against actual storage, including the separate channel PUT and primary-channel readback. These complement earlier local approval, costing and discount work. The drift journey currently proves save is allowed, not send delivery.

ana-log: actual surcharge/pallet/package Add/save/reopen/cancel and exact-parent checks; QR pixels through jsQR and the real action with owned-write guards; picking close/send against empty/zero/partial contents, stale caches and another order's goods. The flow fixture now manufactures its zone/destination/shelf on a fresh database instead of skipping when the extract lacks a warehouse. Synthetic video remains separate from physical camera/label qualification.

Tharros, my8200, IGA and Eliad: their contracts record the audited provider, session, backup and mutation-harness gaps. New complete product journeys for these four are **not implemented by this increment**. Earlier release-wiring drafts remain separate, unactivated work.

## Required next steps before activation

1. Source-to-job mapping: enumerate executable IDs and required lane membership on an owned disposable environment. Missing configuration/fixtures must be repaired rather than skipped.
2. Execute bounded healthy cases and historical plus held-out sibling negative controls after testing is permitted. Collect real JUnit and process outcomes. Verify cleanup even on failure.
3. Finish remaining scenario families, including provider/recipient boundaries, actual Postgres session writers, independent backup silence detection and physical artifact/device corpus.
4. Provision independent evaluator/collector credentials and protected contracts. Keep implementation and approval authority separated; generated tests need independent requirements/oracle review.
5. Integrate the measured candidate and release paths under the existing coordination mechanism. Configure the independent deadline observer and establish baseline data. Verify actual deployed services and promotion outcome.

This is a usable local implementation increment and explicit remaining-work inventory. It does not establish comprehensive coverage, CI activation, production approval or fewer customer errors.
