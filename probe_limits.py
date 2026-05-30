"""
Probe Cerebras rate limits by making a real call and reading response headers.
Also tests the exact prompt shape we'll use in phase2 so token counts are accurate.
"""
from dotenv import load_dotenv
import os, time, json
import httpx

load_dotenv()
KEY = os.getenv("CEREBRAS_API_KEY", "")
URL = "https://api.cerebras.ai/v1/chat/completions"
MODEL = "gpt-oss-120b"

# Simulate a real abstract (avg length from corpus)
SAMPLE_ABSTRACT = (
    "Escherichia coli has served as the premier model microorganism for studying "
    "fundamental biological processes due to its rapid growth rate, well-characterized "
    "genetics, and ease of genetic manipulation. In this study, we exploited the genetic "
    "tractability of E. coli to investigate the mechanisms of antibiotic resistance. "
    "The organism's short doubling time of approximately 20 minutes allowed us to "
    "conduct multiple experimental iterations within a single working day. Furthermore, "
    "its fully sequenced genome and the availability of comprehensive knockout libraries "
    "facilitated systematic analysis of resistance mechanisms. These properties make "
    "E. coli an indispensable tool for molecular biology research."
)

payload = {
    "model": MODEL,
    "temperature": 0.0,
    "max_completion_tokens": 600,   # ← CRITICAL: caps token counting
    "response_format": {"type": "json_object"},
    "messages": [
        {"role": "system", "content": "You extract structured data from scientific abstracts. Return valid JSON only."},
        {"role": "user",   "content": f'Extract justification for using E. coli as model organism. Abstract: {SAMPLE_ABSTRACT}\nReturn: {{"paper_id": "test", "explicit_reason_found": true, "justification_claims": [], "null_reason": null}}'}
    ]
}

print(f"Model     : {MODEL}")
print(f"Calling   : {URL}")
print()

with httpx.Client(timeout=60) as client:
    t0 = time.time()
    resp = client.post(
        URL,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json=payload,
    )
    elapsed = time.time() - t0

print(f"Status    : {resp.status_code}")
print(f"Latency   : {elapsed:.2f}s")
print()

# Print all rate limit headers
print("=== RATE LIMIT HEADERS ===")
limits = {}
for k, v in resp.headers.items():
    if "ratelimit" in k.lower():
        print(f"  {k}: {v}")
        limits[k] = v
print()

if resp.status_code == 200:
    data = resp.json()
    usage = data.get("usage", {})
    print("=== TOKEN USAGE (this call) ===")
    print(f"  Input tokens  : {usage.get('prompt_tokens', '?')}")
    print(f"  Output tokens : {usage.get('completion_tokens', '?')}")
    print(f"  Total tokens  : {usage.get('total_tokens', '?')}")
    print()

    # Calculate safe delay from actual limits
    tpm_limit = int(limits.get("x-ratelimit-limit-tokens-minute", 0))
    rpd_limit = int(limits.get("x-ratelimit-limit-requests-day", 0))
    tpd_limit = int(limits.get("x-ratelimit-limit-tokens-day", 0))

    tokens_per_call = usage.get("total_tokens", 1500)

    print("=== CALCULATED SAFE SETTINGS ===")
    if tpm_limit and tpm_limit < 1_000_000_000:
        safe_rpm = (tpm_limit * 0.75) / tokens_per_call   # 75% of TPM limit
        safe_delay = 60 / safe_rpm
        print(f"  TPM limit     : {tpm_limit:,}")
        print(f"  Tokens/call   : {tokens_per_call}")
        print(f"  Safe RPM (75%): {safe_rpm:.1f}")
        print(f"  Safe delay    : {safe_delay:.1f}s  ← use this as REQUEST_DELAY")
    if tpd_limit and tpd_limit < 1_000_000_000:
        max_papers_day = int(tpd_limit * 0.9 / tokens_per_call)
        days_needed    = 3273 / max_papers_day
        print(f"  TPD limit     : {tpd_limit:,}")
        print(f"  Max papers/day: {max_papers_day}")
        print(f"  Days to finish: {days_needed:.1f}")
    if rpd_limit and rpd_limit < 1_000_000_000:
        print(f"  RPD limit     : {rpd_limit:,}")
else:
    print(f"ERROR: {resp.text}")
