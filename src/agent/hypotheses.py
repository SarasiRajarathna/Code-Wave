"""
hypotheses.py

Multi-Hypothesis Branching Engine for the Ashen Era Archive.
When a historical controversy or divergent record is detected, this engine formulates
dual structured hypotheses:
- Hypothesis A (Orthodox Imperial Record): Authoritative stance, primary citations, doctrinal backing.
- Hypothesis B (Revisionist / Vernacular Record): Counter-narrative, secondary accounts, folk claims.
- Curatorial Synthesis: Methodological reconciliation by the archivist.
"""

from typing import List, Dict, Any, Optional


class HypothesisBrancher:
    """Detects historical debates and branches inquiry into competing structured hypotheses."""

    def branch(
        self,
        question: str,
        answer: str,
        contradictions: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Derives structured competing hypotheses if a historical controversy exists.
        """
        q_lower = question.lower()
        has_conflict = len(contradictions) > 0 or any(
            w in q_lower for w in ["actually", "true", "founding", "conflict", "dispute", "contested", "precise year", "forged"]
        )

        if not has_conflict:
            return None

        # Check for specific historical topics in the Ashen Archive
        if "gloamreach" in q_lower and ("found" in q_lower or "year" in q_lower):
            return {
                "controversy_topic": "The True Founding Year of Gloamreach",
                "hypothesis_a": {
                    "label": "Hypothesis A — The Shadow Compact (Official Orthodoxy)",
                    "claim": "Gloamreach was founded in the early Age of Shadows following the Signing of the Ashen Compact.",
                    "authority": "Codex Vaeloria I (Gazetteer of the Sundered Realms)",
                    "support_level": "Authoritative State Register"
                },
                "hypothesis_b": {
                    "label": "Hypothesis B — The Pre-Sundering Enclave (Antiquarian Dissent)",
                    "claim": "Gloamreach existed as a covert subterranean refuge decades prior to the formal imperial declaration.",
                    "authority": "Ephemera Archive — Field Dispatches & Ballads",
                    "support_level": "Folk Witness Tradition"
                },
                "curatorial_synthesis": "The Codex Vaeloria represents the de jure founding recognized by the Crown, whereas folk chronicles preserve the de facto settlement date."
            }

        if "sorrowfell" in q_lower and ("forged" in q_lower or "year" in q_lower or "gauntlet" in q_lower):
            return {
                "controversy_topic": "Forging Chronology of the Gauntlet of Sorrowfell",
                "hypothesis_a": {
                    "label": "Hypothesis A — Master Alden's Forge Muster (Tier 1)",
                    "claim": "Forged during the Siege of the Iron Keep under Master Smith Alden's direct supervision.",
                    "authority": "Codex Vaeloria II — Armory of Relics",
                    "support_level": "Tier 1 Guild Inscription"
                },
                "hypothesis_b": {
                    "label": "Hypothesis B — The Battlefield Attunement (Tier 2/3)",
                    "claim": "The gauntlet was pre-forged in the First Age and merely attuned or renamed during the Sorrowfell Conflict.",
                    "authority": "Chronicles of the Shattered Vale, Chapter IV",
                    "support_level": "Secondary Courtly Narrative"
                },
                "curatorial_synthesis": "Archivist accepts the Codex armory muster as authentic forging date; courtly accounts confuse original casting with martial attunement."
            }

        if contradictions:
            c = contradictions[0]
            return {
                "controversy_topic": c.get("topic", "Archival Discrepancy"),
                "hypothesis_a": {
                    "label": "Hypothesis A — Authoritative Imperial Record",
                    "claim": "Official account recorded in state registers.",
                    "authority": c.get("tier1_authority", "Codex Vaeloria"),
                    "support_level": "Tier 1 Primacy"
                },
                "hypothesis_b": {
                    "label": "Hypothesis B — Secondary / Eyewitness Variant",
                    "claim": c.get("nature_of_conflict", "Alternative historical testimony."),
                    "authority": c.get("secondary_source", "Secondary Archive"),
                    "support_level": "Secondary Attestation"
                },
                "curatorial_synthesis": c.get("archival_resolution", "Resolved in favor of primary registers per archival curation standard.")
            }

        return None
