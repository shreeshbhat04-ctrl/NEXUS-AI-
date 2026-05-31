---
name: backend-patterns
description: Backend architecture patterns, API design, database optimization, and server-side best practices for Node.js, Express, and Next.js API routes. Use when building or reviewing backend code, REST or GraphQL APIs, data access layers, auth flows, caching, queues, or performance issues.
---

# Backend Patterns

## Overview

Use this skill when a task involves server-side architecture or code review. Prefer clear boundaries, small handlers, reusable services, and explicit data access over ad hoc logic in routes.

## Start Here

Identify the shape of the problem first:

- API design or route structure
- business logic and layering
- database queries and schema use
- auth, sessions, and permissions
- caching, queues, and background work
- observability, logging, and reliability

Then apply the smallest pattern that fits.

## API Design

- Keep handlers thin; move work into services.
- Use consistent request and response shapes.
- Validate inputs at the boundary.
- Return stable status codes and error payloads.
- Favor resource-oriented REST endpoints unless the domain is clearly query-heavy and GraphQL fits better.

For Next.js API routes, keep route files small and delegate:

1. parse and validate input
2. call a service or repository
3. map domain results to HTTP responses

## Layering

Use this default split:

- routes/controllers: HTTP concerns only
- services: business rules and orchestration
- repositories/data access: database queries
- shared utilities: pure helpers, validation, formatting

If a function mixes two layers, split it unless the code is truly trivial.

## Database Work

Prefer:

- indexed predicates for common filters
- batched reads over repeated single-row queries
- projection of only needed columns
- pagination with stable ordering
- transactions for multi-step writes

Watch for:

- N+1 query patterns
- missing indexes on join or filter keys
- unbounded scans
- data duplication that hides stale reads
- connection churn instead of pooling

If performance is slow, inspect the query plan before changing application code.

## Caching

Cache when the data is read-heavy, expensive to compute, or safe to serve slightly stale.

- Cache the output, not intermediate guesses.
- Choose clear invalidation rules.
- Keep cache keys deterministic and scoped.
- Use short TTLs when correctness matters.

If cache invalidation becomes hard, simplify the data flow or narrow the cached surface.

## Auth And Permissions

- Authenticate early at the edge or route boundary.
- Authorize per action, not just per session.
- Treat user identity and permissions as separate checks.
- Avoid leaking whether a resource exists unless that is intentional.

For multi-tenant systems, scope every query by tenant or org ID.

## Background Work

Move slow or retryable work out of the request path when possible.

- Use queues for emails, syncs, and fan-out work.
- Make jobs idempotent.
- Store retry state and failure details.
- Keep request responses fast and predictable.

## Reliability

- Log the important decision points, not every line.
- Include request IDs or trace IDs where available.
- Fail closed on authorization and validation.
- Use structured errors that are easy to inspect.
- Add timeouts around network and database calls.

## Review Checklist

When reviewing backend code, check:

- Is the route thin and readable?
- Is validation happening at the boundary?
- Is the data access path efficient?
- Are auth checks complete and tenant-safe?
- Are errors actionable and stable?
- Would this be easy to test?

## Good Defaults

- Prefer composition over inheritance.
- Prefer explicit dependencies over globals.
- Prefer small, testable functions over large handlers.
- Prefer database constraints for invariants that must never break.
