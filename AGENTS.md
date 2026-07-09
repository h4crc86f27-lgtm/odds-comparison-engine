# AGENTS.md

This repository is production-quality software.

Stability is more important than cleverness.
Prefer conservative changes over ambitious changes.

---

# Project

Repository: Odds Comparison Engine

This repository contains the Python backend responsible for:

- Collecting sportsbook odds
- Communicating with Betfair Exchange
- Matching events
- Calculating price comparisons
- Writing comparison results into MySQL

The PHP frontend only displays data.
The engine is the source of truth.

---

# Current Production State

## Active Providers

Only the following providers are active in production:

- Betfair Exchange
- Unibet
- Bet3000

Unless explicitly instructed otherwise, development should focus only on these providers.

## Legacy Providers

The following modules remain for historical reference:

- Toto
- Bingoal
- Contra
- QRBet
- Yess365
- Bet635
- Live90Bet
- M8Bets

These providers are currently inactive because access has been lost, blocked or discontinued.

Do not maintain, redesign or improve legacy providers unless explicitly requested.

---

# Architecture

Bookmakers
    ↓
Provider Modules
    ↓
gamma/arb_monitor.py
    ↓
Comparison Engine
    ↓
MySQL Database
    ↓
PHP Frontend

Business logic belongs in the engine.

Never move business logic into PHP.

---

# Main Orchestrator

gamma/arb_monitor.py is the central orchestration loop.

Responsibilities:

- Betfair session management
- Competition loading
- Provider execution
- Event matching
- Comparison processing
- Database updates
- Scan scheduling

Do not redesign the orchestration loop unless explicitly requested.

---

# Provider Rules

Each provider must remain isolated.

Rules:

- One provider per module.
- Do not duplicate provider logic.
- Do not make providers depend on each other.
- Preserve existing interfaces.
- Extend existing modules instead of creating replacements.

---

# Database Rules

The engine owns database writes.

The frontend primarily reads data.

Do not redesign the schema unless explicitly requested.

---

# Betfair Rules

Respect API limits.

Avoid unnecessary API requests.

Preserve existing session handling.

Betfair is the primary reference source.

---

# Coding Standards

- Preserve production behaviour.
- Maintain backwards compatibility.
- Prefer small focused changes.
- Avoid unnecessary abstractions.
- Avoid unnecessary dependencies.
- Reuse existing code whenever practical.

---

# AI Efficiency Policy

Minimize AI credit and token usage.

Always:

- Read only files relevant to the task.
- Modify only files that require changes.
- Prefer the smallest practical patch.
- Avoid repository-wide analysis unless requested.
- Keep explanations concise.
- Avoid rewriting entire files for small edits.

Never:

- Perform cosmetic refactors.
- Reformat unrelated files.
- Rename stable modules.
- Introduce new frameworks without approval.
- Rewrite working code simply because a newer approach exists.

---

# Git

Prefer:

- One logical change per commit.
- Small commits.
- Clear commit messages.

Do not mix unrelated changes.

---

# General Principles

When uncertain:

- Choose the safest implementation.
- Preserve existing behaviour.
- Ask for clarification rather than making architectural assumptions.

Respect the existing architecture.
