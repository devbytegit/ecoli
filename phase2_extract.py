"""
APEX-BIO Research Pipeline
Phase 2: LLM-Augmented Claim Extraction (Groq backend)
=========================================================
Reads each abstract from Phase 1 corpus and extracts structured
justification claims for why the organism was used as a model microorganism.

Anti-hallucination measures:
  1. Temperature = 0         → deterministic, no creative generation
  2. Explicit null rule      → model must return null if no reason found
  3. Quote verification      → every extracted quote validated against
                               original abstract text (sliding-window fuzzy match)
  4. Schema validation       → every response validated against strict schema
  5. paper_id echo check     → verifies model returned the correct paper
  6. Progressive saving      → results saved per-paper, never lost on crash

Backend: Groq (llama-3.3-70b-versatile) — free tier, 1,000 RPM, no credit card
Study:   Computational Investigation of E. coli as Premier Model Microorganism
Author:  Olufisayo Timileyin Emmanuel
"""

import json
import logging
import os
import time
import re
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
from openai import OpenAI, RateLimitError, APIConnectionError, APIStatusError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from jsonschema import validate, ValidationError
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
CEREBRAS_API_KEY  = os.getenv("CEREBRAS_API_KEY", "")
OLLAMA_HOST       = os.getenv("OLLAMA_HOST", "")

# ── Backend selector (priority: Cerebras → Ollama → Groq) ────────────────────
if CEREBRAS_API_KEY:
    API_BASE_URL  = "https://api.cerebras.ai/v1"
    API_KEY       = CEREBRAS_API_KEY
    MODEL_NAME        = "gpt-oss-120b"
    REQUEST_DELAY     = 25.0   # 150 RPH limit → 3600s/150 = 24.0s minimum delay + 1.0s buffer
    MAX_OUTPUT_TOKENS = 1600    # Accommodates reasoning token overhead for gpt-oss-120b
    log_backend       = f"Cerebras | model: {MODEL_NAME}"
elif OLLAMA_HOST:
    API_BASE_URL  = f"{OLLAMA_HOST.rstrip('/')}/v1"
    API_KEY       = "ollama"
    MODEL_NAME        = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")
    REQUEST_DELAY     = 0.2
    MAX_OUTPUT_TOKENS = 1024   # no limit concern locally
    log_backend       = f"Ollama @ {OLLAMA_HOST} | model: {MODEL_NAME}"
else:
    API_BASE_URL  = "https://api.groq.com/openai/v1"
    API_KEY       = GROQ_API_KEY
    MODEL_NAME        = "llama-3.3-70b-versatile"
    REQUEST_DELAY     = 2.5
    MAX_OUTPUT_TOKENS = 600
    log_backend       = f"Groq | model: {MODEL_NAME}"
# ─────────────────────────────────────────────────────────────────────────────

TEMPERATURE     = 0.0
INPUT_CSV       = Path("data/raw/corpus_raw.csv")
OUTPUT_JSONL    = Path("data/processed/phase2_claims.jsonl")
OUTPUT_CSV      = Path("data/processed/phase2_claims.csv")
FAILED_LOG      = Path("data/processed/phase2_failed.jsonl")

# Fuzzy match threshold for quote verification
QUOTE_MATCH_THRESHOLD = 0.65

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

Path("data").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/phase2_run.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# JSON SCHEMA
# ─────────────────────────────────────────────

RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["paper_id", "explicit_reason_found", "justification_claims", "null_reason"],
    "additionalProperties": False,
    "properties": {
        "paper_id":             {"type": "string"},
        "explicit_reason_found": {"type": "boolean"},
        "justification_claims": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["claim", "category", "subcategory", "supporting_quote"],
                "additionalProperties": False,
                "properties": {
                    "claim":            {"type": "string", "minLength": 5},
                    "category":         {"type": "string", "enum": [
                                            "biological", "technical",
                                            "historical", "economic", "cultural",
                                        ]},
                    "subcategory":      {"type": "string", "minLength": 3},
                    "supporting_quote": {"type": "string", "minLength": 5},
                },
            },
        },
        "null_reason": {"type": ["string", "null"]},
    },
}

# ─────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a scientific literature analyst specializing in microbiology. "
    "You extract structured data from academic abstracts. "
    "You always return valid JSON exactly matching the requested schema. "
    "You never infer, guess, or use background knowledge — only what is explicitly in the text."
)

def build_user_prompt(paper_id: str, abstract: str, organism: str) -> str:
    return f"""Extract the explicit justification for why the authors chose {organism} as their model microorganism from the abstract below.

STRICT RULES:
1. Only extract reasons EXPLICITLY stated in the abstract.
2. Never infer or use background knowledge about {organism}.
3. supporting_quote must be verbatim or near-verbatim from the abstract.
4. If no explicit reason → explicit_reason_found=false, justification_claims=[], null_reason="explanation".
5. Return ONLY the JSON object. No markdown, no extra text.

CATEGORIES: biological | technical | historical | economic | cultural

PAPER ID: {paper_id}

ABSTRACT:
{abstract}

Return exactly:
{{
  "paper_id": "{paper_id}",
  "explicit_reason_found": true or false,
  "justification_claims": [
    {{
      "claim": "short reason in your own words",
      "category": "one of five categories",
      "subcategory": "specific label e.g. growth_kinetics",
      "supporting_quote": "verbatim phrase from abstract"
    }}
  ],
  "null_reason": null or "brief explanation"
}}"""


# ─────────────────────────────────────────────
# HALLUCINATION DETECTION — sliding window fuzzy match
# ─────────────────────────────────────────────

def quote_match_score(quote: str, abstract: str) -> float:
    """
    Best-matching substring score between quote and abstract.
    Uses sliding window so short quotes aren't unfairly penalised.
    """
    quote    = quote.lower().strip()
    abstract = abstract.lower().strip()

    if not quote:
        return 0.0
    if quote in abstract:
        return 1.0

    # Sliding window over abstract at quote length
    window = len(quote)
    best   = 0.0
    for i in range(max(1, len(abstract) - window + 1)):
        chunk = abstract[i : i + window]
        score = SequenceMatcher(None, quote, chunk).ratio()
        if score > best:
            best = score
            if best >= 0.95:   # Early exit on near-exact match
                return best
    return best


def validate_hallucination(result: dict, abstract: str) -> dict:
    """Verify every supporting_quote against the original abstract."""
    claims = result.get("justification_claims") or []
    if not claims:
        result["hallucination_flags"] = 0
        result["hallucination_free"]  = True
        return result

    for claim in claims:
        score = quote_match_score(claim.get("supporting_quote", ""), abstract)
        claim["quote_match_score"]  = round(score, 3)
        claim["hallucination_risk"] = score < QUOTE_MATCH_THRESHOLD

    flagged = sum(1 for c in claims if c["hallucination_risk"])
    result["hallucination_flags"] = flagged
    result["hallucination_free"]  = flagged == 0
    return result


# ─────────────────────────────────────────────
# GROQ/CEREBRAS API CALL — retry only on transient errors
# ─────────────────────────────────────────────

LAST_API_HEADERS: dict[str, str] = {}

# Cerebras free tier: 5 RPM, 150 RPH, 2400 RPD, 30K TPM, 1M TPD
# Stop 50 papers before daily limit as safety buffer
DAILY_REQUEST_LIMIT = 2_400
DAILY_BUDGET_BUFFER = 50   # stop at 2,350 to never hit the hard cap

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=10, max=60),
    retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
    reraise=True,
)
def call_api(client: OpenAI, paper_id: str, abstract: str, organism: str) -> str:
    """Call the configured LLM backend with proper token cap and return raw JSON."""
    global LAST_API_HEADERS
    raw_response = client.chat.completions.with_raw_response.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_completion_tokens=MAX_OUTPUT_TOKENS,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": build_user_prompt(paper_id, abstract, organism)},
        ],
    )
    LAST_API_HEADERS = {k.lower(): v for k, v in raw_response.headers.items()}
    response = raw_response.parse()
    return response.choices[0].message.content


def parse_json_response(raw: str) -> dict:
    """Parse JSON from model response, stripping any accidental markdown fences."""
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(cleaned)


# ─────────────────────────────────────────────
# RESUME SUPPORT
# ─────────────────────────────────────────────

def load_processed_ids(path: Path) -> set[str]:
    """Return set of paper_ids already written to the output JSONL."""
    if not path.exists():
        return set()
    processed = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                processed.add(str(json.loads(line).get("paper_id", "")))
            except json.JSONDecodeError:
                continue
    log.info("Resume: %d papers already processed — skipping", len(processed))
    return processed


# ─────────────────────────────────────────────
# JSONL → flat CSV builder
# ─────────────────────────────────────────────

def build_flat_csv(jsonl_path: Path, csv_path: Path) -> int:
    """Convert phase2_claims.jsonl to a flat CSV. Returns row count."""
    records = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue

            base = {
                "paper_id":  r["paper_id"],
                "organism":  r.get("organism", ""),
                "year":      r.get("year", ""),
                "journal":   r.get("journal", ""),
                "query_source": r.get("query_source", ""),
                "explicit_reason_found": r["explicit_reason_found"],
                "hallucination_free":    r.get("hallucination_free", True),
                "null_reason":           r.get("null_reason"),
            }
            claims = r.get("justification_claims") or []
            if not claims:
                records.append({**base, "claim": None, "category": None,
                                 "subcategory": None, "supporting_quote": None,
                                 "quote_match_score": None, "hallucination_risk": None})
            else:
                for c in claims:
                    records.append({**base,
                                    "claim":            c.get("claim"),
                                    "category":         c.get("category"),
                                    "subcategory":      c.get("subcategory"),
                                    "supporting_quote": c.get("supporting_quote"),
                                    "quote_match_score": c.get("quote_match_score"),
                                    "hallucination_risk": c.get("hallucination_risk")})

    pd.DataFrame(records).to_csv(csv_path, index=False)
    return len(records)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main() -> None:
    if not any([CEREBRAS_API_KEY, OLLAMA_HOST, GROQ_API_KEY]):
        log.error("No API key configured. Set CEREBRAS_API_KEY in your .env file.")
        return

    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    log.info("Backend: %s | temperature: %s", log_backend, TEMPERATURE)
    log.info("Delay per request: %.1fs | Max output tokens: %d", REQUEST_DELAY, MAX_OUTPUT_TOKENS)

    # Load corpus
    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")
    log.info("Corpus loaded: %d papers", len(df))

    # Resume: skip ONLY successfully processed papers.
    # Failed papers are retried — they may have failed due to quota, not bad data.
    processed_ids = load_processed_ids(OUTPUT_JSONL)
    df = df[~df["paper_id"].isin(processed_ids)].reset_index(drop=True)
    log.info("Already done: %d | Remaining: %d", len(processed_ids), len(df))

    # Counters
    success_count         = 0
    null_count            = 0
    schema_fail_count     = 0
    hallucination_flagged = 0
    failed_ids: list[str] = []
    daily_requests        = 0   # track requests this run vs daily cap

    try:
      with (
        open(OUTPUT_JSONL, "a", encoding="utf-8") as out_f,
        open(FAILED_LOG,   "a", encoding="utf-8") as fail_f,
      ):
        for row in tqdm(df.itertuples(index=False), total=len(df), desc="Phase 2"):
            paper_id = str(row.paper_id)
            abstract = str(row.abstract)
            organism = str(row.organism)
            raw      = None

            # Dynamic Quota Guard — inspect actual remaining limits from previous calls
            if CEREBRAS_API_KEY and LAST_API_HEADERS:
                rem_tokens_day = int(LAST_API_HEADERS.get("x-ratelimit-remaining-tokens-day", 99999999))
                rem_req_day = int(LAST_API_HEADERS.get("x-ratelimit-remaining-requests-day", 99999999))
                rem_req_hour = int(LAST_API_HEADERS.get("x-ratelimit-remaining-requests-hour", 99999999))

                if rem_tokens_day < 15000:
                    log.warning("Daily token limit approaching (%d remaining). Stopping run cleanly to protect quota.", rem_tokens_day)
                    break
                if rem_req_day < 20:
                    log.warning("Daily request limit approaching (%d remaining). Stopping run cleanly to protect quota.", rem_req_day)
                    break
                if rem_req_hour < 5:
                    log.warning("Hourly request limit approaching (%d remaining). Stopping run cleanly to protect quota.", rem_req_hour)
                    break

            paper_attempts = 0
            max_paper_attempts = 3
            success = False

            while paper_attempts < max_paper_attempts and not success:
                paper_attempts += 1
                try:
                    # 1 — Call model
                    raw = call_api(client, paper_id, abstract, organism)
                    daily_requests += 1

                    if not raw:
                        log.error("API returned empty/None content for paper %s (likely ran out of reasoning tokens). Skipping.", paper_id)
                        failed_ids.append(paper_id)
                        fail_f.write(json.dumps({
                            "paper_id": paper_id, "reason": "empty_content",
                        }) + "\n")
                        success = True  # skip to next paper, don't retry empty content
                        continue

                    # 2 — Parse JSON
                    result = parse_json_response(raw)

                    # 3 — Schema validation
                    try:
                        validate(instance=result, schema=RESPONSE_SCHEMA)
                    except ValidationError as ve:
                        log.warning("Schema fail %s: %s", paper_id, ve.message)
                        schema_fail_count += 1
                        fail_f.write(json.dumps({
                            "paper_id": paper_id, "reason": "schema_validation_failed",
                            "detail": ve.message, "raw_response": raw,
                        }) + "\n")
                        success = True  # skip to next paper, don't retry schema failures
                        continue

                    # 4 — Correct paper_id if model returned wrong one
                    if str(result.get("paper_id")) != paper_id:
                        log.warning("paper_id mismatch: expected %s got %s — correcting",
                                    paper_id, result.get("paper_id"))
                        result["paper_id"] = paper_id

                    # 5 — Hallucination detection
                    result = validate_hallucination(result, abstract)

                    # 6 — Enrich with metadata
                    result["organism"]     = organism
                    result["year"]         = str(getattr(row, "year", ""))
                    result["journal"]      = str(getattr(row, "journal", ""))
                    result["query_source"] = str(getattr(row, "query_source", ""))

                    # 7 — Save immediately
                    out_f.write(json.dumps(result) + "\n")
                    out_f.flush()

                    # 8 — Update counters
                    success_count += 1
                    if not result["explicit_reason_found"]:
                        null_count += 1
                    if result.get("hallucination_flags", 0) > 0:
                        hallucination_flagged += 1
                        log.warning("Hallucination risk — paper_id=%s", paper_id)

                    success = True

                except json.JSONDecodeError as e:
                    log.error("JSON parse failed %s: %s", paper_id, e)
                    failed_ids.append(paper_id)
                    fail_f.write(json.dumps({
                        "paper_id": paper_id, "reason": "json_parse_failed",
                        "raw_response": raw or "no response",
                    }) + "\n")
                    success = True  # skip to next paper, don't retry unparseable responses

                except RateLimitError as e:
                    err_msg = str(e).lower()
                    if "queue_exceeded" in err_msg or "high traffic" in err_msg:
                        if paper_attempts < max_paper_attempts:
                            log.warning("Cerebras queue full (attempt %d/%d) for paper %s. Sleeping 45s...",
                                        paper_attempts, max_paper_attempts, paper_id)
                            time.sleep(45)
                            continue
                        else:
                            log.error("Cerebras queue remains full after %d attempts for paper %s. Stopping run.", max_paper_attempts, paper_id)
                            failed_ids.append(paper_id)
                            fail_f.write(json.dumps({
                                "paper_id": paper_id, "reason": "rate_limit_queue_exceeded",
                                "detail": str(e),
                            }) + "\n")
                            break
                    else:
                        log.error("Quota rate limit reached (429) %s: %s. Stopping run to protect quota. Resume later.", paper_id, e)
                        failed_ids.append(paper_id)
                        fail_f.write(json.dumps({
                            "paper_id": paper_id, "reason": "rate_limit_reached",
                            "detail": str(e),
                        }) + "\n")
                        break

                except APIStatusError as e:
                    log.error("API status error %s: %s", paper_id, e)
                    failed_ids.append(paper_id)
                    fail_f.write(json.dumps({
                        "paper_id": paper_id, "reason": "api_status_error",
                        "detail": str(e),
                    }) + "\n")
                    success = True  # skip to next paper, don't retry status errors

                except Exception as e:
                    log.error("Unexpected error %s: %s", paper_id, e)
                    failed_ids.append(paper_id)
                    fail_f.write(json.dumps({
                        "paper_id": paper_id, "reason": "unexpected_error",
                        "detail": str(e),
                    }) + "\n")
                    success = True  # skip to next paper, don't retry unexpected exceptions

                finally:
                    if success:
                        time.sleep(REQUEST_DELAY)

            if not success:
                break

    except KeyboardInterrupt:
        log.warning("Interrupted by user (Ctrl+C) — progress saved. Resume with: python phase2_extract.py")

    # ── always runs: on normal finish, budget guard break, or Ctrl+C ──────────
    def print_summary() -> None:
        done_total = len(load_processed_ids(OUTPUT_JSONL))
        log.info("=" * 45)
        log.info("SESSION SUMMARY")
        log.info("=" * 45)
        log.info("Processed this session : %d", success_count)
        log.info("Total done in corpus   : %d / 3273", done_total)
        log.info("Remaining              : %d", 3273 - done_total)
        log.info("No reason found        : %d", null_count)
        log.info("Schema failures        : %d", schema_fail_count)
        log.info("Hallucination flagged  : %d", hallucination_flagged)
        log.info("API failures           : %d", len(failed_ids))
        if done_total < 3273:
            log.info("Resume anytime with   : python phase2_extract.py")
        log.info("=" * 45)

    # Build flat CSV from whatever is done so far
    if OUTPUT_JSONL.exists():
        log.info("Building flat CSV...")
        row_count = build_flat_csv(OUTPUT_JSONL, OUTPUT_CSV)
        log.info("CSV saved: %s (%d rows)", OUTPUT_CSV, row_count)

    print_summary()


if __name__ == "__main__":
    main()
