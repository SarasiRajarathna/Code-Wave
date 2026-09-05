"""
iterative_agent.py

Implementation of Sub-track 1C: 'Searching the Way a Human Does'.
Executes an iterative, multi-step search loop:
1. Intent Decomposition & Entity Extraction
2. Initial Hybrid Retrieval (Dense Vector + BM25)
3. Evidence Reading & Wikilink Extraction
4. Sufficiency Evaluation
5. Gap Detection & Targeted Query Reformulation (Multi-Hop)
6. Grounded Answer Synthesis with Source Citations & Rich Media Embeds
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from retrieval.hybrid import HybridRetriever
from llm.client import OpenRouterLLM, GROUNDING_SYSTEM_PROMPT
from agent.rich_media import RichMediaResolver
from utils.cache import SimpleDiskCache


@dataclass
class SearchHop:
    hop_number: int
    query: str
    chunks: List[Dict[str, Any]]
    thought: str = ""


@dataclass
class AgentResult:
    question: str
    answer: str
    citations: List[str]
    hops: List[SearchHop]
    rich_media: Optional[Dict[str, Any]] = None
    is_sufficient: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "citations": self.citations,
            "total_hops": len(self.hops),
            "hops": [
                {
                    "hop": h.hop_number,
                    "query": h.query,
                    "thought": h.thought,
                    "retrieved_chunk_count": len(h.chunks)
                }
                for h in self.hops
            ],
            "rich_media": self.rich_media,
            "is_sufficient": self.is_sufficient,
        }


class AshenIterativeAgent:
    """Multi-hop human-like research agent for the Ashen Era Archive."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        llm: Optional[OpenRouterLLM] = None,
        rich_media: Optional[RichMediaResolver] = None,
        max_hops: int = 3,
    ):
        self.retriever = retriever or HybridRetriever()
        self.llm = llm or OpenRouterLLM()
        self.rich_media = rich_media or RichMediaResolver()
        self.max_hops = max_hops
        self.cache = SimpleDiskCache()

    def run(self, question: str, verbose: bool = True, no_cache: bool = False) -> AgentResult:
        """Execute human-like iterative search workflow for the user query."""
        if verbose:
            print(f"\n[Agent] Received Query: \"{question}\"")

        cache_key = self.cache.hash_key("agent_run", question, self.max_hops, self.llm.is_online, self.llm.model)
        if not no_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                if verbose:
                    print("[Agent] Returning cached response.")
                hops = [SearchHop(h["hop"], h["query"], [], h["thought"]) for h in cached_data.get("hops", [])]
                return AgentResult(
                    question=question,
                    answer=cached_data["answer"],
                    citations=cached_data["citations"],
                    hops=hops,
                    rich_media=cached_data.get("rich_media"),
                    is_sufficient=cached_data.get("is_sufficient", True)
                )

        seen_chunk_ids: Set[str] = set()
        accumulated_chunks: List[Dict[str, Any]] = []
        hops: List[SearchHop] = []

        current_query = question
        is_sufficient = False

        for hop_idx in range(1, self.max_hops + 1):
            if verbose:
                print(f"[Agent] Hop {hop_idx}/{self.max_hops} Searching: \"{current_query}\"")

            # 1. Retrieve candidates
            results = self.retriever.search(current_query, top_k=5)

            # Filter out chunks seen in previous hops
            new_chunks = [r for r in results if r["chunk_id"] not in seen_chunk_ids]
            for r in new_chunks:
                seen_chunk_ids.add(r["chunk_id"])

            accumulated_chunks.extend(new_chunks)

            # 2. Extract potential entities & wikilinks from retrieved text
            extracted_wikilinks = set()
            for c in new_chunks:
                text = c.get("text", "")
                links = re.findall(r"\[\[(.*?)\]\]", text)
                extracted_wikilinks.update(links)

            # 3. Evaluate sufficiency
            context_summary = self._format_context(accumulated_chunks)
            evaluation = self._evaluate_sufficiency(question, context_summary, extracted_wikilinks, hop_idx)

            hop_record = SearchHop(
                hop_number=hop_idx,
                query=current_query,
                chunks=new_chunks,
                thought=evaluation["thought"]
            )
            hops.append(hop_record)

            if verbose:
                print(f"  -> Thought: {evaluation['thought']}")

            if evaluation["sufficient"] or hop_idx == self.max_hops:
                is_sufficient = evaluation["sufficient"]
                break

            # 4. Reformulate query for next hop
            current_query = evaluation["next_query"]

        # 5. Synthesize grounded answer
        if verbose:
            print("[Agent] Synthesizing final grounded response...")

        final_context = self._format_context(accumulated_chunks)
        synthesis_prompt = f"""CONTEXT PASSAGES:
{final_context}

QUESTION: {question}

Provide a factual, concise, and definitive answer grounded exclusively in the context above.
Include specific numbers, names, and dates where applicable. Cite the sources."""

        answer = self.llm.generate(
            prompt=synthesis_prompt,
            system_prompt=GROUNDING_SYSTEM_PROMPT,
            temperature=0.1,
        )

        # 6. Format citations
        citations = self._extract_citations(accumulated_chunks)

        # 7. Check rich media (Sub-track 1A)
        rich_item = self.rich_media.find_relevant_image(question, final_context)
        if rich_item:
            answer = answer + rich_item["markdown"]

        result = AgentResult(
            question=question,
            answer=answer,
            citations=citations,
            hops=hops,
            rich_media=rich_item,
            is_sufficient=is_sufficient
        )

        self.cache.set(cache_key, result.to_dict())
        return result

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format chunk text with clear document and chapter/page headers."""
        blocks = []
        for i, c in enumerate(chunks, 1):
            meta = c.get("metadata", {})
            src = meta.get("source_file", "unknown")
            page = meta.get("page", "")
            chapter = meta.get("chapter", "")
            header = f"[{src} | Chapter: {chapter} | Page: {page}]" if chapter else f"[{src} | Page: {page}]"
            blocks.append(f"Passage {i} {header}:\n{c.get('text', '').strip()}")
        return "\n\n".join(blocks)

    def _extract_citations(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract clean unique citation strings."""
        cites = []
        seen = set()
        for c in chunks:
            meta = c.get("metadata", {})
            src = meta.get("source_file", "")
            page = meta.get("page")
            chapter = meta.get("chapter")
            name = Path(src).name if src else "Unknown Source"
            cite_str = f"{name}"
            if chapter and chapter != "(front matter)":
                cite_str += f", {chapter}"
            if page:
                cite_str += f" (p. {page})"
            if cite_str not in seen:
                seen.add(cite_str)
                cites.append(cite_str)
        return cites[:5]

    def _evaluate_sufficiency(
        self,
        question: str,
        context: str,
        wikilinks: Set[str],
        hop_idx: int
    ) -> Dict[str, Any]:
        """Determine whether the evidence suffices or formulate a targeted follow-up query."""
        # If offline without LLM key, use heuristic entity/number check
        if not self.llm.is_online:
            q_words = set(re.findall(r"\b[a-zA-Z0-9]{4,}\b", question.lower()))
            ctx_lower = context.lower()
            overlap = [w for w in q_words if w in ctx_lower]
            overlap_ratio = len(overlap) / max(1, len(q_words))

            target_concepts = [w for w in ["war", "accord", "conflict", "year", "rating", "strength", "object", "cost", "emblem", "motif"] if w in q_words]
            has_resolution = True
            if "war" in q_words or "accord" in q_words:
                has_resolution = any(k in ctx_lower for k in ["victor", "won", "victory", "defeated"])

            # If question is explicitly multi-hop and we found an entity link in hop 1, explore it
            is_multihop_q = any(phrase in question.lower() for phrase in ["faction of", "faction that", "organization that", "member of", "connected to", "won by the", "lair of"])
            if is_multihop_q and wikilinks and hop_idx < self.max_hops:
                generic_ignore = {"ashen era", "the ashen era", "sundered realms", "the sundered realms"}
                candidate_links = [l for l in wikilinks if l.lower() not in question.lower() and l.lower() not in generic_ignore and len(l) > 3]
                if candidate_links:
                    def _entity_priority(name: str) -> int:
                        nl = name.lower()
                        if any(tag in nl for tag in ["cartel", "choir", "vanguard", "house", "order", "legion", "circle", "covenant"]):
                            return 0
                        if any(tag in nl for tag in ["keep", "citadel", "abbey", "hold", "vale", "reach", "fortress"]):
                            return 1
                        return 2

                    candidate_links.sort(key=_entity_priority)
                    next_link = candidate_links[0]
                    target_cue = " ".join([w for w in ["accord", "war", "conflict", "victor", "won", "relic", "garrison", "dominion"] if w in q_words])
                    next_query = f"{next_link} {target_cue}".strip() if target_cue else next_link
                    return {
                        "sufficient": False,
                        "thought": f"Multi-hop question detected. Following identified entity [[{next_link}]]. Formulating next query: '{next_query}'",
                        "next_query": next_query
                    }

            # If strong match found and target concept is resolved, stop early
            if overlap_ratio >= 0.75 and has_resolution:
                return {
                    "sufficient": True,
                    "thought": f"Found high-confidence match for question terms ({len(overlap)}/{len(q_words)} keywords matched).",
                    "next_query": question
                }

            # If we found wikilinks and have remaining hops, follow the new entity
            if wikilinks and hop_idx < self.max_hops:
                # Prefer entities that aren't just repeating the question
                candidate_links = [l for l in wikilinks if l.lower() not in question.lower() and len(l) > 3]
                if not candidate_links:
                    candidate_links = list(wikilinks)

                next_link = candidate_links[0]
                target_cue = " ".join([w for w in ["accord", "war", "conflict", "victor", "won", "relic", "garrison"] if w in q_words])
                next_query = f"{next_link} {target_cue}".strip() if target_cue else next_link

                return {
                    "sufficient": False,
                    "thought": f"Extracted entity [[{next_link}]]. Formulating follow-up query: '{next_query}'",
                    "next_query": next_query
                }

            return {
                "sufficient": overlap_ratio >= 0.5 and has_resolution,
                "thought": f"Matched {len(overlap)} key terms from query.",
                "next_query": question
            }

        prompt = f"""You are analyzing search evidence in the Ashen Era Archive.
User Question: {question}

Current Evidence:
{context[:3000]}

Known Related Entity Links: {list(wikilinks)[:10]}

Answer with a JSON object with two fields:
1. "sufficient": true if the current evidence contains the direct, factual answer to the User Question. false if essential facts or relationships are still missing.
2. "thought": A brief 1-sentence reasoning statement explaining what was found or what is still missing.
3. "next_query": If sufficient is false, formulate a short, targeted search query (2-5 words) to find the missing connection or entity.

Return ONLY the JSON object.
"""
        resp = self.llm.generate(
            prompt=prompt,
            system_prompt="You are a precise search planner. Output valid JSON only.",
            temperature=0.0
        )

        try:
            # Clean possible markdown formatting
            clean_resp = re.sub(r"```json\s*", "", resp)
            clean_resp = re.sub(r"```\s*", "", clean_resp).strip()
            data = json.loads(clean_resp)
            return {
                "sufficient": bool(data.get("sufficient", False)),
                "thought": str(data.get("thought", "Analyzed evidence.")),
                "next_query": str(data.get("next_query", question))
            }
        except Exception:
            # Fallback
            return {
                "sufficient": True,
                "thought": "Proceeding with current evidence.",
                "next_query": question
            }
