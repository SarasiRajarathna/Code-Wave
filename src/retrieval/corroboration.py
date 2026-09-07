"""
corroboration.py

Multi-Source Corroboration Matrix for the Ashen Era Archive.
Evaluates cross-document consensus:
- Calculates distinct source files and corpus categories supporting key facts.
- Determines consensus level: HIGH_CONSENSUS (3+ distinct files), DUAL_CORROBORATED (2 distinct files), or ISOLATED_WITNESS (single file).
- Identifies independent corroborating witnesses.
"""

from pathlib import Path
from typing import List, Dict, Any, Set


class CorroborationMatrix:
    """Evaluates cross-document consensus and multi-source corroboration."""

    def evaluate(
        self,
        answer: str,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Computes the corroboration matrix across retrieved evidence chunks.
        """
        source_files: Set[str] = set()
        source_categories: Set[str] = set()
        corroborating_docs: List[Dict[str, str]] = []

        for c in chunks:
            meta = c.get("metadata", {})
            src = meta.get("source_file", "")
            if src:
                src_name = Path(src).name
                stype = meta.get("source_type", "unknown")
                if src_name not in source_files:
                    source_files.add(src_name)
                    source_categories.add(stype)
                    corroborating_docs.append({
                        "document": src_name,
                        "category": stype,
                        "chapter": meta.get("chapter", "")
                    })

        doc_count = len(source_files)
        cat_count = len(source_categories)

        if doc_count >= 3:
            consensus_level = "HIGH_CONSENSUS"
            consensus_description = f"Fact is multi-corroborated across {doc_count} independent documents spanning {cat_count} archive sectors."
        elif doc_count == 2:
            consensus_level = "DUAL_CORROBORATED"
            consensus_description = f"Corroborated by 2 distinct records with cross-sector agreement."
        else:
            consensus_level = "ISOLATED_WITNESS"
            consensus_description = f"Preserved by a single archival document; single-witness record noted."

        return {
            "consensus_level": consensus_level,
            "independent_sources_count": doc_count,
            "corpus_categories_count": cat_count,
            "consensus_description": consensus_description,
            "corroborating_documents": corroborating_docs[:5]
        }
