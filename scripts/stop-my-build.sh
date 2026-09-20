#!/usr/bin/env bash
# Stop THIS archive's build, and nothing else on the machine.
#
# Written 21 September 2026, after the Defranceski session traced a fault the
# Lerena session had been hunting in its own data. Every archive in this estate
# builds with `astro build` and several keep a top-level `build.sh`, so
# `pkill -f "astro build"` and `pkill -f build.sh` both match EVERY archive's
# processes, not this one's. This session ran the second of those twice today.
#
# It is nearly invisible when it happens. A SIGTERM'd `npm run build` inside a
# gate chain exits non-zero AFTER several checks have already printed ok, so the
# log looks clean and the failure reads like a data fault rather than a signal.
#
# The fix is to match the ABSOLUTE PATH. Every node process carries its own
# path in its command line, so this selects only processes under this repo.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"

mapfile -t PIDS < <(pgrep -f "$ROOT/" 2>/dev/null | grep -v "^$$\$")
# Drop this script and its own shell out of the list.
SELF=$$
KEEP=()
for p in "${PIDS[@]:-}"; do
  [ -z "$p" ] && continue
  [ "$p" = "$SELF" ] && continue
  KEEP+=("$p")
done

if [ "${#KEEP[@]}" -eq 0 ]; then
  echo "stop-my-build: nothing of this archive's is running"
  exit 0
fi

echo "stop-my-build: stopping ${#KEEP[@]} process(es) under $ROOT"
kill "${KEEP[@]}" 2>/dev/null
sleep 2
for p in "${KEEP[@]}"; do
  kill -0 "$p" 2>/dev/null && kill -9 "$p" 2>/dev/null
done
echo "stop-my-build: done"
