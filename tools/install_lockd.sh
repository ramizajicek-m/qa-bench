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
# lockd and heavy start on the standard library and yaml. A restart drops any lock held through the service,
# and those runs stop as DID NOT RUN — so install between runs, not under them.
set -eu
HOST="${KIT_TEST_HOST:-new-laptop}"
TOP="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$TOP" rev-parse HEAD)"
BUNDLE="$(mktemp -d)/lockd.bundle"
git -C "$TOP" bundle create -q "$BUNDLE" HEAD
scp -q -o BatchMode=yes -o ConnectTimeout=20 "$BUNDLE" "$HOST:/tmp/lockd-$SHA.bundle"
rm -rf "$(dirname "$BUNDLE")"
ssh -o BatchMode=yes "$HOST" "sh -s -- '$SHA'" <<'REMOTE'
set -eu
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
sha=$1
src="$HOME/.qabench/lockd-src-$(printf %.12s "$sha")"
venv="$HOME/.qabench/lockd-venv"
plist="$HOME/Library/LaunchAgents/com.qabench.lockd.plist"
mkdir -p "$HOME/.qabench" "$HOME/Library/LaunchAgents"
[ -d "$src/.git" ] || git clone -q "/tmp/lockd-$sha.bundle" "$src"
git -C "$src" -c advice.detachedHead=false checkout -q --force "$sha"
rm -f "/tmp/lockd-$sha.bundle"
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
launchctl bootout "gui/$(id -u)/com.qabench.lockd" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist"
for i in 1 2 3 4 5 6 7 8 9 10; do lsof -nP -iTCP:7461 -sTCP:LISTEN >/dev/null 2>&1 && break; sleep 1; done
lsof -nP -iTCP:7461 -sTCP:LISTEN >/dev/null 2>&1 || { echo "lockd DID NOT START — $HOME/.qabench/lockd.log:"; tail -n 50 "$HOME/.qabench/lockd.log"; exit 3; }
echo "lockd: serving at $(git -C "$src" rev-parse --short HEAD) on 127.0.0.1:7461"
# The proof that matters: a container's `qabench heavy` gets the host's lock through it.
img=$(docker ps --format '{{.Image}}' | grep -m1 estate-runner || true)
[ -n "$img" ] || { echo "lockd: no estate-runner container running to prove it from — DID NOT VERIFY"; exit 3; }
docker run --rm --entrypoint python3 -v "$src:/qb:ro" -e PYTHONPATH=/qb -e QABENCH_SESSION=install_lockd "$img" \
    -m qabench heavy --name lockd-install-check -- true
REMOTE
