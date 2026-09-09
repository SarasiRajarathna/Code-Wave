"""
epistemic.py

Epistemic Uncertainty and Nuance Calibrator for the Ashen Era Archive.
Analyzes linguistic modality across evidence chunks:
- Identifies epistemic hedges ("rumors suggest", "allegedly", "it is believed", "some say")
  versus categorical assertions ("strictly recorded", "muster roll verifies", "decreed", "figure plate depicts").
- Calibrates into 3 epistemic levels:
  1. CATEGORICAL_CERTAINTY (100% direct recorded facts, figures, plate schematics)
  2. PROBABLE_HISTORICAL_CONSENSUS (Standard court chronicles with consistent testimony)
  3. LEGENDARY_SPECULATION (Hedged folk ephemera, rumors, or unverified ballads)
- Computes an epistemic certainty score between 0.0 and 1.0.
"""

import re
from typing import List, Dict, Any


class EpistemicCalibrator:
    """Calibrates epistemic certainty and linguistic modality across historical evidence."""

    def __init__(self):
        # Categorical linguistic markers (High certainty)
        self.categorical_markers = [
            r"\brecorded\s+(?:as|in|under)\b",
            r"\bmuster\s+(?:roll|strength|count)\b",
            r"\bstrictly\s+(?:entered|verified|decreed)\b",
            r"\baccording\s+to\s+the\s+figure\s+plate\b",
            r"\bfigure\s+plate\b",
            r"\bplate\s+\d+\b",
            r"\bofficially\s+ratified\b",
            r"\bconfirmed\s+by\s+the\s+silent\s+choir\b",
            r"\bsealed\s+in\s+the\s+codex\b"
        ]

        # Epistemic hedging markers (Low/Moderate certainty)
        self.hedging_markers = [
            r"\bit\s+is\s+(?:believed|thought|said|rumored|claimed)\b",
            r"\brumors?\s+(?:suggest|whisper|abound)\b",
            r"\ballegedly\b",
            r"\bpurportedly\b",
            r"\bpopular\s+(?:ballad|tale|legend)\b",
            r"\bno\s+surviving\s+record\b",
            r"\bunverified\s+(?:account|chronicle)\b",
            r"\bdisputed\s+attribution\b"
        ]

    def calibrate(
        self,
        question: str,
        answer: str,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates the epistemic certainty level and confidence distribution.
        """
        combined_text = f"{answer} " + " ".join(c.get("text", "") for c in chunks)
        combined_lower = combined_text.lower()

        cat_hits = []
        for pat in self.categorical_markers:
            if re.search(pat, combined_lower):
                cat_hits.append(pat.replace(r"\b", "").replace(r"\s+", " "))

        hedge_hits = []
        for pat in self.hedging_markers:
            if re.search(pat, combined_lower):
                hedge_hits.append(pat.replace(r"\b", "").replace(r"\s+", " "))

        has_plate = any("plate" in c.get("metadata", {}).get("source_file", "").lower() for c in chunks) or "[figure" in answer.lower()
        has_codex = any("codex" in c.get("metadata", {}).get("source_file", "").lower() for c in chunks)

        if has_plate or (has_codex and len(cat_hits) > 0 and len(hedge_hits) == 0):
            epistemic_level = "CATEGORICAL_CERTAINTY"
            certainty_score = 0.99
            archivist_commentary = "Data is attested by primary codex registers and visual figure plates with absolute documentary precision."
        elif len(hedge_hits) > 0:
            epistemic_level = "LEGENDARY_SPECULATION"
            certainty_score = 0.68
            archivist_commentary = f"Evidence contains epistemic hedges ({len(hedge_hits)} detected). Historical accounts reflect vernacular traditions or contested claims."
        else:
            epistemic_level = "PROBABLE_HISTORICAL_CONSENSUS"
            certainty_score = 0.91
            archivist_commentary = "Historical facts are corroborated by court chronicles and encyclopedic records with high archival consensus."

        return {
            "epistemic_level": epistemic_level,
            "certainty_score": certainty_score,
            "categorical_markers_found": len(cat_hits),
            "hedging_markers_found": len(hedge_hits),
            "archivist_commentary": archivist_commentary
        }
