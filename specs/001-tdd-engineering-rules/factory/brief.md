# Brief: engineering discipline for factory code-writing roles

Every factory run must write code test-first (red-green-refactor), with clean code, SOLID design, a functional-leaning style and no over-engineering: before writing a function, the agent looks for an existing one to reuse or extend. The rules live in one shared, harness-neutral reference that the code-writing, planning and reviewing roles all point at, so the discipline is planned for, followed and checked in every run.

## Decisions

- Scope: code-build and fixer follow the rules; spec-builder plans for them (plan writes a "Test seams" section; tasks emits a failing-test task before each implementation task); code-standards enforces them in review.
- Rules live in one new shared reference, `core/skills/factory/references/engineering.md`, referenced by each role. No copies inline in roles.
- No dependency on the external `tdd` skill: the factory owns its rules, self-contained in engineering.md (the tdd skill confirms seams with the user mid-loop, which stateless agents cannot do).
- Test seams are agreed at plan time: plan lists the public seams under test; analyze checks every implementation task maps to a seam and has a test task before it; clarify asks the user only when seams are ambiguous. code-build never invents seams on the fly.
- No test framework in the repo: plan adds a "set up test runner" task first. Pure docs/config changes are exempt from TDD, with the reason stated in the plan. Never skip TDD silently.
- Functional programming is preferred, not mandatory: pure functions, immutable data, side effects at the edges, composition over inheritance, within the language's idiom. The repo's documented conventions win on conflict.
- Proof of red-before-green: per task, run the new test and see it fail before implementing; record `Red: <test name> failed as expected` in the task commit body. No separate red commits (history stays bisectable).
- Full red-green-refactor inside each task: refactor only while green, then re-run the tests.
- Reuse: before writing a function, code-build (and fixer) searches the repo for an existing one and reuses or extends it. code-standards flags new code that duplicates an existing helper; real duplication is blocking.
- Always on for every run. A repo's constitution may override a specific rule.
- DESIGN.md is updated first (constitution, Principle I), then core roles/references, then dist/ re-rendered for every harness and committed (Principle III).
