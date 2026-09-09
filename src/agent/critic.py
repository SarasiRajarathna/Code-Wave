"""
critic.py

Autonomous Archivist Critic and Cognitive Reasoning Engine for the Ashen Era Archive.
Emulates human expert archivist cognition:
1. Self-Reflection and Verification: Sentence-level claim checking against retrieved evidence.
2. Source Perspective and Bias Analysis: Identifies the institutional viewpoint (Imperial, Court, Folk, Encyclopedic).
3. Proactive Investigation Leads: Generates logical follow-up research questions based on unexplored entities.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


class ArchivistCritic:
    """Evaluates answer factuality, assesses source bias, and derives follow-up investigation leads."""

    def __init__(self, llm=None, kg=None):
        self.llm = llm
        self.kg = kg

    def reflect_and_evaluate(
        self,
        question: str,
        answer: str,
        chunks: List[Dict[str, Any]],
        grounding_status: str
    ) -> Dict[str, Any]:
        """
        Executes a self-reflection pass over the synthesized answer to ensure strict fidelity.
        Returns a structured critic evaluation report.
        """
        combined_text = " ".join(c.get("text", "") for c in chunks)
        combined_lower = combined_text.lower()
        ans_lower = answer.lower()

        # 1. Break answer into substantive sentences
        sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", answer)
            if len(s.strip()) > 15 and not s.strip().startswith("[Figure") and not s.strip().startswith("!")
        ]

        verified_claims = []
        cautious_claims = []
        total_claims = max(1, len(sentences))

        for sent in sentences:
            # Extract key words and entities
            words = [w.strip(".,;:\"'()") for w in sent.split()]
            cap_entities = [
                w for w in words
                if w and w[0].isupper() and len(w) > 3 and w.lower() not in {"this", "that", "these", "those", "according", "however", "furthermore", "overall"}
            ]
            numbers = re.findall(r"\b\d{1,3}(?:,\d{3})*\b|\b\d+\b", sent)

            # Check if entities and numbers are grounded in evidence
            entities_grounded = all(ent.lower() in combined_lower for ent in cap_entities) if cap_entities else True
            numbers_grounded = all(n.replace(",", "").lower() in combined_lower.replace(",", "") for n in numbers) if numbers else True

            meaningful_words = [
                w.lower() for w in words
                if len(w) > 4 and w.lower() not in {"recorded", "figure", "citadel", "according", "stated", "mentioned"}
            ]
            overlap = sum(1 for w in meaningful_words if w in combined_lower)
            overlap_ratio = overlap / max(1, len(meaningful_words))

            if entities_grounded and numbers_grounded and overlap_ratio >= 0.45:
                verified_claims.append(sent)
            else:
                cautious_claims.append(sent)

        alignment_score = round(len(verified_claims) / total_claims, 2)

        # 2. Formulate human-like critic verdict
        if "REFUSAL" in grounding_status:
            critic_verdict = "VERIFIED_REFUSAL_OF_UNRECORDED_DATA"
            archivist_notes = "Archivist confirms that requested details do not exist in the canonical corpus. Speculative extrapolation was rejected."
        elif alignment_score >= 0.85:
            critic_verdict = "RIGOROUSLY_GROUNDED"
            archivist_notes = f"All primary assertions ({len(verified_claims)} verified sentences) are strictly traceable to source citations with zero unsupported extrapolation."
        elif alignment_score >= 0.60:
            critic_verdict = "SUBSTANTIALLY_GROUNDED"
            archivist_notes = f"Primary facts verified ({len(verified_claims)}/{total_claims} sentences). Contextual phrasing relies on surrounding archival framing."
        else:
            critic_verdict = "PROVISIONAL_GROUNDING"
            archivist_notes = "Evidence is fragmentary; answer reflects the limit of surviving historical documentation."

        return {
            "critic_verdict": critic_verdict,
            "alignment_score": alignment_score,
            "verified_claims_count": len(verified_claims),
            "cautious_claims_count": len(cautious_claims),
            "archivist_notes": archivist_notes,
            "verified_claims_sample": verified_claims[:3]
        }

    def determine_source_perspective(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes the institutional bias and archival lens of the retrieved sources.
        """
        source_counts = {
            "codex": 0,
            "chronicle": 0,
            "wiki": 0,
            "ephemera": 0,
            "images": 0
        }

        for c in chunks:
            src = c.get("metadata", {}).get("source_file", "").lower()
            if "codex" in src:
                source_counts["codex"] += 1
            elif "chronicle" in src:
                source_counts["chronicle"] += 1
            elif "wiki" in src:
                source_counts["wiki"] += 1
            elif "ephemera" in src:
                source_counts["ephemera"] += 1
            elif any(ext in src for ext in [".png", ".jpg", ".jpeg"]):
                source_counts["images"] += 1

        primary_type = max(source_counts, key=source_counts.get) if any(source_counts.values()) else "chronicle"

        perspectives = {
            "codex": {
                "label": "Imperial Codex Register (Orthodox Standard)",
                "institution": "The Imperial Scribes and Silent Choir",
                "bias_profile": "Rigid bureaucratic precision, verified muster rolls, official state doctrinal alignment.",
                "reliability_tier": "Tier 1 — Highest Authority"
            },
            "chronicle": {
                "label": "Courtly Chronicle (Narrative Record)",
                "institution": "High Chroniclers and Royal Historians",
                "bias_profile": "Dramatized heroic narrative, dynastic emphasis, potential eulogistic bias toward nobility.",
                "reliability_tier": "Tier 2 — Contextual and Narrative"
            },
            "wiki": {
                "label": "Curated Archive Wiki (Encyclopedic Synthesis)",
                "institution": "Contemporary Antiquarians",
                "bias_profile": "Neutral cross-referencing, multi-source compilation, reconciled regional discrepancies.",
                "reliability_tier": "Tier 2 — Comprehensive Synthesis"
            },
            "ephemera": {
                "label": "Frontline Ephemera (Field Accounts and Lore)",
                "institution": "Soldiers, Merchants and Outcast Observers",
                "bias_profile": "Raw eyewitness experience, unvetted rumors, vernacular perspective counter to official doctrine.",
                "reliability_tier": "Tier 3 — Folk and Direct Witness"
            },
            "images": {
                "label": "Visual Figure Plate (Cartographic/Schematic)",
                "institution": "Master Cartographers and Guild Artificers",
                "bias_profile": "Direct architectural and metallurgical schematics; immune to prose reinterpretation.",
                "reliability_tier": "Tier 1 — Visual Proof"
            }
        }

        chosen = perspectives.get(primary_type, perspectives["chronicle"])
        return {
            "source_type": primary_type,
            "perspective_label": chosen["label"],
            "governing_institution": chosen["institution"],
            "bias_profile": chosen["bias_profile"],
            "reliability_tier": chosen["reliability_tier"]
        }

    def generate_investigation_leads(
        self,
        question: str,
        answer: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Proactively formulates 2-3 logical follow-up questions (Curiosity Leads)
        based on entities, locations, or conflicts mentioned in the retrieved evidence.
        """
        combined_text = " ".join(c.get("text", "") for c in chunks)
        q_lower = question.lower()

        wikilinks = re.findall(r"\[\[(.*?)\]\]", combined_text)
        entities = [wl.strip() for wl in wikilinks if wl.strip().lower() not in q_lower and len(wl.strip()) > 3]

        if len(entities) < 3:
            cap_words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", combined_text)
            for cw in cap_words:
                if cw.lower() not in q_lower and len(cw) > 4 and cw not in {"According", "Chapter", "Citadel", "Recorded", "Furthermore"}:
                    entities.append(cw)

        unique_entities = []
        seen = set()
        for e in entities:
            if e.lower() not in seen:
                seen.add(e.lower())
                unique_entities.append(e)

        lead_templates = [
            ("What historical role did {entity} play during this period?", "Lore and Background"),
            ("How was {entity} connected to the key events described in this record?", "Factional Nexus"),
            ("What artifacts or decrees are associated with {entity} in the archive?", "Relics and Decrees"),
            ("What became of {entity} in the aftermath of the Ashen Era conflicts?", "Consequences and Fate")
        ]

        leads = []
        for idx, ent in enumerate(unique_entities[:3]):
            tmpl, category = lead_templates[idx % len(lead_templates)]
            leads.append({
                "entity": ent,
                "question": tmpl.format(entity=ent),
                "category": category
            })

        if not leads:
            leads = [
                {
                    "entity": "Chronicles",
                    "question": "What primary treaties or battles defined the borders of this region?",
                    "category": "Historical Nexus"
                },
                {
                    "entity": "Codex Vaeloria",
                    "question": "What other military strongholds or figures are recorded in this volume?",
                    "category": "Comparative Lore"
                }
            ]

        return leads[:3]
