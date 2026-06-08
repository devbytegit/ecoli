# CLAUDE.md: E. coli Research Pipeline Project Guide

This document defines the development environment, execution commands, coding standards, and LLM Wiki schema. **Read this guide before executing any task in this workspace.**

---

## 🚀 Commands & Development Environment

The active Python virtual environment is located at `.venv/`. Always execute commands within this virtual environment.

### Environment Activation
*   **PowerShell:** `.\.venv\Scripts\Activate.ps1`
*   **CMD:** `.\.venv\Scripts\activate.bat`

### Execution Commands (From Workspace Root)
*   **Phase 1 (Data Collection):** `python pipeline/phase1_data_collection.py`
*   **Phase 2 (Claim Extraction):** `python pipeline/phase2_claim_extraction.py`
*   **Phase 2 Cleanup:** `python pipeline/phase2_claim_cleanup.py`
*   **Phase 3 (Clustering):** `python pipeline/phase3_semantic_clustering.py`
*   **Phase 4 (Pathway Mapping):** `python pipeline/phase4_pathway_mapping.py`
*   **Phase 5 (Temporal Analysis):** `python pipeline/phase5_temporal_analysis.py`
*   **Phase 6 (Comparative Analysis):** `python pipeline/phase6_comparative_analysis.py`
*   **Generate Publication Figures:** `python scripts/generate_figures.py`
*   **Compile Manuscript (Word):** `python scripts/build_docx.py`
*   **Run All Unit Tests:** `pytest`
*   **Verify Corpus Integrity:** `python utils/verify_corpus.py`
*   **Run Preflight Checks:** `python utils/preflight_check.py`

---

## 🎨 Coding Standards
*   **Python Version:** Python 3.14 (ensure standard streams use UTF-8: `sys.stdout.reconfigure(encoding='utf-8')`).
*   **Directories:** All pipeline code resides in `pipeline/`, user scripts in `scripts/`, tests in `tests/`, and helper/diagnostic utilities in `utils/`.
*   **Robust Imports:** Verify imports are resolved relative to the workspace root.
*   **JSON Enforcement:** Enforce strict JSON output structure for all LLM API extractions with fuzzy quote-matching verification to eliminate hallucinations.

---

## 🧠 LLM Wiki Schema (Andrej Karpathy Pattern)

The knowledge base is stored inside `ecoli_brain/` and contains three layers:
1.  **Raw Sources (`ecoli_brain/raw/sources/`):** Immutable research papers, chat clippings, and raw text files. Never modified.
2.  **Wiki Pages (`ecoli_brain/wiki/`):** Labeled summaries, objectives, results, and thematic analysis markdown files.
3.  **Schema (`CLAUDE.md`):** This file, guiding agents on wiki organization and workflows.

### Special Navigation Files
*   **Index (`ecoli_brain/wiki/index.md`):** Content-oriented directory. Organizes all wiki files by category.
*   **Log (`ecoli_brain/wiki/log.md`):** Chronological, append-only record of all ingestions and pipeline runs.
