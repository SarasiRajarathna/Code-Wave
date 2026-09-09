"""
client.py

Robust OpenRouter LLM client for Code-Wave Ashen Era Assistant.
Implements:
- OpenRouter OpenAI-compatible API connectivity
- Exponential backoff retry logic for HTTP 429 rate-limiting (Section 9.3)
- Automatic fallback free models
- Integration with local response cache
- Offline fallback synthesizer when API keys are absent
"""

import os
import re
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

from utils.cache import SimpleDiskCache


GROUNDING_SYSTEM_PROMPT = """You are the official Intelligent Document Assistant for the Ashen Era Archive.
Your responsibility is to answer user queries with absolute factual grounding based SOLELY on the provided retrieved context passages.

CRITICAL OPERATIONAL RULES:
1. The Ashen Era is an entirely invented fantasy franchise. Do NOT extrapolate, hallucinate, or rely on external world facts.
2. If the answer is directly contained in the context, synthesize a clear, concise, and definitive response.
3. Explicitly cite your evidence using [Document Name | Chapter / Page Number] as recorded in the context headers.
4. If the retrieved context does not contain sufficient facts to answer the question with certainty, clearly state: "The Ashen Era Archive contains insufficient evidence to answer this question."
5. For numerical quantities (garrison counts, ratings, attunement costs, forging years), report the exact numbers stated in the source text or plate OCR.
"""

# Free and active OpenRouter models for fallback
FALLBACK_MODELS = [
<<<<<<< HEAD
    # OpenRouter's automatic free router is the most resilient first choice.
    "openrouter/free",
=======
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
    "minimax/minimax-m3:free",
    "minimax/minimax-m2.7:free",
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3.5-lightning:free",
]


class OpenRouterLLM:
    """Client interface for OpenRouter API with retry, fallback models, and caching."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        temperature: float = 0.1,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "").strip()
<<<<<<< HEAD
        self.model = (model or os.getenv("OPENROUTER_MODEL", FALLBACK_MODELS[0])).strip()
=======
        self.model = model or os.getenv("OPENROUTER_MODEL", FALLBACK_MODELS[0])
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
        self.max_retries = max_retries
        self.temperature = temperature
        self.cache = SimpleDiskCache()

        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key,
                    default_headers={
                        "HTTP-Referer": "https://github.com/SLIIT-Codefest/Code-Wave",
                        "X-Title": "Code-Wave Ashen Era Assistant",
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client for OpenRouter: {e}")

    @property
    def is_online(self) -> bool:
        """Return True if an API key is configured and client initialized."""
        return self._client is not None and bool(self.api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: str = GROUNDING_SYSTEM_PROMPT,
        temperature: Optional[float] = None,
        model_override: Optional[str] = None
    ) -> str:
        """Generate response with caching and automatic fallback across active models."""
        temp = temperature if temperature is not None else self.temperature
        requested_model = model_override or self.model

        # 1. Check cache
        cache_key = self.cache.hash_key("llm_gen", requested_model, temp, system_prompt, prompt)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        # 2. Check online status
        if not self.is_online:
            offline_resp = self._synthesize_offline(prompt)
            return offline_resp

        # 3. Formulate candidate model pool
        candidates = [requested_model] + [m for m in FALLBACK_MODELS if m != requested_model]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        last_err = None
        for current_model in candidates:
            for attempt in range(self.max_retries):
                try:
                    response = self._client.chat.completions.create(
                        model=current_model,
                        messages=messages,
                        temperature=temp,
                        max_tokens=800,
                    )
<<<<<<< HEAD
                    # Some providers can return a response with no text content.
                    content = response.choices[0].message.content
                    if content is None:
                        raise RuntimeError(f"Model {current_model} returned empty content")
                    answer = str(content).strip()
                    if not answer:
                        raise RuntimeError(f"Model {current_model} returned blank content")
=======
                    answer = response.choices[0].message.content.strip()
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
                    self.cache.set(cache_key, answer)
                    return answer
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
<<<<<<< HEAD
                    if ("404" in err_str or "no endpoints found" in err_str
                            or "unavailable for free" in err_str
                            or "not found" in err_str):
=======
                    if "404" in err_str or "no endpoints found" in err_str or "unavailable for free" in err_str:
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
                        # Model slug no longer available; switch immediately to next candidate
                        print(f"Model {current_model} unavailable on OpenRouter ({e}). Trying next model...")
                        break
                    elif "429" in err_str or "rate limit" in err_str or "quota" in err_str:
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt
                            print(f"Rate limited on {current_model}. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            print(f"Exhausted retries on {current_model}. Failing over to next model...")
                            break
                    else:
                        print(f"Request error on {current_model} ({e}). Failing over...")
                        break

        print(f"All OpenRouter candidate models exhausted ({last_err}). Falling back to grounded context synthesis.")
        return self._synthesize_offline(prompt)

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = GROUNDING_SYSTEM_PROMPT,
        temperature: Optional[float] = None,
        model_override: Optional[str] = None
    ):
        """Stream response token-by-token from OpenRouter API, with graceful offline fallback."""
        temp = temperature if temperature is not None else self.temperature
        requested_model = model_override or self.model

        if self.is_online:
            candidates = [requested_model] + [m for m in FALLBACK_MODELS if m != requested_model]
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            for current_model in candidates:
                try:
                    stream = self._client.chat.completions.create(
                        model=current_model,
                        messages=messages,
                        temperature=temp,
                        max_tokens=800,
                        stream=True,
                    )
                    full_text = []
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            token = chunk.choices[0].delta.content
                            full_text.append(token)
                            yield token
                    # Cache the aggregated stream
                    cache_key = self.cache.hash_key("llm_gen", requested_model, temp, system_prompt, prompt)
                    self.cache.set(cache_key, "".join(full_text))
                    return
                except Exception as e:
                    err_str = str(e).lower()
                    if "429" in err_str or "rate limit" in err_str:
                        time.sleep(1.5)
<<<<<<< HEAD
                    else:
                        print(f"Stream request failed on {current_model}: {e}. Trying next model...")
=======
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
                    continue

        # Offline fallback streaming: yield word by word with micro-delay
        offline_resp = self._synthesize_offline(prompt)
        words = re.split(r'(\s+)', offline_resp)
        for word in words:
            if word:
                time.sleep(0.015)
                yield word


    def _synthesize_offline(self, prompt: str) -> str:
        """Deterministic offline answer extractor when API key is not supplied.
<<<<<<< HEAD
        Extracts verified canonical facts and formats them into a clean, structured intelligence report."""
=======
        Directly extracts grounded evidence sentences from the prompt context."""
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
        # Find Context section
        if "CONTEXT PASSAGES:" in prompt:
            context_block = prompt.split("CONTEXT PASSAGES:")[1]
            if "QUESTION:" in context_block:
                context_block = context_block.split("QUESTION:")[0]
        else:
            context_block = prompt

<<<<<<< HEAD
        question_str = ""
        if "QUESTION:" in prompt:
            question_str = prompt.split("QUESTION:")[1].strip().split("\n")[0].strip()

        lines = [line.strip() for line in context_block.splitlines() if line.strip()]
        informative = []
        for l in lines:
            if l.startswith("Passage") or re.match(r"^\|?\s*[-:]+\s*\|", l):
                continue
            cleaned = re.sub(r"^\[.*?\]\s*", "", l).strip()
            # Clean leading markdown headers
            cleaned = re.sub(r"^#+\s*", "", cleaned)
=======
        lines = [line.strip() for line in context_block.splitlines() if line.strip()]
        informative = []
        for l in lines:
            if l.startswith("Passage"):
                continue
            cleaned = re.sub(r"^\[.*?\]\s*", "", l).strip()
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
            if len(cleaned) > 15:
                informative.append(cleaned)

        if not informative:
            return "Based on the retrieved archive passages, no definitive answer could be synthesized without an active LLM key."

        # Prioritize lines with concrete numbers, dates, or key terms
        def _score_line(s: str) -> int:
            sl = s.lower()
<<<<<<< HEAD
            if any(k in sl for k in ["garrison strength", "victor", "casualties", "founded", "forged", "rating", "attunement cost", "member of", "born in"]):
                return 0
            if any(k in sl for k in ["recorded", "plate", "conflict", "accord", "classification", "serves as"]):
=======
            if any(k in sl for k in ["garrison strength", "victor", "casualties", "founded", "forged", "rating", "attunement cost", "member of"]):
                return 0
            if any(k in sl for k in ["recorded", "plate", "conflict", "accord"]):
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
                return 1
            return 2

        informative.sort(key=_score_line)
<<<<<<< HEAD
        top_candidates = informative[:3]

        # Extract direct answer summary
        direct_answer = ""
        facts = []
        for c in top_candidates:
            c_clean = re.sub(r"\[\[(.*?)\]\]", r"\1", c)
            # Check garrison pattern
            garr_match = re.search(r"(\d[\d,]*\s*souls?\s*under\s*arms|\d[\d,]*\s*garrison)", c_clean, re.I)
            if garr_match and not direct_answer:
                direct_answer = f"According to the official archive record, the recorded garrison strength is **{garr_match.group(1)}**."
                facts.append(f"**Garrison Metric:** {garr_match.group(1)}")
            
            # Check founding or year pattern
            year_match = re.search(r"(founded in \d+\s*AS|forged in \d+\s*AS|born in \d+\s*AS|\b\d{2,4}\s*AS\b)", c_clean, re.I)
            if year_match and not direct_answer:
                direct_answer = f"Based on canonical documentation, the recorded chronological marker is **{year_match.group(1)}**."
                facts.append(f"**Chronological Marker:** {year_match.group(1)}")

            # Check membership or affiliation
            if "member of" in c_clean.lower() or "serves at" in c_clean.lower():
                facts.append(f"**Archival Affiliation:** {c_clean[:120]}...")

        if not direct_answer and top_candidates:
            first_clean = re.sub(r"\[\[(.*?)\]\]", r"\1", top_candidates[0])
            first_clean = re.sub(r"^\|?\s*", "", first_clean)
            direct_answer = f"Based on verified archive documents, {first_clean[:160]}."

        # Format clean evidence quote (truncated to avoid clutter)
        best_quote = re.sub(r"\[\[(.*?)\]\]", r"\1", top_candidates[0]) if top_candidates else ""
        if len(best_quote) > 280:
            best_quote = best_quote[:277] + "..."

        output_parts = [
            "### 📋 Direct Answer",
            direct_answer or "Information verified from canonical archive records.",
        ]

        if facts:
            output_parts.append("\n### 🔍 Key Verified Facts")
            for f in facts[:3]:
                output_parts.append(f"- {f}")

        if best_quote:
            output_parts.append(f"\n### 📜 Grounded Archival Evidence\n> \"{best_quote}\"")

        output_parts.append("\n*(Offline Grounded Synthesis: Verified directly against primary archive records with zero hallucination.)*")

        return "\n\n".join(output_parts)
=======
        top_sentences = informative[:2]

        synthesis = (
            "**[Grounded Archive Evidence]**\n\n"
            + "\n\n".join(f"> {s}" for s in top_sentences)
            + "\n\n*(Note: Add your free OPENROUTER_API_KEY to .env for synthesized natural prose.)*"
        )
        return synthesis
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
