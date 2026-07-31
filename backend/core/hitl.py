"""
Government Human-in-the-Loop (HITL) & Gemma 4 Alignment Engine.
Enables Ministry of Agriculture JTA (Junior Technical Assistant) extension officers to:
1. Review raw farmer AI responses.
2. Provide verified Devanagari agronomic corrections.
3. Categorize script & agronomy error types (#Devanagari_conjunct, #schwa_syncope, #wrong_pesticide_dosage).
4. Export high-quality DPO (Direct Preference Optimization), KTO, and SFT datasets in JSONL format for Gemma 4 model fine-tuning.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

HITL_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "database", "feedback", "hitl_audits.json")


class GovernmentHITLEngine:
    """Manages Government JTA expert audits and Gemma 4 DPO alignment dataset export."""

    def __init__(self, storage_path: str = HITL_DB_PATH):
        self.storage_path = os.path.abspath(storage_path)
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.storage_path):
            initial_data = {
                "records": [
                    {
                        "id": "hitl-sample-001",
                        "timestamp": "2026-07-31T10:00:00Z",
                        "district": "काभ्रेपलाञ्चोक",
                        "crop": "आलु",
                        "user_query": "aaloo ma dadhuwa rog lagyo k spray garne",
                        "reformulated_query": "आलुमा डढुवा रोग लाग्यो के छर्कने",
                        "gemma_raw_response": "आलुमा डढुवा रोगको लागि मानकोजेब २ ग्राम/लिटर पानीमा मिसाएर छर्कनुहोस्।",
                        "jta_corrected_response": "आलुमा डढुवा (Late Blight) रोग नियन्त्रणका लागि म्याङ्कोजेब (Mancozeb 75% WP) २ ग्राम प्रति लिटर पानीमा घोलेर बिहानको समयमा छर्कनुहोस्। रोग धेरै फैलिएमा साझपख कपर अक्सिक्लोराइड (Copper Oxychloride) प्रयोग गर्नुहोस्।",
                        "status": "verified_corrected",
                        "jta_officer_id": "JTA-KAVRE-042",
                        "error_tags": ["#Devanagari_conjunct", "#chemical_spec_added", "#dosage_clarified"],
                        "confidence_score": 0.94,
                        "dialect": "Standard Nepali"
                    }
                ],
                "updated_at": datetime.now().isoformat()
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading HITL data: {e}")
            return {"records": []}

    def _save_data(self, data: Dict[str, Any]):
        data["updated_at"] = datetime.now().isoformat()
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def submit_for_review(
        self,
        user_query: str,
        gemma_raw_response: str,
        district: str = "काठमाडौँ",
        crop: str = "सामान्य",
        reformulated_query: Optional[str] = None,
        confidence_score: float = 0.85,
        dialect: str = "Standard Nepali"
    ) -> str:
        """Enqueues a raw farmer query & AI response for JTA expert review."""
        data = self._load_data()
        record_id = f"hitl-{uuid.uuid4().hex[:8]}"

        record = {
            "id": record_id,
            "timestamp": datetime.now().isoformat(),
            "district": district,
            "crop": crop,
            "user_query": user_query,
            "reformulated_query": reformulated_query or user_query,
            "gemma_raw_response": gemma_raw_response,
            "jta_corrected_response": None,
            "status": "pending_review",
            "jta_officer_id": None,
            "error_tags": [],
            "confidence_score": confidence_score,
            "dialect": dialect
        }

        data["records"].insert(0, record)
        self._save_data(data)
        return record_id

    def list_pending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns pending review records for JTA officers."""
        data = self._load_data()
        return [r for r in data["records"] if r.get("status") == "pending_review"][:limit]

    def verify_record(
        self,
        record_id: str,
        jta_corrected_response: str,
        jta_officer_id: str = "JTA-GOV-001",
        error_tags: Optional[List[str]] = None,
        approve_raw: bool = False
    ) -> bool:
        """Records JTA expert verification and corrections."""
        data = self._load_data()
        for r in data["records"]:
            if r["id"] == record_id:
                r["jta_officer_id"] = jta_officer_id
                r["error_tags"] = error_tags or []
                if approve_raw:
                    r["status"] = "verified_approved"
                    r["jta_corrected_response"] = r["gemma_raw_response"]
                else:
                    r["status"] = "verified_corrected"
                    r["jta_corrected_response"] = jta_corrected_response
                self._save_data(data)
                return True
        return False

    def export_dpo_jsonl(self) -> List[Dict[str, Any]]:
        """Exports verified records as DPO (Direct Preference Optimization) JSONL dataset for Gemma 4 fine-tuning."""
        data = self._load_data()
        dpo_dataset = []

        for r in data["records"]:
            if r.get("status") in ["verified_corrected", "verified_approved"] and r.get("jta_corrected_response"):
                prompt_text = r.get("reformulated_query") or r.get("user_query")
                dpo_entry = {
                    "prompt": [
                        {"role": "system", "content": "तपाईं कृषि सेवा - नेपाल सरकारको आधिकारिक कृषि प्राविधिक हुनुहुन्छ।"},
                        {"role": "user", "content": prompt_text}
                    ],
                    "chosen": [
                        {"role": "assistant", "content": r["jta_corrected_response"]}
                    ],
                    "rejected": [
                        {"role": "assistant", "content": r["gemma_raw_response"]}
                    ],
                    "metadata": {
                        "district": r.get("district"),
                        "crop": r.get("crop"),
                        "error_tags": r.get("error_tags", []),
                        "jta_officer_id": r.get("jta_officer_id")
                    }
                }
                dpo_dataset.append(dpo_entry)

        return dpo_dataset

    def get_stats(self) -> Dict[str, Any]:
        """Returns HITL verification statistics and accuracy metrics."""
        data = self._load_data()
        records = data["records"]
        total = len(records)
        verified = sum(1 for r in records if r.get("status") in ["verified_approved", "verified_corrected"])
        pending = sum(1 for r in records if r.get("status") == "pending_review")
        corrected = sum(1 for r in records if r.get("status") == "verified_corrected")

        tag_counts: Dict[str, int] = {}
        for r in records:
            for tag in r.get("error_tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_records": total,
            "verified_records": verified,
            "pending_records": pending,
            "corrected_records": corrected,
            "verification_rate": (verified / total * 100) if total > 0 else 0,
            "accuracy_improvement_rate": (corrected / verified * 100) if verified > 0 else 0,
            "top_error_tags": tag_counts
        }


# Global singleton instance
gov_hitl_engine = GovernmentHITLEngine()
