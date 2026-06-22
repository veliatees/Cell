#!/usr/bin/env bash
# Cell validation gate — the validation-qa role as an automatic trigger.
#
# This is the closest thing the project has to an "event bus": instead of agents
# publishing events to each other (not possible with isolated subagents), the
# Organizer wires this to a Stop hook so the QA gate fires automatically at the
# end of each work cycle. It is event-driven and scoped: it inspects which
# subsystem actually changed (via git) and runs ONLY that subsystem's checks, so
# it stays fast and silent when nothing relevant changed.
#
# Exit 0 = PASS (or nothing to check). Exit 2 = a gate failed (this code makes the
# Stop hook wake the Organizer with the failure output so it routes a fix).
set -uo pipefail

cd "$(dirname "$0")/.." || exit 0

changed="$(git status --porcelain 2>/dev/null)"
[ -z "$changed" ] && exit 0  # clean tree → nothing to gate, return instantly

touched_engine=0
touched_frontend=0
echo "$changed" | grep -qE ' (engine/|scripts/export_engine_snapshot\.py)' && touched_engine=1
echo "$changed" | grep -qE ' (src/|index\.html|vite\.config\.ts)' && touched_frontend=1

[ "$touched_engine" = 0 ] && [ "$touched_frontend" = 0 ] && exit 0

fail=0
echo "── Cell gate (auto) ─────────────────────────────"

if [ "$touched_frontend" = 1 ]; then
  echo "▶ frontend changed → tsc + vitest"
  if ! npx tsc --noEmit >/tmp/cell-gate-tsc.log 2>&1; then
    echo "  ✗ tsc FAILED (see /tmp/cell-gate-tsc.log)"; fail=1
  else echo "  ✓ tsc clean"; fi
  if ! npm test >/tmp/cell-gate-vitest.log 2>&1; then
    echo "  ✗ vitest FAILED (see /tmp/cell-gate-vitest.log)"; fail=1
  else echo "  ✓ vitest passing"; fi
fi

if [ "$touched_engine" = 1 ]; then
  echo "▶ engine changed → pytest"
  if ! python3 -m pytest -q >/tmp/cell-gate-pytest.log 2>&1; then
    echo "  ✗ pytest FAILED (see /tmp/cell-gate-pytest.log)"; fail=1
  else echo "  ✓ pytest passing"; fi
fi

if [ "$fail" = 1 ]; then
  echo "── Gate: FAIL — hand back to the owning agent ───"
  exit 2
fi
echo "── Gate: PASS ───────────────────────────────────"
exit 0
