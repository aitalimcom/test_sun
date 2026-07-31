"""Unit tests for Government HITL alignment engine and DPO JSONL exporter."""

import pytest
from core.hitl import gov_hitl_engine


def test_hitl_submit_and_list():
    record_id = gov_hitl_engine.submit_for_review(
        user_query="dhan ko rog",
        gemma_raw_response="धानको रोगको लागि उपचार गर्नुहोस्।",
        district="काठमाडौँ",
        crop="धान"
    )
    assert record_id.startswith("hitl-")

    pending = gov_hitl_engine.list_pending()
    assert any(r["id"] == record_id for r in pending)


def test_hitl_verify_and_dpo_export():
    record_id = gov_hitl_engine.submit_for_review(
        user_query="makai ma kira lagyo",
        gemma_raw_response="मकैमा किराको लागि विषादी हाल्नुहोस्।",
        district="चितवन",
        crop="मकै"
    )

    success = gov_hitl_engine.verify_record(
        record_id=record_id,
        jta_corrected_response="मकैको फौजी किरा नियन्त्रणका लागि एमामेक्टिन बेन्जोएट (Emamectin Benzoate) ०.५ ग्राम प्रति लिटर पानीमा घोलेर छर्कनुहोस्।",
        jta_officer_id="JTA-TEST-007",
        error_tags=["#pesticide_spec_added"]
    )
    assert success is True

    dpo = gov_hitl_engine.export_dpo_jsonl()
    assert len(dpo) > 0
    assert any(item["chosen"][0]["content"].startswith("मकैको फौजी किरा") for item in dpo)


def test_hitl_stats():
    stats = gov_hitl_engine.get_stats()
    assert "total_records" in stats
    assert "verification_rate" in stats
    assert stats["total_records"] > 0
