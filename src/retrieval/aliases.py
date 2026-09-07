"""
aliases.py

Entity Alias and Epithet Resolver for the Ashen Era Archive.
Maps canonical historical entities, regional designations, and alternate aliases
so searches resolve accurately regardless of the phrasing or historical moniker used.
"""

import re
from typing import Dict, List, Set, Optional


class EntityAliasResolver:
    """Resolves entity aliases, epithets, and regional titles across the archive."""

    def __init__(self):
        # Comprehensive alias mapping across the Ashen Era lore
        self.alias_to_canonical: Dict[str, str] = {
            # Locations & Citadels
            "greyfell": "Greyfell Citadel",
            "greyfell citadel": "Greyfell Citadel",
            "high bastion": "Greyfell Citadel",
            "bastion of the shattered vale": "Greyfell Citadel",
            "the great citadel": "Greyfell Citadel",
            "gloamreach": "Gloamreach",
            "the shadowed city": "Gloamreach",
            "haven of gloam": "Gloamreach",
            "emberdeep": "Emberdeep",
            "the sunken furnace": "Emberdeep",
            "sorrowfell": "Sorrowfell",
            "the weeping valley": "Sorrowfell",
            "shattered vale": "The Shattered Vale",
            "the vale": "The Shattered Vale",

            # Relics & Weapons
            "thrice-bound edge": "The Thrice-Bound Edge",
            "thrice bound edge": "The Thrice-Bound Edge",
            "the bound blade": "The Thrice-Bound Edge",
            "gauntlet of sorrowfell": "The Gauntlet of Sorrowfell",
            "sorrowfell gauntlet": "The Gauntlet of Sorrowfell",
            "iron talon of sorrow": "The Gauntlet of Sorrowfell",
            "blade of vaeloria": "Blade of Vaeloria",

            # Figures & Rulers
            "vaelen": "King Vaelen the Unyielding",
            "king vaelen": "King Vaelen the Unyielding",
            "vaelen the unyielding": "King Vaelen the Unyielding",
            "alden": "Master Smith Alden",
            "master alden": "Master Smith Alden",
            "the iron smith": "Master Smith Alden",
            "malakor": "Malakor the Ashen King",
            "the ashen king": "Malakor the Ashen King",
            "high archon": "High Archon of the Pyre",

            # Eras & Periods
            "age of shadows": "Age of Shadows",
            "the shadow epoch": "Age of Shadows",
            "age of ash": "Age of Ash",
            "the ashen era": "The Ashen Era",
            "age of fire": "Age of Fire",
            "the first sun": "Age of Fire",

            # Factions & Orders
            "silent choir": "The Silent Choir",
            "the choir": "The Silent Choir",
            "order of whispers": "The Silent Choir",
            "church of the pyre": "The Church of the Pyre",
            "the pyre": "The Church of the Pyre",
            "ashen exiles": "The Ashen Exiles",
            "the exiles": "The Ashen Exiles"
        }

        # Inverted index: canonical to known aliases
        self.canonical_to_aliases: Dict[str, List[str]] = {}
        for alias, canonical in self.alias_to_canonical.items():
            if canonical not in self.canonical_to_aliases:
                self.canonical_to_aliases[canonical] = []
            if alias.lower() != canonical.lower() and alias not in self.canonical_to_aliases[canonical]:
                self.canonical_to_aliases[canonical].append(alias)

    def resolve_alias(self, text: str) -> Optional[str]:
        """Resolves a raw alias mention to its canonical historical entity name."""
        clean = text.strip().lower()
        return self.alias_to_canonical.get(clean)

    def expand_query_aliases(self, query: str) -> str:
        """
        Detects aliases or canonical entities in the query and returns an expanded search string
        incorporating alternate historical designations.
        """
        q_lower = query.lower()
        additions: List[str] = []

        for alias, canonical in self.alias_to_canonical.items():
            if re.search(rf"\b{re.escape(alias)}\b", q_lower):
                if canonical.lower() not in q_lower and canonical not in additions:
                    additions.append(canonical)
                # Also include prominent aliases if query uses canonical
                for alt in self.canonical_to_aliases.get(canonical, [])[:2]:
                    if alt not in q_lower and alt not in additions and len(alt) > 4:
                        additions.append(alt)

        if additions:
            return f"{query} {' '.join(additions)}"
        return query

    def get_known_aliases(self, entity_name: str) -> List[str]:
        """Returns all recorded epithets and aliases for a given entity."""
        canonical = self.resolve_alias(entity_name) or entity_name
        return self.canonical_to_aliases.get(canonical, [])
