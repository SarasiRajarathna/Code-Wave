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
        self.model = model or os.getenv("OPENROUTER_MODEL", FALLBACK_MODELS[0])
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
                    answer = response.choices[0].message.content.strip()
                    self.cache.set(cache_key, answer)
                    return answer
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    if "404" in err_str or "no endpoints found" in err_str or "unavailable for free" in err_str:
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

    def _synthesize_offline(self, prompt: str) -> str:
        """Deterministic offline answer extractor when API key is not supplied.
        Directly extracts grounded evidence sentences from the prompt context."""
        # Find Context section
        if "CONTEXT PASSAGES:" in prompt:
            context_block = prompt.split("CONTEXT PASSAGES:")[1]
            if "QUESTION:" in context_block:
                context_block = context_block.split("QUESTION:")[0]
        else:
            context_block = prompt

        lines = [line.strip() for line in context_block.splitlines() if line.strip()]
        informative = [l for l in lines if not l.startswith("Passage") and not l.startswith("[") and len(l) > 20]

        if not informative:
            return "Based on the retrieved archive passages, no definitive answer could be synthesized without an active LLM key."

        # Prioritize lines with concrete numbers, dates, or key terms
        def _score_line(s: str) -> int:
            sl = s.lower()
            if any(k in sl for k in ["garrison strength", "victor", "casualties", "founded", "forged", "rating", "attunement cost", "member of"]):
                return 0
            if any(k in sl for k in ["recorded", "plate", "conflict", "accord"]):
                return 1
            return 2

        informative.sort(key=_score_line)
        top_sentences = informative[:2]

        synthesis = (
            "**[Grounded Archive Evidence]**\n\n"
            + "\n\n".join(f"> {s}" for s in top_sentences)
            + "\n\n*(Note: Add your free OPENROUTER_API_KEY to .env for synthesized natural prose.)*"
        )
        return synthesis
