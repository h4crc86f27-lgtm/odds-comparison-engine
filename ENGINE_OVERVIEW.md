# ENGINE OVERVIEW

Version: 1.0

Status: Production

This document describes the overall architecture of the Odds Comparison
Engine.

It is intended for developers and AI assistants working on the Python
backend.

This document describes the current production architecture.

It does not propose redesigns.

------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

The Odds Comparison Engine continuously compares sportsbook odds against
Betfair Exchange prices.

It downloads odds, aligns identical sporting events, calculates
comparisons and writes the results to MySQL.

The PHP frontend never performs these tasks.

The engine is the single source of truth.

------------------------------------------------------------
2. HIGH LEVEL FLOW
------------------------------------------------------------

Betfair
      │
      ▼
Competition discovery
      │
      ▼
Provider downloads
      │
      ▼
Team matching
      │
      ▼
Market alignment
      │
      ▼
Comparison calculations
      │
      ▼
MySQL
      │
      ▼
PHP Frontend

------------------------------------------------------------
3. STARTUP SEQUENCE
------------------------------------------------------------

arb_monitor.py starts the engine.

Startup performs:

• Betfair login

• Session validation

• Team list loading

• Optional raw data collection

• Active competition discovery

• Betfair market discovery

• Provider downloads

• Matching

• Database updates

The engine then repeats this cycle continuously.

------------------------------------------------------------
4. MAIN LOOP
------------------------------------------------------------

The engine operates as an endless polling loop.

Each scan:

1.
Refresh Betfair session if necessary.

2.
Discover active competitions.

3.
Download Betfair markets.

4.
Download sportsbook odds.

5.
Match events.

6.
Calculate comparisons.

7.
Write results.

8.
Update timestamps.

Repeat.

------------------------------------------------------------
5. BETFAIR
------------------------------------------------------------

Betfair is the reference provider.

All comparisons are performed against Betfair.

Betfair controls:

• competitions

• event IDs

• market IDs

• prices

• liquidity

Provider data is aligned to Betfair.

------------------------------------------------------------
6. ACTIVE PROVIDERS
------------------------------------------------------------

Current production providers:

• Betfair

• Unibet

• Bet3000

These are the only providers currently considered active.

Future development should primarily focus on these providers.

------------------------------------------------------------
7. LEGACY PROVIDERS
------------------------------------------------------------

The source tree still contains older providers including:

• TOTO

• Bingoal

• Contra

• QRBet

• Yess365

• Bet635

• M8Bets

• Live90Bet

• Winkel Toto

• BetAlpha

Most are currently inactive because external API access has been removed
or blocked.

These modules remain for historical compatibility.

Do not remove them unless explicitly instructed.

------------------------------------------------------------
8. PROVIDER ARCHITECTURE
------------------------------------------------------------

Every provider module follows approximately the same structure:

Pull remote data

↓

Match against Betfair

↓

Transform data

↓

Insert into database

Provider modules should remain isolated.

Avoid copying logic between providers.

------------------------------------------------------------
9. MATCHING
------------------------------------------------------------

Matching occurs in two stages.

Stage 1

Exact timestamp matching.

Stage 2

Fuzzy team-name matching.

Fuzzy matching is only used when necessary.

------------------------------------------------------------
10. DATABASE
------------------------------------------------------------

The engine writes directly to MySQL using pymysql.

There is currently no central database abstraction layer.

Database writes occur throughout the provider modules.

Do not introduce a database abstraction unless explicitly requested.

------------------------------------------------------------
11. THREADING
------------------------------------------------------------

Provider downloads are parallelised.

Thread counts vary per provider.

Concurrency is intentionally conservative to avoid API rate limits.

------------------------------------------------------------
12. RAW DATA
------------------------------------------------------------

The engine periodically stores raw provider information.

Raw data assists with:

• diagnostics

• debugging

• historical comparison

• provider verification

------------------------------------------------------------
13. HISTORICAL DATA
------------------------------------------------------------

Historical odds are stored separately.

The engine writes odds history while simultaneously updating current
prices.

------------------------------------------------------------
14. CRITICAL FILES
------------------------------------------------------------

gamma/arb_monitor.py

Main scheduler.

gamma/arber_modules/betfair.py

Betfair integration.

gamma/arber_modules/unibet.py

Unibet provider.

gamma/arber_modules/bet3000.py

Bet3000 provider.

gamma/arber_modules/utils.py

Shared helper functions.

------------------------------------------------------------
15. SAFE MODIFICATION RULES
------------------------------------------------------------

Future developers and AI assistants should:

• Preserve existing behaviour.

• Avoid changing business logic without explicit approval.

• Avoid unnecessary refactoring.

• Keep provider implementations isolated.

• Prefer documentation over redesign.

• Preserve backwards compatibility.

------------------------------------------------------------
16. DEVELOPMENT PHILOSOPHY
------------------------------------------------------------

The project has evolved over many years.

Consistency is more important than elegance.

Reliability is more important than cleverness.

Small safe improvements are preferred over large architectural changes.

------------------------------------------------------------
17. AI ASSISTANT NOTES
------------------------------------------------------------

Before modifying code:

1.
Read README.md

2.
Read AGENTS.md

3.
Read ENGINE_ARCHITECTURE.md

4.
Read CODEMAP.md

5.
Read this document

Only then begin analysing source code.

This greatly reduces unnecessary analysis, improves consistency and
minimises AI token usage.