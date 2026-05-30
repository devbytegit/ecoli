"""Clean up phase2 output files — remove 429 false-alarm failure entries."""
import json, shutil
from pathlib import Path

claims  = Path("data/processed/phase2_claims.jsonl")
failed  = Path("data/processed/phase2_failed.jsonl")
archive = Path("data/processed/phase2_failed_groq_quota.jsonl")

# Load all successfully processed IDs
good_ids = set()
for line in open(claims, encoding="utf-8"):
    line = line.strip()
    if line:
        try:
            good_ids.add(str(json.loads(line).get("paper_id", "")))
        except:
            pass

# Separate false alarms from genuine failures
clean_fails  = []
false_alarms = 0
for line in open(failed, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
        if str(r.get("paper_id", "")) in good_ids:
            false_alarms += 1   # already succeeded — skip
        else:
            clean_fails.append(line)
    except:
        pass

# Archive the original failed log
shutil.copy(failed, archive)

# Write clean failed log (only genuine failures)
with open(failed, "w", encoding="utf-8") as f:
    for line in clean_fails:
        f.write(line + "\n")

remaining    = 3273 - len(good_ids)
est_hrs      = remaining * 3.5 / 3600
est_cost_usd = est_hrs * 3.44

print("=== CLEANUP COMPLETE ===")
print(f"Successfully processed (kept) : {len(good_ids)} papers")
print(f"False-alarm failures removed  : {false_alarms}")
print(f"Genuine 429 failures archived : {len(clean_fails)}")
print()
print(f"Archive saved to : {archive}")
print()
print("=== GPU RUN FORECAST ===")
print(f"Will skip         : {len(good_ids)} papers (resume logic)")
print(f"Will process      : {remaining} papers")
print(f"Est. time (H200)  : {est_hrs:.1f} hrs")
est_str = f"${est_cost_usd:.2f}"
print(f"Est. cost (H200)  : {est_str}")
