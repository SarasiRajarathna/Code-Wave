"""
conversation.py

Multi-Turn Conversational Memory & Coreference Resolver:
Allows natural, human-like dialogue across consecutive questions.
Resolves pronouns ('he', 'his', 'that ruler', 'the citadel', 'it') using active entity history.
"""

from typing import Dict, Any, List, Optional
import re
import uuid


class ConversationManager:
    """
    Maintains conversational session state and handles coreference disambiguation.
    """

    def __init__(self):
        # session_id -> list of turn dicts: {"role": "user"|"assistant", "text": "...", "entities": [...]}
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        if not session_id or session_id not in self.sessions:
            new_id = session_id or str(uuid.uuid4())[:8]
            self.sessions[new_id] = []
            return new_id
        return session_id

    def resolve_coreference(self, session_id: str, current_query: str) -> Dict[str, Any]:
        """
        Detects if current_query contains unresolved anaphora/pronouns,
        and rewrites it into a self-contained archival search query.
        """
        history = self.sessions.get(session_id, [])
        if not history:
            return {
                "resolved_query": current_query,
                "was_resolved": False,
                "anchor_entity": None,
                "original_query": current_query
            }

        # Look at the most recent assistant answer and user query
        last_turn = history[-1]
        last_entities = last_turn.get("entities", [])
        last_user_query = history[-2]["text"] if len(history) >= 2 and history[-2]["role"] == "user" else ""

        q_clean = current_query.strip()
        q_lower = q_clean.lower()

        # Pronoun patterns
        pronoun_patterns = [
            (r"\b(he|him|his)\b", "PERSON"),
            (r"\b(she|her)\b", "PERSON"),
            (r"\b(they|their|them)\b", "FACTION/GROUP"),
            (r"\b(it|its|that thing|that weapon|that relic)\b", "RELIC/OBJECT"),
            (r"\b(that place|that fortress|that city|there)\b", "LOCATION"),
            (r"\b(that ruler|the ruler|the king|the archon)\b", "PERSON"),
            (r"\b(that year|when)\b", "DATE"),
        ]

        detected_type = None
        has_pronoun = False

        for pat, ptype in pronoun_patterns:
            if re.search(pat, q_lower):
                has_pronoun = True
                detected_type = ptype
                break

        # Check if query is very short or clearly an ellipsis (e.g. "What about in the Age of Shadows?", "And why?")
        is_ellipsis = len(q_clean.split()) <= 4 or q_lower.startswith(("and ", "what about ", "why did ", "when did ", "where was "))

        if not has_pronoun and not is_ellipsis:
            return {
                "resolved_query": current_query,
                "was_resolved": False,
                "anchor_entity": None,
                "original_query": current_query
            }

        # Select primary anchor entity from last turn
        anchor_entity = None
        if last_entities:
            anchor_entity = last_entities[0]

        if not anchor_entity:
            return {
                "resolved_query": current_query,
                "was_resolved": False,
                "anchor_entity": None,
                "original_query": current_query
            }

        # Rewrite query
        resolved = current_query
        if has_pronoun:
            # Replace pronouns with the anchor entity
            for pat, _ in pronoun_patterns:
                resolved = re.sub(pat, anchor_entity, resolved, flags=re.IGNORECASE)
        elif is_ellipsis:
            resolved = f"{current_query.rstrip('?')} regarding {anchor_entity}?"

        return {
            "resolved_query": resolved,
            "was_resolved": resolved != current_query,
            "anchor_entity": anchor_entity,
            "original_query": current_query
        }

    def record_turn(self, session_id: str, question: str, answer: str, citations: List[str]):
        """Record turn and extract focal entities for future reference."""
        session = self.sessions.setdefault(session_id, [])

        # Extract entities from question and answer
        entities = self._extract_key_entities(question, answer)

        session.append({
            "role": "user",
            "text": question,
            "entities": entities
        })
        session.append({
            "role": "assistant",
            "text": answer,
            "citations": citations,
            "entities": entities
        })

        # Keep last 20 turns
        if len(session) > 20:
            self.sessions[session_id] = session[-20:]

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self.sessions.get(session_id, [])

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id] = []

    def _extract_key_entities(self, question: str, answer: str) -> List[str]:
        """Extract high-significance proper nouns and titles from text."""
        known_canon_entities = [
            "Greyfell Citadel", "Gloamreach", "Shattered Vale", "High Archon Malakor",
            "Gauntlet of Sorrowfell", "Sorrowfell", "Thrice-Bound Edge", "Age of Shadows",
            "Vaeloria", "Emberdeep", "Archon Velthorn", "Lady Isabel", "Order of the Veiled Sun"
        ]

        found = []
        combined = f"{question} {answer}"
        for ce in known_canon_entities:
            if ce.lower() in combined.lower() and ce not in found:
                found.append(ce)

        # Also grab capitalized 2-word sequences if not in list
        cap_candidates = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", answer)
        for c in cap_candidates:
            if c not in found and len(c) > 5 and not c.startswith(("According To", "As Stated", "In The")):
                found.append(c)

        return found[:5]
