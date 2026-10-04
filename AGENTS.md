# CodeAtlas

## Learning mode

- This is a learning-first AI full-stack project.
- Before proposing changes, inspect the relevant current files and learning checkpoint when available.
- Advance one small goal at a time: a runnable behavior with clear acceptance criteria, not a few lines of code or an unfinished function. Split large goals into independently verifiable behaviors.
- Explain the concept and data flow before implementation. Teach one main learning point in depth per goal; explain supporting concepts enough to use them.
- Provide coherent guidance covering the files and all changes needed to complete the agreed goal. Do not withhold necessary steps until the user repeatedly says "continue".
- The user edits application code by default; edit it only when explicitly asked. Complete guidance is allowed and does not imply permission to implement it directly.
- Give the user opportunities to reason about and implement key logic. Repetitive code may be provided in full, with progressive help when needed.
- Ask questions to resolve important misunderstandings, missing information, or consequential choices; avoid routine confirmations and proceed once resolved.
- Provide run commands, verification steps, and expected results for each goal. After the user finishes editing, review and verify the behavior together before planning the next goal. Syntax checks, builds, or old passing tests alone do not prove a new behavior is complete.
- Preserve existing safety checks and test requirements; keep additional testing proportional to risk.
- Do not install many dependencies, delete files, or expand scope without need.

## Project direction

- `docs/` contains local-only learning material and is not tracked. If absent, use README.md and the MVP scope below; ask for missing learning context only when needed, and do not invent it.
- Follow `docs/roadmap.md` when available.
- Keep the MVP focused on repository import, browsing, cited code Q&A, and learning progress.
- Put durable learning notes in `docs/`.
- When maintaining local learning notes, keep the current checkpoint in `docs/learning-log.md`.
