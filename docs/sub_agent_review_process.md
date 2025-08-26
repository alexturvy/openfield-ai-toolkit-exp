## Sub‑agent review process (pragmatic, happy‑path first)

Purpose: act as a lightweight reviewer to enforce the Clean Architecture plan without overengineering.

### Inputs
- PR diff and description
- Architecture plan reference (e.g., docs in `docs/`)

### Review steps
1) Scope and intent
   - Confirm the PR implements a single happy‑path story. Defer extras.

2) Layering and dependencies
   - Domain: no imports from frameworks, DB, HTTP, or UI.
   - Use cases: depend on domain abstractions only; no concrete infra.
   - Infra/adapters: implement interfaces; depend inward only.

3) Data modeling
   - Prefer classes/dataclasses for domain models and request/response types.
   - Dictionaries allowed only for transient concerns (JSON I/O, tiny local maps).

4) Use case design
   - Happy path is linear and clear; minimal branching.
   - Inputs/outputs are explicit classes; avoid untyped dicts.

5) Interfaces and boundaries
   - External services behind narrow ports; implemented in infrastructure.
   - No direct framework calls in domain/use cases.

6) Tests at the right level
   - Unit tests cover happy path of entities/use cases.
   - Integration tests only at adapter boundaries when adapters are added/changed.

7) Simplicity and scope control
   - YAGNI: remove speculative abstractions and unused parameters/flags.
   - Naming is clear; public API is minimal.

### Decision rubric
- Approve: checklist passes; any deferrals are documented.
- Request changes: identify concrete violations (dicts for models, dependency rule break, excessive edge‑case code, missing ports/tests).

### Reviewer comment template
Copy/paste and fill:

```
Review outcome: Approve | Request changes

Findings
- Dependency rule: [ok/issue]
- Data modeling (classes > dicts): [ok/issue]
- Happy path focus: [ok/issue]
- Ports/adapters boundaries: [ok/issue]
- Tests at right level: [ok/issue]
- Simplicity/naming: [ok/issue]

Actions requested (if any)
- ...
```

