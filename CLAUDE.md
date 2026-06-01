# CLAUDE.md: E. coli Research Pipeline Project Guide

This document defines the development environment, build commands, coding standards, and LLM Wiki schema. **Read this guide before executing any task in this workspace.**

---

## 🚀 Commands & Development Environment

The active Python virtual environment is located at `.venv/`. Always execute commands within this virtual environment.

### Environment Activation
*   **PowerShell:** `.\.venv\Scripts\Activate.ps1`
*   **CMD:** `.\.venv\Scripts\activate.bat`

### Execution Commands
*   **Run Clustering Pipeline (Phase 3):** `python -u phase3_cluster.py`
*   **Run Extraction Pipeline (Phase 2):** `python phase2_extract.py`
*   **Verify Corpus:** `python verify_corpus.py`
*   **Run Tests:** `pytest` (e.g. `pytest test_phase2.py`)

---

## 🎨 Coding Standards
*   **Python Version:** Python 3.14 (ensure standard streams use UTF-8: `sys.stdout.reconfigure(encoding='utf-8')`).
*   **Robust Imports:** Prefer explicit packages, verify dependencies in `.venv/` using `pip list`.
*   **Caching Support:** Before generating heavy data or executing slow API requests, check if cache outputs exist (e.g. `data/processed/phase3_embeddings.npy`) and load them directly.
*   **JSON Enforcement:** Always enforce strict JSON output format from LLM API calls with matching schema verification and self-correction guardrails.

---

## 🧠 LLM Wiki Schema (Andrej Karpathy Pattern)

The knowledge base is stored inside `ecoli_brain/` and contains three layers:
1.  **Raw Sources (`ecoli_brain/raw/sources/`):** Immutable research papers, chat clippings, and raw text files. Never modified.
2.  **Wiki Pages (`ecoli_brain/wiki/`):** Labeled summaries, objectives, results, and thematic analysis markdown files.
3.  **Schema (`CLAUDE.md`):** This file, guiding agents on wiki organization and workflows.

### Special Navigation Files
*   **Index (`ecoli_brain/wiki/index.md`):** Content-oriented directory. Organizes all wiki files by category with a one-line description and a markdown link.
*   **Log (`ecoli_brain/wiki/log.md`):** Chronological, append-only record of all ingestions and pipeline runs. Format: `## [YYYY-MM-DD] action | Description`.

### LLM Wiki Operations

#### 1. Ingest Workflow
When a new raw source file is placed in `ecoli_brain/raw/sources/`:
1.  Read the source file content.
2.  Write a summary page or update relevant pages in `ecoli_brain/wiki/`.
3.  Add the new page to the Index (`index.md`) under the correct category.
4.  Append an entry to the Chronological Log (`log.md`) with format: `## [YYYY-MM-DD] ingest | Source Name`.

#### 2. Query Workflow
When answering queries, the agent must:
1.  Read the Index (`index.md`) to find relevant wiki pages.
2.  Read the target wiki pages to synthesize an answer.
3.  Save complex comparisons or findings back to `ecoli_brain/wiki/` as new knowledge pages.

#### 3. Lint Workflow
Periodically, run a check over the wiki to find:
*   Contradictions or outdated claims.
*   Orphan pages (no links in `index.md` or other pages).
*   Missing cross-references between related pages.
