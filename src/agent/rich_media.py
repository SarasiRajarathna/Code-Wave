"""
rich_media.py

Supports Sub-track 1A: 'Rich Answers, Not Just Text'.
Detects if queries or retrieved chunks reference figure plates, heraldic banners,
character portraits, or creature illustrations, and embeds the actual image path
and extracted structured metrics into the final response.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class RichMediaResolver:
    """Finds and formats relevant figure plates, banners, and portraits for queries."""

    def __init__(self, search_roots: Optional[List[str]] = None):
        if search_roots is None:
            # Common paths where images reside in workspace
            base = Path(__file__).resolve().parent.parent.parent
            self.roots = [
                base / "data" / "corpus",
                base.parent / "Ashen_Era_Archive" / "Ashen_Era_Archive",
                base / "data" / "extracted",
            ]
        else:
            self.roots = [Path(r) for r in search_roots]

        self.image_index: Dict[str, Path] = {}
        self._index_images()

    def _index_images(self):
        """Build filename and stem lookup index for all archive images."""
        for root in self.roots:
            if not root.exists():
                continue
            for img_path in root.glob("**/*"):
                if img_path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    clean_key = img_path.stem.lower()
                    self.image_index[clean_key] = img_path
                    # Also index sub-parts (e.g., 'weeping_lurker', 'greyfell_citadel')
                    parts = clean_key.replace("plate_", "").replace("atmo_", "").replace("heraldry_", "").replace("portrait_", "").replace("artifact_", "").replace("creature_", "").replace("location_", "")
                    self.image_index[parts] = img_path

    def find_relevant_image(self, query: str, context_text: str = "") -> Optional[Dict[str, Any]]:
        """Identify if an image plate directly matches the subject of the query or context."""
        q_lower = query.lower()
        ctx_lower = context_text.lower()

        best_match = None
        best_match_len = 0

        # 1. First priority: Direct phrase match in the user query
        for key, img_path in self.image_index.items():
            words = key.split("_")
            if len(words) >= 2:
                phrase = " ".join(words)
                if phrase in q_lower and len(phrase) > best_match_len:
                    best_match = (key, img_path)
                    best_match_len = len(phrase)

        # 2. Second priority: Explicit plate markers in context
        if not best_match:
            plate_match = re.search(r"Plate\s*[-–:]\s*([A-Za-z0-9\s'_-]+)", context_text)
            if plate_match:
                plate_name = plate_match.group(1).strip()
                clean_name = re.sub(r"[^a-zA-Z0-9]+", "_", plate_name.lower())
                for key, img_path in self.image_index.items():
                    if clean_name in key or key in clean_name:
                        best_match = (plate_name, img_path)
                        break

        # 3. Third priority: Phrase match in context
        if not best_match:
            for key, img_path in self.image_index.items():
                words = key.split("_")
                if len(words) >= 2:
                    phrase = " ".join(words)
                    if phrase in ctx_lower and len(phrase) > best_match_len:
                        best_match = (key, img_path)
                        best_match_len = len(phrase)

        if best_match:
            key, img_path = best_match
            title = key.replace("_", " ").title()
            return {
                "title": title,
                "path": str(img_path),
                "relative_path": img_path.name,
                "markdown": f"\n\n![Figure: {title}]({img_path.as_uri()})\n*Figure: {title}*\n"
            }

        return None
