"""Preflight check — Cerebras backend."""
from dotenv import load_dotenv
import os, json
from pathlib import Path

load_dotenv()
ok = True

key = os.getenv("CEREBRAS_API_KEY", "")
if key:
    print(f"[1] CEREBRAS_API_KEY : YES ({key[:12]}...)")
else:
    print("[1] CEREBRAS_API_KEY : NO - paste your key in .env")
    ok = False

import pandas as pd
corpus = Path("data/raw/corpus_raw.csv")
if corpus.exists():
    print(f"[2] Corpus           : YES — {len(pd.read_csv(corpus))} papers")
else:
    print("[2] Corpus           : MISSING")
    ok = False

jsonl = Path("data/processed/phase2_claims.jsonl")
done = sum(1 for l in open(jsonl, encoding="utf-8") if l.strip()) if jsonl.exists() else 0
print(f"[3] Already done     : {done} (remaining: {3273 - done})")

try:
    from openai import OpenAI
    client = OpenAI(base_url="https://api.cerebras.ai/v1", api_key=key)
    resp = client.chat.completions.create(
        model="gpt-oss-120b",
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": 'Reply only with valid JSON: {"status": "ok"}'}],
    )
    print(f"[4] Cerebras API     : OK — {resp.choices[0].message.content.strip()}")
except Exception as e:
    print(f"[4] Cerebras API     : FAILED — {e}")
    ok = False

try:
    import tenacity, jsonschema, tqdm
    print("[5] All imports      : OK")
except ImportError as e:
    print(f"[5] All imports      : FAILED — {e}")
    ok = False

print()
if ok:
    print("==> ALL CHECKS PASSED — run: python pipeline/phase2_claim_extraction.py")
else:
    print("==> Fix issues above first")
