"""
APEX-BIO Research Pipeline
Phase 1: PubMed Data Collection
================================
Collects peer-reviewed abstracts from PubMed where E. coli (and comparison
organisms) are explicitly referenced as model microorganisms.

Study: Computational Investigation of E. coli as Premier Model Microorganism
Author: Olufisayo Timileyin Emmanuel
"""

import os
import re
import time
import logging
import csv
import tempfile
import shutil

from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm
from Bio import Entrez
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file


# ─────────────────────────────────────────────
# CONFIGURATION — Edit only this section
# ─────────────────────────────────────────────

ENTREZ_EMAIL     = os.getenv("ENTREZ_EMAIL")
ENTREZ_API_KEY   = os.getenv("ENTREZ_API_KEY")
BATCH_SIZE       = 200                               # Records fetched per API call
OUTPUT_DIR       = Path("data/raw")                  # Where to save outputs
DATE_START       = "1990"
DATE_END         = "2025"                              
MAX_RETRIES      = 3                                 # Retry count for transient API failures
RETRY_BACKOFF    = 2.0                               # Exponential backoff multiplier (seconds)

# Dynamic rate limiting: NCBI allows 10 req/sec with API key, 3/sec without
RATE_LIMIT_DELAY = 0.11 if ENTREZ_API_KEY else 0.4

# ─────────────────────────────────────────────
# SEARCH QUERIES
# ─────────────────────────────────────────────

QUERIES = {
    # --- E. coli primary queries ---
    "ecoli_model_organism": (
        '("Escherichia coli"[Title/Abstract] AND "model organism"[Title/Abstract])'
        f' AND ("{DATE_START}"[Date - Publication] : "{DATE_END}"[Date - Publication])'
        ' AND (journal article[Publication Type])'
        ' AND (hasabstract)'
        ' AND (English[Language])'
    ),
    "ecoli_model_system": (
        '("Escherichia coli"[Title/Abstract] AND "model system"[Title/Abstract])'
        f' AND ("{DATE_START}"[Date - Publication] : "{DATE_END}"[Date - Publication])'
        ' AND (journal article[Publication Type])'
        ' AND (hasabstract)'
        ' AND (English[Language])'
    ),
    "ecoli_abbrev_model_organism": (
        '("E. coli"[Title/Abstract] AND "model organism"[Title/Abstract])'
        f' AND ("{DATE_START}"[Date - Publication] : "{DATE_END}"[Date - Publication])'
        ' AND (journal article[Publication Type])'
        ' AND (hasabstract)'
        ' AND (English[Language])'
    ),
    "ecoli_model_bacterium": (
        '("Escherichia coli"[Title/Abstract] AND "model bacterium"[Title/Abstract])'
        f' AND ("{DATE_START}"[Date - Publication] : "{DATE_END}"[Date - Publication])'
        ' AND (journal article[Publication Type])'
        ' AND (hasabstract)'
        ' AND (English[Language])'
    ),
    "ecoli_reference_organism": (
        '("Escherichia coli"[Title/Abstract] AND "reference organism"[Title/Abstract])'
        f' AND ("{DATE_START}"[Date - Publication] : "{DATE_END}"[Date - Publication])'
        ' AND (journal article[Publication Type])'
        ' AND (hasabstract)'
        ' AND (English[Language])'
    ),

    # --- Comparison organism queries (Obj 6) ---
    "yeast_model_organism": (
        '("Saccharomyces cerevisiae"[Title/Abstract] AND "model organism"[Title/Abstract])'
        f' AND ("{DATE_START}"[Date - Publication] : "{DATE_END}"[Date - Publication])'
        ' AND (journal article[Publication Type])'
        ' AND (hasabstract)'
        ' AND (English[Language])'
    ),
    "bacillus_model_organism": (
        '("Bacillus subtilis"[Title/Abstract] AND "model organism"[Title/Abstract])'
        f' AND ("{DATE_START}"[Date - Publication] : "{DATE_END}"[Date - Publication])'
        ' AND (journal article[Publication Type])'
        ' AND (hasabstract)'
        ' AND (English[Language])'
    ),
}

# Map each query to its target organism label
QUERY_ORGANISM_MAP = {
    "ecoli_model_organism":          "E. coli",
    "ecoli_model_system":            "E. coli",
    "ecoli_abbrev_model_organism":   "E. coli",
    "ecoli_model_bacterium":         "E. coli",
    "ecoli_reference_organism":      "E. coli",
    "yeast_model_organism":          "S. cerevisiae",
    "bacillus_model_organism":       "B. subtilis",
}

# Regex for MEDLINE tag lines: 1-4 uppercase chars, 0-3 spaces padding, then "- "
_MEDLINE_TAG_RE = re.compile(r"^([A-Z]{1,4})\s{0,3}- (.*)$")


# ─────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────

def _setup_logging() -> None:
    """Configure logging with both console and file handlers."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT_DIR.parent / "phase1_run.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def setup_entrez() -> None:
    """Configure Biopython Entrez with email and optional API key."""
    Entrez.email = ENTREZ_EMAIL
    if ENTREZ_API_KEY:
        Entrez.api_key = ENTREZ_API_KEY
    log.info("Entrez configured — email: %s | API key: %s",
             ENTREZ_EMAIL, "yes" if ENTREZ_API_KEY else "no (3 req/sec limit)")


def _retry_call(func, *args, **kwargs):
    """
    Call `func` with retry + exponential backoff for transient NCBI errors.
    Returns the result on success, raises on exhaustion.
    """
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF ** attempt
                log.warning("  ⚠ Attempt %d/%d failed: %s — retrying in %.1fs",
                            attempt, MAX_RETRIES, exc, wait)
                time.sleep(wait)
            else:
                log.error("  ✖ All %d attempts failed: %s", MAX_RETRIES, exc)
    raise last_exc  # type: ignore[misc]


def search_and_fetch(query: str, query_name: str) -> tuple[int, list[dict[str, Any]], list[int]]:
    """
    Search PubMed and fetch records in a single pass using EHistory streaming.

    Instead of: esearch → loop esearch for PMIDs → efetch with PMIDs
    We do:      esearch (once, get WebEnv) → efetch directly via WebEnv/QueryKey

    This eliminates redundant API calls and avoids holding all PMIDs in memory.

    Returns:
        (total_count, records, failed_batch_offsets)
    """
    log.info("Searching PubMed -- query: %s", query_name)
    failed_batches: list[int] = []

    try:
        handle = _retry_call(
            Entrez.esearch,
            db="pubmed",
            term=query,
            usehistory="y",
            retmax=0,           # We only want the count + WebEnv
        )
        result = Entrez.read(handle)
        handle.close()

        count     = int(result["Count"])
        web_env   = result["WebEnv"]
        query_key = result["QueryKey"]
        log.info("  -> %d records found on server", count)

        if count == 0:
            return 0, [], []

    except Exception as exc:
        log.error("Search failed for %s: %s", query_name, exc)
        return 0, [], []

    # Stream records directly from server via WebEnv — no intermediate PMID list
    records: list[dict[str, Any]] = []
    num_batches = (count + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx, start in enumerate(
        tqdm(range(0, count, BATCH_SIZE), desc=f"  Fetching {query_name}", total=num_batches)
    ):
        time.sleep(RATE_LIMIT_DELAY)
        try:
            fetch_handle = _retry_call(
                Entrez.efetch,
                db="pubmed",
                WebEnv=web_env,
                query_key=query_key,
                retstart=start,
                retmax=BATCH_SIZE,
                rettype="medline",
                retmode="text",
            )
            raw = fetch_handle.read()
            fetch_handle.close()

            # Ensure we have a string, not bytes
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")

            records.extend(parse_medline_batch(raw))
        except Exception as exc:
            failed_batches.append(start)
            log.error("  Batch %d failed (offset=%d): %s", batch_idx + 1, start, exc)

    if failed_batches:
        log.warning("  %d/%d batches failed for %s — data may be incomplete",
                    len(failed_batches), num_batches, query_name)

    return count, records, failed_batches


def parse_medline_batch(raw_text: str) -> list[dict[str, Any]]:
    """
    Parse raw MEDLINE format text into a list of record dicts.

    MEDLINE fields we extract:
        PMID  → paper_id
        TI    → title
        AB    → abstract
        DP    → year (first 4 chars)
        TA    → journal
        MH    → mesh_terms (joined)
        AU    → authors (first author)
    """
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    current_field: str | None = None

    def _new_record(pmid_value: str) -> dict[str, Any]:
        return {
            "paper_id": pmid_value,
            "title": "",
            "abstract": "",
            "year": "",
            "journal": "",
            "authors": [],
            "mesh_terms": [],
        }

    for line in raw_text.splitlines():
        # Match MEDLINE tag line using regex (handles 1-4 char tags correctly)
        m = _MEDLINE_TAG_RE.match(line)
        if m:
            tag   = m.group(1)
            value = m.group(2).strip()
            current_field = tag

            if tag == "PMID":
                # Save previous record before starting new one
                if current.get("paper_id") and current.get("abstract"):
                    records.append(current)
                current = _new_record(value)

            # Guard: skip field assignments if no PMID seen yet
            elif not current.get("paper_id"):
                continue

            elif tag == "TI":
                current["title"] = value
            elif tag == "AB":
                current["abstract"] = value
            elif tag == "DP":
                current["year"] = value[:4]       # "2019 Mar" → "2019"
            elif tag == "TA":
                current["journal"] = value
            elif tag == "AU":
                current["authors"].append(value)
            elif tag == "MH":
                current["mesh_terms"].append(value)

        # Continuation line (starts with spaces)
        elif line.startswith("      ") and current_field and current:
            value = line.strip()
            if current_field == "TI":
                current["title"] += " " + value
            elif current_field == "AB":
                current["abstract"] += " " + value
            elif current_field == "MH":
                # MeSH terms can span continuation lines
                if current["mesh_terms"]:
                    current["mesh_terms"][-1] += " " + value
            elif current_field == "AU":
                # Author names can span continuation lines
                if current["authors"]:
                    current["authors"][-1] += " " + value

    # Catch the last record
    if current.get("paper_id") and current.get("abstract"):
        records.append(current)

    return records


def build_dataframe(all_records: list[dict]) -> pd.DataFrame:
    """
    Convert raw records to a clean DataFrame:
    - Flatten list fields (authors, mesh_terms)
    - Drop rows missing critical fields
    - Deduplicate by paper_id (PMID)
    """
    if not all_records:
        log.warning("No records to build DataFrame from")
        return pd.DataFrame(columns=[
            "paper_id", "organism", "query_source",
            "title", "abstract", "year", "journal",
            "authors", "mesh_terms",
        ])

    # Work on copies to avoid mutating the caller's data
    cleaned = []
    for rec in all_records:
        row = rec.copy()
        row["authors"]    = "; ".join(row.get("authors", []) if isinstance(row.get("authors"), list) else [])
        row["mesh_terms"] = "; ".join(row.get("mesh_terms", []) if isinstance(row.get("mesh_terms"), list) else [])
        cleaned.append(row)

    df = pd.DataFrame(cleaned)

    # Keep only rows with a real abstract
    before = len(df)
    df = df[df["abstract"].str.strip().str.len() > 30]
    log.info("Dropped %d rows with missing/short abstracts", before - len(df))

    # Deduplicate by PMID
    before = len(df)
    df = df.drop_duplicates(subset="paper_id")
    log.info("Removed %d duplicate PMIDs", before - len(df))

    # Ensure year is numeric where possible
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Enforce study scope: 1990–2025 only
    before = len(df)
    df = df[df["year"] <= 2025]
    log.info("Dropped %d papers outside study scope (year > 2025)", before - len(df))

    # Reorder columns cleanly
    expected_cols = ["paper_id", "organism", "query_source",
                     "title", "abstract", "year", "journal",
                     "authors", "mesh_terms"]
    # Only select columns that actually exist (defensive)
    df = df[[c for c in expected_cols if c in df.columns]]

    return df.reset_index(drop=True)


def _save_csv_atomic(df: pd.DataFrame, path: Path, **kwargs) -> None:
    """
    Write a DataFrame to CSV atomically: write to a temp file first,
    then rename. Prevents corrupt/partial files on crash.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".csv.tmp",
        dir=str(path.parent),
    )
    try:
        # Close the raw fd, pandas will open by name
        os.close(tmp_fd)
        df.to_csv(tmp_path, **kwargs)
        shutil.move(tmp_path, str(path))
    except Exception:
        # Clean up temp file on failure
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except OSError:
            pass
        raise


# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────

def main() -> None:
    _setup_logging()
    global log
    log = logging.getLogger(__name__)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    setup_entrez()

    all_records: list[dict] = []
    query_summary: list[dict] = []
    all_failed_batches: dict[str, list[int]] = {}
    total_queries = len(QUERIES)

    for idx, (query_name, query_str) in enumerate(QUERIES.items(), 1):
        organism = QUERY_ORGANISM_MAP.get(query_name)
        if organism is None:
            log.error("No organism mapping for query '%s' -- skipping", query_name)
            continue

        log.info("=" * 50)
        log.info("Query [%d/%d]: %s | Organism: %s", idx, total_queries, query_name, organism)

        server_count, records, failed_batches = search_and_fetch(query_str, query_name)

        if failed_batches:
            all_failed_batches[query_name] = failed_batches

        # Tag each record with organism and query source
        for rec in records:
            rec["organism"]     = organism
            rec["query_source"] = query_name

        all_records.extend(records)
        query_summary.append({
            "query_name": query_name,
            "organism":   organism,
            "server_count": server_count,
            "records_with_abstract": len(records),
            "failed_batches": len(failed_batches),
        })
        log.info("  -> %d records with abstracts collected", len(records))

    # -- Build and clean final dataframe --
    log.info("=" * 50)
    log.info("Building final dataset...")
    df = build_dataframe(all_records)

    # ── Save outputs ──
    output_path  = OUTPUT_DIR / "corpus_raw.csv"
    summary_path = OUTPUT_DIR / "query_summary.csv"

    _save_csv_atomic(df, output_path, index=False, quoting=csv.QUOTE_ALL)
    _save_csv_atomic(pd.DataFrame(query_summary), summary_path, index=False)

    # ── Final report ──
    log.info("=" * 50)
    log.info("PHASE 1 COMPLETE")
    log.info("=" * 50)
    log.info("Total records collected : %d", len(df))

    if len(df) > 0:
        log.info("E. coli papers          : %d", len(df[df["organism"] == "E. coli"]))
        log.info("S. cerevisiae papers    : %d", len(df[df["organism"] == "S. cerevisiae"]))
        log.info("B. subtilis papers      : %d", len(df[df["organism"] == "B. subtilis"]))

        valid_years = df["year"].dropna()
        if len(valid_years) > 0:
            log.info("Year range              : %d - %d",
                     int(valid_years.min()), int(valid_years.max()))
    else:
        log.warning("No records were collected -- check network and query parameters")

    log.info("Saved to                : %s", output_path)
    log.info("Query summary saved to  : %s", summary_path)

    # ── Dataset integrity check ──
    if all_failed_batches:
        log.warning("=" * 50)
        log.warning("DATASET INTEGRITY WARNING")
        log.warning("%d queries had failed batches:", len(all_failed_batches))
        for qname, offsets in all_failed_batches.items():
            log.warning("  %s: %d batches failed (offsets: %s)", qname, len(offsets), offsets)
        log.warning("Re-run the script to attempt recovery of missing records.")
        log.warning("=" * 50)
    else:
        log.info("Dataset integrity: ALL batches succeeded -- no data gaps.")

    log.info("=" * 50)


# Module-level logger placeholder (configured in main)
log = logging.getLogger(__name__)

if __name__ == "__main__":
    main()