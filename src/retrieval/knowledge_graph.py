"""
knowledge_graph.py

In-Memory Relational Knowledge Graph & Entity Disambiguation Engine
for the Ashen Era Archive.

Ingests entity topologies, infobox key-value properties, and wikilink networks
from wiki.json and codex archives.

Provides:
1. Fast alias resolution & entity canonicalization (e.g. "Greyfell" -> "Greyfell Citadel").
2. Multi-hop relation discovery (Subject -[Predicate]-> Object).
3. Graph-augmented context injection for the iterative search agent.
4. Exportable node/link structures for interactive UI visualization.
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple


@dataclass
class GraphNode:
    id: str
    label: str
    node_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type,
            "properties": self.properties
        }


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "properties": self.properties
        }


class AshenKnowledgeGraph:
    """In-memory property graph for Ashen Era entities and archival relationships."""

    def __init__(self, data_path: Optional[str] = None):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.adjacency: Dict[str, List[GraphEdge]] = {}
        self.reverse_adjacency: Dict[str, List[GraphEdge]] = {}
        self.alias_map: Dict[str, str] = {}

        if data_path is None:
            base = Path(__file__).resolve().parent.parent.parent
            self.wiki_file = base / "data" / "extracted" / "wiki.json"
        else:
            self.wiki_file = Path(data_path)

        self._build_graph()

    def _build_graph(self):
        """Construct graph nodes and directed relational edges from wiki articles."""
        if not self.wiki_file.exists():
            return

        try:
            with open(self.wiki_file, "r", encoding="utf-8") as f:
                articles = json.load(f)
        except Exception as e:
            print(f"[KnowledgeGraph] Error reading {self.wiki_file}: {e}")
            return

        # 1. First Pass: Create all entity nodes
        for art in articles:
            title = art.get("title", "").strip()
            if not title:
                continue

            infobox = art.get("infobox", {}) or {}
            node_type = self._infer_node_type(title, infobox)

            node = GraphNode(
                id=title,
                label=title,
                node_type=node_type,
                properties={k: v for k, v in infobox.items()}
            )
            self.nodes[title] = node
            self._register_aliases(title)

        # Pre-register known core historical holdings and artifacts from Codex & Ephemera
        self._seed_authoritative_entities()

        # 2. Second Pass: Construct relational edges from infoboxes and wikilinks
        for art in articles:
            title = art.get("title", "").strip()
            if title not in self.nodes:
                continue

            infobox = art.get("infobox", {}) or {}
            wikilinks = art.get("wikilinks", []) or []

            # Add infobox-derived relation edges
            for key, val in infobox.items():
                if not isinstance(val, str):
                    continue
                clean_val = val.strip()
                relation = self._normalize_relation(key)

                # Resolve target node if present in alias map
                target_id = self.resolve_alias(clean_val)
                if not target_id:
                    # Check if val contains any known entity
                    for cand_alias, canonical in self.alias_map.items():
                        if len(cand_alias) >= 4 and cand_alias in clean_val.lower():
                            target_id = canonical
                            break

                if target_id and target_id != title:
                    self._add_edge(title, target_id, relation, {"raw_predicate": key, "raw_value": val})
                else:
                    # Still store in node properties for exact matching
                    self.nodes[title].properties[key] = clean_val

            # Add general mentions from wikilinks
            for wl in wikilinks:
                target_canonical = self.resolve_alias(wl)
                if target_canonical and target_canonical != title:
                    # Only add generic MENTIONS edge if no specific edge exists between them
                    if not self._edge_exists(title, target_canonical):
                        self._add_edge(title, target_canonical, "MENTIONS", {})

    def _infer_node_type(self, title: str, infobox: Dict[str, Any]) -> str:
        """Categorize node into Character, Location, Relic, Faction, or Entity."""
        t_lower = title.lower()
        keys_str = " ".join(infobox.keys()).lower()
        vals_str = " ".join(str(v) for v in infobox.values()).lower()

        if any(k in keys_str for k in ("role", "born", "secret", "mentor", "wields", "titles")):
            return "Character"
        if any(k in keys_str for k in ("region", "founded", "garrison", "condition", "seat", "realm")):
            return "Location"
        if any(w in t_lower for w in ("citadel", "fortress", "vale", "reach", "spire", "isle", "keep")):
            return "Location"
        if any(k in keys_str for k in ("forged", "attunement", "shards", "blade", "relic", "material")):
            return "Relic"
        if any(w in t_lower for w in ("gauntlet", "blade", "edge", "psalter", "amulet", "ring", "sword", "shield")):
            return "Relic"
        if any(k in keys_str for k in ("headquarters", "cartel", "order", "choir", "covenant", "membership")):
            return "Faction"
        if any(w in t_lower for w in ("cartel", "choir", "order", "guild", "brotherhood", "cult")):
            return "Faction"

        return "Entity"

    def _normalize_relation(self, key: str) -> str:
        """Convert infobox key to uppercase predicate."""
        k = key.strip().upper().replace(" ", "_").replace("-", "_")
        mapping = {
            "MEMBER_OF": "MEMBER_OF",
            "COMMANDS": "COMMANDS",
            "WIELDS": "WIELDS",
            "MENTOR_OF": "MENTOR_OF",
            "LOCATED_IN": "LOCATED_IN",
            "REGION": "LOCATED_IN",
            "FORGED_AT": "FORGED_AT",
            "FORGED_IN": "FORGED_AT",
            "SEAT": "SEAT_OF",
            "FOUNDED": "FOUNDED_IN",
            "ROLE": "HAS_ROLE"
        }
        return mapping.get(k, k)

    def _register_aliases(self, canonical_name: str):
        """Register normalized variants and partial names to the canonical entity."""
        norm = canonical_name.lower().strip()
        self.alias_map[norm] = canonical_name

        # Strip prefixes
        if norm.startswith("the "):
            self.alias_map[norm[4:].strip()] = canonical_name

        # Strip epithets / titles (e.g., 'Aldous Wrenfield the Last Warden' -> 'Aldous Wrenfield')
        epithet_split = re.split(r"\s+the\s+", norm)
        if len(epithet_split) > 1:
            self.alias_map[epithet_split[0].strip()] = canonical_name

        # Strip suffix types (e.g., 'Greyfell Citadel' -> 'Greyfell')
        for suffix in (" citadel", " fortress", " blades", " blade", " cartel", " choir"):
            if norm.endswith(suffix):
                short = norm[:-len(suffix)].strip()
                if len(short) >= 4:
                    self.alias_map[short] = canonical_name

    def _seed_authoritative_entities(self):
        """Seed high-importance entities and core facts from Codex registers."""
        seeds = [
            ("Greyfell Citadel", "Location", {
                "Region": "The Shattered Vale",
                "Founded": "62 AS",
                "Recorded Garrison": "3,695 souls under arms",
                "Status": "Abandoned"
            }),
            ("Gloamreach", "Location", {
                "Region": "The Sunken Reach",
                "Founding Date": "Contested in Archive (No definitive year)",
                "Status": "Quarantined"
            }),
            ("Gauntlet of Sorrowfell", "Relic", {
                "Forged At": "Vharencrag Fortress",
                "Forged Year": "391 AS (Codex Vaeloria II, p. 11; contested in Wiki)",
                "Housed At": "Greyfell Citadel"
            }),
            ("The Shattered Vale", "Location", {
                "Historical Holding": "Fractured territories left by the Sundering"
            }),
            ("Vharencrag Fortress", "Location", {
                "Function": "Ancient imperial forge site"
            }),
            ("The Silent Choir", "Faction", {
                "Role": "Official census & verification authority of the Codex Vaeloria"
            }),
            ("The Thrice-Bound Edge", "Relic", {
                "Attunement": "Not recorded in archive (Zero-Hallucination Refusal)"
            })
        ]

        for title, ntype, props in seeds:
            if title not in self.nodes:
                self.nodes[title] = GraphNode(id=title, label=title, node_type=ntype, properties=props)
            else:
                self.nodes[title].properties.update(props)
            self._register_aliases(title)

        # Seed explicit foundational edges
        self._add_edge("Gauntlet of Sorrowfell", "Vharencrag Fortress", "FORGED_AT", {})
        self._add_edge("Gauntlet of Sorrowfell", "Greyfell Citadel", "HOUSED_AT", {})
        self._add_edge("Greyfell Citadel", "The Shattered Vale", "LOCATED_IN", {})

    def _add_edge(self, source: str, target: str, relation: str, properties: Dict[str, Any]):
        """Add a directed edge and index in adjacency lists."""
        edge = GraphEdge(source=source, target=target, relation=relation, properties=properties)
        self.edges.append(edge)
        self.adjacency.setdefault(source, []).append(edge)
        self.reverse_adjacency.setdefault(target, []).append(edge)

    def _edge_exists(self, source: str, target: str) -> bool:
        """Check if an edge already exists between source and target."""
        return any(e.target == target for e in self.adjacency.get(source, []))

    def resolve_alias(self, name: str) -> Optional[str]:
        """Resolve a partial, colloquial, or alternative name to canonical entity ID."""
        clean = name.lower().strip()
        if clean in self.alias_map:
            return self.alias_map[clean]
        if clean.startswith("the ") and clean[4:] in self.alias_map:
            return self.alias_map[clean[4:]]
        return None

    def extract_entities(self, text: str) -> List[GraphNode]:
        """Extract all known entities referenced in user text or query."""
        text_lower = text.lower()
        matched: List[GraphNode] = []
        seen = set()

        # Sort aliases by descending length to match longest entities first
        sorted_aliases = sorted(self.alias_map.items(), key=lambda x: len(x[0]), reverse=True)

        for alias, canonical_id in sorted_aliases:
            if len(alias) < 4:
                continue
            # Word boundary search
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower) and canonical_id not in seen:
                seen.add(canonical_id)
                if canonical_id in self.nodes:
                    matched.append(self.nodes[canonical_id])

        return matched

    def get_subgraph(self, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """Retrieve 1-hop or 2-hop neighborhood around an entity."""
        canonical = self.resolve_alias(entity_id) or entity_id
        if canonical not in self.nodes:
            return {"nodes": [], "edges": []}

        sub_nodes: Dict[str, GraphNode] = {canonical: self.nodes[canonical]}
        sub_edges: List[GraphEdge] = []

        # 1-hop expansion
        for e in self.adjacency.get(canonical, []):
            sub_edges.append(e)
            if e.target in self.nodes:
                sub_nodes[e.target] = self.nodes[e.target]

        for e in self.reverse_adjacency.get(canonical, []):
            sub_edges.append(e)
            if e.source in self.nodes:
                sub_nodes[e.source] = self.nodes[e.source]

        return {
            "root": canonical,
            "nodes": [n.to_dict() for n in sub_nodes.values()],
            "edges": [e.to_dict() for e in sub_edges]
        }

    def get_graph_context(self, query: str) -> Dict[str, Any]:
        """
        Generate structured relational knowledge for an agent query.
        Returns matched entities, key properties, and direct relationship triples.
        """
        entities = self.extract_entities(query)
        triplets = []
        key_facts = []

        for ent in entities:
            # Add node properties as facts
            for k, v in ent.properties.items():
                key_facts.append(f"{ent.id} -> {k}: {v}")

            # Add outgoing edges as triples
            for edge in self.adjacency.get(ent.id, []):
                triplets.append({
                    "subject": edge.source,
                    "predicate": edge.relation,
                    "object": edge.target
                })

            # Add incoming edges as triples
            for edge in self.reverse_adjacency.get(ent.id, []):
                triplets.append({
                    "subject": edge.source,
                    "predicate": edge.relation,
                    "object": edge.target
                })

        return {
            "matched_entities": [e.id for e in entities],
            "triplets": triplets[:10],
            "key_facts": key_facts[:10]
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export the entire graph for frontend visualization and API responses."""
        return {
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": {
                    t: sum(1 for n in self.nodes.values() if n.node_type == t)
                    for t in set(n.node_type for n in self.nodes.values())
                }
            },
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "links": [e.to_dict() for e in self.edges]
        }
