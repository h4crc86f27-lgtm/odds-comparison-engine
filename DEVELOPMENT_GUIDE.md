# DEVELOPMENT GUIDE

Version: 1.0

Status: Production

This document describes the preferred development workflow for the Odds
Comparison Engine.

It is intended for both human developers and AI assistants.

The goal is to minimise risk while keeping development efficient.

------------------------------------------------------------
1. DEVELOPMENT PHILOSOPHY
------------------------------------------------------------

The engine is production software.

Stability is more important than elegance.

Correctness is more important than speed.

Small, reviewable changes are preferred over large refactors.

Every change should be easy to understand and easy to revert.

------------------------------------------------------------
2. BEFORE MODIFYING CODE
------------------------------------------------------------

Read the following documents first:

1. README.md

2. AGENTS.md

3. ENGINE_ARCHITECTURE.md

4. ENGINE_OVERVIEW.md

5. CODEMAP.md

6. PRODUCTION_FILES.md

7. TECHNICAL_AUDIT.md

Only then begin analysing source code.

------------------------------------------------------------
3. ACTIVE DEVELOPMENT TARGETS
------------------------------------------------------------

Current production providers:

• Betfair

• Unibet

• Bet3000

Development should primarily focus on these modules.

Legacy providers should normally be ignored unless explicitly requested.

------------------------------------------------------------
4. SAFE DEVELOPMENT RULES
------------------------------------------------------------

Unless explicitly instructed otherwise:

• Do not change runtime behaviour.

• Do not change business logic.

• Do not change SQL.

• Do not redesign architecture.

• Do not rename public functions.

• Do not move large blocks of code.

• Preserve backwards compatibility.

------------------------------------------------------------
5. AI WORKFLOW
------------------------------------------------------------

One file at a time.

Typical workflow:

1.
Select one file.

2.
Modify only that file.

3.
Review the diff.

4.
Commit.

5.
Push.

Large multi-file changes should be avoided whenever possible.

------------------------------------------------------------
6. CODEX PROMPTS
------------------------------------------------------------

Preferred characteristics:

• Small scope.

• One file only.

• Documentation or narrowly scoped improvements.

• Explicit constraints.

Avoid broad repository-wide requests.

------------------------------------------------------------
7. REVIEW PROCESS
------------------------------------------------------------

Never commit immediately after an AI-generated change.

Always inspect the diff first.

Recommended workflow:

Codex

↓

git diff

↓

Human review

↓

Commit

↓

Push

------------------------------------------------------------
8. LINE ENDINGS
------------------------------------------------------------

Preserve existing line endings.

Do not convert LF to CRLF.

Do not normalise files unless explicitly requested.

------------------------------------------------------------
9. TYPE HINTS
------------------------------------------------------------

Do not introduce type hints into legacy production code unless explicitly
requested.

Large-scale type-hint additions often produce unnecessary changes and
make code reviews more difficult.

------------------------------------------------------------
10. FORMATTING
------------------------------------------------------------

Avoid formatting-only commits.

Do not re-indent files.

Do not reorder imports.

Do not reflow comments unnecessarily.

Formatting changes should only accompany functional work when required.

------------------------------------------------------------
11. TESTING
------------------------------------------------------------

Every change should preserve existing behaviour.

Documentation-only changes should not modify runtime behaviour.

Behavioural changes should be validated before deployment.

------------------------------------------------------------
12. COMMITS
------------------------------------------------------------

Keep commits small.

Examples:

Document Unibet provider

Improve Bet3000 logging

Fix retry handling

Avoid combining unrelated work into a single commit.

------------------------------------------------------------
13. FUTURE REFACTORING
------------------------------------------------------------

Potential future improvements include:

• Centralised database layer

• Shared provider base functions

• Unified retry handling

• Improved configuration management

• Better logging

• Automated tests

These should only be introduced gradually after production behaviour is
fully understood.

------------------------------------------------------------
14. AI CREDIT EFFICIENCY
------------------------------------------------------------

To minimise AI usage:

• Work on one file at a time.

• Avoid repository-wide analysis.

• Avoid unnecessary explanations.

• Prefer targeted prompts.

• Review before committing.

• Reuse existing documentation rather than regenerating context.

------------------------------------------------------------
15. FINAL PRINCIPLE
------------------------------------------------------------

The objective is not to create the most modern codebase.

The objective is to maintain a reliable production system that can evolve
safely over time.

Every change should leave the project slightly better than before,
without introducing unnecessary risk.

End of document.