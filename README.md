# Quantifying the Premier Model Microorganism

A computational literature-mining, semantic clustering, and database mapping study investigating why *Escherichia coli* is established as the premier model organism of molecular biology.

---

## 📂 Repository Directory Map

The workspace has been organized into a professional, structured directory layout:

```
c:\Users\olufi\Desktop\QUICK FILES\ECOLI\
│
├── paper_draft/             # Raw Markdown drafts for each section (01_abstract.md - 07_references.md)
│
├── manuscript/              # Microsoft Word Compiled Manuscripts
│   ├── README.txt           # File register for the manuscripts
│   ├── RESEARCH_MASTER_GUIDE.md    # Project Master Research Guide
│   ├── ECOLI_Model_Organism_Manuscript.docx        # ACTIVE manuscript file (linked in your Word editor)
│   └── archive/             # Archive of older drafts
│       ├── ECOLI_Model_Organism_Manuscript_v1_draft.docx   # Basic v1 draft
│       └── ECOLI_Model_Organism_Manuscript_v2_backup.docx   # Backup v2 compilation
│
├── pipeline/                # Computational Pipeline Scripts (Phases 1-6)
│   ├── phase1_data_collection.py      # PubMed download and parsing (script.py)
│   ├── phase2_claim_extraction.py     # Cerebras LLM extraction (phase2_extract.py)
│   ├── phase2_claim_cleanup.py        # Hallucination filter (cleanup_phase2.py)
│   ├── phase3_semantic_clustering.py  # PubMedBERT + UMAP + HDBSCAN clustering (phase3_cluster.py)
│   ├── phase4_pathway_mapping.py      # KEGG and EcoCyc database mapping
│   ├── phase5_temporal_analysis.py    # Decadal trends over time
│   └── phase6_comparative_analysis.py # Cross-organism normalized matrix
│
├── scripts/                 # Main User-Facing Action Scripts
│   ├── generate_figures.py  # Re-generates all 9 publication-grade Matplotlib figures
│   └── build_docx.py        # Compiles markdown drafts and figures into the final Word document
│
├── tests/                   # pytest Unit Test Suite
│   ├── test_parser.py       # Unit tests for the PubMed MEDLINE parser
│   └── test_phase2.py       # Unit tests for JSON schema and quote-matching
│
├── utils/                   # Developer Diagnostics and Utilities
│   ├── preflight_check.py   # Imports and API key validator
│   ├── probe_limits.py      # API rate limits checker
│   ├── list_models.py       # Queries Cerebras/Groq for active models
│   ├── verify_corpus.py     # Structural checks on the downloaded dataset
│   ├── verify_data.py       # Data integrity checker
│   ├── read_clusters.py     # Summarizes text themes per cluster
│   ├── query_kegg.py        # Connects to rest.kegg.jp
│   ├── extract_references.py# Reference metadata scraper
│   └── test_legend_positions.py # Visual layout debugger
│
├── data/                    # Datasets and Visual Elements
│   ├── raw/                 # Raw corpus CSV (3,273 papers)
│   ├── processed/           # Processed datasets, embeddings, and cluster mapping CSVs
│   └── figures/             # 9 Publication figures (fig1_... through fig9_...)
│
├── ecoli_brain/             # Obsidian Research Wiki (Karpathy Method log)
│

├── CLAUDE.md                # Quick reference coding standards and execution wiki
└── requirements.txt         # Python virtual environment library dependencies
```

---

## 📝 Finding Your Manuscript Files
To prevent confusion around duplicate files, the manuscripts are structured as follows:

1.  **`manuscript/ECOLI_Model_Organism_Manuscript.docx`**
    *   *Role:* The active, live document that you can edit. It has been updated with all centered figures, shaded tables, en-dash sub-bullets, and clean inline formatting.
2.  **`manuscript/archive/`**
    *   *Role:* Archives older, deprecated drafts (like the uncorrected v1 draft) to keep your main workspace neat while preventing any data loss.

---

## 🚀 Execution Instructions

All commands must be executed within your Python virtual environment.

### 1. Activating the Environment
*   **PowerShell:** `.\.venv\Scripts\Activate.ps1`
*   **CMD:** `.\.venv\Scripts\activate.bat`

### 2. Compiling the Manuscript
If you edit the text files in `paper_draft/` and want to compile a fresh Word manuscript, run:
```bash
python scripts/build_docx.py
```
This builds directly to `ECOLI_Model_Organism_Manuscript.docx` in the root and updates the backup in `manuscript/`.

### 3. Re-generating Figures
If you need to tweak style parameters or colors in the figures, edit the plotting code in `scripts/generate_figures.py` and run:
```bash
python scripts/generate_figures.py
```
All figures are saved to `data/figures/`.

### 4. Running the Pipeline Phases
The pipeline stages are saved in `pipeline/` and run sequentially:
```bash
# Phase 1: Download raw abstracts
python pipeline/phase1_data_collection.py

# Phase 2: Run LLM extraction and filter out hallucinations
python pipeline/phase2_claim_extraction.py
python pipeline/phase2_claim_cleanup.py

# Phase 3: Cluster semantic justifications
python pipeline/phase3_semantic_clustering.py

# Phases 4-6: Run database mapping, temporal shifts, and comparative analysis
python pipeline/phase4_pathway_mapping.py
python pipeline/phase5_temporal_analysis.py
python pipeline/phase6_comparative_analysis.py
```

### 5. Running Tests
To run unit tests and ensure the parser is fully functional:
```bash
pytest
```
