"""
Gemini helper shared by the analysis and chat services.
- One place to configure the model name and output budget
- Robust JSON parsing (code fences, stray prose) with one retry
- Runs the blocking SDK call in a worker thread so the event loop stays free
"""

from typing import Any, Dict, List, Optional
import asyncio
import json
import logging
import re
import time

import google.generativeai as genai

from src.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger("klara.llm")

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


class LLMError(Exception):
    """Raised when the model cannot produce usable JSON."""


def parse_json_text(text: str) -> Any:
    """
    Parse model output as JSON. Accepts plain JSON, JSON wrapped in ``` fences,
    or JSON surrounded by a little prose. Raises ValueError when nothing parses.
    """
    if text is None:
        raise ValueError("empty model output")
    s = _FENCE_RE.sub("", text.strip()).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Fall back to the outermost object or array in the text
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start, end = s.find(open_ch), s.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(s[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("model output is not valid JSON")


def is_configured() -> bool:
    return bool(settings.gemini_api_key)


def json_model(max_output_tokens: int, temperature: float = 0.2) -> Optional[genai.GenerativeModel]:
    """Build a JSON-mode model, or None when no API key is configured."""
    if not settings.gemini_api_key:
        return None
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config={
            "response_mime_type": "application/json",
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        },
    )


def _response_text(resp: Any) -> str:
    try:
        return resp.text
    except Exception as e:
        # .text raises when the candidate was blocked or cut before any text
        reason = None
        try:
            reason = resp.candidates[0].finish_reason
        except Exception:
            pass
        raise ValueError(f"no text in model response (finish_reason={reason})") from e


async def generate_json(
    model: genai.GenerativeModel,
    parts: List[Dict[str, str]],
    retries: int = 1,
) -> Any:
    """
    Call the model and return parsed JSON. Retries once on empty or invalid JSON
    or an API error.
    Raises LLMError with the last error when every attempt fails.
    """
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        started = time.monotonic()
        try:
            resp = await asyncio.to_thread(
                model.generate_content,
                contents=[{"role": "user", "parts": parts}],
            )
            data = parse_json_text(_response_text(resp))
            usage = getattr(resp, "usage_metadata", None)
            logger.info(
                "gemini ok in %.1fs (attempt %d, prompt %s tokens, output %s tokens, total %s)",
                time.monotonic() - started, attempt + 1,
                getattr(usage, "prompt_token_count", "?"),
                getattr(usage, "candidates_token_count", "?"),
                getattr(usage, "total_token_count", "?"),
            )
            return data
        except Exception as e:
            # Invalid JSON, a blocked answer or a transient API error: try once more
            logger.warning("gemini attempt %d failed after %.1fs: %s", attempt + 1, time.monotonic() - started, e)
            last_err = e
            continue
    raise LLMError(str(last_err))
