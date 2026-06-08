"""
pytest test suite for phase2_extract.py
========================================
Unit tests:  no API calls, fully offline
Integration: real Cerebras call (requires CEREBRAS_API_KEY in .env)
             run with: pytest -m integration

Run all unit tests:
    pytest test_phase2.py -v

Run everything including integration:
    pytest test_phase2.py -v -m "unit or integration"
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── import the functions we want to test ──────────────────────────────────────
from pipeline.phase2_claim_extraction import (
    quote_match_score,
    validate_hallucination,
    parse_json_response,
    load_processed_ids,
    build_flat_csv,
    build_user_prompt,
    RESPONSE_SCHEMA,
    QUOTE_MATCH_THRESHOLD,
)
from jsonschema import validate as jvalidate, ValidationError


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_ABSTRACT = (
    "Escherichia coli has served as the premier model microorganism for studying "
    "fundamental biological processes due to its rapid growth rate, well-characterized "
    "genetics, and ease of genetic manipulation. The organism's short doubling time of "
    "approximately 20 minutes allowed multiple experimental iterations within a single day."
)

VALID_RESULT = {
    "paper_id": "12345678",
    "explicit_reason_found": True,
    "justification_claims": [
        {
            "claim": "E. coli chosen for rapid growth rate",
            "category": "biological",
            "subcategory": "growth_kinetics",
            "supporting_quote": "rapid growth rate",
        }
    ],
    "null_reason": None,
}

NULL_RESULT = {
    "paper_id": "99999999",
    "explicit_reason_found": False,
    "justification_claims": [],
    "null_reason": "No explicit justification stated in abstract",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. QUOTE MATCH SCORE — sliding window fuzzy match
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestQuoteMatchScore:
    def test_exact_match_returns_1(self):
        assert quote_match_score("rapid growth rate", SAMPLE_ABSTRACT) == 1.0

    def test_substring_exact_returns_1(self):
        assert quote_match_score("short doubling time", SAMPLE_ABSTRACT) == 1.0

    def test_near_match_above_threshold(self):
        # Minor typo — should still score above threshold
        score = quote_match_score("rapid grwoth rate", SAMPLE_ABSTRACT)
        assert score >= QUOTE_MATCH_THRESHOLD

    def test_hallucinated_quote_below_threshold(self):
        # Completely fabricated — should fail
        score = quote_match_score("extraordinary antibiotic production capacity", SAMPLE_ABSTRACT)
        assert score < QUOTE_MATCH_THRESHOLD

    def test_empty_quote_returns_0(self):
        assert quote_match_score("", SAMPLE_ABSTRACT) == 0.0

    def test_empty_abstract_returns_low(self):
        score = quote_match_score("rapid growth rate", "")
        assert score < QUOTE_MATCH_THRESHOLD

    def test_full_sentence_match(self):
        quote = "ease of genetic manipulation"
        assert quote_match_score(quote, SAMPLE_ABSTRACT) == 1.0

    def test_case_insensitive(self):
        assert quote_match_score("RAPID GROWTH RATE", SAMPLE_ABSTRACT) == 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. HALLUCINATION DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestValidateHallucination:
    def test_real_quote_flagged_clean(self):
        result = {**VALID_RESULT, "justification_claims": [
            {**VALID_RESULT["justification_claims"][0]}
        ]}
        out = validate_hallucination(result, SAMPLE_ABSTRACT)
        assert out["hallucination_free"] is True
        assert out["hallucination_flags"] == 0
        assert out["justification_claims"][0]["quote_match_score"] == 1.0
        assert out["justification_claims"][0]["hallucination_risk"] is False

    def test_fabricated_quote_flagged(self):
        result = {
            "paper_id": "123",
            "explicit_reason_found": True,
            "justification_claims": [
                {
                    "claim": "some claim",
                    "category": "biological",
                    "subcategory": "test",
                    "supporting_quote": "extraordinary antibiotic production capacity never in abstract",
                }
            ],
            "null_reason": None,
        }
        out = validate_hallucination(result, SAMPLE_ABSTRACT)
        assert out["hallucination_free"] is False
        assert out["hallucination_flags"] == 1
        assert out["justification_claims"][0]["hallucination_risk"] is True

    def test_empty_claims_is_clean(self):
        out = validate_hallucination({**NULL_RESULT}, SAMPLE_ABSTRACT)
        assert out["hallucination_free"] is True
        assert out["hallucination_flags"] == 0

    def test_multiple_claims_partial_hallucination(self):
        result = {
            "paper_id": "123",
            "explicit_reason_found": True,
            "justification_claims": [
                {"claim": "a", "category": "biological", "subcategory": "x",
                 "supporting_quote": "rapid growth rate"},           # real
                {"claim": "b", "category": "technical",  "subcategory": "y",
                 "supporting_quote": "fabricated nonsense xyz abc"},  # fake
            ],
            "null_reason": None,
        }
        out = validate_hallucination(result, SAMPLE_ABSTRACT)
        assert out["hallucination_flags"] == 1
        assert out["hallucination_free"] is False
        assert out["justification_claims"][0]["hallucination_risk"] is False
        assert out["justification_claims"][1]["hallucination_risk"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 3. JSON RESPONSE PARSING
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestParseJsonResponse:
    def test_clean_json(self):
        raw = json.dumps(VALID_RESULT)
        result = parse_json_response(raw)
        assert result["paper_id"] == "12345678"

    def test_strips_markdown_json_fence(self):
        raw = f"```json\n{json.dumps(VALID_RESULT)}\n```"
        result = parse_json_response(raw)
        assert result["paper_id"] == "12345678"

    def test_strips_plain_code_fence(self):
        raw = f"```\n{json.dumps(VALID_RESULT)}\n```"
        result = parse_json_response(raw)
        assert result["paper_id"] == "12345678"

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_json_response("this is not json at all")

    def test_null_result_parsed(self):
        raw = json.dumps(NULL_RESULT)
        result = parse_json_response(raw)
        assert result["explicit_reason_found"] is False
        assert result["justification_claims"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 4. JSON SCHEMA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestSchemaValidation:
    def test_valid_result_passes(self):
        jvalidate(instance=VALID_RESULT, schema=RESPONSE_SCHEMA)  # must not raise

    def test_null_result_passes(self):
        jvalidate(instance=NULL_RESULT, schema=RESPONSE_SCHEMA)   # must not raise

    def test_missing_paper_id_fails(self):
        bad = {k: v for k, v in VALID_RESULT.items() if k != "paper_id"}
        with pytest.raises(ValidationError):
            jvalidate(instance=bad, schema=RESPONSE_SCHEMA)

    def test_invalid_category_fails(self):
        bad = json.loads(json.dumps(VALID_RESULT))
        bad["justification_claims"][0]["category"] = "political"  # not in enum
        with pytest.raises(ValidationError):
            jvalidate(instance=bad, schema=RESPONSE_SCHEMA)

    def test_extra_field_fails(self):
        bad = {**VALID_RESULT, "extra_field": "unexpected"}
        with pytest.raises(ValidationError):
            jvalidate(instance=bad, schema=RESPONSE_SCHEMA)

    def test_claim_too_short_fails(self):
        bad = json.loads(json.dumps(VALID_RESULT))
        bad["justification_claims"][0]["claim"] = "Hi"  # minLength: 5
        with pytest.raises(ValidationError):
            jvalidate(instance=bad, schema=RESPONSE_SCHEMA)

    def test_all_five_categories_valid(self):
        for cat in ["biological", "technical", "historical", "economic", "cultural"]:
            r = json.loads(json.dumps(VALID_RESULT))
            r["justification_claims"][0]["category"] = cat
            jvalidate(instance=r, schema=RESPONSE_SCHEMA)  # must not raise


# ═══════════════════════════════════════════════════════════════════════════════
# 5. RESUME — load_processed_ids
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestLoadProcessedIds:
    def test_empty_file_returns_empty_set(self, tmp_path):
        f = tmp_path / "claims.jsonl"
        f.write_text("", encoding="utf-8")
        assert load_processed_ids(f) == set()

    def test_missing_file_returns_empty_set(self, tmp_path):
        f = tmp_path / "nonexistent.jsonl"
        assert load_processed_ids(f) == set()

    def test_reads_paper_ids(self, tmp_path):
        f = tmp_path / "claims.jsonl"
        f.write_text(
            json.dumps({"paper_id": "111"}) + "\n" +
            json.dumps({"paper_id": "222"}) + "\n",
            encoding="utf-8",
        )
        ids = load_processed_ids(f)
        assert ids == {"111", "222"}

    def test_skips_corrupted_lines(self, tmp_path):
        f = tmp_path / "claims.jsonl"
        f.write_text(
            json.dumps({"paper_id": "111"}) + "\n" +
            "CORRUPTED LINE {{{\n" +
            json.dumps({"paper_id": "333"}) + "\n",
            encoding="utf-8",
        )
        ids = load_processed_ids(f)
        assert "111" in ids
        assert "333" in ids
        assert len(ids) == 2  # corrupted line skipped


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CSV BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestBuildFlatCsv:
    def _write_jsonl(self, path, records):
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def test_with_claims_produces_rows(self, tmp_path):
        jsonl = tmp_path / "claims.jsonl"
        csv   = tmp_path / "claims.csv"
        record = {**VALID_RESULT, "organism": "E. coli", "year": "2020",
                  "journal": "Nature", "query_source": "ecoli",
                  "hallucination_free": True}
        record["justification_claims"][0].update(
            {"quote_match_score": 1.0, "hallucination_risk": False}
        )
        self._write_jsonl(jsonl, [record])
        count = build_flat_csv(jsonl, csv)
        assert count == 1
        import pandas as pd
        df = pd.read_csv(csv)
        assert df.iloc[0]["claim"] == "E. coli chosen for rapid growth rate"
        assert df.iloc[0]["category"] == "biological"

    def test_null_result_produces_one_empty_row(self, tmp_path):
        jsonl = tmp_path / "claims.jsonl"
        csv   = tmp_path / "claims.csv"
        record = {**NULL_RESULT, "organism": "E. coli", "year": "2020",
                  "journal": "Nature", "query_source": "ecoli",
                  "hallucination_free": True}
        self._write_jsonl(jsonl, [record])
        count = build_flat_csv(jsonl, csv)
        assert count == 1

    def test_corrupted_line_skipped(self, tmp_path):
        jsonl = tmp_path / "claims.jsonl"
        csv   = tmp_path / "claims.csv"
        with open(jsonl, "w", encoding="utf-8") as f:
            f.write("CORRUPTED\n")
            record = {**NULL_RESULT, "organism": "E. coli", "year": "2020",
                      "journal": "J", "query_source": "q", "hallucination_free": True}
            f.write(json.dumps(record) + "\n")
        count = build_flat_csv(jsonl, csv)
        assert count == 1  # only the good line


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestBuildUserPrompt:
    def test_contains_paper_id(self):
        p = build_user_prompt("99999", SAMPLE_ABSTRACT, "E. coli")
        assert "99999" in p

    def test_contains_abstract(self):
        p = build_user_prompt("1", SAMPLE_ABSTRACT, "E. coli")
        assert SAMPLE_ABSTRACT in p

    def test_contains_organism(self):
        p = build_user_prompt("1", SAMPLE_ABSTRACT, "B. subtilis")
        assert "B. subtilis" in p

    def test_contains_json_template(self):
        p = build_user_prompt("1", SAMPLE_ABSTRACT, "E. coli")
        assert "justification_claims" in p
        assert "explicit_reason_found" in p


# ═══════════════════════════════════════════════════════════════════════════════
# 8. INTEGRATION — real Cerebras API call (skipped without key)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCerebrasIntegration:
    """Requires CEREBRAS_API_KEY in .env. Run with: pytest -m integration"""

    def test_real_extraction_valid_schema(self):
        import os
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv()

        key = os.getenv("CEREBRAS_API_KEY", "")
        if not key:
            pytest.skip("CEREBRAS_API_KEY not set")

        client = OpenAI(base_url="https://api.cerebras.ai/v1", api_key=key)
        from pipeline.phase2_claim_extraction import call_api, RESPONSE_SCHEMA
        from jsonschema import validate as jv

        raw = call_api(client, "TEST001", SAMPLE_ABSTRACT, "E. coli")
        result = parse_json_response(raw)

        # Must conform to schema
        jv(instance=result, schema=RESPONSE_SCHEMA)

        # paper_id must be present
        assert "paper_id" in result
        assert "explicit_reason_found" in result

        # If claims found, they must have all fields
        for claim in result.get("justification_claims", []):
            assert "claim" in claim
            assert "category" in claim
            assert claim["category"] in ["biological","technical","historical","economic","cultural"]
            assert "supporting_quote" in claim

        # If no claims, null_reason must be set
        if not result["explicit_reason_found"]:
            assert result["null_reason"] is not None

    def test_real_extraction_hallucination_check(self):
        import os
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv()

        key = os.getenv("CEREBRAS_API_KEY", "")
        if not key:
            pytest.skip("CEREBRAS_API_KEY not set")

        client = OpenAI(base_url="https://api.cerebras.ai/v1", api_key=key)
        from pipeline.phase2_claim_extraction import call_api

        raw    = call_api(client, "TEST002", SAMPLE_ABSTRACT, "E. coli")
        result = parse_json_response(raw)
        result["paper_id"] = "TEST002"
        result = validate_hallucination(result, SAMPLE_ABSTRACT)

        # hallucination_flags and hallucination_free must be set
        assert "hallucination_flags" in result
        assert "hallucination_free" in result

        # For this well-structured abstract, expect no hallucinations
        if result["justification_claims"]:
            assert result["hallucination_free"] is True, (
                f"Hallucination detected in claims: "
                f"{[c['supporting_quote'] for c in result['justification_claims']]}"
            )
