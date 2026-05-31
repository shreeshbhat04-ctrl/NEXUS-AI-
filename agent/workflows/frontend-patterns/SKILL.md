---
name: frontend-patterns
description: Framework-agnostic frontend component design patterns with emphasis on React, Vue, and Angular implementations. Use when building or reviewing UI components, state management, hooks, forms, accessibility, rendering performance, or component architecture.
---

# Frontend Patterns

## Overview

Use this skill when a UI needs to be easier to reason about, more reusable, or more responsive. Favor patterns that keep state predictable, components small, and behavior close to the place it matters.

## Start Here

Classify the problem first:

- component structure
- state management
- data fetching and async UI
- forms and validation
- accessibility and keyboard flow
- rendering performance
- responsive layout and composition

## Component Structure

- Keep components focused on one responsibility.
- Split presentational rendering from orchestration when a component grows.
- Pass data and callbacks through props instead of deep coupling.
- Prefer composition over oversized prop surfaces.
- Extract repeated UI into reusable pieces only when it is truly repeated.

## State Management

- Keep state as local as possible.
- Derive values instead of storing duplicates.
- Lift state only when multiple children need it.
- Model UI state explicitly when loading, empty, error, and success all matter.
- Use shared stores sparingly and only for shared cross-cutting state.

## Data Fetching

- Keep loading and error states visible and predictable.
- Avoid storing server data in too many places.
- Refresh data with clear invalidation rules.
- Cancel or ignore stale requests when interactions can race.
- Prefer server truth over optimistic guesses unless the UX needs optimism.

## Forms

- Validate at the boundary.
- Keep field state and submission state separate.
- Surface actionable error messages near the related input.
- Disable or guard duplicate submissions.
- Preserve accessibility with labels, focus order, and keyboard support.

## Accessibility

- Use semantic elements first.
- Preserve keyboard navigation and visible focus.
- Ensure color is not the only signal.
- Provide labels, names, and roles that match the control's purpose.
- Test dialog, menu, and form interactions with assistive technologies in mind.

## Performance

- Avoid unnecessary re-renders and oversized prop objects.
- Memoize only when there is a measured need.
- Split heavy views into smaller boundaries when it helps loading or interactivity.
- Virtualize large lists when the DOM becomes a bottleneck.
- Keep client-side work out of the critical render path when possible.

## Responsive UI

- Design for flexible containers, not fixed pixels.
- Let spacing and layout adapt across breakpoints.
- Prefer fluid grids and stacking behavior over one-off overrides.
- Keep touch targets large enough for mobile interaction.

## Review Checklist

When reviewing frontend code, check:

- Is component responsibility clear?
- Is state colocated and minimal?
- Are loading, empty, and error states handled?
- Is the UI accessible by keyboard and assistive tech?
- Are performance optimizations justified?
- Does the layout work across screen sizes?

## Good Defaults

- Prefer simple data flow.
- Prefer semantic HTML and accessible primitives.
- Prefer reusable composition over copy-paste UI.
- Prefer explicit states over hidden assumptions.
