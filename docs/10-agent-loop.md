# The Cell Agent Loop

How the multi-agent workflow actually operates. This is the canonical reference;
`artifacts/agent-scope-ownership.md` holds the live per-sprint scope ledger.

## There is no event bus

Earlier (Codex-era) notes mention a "Cell Event Bus Broker" and `AGENT_EVENT`
messages. **That was external orchestration runtime, never code in this repo, and
it does not exist under Claude Code.** Claude Code subagents are stateless and
isolated: they **cannot publish events to or trigger each other**. Each subagent
returns its result to the **Organizer** (the main thread), which decides what runs
next. The loop is *conductor-mediated*, not *bus-mediated*.

```
        ┌──────────────┐   I am the router. Subagents return to me;
   YOU →│  ORGANIZER   │   I route to the next one. No agent wakes another.
        └──┬────┬───┬──┘
           ▼    ▼   ▼
        agent agent agent   (isolated — no agent-to-agent messaging)
```

The closest thing to event-driven triggering is the **automatic validation gate**
below — a deterministic hook, not agent pub/sub.

## The loop

```
 YOU → Organizer ── assigns ONE scope ──▶ GATE 1: evidence-curator
                                              │ cleared ✓ / blocked ✗→back
                                              ▼
                        BUILDER (engine-biologist · stochastic-numerics ·
                                 snapshot-bridge · viz-frontend)
                                              │ change + report
                       ┌──────────────────────┴───────────────────────┐
                       ▼                                               ▼
              GATE 2a: validation-qa                        GATE 2b: visual-reviewer
              pytest · vitest · tsc · build                 (frontend only) loads the
              scope + evidence gates                        app in Chrome, screenshots,
                       │                                    judges looks + fidelity
                       └──────────────────┬─────────────────┘
                            PASS ✓ → Organizer commits        FAIL/REVISE/BLOCK ✗
                                                              → back to owning builder ↺
```

Three feedback edges make it a closed loop, not a pipeline:
1. **Evidence rejection** — a builder cannot implement an unsourced value.
2. **QA failure** — bounces back to the owning builder, never forward.
3. **Scope violation** — editing outside an assigned file is blocked and re-routed.

## The automatic gate (the real "trigger")

`scripts/gate.sh` is the `validation-qa` role as an automatic trigger. It is wired
to a **Stop hook** in `.claude/settings.json`, so at the end of each work cycle it:

- inspects `git status` and runs **only** the changed subsystem's checks
  (`engine/` → pytest; `src/` etc. → tsc + vitest);
- exits instantly when nothing relevant changed;
- runs in the background (`async`) and, on failure, **wakes the Organizer**
  (`asyncRewake`, exit code 2) with the failure output so a fix gets routed.

This is deterministic command automation — the honest equivalent of an event bus
for "validate when code changes." It does **not** make agents trigger each other.

> Note: because the settings file was added mid-project, the hook is picked up only
> after opening `/hooks` once (or restarting Claude Code).

## Invariants the loop guarantees

1. **No unsourced biology** — Gate 1 stands between every parameter and the engine.
2. **No un-green merge** — Gate 2a (tests, read-only) stands between every change and commit.
3. **No ugly or dishonest visuals** — Gate 2b (browser, read-only) stands between every
   frontend change and commit: it must look good *and* match the engine snapshot.
