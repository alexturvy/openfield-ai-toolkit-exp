## Clean Architecture review checklist

Use this concise checklist to keep reviews focused on the happy path and avoid overengineering. Check only what is essential.

### Dependency rule and layering
- [ ] Domain entities have no imports from frameworks, databases, or UI.
- [ ] Use cases depend only on domain abstractions, never on concrete infra.
- [ ] Adapters/infrastructure depend inward on abstract ports, not vice versa.

### Data modeling (prefer classes over dictionaries)
- [ ] New domain data structures are classes (e.g., Python classes/dataclasses), not bare dictionaries.
- [ ] Value objects are immutable where practical; behavior is colocated with data.
- [ ] Dictionaries appear only for transient concerns (e.g., JSON I/O, small local maps), never as long‑lived domain models.

### Use cases (focus on happy path)
- [ ] Each use case expresses the primary success path clearly with minimal branching.
- [ ] Edge cases are handled only if required by current stories; otherwise deferred.
- [ ] Inputs/outputs are defined via explicit request/response models (classes), not untyped dicts.

### Interfaces and boundaries
- [ ] External dependencies are introduced behind narrow interfaces (ports).
- [ ] Implementations live in infrastructure and are injected; no direct framework calls in domain/use cases.

### Simplicity and scope control
- [ ] No speculative features, flags, or abstractions without a concrete requirement (YAGNI).
- [ ] Naming is clear and intention‑revealing; public surface is minimal.

### Testing (right level, right scope)
- [ ] Unit tests cover the happy path for entities and use cases.
- [ ] Integration tests exist only at adapter boundaries as needed; no deep end‑to‑end added unless justified.

### PR hygiene
- [ ] PR description references the relevant plan and summarizes the happy path.
- [ ] Documentation updated if new concepts/interfaces are introduced.

Reference: keep changes thin, vertical, and centered on the primary story. Defer non‑essential edge cases.

