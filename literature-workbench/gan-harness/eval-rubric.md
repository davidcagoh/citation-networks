# Slice 1 Evaluation Rubric

Score each category from 0–2. Passing score: 8/10, with provenance correctness
and tests both scoring 2.

1. **Provenance correctness** — every generated substantive sentence has a
   traversable persisted chain and exact source offsets.
2. **End-to-end function** — fixture project runs from brief through review and
   evidence inspection without external services.
3. **Persistence and boundaries** — validated domain contracts, migrations,
   stage records, and no direct prompt-output coupling.
4. **Usability** — clear corpus/structure/review screens and evidence drawer.
5. **Engineering proof** — tests cover schema integrity, exact spans, invalid
   references, degraded inputs, pipeline integration, and frontend claim
   inspection; coverage is at least 80% for implemented backend code.
