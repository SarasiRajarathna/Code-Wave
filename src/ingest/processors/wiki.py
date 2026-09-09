"""
processors/wiki.py

Wiki articles have two things no other folder has, and they're both
valuable enough to extract on their own:

1. [[Wikilinks]] -- every wiki article links to related entities
   (places, factions, people). This is basically a hand-built graph
   of "what connects to what" in the archive. For track 1C, this is
   gold: when your agent is deciding what to search next, the links
   already on the current page are strong candidates for the next hop.

2. An infobox table -- a markdown table near the top with structured
   fields (Region, Garrison strength, Status, Ruled by...). This is
   cleaner and more reliable than the prose for factual lookups, so
   it's worth pulling out separately rather than letting it get
   chunked in as plain text.

This processor runs AFTER loaders.load_file() -- it takes the already
-extracted page dicts and adds extra fields on top. It doesn't replace
the loader; it enriches what the loader already gave you.
"""

import re


def extract_wikilinks(text: str) -> list[str]:
    """Find every [[Entity Name]] reference in the text and return the
    unique entity names, in order of first appearance."""
    matches = re.findall(r"\[\[([^\]]+)\]\]", text)
    seen = []
    for m in matches:
        if m not in seen:
            seen.append(m)
    return seen


def extract_title(text: str) -> str | None:
    """Pull the article title from the first '# Heading' line, if present."""
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_infobox(text: str) -> dict:
    """Parse the first markdown table in the article (the infobox) into
    a plain dict, e.g. {"Region": "The Weeping Marshes", "Garrison strength": "2598", ...}.
    Wikilink brackets are stripped from values so they're clean plain text.
    Returns {} if no table is found.
    """
    table_match = re.search(
        r"\|\s*Field\s*\|\s*Value\s*\|\n\|[-\s|]+\|\n((?:\|.+\|\n?)+)",
        text,
    )
    if not table_match:
        return {}

    infobox = {}
    rows = table_match.group(1).strip().split("\n")
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) == 2:
            field, value = cells
            value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)  # strip [[ ]]
            infobox[field] = value

    return infobox


def process_wiki_page(page: dict) -> dict:
    """Take one page dict from loaders.load_file() and return it enriched
    with title, wikilinks, and infobox fields. The original 'text' field
    is left untouched -- this just adds metadata alongside it."""
    text = page["text"]
    enriched = dict(page)  # copy, don't mutate the original
    enriched["title"] = extract_title(text)
    enriched["wikilinks"] = extract_wikilinks(text)
    enriched["infobox"] = extract_infobox(text)
    return enriched
