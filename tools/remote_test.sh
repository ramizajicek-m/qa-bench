#!/bin/sh
# The kit's own tests, on the gate host, under that machine's heavy-run lock.
#
# WHY. The tests drive real browsers, and a verdict that depends on how loaded
# the machine was is not a verdict: on 2026-11-02 a release failed one
# sideways-scroll test on the working laptop at load 53-64 and passed it 3 of 3
# when rerun, with no output kept to say which. So the release check runs on
# the gate host (KIT_TEST_HOST, default new-laptop), one heavy run at a time,
# with -rA so every test's outcome is in the log.
#
#   tools/remote_test.sh [pytest args]       # the committed HEAD; uncommitted work is not sent
#
# The commit travels as a git bundle (the host's keychain cannot be read over
# ssh, so it cannot fetch the private remote). Its venv is the kit's own,
# ~/.qabench/kit-venv-<kit>, with playwright pinned to a build whose browsers
# the host already has (KIT_TEST_PLAYWRIGHT): a browser the host lacks is a
# skip the test names, never a download from here. Exit code: pytest's.
#
# The run is DETACHED on the host and its whole output kept there
# (~/.qabench/kit-test-<run>.log): on 2026-11-02 the first run lost its last
# 5% and every -rA line when the ssh link dropped, and the run died with it.
# This side follows the log, reconnects when the link drops, and exits with
# the status the run wrote — never with ssh's own 255.
#
# EVERY RUN HAS ITS OWN tree, log and status (RUN, below). On 2026-11-02 two
# runs of one kit shared them: one rewrote the tree and the log under the
# other, and a release read the other run's exit 5. And a run that collected
# no tests (pytest's 5) is DID NOT RUN, exit 3 — never a red, never a green.
set -eu
HOST="${KIT_TEST_HOST:-new-laptop}"
TOP="$(git rev-parse --show-toplevel)"
KIT="$(basename "$(git -C "$TOP" rev-parse --path-format=absolute --git-common-dir | sed 's#/\.git$##')")"
SHA="$(git -C "$TOP" rev-parse HEAD)"
RUN="$KIT-$(date -u +%Y%m%dT%H%M%S)-$$"
BUNDLE="$(mktemp -d)/kit.bundle"
git -C "$TOP" bundle create -q "$BUNDLE" HEAD
# The link to the host drops now and then (2026-11-02, twice in an hour): retried, then refused.
sent=""
for attempt in 1 2 3; do
  scp -q -o BatchMode=yes -o ConnectTimeout=20 "$BUNDLE" "$HOST:/tmp/$RUN.bundle" && { sent=1; break; }
  sleep 15
done
[ -n "$sent" ] || { echo "kit tests DID NOT RUN: could not copy the commit to $HOST" >&2; exit 3; }
rm -rf "$(dirname "$BUNDLE")"
echo "kit tests: $KIT at $SHA on $HOST, run $RUN"
SSH="ssh -o BatchMode=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=4"
# ssh joins its arguments into one remote command line, so each is quoted here: `-k "a or b"` stays one word.
q=""
for a in "$KIT" "$SHA" "${KIT_TEST_PLAYWRIGHT:-1.64.1}" "${LAND_SESSION:-kit-test}" "$RUN" "$@"; do
  q="$q '$(printf '%s' "$a" | sed "s/'/'\\\\''/g")'"
done
$SSH "$HOST" "sh -s --$q" <<'REMOTE'
set -eu
export PATH="/opt/homebrew/bin:$PATH"
kit=$1 sha=$2 pw=$3 who=$4 run=$5; shift 5
bundle=/tmp/$run.bundle
dir="$HOME/Projects/worktrees/kit-test-$run"
log="$HOME/.qabench/kit-test-$run.log"; status="$log.status"
mkdir -p "$HOME/.qabench"
# Runs older than a day are swept: their trees and logs, never a live one (its status is not yet written).
find "$HOME/.qabench" -maxdepth 1 -name "kit-test-$kit-*.log.status" -mtime +1 2>/dev/null | while read -r st; do
  old=$(basename "$st" .log.status); rm -rf "$HOME/Projects/worktrees/$old" "$HOME/.qabench/$old.log" "$st"
done
git clone -q "$bundle" "$dir"
rm -f "$bundle"
cd "$dir"
git -c advice.detachedHead=false checkout -q --force "$sha"
venv="$HOME/.qabench/kit-venv-$kit"
[ -x "$venv/bin/python" ] || python3.13 -m venv "$venv"
"$venv/bin/pip" install -q --disable-pip-version-check ".[dev,print]" "playwright==$pw"
echo "kit tests: $(git rev-parse --short HEAD) in $dir, playwright $pw, load $(uptime | sed 's/.*load averages*: //')" > "$log"
# The session name is for the holder line of the lock only: the tests read those variables themselves.
nohup sh -c 'who=$1 venv=$2 kit=$3 status=$4; shift 4
env PYTHONPATH=. QABENCH_SESSION="$who" "$venv/bin/python" -m qabench heavy --name "kit tests $kit" -- \
    env -u QABENCH_SESSION -u LAND_SESSION "$venv/bin/python" -m pytest tests -rA -q -p no:cacheprovider "$@"
rc=$?
if [ "$rc" = 5 ]; then echo "kit tests DID NOT RUN: pytest collected no tests (its exit 5) — not a pass, not a red"; rc=3; fi
echo "$rc" > "$status"' \
    kit-test "$who" "$venv" "$kit" "$status" "$@" >> "$log" 2>&1 < /dev/null &
REMOTE
# Follow the log until the run writes its status. A dropped link reconnects and prints the log again
# from its start, so nothing is lost between the drop and the reconnect.
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  $SSH "$HOST" "log=\$HOME/.qabench/kit-test-$RUN.log; tail -n +1 -f \"\$log\" & t=\$!; while [ ! -s \"\$log.status\" ]; do sleep 5; done; sleep 1; kill \$t" && break
  echo "kit tests: lost the link to $HOST (attempt $attempt); the run goes on there — reconnecting, the log again from its start" >&2
  sleep 15
done
rc=$($SSH "$HOST" "cat \$HOME/.qabench/kit-test-$RUN.log.status" 2>/dev/null || echo "")
[ -n "$rc" ] || { echo "kit tests DID NOT finish as far as this side can see — the log is $HOST:~/.qabench/kit-test-$RUN.log" >&2; exit 3; }
exit "$rc"
