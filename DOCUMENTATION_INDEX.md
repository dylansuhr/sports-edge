# SportsEdge - Documentation Index

**Last Updated:** October 12, 2025

---

## 📚 Documentation Structure

We've consolidated all documentation into a clear, easy-to-navigate structure with **5 core documents**:

### Root Level (High-Level Overview)

#### [`CLAUDE.md`](./CLAUDE.md)
**Purpose:** Quick-reference guide for Claude Code AI
**Audience:** AI assistant, developers starting work
**Contents:**
- Project overview and tech stack
- Essential commands (`make etl`, `make signals`, etc.)
- Architecture principles (API-only, idempotent operations)
- File structure reference
- Current system status
- Critical rules (compliance, code quality, security)
- Common tasks (adding sports, debugging, updating models)

**When to use:** Starting a new coding session, need quick facts about the project

---

#### [`COMPLIANCE.md`](./COMPLIANCE.md)
**Purpose:** Legal and Terms of Service compliance
**Audience:** Legal review, compliance audit
**Contents:**
- Human-in-the-loop policy (no automated bet placement)
- Data source ToS compliance (The Odds API)
- Sportsbook ToS compliance
- API key security best practices
- Legal disclaimers
- Responsible gambling guidelines
- Data privacy policy

**When to use:** Verifying legal compliance, onboarding new contributors, audit preparation

---

#### [`README.md`](./README.md)
**Purpose:** First-time setup and quick start
**Audience:** New developers
**Contents:**
- Prerequisites
- Installation steps
- First-time setup
- Basic usage examples

**When to use:** Setting up the project for the first time

---

### `claude/` Directory (Detailed Technical Docs)

#### [`claude/ROADMAP.md`](./claude/ROADMAP.md)
**Purpose:** Comprehensive technical roadmap and reference
**Audience:** Developers, project managers
**Contents:**
- **Quick Start:** Setup and daily operations
- **Current System Status:** Production metrics, operational features, known issues
- **What We've Built:** Baseline features, critical fixes, database schema
- **Architecture Deep Dive:** Data flow, key patterns, signal generation logic
- **Phase 1-3 Roadmaps:** Detailed implementation plans with effort estimates
- **Troubleshooting Guide:** Common issues and solutions
- **Development Workflow:** Making changes, testing, committing
- **Configuration Reference:** Environment variables, Makefile commands
- **Success Metrics:** Current vs target KPIs

**When to use:**
- Planning new features
- Understanding system architecture
- Troubleshooting issues
- Checking roadmap priorities

---

#### [`claude/CODEBASE_ANALYSIS.md`](./claude/CODEBASE_ANALYSIS.md)
**Purpose:** Deep technical analysis and cleanup report
**Audience:** Technical leads, code reviewers
**Contents:**
- **Executive Summary:** Code quality assessment
- **Architecture Analysis:** Package structure, module dependencies
- **Dead Code Identification:** Archived scripts (24.2KB removed)
- **Modularity Assessment:** Well-modularized components, improvement areas
- **Automation Assessment:** Fully/partially/not automated operations
- **Performance Analysis:** Bottlenecks, memory usage, optimization opportunities
- **Security Assessment:** Secure practices, recommendations
- **Recommendations:** Immediate/short-term/long-term actions

**When to use:**
- Code review
- Performance optimization
- Security audit
- Technical debt assessment

---

## 🗂️ Archived Documentation

The following files have been **removed** to reduce clutter (content merged into above docs):

- ~~`BASELINE_READY.md`~~ → Merged into `claude/ROADMAP.md`
- ~~`PROJECT_STATUS.md`~~ → Merged into `claude/ROADMAP.md`
- ~~`claude/SETUP.md`~~ → Merged into `claude/ROADMAP.md` (Quick Start section)
- ~~`claude/IMPLEMENTATION_ROADMAP.md`~~ → Merged into `claude/ROADMAP.md`

---

## 📖 How to Use This Documentation

### For New Developers:

1. Start with **`README.md`** - Get the project running
2. Read **`CLAUDE.md`** - Understand architecture and commands
3. Reference **`claude/ROADMAP.md`** - Learn what's been built and what's next
4. Review **`COMPLIANCE.md`** - Understand legal requirements

### For Active Development:

1. **Quick reference:** `CLAUDE.md` (commands, file structure, rules)
2. **Detailed info:** `claude/ROADMAP.md` (architecture, troubleshooting)
3. **Planning:** `claude/ROADMAP.md` (Phase 1-3 roadmaps)

### For Code Review / Audit:

1. **Architecture:** `claude/ROADMAP.md` (Architecture Deep Dive section)
2. **Code quality:** `claude/CODEBASE_ANALYSIS.md`
3. **Compliance:** `COMPLIANCE.md`

---

## 🔍 Quick Lookup Table

| Need to... | See Document | Section |
|-----------|--------------|---------|
| Run ETL/signals | `CLAUDE.md` | Quick Reference → Essential Commands |
| Understand architecture | `CLAUDE.md` | Architecture Principles |
| Fix "No signals generated" | `claude/ROADMAP.md` | Troubleshooting Guide |
| Add new sport | `CLAUDE.md` | Common Tasks → Adding a New Sport |
| Review recent enhancements | `claude/ROADMAP.md` | Recent Enhancements (Oct 10, 2025) |
| Plan Phase 1 work | `claude/ROADMAP.md` | Phase 1: Model Refinement |
| **Prepare for real money betting** | `claude/ROADMAP.md` | **Phase 2.5: Promo System Deployment** |
| **Review promo tracking plan** | `claude/ROADMAP.md` | **Phase 2.5 → Implementation Tasks** |
| Check legal compliance | `COMPLIANCE.md` | Entire document |
| **Review promo compliance** | `COMPLIANCE.md` | **Section 2 → Promo Tracking (Phase 3)** |
| Review code quality | `claude/CODEBASE_ANALYSIS.md` | Code Quality Assessment |
| Optimize performance | `claude/CODEBASE_ANALYSIS.md` | Performance Analysis |
| Understand data flow | `claude/ROADMAP.md` | Architecture Deep Dive → Data Flow |
| Configure environment | `claude/ROADMAP.md` | Configuration Reference |
| Generate CLV reports | `CLAUDE.md` | Essential Commands → make clv-report |

---

## 📝 Documentation Maintenance

### When to Update:

- **`CLAUDE.md`**: After major architectural changes, new critical rules
- **`COMPLIANCE.md`**: After legal review, ToS changes, new data providers
- **`claude/ROADMAP.md`**: After completing phases, adding new features, major bugs
- **`claude/CODEBASE_ANALYSIS.md`**: After major refactoring, performance work, security audit

### Update Frequency:

- `CLAUDE.md`: As needed (major changes only)
- `COMPLIANCE.md`: Quarterly review
- `claude/ROADMAP.md`: Weekly (during active development)
- `claude/CODEBASE_ANALYSIS.md`: Monthly or after major refactoring

---

## 🎯 Current Status Summary

**System:** Production-ready with research-aligned NFL-only focus
**Phase:** Phase 1A - Quick Wins & Validation (✅ Line shopping complete)
**Documentation:** ✅ Complete and consolidated
**Code Quality:** ✅ Clean, modular, minimal technical debt
**Recent Enhancements:** ✅ Line shopping (+1-2% ROI), ✅ Milestone tracking, ✅ NFL-only workflows
**Next Phase:** Historical backtesting, continued paper betting accumulation

---

**Document Version:** 1.2
**Last Updated:** October 12, 2025
**Maintained by:** Dylan Suhr
