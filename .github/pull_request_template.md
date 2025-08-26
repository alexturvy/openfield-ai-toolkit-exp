## Pull request template — Clean Architecture guardrails

### Summary
What happy path does this change enable? Link the issue/plan.

### Checklist (must pass to merge)
- [ ] Respects dependency rule: domain/use cases are framework‑free.
- [ ] No reliance on dictionaries for domain models; classes/dataclasses used.
- [ ] Happy path is implemented; only necessary edge cases included.
- [ ] External deps are behind interfaces; adapters in infrastructure only.
- [ ] Inputs/outputs are typed classes, not unstructured dicts.
- [ ] Tests cover the happy path at the correct level (unit/integration at boundaries).
- [ ] Names and public surface are minimal and intention‑revealing.
- [ ] Docs updated where new concepts/interfaces were introduced.

### Notes for reviewers
Call out any trade‑offs, intentional deferrals, or follow‑ups.

