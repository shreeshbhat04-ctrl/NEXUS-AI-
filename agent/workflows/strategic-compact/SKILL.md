---
name: strategic-compact
description: Guidance for deciding when to compact context between research, planning, implementation, and testing phases. Use when long tasks accumulate history, the thread becomes noisy, or a fresh context would make the next step clearer and safer.
---

# Strategic Compact

## Overview

Use this skill when a task is getting long enough that the current thread is no longer the clearest place to continue. The goal is to compact at natural boundaries, not randomly mid-thought.

## When To Compact

Compact when one of these is true:

- a phase just finished and the next phase starts cleanly
- the thread has a lot of exploratory dead ends
- important decisions are already settled
- the next step only needs a short state summary
- a new agent or fresh pass would reduce confusion

Good phase boundaries:

- research to planning
- planning to implementation
- implementation to verification
- debugging to retry with a narrower scope

## What To Keep

Before compacting, preserve:

- the user's goal
- confirmed decisions
- open risks or tradeoffs
- file paths or commands that matter
- test results that still constrain the next step

Drop:

- discarded hypotheses
- repeated reasoning
- stale alternatives already ruled out
- low-value transcript noise

## How To Decide

Ask three questions:

1. What is already known for sure?
2. What is the next concrete action?
3. Would a shorter thread make that action easier?

If the answer to the third question is yes, compact.

## Good Defaults

- Compact after major milestones, not after every small step.
- Compact before switching from exploration to execution.
- Keep the summary short and actionable.
- Preserve only what the next phase truly needs.
