"""
provenance.py

Hermeneutic Scepticism & Ideological Provenance Engine:
Evaluates source motivations, scribal patronage, and ideological lenses.
Exposes why chroniclers wrote what they did (Imperial Orthodoxy vs Dissident Whispers vs Guild Plates).
"""

from typing import Dict, Any, List, Optional


class HermeneuticScepticismEngine:
    """
    Applies historical source criticism (hermeneutics of suspicion) to the archival corpus.
    Categorizes textual strata by political bias, patronage, and empirical reliability.
    """

    CORPUS_PROVENANCE = {
        "codex": {
            "stratum": "Imperial Hegemonic Orthodoxy",
            "patron": "High Archon Council of Vaeloria",
            "motive": "Legitimizing imperial conquest, enforcing state orthodoxy, standardizing calendar reckonings.",
            "ideological_bias": "Imperial triumphalism; tends to censor defeats, erase rebel lineages, and attribute divine mandate.",
            "reliability_tier": "Tier-1 Administrative & Legal Authority",
            "scepticism_level": "MODERATE_SCEPTICISM",
            "critical_note": "Authoritative on imperial dates and legal decrees, but inherently biased against provincial rebellions."
        },
        "chronicle": {
            "stratum": "Dissident Subversive Tradition",
            "patron": "Underground Scriveners & Dissident Sects of Sorrowfell",
            "motive": "Preserving forbidden oral memories, documenting suppressed insurgencies and true relic origins.",
            "ideological_bias": "Counter-hegemonic sentiment; prone to mythological aggrandizement and martyrdom bias.",
            "reliability_tier": "Tier-2 Oral & Heterodox Testimony",
            "scepticism_level": "HIGH_SCEPTICISM",
            "critical_note": "Crucial for identifying redacted events, but dates must be cross-examined against imperial censuses."
        },
        "plate": {
            "stratum": "Empirical Architectural & Cartographic Guild Records",
            "patron": "Guild of Surveyors & Fortress Quartermasters",
            "motive": "Documenting physical logistics, garrison strengths, architectural schematics, and defensive bastions.",
            "ideological_bias": "Empirical pragmatism; minimal political commentary.",
            "reliability_tier": "Tier-1 Empirical Primary Artifact",
            "scepticism_level": "LOW_SCEPTICISM",
            "critical_note": "Highest reliability for quantitative counts and physical layout. Free from doctrinal embellishment."
        },
        "figure": {
            "stratum": "Empirical Architectural & Cartographic Guild Records",
            "patron": "Guild of Surveyors & Fortress Quartermasters",
            "motive": "Documenting physical logistics, garrison strengths, architectural schematics, and defensive bastions.",
            "ideological_bias": "Empirical pragmatism; minimal political commentary.",
            "reliability_tier": "Tier-1 Empirical Primary Artifact",
            "scepticism_level": "LOW_SCEPTICISM",
            "critical_note": "Highest reliability for quantitative counts and physical layout. Free from doctrinal embellishment."
        },
        "wiki": {
            "stratum": "Retrospective Scholarly Synthesis",
            "patron": "Academy of Ashen Antiquaries",
            "motive": "Harmonizing fragmented ancient chronicles into a unified pedagogical encyclopedia.",
            "ideological_bias": "Scholarly distance; tendency to over-smooth unresolvable historical contradictions.",
            "reliability_tier": "Tier-3 Secondary Academic Reference",
            "scepticism_level": "LOW_TO_MODERATE",
            "critical_note": "Helpful overview of cross-chronicle consensus, but may reproduce scribal translation errors."
        }
    }

    def audit_sources(self, citations: List[str], accumulated_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Produce a comprehensive hermeneutic audit of the cited sources."""
        identified_strata = []
        highest_scepticism = "LOW_SCEPTICISM"
        dominant_perspective = "Empirical Archival Consensus"

        # Tally source types
        for cit in citations:
            c_low = cit.lower()
            matched_key = None
            if "plate" in c_low or "figure" in c_low:
                matched_key = "plate"
            elif "codex" in c_low or "vaeloria" in c_low:
                matched_key = "codex"
            elif "chronicle" in c_low or "whisper" in c_low:
                matched_key = "chronicle"
            elif "wiki" in c_low or ".md" in c_low:
                matched_key = "wiki"

            if matched_key and matched_key in self.CORPUS_PROVENANCE:
                prov = self.CORPUS_PROVENANCE[matched_key]
                identified_strata.append({
                    "source": cit,
                    "stratum": prov["stratum"],
                    "patron": prov["patron"],
                    "motive": prov["motive"],
                    "ideological_bias": prov["ideological_bias"],
                    "scepticism_level": prov["scepticism_level"]
                })
                if prov["scepticism_level"] == "HIGH_SCEPTICISM":
                    highest_scepticism = "HIGH_SCEPTICISM"
                elif prov["scepticism_level"] == "MODERATE_SCEPTICISM" and highest_scepticism != "HIGH_SCEPTICISM":
                    highest_scepticism = "MODERATE_SCEPTICISM"

        if any(s["stratum"].startswith("Empirical") for s in identified_strata):
            dominant_perspective = "Guild Empirical Census (High Physical Precision)"
        elif any(s["stratum"].startswith("Imperial") for s in identified_strata):
            dominant_perspective = "Imperial Statecraft Orthodoxy (Codex Vaeloria)"
        elif any(s["stratum"].startswith("Dissident") for s in identified_strata):
            dominant_perspective = "Dissident Counter-Chronicle (Subversive Oral Memory)"

        hermeneutic_guidance = (
            "This investigation integrates empirical guild records with imperial annals. "
            "Numbers derived from plates are treated as empirical ground truth, while political motives "
            "and disputed founding years are contextualized according to their chronicler's allegiance."
        )

        return {
            "dominant_perspective": dominant_perspective,
            "overall_scepticism_level": highest_scepticism,
            "hermeneutic_guidance": hermeneutic_guidance,
            "audited_strata": identified_strata[:4]
        }
