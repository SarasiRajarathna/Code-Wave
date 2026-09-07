"""
Source Pedigree & Archival Integrity Scorer
Calculates transmission fidelity, historical provenance tier, and composite archival integrity
scores for cited source documents in the Ashen Era Archive.
"""

from typing import List, Dict, Any
import re


class PedigreeScorer:
    """
    Evaluates the historical pedigree and transmission integrity of sources.
    Tiers:
      Tier 1: Canonical Imperial Codices & Visual Plates (0.95 - 0.99)
      Tier 2: Official Dynastic Chronicles & Annals (0.88 - 0.94)
      Tier 3: Secondary Compendiums & Wiki Syntheses (0.80 - 0.87)
      Tier 4: Ephemeral Letters, Diaries & Field Fragments (0.65 - 0.78)
    """

    TIER_RULES = [
        {
            "tier": "Tier 1: Canonical Imperial Codex",
            "keywords": ["codex", "vaeloria", "imperial", "decree", "ledger", "plate", "figure", "visual"],
            "base_score": 0.98,
            "weight": 1.0,
            "classification": "Primary Canonical",
            "fidelity": "High Epigraphic Preservation",
            "curator_note": "Direct primary record with authoritative imperial seal; transmission chain unbroken."
        },
        {
            "tier": "Tier 2: Dynastic Chronicle",
            "keywords": ["chronicle", "annals", "royal", "court", "record", "archive"],
            "base_score": 0.91,
            "weight": 0.85,
            "classification": "Official Historiography",
            "fidelity": "High Institutional Authority",
            "curator_note": "Compiled by sworn court archivists; susceptible to minor dynastic redaction."
        },
        {
            "tier": "Tier 3: Scholarly Compendium",
            "keywords": ["wiki", "compendium", "treatise", "synthesis", "overview", "scholar"],
            "base_score": 0.83,
            "weight": 0.75,
            "classification": "Secondary Synthesis",
            "fidelity": "Collated Archival Digest",
            "curator_note": "Collation of surviving fragments; reliable for cross-referencing but secondary."
        },
        {
            "tier": "Tier 4: Ephemeral Account",
            "keywords": ["ephemera", "letter", "diary", "fragment", "field_notes", "rumor", "song"],
            "base_score": 0.71,
            "weight": 0.60,
            "classification": "Informal Eyewitness / Fragment",
            "fidelity": "Unverified Oral/Scribal Transmission",
            "curator_note": "Contemporary informal testimony; carries situational nuance but vulnerable to bias."
        }
    ]

    def score_source(self, source_name: str) -> Dict[str, Any]:
        s_lower = str(source_name).lower()
        
        # Check visual plates
        if any(ext in s_lower for ext in [".png", ".jpg", ".jpeg", "figure", "plate"]):
            return {
                "source": source_name,
                "tier": "Tier 1: Direct Visual Plate",
                "integrity_score": 0.97,
                "weight": 1.0,
                "classification": "Visual Artifact",
                "fidelity": "Direct Archaeological Reproduction",
                "curator_note": "Unadulterated visual plate; absolute physical evidence of recorded heraldry/inscriptions."
            }

        # Check matched rule
        for rule in self.TIER_RULES:
            if any(kw in s_lower for kw in rule["keywords"]):
                # Adjust slightly based on specific name attributes
                score = rule["base_score"]
                if "corrupted" in s_lower or "fragment" in s_lower:
                    score -= 0.08
                return {
                    "source": source_name,
                    "tier": rule["tier"],
                    "integrity_score": round(max(0.40, min(0.99, score)), 2),
                    "weight": rule["weight"],
                    "classification": rule["classification"],
                    "fidelity": rule["fidelity"],
                    "curator_note": rule["curator_note"]
                }

        # Default if unclassified
        return {
            "source": source_name,
            "tier": "Tier 3: General Document",
            "integrity_score": 0.82,
            "weight": 0.70,
            "classification": "Standard Archive Record",
            "fidelity": "Standard Preservation",
            "curator_note": "Standard document from the archive collections."
        }

    def evaluate_sources(self, citations: List[str]) -> Dict[str, Any]:
        """
        Calculates composite archival integrity and pedigree breakdown for a list of cited documents.
        """
        if not citations:
            return {
                "composite_integrity_score": 0.85,
                "tier_distribution": {},
                "primary_ratio": 0.0,
                "pedigrees": [],
                "curator_integrity_verdict": "No citations supplied; using baseline archival confidence."
            }

        pedigrees = [self.score_source(src) for src in citations]
        
        total_score = sum(p["integrity_score"] for p in pedigrees)
        avg_integrity = round(total_score / len(pedigrees), 3)

        tier_counts = {}
        tier1_count = 0
        for p in pedigrees:
            tier_name = p["tier"].split(":")[0].strip()
            tier_counts[tier_name] = tier_counts.get(tier_name, 0) + 1
            if "Tier 1" in p["tier"]:
                tier1_count += 1

        primary_ratio = round(tier1_count / len(pedigrees), 2)

        if avg_integrity >= 0.92:
            verdict = "Authoritative Imperial Pedigree: Conclusions anchored overwhelmingly in Tier-1 Primary Codices and unadulterated plates."
        elif avg_integrity >= 0.84:
            verdict = "Historiographical Consensus: Derived from established official dynastic chronicles with solid cross-document verification."
        else:
            verdict = "Variable Transmission Pedigree: Partially grounded in secondary compendiums or eyewitness ephemera; cross-verification advised."

        return {
            "composite_integrity_score": avg_integrity,
            "tier_distribution": tier_counts,
            "primary_ratio": primary_ratio,
            "pedigrees": pedigrees,
            "curator_integrity_verdict": verdict
        }
