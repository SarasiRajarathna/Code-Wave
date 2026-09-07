"""
decomposer.py

Sub-Query Decomposition & Hypothetical Document Embeddings (HyDE) Engine.
Implements cognitive decomposition of compound multi-hop questions into
ordered sub-queries, and generates hypothetical archivist excerpts to enhance
dense vector recall across the Ashen Era archive.
"""

import re
from typing import List, Dict, Any, Optional

class QueryDecomposer:
    """Decomposes compound questions and produces HyDE query expansions."""

    def __init__(self, llm=None):
        self.llm = llm

    def is_compound_query(self, query: str) -> bool:
        """Detect if a query requires multi-step cognitive decomposition."""
        q_lower = query.lower()
        temporal_connectors = [" when ", " while ", " after ", " before ", " during which "]
        has_temporal = any(c in q_lower for c in temporal_connectors)
        has_multiple_entities = len(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)) >= 2
        return has_temporal and has_multiple_entities

    def decompose(self, query: str) -> List[str]:
        """Break down a compound multi-hop question into sequential sub-queries."""
        q_lower = query.lower()

        # Pattern 1: "Who was the [role] of [place/group] when [event] was [constructed/founded/etc.]?"
        m = re.search(r'who (?:was|is) the (.+?) of (.+?) when (.+?) was (.+?)\??$', q_lower)
        if m:
            role, entity1, entity2, action = m.groups()
            sub_q1 = f"When was {entity2.strip()} {action.strip()}?"
            sub_q2 = f"Who was the {role.strip()} of {entity1.strip()} during that era?"
            return [sub_q1, sub_q2]

        # Pattern 2: Split by ' when '
        if " when " in q_lower:
            parts = re.split(r'\s+when\s+', query, flags=re.IGNORECASE)
            if len(parts) == 2:
                first_part = parts[0].strip()
                second_part = parts[1].strip().rstrip('?')
                sub_q1 = f"When did {second_part} happen?"
                sub_q2 = f"{first_part} during that time?"
                return [sub_q1, sub_q2]

        # Default: single primary query
        return [query]

    def generate_hyde_doc(self, query: str) -> str:
        """Generate a hypothetical archivist passage in Codex Vaeloria tone for dense embedding."""
        q_clean = query.rstrip('?').strip()
        q_lower = q_clean.lower()

        if "garrison strength" in q_lower:
            return f"Codex Vaeloria records the official garrison strength of the fortress, specifying the exact souls under arms and active sentinels stationed within the walls."
        elif "founding" in q_lower or "founded" in q_lower:
            return f"Historical chronicles and archival annals of the Age of Shadows document the true founding year and establishment of the settlement under early decree."
        elif "forged" in q_lower or "gauntlet" in q_lower:
            return f"The sacred relics and bound weapons register indicates the precise forging year in the Age of Shadows (AS) when the smiths completed the artifact."
        elif "binding" in q_lower or "material" in q_lower:
            return f"The treatise on relic binding and sorrowfell weaponry details the primary binding materials, metals, and eldritch alloys used in the forge."
        elif "ruler" in q_lower or "governor" in q_lower or "monarch" in q_lower:
            return f"The genealogical rolls and dynastic records identify the reigning ruler and sovereign of the realm at the time of construction."
        else:
            return f"According to the definitive historical records preserved in the Codex Vaeloria, the factual details regarding {q_clean} are systematically recorded."
