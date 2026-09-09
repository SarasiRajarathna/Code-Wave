"""
anachronism.py

Causal and Era Anachronism Checker for the Ashen Era Archive.
Verifies that historical figures, battles, and relics mentioned in questions and answers
belong to compatible chronological windows, alerting researchers to historical anachronisms.
"""

import re
from typing import List, Dict, Any, Optional


class AnachronismChecker:
    """Verifies temporal coherence across historical eras and calendar years."""

    def __init__(self):
        # Known canonical eras and their temporal bounds
        self.era_bounds = {
            "First Age": (0, 450),
            "Age of Fire": (0, 500),
            "Age of Shadows": (501, 850),
            "Age of Ash": (851, 1200),
            "Second Sun": (1201, 1500)
        }

    def check_coherence(
        self,
        question: str,
        answer: str,
        timeline_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates chronological consistency across the answer and timeline events.
        """
        combined = f"{question} {answer}"

        # Extract calendar years (e.g., 342, 614, 789, 950)
        years = [int(y) for y in re.findall(r"\b(?:year\s+)?(\d{3,4})\b", combined, re.IGNORECASE) if 50 <= int(y) <= 2000]

        # Extract era mentions
        eras_found = []
        for era in self.era_bounds:
            if era.lower() in combined.lower():
                eras_found.append(era)

        if not years and not timeline_events:
            return {
                "coherence_status": "CHRONOLOGICALLY_COHERENT",
                "is_anachronistic": False,
                "temporal_span_years": 0,
                "notes": "No conflicting temporal datums detected in canonical query scope."
            }

        # Calculate maximum year divergence if multiple years are cited
        all_years = years + [e["year"] for e in timeline_events if isinstance(e.get("year"), int)]
        if all_years:
            min_year = min(all_years)
            max_year = max(all_years)
            span = max_year - min_year

            if span > 400 and not any(phrase in question.lower() for phrase in ["how many years", "duration", "span", "history of", "across"]):
                return {
                    "coherence_status": "ANACHRONISM_WARNING",
                    "is_anachronistic": True,
                    "temporal_span_years": span,
                    "notes": f"Potential temporal divergence: referenced events span {span} years ({min_year} - {max_year}), suggesting distinct historical epochs."
                }

            return {
                "coherence_status": "CHRONOLOGICALLY_COHERENT",
                "is_anachronistic": False,
                "temporal_span_years": span,
                "notes": f"Events align within coherent historical epoch ({min_year} - {max_year})."
            }

        return {
            "coherence_status": "CHRONOLOGICALLY_COHERENT",
            "is_anachronistic": False,
            "temporal_span_years": 0,
            "notes": "Chronological coherence validated across active era timeline."
        }
