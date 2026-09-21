#!/usr/bin/env bash
# Stop THIS archive's build, and nothing else on the machine.
#
# WHY NOT `pkill -f`. Every archive in this estate builds with `astro build`
# and several keep a top-level `build.sh`, so `pkill -f "astro build"` and
# `pkill -f build.sh` both match EVERY archive's processes. This session ran
# the second of those twice on 21 September 2026. The Lerena session lost three
# verify runs to a neighbour doing the same.
#
# WHY NOT MATCHING THE PATH EITHER, WHICH IS WHAT THIS SCRIPT DID FIRST. The
# first version selected on `pgrep -f "$ROOT/"`, reasoning that every node
# process carries its own absolute path. It does — but the SCRIPT does not:
# `bash ./build.sh` is a relative path and carries no root at all, and neither
# does `npm run build` or the `sh -c` wrapper under it. Run against a live
# build forty seconds in, before any astro process existed, it selected
# NOTHING. A tool written, committed, recommended to another session, and
# never once run. Own error 41's lesson in the tool built to serve it.
#
# WHAT WORKS IS THE WORKING DIRECTORY. Every process in a build — the script,
# npm, the sh wrapper, node, esbuild — has a cwd inside the repo, whatever its
# command line says. Verified 21 September with four archives building at once:
# it selected this archive's five and left The Geneology Map's astro and
# esbuild, Falco's shells and Defranceski's alone.
#
#   scripts/stop-my-build.sh          # stop them
#   scripts/stop-my-build.sh --dry    # list what would be stopped, kill nothing
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
DRY=0; [ "${1:-}" = "--dry" ] && DRY=1

# Never kill the shell this is running in, or anything that launched it — a
# parent's cwd is this repo too, and killing it takes the caller down with the
# build it asked to stop.
SAFE=" "
pid=$$
while [ "$pid" -gt 1 ]; do
  SAFE="$SAFE$pid "
  pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
  [ -z "$pid" ] && break
done

PIDS=""
for p in $(pgrep -u "$(id -u)" -f 'build\.sh|astro|esbuild|npm run|node ' 2>/dev/null); do
  case "$SAFE" in *" $p "*) continue ;; esac
  cwd=$(lsof -a -d cwd -Fn -p "$p" 2>/dev/null | sed -n 's/^n//p' | head -1)
  case "$cwd" in
    "$ROOT"|"$ROOT"/*) PIDS="$PIDS $p" ;;
  esac
done

set -- $PIDS
if [ "$#" -eq 0 ]; then
  echo "stop-my-build: nothing of this archive's is running"
  exit 0
fi

for p in "$@"; do
  echo "  [$p] $(ps -o command= -p "$p" 2>/dev/null | cut -c1-90)"
done
if [ "$DRY" -eq 1 ]; then
  echo "stop-my-build: --dry, $# process(es) would be stopped, none were"
  exit 0
fi
echo "stop-my-build: stopping $# process(es) under $ROOT"
kill "$@" 2>/dev/null
sleep 2
for p in "$@"; do kill -0 "$p" 2>/dev/null && kill -9 "$p" 2>/dev/null; done
echo "stop-my-build: done"
