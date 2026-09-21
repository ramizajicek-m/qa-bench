r"""population — a guard's SUBJECT is the property's population, not the example's neighbourhood.

    python -m qabench population                 # the `population:` block of qa/manifest.yml
    python -m qabench population --json          # the rows, for a test to read
    python -m qabench population --repo DIR      # another checkout

WHY. On 2026-09-20 twelve defects were found behind green tests in anat and
ana-log. Eight are one shape, and it is not a missing insight — `contract.yml`
already requires every piece of evidence to "print the SIZE of the population
it examined". The size was printed. Nothing ever compared it to a population
derived INDEPENDENTLY of the guard, so a guard could sweep the neighbourhood of
the example it was written against and report that neighbourhood's size as
though it were the whole:

  ACT-11  the corpus of "routes that report a count" was keyed on the PATH
          containing "batch" or "bulk". Re-keyed on the AST property — a route
          that iterates a collection and returns a dict containing len()/sum()
          — it found 11 more routes and a second live defect.
  MSG-03  a ratchet on raw HTTP status codes in user-facing errors counted
          admin templates and api.js. The technician field app has its own
          fetch wrapper; the ratchet read zero on it and technicians on roofs
          read "Not saved: Not Found".
  FRM-01  the required-signature mark is styled by style.css. The markup sweep
          credited the rule to every template alike, including three standalone
          documents that never load it.
  FRM-04  a switch over eleven pydantic error types was tested against the
          eleven cases in the switch. Twelve more are reachable.
  FRM-10  a detector using `\\bcan_\\b` can never match `can_edit_field` — there
          is no word boundary between word characters. It reported ZERO gated
          fields, which reads exactly like a clean tree. The real number was
          ten, one of them a live defect.
  STA-02  "an empty screen explains why it is empty and offers the next
          action", swept over `class="empty-state"` plus every AnatEmpty call —
          and the class is what the CONVERSION added. A ratchet drove 75
          hand-rolled empty states to 38 to 0 by moving them onto the helper,
          each conversion adding the class, so the population is exactly THE SET
          OF THINGS ALREADY FIXED. The screen the coordinator found renders
          `<td colspan="7" style="text-align:center">` through the LIST helper,
          which has no action parameter at all, and was never in the ratchet to
          survive it. 75 → 38 → 0 is true and counts the conversion, not the
          surface.
  and the harness class: a guard that watched ONE global name (AnatList) while
          seven harnesses failed on another (AnatDate).

So every guard names two commands. `population` enumerates what the property
claims to hold over; `subject` prints what the guard actually examined. This
module runs both and compares them by MEMBER. A member of the population the
guard never examined is a hole with a name, not a percentage.

FOUR RULES, each paid for by one of the rows above:

  1. A POPULATION IS DERIVED, NEVER NAMED. `derived_from` is one of ast,
     route_table, schema, enumeration, filesystem — the ways to ask what a
     thing IS. `names`, `grep` and their kin are refused, because a naming
     heuristic is the defect (ACT-11, MSG-03). This is the meta-rule that
     stops a widened corpus being narrowed back later.
  2. ZERO IS RED. A subject of nothing against a population of something is a
     finding, never a pass: a detector matching nothing is indistinguishable
     from a clean tree (FRM-10). And its converse, which a live corpus of one
     forced into the open: a guard whose POPULATION may legitimately be empty
     declares a `capability:` command — a self-test on a permanent synthetic
     corpus, proving the detector still detects — and then an empty live scan
     is REPORTED rather than judged. Capability and corpus are two claims, and
     the only honest way to let a live scan find nothing is to prove the
     detector elsewhere. The capability runs on every invocation, not only when
     the corpus is empty, because a detector that quietly stopped detecting
     over a NON-empty corpus is FRM-10 itself.

     A CAPABILITY DECLARES BOTH HALVES, and both are REAL cases out of the
     tree, each naming where it comes from: `fires:`, at least one
     known-positive the detector must catch, and `silent:`, at least one
     near-miss it must not. POSITIVES-ONLY PROVES A DETECTOR FIRES, NEVER THAT
     IT DISCRIMINATES — FRM-04's switch tested against the cases in the switch
     — and an all-positives self-test over an EMPTY corpus is indistinguishable
     from a detector that fires on everything over a clean tree. So a
     capability missing either half is refused by name.

     THE KNOWN-POSITIVE MUST BE THE REAL INSTANCE, and this is the cheapest test
     nobody runs, because checking the case you were staring at when you wrote
     the detector feels absurd. It is not: the detector was written from a
     MEMORY of that instance, not from the instance. A verifier that followed
     23 dialogs' dismiss handlers reported 16 verified and 15 cleared, with the
     one independently confirmed bypass in the CLEARED list. Re-running found
     nothing; re-reading the code found nothing; checking the one case whose
     answer was already known found it in a minute.

     THE NEAR-MISS HAS TO COME OUT OF THE TREE FOR THE SAME REASON. A detector
     for "typing is never blocked mid-entry" reported four blocking handlers,
     all false: its regex knew `if (e.key === "Enter")` and missed the inverted
     `if (e.key !== "Enter") return`, which is how three of them are written. A
     near-miss drawn from real code catches that, because the inverted form is
     what the codebase actually uses; an invented one is written in the
     spelling its author already had in mind.

     AND THE DETECTOR MUST BE A NAMED, CALLABLE FUNCTION, OR THE SELF-TEST CAN
     ONLY BE A TAUTOLOGY. Inline logic offers no other move, so the only control
     expressible is a restatement of the arithmetic — a tautology with the shape
     of a measurement, which its author does not feel writing. An inline
     `if stuck > baseline:` had a control asserting `3 > 0`, `not (1 > 1)` and
     `2 - 1 == 1`: TRUE ON AN EMPTY REPOSITORY, green, beside a docstring
     correctly naming the degeneracy it failed to check. Extracting
     `_stuck_finding(stuck, baseline)` made the mutation `stuck > stuck` go red,
     which it could not before — and the same author wrote two more within the
     hour of naming the class, in guards written deliberately against it. The
     cure was ALREADY IN THE TREE TWICE, once under the best sentence of the
     night — TESTING THE DETECTOR MEANS RUNNING THE DETECTOR — and KEPT BEING
     REDISCOVERED BECAUSE IT LIVED IN A DOCSTRING RATHER THAN IN THE KIT. So
     `capability.detector:` names it as `path::function`, and a capability whose
     detector cannot be named that way is refused: extract first.
  3. THE GAP IS NAMED MEMBER BY MEMBER, so "credited to every template alike"
     is impossible to write (FRM-01).
  4. A RATCHET'S FALL PROVES NOTHING ABOUT A POPULATION THE RATCHET DEFINES.
     When the marker a population is keyed on is the one each fix adds, the
     count falls to zero by construction and says nothing about what was never
     in it. The question is always what CAN exhibit the property, never what
     carries the sign of having been handled.
  5. THE POPULATION COUNT IS PINNED AND THE PIN IS EXACT. It may rise in the
     commit that raises it; it may fall only behind `shrunk:` with a reason,
     evidence and a date. A corpus that quietly returns to a naming heuristic
     fails here.

THE REACH TABLE'S VALUE IS TELLING YOU WHICH ROWS DESERVE THE SUSPICION, not
which are broken, and that is the argument for running it routinely rather than
as an investigation. Reviewing FRM-07, knowing it rested on a helper whose close
path reaches 123 of 146 dialogs, the review became "check that specific hole"
instead of "read this file looking for nothing in particular" — and most of the
cost of a review is deciding what to look for. The answer was a NEGATIVE: Enter
is a document-level keydown scoped to `.modal-overlay.open`, so it reaches every
dialog however its close is wired, while the unsaved-changes prompt hangs off a
delegation that 23 bypass. Two mechanisms, one shared helper, one bounded and
one not. That result took minutes and is worth having on its own, because it
also proves ACT-07's defect was never in the save helper — which stops somebody
"fixing" a helper that is fine.

A COVERAGE MEASUREMENT MUST BE ABLE TO EXONERATE, and is not trustworthy until
it has. Triaging the 109 uncovered fetches above against STA-04 ("loss of
connectivity is announced") found it genuinely NOT implicated: progress.js wraps
window.fetch globally, so a DISCONNECT is announced on all 109, while a 500 on a
read is not. A triage that implicates everything it touches is not a triage —
`complement:` is the same mechanism used in the honest direction, and a run that
never clears anything is evidence about the run rather than about the code.

A TRANSFORM IS PART OF THE GUARD, AND A DESTROYED CORPUS REPORTS EXACTLY LIKE A
CLEAN ONE. A guard tripping on the COMMENT that explained a fix was made to
strip comments first — `<!--.*?-->|/\*.*?\*/|^[ \t]*//.*$` with DOTALL — and a
stray `/*` inside a script string found a distant partner, blanking 58 % of one
real file, 73 % of another and 76 % of a third. Two checks had ALREADY been
watched going green over that gutted corpus and recorded as mutations passed.
This is the false-green shape arriving from the direction nobody watches: not
the check, not the oracle, but the NORMALISATION STEP in between, which nobody
thinks of as part of the verdict. Anything that transforms a corpus before the
assertion owes the same proof as the assertion — declare `transform:` with the
size before and after and the shrink you INTENDED, and an unintended shrink is
red. One line, and it would have caught this instantly.

AND THE SELECTION EFFECT UNDERNEATH IT, which is the part worth carrying to
every project: real source has prose in it, and THE PROSE CLUSTERS EXACTLY WHERE
THE DEFECTS WERE, because that is where people stop to explain themselves. So a
text-matching guard is systematically MOST likely to be wrong at the very sites
it was written for. That is not bad luck, it is selection — prose density
correlates with defect history. Two failures in one file in one hour came from
it: the guard above, and a click-handler detector matching
`addEventListener('click', … [^{}]{0,200} … AnatDialog.close(` whose window was
pushed past 200 characters by the three-line comment explaining the fix, so
restoring the defect left the test GREEN and only the mutation found it.

The rule all three collapse into: THE CORPUS A GUARD ASSERTS OVER MUST BE THE
CORPUS A BROWSER OR RUNTIME ACTS ON, transformed as little as possible, with
every transform proving it did not shrink what it touched. Anchor to structure —
a tag, an AST node — rather than cleaning text to make a pattern work. When a
pattern needs the text cleaned to be correct, the pattern is wrong.

A RATCHET GOES GREEN OVER NOTHING IN TWO WAYS — THE WORK SUCCEEDING, OR THE SCAN
BREAKING — AND THEY NEED DIFFERENT DEFENCES. The work succeeding: a population
keyed on the shape of the old code empties as the fix lands, and the defence is
a bucket keyed on the PROPERTY, which moves the opposite way. The scan breaking:
a corpus that empties by accident, and the defence is a corpus FLOOR.

THE CASE THAT BITES IS NOT AN EMPTY CORPUS BUT A QUIETLY SHRUNKEN ONE. A real
migration caught a scan that fell FROM 350 FILES TO 5, which would have passed
any "at least one" floor and any non-vacuity check. That is why the pin in this
module is EXACT in both directions rather than a minimum: a minimum answers the
empty case and is blind to the case that actually happens.

(Where that defence is deliberately given up, `population.observed_from:` says
so — a population read out of an environment cannot pin its size, so a quiet
shrink there is invisible and the discrimination has to come from the
capability's constructed case instead. That is a trade, and it is the only place
in this module where a shrinking corpus is not a finding.)

A RATCHET HAS TWO POSSIBLE PURPOSES AND THEY HAVE OPPOSITE CORRECT ENDINGS, so
`for:` is declared. A ratchet measuring a PROPERTY the fix must preserve must
not be keyed on the shape of the old code, because it empties and goes green
while the property is unmeasured — that is the case below. A ratchet that is a
HOLDING ACTION against a known-broken mechanism SHOULD empty when the mechanism
is replaced, and its end state is DELETION: a ceiling of 119 unparseable
functions exists only to stop that number growing while the parser is known
wrong, and when a real parser lands the honest move is to delete the ceiling,
not to invent a property-keyed bucket beside it. LEAVING IT GREEN IS THE ERROR,
NOT THE EMPTYING. Both look identical in the file — a shrink-only count with a
ceiling — and only the declaration says which.

A COVERAGE RATCHET AND A PROPERTY RATCHET ARE DIFFERENT INSTRUMENTS AND A
PROJECT NEEDS BOTH. Measuring a migration is a real thing to measure; it is just
not the property, and the day a project confuses them is the day its guards go
green by being emptied. A RATCHET KEYED ON THE SHAPE OF THE OLD CODE EMPTIES AS
THE FIX LANDS, AND AN EMPTY RATCHET IS GREEN — the number falls as the codebase
improves and reads as progress the whole way down. So the question to ask of any
new ratchet is one line: WHAT DOES THIS COUNT WHEN THE WORK SUCCEEDS?

Three ceilings over 672 raw call sites — 55 with nothing at all, 145 checking
`.ok` and dying on a rejection — every number true, every ceiling shrink-only,
and all three emptying as the migration proceeds. THE REPAIR IS NOT A
REPLACEMENT: a FOURTH bucket keyed on the PROPERTY rather than the call shape —
helper sites that use the result without testing it, six today. The helper
reports failures by default, so the banner is there; what those sites add is a
screen that ALSO renders a fallback as fact beside it, an empty state asserting
"you have none" next to a banner saying the load failed. A CARELESS MIGRATION
LOWERS THE FIRST THREE AND RAISES THE FOURTH. No single ceiling can see that;
the four together can, which is why `paired_with:` is required on a reach guard.

And the mutation that demonstrates it is the model, because THE NON-MOVEMENT IS
THE DEMONSTRATION: a carelessly migrated call takes the fourth to 7 against a
ceiling of 6 AND THE RAW CEILINGS DO NOT MOVE. Asserting what must not move is
as much of the proof as asserting what must.

REACH IS A DENOMINATOR, AND A DENOMINATOR NEEDS ITS OWN COVERAGE MEASUREMENT.
For every blessed helper, how many call sites go through it? Mechanical,
countable, and nobody was asking. On anat: AnatFlash.toast 987 against one stray
alert(, AnatDate 136 against zero, AnatDialog.open 159 against 8, close 133
against 12, AnatEmpty 50 against 38, and apiFetch 198 against 783 raw fetches —
20 %.

That 20 % would have started a rewrite, and it is wrong. BYPASSING A HELPER IS
NOT THE SAME AS BEING UNCOVERED: anat has three other global fetch wrappers
which between them give every raw call the loading indicator, session activity,
the CSRF header and the 401 bounce; 538 check status themselves; 297 report a
failure to a person; 109 do NEITHER. One hundred and nine is the actionable
number and it is a much smaller, correct piece of work.

AND THEN THE BROWSER CORRECTED THAT MEASUREMENT TOO, which is why `complement:`
now demands a proof per layer. The 538 counted "checks res.ok" as handling
failure — but `res.ok` only exists if the promise RESOLVED. A network rejection
throws out of the Promise.all and the check never runs, so the screen keeps the
old rows and says nothing. THE POPULATION WAS RIGHT AND THE BUCKET BOUNDARY WAS
WRONG: a third class beside marker-keyed and surface-default, where the corpus
is complete, the arithmetic is sound, and a category line sits in the wrong
place so members are filed as covered while suffering the outcome. So a layer
carries `proven_by:` — a command showing the layer actually covers a real member
— for the same reason a capability carries `fires:`. A COVERAGE CLAIM IS A CLAIM
LIKE ANY OTHER.

The repair that follows is the headline from that browser run: THREE mechanisms
— a network rejection, a wrong-shaped 200, and a half-handled HTTP error —
converge on ONE user-visible outcome, the screen keeping old data and saying
nothing. On one list the main region was byte-identical before and after a
failed read, 931 characters both times, with the count still asserting "8
clients"; on another, twenty-three stale rows and a MutationObserver recording
zero nodes added. A guard is keyed on THE OUTCOME A PERSON SUFFERS, not on which
check a call site performs — three buckets cannot be got right when the thing
that matters is the same in all three.

So a guard may declare `kind: reach`, and then `complement:` is MANDATORY — the
layers that cover what bypasses the helper, applied in order, with the residue
named as the finding. A reach guard without it is refused the way a population
derived from naming is refused, because a denominator with no
coverage-by-other-means measurement is a verdict without a population, which is
this module's own subject arriving in its own instrument.

Two results from that table worth keeping. Four helpers at 100 % answer "20 % is
inevitable at this scale" — it is not, in the same codebase, at five times the
call volume. And AnatEmpty's 57 % was found COLD by the source audit, hours
after the same gap was found from a browser report on STA-02, with no knowledge
of the first: two independent routes to one finding is the closest thing to
validation this method gets, and it is worth more than any number in the table.

WHEN TO SPEND ON A BROWSER, which is the piece that turns the tier argument into
a decision. A source-read claim and a browser-driven claim COST ABOUT THE SAME
TO MAKE and differ by roughly an order of magnitude IN WHAT THEY COST TO REFUTE,
because the browser hands you the artefact that settles it. One night's tally:
ELEVEN source-read false positives, none cheaply killable, each costing an
inspection to dismiss — three of them `querySelector` strings INSIDE COMMENTS.
Against ONE browser-driven false positive, killed in a single step because the
probe printed the `outerHTML` showing the "unnamed required control" was a
framework's aria-hidden shadow input behind a properly labelled combobox.

SO THE RULE IS NOT "DRIVE A BROWSER WHEN THE PROPERTY IS VISUAL". IT IS: DRIVE A
BROWSER WHEN YOU EXPECT TO BE WRONG OFTEN, BECAUSE CHEAP REFUTATION IS WHAT YOU
ARE BUYING. And it carries its own limit, which is what stops it becoming a
mandate nobody can afford: source reading is fine where the base rate of false
positives is low — a grep for an import that either exists or does not. THE
EXPENSIVE CASE IS A WINDOW AROUND A PATTERN, because the window is a guess about
layout and layout is what varies.

DRIVING IS NOT STRICTER THAN DERIVING — measured on one file. Required controls
in one large template: a markup scan of the FILE says 20, the tree-wide guard
18, the DOM on a loaded page 16. Overlap about 10; MARKUP-ONLY 10; DOM-ONLY 3.
Deriving misses what the page HAS and the file does not contain (four
`{% include %}` directives; three of the sixteen observed appear zero times in
that file). Driving misses what the file HAS and this instance does not render
(ten of the twenty never reached the DOM, all conditional on client state the
sandbox client lacks). HALF THE DERIVED COUNT WAS NOT ON THE SCREEN AND A FIFTH
OF WHAT WAS ON THE SCREEN WAS NOT IN THE FILE. So: WORK FROM THE DERIVED LIST
BECAUSE IT IS THE COMPLETE ONE; VERIFY THROUGH A GESTURE BECAUSE THAT IS THE
ONLY THING THAT PROVES A FIX REACHES A PERSON. NEITHER IS EVIDENCE FOR THE
OTHER'S POPULATION, and A DRIVEN PAGE IS ONE INSTANCE OF A TEMPLATE. (One
conclusion drawn from that calibration — "a per-file count under-counts pages
built from partials" — was WITHDRAWN: the helper globs partials as files in
their own right, so a control is counted once, IN THE FILE A REPAIR WOULD
ACTUALLY EDIT. A count's unit is a choice about where the work lands: per-file
counts the repair, per-page counts the exposure.)

INDEPENDENCE OF METHOD IS NOT INDEPENDENCE OF ERROR. A source scan said 8 of 23
surfaces lack a sort control; a browser drive of a surface NOT among the 8
agreed, and the agreement was reported as proof the scan under-counted. Both
were wrong: the drive queried `thead th` ACROSS THE WHOLE PAGE and judged 20
headers from THREE tables — the real list has 15, 11 sortable, and THE ELEMENT
UNDER TEST WAS NEVER LOCATED — while the scan could not see sort at all because
it is applied AT RUNTIME by a shared helper. Different mechanisms, same error,
from one unstated shared assumption: THAT THE PAGE CONTAINS ONE LIST. SO WHEN
TWO METHODS AGREE, THE QUESTION IS NOT "WERE THEY INDEPENDENT?" BUT "COULD THEY
FAIL THE SAME WAY?" — corroboration is evidence only if the failure modes are
disjoint. The standard that settles it: NO ROW IS DEMOTED UNTIL THE ELEMENT THE
REQUIREMENT IS ABOUT HAS BEEN LOCATED AND DRIVEN — not the file, not the page,
THE ELEMENT.

THE CEILING OF A BROWSER-EXTENSION TIER, stated once rather than rediscovered
per project: THE TIER DRIVES A HIDDEN TAB, and three limits share that root —
load-time focus, `focusout`, and TIMER GRANULARITY (`setTimeout` at 50, 250 and
500 ms all fire at the same instant on a one-second boundary, so anything
debounced, throttled, delayed or auto-dismissed is unmeasurable there). Two more
are separate: REQUEST TIMING, where interception must happen BELOW the page's
own wrappers, and a CREDENTIAL A SESSION DECLINES TO ENTER, a judgement rather
than a capability. NOT affected: Navigation Timing, which is not timer-based,
and anything DOM-derived and synchronous — `closest()`, `offsetParent`,
settled-DOM reads.

AN INSTRUMENT LIMIT, ONCE FOUND, GETS OVER-APPLIED. That focus limit was first
recorded flat; it is true of FULL-PAGE forms, which rely on the load-time focus
Chrome suppresses, and FALSE of dialogs, which focus EXPLICITLY and do not
depend on document focus. The first proof was correct and ITS SCOPE WAS ASSUMED
RATHER THAN MEASURED — this file's subject aimed at a limitation instead of a
population. An over-applied limit is worse than an over-applied guard: it does
not produce a false finding, it produces A REFUSAL TO LOOK, and nothing revisits
a thing declared unmeasurable.

A NUMBER BUILT WHERE NO CLOCK COULD REACH is not a wrong measurement but an
UNMEASURABLE one, and the honest report is "unmeasurable", not a reconstruction.
The ~730 ms of unexplained client latency was chased through two reasonable and
wrong hypotheses before the clamp above explained it, and the corrected figure —
debounce plus server plus render — IS A RECONSTRUCTION ASSEMBLED FROM PARTS, THE
SAME KIND OF CLAIM AS THE WRONG FIGURE IT REPLACED. Naming the environment is
necessary and NOT SUFFICIENT when the environment puts the clock out of reach.

THE ESTABLISHED CONVENTION IS NOT EVIDENCE OF CORRECTNESS. Two date fields
lacked a today-default and the proposed repair was to copy the convention —
NINETEEN EXISTING SITES. A sweep refused it: all nineteen compute the day in
UTC, and `new Date().toISOString().slice(0,10)` returns the 20th on a machine
whose wall clock says the 21st. Wrong in both directions, with the correct
helper already on the page. NINETEEN CALL SITES AGREEING IS EXACTLY WHAT A
COPIED BUG LOOKS LIKE; "follow the existing pattern" is sound advice and also
the mechanism that propagates one, and only a guard over the convention tells
the two apart. This file has reasoned from convention itself — "the same page
carries ten correctly bound pairs, so the codebase knows how" — which is the
same inference and was luckier.

A SWEEP RETURNS WHAT IT EXAMINED, NOT ONLY HOW MUCH — and this is the
precondition for the witness rule below, not a tidiness point. A SWEEP THAT
RETURNS A COUNT AND A VERDICT CANNOT HAVE A WITNESS AT ALL WITHOUT BEING
REWRITTEN FIRST. Two guards got witnesses for the price of a substring check
because their scans already returned identifiable rows; a third cost a change to
its resolver, which returned `{failures, undecided, judged}` — a count and a
verdict, with nothing to name — and had to grow a `seen` map of the distinct
signatures it JUDGED, not only the failing ones, before a witness was
expressible.

THAT IS PROBABLY WHY SO FEW GUARDS HAVE ONE. "Assert a named witness" reads as a
discipline problem and is an INTERFACE problem: the guard's return shape decides
whether the discipline is available, a scan returning `(count, ok)` forecloses
it, AND THE FORECLOSURE IS INVISIBLE, because nothing about `(count, ok)` looks
incomplete. If a guard returns a bare count today, that is the change to make
first — none of the witness guidance can be applied to it until it does. (This
module's `population` and `subject` commands print MEMBERS for exactly this
reason, and the count falls out of them for free.) Cost is small in the
direction that matters: a few hundred DISTINCT signatures over 7,426 judged
nodes, because distinct is the right granularity for membership — you never want
every node, you want every KIND of node.

AND A WITNESS CAN BE A KIND RATHER THAN A MEMBER, which is the other half. A
floor of 30 on a citation guard was written specifically to assert a widening,
was measured, and was mutation-tested — AND WOULD STILL PASS AGAINST A CORPUS
THAT HAD LOST THE ENTIRE SHAPE THE WIDENING WAS FOR: thirty citations all
carrying the `UI-` prefix satisfy it perfectly, while the prefixless ones the
widening existed to include could all be gone. A SIZE CANNOT EXPRESS "CONTAINS
THIS KIND OF THING". So a witness takes `member:` or `matching:`, a pattern at
least one population member must satisfy.

IF THIS FILE KEEPS ONE LINE FROM THE NIGHT IT IS THIS: A SHRINK-ONLY RATCHET IS
BLIND IN THE DIRECTION THAT LOOKS LIKE SUCCESS, AND ONLY A NAMED MEMBER CAN SEE
THERE.

ASSERT THE WITNESS, NOT THE SIZE — two rules that look alike, are not
interchangeable, and the weaker one is the likelier to get written.

    a corpus WIDENED because a proxy missed something
        -> ASSERT THE SIZE, WITH THE NUMBER. Catches a later tidy narrowing it
           back.
    a corpus that must contain a SPECIFIC element
        -> ASSERT THE WITNESS, BY NAME. Catches that, AND survives a legitimate
           narrowing.

The size assertion cannot express "the population still contains the thing this
guard exists for". A composited-contrast sweep judges 7,426 elements against a
floor of 6,000, and the element it was BUILT for — one chip read by a person at
2.86:1 — IS FOUR NODES. 7,426 minus four chips is 7,422, WHICH PASSES THE FLOOR
COMFORTABLY. Anyone tidying the seed that produces them re-blinds the sweep for
its own subject and every number stays green.

AND A SIZE RATCHET IS DIRECTIONAL, THEREFORE BLIND IN THE DIRECTION THAT LOOKS
LIKE SUCCESS; A NAMED WITNESS HAS NO DIRECTION. The same sweep NARROWED, 7,500
to 7,426, when a bug in it was fixed — 78 undrawn `font-size: 0` spans correctly
left the population. CORRECTNESS WENT UP WHILE THE COUNT WENT DOWN, and a size
assertion cannot tell that from a regression. (The session that first read it
pattern-matched "the number moved after a fix" onto the widening class WITHOUT
CHECKING THE DIRECTION — the same proxy failure both projects spent the night
documenting, inside the tool built to document it.)

THE WITNESS RULE HAD ALREADY PAID HOURS BEFORE ANYBODY HAD WORDS FOR IT. A
calendar-day guard names five specific sites and asserts each still matches —
written to stop prose describing moved sites, so the right structure for the
wrong reason. When an `accept="image/*"` opened a CSS comment that swallowed
1,163 lines, the count fell TEN TO EIGHT: DOWN, IN A SHRINK-ONLY RATCHET, WHERE
DOWN READS AS PROGRESS AND NOTHING QUESTIONS IT. The two named sites that stopped
matching are the only reason a silent catastrophe was legible as a defect.

So `population.witness:` names members that MUST appear in the population's own
output, each with the `why:` that makes it the witness — the element that
motivated the guard, the route that broke, the row a person complained about.
Its mutation is whatever makes that member disappear, and the test must go red
NAMING IT while the guard's other assertions stay green; otherwise you have
proved the guard notices something, not that it notices THIS. Note this is a
different claim from `capability.fires`, which proves the DETECTOR still
detects: a detector can be perfectly capable while the corpus no longer contains
the member it exists for.

A DERIVATION FROM A REAL SOURCE READS AS PRINCIPLED, WHICH IS WHY NOBODY COUNTS
IT. Two browser sweeps walk FOUR dialogs while twenty-three files render one.
The corpus is derived and FAITHFUL — a component registry crossed with the
actions the descriptors declare, every registered dialog reached, none missed.
THERE IS NO PROXY AND NO FILTER TO INTERROGATE. It is simply narrower than the
property it is taken to cover, and every internal check it has agrees with it.
Worse, its own control asserted `len(CONTROLS) >= 4` — A FLOOR THE CORPUS MET
EXACTLY — so a clean result from a short list was indistinguishable from a clean
tree. A CONTROL CALIBRATED TO THE CORPUS IT IS CHECKING CANNOT DETECT THAT THE
CORPUS IS THE WRONG CORPUS.

So the two defences are complementary and neither is complete alone. ONE ASKS
WHAT THE FILTER EXCLUDED — assert every widening, with the number, wherever a
corpus was widened because a proxy missed something. THE OTHER ASKS HOW MANY
THERE ARE — take the instrument's population count and compare it against a
count DERIVED SOME OTHER WAY. Two counts, two derivations, one comparison. That
second one is what `population.superset:` is, and the rule it carries applies
generally: A FLOOR MUST NOT BE DERIVED FROM THE CORPUS IT BOUNDS.

THREE CRAFT POINTS FROM THE GUARD THAT CLOSED IT, which generalise better than
the finding. RE-DERIVE THE CORPUS QUERY RATHER THAN IMPORTING IT from the sweep
under test, because AN ORACLE THAT QUOTES THE CODE IT GRADES AGREES WITH IT BY
CONSTRUCTION — and note the tension with this file's other advice, which is to
IMPORT the rule rather than restate it: import the RULE, RE-DERIVE THE CORPUS.
Restating a rule invents false positives; importing a corpus inherits its blind
spot. NAME THE UNREACHED RATHER THAN COUNT THEM, so a dialog added tomorrow
joins the unmeasured set loudly and a diff says which one moved. And the
mutation worth copying wholesale: registering a dialog NO descriptor declares
correctly does NOT move the count, while registering one the descriptors DO
declare moves it and reddens. A GUARD THAT REDDENS ON ANY PERTURBATION IS MERELY
REACTIVE; distinguishing a genuinely unreachable entry from a hole is what shows
it is measuring the property rather than noticing that something changed.

A SEAM BETWEEN TWO HONEST GUARDS IS NOT ANY OF THE POPULATION CLASSES ABOVE,
because every one of those is about ONE guard's corpus being wrong. A unit sweep
checks that required fields are MARKED, reads dialog markup, and passes. An e2e
sweep checks that required fields are ASSOCIATED with a label, and never opens a
dialog, so it never sees them. EACH IS CORRECT IN ITS OWN SCOPE, and 78 unnamed
required controls live precisely in the space both exclude: not a dishonest
guard anywhere, not a narrow corpus anybody chose, TWO RIGHT CORPORA THAT DO NOT
MEET.

So a guard may declare `abuts:` — another guard in the register whose scope must
meet this one's — together with `jointly:`, the population the PAIR is
responsible for. The module runs both subjects and names what falls in neither.
Nothing else here asks whether two well-scoped checks overlap or at least abut,
and the defect sat in the seam.

AND AN UNSIZED DEFERRAL IS THE SAME DEFECT ONE LEVEL UP. Asked to STATE a modal
exclusion the way a parser's script-blindness had been stated, the session
measured it instead: 86 required controls sit in the DOM unjudged across the 78
pages that run, worst two files at 20 each, shrink-only, mutation red at 87. The
number falls either when somebody fixes a field or when somebody teaches the
sweep to open a dialog, so THE RATCHET REWARDS BOTH. Two details worth copying:
it took a different ratchet shape than its own instinct because a six-page
sample showed the first idea — a floor on "pages that judge at least one field"
— starts at zero-or-one on nearly every page that matters, correct and
unshippable as a gate; and the shape it chose keeps "JUDGED 0 OF 16" APART FROM
"JUDGED 0 OF 0", because a page with nothing to check is not a failure to check,
which is what makes an empty corpus legible rather than silently green.

ONE REQUIREMENT MAY HAVE SEVERAL DETECTORS, and then the population is the
REQUIREMENT'S rather than any one detector's. STA-02 — "an empty screen explains
why it is empty and offers the next action" — was guarded by three tests: the
helper renders what/why/next-step (executed in isolation, correct, and proves
nothing about who calls it); every AnatEmpty call passes a `why` (corpus:
AnatEmpty calls); hand-rolled empty states only fall, ceiling zero (corpus:
markup carrying the empty-state class). A list dropping a sentence into a plain
table cell is NEITHER — sanctioned, so not hand-rolled; not AnatEmpty, so never
checked for why and action. Both detectors are individually sound and neither is
blind in a way you could see from its own output, because each population was a
proper subset of the claim and THE UNION OF THE TWO SUBSETS IS STILL A PROPER
SUBSET. So `subject.detectors` takes several commands, the union is compared to
the requirement's population, and a member no detector covers is named.

The detail that generalises beyond that repo: the hand-rolled detector's design
is "anything not going through the blessed helper is suspect", which is a good
design carrying an implicit assumption — that there is ONE blessed helper. The
moment a second sanctioned helper exists with a narrower contract, everything on
the second path is exempt from the first detector by construction and covered by
nothing. A guard defined as "not the approved way" silently grows a hole every
time somebody approves another way.

A MEMBER MAY BE A PAIR, and that is how the catalogue cases are written. ACT-05
swept 146 dialogs and made every save answer 500 — one arm of the client. A
dropped connection resolves through the `catch` with status 0 and never throws,
so a handler written against an exception falls into its success branch and no
number of 500s can see it. Emit `dialog::500` and `dialog::offline` and the two
modes are two members: a mode that reached nothing is then a gap with a name
instead of a count one mode covered for. An injection harness enumerates its
modes by asking what the CLIENT does differently, never by picking a plausible
error — for a fetch client that is three arms, an error status (the response
path), a transport failure (the catch around fetch), and a SUCCESS carrying an
unexpected body, which takes no error path at all and throws inside the
renderer after the region has been cleared. The third is the one everybody
forgets and the only one that produces STA-07's literal subject, a blank white
screen; a sweep that sends 500 and only 500 cannot reach it. ACT-10 is the same
shape in a PAIRING — a button's verb against its success sentence — where the
guard checked one end: 20 of 183 messages resolved to a control, and the other
163 were nobody's.

The sharpest case of all is a differential whose corpus is the INTERSECTION of
the two things it compares: the field app's 16 HTTP reason phrases against
api.js's 39, under a comment claiming parity, tested on 404/422/403/500 — four
phrases in both lists. It could not see the difference it existed to measure.
The population there is the union; the subject was the intersection, and this
module prints the twenty-three names in the first and not the second.

WHEN A PATTERN STANDS IN FOR A PROPERTY, THE COUNT IS THE CANDIDATE SET AND NOT
THE FINDING. A sweep for "same button, same word" keyed on what a button is
WIRED to — a primary button carrying an id naming a commit verb — because most
dialogs there are div clusters with no `type="submit"`. 27 matched; all 27 were
opened; FOUR WERE FABRICATED. A client-picker "Apply", a bulk-flag "Apply", a
checklist-fill "Apply" and a TOTP "Confirm" are different acts correctly
carrying different words: THE MATCH WAS ON THE STRING AND THE PROPERTY WAS THE
ACT. Published as a count, the row would now carry four invented findings.

That is the same root as an under-returning pattern and the opposite direction.
Under-returning is INVISIBLE — nothing tells you what the pattern did not match.
Over-returning is visible ONLY IF SOMEBODY OPENS EACH ONE, and it presents AS A
FINDING, which is the direction with social momentum behind it: four extra
findings look like the sweep working. So report "27 candidates, 23 confirmed by
reading, 4 rejected with reasons", and a sweep that cannot afford to read its
candidates SAYS HOW MANY IT DID NOT READ. THE READING IS NOT A QUALITY CHECK ON
THE PATTERN, IT IS PART OF THE MEASUREMENT. (`subject.reports: candidates` with
`read:` is that; the verdict prints the unread remainder.)

A CANDIDATE'S SAFETY IS IN ITS CONTEXT, NOT ITS TEXT, and two sites of one
expression proved it in one sweep. `AnatTime.todayLocal()` was the recommended
replacement for `new Date().toISOString().slice(0,10)`, and it carries TWO
boundaries neither visible in the matched expression: it is right for a date a
person READS and not automatically for one the client SENDS, where a server may
judge it against a third clock; and it is only CALLABLE where DEFERRED GLOBALS
EXIST. `wall-time.js` loads with `defer`, so an inline script inside a content
block runs at PARSE TIME and the helper is undefined there. One matched site is
an IIFE invoked immediately — the swap would have thrown, killing the whole IIFE
and the seventy lines below it: console error, SILENT DEAD FEATURE. The other
sits inside an `async function` fired by a user gesture and is safe. SAME
EXPRESSION, SAME SWEEP, SAME "MECHANICAL" CLASSIFICATION, and the only reason
anyone knows they differ is that somebody checked THE ENCLOSING FUNCTION rather
than assuming two sites of one expression were alike.

A THIRD CATEGORY BESIDE CONFIRMED AND REJECTED, which had no name in anybody's
output: SITES WHERE THE MATCH IS REAL, THE SUBSTITUTION IS AVAILABLE, AND THE
CHANGE IS STILL NOT WORTH MAKING. That IIFE key is one person's own routine,
never sent anywhere, never compared to a server value, so the viewer's day is
the only day it must agree with and it agrees with itself in any zone. IT WAS
NEVER A DEFECT; the swap was cosmetic, and the ledger read zero user-visible
benefit against three real costs. A CHANGE WITH NO BENEFIT AND THREE COSTS IS
NOT A CHANGE. The site now carries two sentences saying why, so the next sweep
stops at the line instead of rediscovering the trap — or worse, not discovering
it. `subject.declined:` with `declined_why:` is that category; without the
sentence a declined site is indistinguishable from an unexamined one.

AND THE COST OF REFUTATION IS WHAT SEPARATES THE TIERS, which is not an accuracy
argument. A SOURCE-READ CLAIM COSTS AS MUCH TO REFUTE AS TO MAKE: four button
lines to kill four claims, one each. A RENDERED CLAIM CAN BE KILLED WHOLESALE:
of 84 reported contrast failures, 78 were one selector at FONT-SIZE 0, and
killing all 78 cost ONE observation — the computed font size, from the element
itself. The source read was entirely accurate about what it matched; the
difference is that a property of the rendered thing refutes a whole class at
once, and a property of the text refutes one line at a time.

AN ABSENCE HAS NO LINE NUMBER, so an absence-shaped finding needs a different
contract from a presence-shaped one. A scan flagged 8 files for lacking a
filtered-empty message — "this FILE contains 'no X yet' AND does NOT contain a
filtered-empty message" — and the session handed the list found every file
apparently correct but could not tell WHICH LIST on each page had been flagged,
because each page has several. You cannot point at what is not there. It asked
for line numbers rather than fixing or dismissing, and its reasoning is the
rule: declaring them false positives would be the same error as fixing them
blindly, a claim about a population it had not matched to the finding.

So a guard declaring `claims_shape: absence` must report members that NAME THE
ELEMENT the thing was expected near — `path::anchor`, the estate's convention —
because a file-level absence is unactionable on any file containing more than
one instance of the thing. A LOCATED FINDING IS WORTH MORE THAN A COUNTED ONE,
and where a scan hands work to somebody else a handover of counts is a handover
of a claim the receiver cannot verify. The only safe response to one is refusal.

AND NARROWING A WRONG POPULATION MAKES IT SMALLER, NOT TRUER. That scan was
narrowed twice — 29 → 9 → 8 — and its author felt the narrowing had earned the
number. When the eight were finally opened it was wrong IN BOTH DIRECTIONS AT
ONCE: over-reporting sub-panels and a FIELD PLACEHOLDER ("No date yet") as
filtered list states, and under-reporting six real implementations because the
pattern required "match this FILTER" while the product says "match this TAB AND
THESE FILTERS" — one of them under a comment naming the requirement id itself.
Net: ONE real finding out of eight, and the real one was the single site that
could be LOCATED. Three narrowings cost more than one instance read.

FILE-LEVEL CREDIT FOR A MEMBER-LEVEL PROPERTY UNDER-REPORTS BY CONSTRUCTION, and
that is the dangerous direction. (THE INSTANCE FIRST RECORDED HERE FOR THIS WAS RETRACTED WITHIN HOURS AND IS
KEPT AS THE RETRACTION, because the rule stands on structure and the instance
did not. A scan said 8 of 23 surfaces lack a sort mechanism; a browser drive of
a surface NOT among the 8 found 20 headers and none sortable, and the agreement
was reported as proof the scan under-counted. Both were wrong. The drive queried
`thead th` ACROSS THE WHOLE PAGE and judged 20 headers from THREE tables — the
real list has 15 headers, 11 sortable, and THE ELEMENT UNDER TEST WAS NEVER
LOCATED — while the scan could not see sort at all because it is applied AT
RUNTIME by a shared helper rather than written into the template. So this rule
has no verified instance in this estate; it is here because file-level credit
under-reports BY CONSTRUCTION, which is an argument rather than a measurement,
and it is labelled as one.)

THE ASYMMETRY, which this kit had backwards all day: an OVER-reporting scan is
SELF-CORRECTING — the first person to read an instance finds a false positive
and re-narrows, which is what happened five times in one night (119 empty states
that were 59, 250 unreachable cells that were 0, 29 lists that were 9, 35
marker-keyed guards that were 3, 14 floorless ratchets that were 0). An
UNDER-reporting scan is INVISIBLE: nothing in its output points at what it
missed, and it is found only by driving a case it did not flag. The same defect
has a bounded cost in one direction and an unbounded one in the other, and
"read an instance before quoting the number" only catches the cheap direction.

So where a scan cannot resolve the member, THE HONEST OUTPUT IS A FLOOR WITH THE
RESOLUTION LIMIT STATED, NOT A COUNT — `subject.reports: floor` says so and the
verdict prints it beside the numbers, so the limitation travels with the figure
instead of being lost the first time somebody quotes it.

A GUARD'S UNIT MUST BE THE UNIT THE REQUIREMENT QUANTIFIES OVER. Whenever the
guard's unit is COARSER than the requirement's, the difference is invisible by
construction and looks exactly like coverage.

A census for "a refusal takes the person to the offending field" checked whether
each FILE containing a refusal also contained a focus call. Two of the sign-in
screen's three focus calls were removed to watch it go red and IT STAYED GREEN,
because the third still matched somewhere in the same file: one call vouching
for three refusals. The same shape turned up twice the same day in another
codebase, in a ratchet and in a date check. THE FILE CONTAINING THE RIGHT THING
SOMEWHERE SAYS NOTHING ABOUT WHETHER THIS MEMBER GOT IT. Per site is the fix:
for each refusal, require the pointer between the setter and its `return`, and
report the count of silent sites rather than a verdict.

This is one rule with three faces, and the other two are elsewhere in this file:
a row about every refusal needs a check per refusal; a row about every dialog
needs a check per dialog (ACT-07, 12 of 146 unreached); an exemption about one
file needs a check that removing THAT entry bites. So `population.unit:` is
declared and says what ONE MEMBER IS — a site, a dialog, a route, a template —
and a reader can then challenge it against the requirement's own wording, which
is the only place the mismatch is visible.

THE SAME ROW FAILS IN CODEBASES THAT SHARE NO CODE, which is why the row rather
than the implementation is the unit of failure. Three rows were found
independently in two products on one day — FRM-05 (one meaning "first in the
response body" with an e2e driving a single field; the other holding on one
surface of ten), ACT-07 (12 of 146 dialogs bypassing the prompt there, 13 of 14
here), and the class-keyed census shape. What they share is not a bug pattern
but a TEST pattern: each row was closed by evidence exercising ONE MEMBER of a
population the row quantifies over, and in each case the one member was the one
where the property already held. The row's text invites a single worked example,
and a single worked example is exactly what cannot see it.

AN EXEMPTION MUST BE TESTED IN THE DIRECTION THAT PROVES IT IS LOAD-BEARING.
Two entries were added to one exemption map in a single edit, reading
identically — a sentence saying the page's state is view state and it writes
nothing a person typed. One was real: delete it and the test goes red, because
the file genuinely is a candidate and the entry is the only thing keeping it out
of the failure list. THE OTHER ENFORCED NOTHING — its only call was already on
the reads list, so the file never entered the candidate set, and deleting it
left every test green. It had the shape of a considered decision and the force
of a blank line. Neither reading the entry nor reviewing the diff distinguishes
them; deleting each one and watching does.

So an exempted member that the guard never had in its population is a finding of
its own here, separate from one the guard has since started examining: the first
means the honest record belongs upstream, the second means the case is fixed.
Every project in the estate carries lists of this kind — exclusion maps, skip
budgets, ratchet baselines — and nothing was checking any of them this way.

EVIDENCE THAT IS SOUND AND ANSWERS THE WRONG QUESTION — not a narrow corpus, not
a stale reason, not a marker-keyed population, not a vacuous check. A row reading
"the display remains correct at up to 200% TEXT zoom" is implemented on four
green tests, honestly written, which set the viewport to 640x400 and assert no
sideways scroll and no clipping. NOTHING IN THE EVIDENCE ENLARGES ANY TEXT. The
test's own docstring states the assumption — "a browser at 200% lays a 1280x800
window out as 640x400 CSS pixels" — which is true of PAGE zoom and false of TEXT
zoom.

THE TWO HAVE DIFFERENT FAILURE MODES, NOT DIFFERENT PROCEDURES. Page zoom
shrinks the viewport and the layout reflows. Text zoom leaves the viewport alone
and text grows INSIDE its container, breaking fixed-height boxes,
`overflow:hidden`, line clamps, and any control sized in px around text sized in
em. A viewport change cannot produce a single instance of that. SO THE GREEN IS
NOT A WEAKER VERSION OF THE RIGHT ANSWER, IT IS ORTHOGONAL TO IT, and no amount
of strengthening the reflow test approaches the claim.

The detection question is cheap and nobody had run it: DOES THE ROW'S EVIDENCE
COVER EVERY CLAUSE OF THE ROW'S TEXT? Two fields in one file, no browser. And
the tell that makes it hard is worth more than the instance: ALL FOUR TESTS ARE
NAMED FOR THE ROW THEY DO NOT DISCHARGE, so every previous reading checked the
evidence LIST, saw four matching names, and moved on. THE METHOD MUST READ WHAT
EACH TEST ASSERTS, NEVER WHAT IT IS CALLED — the name is the one field that
cannot be trusted, and it is the field every audit reads first. (That is why
`capability.fires` and `silent` demand `was:`, the thing QUOTED, beside the
command: a name is not evidence anywhere in this file.)

No field here enforces it. `undecided:` is where it lands — that row's would have
read "text zoom is not judged; the evidence measures page zoom" — and the
criterion mismatch is a question for a reader rather than a declaration to add,
since a guard that could state its own criterion correctly would not have had
the problem.

"LOCATED" IS NOT A SYNONYM FOR "TRUE", and this is the correction to the rule
that a located finding beats a counted one. A contrast sweep reported 303
FAILURES, EACH WITH A SELECTOR AND A COMPUTED VALUE — exactly the located
evidence this file spends pages demanding. Every one was wrong. Its background
resolver took the first non-transparent `backgroundColor` up the chain and
accepted `rgba(124,58,237,0.05)` as the painted colour, so A FIVE PERCENT TINT
WAS TREATED AS SOLID PURPLE; the design tints everything at 5–8%, so nearly
every element got a fabricated background and many computed to a ratio of
EXACTLY 1.0 — foreground identical to background, invisible text, ON A PAGE
SOMEBODY WAS LOOKING AT AND COULD READ. Compositing every translucent layer over
the page background: 747 measured, 5 failing. A SIXTY-FOLD DIFFERENCE.

A finding with a selector is checkable BY SOMEBODY WHO CHECKS, and 303 of them
is past the number anyone checks. WHAT CAUGHT IT WAS NOT A REVIEW, A MUTATION OR
A CONTROL — it was a SANITY INVARIANT: a ratio of 1.0 on legible text is
impossible. So a guard computing a PHYSICAL QUANTITY declares `plausible:`, the
range the quantity can take in a working system, and a value outside it is an
INSTRUMENT FAULT rather than a finding. Contrast ratios live in [1, 21] and 1.0
on rendered text is unreachable; a latency of 0 ms, a font size of 0 px and a
viewport of 0 are the same shape.

(Two more from the same work. A DOCUMENTED RATIO MEASURED AGAINST THE WRONG
BACKGROUND: a token's comment records 5.0:1, measured against WHITE, while the
failing pairing is that colour on a 10% tint OVER white — adopting the
documented figure without compositing reproduces the original error one
generation later, WITH A CITED NUMBER THE NEXT PERSON WILL TRUST. A recorded
measurement that does not name its conditions is a trap with a reference
attached, which is the dated-conclusion class with the written-downness as the
aggravating factor. And a guard keyed on the offending TOKEN would be mostly
false, because the same colour passes at large sizes and most of its uses are
24 px figures; keyed on computed size under 18.66 px it finds exactly the five
that matter. SAME TOKEN, OPPOSITE VERDICTS, DECIDED BY RENDERED SIZE.)

A CROSS-CHECK WHOSE FAILURE MODES ARE GENUINELY DISJOINT is the positive
counterpart to the false corroboration above, and the difference is the whole
rule. Two sweeps found the same five elements: one measured EVERY visible text
element and ranked by computed ratio, the other filtered on the computed colour
TOKEN. Different populations, different mechanisms, and no shared assumption —
one cannot be fooled by the colour, the other cannot be fooled by the ranking.
The question is never "were they independent" but "COULD THEY FAIL THE SAME
WAY", and here the answer is no, WHICH IS WHY THE AGREEMENT COUNTS.

A MEASURE THAT CANNOT FAIL IN ONE DIRECTION is the fourth face, and it is not
the corpus and not the conclusion. A guard for "the primary action is within
thumb reach on a phone" walks every screen, computes the emphasised button's
centre as a percentage of viewport height, and counts it out of reach below a
45 % arc. Corpus complete, vacuity floors on both sides, ratchet at zero,
written by somebody being careful. A BUTTON AT 199 % — a third of a page below
the fold, reachable only by scrolling — SCORES AS COMFORTABLY IN REACH. The
metric knows "too high" and has no way to express "not on the screen at all",
which is the same failure from the other end and the more common one, because
content grows downward.

Nothing about the corpus is wrong and nothing about the conclusion is stale. THE
METRIC IS INCAPABLE OF EXPRESSING THE FAILURE, and the blindness is inherited
silently by anyone who widens the sweep: extending it to 77 never-measured
screens returned 0 out of reach, the expected number, and every future extension
would have carried the blindness forward while the number looked better.

AN OBSERVER THAT SHARES A RESOURCE WITH THE OBSERVED CANNOT REPORT A TIMING.
A search-latency measurement returned 1998 ms, twice, consistently, right at the
row's ceiling — from a polling loop re-querying the table every 25 ms, each tick
running a querySelectorAll plus a filter over every row. IT WAS TIMING THE
SEARCH PLUS ITS OWN MEASUREMENT OF THE SEARCH. Re-done with a MutationObserver,
event-driven and zero polling: 1233 ms to first mutation, 1419 ms to last
response. THE POLLING INFLATED THE RESULT BY ~700 ms, more than a third.

Every other instrument failure in this file produced a wrong answer ABOUT
SOMETHING THAT EXISTED. This one CHANGED THE SUBJECT WHILE MEASURING IT. And the
tell that was mistaken for reassurance is worth naming: THE NUMBER WAS
REPRODUCIBLE — twice, consistently — AND THE CONSISTENCY WAS EVIDENCE OF THE
INSTRUMENT'S COST, NOT OF THE PRODUCT'S BEHAVIOUR. Polling a DOM to time a DOM
operation is the canonical case; the event-driven equivalent is not merely more
accurate, IT IS THE ONLY KIND THAT IS VALID.

A PERFORMANCE CEILING NAMES THE ENVIRONMENT IT WAS MEASURED IN, OR IT IS NOT A
MEASUREMENT. Those figures are staging, on a different instance from production,
from one laptop on one network with one client's data volume: what they
establish is the SHAPE — server fast, client slow before the request — and not
the absolute values. The session declined to flip the performance rows green on
them, because a row that goes green on one laptop's reading of staging is a row
resting on the wrong measurement. So `metric:` requires `measured_in:`, and the
verdict prints it.

(The finding underneath survives the retraction: three server calls, none over
240 ms, a 250 ms debounce, and THE FIRST REQUEST DOES NOT START UNTIL 984 ms
after the keystroke — ~730 ms of client-side delay before any network, of which
the debounce explains 250 and a second timer in the same file might explain 300,
leaving ~430 ms unaccounted. It was not chased and was not guessed at.)

THE CHECK IS CHEAP AND THE DISTINCTION IN IT IS THE WHOLE THING: mutate the
property THE REQUIREMENT NAMES and see whether the number moves. Moving a save
bar from `position: sticky` to `position: static` left the count at 0 while ten
of twenty-four screens moved their save to between 142 % and 199 %. Lowering the
threshold, or feeding a synthetic 200, proves the ARITHMETIC; breaking the
product and watching the number is what proves the METRIC. So a guard declaring
`metric:` must carry a known-positive with `by_mutating:` — the product property
broken — and `moved:`, what the number did, because only a number somebody
watched move is evidence the measure can fail.

(When that metric was repaired it found two defects immediately: a print button
at 102 % on a screen whose toolbar wraps on a phone, so the one verb the screen
exists for fell off the bottom edge, and a settings save at 131 %, below every
setting on the page. Both had been there since those screens were written, under
a guard reporting zero. And `min(pct)` as the way to pick "the" primary action
became wrong in the new terms — it judges a screen by whichever emphasised
button sits HIGHEST rather than by its best one — so the selection rule had to
change with the metric. A threshold change is rarely only a threshold change.)

AND THE EXEMPTION NOBODY WROTE DOWN AS ONE: THE HARNESS IS ON THE ALLOW-LIST. A
management host redirects any customer path to the customer domain — and every
unit and e2e test runs as `testserver`, which the host check EXEMPTS. So the
middleware NEVER RAN in any test, and staff links to `/order/{code}` from the
customer card and the audit page went live 307-ing cross-host to a coming-soon
page (and, after go-live, to a customer verification gate, SIGNED OUT, because
the session cookie is host-only). Measured read-only in production. No tier saw
it, because THE TEST ENVIRONMENT'S OWN IDENTITY WAS EXCLUDED FROM THE PROPERTY
UNDER TEST: a corpus defined by the property, one level up — not the population
that cannot contain a failing member, but THE ENVIRONMENT that cannot. An
explicit exemption with a reason can be shown able to bite; a harness identity
that happens to be on an allow-list is an exemption with no entry, no reason and
no review, and it covered the whole middleware.

AND THE POPULATION IS NOT "LINKS" — IT IS ANY BEHAVIOUR THAT DEPENDS ON WHICH
HOST ANSWERED. That product routes on the Host header: the management/public
bounce, the landing gate, the host-only session cookie, and template content
driven by which host it is. Every test uses one host, so THE WHOLE SUITE RUNS
INSIDE ONE HOST UNIVERSE THAT PRODUCTION NEVER SERVES. The instrument is
FAITHFUL and its universe is narrower than the property — the same shape as a
derivation from a real source reading as principled, arriving at the level of
the harness. The instrument gap is that NOTHING EXERCISES MORE THAN ONE HOST,
and the mechanical form runs each surface's key journeys under every real host
(and with the landing gate on and off), without following redirects, asserting
that no staff journey crosses to a host where its cookie is absent. Links were
the instance that bit a person; they are not the population.

THE FOUR REQUIREMENTS ARE ONE REQUIREMENT — SHOW THE THING CAPABLE OF THE
OUTCOME IT CLAIMS: a guard must be shown able to fail, a near-miss must be a
real near-miss, an exemption must be shown able to bite, and a metric must be
shown able to produce a failing value. Each is a face where the thing looks
present and is not load-bearing; the exemption and the metric are the two where
the failure is invisible BY CONSTRUCTION, because an exemption's job is to make
something not happen and a metric's is to return a number either way.

AND WHEN A REQUIREMENT ENUMERATES OPTIONS, THE TEST POPULATION IS THE
ENUMERATION, NOT ONE MEMBER OF IT. ACT-07 asks for three choices on leaving a
dirty screen — save, leave without saving, cancel. A browser file that clicked
cancel and nothing else sat over a save path broken twice over: the handler
answered from a stale closure so it never released the navigation, and the
writer swallowed every error so success and refusal resolved identically. Both
shipped-ready, both invisible, because the case that exercises them did not
exist.

REFUSE, DO NOT ATTRIBUTE — the failure in the other direction, and it now has a
number. A resolver that guessed each toast's button from the nearest enclosing
named function produced three confident phantoms in one hour, and a phantom
costs more than a miss: it costs somebody the time to disbelieve the guard, and
then the real findings it makes afterwards. Measured on a second corpus the same
day, both ways, after two retractions: over 8 cross-references in a tracker's
reasons, a strict parser (the status word must attach to the id as its SUBJECT,
present tense) resolves 1 and refuses 7, finding the one genuine defect with no
phantoms; a loose parser (a status word within 45 characters of an id) resolves
all 8 and reports two defects, of which one is false. Seven attributions
declined, one extra "finding" bought by attributing, and that one wrong.
Precision 1.0 against 0.5.

Not oversold: the loose parser's other six attributions were correct passes. The
strict parser is not better because those six were dangerous — it is better
because the loose one cannot tell which of the eight it is competent to judge,
and the one it got wrong is the one that cost. The numbers travel with their
sentence: it found a genuine defect nothing else would have found, at zero
false-positive cost, AND IT CANNOT SEE SEVEN OF EIGHT CLAIMS. Precision known
and perfect; recall unknown and probably poor. A subject command therefore prints only the members the guard
PROVED it judged. Everything it could not resolve it leaves out, where this
module names it as a gap — which is the honest denominator, and removes the
reason to guess: a guard can no longer buy coverage with an attribution.

THE POPULATION IS NOT ALWAYS CODE. An aggregate requirement — "no action fails
while the screen looks as though it succeeded" — is satisfied when its PARTS
are, and a parts list is a denominator like any other. GEN-03's was written by
example and did not name ACT-11, which is the row the silent failure of the day
actually was, so the aggregate could have gone green with the principle's own
defect live. Any tracker that decomposes principles into rows has this shape.
The population there is `requirement_text` and the exclusions are `exemptions`:
each one read rather than filled in, because SEC-04 deliberately says less (a
login error must not reveal whether the account exists) and that is a different
question, not a gap. A sweep whose exclusion list was filled in quickly to get
green would be the defect wearing the fix's clothes.

A PARSER'S BY-DESIGN LIMIT BECOMES THE GUARD'S POPULATION BOUNDARY SILENTLY, and
a mutation is what says so. An empty-state guard was widened to resolve blocks
with a real parser — 47 blocks judged, 19 bare, 2 files refused with their own
asserted ceiling, all honest. Then its OWN STATED MUTATION DID NOT GO RED:
HTMLParser does not parse markup inside `<script>`, BY DESIGN, so an empty state
built in a JS string is invisible to it. 47 judged in markup against 119
empty-ish texts inside `<script>` — INCLUDING THREE OF THE FIVE THE SESSION HAD
FIXED THAT NIGHT. And the gap between that guard and the helper-call guard — a
hand-rolled empty state inside a JS string — is watched by NEITHER, which is the
union-of-proper-subsets problem arriving BETWEEN TWO GUARDS rather than between
two detectors of one.

THE MUTATION IS WHAT FOUND IT, twice in one night: a mutation does not only
prove a guard DISCRIMINATES, it proves the guard REACHES. A stated mutation that
fails to go red is the cheapest possible report that a guard is lying about its
reach, and nothing in reading the guard says it.

A PARAPHRASE CHECKED AGAINST ITS OWN SOURCE ALWAYS AGREES. There is a good test
doing the rounds — a reason that cannot be stated without naming an
implementation detail is probably describing something narrower than the
requirement, so restate it in the person's vocabulary and see whether it still
holds. It has a hole, and the hole cost two real overclaims before anyone saw
it: LST-07's claim was restated honestly as "long lists page rather than loading
every row", and then verified AGAINST THE ROW'S OWN EVIDENCE — five database
tables that all page. It read as passing. A browser then found a client Contacts
tab rendering all 316 rows unpaged. Both were true: the row cited "contacts
(946)", the GLOBAL list, which pages; the browser hit
`/api/clients/{id}/contacts`, a different surface with the same noun, which
takes no limit or offset. Not an endpoint but a CATEGORY — every per-client
sub-list, 0 paged and 15 unpaged.

THE VOCABULARY CHANGED AND THE DENOMINATOR DID NOT. So the restatement must be
verified against the SURFACE A PERSON TOUCHES, never against the evidence
already cited, and that is a structural property rather than a discipline: THE
VERIFICATION MUST READ SOMETHING THE ROW DOES NOT CITE. Declare `cites:` (what
the claim already rests on) and `subject.reads:` (what the verification looks
at), and a verification whose sources are a subset of the citations is refused.
Otherwise the test is a paraphrase with extra steps.

Measured, on seven implemented rows: the incomplete test found ZERO gaps; the
same seven with the surface check found TWO overclaims, both real — 15 unpaged
per-client sub-lists outside a population of top-level lists, and 14 admin lists
rendering their empty row BY HAND with one fixed sentence, so a person who
filters a lead list to nothing reads "No leads yet. They will appear here when a
call comes in", which does not merely word it wrongly, it asserts something
false about their data. Same shape in both: the helper is correct, the
population is the CALLERS of the helper, and the surface has lists outside it.

THE DEFAULT POPULATION IS THE SURFACE THE AUTHOR WORKS IN — a second named
class, distinct from the marker-keyed one and needing a different fix. Three
instances in one day, all independent:

  FRM-01 required fields are marked. The mark comes from a rule in style.css and
         the sweep credited it to every template alike; the six customer-facing
         token pages are standalone documents that never load the sheet, so the
         required SIGNATURE field on the proposal, change-order and submittal
         approval pages had no mark at all, on a novalidate form that says
         nothing until Approve is pressed.
  ACC-06 the display holds at 200 % zoom. Population: 79 admin owner pages.
         Outside it: the portal and twelve public and token templates — and
         200 % is exactly the setting someone reading an invoice ON A PHONE is
         likeliest to have on, who is not an admin.
  ACC-05 meaning is never carried by colour alone. The reasoning walks the admin
         templates' dot indicators; the portal is not in the argument at all.

The marker-keyed class is about HOW A GUARD FINDS THINGS and its fix is a
derivation. This one is about WHERE NOBODY THOUGHT TO LOOK, and NO DERIVATION
FIXES IT: a perfectly derived population of the wrong directory is still wrong,
because templates/admin is the surface the author develops against, reviews in
and pictures when reading the requirement.

The fix is cheaper: the surfaces are LISTED BEFORE ANYONE STARTS — "admin shell,
contractor portal, public token pages, marketing site, field app" — and every
guard names each one as `{covered_by: <path prefix>}` or `{excluded: <reason>}`.
Leaving one out becomes an act rather than an oversight.

AND THE PREFIX IS CHECKED AGAINST THE POPULATION'S OWN OUTPUT, because the first
version of this took a sentence and not evidence: a trial guard declared all
four surfaces covered while its population command read templates/admin only,
omitting nine required controls on the public and portal pages, AND IT PASSED.
Nothing correlated the claim with what the command read. Now a surface claimed
covered by `templates/portal/` with zero members under it in the population is a
refusal rather than a sentence.

SAY PLAINLY WHAT A GREEN SURFACES BLOCK IS AND IS NOT: it catches the
CARELESSNESS — a surface nobody thought about, a prefix nothing reads — and it
does not catch the BELIEF. A guard can name a prefix, read one file under it and
claim the surface. Nobody may read a green surfaces block as coverage, and the
first person who quotes one as coverage will be quoting this paragraph, so it
says so here. It matters more than its frequency
suggests, because the excluded surfaces are where CUSTOMERS meet the product —
approving a proposal, paying an invoice, signing a submittal — so the omission
is systematically worst exactly where the stakes are highest, and invisible
precisely because the admin surface is what everyone works in. An admin meets a
defect and files a ticket; a customer meets one and forms a view of the
contractor who sent them the link.

AND A ROW THAT CANNOT DETECT ITS OWN FALSIFICATION, which belongs beside it:
ACC-05's claim currently holds because badges are text on a colour — BY
CONSTRUCTION, not by the mechanism its reason describes, which is about dots.
Ship one badge variant that is an icon on a colour with no text and the row is
false while its own reason still reads perfectly correct. A row whose stated
mechanism is not the thing making it true cannot notice when it stops being
true, and the only cheap check is a CONSTRUCTED known-positive: build the
icon-only badge in `capability.fires` and watch whether the guard sees it.

PREFER THE POPULATION THE CODE DETERMINES OVER THE POPULATION AN EXECUTION
DETERMINES. A corpus assembled by RUNNING the product measures whatever states
happened to exist when it ran — which depends on the seed, on what else ran
first in the same session, and on the order the runner chose. It fails in two
directions and BOTH READ AS CLEAN.

  UNSTABLE: a composited-contrast ratchet over 78 rendered pages breached in
  tier1 with a fifth signature — `span.ts-status-badge.ts-badge-submitted`,
  2.86:1 at 9.792 px — and DID NOT REPRODUCE in isolation on the same merged
  tree. The class is built at runtime as `'ts-status-badge ts-badge-' + r.status`,
  so it exists in the DOM only when a row is in `submitted` state, and nothing
  seeds one; something upstream in that session had submitted a timesheet. Same
  code, same tree, two answers. The honest-looking conclusion available to the
  next person is "flaky, re-run it".

  TOO SMALL: on the same night, a chip could not render at all on the test stack
  because nothing seeded the field its only writer sets, so a shrink-only
  ratchet SAT PERMANENTLY GREEN OVER ITS OWN MOTIVATING DEFECT until four values
  were seeded.

The population it should have keyed on is the one the CODE fixes: fourteen
selectors still set the inaccessible token, and FOURTEEN SELECTORS IS FOURTEEN
SELECTORS WHATEVER THE DATA DOES — no seeding, no ordering, no state. Chasing
the unreproducible fifth collapsed all five findings into ONE defect.

AND THIS IS A ROLE DISTINCTION, NOT A REPLACEMENT: the DOM sweep sees what a
static scan cannot — composited stacks, inherited colour, what actually rendered
— and the static scan cannot tell you an element ever appears. They are
complements. The failure was using the execution-determined one AS A RATCHET,
which is the role that needs a stable population. THE RATCHET BELONGS ON THE
CODE-DETERMINED POPULATION; THE EXECUTION-DETERMINED SWEEP BELONGS IN A
REPORTING TIER THAT IS ALLOWED TO VARY. `observed_from:` marks the second kind
and makes its size INFORMATION rather than a gate, which is that rule enforced.

A FLOOR COUNTED FROM WHAT THE ENVIRONMENT HAPPENS TO CONTAIN IS NOT A FLOOR,
and this is the same failure from the opposite direction: not a denominator too
small to discriminate, but a denominator whose property was ASSERTED rather than
CONSTRUCTED. A guard required at least three group/caller pairs to come back
refused, so that a run in which everything was editable could not pass and be
mistaken for the feature working. The number was derived, not guessed — group 1
refuses both callers, group 2 refuses the non-superadmin, so three is a
conservative margin under a deterministic four — and a reviewer checked the
arithmetic and agreed. It is true of a laptop loaded from a customer extract and
false of the seeded database CI runs against, whose groups do not start at id 1.
It went red there having said nothing whatever about the code.

THE DISCRIMINATING CASE MUST BE ONE THE TEST BUILDS, NOT ONE IT HOPES TO FIND.
The fixture already created a group whose name trips the rule; that group is
refused to one caller and open to the other in EVERY environment, by
construction, so the floor became those two reads and the found-count became
information printed beside them rather than a gate. Same discrimination, no
environment coupling.

So a population `observed_from:` an environment may not gate on a count of rows
it did not create: its pin is printed and never enforced, and it must declare a
`capability:` — which is exactly the constructed discriminator, the case the
guard builds and therefore finds everywhere.

And what caught it is worth as much as the rule: not review, and not the tier.
Two reviewers and the author read the number and agreed with the reasoning; a
run against the seeded CI database disagreed in four seconds. The reasoning was
written down, was correct about its premises, and was wrong.

CLASS-KEYED POPULATION is the sharpest sub-class of everything above, and it had
FOUR instances in one day: the denominator is the MARKER THE COMPLIANT CASES
SHARE, so a non-compliant case is excluded by the very property that makes it
non-compliant.

    STA-02  population = elements with class="empty-state"   -> hand-rolled ones invisible
    LST-08  population = tables with class="data-table"      -> 16 of 146 outside, 10 growable
    LST-05  population = tables declaring data-row-actions   -> 2 record lists outside
    LST-04  population = lists that CALL the helper          -> 14 render their empty row by hand

AND THE INVERSE TRIGGER, which is worse because the number moves the reassuring
way: KEYED ON WHAT THE FIX REMOVES. A guard for "a request body drops a field"
required `JSON.stringify` within 900 characters of a call — and the blessed
helper takes an OBJECT, so every call through it was invisible, and the window
then walked PAST the invisible call to report the next call's keys against the
first call's path: a wrong answer rather than a missing one. 182 → 226 matched
calls after the fix, 44 of them the object form nobody had ever seen. That
codebase is mid-migration onto the helper, so EVERY MIGRATED SITE WOULD HAVE
LEFT THE GUARD'S POPULATION, its matched count would have fallen as the code
improved, and a falling count on a coverage guard reads as progress — ending
green over a population of nearly nothing, in the middle of the work meant to
make it meaningful. The design-time question: for any corpus defined by a
syntactic form, ask what happens to it if the codebase adopts THE RECOMMENDED
ALTERNATIVE. If the answer is "it shrinks to zero", the guard is measuring the
old way of writing things rather than the property.

What makes both worse than an ordinary corpus gap is that THE MARKER IS APPLIED BY
THE CONVERSION. STA-02's ratchet drove hand-rolled empty states 75 → 38 → 0 by
moving them onto the helper, each conversion adding the class, so the population
is exactly "the things already fixed" and the number measures the conversion
rather than the surface. And one hole hid TWO rows for months: STA-02 and LST-04
both read implemented, and the same fourteen hand-rolled empty rows were
invisible to both, because both keyed on the marker the converted cases carry.

When a marker-keyed detector was replaced by a SHAPE-keyed one — a colspan cell
whose text opens with No/Nothing/None rather than an element carrying a class —
the count went UP, 14 to 19. It was the only number that rose that day, and it
is the cleanest evidence that the marker was hiding cases rather than bounding
them: the rule is NEVER KEY A POPULATION ON THE THING THE FIX ADDS. Derive from
what both kinds share — tag, route, AST node, rendered text — and let the marker
be what you ASSERT, never what you search for.

The check is cheap: count the things that would qualify STRUCTURALLY and
compare. Not "how many carry the class" but "how many are the kind of thing the
requirement is about" — for LST-08, `<table>` elements whose rows are built from
a collection; for STA-02, render paths that branch on a zero-length result. Both
derivable; neither derived until something asked. So a marker-keyed population
is permitted ONLY with `population.superset:`, the structural set it is a subset
OF, and the difference is reported. A denominator made of an implementation
detail of the fix can only ever measure the fix.

A SCAN GENERATES CANDIDATES, NEVER COUNTS — on prose-bearing source at least,
and a scaled count is an UPPER BOUND until one instance has been read by hand.
Nine times in one day a confident scaled heuristic was beaten by a targeted
read, twice agreeing with the wrong answer. The instance that settles it is
recursive: a sweep for marker-keyed guards reported 35, three were read by hand,
and ALL THREE WERE FALSE POSITIVES — the heuristic could not tell a guard that
ASSERTS a marker from one that DERIVES its population from one, which is the
very distinction it existed to make. Every number that held up that day came
from a structural derivation or from reading the sites. That is what
`capability.fires` is for: a real known-positive, named with `from:` and `was:`,
is a hand-read instance, and a guard that cannot produce one is reporting an
upper bound.

THE PROXY CLASS, with its own tally: filtering on a proxy for the property
UNDER-COUNTS IN THE DIRECTION THAT LOOKS COMPLETE. Ten proxies in one night, one
reader — a unit-bearing number for "names a threshold" (found 3, real 6), a
quoted phrase for "names a contract term" (8 of 9 flagged, 7 fine), writer
location for "no seed produces it" (found 3, real 43), a column name for "gates
something visible", HAS-A-CONTROL for "the row is sound" (8 of 9, both failures
included), a conjunction for "states two obligations" (found 28, missed 4), the
`UI-` prefix for "cites a row" (37 seen, 127 exist), `[required]` for "a control
a person fills", co-occurrence for "one mechanism", and a branch name for "what
the branch does". NINE OF TEN UNDER-RETURN. The one that over-returned was the
one discarded as noisy: A NOISY FILTER ANNOUNCES ITSELF; A QUIET ONE HANDS YOU A
SHORT CLEAN LIST AND YOU STOP. Five would have shipped as findings.

AND THE ONLY RULE ANYBODY PRODUCED FOR WHEN A PROXY IS SAFE: A FILTER THAT
SELECTS ATTENTION IS NOT A FILTER THAT PRODUCES CLAIMS. Absolute wording
("every", "always", "never") was used to choose which unread rows to OPEN; one
row — "the count is ALWAYS shown" — had evidence named like a register of
exceptions to itself, and a finding was half-written before the register was
opened and found empty. The proxy chose where to look and the reading decided.
That is the same rule as the next paragraph from the other side: a proxy may
rank what to read, and may never be the verdict.

A TELL IS A PRIORITISER, NEVER A FILTER — and this matters for anything that
might one day rank which guards to suspect. The tell that works is vocabulary: a
reason that cannot be stated without naming an implementation detail is
describing something narrower than the requirement. Measured:

    vocabulary-flagged rows, checked against the evidence:      0 of 7 moved
    the same rows, checked against the SURFACE:                 2 of 7 moved
    UNFLAGGED screen-facing rows, checked against the surface:  1 of 12 moved

The third number is the one to keep. The tell does real work — roughly four
times likelier to carry the gap — and it is NOT NECESSARY. LST-08's reason is
plain language ("every .data-table keeps its heading row on screen while
scrolling") and carries the identical defect: the population is a CSS CLASS, 146
tables exist, 130 carry it, and ten of the sixteen outside build their rows from
a collection and so can grow and scroll. A heuristic that EXCLUDED the unflagged
rows would have missed it — and would itself be a corpus keyed on a naming
heuristic, which is the thing this module refuses. So: it ranks, it does not
exclude.

(That is the third class-keyed population found in one day, after STA-02's
`empty-state` and LST-05's `data-row-actions`. Three instances is the framework's
own threshold for redesign rather than another row, which is why
`class_attribute` and `conversion_marker` are refused by name above.)

A WRONG DETECTOR AND A WRONG METHOD ARE NOT THE SAME COST, which is the argument
for a browser tier in one line. A wrong detector is bounded by its own scope and
the phantom is visible the moment you read the thing it named — seven of them in
a day, every one caught by reading the code the detector described. A wrong
METHOD is unbounded and invisible from inside, because every row it passed looks
exactly like a row that was actually checked; the one that happened was caught
by somebody else driving a browser, and by nothing else.

MEASURING ONE REQUIREMENT'S EVIDENCE AGAINST ANOTHER'S CLAIM. A scan for
"empty-state block with almost no text" returned 33 — a real number, correctly
counted, from a scan that ran exactly as written. Most of the 33 were
`Loading…`. The loading placeholder lives in the SAME ELEMENT as the empty
state, because the element is reused: it says "Loading…" while the request is
out and "No responses yet" after it answers. A loading placeholder is a
DIFFERENT requirement's evidence — "any action taking more than 300 ms shows a
loading indicator" — so the scan was about to file a page's COMPLIANCE with one
rule as its VIOLATION of another.

The window was fine and the corpus was fine. What is wrong is that TWO
REQUIREMENTS SHARE ONE SURFACE and the scan had no way to ask which state the
element was in: nothing in the markup distinguishes "empty because nothing
exists" from "empty because it has not loaded yet", because THAT DISTINCTION
LIVES IN TIME, NOT IN THE DOM. A static scan cannot see it at all, and a browser
scan sees whichever moment it happened to sample.

THE TELL: A REQUIREMENT ABOUT A STATE, SCANNED STATICALLY, WILL COLLECT EVERY
OTHER STATE THAT SHARES ITS ELEMENT. Empty, loading and failed all render into
one div in that codebase, and the day's other findings are the same three states
in the same container, which is unlikely to be a coincidence.

The sequence is the instructive part, and it is why a first number should never
leave the room: 119 (THE POPULATION INCLUDED THE MECHANISM UNDER TEST — it
counted the macro that RENDERS an action as an empty state with no action) → 33 (the loading confusion) → 59, of which 52 explain
themselves, 7 are bare labels and 2 of the 7 are not defects. Three numbers, one
scan, ten minutes, and only the last is true.

(No field in this module enforces that. Declaring the sibling states that share
a surface would be a tenth required declaration, and the cost of the nine it
already asks for has not been measured yet — adding a tenth while that is open
would be the kind of thing this file refuses elsewhere. The question is here to
be asked, not checked.)

CLOSE THE CLASS AT THE PROCESS LEVEL WHERE YOU CAN, rather than sweeping site by
site. One codebase has ten UTC-date sites with one live defect; another has ZERO
— not because the idiom is absent but because `app/clock.py` PINS THE PROCESS
ZONE AND THE DATABASE SESSION ZONE TOGETHER AND REFUSES TO START if the offset is
not the right one. Same for accessible names: 170 required controls, zero
unnamed, because the generic components build labels from the descriptors. Both
classes were REMOVED STRUCTURALLY, and for ten sites that is likely cheaper than
ten conversions — and it FAILS LOUDLY RATHER THAN SILENTLY, which is the half
that matters, since a swept site regresses quietly and a refusing process does
not.

THE INERT FIX is the extreme of the same measurement and the mirror image of the
marker-keyed class. A CSS token was defined with a comment naming its
requirement and documenting 5.0:1, AND USED IN ZERO RULES, while fourteen
selectors still set the inaccessible token and five of those sit at 2.86:1.
Somebody found the defect, computed the numbers, wrote the accessible token and
never wired it to anything — and nothing since noticed, because EVERY GUARD IN
REACH ASKED WHETHER THE REMEDY EXISTS, NOT WHETHER ANYTHING CONSUMES IT.

The discriminator: A GUARD THAT ASSERTS AN ARTEFACT EXISTS IS SATISFIED BY THE
ARTEFACT'S DEFINITION. A guard that asserts a DEFECT IS ABSENT must be keyed on
the defect's population — selectors setting a colour, not tokens declaring one.
Marker-keyed populations are blind to the non-compliant cases; THIS ONE COUNTS
THE FIX ITSELF AS A COMPLIANT CASE.

So the instrument is CONSUMER COUNT, and it applies to any NAMED REMEDY — a
token, a helper, a wrapper, a constant: how many sites use it, and is that
number asserted anywhere? `kind: reach` with `proves_helper:` is that
measurement; the inert fix is simply its zero, and a reach guard whose subject
is empty says so in those words rather than the vacuity ones.

A HELPER IMPLEMENTS THE CONTRACT CORRECTLY AND MOST OF THE PRODUCT DOES NOT
CALL IT — three instances in one codebase, each found separately, by a different
route, on a different row: apiFetch reports every failure by default and 198 of
870 sites call it; AnatEmpty takes title/why/action and refuses a null action
unless you say why, with 20 sites using it against 59 hand-rolled; and a third
message builder reached by neither of the other two paths at all. A TRACKER READ
66 ROWS IMPLEMENTED AND EVERY ONE OF THEM WAS TRUE OF THE HELPER.

That changes what such a programme MEANS: most rows are not "build the
behaviour" but "route the product through the behaviour it already has". So a
guard declaring `proves_helper:` must name a `paired_with:` REACH guard giving
the fraction of eligible call sites that arrive — A CONTRACT PROVEN ON A
MECHANISM NOBODY CALLS IS THE MOST EXPENSIVE KIND OF GREEN. The question is not
"does the product do X" but "WHAT FRACTION OF THE PLACES THAT SHOULD DO X GO
THROUGH THE THING THAT DOES IT".

A CORPUS DEFINED BY THE PROPERTY UNDER TEST, which is not the denominator
problem and needs its own name, because the usual fix does not work on it.

ACC-04 — "every action is performable with the keyboard alone, with a visible
focus indicator" — tabs 30 stops on 40+ pages and compares each focused
element's computed style against an unfocused clone. A good check, honestly
built, and it has caught real regressions. But IT REACHES ITS CORPUS BY TABBING,
so its population is "the controls already in the tab order" and a control
absent from that order cannot appear in it. The row claims every action is
keyboard-performable; the check can only inspect actions that already are. Four
KPI cards were `<div class="kpi-card" style="cursor:pointer">` with no role, no
tabindex and no key handler — controls to a mouse, nothing at all to a keyboard
— and the check tabbed past them because there was nothing to tab to.

Widening does not help, which is what makes it a different shape: ANY
ENUMERATION PERFORMED BY THE MECHANISM UNDER TEST INHERITS ITS BLIND SPOT.
Tabbing to find things in order to check whether they are tabbable is circular.

A WRONG DETECTOR CAN PRODUCE A FALSE DEMOTION AND CONCEAL A REAL FINDING IN THE
SAME PASS, AND THE TWO LOOK LIKE ONE RESULT. A check for "every required field
carries a visible required marker" read label `textContent` for "*" or
"required", found ZERO of eleven marked, and was one message from filing the row
as broken. The asterisk is a CSS `::after` with `content: " *"`:
`getComputedStyle(label, '::after').content` returns " *" on five of six
sampled, so THE ROW HOLDS and the detector was measuring a surface the marker
does not live on. Generated content, ARIA attributes and anything set at runtime
are all invisible to a text read of markup, and the failure direction was a
FALSE DEMOTION OF CORRECT CODE.

And underneath it, in the SAME eleven elements, a real defect: ten of the eleven
required controls have NO ACCESSIBLE NAME — the label is a SIBLING of the input,
not a wrapper, with no `for` and no id. A screen-reader user hears ten unnamed
controls, clicking the visible label does nothing, and the asterisk is painted
on a label that is not associated with its field, so assistive technology gets
neither the name nor the requirement. One field has no label element at all,
only a placeholder that disappears on typing. The same page carries ten
correctly bound pairs.

HAD THE FALSE DEMOTION BEEN FILED, THE SESSION WOULD HAVE "FOUND SOMETHING" AND
STOPPED LOOKING, one layer above the finding that mattered. So: READ THE MARKUP
AFTER A DETECTOR FIRES, NOT ONLY WHEN IT STAYS SILENT. This file has been
treating "a clean result deserves suspicion" as the rule; this is the converse,
and it is the more expensive direction, because a positive result feels like
work completed.

(The guard that replaced it is structural and cannot be gamed by a marker: every
`[required]` control must be associated with a label by for/id or by wrapping.
No class, no attribute the fix adds, no naming convention — which is what this
module asks for, arriving from a session that had just been burnt by a marker.)

THE TEST FOR THE SHAPE: ask whether the corpus COULD CONTAIN A FAILING MEMBER.
If members are found by the same faculty the property is about, it cannot, and
the check is decorative however carefully it is written:

    tab to find controls              -> cannot find an unfocusable control
    query rendered pages for empties  -> cannot find a page that never rendered
    enumerate registered routes       -> cannot find the unregistered one
    read the rows a query returns     -> cannot check the query returns the right rows

Each reads as thorough and each is closed under its own defect. So a guard names
the FACULTY its population is found by and the faculty its claim is ABOUT, and
they may not be the same: the finding is then the DIFFERENCE between two
enumerations by different faculties — for ACC-04, "clickable" minus "focusable",
in that direction, since focusable-minus-clickable is a different and much less
interesting set.

The sibling caveat for `subject.detectors`: two detectors whose corpora come
from the same faculty can cover each other perfectly and both be blind, so a
complete union is necessary and not sufficient. What matters is whether ANY
derivation could have found a failing member, which is a property of the
derivation rather than of the coverage — so no detector may share the claim's
faculty either.

THE TWO WAYS A POPULATION GOES UNSTATED, and the worked example is a pair of
rows that are both HONEST, both well written, and both unbounded — which is why
it is the better example: the others could be dismissed as sloppiness.

  ACT-05 "a failed save leaves the user in the form with everything they
         entered, and states why it failed" — swept over every dialog on every
         admin page an owner can open, filled, answered 500, its own save
         pressed. 146 dialogs, and the sweep proves exactly what it claims. Its
         population IS dialogs and its own reason says so in the first line.
         What nobody said is that a save can also be fired from a PAGE: 32 raw
         fetches with a mutating method neither check their status nor report a
         failure. The person presses, the screen does not change, nothing
         appears. A ROW THAT NAMES ITS POPULATION AND IS BOUNDED BY IT WITHOUT
         SAYING THE BOUNDARY IS A BOUNDARY.

  MSG-02 "one message hierarchy: toast for success, persistent banner for a
         screen-level error" — the rule is right and the hierarchy is
         implemented. What was never counted is how many loads can fail without
         saying so: 74 raw reads that draw the screen check no status and report
         nothing, so a failed read renders THE EMPTY STATE. The person reads "no
         data" when the truth is "this did not load", concludes there are no
         invoices, and acts on it — worse than a missing banner, a wrong answer
         presented calmly. A ROW THAT STATES A RULE AND NEVER COUNTS THE CALL
         SITES THE RULE APPLIES TO.

Those are the only two shapes, and the fixes differ: the first needs its
denominator widened or its scope written into the requirement; the second needs
a denominator at all. Hence `claims:` AND `undecided:` on every guard — one
sentence for what it proves, one for what it does not judge. ACT-05's would have
read "page-level saves are not judged", where a reader could challenge it; and
MSG-02 could not have been written without answering "of how many?".

`undecided:` also survives what nothing mechanical survives: TWO WRONG METHODS
AGREEING. Two sessions derived the same population and got 17 and 12, and the
truth was outside both because the dominant real pattern was a third shape
neither looked for; had they agreed, the agreement would have been read as
confirmation. A statement of what was NOT decided is the one field a second
wrong method cannot accidentally reproduce.

THE CORPUS IS WHAT THE MECHANISM CAN SEE, NOT WHAT THE CLAIM COVERS. ACT-07
says "leaving a form with unsaved changes warns, with three choices". Its e2e is
a good test by every standard in this file: it asserts the labels EXACTLY —
["Keep editing", "Discard changes", "Save"] — then clicks each one and checks
its effect, which is not a presence check. What nothing asked is WHICH DIALOGS
REACH THE HELPER. 146 have an id; 133 delegate their close through it; 12 close
directly and were never in anybody's population. The helper is not failing, it
is not reached, and the e2e's fixture is a compliant dialog, so it can only ever
confirm compliance.

That is also the argument for driving a real browser rather than reading better.
The session that closed this row clean had read the code carefully the same
morning and stopped, because the helper WAS correct. Reading source tells you
what a mechanism does; it does not tell you what reaches the mechanism. A
reachability population is the static form of the browser's question, and it is
derivable — but nobody derives it until something asks.

THREE NUMBERS, NOT ONE, when a finding like this is reported: 12 of 146 broken,
7 of those harmful (the rest hold no real fields), and ZERO harm on the one the
browser demonstrated, because that dialog happens to persist every keystroke to
local storage and restore it. The browser picked the least harmful of the twelve.
Report the demonstrated instance, the broken population and the harmful subset,
or the row is prioritised off whichever number was nearest.

A LIVE CORPUS OF ONE IS THE HARD CASE, and it is where `capability:` comes
from. A cross-reference check over a 109-row tracker — does a row justify itself
by asserting another row's status, and is that status still true — found exactly
one real defect. Correct that defect and the scan resolves ZERO: its entire live
corpus is the thing it was written for. A guard whose only comparison disappears
the moment you fix what it found cannot fail afterwards, and an empty corpus
reads exactly like a clean table. The class was real and detectable; the corpus
was one. So the detector's capability is proven on synthetic prose that cannot
go away — a subject-attached stale citation must be caught, a past-tense mention
("the one thing that was missing is now supplied by the PRT-03 work") must not
be, a bare pointer ("the same reasoning as NAV-03") must not be — and the live
scan is then allowed to find nothing without that reading as a pass.

A CLOSED DENOMINATOR IS ACHIEVABLE AT SCALE, and the obvious objection — that
this only works on small corpora — has a counterexample in the tree. anat's
MSG-04 guard does not report its unjudged share, it drives it to zero:
`test_no_sentence_is_hidden_from_the_sweep` asserts that NO person-facing error
detail is dynamic, so a sentence the AST walk cannot read is a failure rather
than a quiet gap in the denominator. Page literals judged, the page helper
executed under node with every branch judged by the same rule, pass-throughs
traced to the server or to apiFetch, 1,399 server sentences judged, nothing
left over. That is the reference implementation, and the ambition this module
reports against: a guard states its denominator and drives the unjudged share
to zero, or names what is in it.

WHAT THIS MODULE CANNOT SEE, AND IT IS HALF THE PROBLEM. Everything enforced
here answers ONE question — DID THE CHECK MEASURE ANYTHING? — and there is a
second, orthogonal to it: DID IT MEASURE THE RIGHT THING?

    VACUITY           the check measured NOTHING. Corpus floors, known
                      positives, real near-misses, exact pins, mutation replay,
                      plausible ranges: this file is built for it.
    CRITERION MISMATCH the check measured the WRONG THING, CORRECTLY. Nothing
                      here touches it.

AND A CONTROL MAKES A WRONG MEASUREMENT MORE CREDIBLE, WHICH IS THE PART THAT
HURTS. The text-zoom row below has a control, and a good one — a corpus floor
asserting forty-plus pages were opened. It works perfectly. IT PROVES THE SWEEP
RAN, AND THE SWEEP WAS MEASURING THE WRONG CRITERION THE WHOLE TIME. A reviewer
who checks for a control finds one and moves on, which is what happened to that
row for months.

That was established by a session proposing exactly the shortcut this file
invites — "the rows that hold are the ones whose author wrote a control" — AND
VALIDATING IT BEFORE OFFERING IT, against nine rows labelled by reading: 8 of 9
have a control, INCLUDING BOTH FAILURES, and the one without a control is sound.
As a filter it puts both known-bad rows in the pile you skip.

THREE MECHANICAL SHORTCUTS WERE TRIED IN ONE NIGHT AND ALL THREE FAILED, EACH IN
THE DIRECTION THAT LOOKS LIKE SUCCESS: a quoted-phrase check flagged 8 of 9
reasons and 7 were correctly fine, because quotes in requirements are
illustrations rather than contract terms; a name-match over derived columns was
wrong on 3 of 17, caught by reading four lines; and the control heuristic above.
THE ONLY METHOD THAT HAS WORKED EVERY TIME IS READING WHAT A TEST ASSERTS NEXT
TO WHAT THE ROW SAYS, and its slowness is not incidental to it — IT IS THE
METHOD. A HEURISTIC THAT HAS NOT MET A LABELLED SET IS A HYPOTHESIS.

WHAT THAT READING LOOKS LIKE WHEN SOMEBODY DOES IT WELL, since "read what each
test asserts" is easy to endorse and hard to do. One audit of another project
applied FOUR HEADINGS to every test cited as evidence, and the headings are the
method:

    ASSERTS            the clauses it actually asserts, by requirement id
    NAME-ONLY          the clauses its name, or the brief, suggests and it does
                       NOT assert
    POPULATION         customer, admin or both, with the size DERIVED A SECOND
                       WAY
    STILL PASSES AGAINST  what could break tomorrow without it going red

NAME-ONLY is the heading that finds the class above, and it found it at once: a
sideways-scroll test cited for 200% TEXT zoom asserts 390 px reflow — "the exact
trap" another project had hit the same week, now in a THIRD codebase with no
shared code. The row's wording produces the same wrong test wherever it is
read. STILL PASSES AGAINST is the heading that finds vacuity; the two together
cover both halves of the split drawn above, which is why a four-heading audit
beats any single check.

AND ONE CLASS THE READING FOUND THAT NOTHING ELSE HERE NAMES: A TEST WHOSE
ORACLE IS THE DEFECT. A test asserts that the English detail "MMSI must be 9
digits" reaches an operator — pinning, as the DESIRED behaviour, a violation of
the requirement that system output be translated. Ninety of the 101 literal
400-details in that tree have no Hebrew. This is not a guard measuring the wrong
thing; it is a guard DEFENDING the wrong thing, and it is the most perverse
direction in the set: THE SUITE WILL GO RED WHEN SOMEBODY FIXES IT, so the fix
has to argue with a green test that looks like evidence — and the natural
reaction to a red test on a fix is to back the fix out.

A GUARD THAT ENFORCES THE DEFECT IS DIFFERENT FROM ONE THAT IS BLIND TO IT, and
the anatomy is worth keeping: THE PREMISE WAS RIGHT — an operator must see the
SPECIFIC reason, not "something went wrong" — and the test PINNED THE REASON'S
LITERAL WORDING, which is itself the violation. A review's premise can be right
while its fix is wrong, and here that is frozen into a test. The mechanical form
is ANY ASSERTION WHOSE EXPECTED LITERAL IS OUTPUT A REQUIREMENT FORBIDS: every
string a test asserts is present in a rendered response, read against the rows
that constrain that string. And the repair KEEPS BOTH HALVES rather than
deleting the test: assert the route's own specific detail is shown, WHATEVER
ITS LANGUAGE, and separately that what is shown satisfies the constraint. PIN
THE PROPERTY THE PREMISE NEEDS, NOT THE LITERAL THAT HAPPENS TO EXHIBIT IT —
which is the marker-keyed rule arriving in an assertion's expected value: a test
keyed on the literal is keyed on the current implementation of the fix.

So nothing in this file should be read as covering the criterion question, and
the decision not to add a `criterion:` field is now supported rather than merely
prudent: a guard able to state its own criterion correctly would not have had
the problem, and a declaration would become one more thing a reviewer ticks.

WHAT IT CANNOT SEE, stated: that the guard's ORACLE is right. A guard may sweep
the whole population and still assert the wrong thing about each member — FRM-04
swept its eleven types and asked the implementation what the answer was, FRM-05
drove one field where every ordering agrees. Population is the denominator;
discrimination is a separate question and this module does not answer it.

The sharpest instance of that half, from ana-log the same week, because it shows
a RIGHT corpus with an oracle satisfied BY the defect: `/group-permissions/:id`
crashed to the error boundary on every load for a day — a hook added below an
early return, so render one calls eight hooks and render two calls nine. EIGHT
e2e files drive that route and not one went red, because every one of them
asserts a FAILURE state: a corrupted response, an empty catalogue, a stalled
request, a problem screen with a working exit, a save that fails. A screen
permanently in a failure state satisfies all eight. A TEST THAT ASSERTS AN ERROR
BOUNDARY VOUCHES FOR NOTHING BEHIND IT, AND EIGHT OF THEM VOUCH FOR NOTHING
EIGHT TIMES. The ninth test, in another file, does assert the rendered screen and
was red on main — unseen, because that project's e2e tier is not in CI. No
population check would have caught this: the corpus was right and the oracle was
wrong in the same direction eight times over.

Exit: 0 every guard sweeps its population · 1 a gap, a vacuous subject, a bad
pin or a bad exemption · 3 no register, or a population command that could not
run (never reported as 0).

Manifest shape:

    population:
      register: qa/guards.yml
      surfaces: [admin shell, contractor portal, public token pages, field app]

And in a guard:

    surfaces:
      admin shell:        {covered_by: templates/admin/}
      contractor portal:  {covered_by: templates/portal/}
      public token pages: {covered_by: templates/public/}
      field app:          {excluded: "no forms; read-only, checked under MSG-03"}

And the register:

    version: 1
    guards:
      - id: act11-count-reporting-routes
        check: C6
        claims: "a route that iterates a collection and reports a count reports its failures too"
        unit: "one route handler"          # what ONE member is
        claims_faculty: "what the route DOES at runtime"     # and the population is found by another
        undecided: "routes that report no count at all; anything reached from a background job"
        population:
          derived_from: ast
          faculty: "static parse of the route table"         # never the claim's own faculty
          cmd: "python3 scripts/qa/pop_count_routes.py"
          count: 11                      # exact; raise it in the commit that raises it
        subject:
          cmd: "python3 scripts/guards/act11.py --subjects"
        capability:                        # required when the live corpus may be empty
          fires:                           # REAL known-positives, best of all the originating instance
            - cmd: "python3 scripts/guards/act11.py --selftest add-modal"
              from: templates/admin/clients.html
              was: "data-close-add-modal wired straight to _closeAddModal"
          silent:                          # REAL near-misses the looser sibling fired on
            - cmd: "python3 scripts/guards/act11.py --selftest past-tense"
              from: qa/ui-standard.md
              was: "the one thing that was missing is now supplied by the PRT-03 work"
            - cmd: "python3 scripts/guards/act11.py --selftest bare-pointer"
              from: qa/ui-standard.md
              was: "the same reasoning as NAV-03, which this follows"
        exemptions:
          - member: "app/api/legacy.py::export_csv"
            reason: "deleted in the 2026-10 cutover; no caller since 09-02"
            evidence: docs/checker-calibration-ledger.md
            review_by: 2026-10-15
"""
from __future__ import annotations

import datetime as dt
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import warrant

#: How a population may be derived: by asking what a thing IS. Every one of
#: these reads a structure — a parse tree, the app's own route table, the
#: schema, an explicit enumeration, the filesystem, or the REQUIREMENT PROSE
#: the project already maintains. What is NOT here is the whole point: a
#: population chosen by what things are CALLED is the defect this module exists
#: for, so `names`, `grep`, `regex` and `convention` are refused by name rather
#: than by omission, with the reason printed.
#:
#: `requirement_text` is a text sweep and is admitted anyway, which looks like
#: an exception and is not. The refusal is on deriving a population from what
#: the CODE happens to be called; the spec is the other side of the question,
#: and a population read out of prose the project maintains GROWS BY ITSELF
#: when a row is added — which a hand-written tuple cannot. GEN-03 is why it is
#: here: "no action fails while the screen looks as though it succeeded" was an
#: aggregate row whose parts were listed by hand, and ACT-11 — a bulk action
#: that answered {"updated": 50} having written none — was not on the list. The
#: aggregate could have gone green with the principle's own defect live, and
#: its guard would have agreed, not by being wrong but because the row was not
#: one of the things it was looking at. Swept from the requirement text instead
#: ("every row whose wording talks about failing, erroring or succeeding is a
#: part of GEN-03 or is answered with the reason it is a different question"),
#: it names ACT-11 and FRM-13 by id.
#: `reachability` is the sixth and it is not a set of files at all: it is
#: "everything whose path REACHES the guarded mechanism", and its complement is
#: the defect. ACT-07 is the cleanest example this estate has produced —
#: 146 dialogs have an id, 133 route their close through the helper that prompts
#: for unsaved changes, and 12 close directly and never reach it. The helper is
#: CORRECT; the e2e asserts its three labels exactly and clicks each one; the
#: corpus is the entire defect. Derivable from the delegation attribute, with
#: the twelve as exactly the complement.
DERIVATIONS = ("ast", "route_table", "schema", "enumeration", "filesystem", "requirement_text", "reachability")
REFUSED = {
    "names": "ACT-11: the corpus was routes whose PATH contained batch|bulk; the property was routes that iterate a collection",
    "naming": "a naming heuristic is the defect, not a derivation",
    "grep": "a regex also matches the docstring that explains the rename — derive by structure",
    "regex": "FRM-10: `\\bcan_\\b` cannot match can_edit_field, and matched nothing, and read as clean",
    "convention": "a convention is what the example happened to follow",
    # The subtlest one, and the only one that is not obviously a naming
    # heuristic: a population keyed on the marker the FIX adds. It is not the
    # example's name and not a marker the compliant cases happen to share — it
    # is what each case was GIVEN during the conversion, so the population is
    # the set of things already fixed and the ratchet's fall to zero counts the
    # conversion rather than the surface. Ask instead what can EXHIBIT the
    # property: every list render path that branches on a zero-length result,
    # not every element carrying `class="empty-state"`.
    "conversion_marker": "STA-02: the class was added BY the conversion, so the population was the set of "
                         "things already fixed and 75 → 38 → 0 measured the conversion, not the surface",
    "class_attribute": "a class is applied to the cases somebody has already handled; derive what CAN exhibit "
                       "the property instead",
    "marker": "A MARKER IS NOT ONLY A CLASS, IT IS ANY SHAPE THE FIX PRODUCES — a wrapper element, a helper "
              "call, an attribute, a sibling text node. A text-node reader flagged a state it had FIXED AN HOUR "
              "EARLIER, because the fix puts the title in a <strong> and the why in the sibling text: it flagged "
              "correctly-fixed states BY THE SHAPE OF THE FIX. The population is the cases that OUGHT to carry "
              "it, however the fix happens to look",
}
#: The marker family: refused outright, UNLESS the guard declares the structural
#: superset its marked set is a subset OF, and lets the difference be reported.
#: A refusal alone only makes people write `derived_from: ast` and carry on; the
#: superset turns the refusal into a measurement.
MARKER_FAMILY = ("conversion_marker", "class_attribute", "marker")

EXEMPTION_KEYS = ("member", "reason", "evidence", "review_by")
SHRUNK_KEYS = ("reason", "evidence", "date")


@dataclass
class Set_:
    """One side of a guard: the members a command printed, or why it could not."""
    members: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class Row:
    id: str
    check: str
    claims: str
    #: HOW the population was derived, printed with the numbers. Two sessions
    #: derived the same population the same day and got 17 and 12, both
    #: sincerely — one scanned a text window from one dialog id to the next,
    #: which runs past its own dialog so a neighbour's attribute counted as
    #: compliance; the other traced the close path. Neither number carried
    #: anything saying which to trust. A derived population ships with its
    #: derivation, not just its result.
    derived_from: str = ""
    undecided: str = ""                                   # what this guard does NOT judge
    unit: str = ""                                        # what ONE member is
    population: int = 0
    subject: int = 0
    missing: list[str] = field(default_factory=list)      # in the population, never examined
    stray: list[str] = field(default_factory=list)        # examined, outside the declared population
    exempted: int = 0
    problems: list[str] = field(default_factory=list)     # why the row is red
    unrunnable: bool = False                              # a command exited non-zero: did not run
    capability: bool = False                              # a self-test proved the detector still detects
    detectors: dict = field(default_factory=dict)         # name -> members, when a requirement has several
    seam: list = field(default_factory=list)              # in neither this guard's scope nor its abutting one's
    outside: list = field(default_factory=list)           # in the structural superset, outside the marked set
    covered_by: dict = field(default_factory=dict)        # reach guards: layer -> how much of the bypass it covers
    note: str = ""                                        # reported, not judged
    reports: str = "count"                                # `floor` or `candidates` when the subject is weaker
    unread: int = 0                                       # candidates nobody opened
    declined: int = 0                                     # real matches deliberately not changed
    witnesses: int = 0                                    # named members confirmed present in the population                                # `floor` when the subject cannot resolve the unit


def read_members(root: Path, cmd: str, *, timeout: float = 120.0) -> Set_:
    """Run `cmd` in `root` and take one member per non-empty, non-comment line.

    No shell. A register is a tracked file in the project's own repo, at the
    same trust as its Makefile — but a shell also turns a member containing a
    space into two, which is a silent narrowing of exactly the kind measured
    here, so the argv is split once and passed through.
    """
    try:
        p = subprocess.run(shlex.split(cmd), cwd=root, capture_output=True, text=True, timeout=timeout)
    except (OSError, ValueError, subprocess.SubprocessError) as ex:
        return Set_(error=f"{cmd!r} could not run: {ex}")
    if p.returncode != 0:
        tail = (p.stderr or p.stdout or "").strip().splitlines()[-1:] or [""]
        return Set_(error=f"{cmd!r} exited {p.returncode}: {tail[0][:200]}")
    members = [l.strip() for l in p.stdout.splitlines()]
    return Set_(members=sorted({m for m in members if m and not m.startswith("#")}))


def judge_exemption(ex, root: Path, today: dt.date) -> str:
    """"" when the exemption stands; otherwise why it does not.

    One contract, in `qabench.warrant`: four files had written it out four
    times, and a contract with four copies is four contracts."""
    return warrant.judge(ex, root, today, subject="member", label="exemption")


def judge_transform(t, root: Path, run) -> str:
    """A normalisation step proves it did not gut the corpus, or it is not trusted.

    `before:` and `after:` each print ONE number — bytes, nodes, lines, whatever
    the transform is measured in — and `keeps:` is the fraction that must
    survive, stated because the shrink you intended is a fact you know and the
    shrink you did not is the defect.
    """
    if not isinstance(t, dict) or not t.get("before") or not t.get("after") or t.get("keeps") is None:
        return f"transform {t!r} needs `before:`, `after:` and `keeps:` (the fraction that must survive)"
    name = t.get("name", "transform")
    sizes = []
    for half in ("before", "after"):
        got = run(root, t[half])
        if got.error:
            return f"{name}: {half} could not run: {got.error}"
        try:
            sizes.append(float(got.members[0]))
        except (IndexError, ValueError):
            return f"{name}: {half} did not print a single number"
    before, after = sizes
    if before <= 0:
        return f"{name}: the corpus measured {before} BEFORE the transform — there was nothing to transform"
    kept = after / before
    if kept < float(t["keeps"]):
        return (f"{name} kept {kept:.0%} of the corpus ({after:.0f} of {before:.0f}), declared to keep at least "
                f"{float(t['keeps']):.0%} — a transform that guts its corpus reports EXACTLY like a clean tree, "
                "and every check downstream of it has been passing over nothing")
    return ""


NEAR_MISS_KEYS = ("cmd", "from", "was")


def judge_capability(cap: dict, root: Path, *, metric: str = "", stimulus: str = "",
                     measured_in: str = "") -> list[str]:
    """A capability proves the detector DISCRIMINATES, or it proves nothing.

    `fires:` is the positive. `silent:` is one or more REAL near-misses — a
    sentence, route, element or record that actually exists in the tree and
    that the detector's looser sibling DID fire on. Real, not invented: `from:`
    is a path that must exist, and `was:` quotes the thing itself, so the entry
    cannot drift into a synthetic case somebody wrote to be easy to pass.
    """
    out: list[str] = []
    detector = str(cap.get("detector") or "")
    if "::" not in detector:
        out.append(
            "capability names no `detector: path::function` — a capability whose detector is not a NAMED, "
            "CALLABLE FUNCTION cannot have a self-test, only a tautology. An inline `if stuck > baseline:` had a "
            "control asserting `3 > 0`, `not (1 > 1)` and `2 - 1 == 1`: true on an empty repository, green, "
            "and unable to fail. TESTING THE DETECTOR MEANS RUNNING THE DETECTOR — extract first")
    else:
        path, func = detector.split("::", 1)
        target = root / path
        if not target.exists():
            out.append(f"capability.detector {detector!r}: {path} does not exist")
        elif not re.search(r"^\s*(?:async\s+)?def\s+" + re.escape(func) + r"\s*\(",
                           target.read_text(encoding="utf-8", errors="replace"), re.M):
            out.append(f"capability.detector {detector!r}: no `def {func}(` in {path} — the detector is not a "
                       "named callable there, so the self-test cannot be running it")
    fires = cap.get("fires")
    if stimulus and isinstance(fires, list) and not any(
            isinstance(f, dict) and f.get("produced") for f in fires):
        out.append(
            f"this guard drives a stimulus ({stimulus}) and no known-positive names `produced:` — the effect "
            "the harness was shown to MAKE HAPPEN in the same run. A TEST THAT CANNOT MAKE THE MECHANISM FIRE "
            "CANNOT REPORT THAT IT DID NOT FIRE. A check for a loading indicator during a slow request ran two "
            "orderings, saw nothing twice and was nearly filed — and neither experiment could have produced an "
            "indicator, because the wrapper captured `window.fetch` at parse time and both available orderings "
            "put the delay on the wrong side of it. The null result was a property of the instrument")
    if metric and not cap.get("plausible"):
        out.append(
            f"this guard computes a metric ({metric}) and declares no `plausible:` range — the values the "
            "quantity can take in a WORKING system, outside which a reading is an INSTRUMENT FAULT rather than "
            "a finding. A contrast sweep reported 303 located failures, every one wrong, many at a ratio of "
            "EXACTLY 1.0 — foreground identical to background, invisible text, on a page somebody was reading. "
            "A review did not catch it, a mutation did not catch it, a control did not catch it: the "
            "IMPOSSIBILITY did. 747 measured and 5 failing once the translucent layers were composited")
    if metric and not measured_in:
        out.append(
            f"this guard computes a metric ({metric}) and names no `measured_in:` — A PERFORMANCE CEILING NAMES "
            "THE ENVIRONMENT IT WAS MEASURED IN, OR IT IS NOT A MEASUREMENT. A search latency of 1998 ms was "
            "staging, on a different instance from production, from one laptop on one network with one client's "
            "data volume, and the session declined to flip its rows green on it: a row that goes green on one "
            "laptop's reading of staging rests on the wrong measurement. AND A RATIO NAMES ITS GROUND: a token "
            "documented as 3.2:1 on white against a replacement at 5.0:1 on white was still wrong for its job, "
            "because the badges sit on a TINT rather than on white, where the replacement is 4.52:1 — passing "
            "by 0.02. Nobody measured badly; they measured against the wrong GROUND, which produces a "
            "reproducible, checkable, review-surviving number that does not answer the question. Any "
            "ratio-style assertion whose denominator is implicit is incomplete")
    if metric and isinstance(fires, list) and not any(
            isinstance(f, dict) and f.get("by_mutating") and f.get("moved") for f in fires):
        out.append(
            f"this guard computes a metric ({metric}) and no known-positive names `by_mutating:` and `moved:`. "
            "A metric must be shown able to PRODUCE A FAILING VALUE, and only a mutation of the property the "
            "requirement names shows that: lowering the threshold or feeding a synthetic value proves the "
            "arithmetic. A thumb-reach guard scored a button at 199%, a third of a page below the fold, as "
            "comfortably in reach — it knew 'too high' and could not express 'not on the screen at all', and "
            "moving a save bar from sticky to static left its count at 0 while ten of twenty-four screens moved "
            "their save to between 142% and 199%")
    if isinstance(fires, str):
        out.append("capability `fires:` must be a list of REAL known-positives, not a bare command. A detector is "
                   "written from a MEMORY of the instance it was built for, not from the instance: a verifier "
                   "that reported 16 of 23 dialogs cleared had the one independently-confirmed bypass in the "
                   "CLEARED list, and no amount of re-running or re-reading found that — checking the one case "
                   "whose answer was already known did")
        return out
    if not fires:
        out.append("capability lacks `fires:` — at least one REAL known-positive the detector must catch, best "
                   "of all the instance it was written for")
    silent = cap.get("silent")
    if not silent:
        out.append("capability has no `silent:` — REFUSED by name, like a population derived from naming. An "
                   "all-positives self-test proves a detector FIRES, never that it DISCRIMINATES (FRM-04: a "
                   "switch tested against the cases in the switch), and over an empty corpus it is "
                   "indistinguishable from a detector that fires on everything")
        return out
    if not isinstance(silent, list):
        return out + ["capability `silent:` must be a list of near-misses"]
    for n in list(silent) + (fires if isinstance(fires, list) else []):
        if not isinstance(n, dict):
            out.append(f"near-miss {n!r} is not a mapping with {', '.join(NEAR_MISS_KEYS)}")
            continue
        lacking = [k for k in NEAR_MISS_KEYS if not n.get(k)]
        if lacking:
            out.append(f"near-miss {n.get('was', n.get('cmd', '?'))!r} lacks {', '.join(lacking)}")
            continue
        if not (root / str(n["from"]).split("::")[0]).exists():
            out.append(f"near-miss {n['was']!r} says it comes from {n['from']!r}, which does not exist — a "
                       "near-miss must be REAL, out of the tree, not one written to be easy to pass")
    return out


def judge_pin(pinned, actual: int, shrunk, root: Path) -> str:
    """The ratchet. Exact, because only an exact pin can catch a narrowing."""
    if not isinstance(pinned, int):
        return (f"population.count is {pinned!r}, not a number — the population is {actual}; "
                "pin it, or a corpus can be narrowed back to a naming heuristic with nothing red")
    if actual == pinned:
        return ""
    if actual > pinned:
        return (f"the population grew {pinned} → {actual}; raise population.count in the same commit "
                "(a pin that lags cannot detect the fall back)")
    if not isinstance(shrunk, dict):
        return (f"the population FELL {pinned} → {actual} with no `shrunk:` — this is what re-keying a "
                "corpus on a naming heuristic looks like from the outside, AND what a MIGRATION looks like "
                "from the outside: if the codebase is adopting the recommended alternative and this corpus is "
                "keyed on the old syntactic form, the count falls as the code improves and reads as progress")
    lacking = [k for k in SHRUNK_KEYS if not shrunk.get(k)]
    if lacking:
        return f"the population fell {pinned} → {actual}; `shrunk:` lacks {', '.join(lacking)}"
    ev = shrunk["evidence"] if isinstance(shrunk["evidence"], list) else [shrunk["evidence"]]
    absent = [e for e in ev if not (root / str(e).split("::")[0]).exists()]
    if absent:
        return f"the population fell {pinned} → {actual}; `shrunk.evidence` does not exist: {', '.join(absent)}"
    return (f"the population fell {pinned} → {actual} and `shrunk:` explains it — set population.count to "
            f"{actual}. Before you do: if the fall is a MIGRATION, ask what this population becomes when the "
            "migration finishes. A corpus keyed on the form being migrated AWAY from shrinks to nothing exactly "
            "while the work that was meant to make it meaningful is happening")


def judge(spec: dict, root: Path, today: dt.date, *, run=read_members, surfaces=(), register=()) -> Row:
    """One guard: run both sides, compare by member, apply the four rules."""
    row = Row(id=str(spec.get("id") or "?"), check=str(spec.get("check") or ""),
              claims=str(spec.get("claims") or ""),
              derived_from=str((spec.get("population") or {}).get("derived_from") or "?"),
              undecided=str(spec.get("undecided") or ""), unit=str(spec.get("unit") or ""))
    if not spec.get("id"):
        row.problems.append("a guard with no `id:` — a finding nobody can look up")
    if not row.check:
        row.problems.append("no `check:` — every guard serves one of C1–C12, or it is runtime with no owner")
    if not row.claims:
        row.problems.append("no `claims:` — the one sentence the population is the population OF")
    claims_faculty = str(spec.get("claims_faculty") or "")
    pop_faculty = str((spec.get("population") or {}).get("faculty") or "")
    if not claims_faculty or not pop_faculty:
        row.problems.append(
            "a guard names `claims_faculty:` (the faculty the claim is ABOUT) and `population.faculty:` (the "
            "faculty its members are FOUND BY). Without both, the circular case is undetectable")
    elif claims_faculty == pop_faculty:
        row.problems.append(
            f"the population is found by the same faculty the claim is about ({pop_faculty!r}) — the corpus "
            "CANNOT CONTAIN A FAILING MEMBER, so the check is decorative however carefully it is written. "
            "ACC-04 tabbed to find controls and could not find an unfocusable one; the same shape is querying "
            "rendered pages for empty states, enumerating registered routes to check routes are registered, or "
            "reading the rows a query returns to check the query returns the right rows. Derive the population "
            "through a DIFFERENT faculty and make the finding the difference")
    for d in ((spec.get("subject") or {}).get("detectors") or []):
        if isinstance(d, dict) and claims_faculty and str(d.get("faculty") or "") == claims_faculty:
            row.problems.append(
                f"detector {d.get('name')!r} is found by the claim's own faculty ({claims_faculty!r}) — two "
                "detectors sharing a faculty can cover each other perfectly and both be blind, so a complete "
                "union is necessary and not sufficient")
    if (spec.get("population") or {}).get("observed_from") and not spec.get("capability"):
        row.problems.append(
            "this population is observed from an environment and the guard declares no `capability:` — a guard "
            "whose pass/fail turns on a count of rows IT DID NOT CREATE is environment-coupled. A floor derived "
            "from a laptop loaded with a customer extract read as three refusals; the seeded CI database, whose "
            "ids start elsewhere, made it red while saying nothing about the code. The discriminating case must "
            "be one the guard BUILDS and therefore finds everywhere")
    if surfaces:
        declared = spec.get("surfaces")
        if not isinstance(declared, dict):
            row.problems.append(
                "no `surfaces:` — THE DEFAULT POPULATION IS THE SURFACE THE AUTHOR WORKS IN. Name every surface "
                f"this project has ({', '.join(surfaces)}) as {{covered_by: <path prefix>}} or "
                "{excluded: <reason>}, so leaving one out is an act rather than an oversight")
        else:
            for name in surfaces:
                if name not in declared:
                    row.problems.append(
                        f"surface {name!r} is neither covered nor excluded. A perfectly derived population of "
                        "the wrong directory is still wrong, and the surfaces left out are systematically the "
                        "ones where CUSTOMERS meet the product")
            for name, how in declared.items():
                if name not in surfaces:
                    row.problems.append(f"surface {name!r} is not one this project declares ({', '.join(surfaces)})")
                elif not isinstance(how, dict) or not (how.get("covered_by") or how.get("excluded")):
                    row.problems.append(
                        f"surface {name!r} must be {{covered_by: <path prefix>}} or {{excluded: <reason>}}. A "
                        "sentence is not evidence: a guard declaring four surfaces covered while its population "
                        "command read templates/admin only PASSED, and the false claim was invisible")
    cites = spec.get("cites")
    reads = (spec.get("subject") or {}).get("reads")
    if cites or reads:
        if not cites or not reads:
            row.problems.append("a guard declaring one of `cites:` / `subject.reads:` declares both — what the "
                                "claim already rests on, and what the verification looks at")
        elif set(map(str, reads)) <= set(map(str, cites)):
            row.problems.append(
                "the verification reads nothing the claim does not already cite — a paraphrase checked against "
                "its own source always agrees. LST-07's claim was restated honestly and verified against the "
                "row's own five paging tables; a browser then found 15 unpaged per-client sub-lists, a category "
                "outside the population entirely. Verify against the SURFACE a person touches")
    if not spec.get("unit"):
        row.problems.append(
            "no `unit:` — what ONE MEMBER IS (a site, a dialog, a route, a template). A guard's unit must be "
            "the unit the requirement quantifies over, and a coarser one is invisible by construction: a census "
            "asking whether each FILE containing a refusal also contained a focus call stayed GREEN after two of "
            "three focus calls were deleted, because the third still matched somewhere in the same file")
    if not spec.get("undecided"):
        row.problems.append(
            "no `undecided:` — one sentence for what this guard does NOT judge. ACT-05 swept 146 dialogs "
            "honestly and its population was dialogs; saves fired from a PAGE were never in it, and nothing "
            "in a correct, well-written row said so. A boundary nobody states is a boundary nobody can "
            "challenge, and it is the one field a second method arriving at the same wrong answer cannot "
            "accidentally reproduce")

    kind = str(spec.get("kind") or "sweep")
    if kind not in ("sweep", "reach"):
        row.problems.append(f"kind must be `sweep` or `reach`, not {kind!r}")
    proves_helper = spec.get("proves_helper")
    if proves_helper:
        by_id = {str(g.get("id")): g for g in register if isinstance(g, dict)}
        pair = by_id.get(str(spec.get("paired_with") or ""))
        if not pair or str(pair.get("kind") or "sweep") != "reach":
            row.problems.append(
                f"this guard proves the contract of {proves_helper!r} and names no `paired_with:` REACH guard "
                "saying what fraction of the eligible call sites reach it. A CONTRACT PROVEN ON A MECHANISM "
                "NOBODY CALLS IS THE MOST EXPENSIVE KIND OF GREEN: apiFetch reports every failure by default "
                "and 198 of 870 sites call it; AnatEmpty refuses a null action unless you say why and 20 sites "
                "use it against 59 hand-rolled. A tracker read 66 rows implemented, and every one of them was "
                "TRUE OF THE HELPER")
    complement = spec.get("complement")
    if kind == "reach":
        purpose = str(spec.get("for") or "")
        paired = spec.get("paired_with")
        by_id = {str(g.get("id")): g for g in register if isinstance(g, dict)}
        if purpose not in ("property", "holding"):
            row.problems.append(
                "a `reach` guard declares `for:` — `property` (measuring something the fix must PRESERVE) or "
                "`holding` (bounding a known-broken mechanism until it is replaced). BOTH LOOK IDENTICAL IN "
                "THE FILE, a shrink-only count with a ceiling, AND THEY HAVE OPPOSITE CORRECT ENDINGS: a "
                "property ratchet keyed on the old shape empties and goes green while the property is "
                "unmeasured, which is the failure; a holding ratchet SHOULD empty when the mechanism is "
                "replaced, and its end state is DELETION — leaving it green is the error, not the emptying")
        elif purpose == "property":
            if not paired:
                row.problems.append(
                    "a `for: property` reach guard names `paired_with:` — the id of a PROPERTY guard whose "
                    "count moves the OPPOSITE way. A RATCHET KEYED ON THE SHAPE OF THE OLD CODE EMPTIES AS THE "
                    "FIX LANDS, AND AN EMPTY RATCHET IS GREEN: three ceilings over 672 raw call sites, every "
                    "number true and every ceiling shrink-only, all three emptying as the migration proceeds. "
                    "The repair is not a replacement but a FOURTH bucket keyed on the property, which RISES "
                    "when a careless migration lowers the other three. Ask of any new ratchet: WHAT DOES THIS "
                    "COUNT WHEN THE WORK SUCCEEDS?")
            elif str(paired) not in by_id:
                row.problems.append(f"`paired_with: {paired}` names no guard in this register")
            elif str((by_id[str(paired)].get("kind") or "sweep")) == "reach":
                row.problems.append(
                    f"`paired_with: {paired}` is another REACH guard — two coverage ratchets empty together. "
                    "The pair must be a PROPERTY guard, which moves the opposite way")
        elif not spec.get("ends_when"):
            row.problems.append(
                "a `for: holding` reach guard names `ends_when:` — what makes this ceiling DELETABLE. It "
                "exists only to stop a number growing while a mechanism is known-broken, so when the real fix "
                "lands the honest move is to delete it rather than invent a property bucket beside it. "
                "Without that sentence a holding ratchet sits green over nothing and is read as a measurement")
    if kind == "reach" and not complement:
        row.problems.append(
            "a `reach` guard MUST declare `complement:` — REFUSED by name, like a population derived from "
            "naming. A reach number is a DENOMINATOR, and a denominator with no coverage-by-other-means "
            "measurement is a verdict without a population, which is the thing this module exists for. "
            "Measured on anat: apiFetch reaches 198 call sites and 783 bypass it, which reads as 20% and would "
            "have started a rewrite — but three other global fetch wrappers give every raw call the loading "
            "indicator, session activity, the CSRF header and the 401 bounce, 538 of them check status "
            "themselves and 297 report a failure to a person. The actionable number was 109, not 783 — and a "
            "browser later showed even the 538 was wrong, because `res.ok` only exists if the promise RESOLVED "
            "and a network rejection never reaches it. Hence `proven_by:` below: a coverage claim is a claim "
            "like any other")
    transforms = spec.get("transform") or []
    cap_spec = spec.get("capability") or {}
    pop_spec = spec.get("population") or {}
    sub_spec = spec.get("subject") or {}
    derived = str(pop_spec.get("derived_from") or "")
    superset = pop_spec.get("superset") or {}
    if derived in MARKER_FAMILY and superset.get("cmd") and superset.get("describes"):
        derived = ""                      # permitted, and measured against the superset below
    elif derived in REFUSED:
        row.problems.append(f"population.derived_from: {derived!r} is refused — {REFUSED[derived]}")
    elif derived and derived not in DERIVATIONS:
        row.problems.append(f"population.derived_from must be one of {', '.join(DERIVATIONS)}, not {derived!r}")
    detectors = sub_spec.get("detectors")
    if detectors and sub_spec.get("cmd"):
        row.problems.append("a subject names `cmd` OR `detectors`, not both")
        return row
    if not (pop_spec.get("cmd") or pop_spec.get("cmd_from")) or not (sub_spec.get("cmd") or detectors):
        row.problems.append("a guard names both a population.cmd and a subject.cmd (or subject.detectors), or it "
                            "is a claim about itself")
        return row

    if cap_spec:
        problems = judge_capability(cap_spec, root, metric=str(spec.get("metric") or ""),
                                    stimulus=str(spec.get("stimulus") or ""),
                                    measured_in=str(spec.get("measured_in") or ""))
        if problems:
            row.problems.extend(problems)
            return row
        for cmd in [n["cmd"] for n in cap_spec["fires"]] + [n["cmd"] for n in cap_spec["silent"]]:
            proof = run(root, cmd)
            if proof.error:
                row.problems.append(f"the capability self-test did not pass: {proof.error} — a detector whose "
                                    "self-test cannot run is not proven, whatever its live scan reports")
                row.unrunnable = True
                return row
        row.capability = True

    for t in transforms:
        problem = judge_transform(t, root, run)
        if problem:
            row.problems.append(problem)
            row.unrunnable = "could not run" in problem or "did not print" in problem
            return row

    # A command READ from the manifest rather than carried as a copy. A guard
    # holding its own copy of the manifest's string passes today and drifts the
    # next time the manifest line changes — D4 one file over, where the copy
    # runs, passes, and is no longer the command anybody consumes.
    if pop_spec.get("cmd_from"):
        mdoc = (yaml.safe_load((root / "qa" / "manifest.yml").read_text(encoding="utf-8"))
                if (root / "qa" / "manifest.yml").exists() else {}) or {}
        node = mdoc
        for part in str(pop_spec["cmd_from"]).split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if not isinstance(node, str) or not node.strip():
            row.unrunnable = True
            row.problems.append(f"population.cmd_from: {pop_spec['cmd_from']!r} names no command in the manifest")
            return row
        pop_spec = {**pop_spec, "cmd": node}
    pop = run(root, pop_spec["cmd"])
    # ONE REQUIREMENT, SEVERAL DETECTORS: the population is the REQUIREMENT'S,
    # and what has to be asserted is that the detectors' corpora COVER it. Two
    # corpora that are each honestly reported can leave a hole neither reports,
    # and nothing in either one's output hints at it — STA-02 was guarded by a
    # sweep of AnatEmpty calls and a ratchet on hand-rolled markup, both sound,
    # and a list dropping a sentence into a plain table cell was neither.
    if detectors:
        named = [(str(d.get("name") or f"#{i}"), d.get("cmd")) for i, d in enumerate(detectors)]
        if any(not c for _, c in named):
            row.problems.append("every detector names a `cmd`")
            return row
        results = {n: run(root, c) for n, c in named}
        first_error = next((r.error for r in results.values() if r.error), "")
        by_detector = {n: set(r.members) for n, r in results.items()}
        sub = Set_(sorted(set().union(*by_detector.values())) if by_detector else [], first_error)
    else:
        by_detector = {}
        sub = run(root, sub_spec["cmd"])
    if pop.error or sub.error:
        row.unrunnable = True
        row.problems.append(pop.error or sub.error)
        return row

    row.population, row.subject = len(pop.members), len(sub.members)
    row.reports = str(sub_spec.get("reports") or "count")
    if row.reports not in ("count", "floor", "candidates"):
        row.problems.append(f"subject.reports is {row.reports!r}; it is `count`, `floor` or `candidates`")
    elif row.reports == "candidates":
        read = sub_spec.get("read")
        if not isinstance(read, int):
            row.problems.append(
                "`reports: candidates` names `read:` — how many candidates were OPENED. When a pattern stands "
                "in for a property the count is the candidate set, not the finding: 27 matched a commit-verb "
                "id, all 27 were opened, and FOUR were different acts correctly carrying different words. "
                "Over-returning is visible only if somebody opens each one, and it presents AS A FINDING")
        else:
            row.unread = max(0, row.subject - read)
        declined = sub_spec.get("declined")
        if declined and not sub_spec.get("declined_why"):
            row.problems.append(
                f"{declined} candidates are DECLINED and `declined_why:` says nothing. A site where the match "
                "is real, the substitution is available and the change is still not worth making is a third "
                "category beside confirmed and rejected — and without the sentence it is indistinguishable "
                "from a site nobody examined. A change with no benefit and three costs is not a change, but "
                "only the reason makes that legible to the next sweep")
        row.declined = int(declined or 0)
    row.detectors = {n: len(m) for n, m in by_detector.items()}
    exemptions = spec.get("exemptions") or []
    for ex in exemptions:
        problem = judge_exemption(ex, root, today)
        if problem:
            row.problems.append(problem)
    excused = {str(e.get("member")) for e in exemptions if isinstance(e, dict) and not judge_exemption(e, root, today)}

    if not pop.members:
        if row.capability:
            # Reported, not judged. The detector is proven on a corpus that
            # cannot go away, so a live scan of nothing is a fact about the
            # tree rather than a verdict about the guard.
            row.note = (f"live corpus is EMPTY; capability proven by {len(cap_spec['fires'])} known-positive(s) "
                        f"against "
                        f"{len(cap_spec['silent'])} real near-miss(es). Nothing to compare, and that is "
                        "allowed here precisely because the detector is proven elsewhere")
            return row
        row.unrunnable = True
        row.problems.append(f"{pop_spec['cmd']!r} enumerated NOTHING — a population of nothing cannot show that "
                            "anything was swept. Declare a `capability:` self-test on a corpus that cannot go "
                            "empty, exclude the guard by declaration, or fix the enumeration")
        return row

    if superset.get("cmd") and superset.get("describes"):
        whole = run(root, superset["cmd"])
        if whole.error:
            row.unrunnable = True
            row.problems.append(whole.error)
            return row
        outside = [m for m in whole.members if m not in set(pop.members)]
        row.outside = outside
        if outside:
            row.problems.append(
                f"{len(outside)} of {len(whole.members)} {superset['describes']} are OUTSIDE the declared "
                f"population entirely: " + ", ".join(outside[:8])
                + ". A marker is applied by the fix, so a denominator made of it can only ever measure the fix — "
                "a case that never entered the conversion is not a survivor of it, it was never in it")

    # THE SURFACE CLAIM IS CHECKED AGAINST WHAT THE POPULATION ACTUALLY READ.
    # Declaring a surface covered is a sentence; a prefix with no member under
    # it in the population's own output is a refusal.
    for name, how in (spec.get("surfaces") or {}).items():
        prefix = how.get("covered_by") if isinstance(how, dict) else None
        if prefix and not any(str(prefix) in m for m in pop.members):
            row.problems.append(
                f"surface {name!r} is declared covered by {prefix!r} and the population contains NO member under "
                "it — the declaration is a sentence and the command is the evidence; they disagree")

    if str(spec.get("claims_shape") or "presence") == "absence":
        unlocatable = [m for m in pop.members if "::" not in m][:8]
        if unlocatable:
            row.problems.append(
                "this guard claims an ABSENCE and its members name no anchor: " + ", ".join(unlocatable)
                + ". AN ABSENCE HAS NO LINE NUMBER — a file-level absence is unactionable on any file holding "
                "more than one instance of the thing, and the session handed such a list could neither fix it "
                "nor dismiss it, because declaring them false positives would be the same error as fixing them "
                "blindly. Report `path::anchor`, naming the element the thing was expected near")
            return row

    abuts, jointly = spec.get("abuts"), spec.get("jointly") or {}
    if abuts or jointly:
        by_id = {str(g.get("id")): g for g in register if isinstance(g, dict)}
        other = by_id.get(str(abuts))
        if not other or not jointly.get("cmd") or not jointly.get("describes"):
            row.problems.append(
                "`abuts:` names a guard in this register and comes with `jointly: {cmd, describes}` — the "
                "population the PAIR is responsible for. A unit sweep checking that required fields are MARKED "
                "and an e2e sweep checking they are ASSOCIATED were each correct in their own scope, and 78 "
                "unnamed controls lived in the space both excluded: not a dishonest guard anywhere, a SEAM "
                "between two honest ones")
            return row
        theirs = run(root, ((other.get("subject") or {}).get("cmd")) or "")
        whole = run(root, jointly["cmd"])
        if theirs.error or whole.error:
            row.unrunnable = True
            row.problems.append(theirs.error or whole.error)
            return row
        covered = set(sub.members) | set(theirs.members)
        seam = [m for m in whole.members if m not in covered]
        row.seam = seam
        if seam:
            row.problems.append(
                f"{len(seam)} of {len(whole.members)} {jointly['describes']} fall in the SEAM between this "
                f"guard and {abuts}: " + ", ".join(seam[:8])
                + ". Each guard is correct in its own scope and the pair does not meet")

    for w in (pop_spec.get("witness") or []):
        if not isinstance(w, dict) or not (w.get("member") or w.get("matching")) or not w.get("why"):
            row.problems.append(
                f"witness {w!r} names a `member` (or `matching:`, a pattern at least one member must satisfy) "
                "and the `why` that makes it the witness")
            continue
        if w.get("matching"):
            try:
                hit = any(re.search(str(w["matching"]), m) for m in pop.members)
            except re.error as ex:
                row.problems.append(f"witness pattern {w['matching']!r} does not compile: {ex}")
                continue
            if not hit:
                row.problems.append(
                    f"WITNESS KIND ABSENT: no member matches {w['matching']!r}, and that kind is why this guard "
                    f"exists ({w['why']}). A size cannot express 'contains this kind of thing' — a floor of 30 "
                    "on a citation guard is satisfied perfectly by thirty citations all carrying the prefix, "
                    "while the prefixless ones the widening existed to include are all gone")
            else:
                row.witnesses += 1
            continue
        if not any(str(w["member"]) in m for m in pop.members):
            row.problems.append(
                f"WITNESS ABSENT: {w['member']!r} is not in the population, and it is why this guard exists "
                f"({w['why']}). A size floor cannot express this — a sweep judging 7,426 elements against a "
                "floor of 6,000 loses the four nodes it was built for and still passes comfortably. A size "
                "ratchet is directional and therefore blind in the direction that looks like success; A NAMED "
                "WITNESS HAS NO DIRECTION")
        else:
            row.witnesses += 1

    missing = [m for m in pop.members if m not in set(sub.members)]
    row.exempted = len([m for m in missing if m in excused])
    row.missing = [m for m in missing if m not in excused]
    row.stray = [m for m in sub.members if m not in set(pop.members)]
    if kind == "reach" and not sub.members and pop.members:
        # Checked BEFORE the complement partition, which returns early when the
        # residue is empty — and a remedy nothing uses has an empty residue by
        # construction, so the inert case would have been swallowed there.
        row.problems.append(
            f"THE REMEDY IS INERT: zero of {row.population} sites use it. A token was defined with a comment "
            "naming its requirement and documenting 5.0:1, and used in ZERO rules, while fourteen selectors "
            "still set the inaccessible one — somebody found the defect, computed the numbers, wrote the fix "
            "and never wired it, and nothing noticed because every guard in reach asked whether the remedy "
            "EXISTS rather than whether anything CONSUMES it")
        return row
    if kind == "reach" and complement and row.missing:
        # BYPASSING A HELPER IS NOT THE SAME AS BEING UNCOVERED. The complement
        # is partitioned by what else covers it, and only the residue is a
        # finding. Reporting the bypass count alone is how a mostly-fine
        # codebase acquires a rewrite ticket.
        residue, layers = list(row.missing), {}
        for layer in complement:
            if not isinstance(layer, dict) or not layer.get("cmd") or not layer.get("name"):
                row.problems.append(f"every `complement:` layer names a `name` and a `cmd`: {layer!r}")
                return row
            if not layer.get("proven_by"):
                row.problems.append(
                    f"complement layer {layer['name']!r} has no `proven_by:` — a command showing it actually "
                    "covers a real member. A layer counting 538 call sites as handling failure because they "
                    "check `res.ok` was wrong: res.ok only exists if the promise RESOLVED, and a network "
                    "rejection throws before it. The population was right and the BUCKET BOUNDARY was wrong, so "
                    "a coverage claim needs the same proof a capability does")
                return row
            got = run(root, layer["cmd"])
            if got.error:
                row.unrunnable = True
                row.problems.append(got.error)
                return row
            covered = set(got.members)
            layers[layer["name"]] = len([m for m in residue if m in covered])
            residue = [m for m in residue if m not in covered]
        row.covered_by = layers
        row.missing = residue
        row.note = (f"reach {row.subject}/{row.population}; of the {row.population - row.subject} that bypass it, "
                    + ", ".join(f"{n} covers {c}" for n, c in layers.items())
                    + f" — leaving {len(residue)} covered by NOTHING, which is the actionable number")
        if not residue:
            row.problems = [p for p in row.problems if "never examined" not in p]
            return row
        row.problems = [p for p in row.problems if "never examined" not in p]
        row.problems.append(f"{len(residue)} of {row.population} are covered by neither the helper nor any "
                            f"declared layer: " + ", ".join(residue[:8]))
    if by_detector and row.missing:
        row.note = ("no detector covers: " + ", ".join(row.missing[:8])
                    + " — each corpus here is honestly reported and the UNION is still a proper subset of the "
                      "requirement. A guard defined as 'anything not the approved way' grows a hole the day "
                      "somebody approves another way")
    # AN EXEMPTION MUST BE SHOWN ABLE TO BITE, and the two ways it cannot are
    # different findings with different repairs.
    stale_examined = sorted(m for m in excused if m in set(pop.members) and m not in set(missing))
    never_a_candidate = sorted(m for m in excused if m not in set(pop.members))

    if not sub.members:
        row.problems.append(f"the guard examined NOTHING against a population of {row.population} — a detector "
                            "matching nothing is indistinguishable from a clean tree (FRM-10)")
    if row.missing:
        shown = ", ".join(row.missing[:8]) + (f" … +{len(row.missing) - 8}" if len(row.missing) > 8 else "")
        row.problems.append(f"{len(row.missing)} of {row.population} never examined: {shown}")
    if row.stray:
        shown = ", ".join(row.stray[:8]) + (f" … +{len(row.stray) - 8}" if len(row.stray) > 8 else "")
        row.problems.append(f"{len(row.stray)} examined but outside the declared population — the population "
                            f"expression is narrower than the guard: {shown}")
    for m in stale_examined:
        row.problems.append(f"exemption {m!r} is stale: the guard now examines it — delete the entry")
    for m in never_a_candidate:
        row.problems.append(
            f"exemption {m!r} enforces NOTHING: it is not in the population at all, so the guard would never "
            "have judged it. Delete it and the guard does not change — an entry with the shape of a considered "
            "decision and the force of a blank line. Either it is already excluded upstream, where the honest "
            "record belongs, or it covers a case that no longer exists")
    observed = pop_spec.get("observed_from")
    if observed:
        row.note = ((row.note + " · ") if row.note else "") + (
            f"population observed from {observed}; its size ({row.population}) is INFORMATION, not a gate — a "
            "floor counted from what an environment happens to contain is not a floor, and the discrimination "
            "comes from the capability's constructed case. THIS GUARD BELONGS IN A REPORTING TIER THAT IS "
            "ALLOWED TO VARY, never in a gating one: an execution-determined population is unstable in one "
            "direction and too small in the other, and both read as clean. If a RATCHET is wanted here, key it "
            "on what the CODE determines — fourteen selectors is fourteen selectors whatever the data does")
    else:
        pin = judge_pin(pop_spec.get("count"), row.population, pop_spec.get("shrunk"), root)
        if pin:
            row.problems.append(pin)
    return row


def run_population(root: Path, cfg: dict, *, today: dt.date | None = None, run=read_members) -> dict:
    today = today or dt.date.today()
    reg_path = root / cfg["register"]
    doc = yaml.safe_load(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else None
    guards = (doc or {}).get("guards") or []
    surfaces = tuple(cfg.get("surfaces") or ())
    rows = [judge(g, root, today, run=run, surfaces=surfaces, register=guards) for g in guards]

    # The completeness half. A check the manifest calls `implemented` with no
    # registered guard is the state every row above was found in: evidence that
    # exists, and no statement of what it claims to cover.
    mpath = root / "qa" / "manifest.yml"
    manifest = (yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}) or {}
    implemented = sorted(cid for cid, spec in (manifest.get("checks") or {}).items()
                         if isinstance(spec, dict) and spec.get("status") == "implemented")
    covered = {r.check for r in rows}
    return {
        "register": str(reg_path),
        "guards": len(rows),
        "rows": [r.__dict__ for r in rows],
        "red": [r.__dict__ for r in rows if r.problems],
        "unrunnable": [r.__dict__ for r in rows if r.unrunnable],
        "unregistered": [c for c in implemented if c not in covered],
    }


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def run(argv: list[str], *, today: dt.date | None = None) -> int:
    root = Path(_arg(argv, "--repo", ".")).resolve()
    mpath = root / "qa" / "manifest.yml"
    doc = yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    cfg = (doc or {}).get("population")
    if not cfg or not cfg.get("register"):
        print(f"no `population:` block with a `register:` in {mpath} — no guard states the population it "
              "claims over (exit 3)", file=sys.stderr)
        return 3
    if not (root / cfg["register"]).exists():
        print(f"{cfg['register']} does not exist — nothing measured (exit 3)", file=sys.stderr)
        return 3
    out = run_population(root, cfg, today=today, run=read_members)
    if "--json" in argv:
        print(json.dumps(out, indent=1, ensure_ascii=False))
    else:
        print(f"POPULATION — {out['guards']} guards in {out['register']}")
        for r in out["rows"]:
            mark = "RED " if r["problems"] else "ok  "
            print(f"  {mark}{r['id']:38} {r['check']:4} {r['subject']:>5}/{r['population']:<5} swept"
                  + f"  [{r['derived_from']}]"
                  + ("  [capability proven]" if r["capability"] else "")
                  + (f"   ({r['exempted']} exempted)" if r["exempted"] else ""))
            if r["reports"] == "candidates":
                print(f"       these are CANDIDATES, not findings — {r['unread']} of {r['subject']} were never "
                      "opened, and a pattern standing in for a property fabricates as readily as it misses"
                      + (f"; {r['declined']} declined with a reason" if r["declined"] else ""))
            if r["reports"] == "floor":
                print(f"       these are a FLOOR, NOT A COUNT — the subject cannot resolve to one {r['unit']}, "
                      "so what it missed is invisible in its own output")
            if r["undecided"]:
                print(f"       does not judge: {r['undecided']}")
            if r["note"]:
                print(f"       {r['note']}")
            for p in r["problems"]:
                print(f"       {p}")
        for c in out["unregistered"]:
            print(f"  RED  {c} is `implemented` in the manifest and no guard says what population it covers")
    if not out["guards"]:
        print("the register names no guards — treat as did not run (exit 3)", file=sys.stderr)
        return 3
    if out["unrunnable"]:
        print(f"{len(out['unrunnable'])} guard(s) could not run — did not run, not clean (exit 3)", file=sys.stderr)
        return 3
    return 1 if (out["red"] or out["unregistered"]) else 0
