"""
chronology.py

Temporal Reasoning & Era Chronology Engine for the Ashen Era Archive.
Extracts temporal anchors, historical dates, and era milestones from retrieved
archive chunks, organizing them into a canonical chronological event timeline.
"""

import re
from typing import List, Dict, Any, Optional

CANONICAL_ERAS = [
    {"name": "Age of Dawn", "alias": ["dawn", "first age", "proto"], "order": 100},
    {"name": "Age of Fire", "alias": ["fire", "age of myth"], "order": 200},
    {"name": "Age of Shadows", "alias": ["shadows", "as", "a.s."], "order": 300},
    {"name": "Ashen Era", "alias": ["ashen", "strife", "current era"], "order": 400},
]

class LoreChronologyEngine:
    """Extracts and structures chronological timelines across the Ashen Era archive."""

    def __init__(self):
        self.year_as_regex = re.compile(r'\b(\d{1,4})\s*(?:AS|A\.S\.|in the Age of Shadows|Age of Shadows)\b', re.IGNORECASE)
        self.year_general_regex = re.compile(r'\b(?:year|in the year)\s*(\d{1,4})\b', re.IGNORECASE)
        self.era_mention_regex = re.compile(r'\b(Age of [A-Za-z]+|Ashen Era)\b', re.IGNORECASE)

    def extract_timeline(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract chronological events from a set of retrieved chunks."""
        events = []
        seen_events = set()

        for chunk in chunks:
            text = chunk.get("text", "")
            meta = chunk.get("metadata", {})
            source = meta.get("source_file", "Unknown Source")
            page = meta.get("page", "")
            source_label = f"{source} (p. {page})" if page else source

            # Split into individual sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for sentence in sentences:
                sentence_clean = sentence.strip()
                if len(sentence_clean) < 25 or len(sentence_clean) > 300:
                    continue

                as_match = self.year_as_regex.search(sentence_clean)
                gen_match = self.year_general_regex.search(sentence_clean)
                era_match = self.era_mention_regex.search(sentence_clean)

                if as_match:
                    year_num = int(as_match.group(1))
                    year_display = f"{year_num} AS"
                    era_name = "Age of Shadows"
                    sort_key = 300000 + year_num
                elif gen_match and era_match:
                    year_num = int(gen_match.group(1))
                    era_name = era_match.group(1).title()
                    year_display = f"Year {year_num} ({era_name})"
                    sort_key = self._era_order(era_name) + year_num
                elif as_num := re.search(r'\b(\d{3,4})\b', sentence_clean):
                    if "shadow" in sentence_clean.lower():
                        year_num = int(as_num.group(1))
                        year_display = f"{year_num} AS"
                        era_name = "Age of Shadows"
                        sort_key = 300000 + year_num
                    else:
                        continue
                elif era_match:
                    era_name = era_match.group(1).title()
                    year_display = era_name
                    sort_key = self._era_order(era_name)
                else:
                    continue

                event_summary = re.sub(r'\s+', ' ', sentence_clean)
                key = (era_name, year_display, event_summary[:60].lower())
                if key in seen_events:
                    continue
                seen_events.add(key)

                is_tier1 = "codex" in source.lower()
                authority = "Tier 1 (Authoritative Codex)" if is_tier1 else "Tier 2/3 (Chronicle/Wiki)"

                events.append({
                    "era": era_name,
                    "year": year_display,
                    "sort_key": sort_key,
                    "event": event_summary,
                    "source": source_label,
                    "authority": authority
                })

        events.sort(key=lambda x: x["sort_key"])
        return events[:8]

    def _era_order(self, era_name: str) -> int:
        en = era_name.lower()
        for era in CANONICAL_ERAS:
            if any(a in en for a in era["alias"]):
                return era["order"] * 1000
        return 500000
