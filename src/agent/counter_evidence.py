"""
counter_evidence.py

Counter-Evidence and Devil's Advocate Prober for the Ashen Era Archive.
Actively probes evidence chunks to detect dissent, debunking statements, retractions,
or claims of forgery/inaccuracy before finalizing the archivist verdict.
"""

import re
from typing import List, Dict, Any, Optional


class CounterEvidenceProber:
    """Probes retrieved passages for dissenting counter-evidence or debunked assertions."""

    def __init__(self):
        # Specific historical counter-evidence patterns
        self.dissent_indicators = [
            r"\blater\s+(?:proven|found|revealed)\s+(?:false|untrue|fabricated|forged)\b",
            r"\bdisputed\s+by\s+(?:contemporary|subsequent|imperial)\b",
            r"\bpopular\s+(?:myth|misconception|folklore)\b",
            r"\brefuted\s+by\s+(?:the\s+)?(?:codex|chronicle|records)\b",
            r"\bno\s+canonical\s+basis\b",
            r"\berroneously\s+attributed\b",
            r"\bfalsely\s+claimed\b",
            r"\bannulled\s+by\s+decree\b"
        ]

    def probe(
        self,
        question: str,
        answer: str,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes a counter-evidence probe over the accumulated evidence.
        """
        dissenting_passages = []

        for c in chunks:
            text = c.get("text", "")
            meta = c.get("metadata", {})
            src = meta.get("source_file", "Archive Record")

            for pat in self.dissent_indicators:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    # Extract surrounding snippet
                    start = max(0, match.start() - 60)
                    end = min(len(text), match.end() + 80)
                    snippet = text[start:end].strip()
                    dissenting_passages.append({
                        "source": src,
                        "matched_pattern": match.group(0),
                        "snippet": f"...{snippet}..."
                    })
                    break

        if dissenting_passages:
            return {
                "probe_status": "COUNTER_EVIDENCE_IDENTIFIED",
                "has_counter_evidence": True,
                "dissent_count": len(dissenting_passages),
                "archivist_verdict": "Historical controversy / dissenting account identified in secondary sources.",
                "dissenting_records": dissenting_passages[:2]
            }

        return {
            "probe_status": "NO_COUNTER_EVIDENCE_FOUND",
            "has_counter_evidence": False,
            "dissent_count": 0,
            "archivist_verdict": "Corpus demonstrates unified historical consensus with zero recorded dissent.",
            "dissenting_records": []
        }
