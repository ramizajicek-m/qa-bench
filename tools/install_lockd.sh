#!/bin/sh
# Installs `qabench lockd` on the gate host (KIT_TEST_HOST, default new-laptop) as a LaunchAgent, kept alive,
# from this checkout's committed HEAD — then proves it from inside a container.
#
#   tools/install_lockd.sh
#
# WHY. The host's Docker runners cannot see its flock; `qabench heavy` in a container asks this service instead
# (qabench/lockd.py). Unreachable is DID NOT RUN, so once a project wraps its container steps, this service is
# what they need running. It binds 127.0.0.1:7461: Docker Desktop's host.docker.internal reaches the host's
# loopback, and nothing off the machine can.
#
# The source is a git bundle (the host cannot fetch the private remote), cloned per commit under
# ~/.qabench/lockd-src-<sha> with ~/.qabench/lockd-src pointing at the live one. Its venv holds pyyaml only:
# lockd and heavy start on the standard library and yaml.
#
# A RESTART CUTS OFF EVERY RUN HELD OR QUEUED THROUGH THE SERVICE (DID NOT RUN). On 2026-11-02 a reinstall killed
# a project's CI unit run mid-way ("lock lost while it ran"). So: the same commit already serving is not
# restarted at all, and otherwise the install waits until no run holds or waits through the service, naming
# them while it waits, and refuses after LOCKD_IDLE_WAIT seconds (default 3600) rather than cut them off.
set -eu
HOST="${KIT_TEST_HOST:-new-laptop}"
TOP="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$TOP" rev-parse HEAD)"
BUNDLE="$(mktemp -d)/lockd.bundle"
git -C "$TOP" bundle create -q "$BUNDLE" HEAD
scp -q -o BatchMode=yes -o ConnectTimeout=20 "$BUNDLE" "$HOST:/tmp/lockd-$SHA.bundle"
rm -rf "$(dirname "$BUNDLE")"
ssh -o BatchMode=yes "$HOST" "sh -s -- '$SHA' '${LOCKD_IDLE_WAIT:-3600}'" <<'REMOTE'
set -eu
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
sha=$1
idle_wait=$2
src="$HOME/.qabench/lockd-src-$(printf %.12s "$sha")"
venv="$HOME/.qabench/lockd-venv"
plist="$HOME/Library/LaunchAgents/com.qabench.lockd.plist"
mkdir -p "$HOME/.qabench" "$HOME/Library/LaunchAgents"
[ -d "$src/.git" ] || git clone -q "/tmp/lockd-$sha.bundle" "$src"
git -C "$src" -c advice.detachedHead=false checkout -q --force "$sha"
rm -f "/tmp/lockd-$sha.bundle"
svc="gui/$(id -u)/com.qabench.lockd"
old=$(lsof -nP -t -iTCP:7461 -sTCP:LISTEN 2>/dev/null | head -1 || true)
# Decided BEFORE the source link moves: the running lockd's children import through it.
lpid=$(launchctl print "$svc" 2>/dev/null | sed -nE 's/^[[:space:]]*pid = ([0-9]+)$/\1/p' | head -1)
if [ -n "$old" ] && [ "$old" = "$lpid" ] && [ "$(readlink "$HOME/.qabench/lockd-src" || true)" = "$src" ]; then
  echo "lockd: already serving $(printf %.12s "$sha") as pid $old — not restarted"
  exit 0
fi
# Who holds or waits through the service: their lines say "via the host lock service"; a holder names its pid,
# a ticket is named <time_ns>-<pid>. Entries whose process is gone are not runs.
through_service() {
  lock="${QABENCH_HEAVY_LOCK:-$HOME/.qabench/heavy.lock}"
  for f in "$lock.holders"/* "$lock.queue"/*; do
    [ -f "$f" ] && grep -q "via the host lock service" "$f" 2>/dev/null || continue
    pid=$(sed -nE 's/.*, pid ([0-9]+) .*/\1/p' "$f"); [ -n "$pid" ] || pid=${f##*-}
    kill -0 "$pid" 2>/dev/null && echo "  $(cat "$f")"
  done
  return 0
}
waited=0
while runs=$(through_service) && [ -n "$runs" ]; do
  [ "$waited" -ge "$idle_wait" ] && { echo "lockd: NOT RESTARTED — after ${idle_wait}s these runs still hold or wait through it, and a restart would cut them off:"; echo "$runs"; exit 4; }
  [ $((waited % 300)) -eq 0 ] && { echo "lockd: waiting for the runs through the service to finish before restarting (${waited}s of ${idle_wait}s):"; echo "$runs"; }
  sleep 10; waited=$((waited + 10))
done
ln -sfn "$src" "$HOME/.qabench/lockd-src"
[ -x "$venv/bin/python" ] || python3.13 -m venv "$venv"
"$venv/bin/pip" install -q --disable-pip-version-check "pyyaml==6.0.3"
cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.qabench.lockd</string>
  <key>ProgramArguments</key><array>
    <string>$venv/bin/python</string><string>-m</string><string>qabench</string><string>lockd</string>
  </array>
  <key>EnvironmentVariables</key><dict>
    <key>PYTHONPATH</key><string>$HOME/.qabench/lockd-src</string>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/.qabench/lockd.log</string>
  <key>StandardErrorPath</key><string>$HOME/.qabench/lockd.log</string>
</dict></plist>
PLIST
# BOOTOUT IS ASYNCHRONOUS. On 2026-11-02 bootstrap ran while the old job was still being torn down, failed with
# "Bootstrap failed: 5: Input/output error", and left lockd DOWN on the gate host. Wait until launchd no longer
# knows the label, then bootstrap, retrying, and refuse unless a NEW process answers on 7461.
launchctl bootout "$svc" 2>/dev/null || true
for i in $(seq 1 30); do launchctl print "$svc" >/dev/null 2>&1 || break; sleep 1; done
launchctl print "$svc" >/dev/null 2>&1 && { echo "lockd: $svc still loaded 30s after bootout — NOT INSTALLED"; exit 3; }
ok=
for i in 1 2 3; do
  launchctl bootstrap "gui/$(id -u)" "$plist" && { ok=1; break; }
  echo "lockd: bootstrap attempt $i failed; retrying in $((i * 2))s"; sleep $((i * 2))
done
[ -n "$ok" ] || { echo "lockd: bootstrap failed 3 times — lockd is DOWN on this host, every wrapped container job is DID NOT RUN until it is up"; exit 3; }
new=
for i in $(seq 1 20); do new=$(lsof -nP -t -iTCP:7461 -sTCP:LISTEN 2>/dev/null | head -1 || true); [ -n "$new" ] && [ "$new" != "$old" ] && break; sleep 1; done
[ -n "$new" ] && [ "$new" != "$old" ] || { echo "lockd DID NOT START (listener: ${new:-none}, before: ${old:-none}) — $HOME/.qabench/lockd.log:"; tail -n 50 "$HOME/.qabench/lockd.log"; exit 3; }
# THE LISTENER IS THIS JOB: launchd's pid for the label is the one on 7461, and it started after the source link
# moved, so it imported $src. (ps shows the framework binary, not the venv path, so it is matched by launchd's pid.)
lpid=$(launchctl print "$svc" 2>/dev/null | sed -nE 's/^[[:space:]]*pid = ([0-9]+)$/\1/p' | head -1)
[ "$lpid" = "$new" ] || { echo "lockd: 7461 is held by pid $new but launchd runs $svc as pid ${lpid:-none}: $(ps -o command= -p "$new")"; exit 3; }
want=$(sed -nE 's/^__version__ = "([^"]+)"$/\1/p' "$src/qabench/__init__.py")
echo "lockd: serving at $(git -C "$src" rev-parse --short HEAD) (qabench $want) on 127.0.0.1:7461, pid $new (was ${old:-none})"
# The proof that matters: a container's `qabench heavy` gets the host's lock through it.
img=$(docker ps --format '{{.Image}}' | grep -m1 estate-runner || true)
[ -n "$img" ] || { echo "lockd: no estate-runner container running to prove it from — DID NOT VERIFY"; exit 3; }
docker run --rm --entrypoint python3 -v "$src:/qb:ro" -e PYTHONPATH=/qb -e QABENCH_SESSION=install_lockd "$img" \
    -m qabench heavy --name lockd-install-check -- true
REMOTE
