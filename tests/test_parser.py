"""Quick smoke test for the MEDLINE parser and DataFrame builder."""
from pipeline.phase1_data_collection import parse_medline_batch, build_dataframe

# Simulate a MEDLINE record with various tag lengths (2, 3, 4 chars)
sample = """PMID- 12345678
OWN - NLM
STAT- MEDLINE
TI  - A very long title that spans
      multiple continuation lines here.
AB  - This is the abstract of the paper which discusses E. coli
      as a model organism for studying gene regulation mechanisms.
AU  - Smith JA
AU  - Doe RB
DP  - 2022 Mar
TA  - Nature
MH  - Escherichia coli/*genetics
MH  - Models, Biological

PMID- 99999999
TI  - Second paper title
AB  - Short.
DP  - 2023
TA  - Science
AU  - Jones CD

"""

records = parse_medline_batch(sample)
print(f"Records parsed: {len(records)}")
for r in records:
    print(f"  PMID={r['paper_id']}, title_len={len(r['title'])}, "
          f"abstract_len={len(r['abstract'])}, authors={len(r['authors'])}, "
          f"mesh={len(r['mesh_terms'])}, year={r['year']}")

# Verify continuation lines worked
assert "continuation" in records[0]["title"], "Title continuation failed!"
assert "mechanisms" in records[0]["abstract"], "Abstract continuation failed!"
assert len(records[0]["authors"]) == 2, f"Expected 2 authors, got {len(records[0]['authors'])}"
assert len(records[0]["mesh_terms"]) == 2, f"Expected 2 MeSH, got {len(records[0]['mesh_terms'])}"
assert records[0]["year"] == "2022"

# Second record has short abstract — should parse but be filtered by build_dataframe
assert len(records) == 2, "Both records should be parsed"

# Test build_dataframe filters short abstracts and doesn't mutate originals
for r in records:
    r["organism"] = "E. coli"
    r["query_source"] = "test"

authors_before = records[0]["authors"].copy()
df = build_dataframe(records)

# Verify short abstract was filtered
assert len(df) == 1, f"Expected 1 row after filtering, got {len(df)}"
assert df.iloc[0]["paper_id"] == "12345678"

# Verify originals were NOT mutated (authors should still be a list)
assert isinstance(records[0]["authors"], list), "build_dataframe mutated input!"
assert records[0]["authors"] == authors_before, "authors list was modified!"

# Test empty input
empty_df = build_dataframe([])
assert len(empty_df) == 0
assert "paper_id" in empty_df.columns

print("\n[PASS] All assertions passed -- parser and builder are solid!")
